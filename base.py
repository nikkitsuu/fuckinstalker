import os
import os.path
import unittest
import sherlock
from result import QueryStatus
from result import QueryResult
from notify import QueryNotify
from sites  import SitesInformation
import warnings


class SherlockBaseTest(unittest.TestCase):
    def setUp(self):

        warnings.simplefilter("ignore", ResourceWarning)

        sites = SitesInformation()
        
        site_data_all = {}
        for site in sites:
            site_data_all[site.name] = site.information
        self.site_data_all = site_data_all

        excluded_sites_path = os.path.join(os.path.dirname(os.path.realpath(sherlock.__file__)), "tests/.excluded_sites")
        try:
          with open(excluded_sites_path, "r", encoding="utf-8") as excluded_sites_file:
            self.excluded_sites = excluded_sites_file.read().splitlines()
        except FileNotFoundError:
          self.excluded_sites = []

        self.query_notify = QueryNotify()

        self.tor=False
        self.unique_tor=False
        self.timeout=None
        self.skip_error_sites=True

        return

    def site_data_filter(self, site_list):

        site_data = {}
        for site in site_list:
            with self.subTest(f"Checking test vector Site '{site}' "
                              f"exists in total site data."
                             ):
                site_data[site] = self.site_data_all[site]

        return site_data

    def username_check(self, username_list, site_list, exist_check=True):
    
        site_data = self.site_data_filter(site_list)

        if exist_check:
            check_type_text = "claimed"
            exist_result_desired = QueryStatus.CLAIMED
        else:
            check_type_text = "available"
            exist_result_desired = QueryStatus.AVAILABLE

        for username in username_list:
            results = sherlock.sherlock(username,
                                        site_data,
                                        self.query_notify,
                                        tor=self.tor,
                                        unique_tor=self.unique_tor,
                                        timeout=self.timeout
                                       )
            for site, result in results.items():
                with self.subTest(f"Checking Username '{username}' "
                                  f"{check_type_text} on Site '{site}'"
                                 ):
                    if (
                         (self.skip_error_sites == True) and
                         (result['status'].status == QueryStatus.UNKNOWN)
                       ):
                        #Some error connecting to site.
                        self.skipTest(f"Skipping Username '{username}' "
                                      f"{check_type_text} on Site '{site}':  "
                                      f"Site returned error status."
                                     )

                    self.assertEqual(exist_result_desired,
                                     result['status'].status)

        return

    def detect_type_check(self, detect_type, exist_check=True):
        sites_by_username = {}

        for site, site_data in self.site_data_all.items():
            if (
                 (site in self.excluded_sites)                 or
                 (site_data["errorType"] != detect_type)       or
                 (site_data.get("username_claimed")   is None) or
                 (site_data.get("username_unclaimed") is None)
               ):
                pass
            else:
                if exist_check:
                     username = site_data.get("username_claimed")
                else:
                     username = site_data.get("username_unclaimed")
                if username in sites_by_username:
                    sites_by_username[username].append(site)
                else:
                    sites_by_username[username] = [site]
        for username, site_list in sites_by_username.items():
            self.username_check([username],
                                site_list,
                                exist_check=exist_check
                               )
        return

    def coverage_total_check(self):

        site_no_tests_list = []

        for site, site_data in self.site_data_all.items():
            if (
                 (site_data.get("username_claimed")   is None) or
                 (site_data.get("username_unclaimed") is None)
               ):
                site_no_tests_list.append(site)

        self.assertEqual("", ", ".join(site_no_tests_list))

        return
