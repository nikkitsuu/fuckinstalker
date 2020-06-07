#! /usr/bin/env python3

import csv
import os
import platform
import re
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from time import monotonic

import requests

from requests_futures.sessions import FuturesSession
from torrequest import TorRequest
from result import QueryStatus
from result import QueryResult
from notify import QueryNotifyPrint
from sites  import SitesInformation

module_name = "Sherlock: Find Usernames Across Social Networks"
__version__ = "0.00.0"



class SherlockFuturesSession(FuturesSession):
    def request(self, method, url, hooks={}, *args, **kwargs):
        start = monotonic()

        def response_time(resp, *args, **kwargs):
            resp.elapsed = monotonic() - start

            return
        try:
            if isinstance(hooks['response'], list):
                hooks['response'].insert(0, response_time)
            elif isinstance(hooks['response'], tuple):
                #Convert tuple to list and insert time measurement hook first.
                hooks['response'] = list(hooks['response'])
                hooks['response'].insert(0, response_time)
            else:
                hooks['response'] = [response_time, hooks['response']]
        except KeyError:
            hooks['response'] = [response_time]

        return super(SherlockFuturesSession, self).request(method,
                                                           url,
                                                           hooks=hooks,
                                                           *args, **kwargs)


def get_response(request_future, error_type, social_network):

    response = None

    error_context = "General Unknown Error"
    expection_text = None
    try:
        response = request_future.result()
        if response.status_code:
            error_context = None
    except requests.exceptions.HTTPError as errh:
        error_context = "HTTP Error"
        expection_text = str(errh)
    except requests.exceptions.ProxyError as errp:
        error_context = "Proxy Error"
        expection_text = str(errp)
    except requests.exceptions.ConnectionError as errc:
        error_context = "Error Connecting"
        expection_text = str(errc)
    except requests.exceptions.Timeout as errt:
        error_context = "Timeout Error"
        expection_text = str(errt)
    except requests.exceptions.RequestException as err:
        error_context = "Unknown Error"
        expection_text = str(err)

    return response, error_context, expection_text


def sherlock(username, site_data, query_notify,
             tor=False, unique_tor=False,
             proxy=None, timeout=None):

    query_notify.start(username)
    
    if tor or unique_tor:
        underlying_request = TorRequest()
        underlying_session = underlying_request.session
    else:
        underlying_session = requests.session()
        underlying_request = requests.Request()
    if len(site_data) >= 20:
        max_workers=20
    else:
        max_workers=len(site_data)
    session = SherlockFuturesSession(max_workers=max_workers,
                                     session=underlying_session)
    results_total = {}
    for social_network, net_info in site_data.items():
        results_site = {}
        results_site['url_main'] = net_info.get("urlMain")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
        }

        if "headers" in net_info:
            headers.update(net_info["headers"])
        url = net_info["url"].format(username)

        regex_check = net_info.get("regexCheck")
        if regex_check and re.search(regex_check, username) is None:
            results_site['status'] = QueryResult(username,
                                                 social_network,
                                                 url,
                                                 QueryStatus.ILLEGAL)
            results_site["url_user"] = ""
            results_site['http_status'] = ""
            results_site['response_text'] = ""
            query_notify.update(results_site['status'])
        else:
            results_site["url_user"] = url
            url_probe = net_info.get("urlProbe")
            if url_probe is None:
                url_probe = url
            else:
                url_probe = url_probe.format(username)

            if (net_info["errorType"] == 'status_code' and 
                net_info.get("request_head_only", True) == True):
                request_method = session.head
            else:
                request_method = session.get

            if net_info["errorType"] == "response_url":
                allow_redirects = False
            else:
                allow_redirects = True
            if proxy is not None:
                proxies = {"http": proxy, "https": proxy}
                future = request_method(url=url_probe, headers=headers,
                                        proxies=proxies,
                                        allow_redirects=allow_redirects,
                                        timeout=timeout
                                        )
            else:
                future = request_method(url=url_probe, headers=headers,
                                        allow_redirects=allow_redirects,
                                        timeout=timeout
                                        )
            net_info["request_future"] = future
            if unique_tor:
                underlying_request.reset_identity()
        results_total[social_network] = results_site
    for social_network, net_info in site_data.items():

        results_site = results_total.get(social_network)

        url = results_site.get("url_user")
        status = results_site.get("status")
        if status is not None:
            continue

        error_type = net_info["errorType"]
        future = net_info["request_future"]
        r, error_text, expection_text = get_response(request_future=future,
                                                     error_type=error_type,
                                                     social_network=social_network)

        try:
            response_time = r.elapsed
        except AttributeError:
            response_time = None

        try:
            http_status = r.status_code
        except:
            http_status = "?"
        try:
            response_text = r.text.encode(r.encoding)
        except:
            response_text = ""

        if error_text is not None:
            result = QueryResult(username,
                                 social_network,
                                 url,
                                 QueryStatus.UNKNOWN,
                                 query_time=response_time,
                                 context=error_text)
        elif error_type == "message":
            error = net_info.get("errorMsg")
            # Checks if the error message is in the HTML
            if not error in r.text:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        elif error_type == "status_code":
            # Checks if the status code of the response is 2XX
            if not r.status_code >= 300 or r.status_code < 200:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        elif error_type == "response_url":
            if 200 <= r.status_code < 300:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        else:
            raise ValueError(f"Unknown Error Type '{error_type}' for "
                             f"site '{social_network}'")


        query_notify.update(result)

        results_site['status'] = result

        results_site['http_status'] = http_status
        results_site['response_text'] = response_text

        results_total[social_network] = results_site
        
    query_notify.finish()

    return results_total


