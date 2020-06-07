from result import QueryStatus
from colorama import Fore, Style, init


class QueryNotify():
    def __init__(self, result=None):
        """Create Query Notify Object.

        Contains information about a specific method of notifying the results
        of a query.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """

        self.result = result

        return

    def start(self, message=None):

        return

    def update(self, result):

        self.result = result

        return

    def finish(self, message=None):

        return

    def __str__(self):
 
        result = str(self.result)

        return result


class QueryNotifyPrint(QueryNotify):
    def __init__(self, result=None, verbose=False, print_found_only=False,
                 color=True):
        init(autoreset=True)

        super().__init__(result)
        self.verbose = verbose
        self.print_found_only = print_found_only
        self.color = color

        return

    def start(self, message):
        title = "Checking username"
        if self.color:
            print(Style.BRIGHT + Fore.GREEN + "[" +
                Fore.YELLOW + "*" +
                Fore.GREEN + f"] {title}" +
                Fore.WHITE + f" {message}" +
                Fore.GREEN + " on:")
        else:
            print(f"[*] {title} {message} on:")

        return

    def update(self, result):
        self.result = result

        if self.verbose == False or self.result.query_time is None:
            response_time_text = ""
        else:
            response_time_text = f" [{round(self.result.query_time * 1000)} ms]"
            
        if result.status == QueryStatus.CLAIMED:
            if self.color:
                print((Style.BRIGHT + Fore.WHITE + "[" +
                       Fore.GREEN + "+" +
                       Fore.WHITE + "]" +
                       response_time_text +
                       Fore.GREEN +
                       f" {self.result.site_name}: {self.result.site_url_user}"))
            else:
                print(f"[+]{response_time_text} {self.result.site_name}: {self.result.site_url_user}")
        elif result.status == QueryStatus.AVAILABLE:
            if not self.print_found_only:
                if self.color:
                    print((Style.BRIGHT + Fore.WHITE + "[" +
                           Fore.RED + "-" +
                           Fore.WHITE + "]" +
                           response_time_text +
                           Fore.GREEN + f" {self.result.site_name}:" +
                           Fore.YELLOW + " Not Found!"))
                else:
                    print(f"[-]{response_time_text} {self.result.site_name}: Not Found!")
        elif result.status == QueryStatus.UNKNOWN:
            if self.color:
                print(Style.BRIGHT + Fore.WHITE + "[" +
                      Fore.RED + "-" +
                      Fore.WHITE + "]" +
                      Fore.GREEN + f" {self.result.site_name}:" +
                      Fore.RED + f" {self.result.context}" +
                      Fore.YELLOW + f" ")
            else:
                print(f"[-] {self.result.site_name}: {self.result.context} ")
        elif result.status == QueryStatus.ILLEGAL:
            if not self.print_found_only:
                msg = "Illegal Username Format For This Site!"
                if self.color:
                    print((Style.BRIGHT + Fore.WHITE + "[" +
                           Fore.RED + "-" +
                           Fore.WHITE + "]" +
                           Fore.GREEN + f" {self.result.site_name}:" +
                           Fore.YELLOW + f" {msg}"))
                else:
                    print(f"[-] {self.result.site_name} {msg}")
        else:
            #It should be impossible to ever get here...
            raise ValueError(f"Unknown Query Status '{str(result.status)}' for "
                             f"site '{self.result.site_name}'")

        return

    def __str__(self):

        result = str(self.result)

        return result