def timeout_check(value):

    from argparse import ArgumentTypeError

    try:
        timeout = float(value)
    except:
        raise ArgumentTypeError(f"Timeout '{value}' must be a number.")
    if timeout <= 0:
        raise ArgumentTypeError(f"Timeout '{value}' must be greater than 0.0s.")
    return timeout


def main():

    version_string = f"%(prog)s {__version__}\n" +  \
                     f"{requests.__description__}:  {requests.__version__}\n" + \
                     f"Python:  {platform.python_version()}"

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=f"{module_name} (Version {__version__})"
                            )
    parser.add_argument("--version",
                        action="version",  version=version_string,
                        help="Display version information and dependencies."
                        )
    parser.add_argument("--verbose", "-v", "-d", "--debug",
                        action="store_true",  dest="verbose", default=False,
                        help="Display extra debugging information and metrics."
                        )
    parser.add_argument("--rank", "-r",
                        action="store_true", dest="rank", default=False,
                        help="Present websites ordered by their Alexa.com global rank in popularity.")
    parser.add_argument("--folderoutput", "-fo", dest="folderoutput",
                        help="If using multiple usernames, the output of the results will be saved to this folder."
                        )
    parser.add_argument("--output", "-o", dest="output",
                        help="If using single username, the output of the result will be saved to this file."
                        )
    parser.add_argument("--tor", "-t",
                        action="store_true", dest="tor", default=False,
                        help="Make requests over Tor; increases runtime; requires Tor to be installed and in system path.")
    parser.add_argument("--unique-tor", "-u",
                        action="store_true", dest="unique_tor", default=False,
                        help="Make requests over Tor with new Tor circuit after each request; increases runtime; requires Tor to be installed and in system path.")
    parser.add_argument("--csv",
                        action="store_true",  dest="csv", default=False,
                        help="Create Comma-Separated Values (CSV) File."
                        )
    parser.add_argument("--site",
                        action="append", metavar='SITE_NAME',
                        dest="site_list", default=None,
                        help="Limit analysis to just the listed sites. Add multiple options to specify more than one site."
                        )
    parser.add_argument("--proxy", "-p", metavar='PROXY_URL',
                        action="store", dest="proxy", default=None,
                        help="Make requests over a proxy. e.g. socks5://127.0.0.1:1080"
                        )
    parser.add_argument("--json", "-j", metavar="JSON_FILE",
                        dest="json_file", default=None,
                        help="Load data from a JSON file or an online, valid, JSON file.")
    parser.add_argument("--timeout",
                        action="store", metavar='TIMEOUT',
                        dest="timeout", type=timeout_check, default=None,
                        help="Time (in seconds) to wait for response to requests. "
                             "Default timeout of 60.0s."
                             "A longer timeout will be more likely to get results from slow sites."
                             "On the other hand, this may cause a long delay to gather all results."
                        )
    parser.add_argument("--print-found",
                        action="store_true", dest="print_found_only", default=False,
                        help="Do not output sites where the username was not found."
                        )
    parser.add_argument("--no-color",
                        action="store_true", dest="no_color", default=False,
                        help="Don't color terminal output"
                        )
    parser.add_argument("username",
                        nargs='+', metavar='USERNAMES',
                        action="store",
                        help="One or more usernames to check with social networks."
                        )
    parser.add_argument("--browse", "-b",
                        action="store_true", dest="browse", default=False,
                        help="Browse to all results on default bowser.")

    args = parser.parse_args()

    if args.tor and (args.proxy is not None):
        raise Exception("Tor and Proxy cannot be set at the same time.")

    if args.proxy is not None:
        print("Using the proxy: " + args.proxy)

    if args.tor or args.unique_tor:
        print("Using Tor to make requests")
        print("Warning: some websites might refuse connecting over Tor, so note that using this option might increase connection errors.")

    if args.output is not None and args.folderoutput is not None:
        print("You can only use one of the output methods.")
        sys.exit(1)

    if args.output is not None and len(args.username) != 1:
        print("You can only use --output with a single username")
        sys.exit(1)

    try:
        sites = SitesInformation(args.json_file)
    except Exception as error:
        print(f"ERROR:  {error}")
        sys.exit(1)

    site_data_all = {}
    for site in sites:
        site_data_all[site.name] = site.information

    if args.site_list is None:
        site_data = site_data_all
    else:

        site_data = {}
        site_missing = []
        for site in args.site_list:
            for existing_site in site_data_all:
                if site.lower() == existing_site.lower():
                    site_data[existing_site] = site_data_all[existing_site]
            if not site_data:
                site_missing.append(f"'{site}'")

        if site_missing:
            print(
                f"Error: Desired sites not found: {', '.join(site_missing)}.")
            sys.exit(1)

    if args.rank:
        site_dataCpy = dict(site_data)
        ranked_sites = sorted(site_data, key=lambda k: ("rank" not in k, site_data[k].get("rank", sys.maxsize)))
        site_data = {}
        for site in ranked_sites:
            site_data[site] = site_dataCpy.get(site)

    query_notify = QueryNotifyPrint(result=None,
                                    verbose=args.verbose,
                                    print_found_only=args.print_found_only,
                                    color=not args.no_color)
    for username in args.username:
        print()

        results = sherlock(username,
                           site_data,
                           query_notify,
                           tor=args.tor,
                           unique_tor=args.unique_tor,
                           proxy=args.proxy,
                           timeout=args.timeout)

        if args.output:
            result_file = args.output
        elif args.folderoutput:
            os.makedirs(args.folderoutput, exist_ok=True)
            result_file = os.path.join(args.folderoutput, f"{username}.txt")
        else:
            result_file = f"{username}.txt"

        with open(result_file, "w", encoding="utf-8") as file:
            exists_counter = 0
            for website_name in results:
                dictionary = results[website_name]
                if dictionary.get("status").status == QueryStatus.CLAIMED:
                    exists_counter += 1
                    file.write(dictionary["url_user"] + "\n")
            file.write(f"Total Websites Username Detected On : {exists_counter}")

        if args.csv:
            with open(username + ".csv", "w", newline='', encoding="utf-8") as csv_report:
                writer = csv.writer(csv_report)
                writer.writerow(['username',
                                 'name',
                                 'url_main',
                                 'url_user',
                                 'exists',
                                 'http_status',
                                 'response_time_s'
                                 ]
                                )
                for site in results:
                    response_time_s = results[site]['status'].query_time
                    if response_time_s is None:
                        response_time_s = ""
                    writer.writerow([username,
                                     site,
                                     results[site]['url_main'],
                                     results[site]['url_user'],
                                     str(results[site]['status'].status),
                                     results[site]['http_status'],
                                     response_time_s
                                     ]
                                    )


if __name__ == "__main__":
    main()
