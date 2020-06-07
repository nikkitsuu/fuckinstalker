import os
import json
import operator
import requests
import sys


class SiteInformation():
    def __init__(self, name, url_home, url_username_format, popularity_rank,
                 username_claimed, username_unclaimed,
                 information):

        self.name                = name
        self.url_home            = url_home
        self.url_username_format = url_username_format

        if (popularity_rank is None) or (popularity_rank == 0):
            popularity_rank = sys.maxsize
        self.popularity_rank     = popularity_rank

        self.username_claimed    = username_claimed
        self.username_unclaimed  = username_unclaimed
        self.information         = information

        return

    def __str__(self):
        return f"{self.name} ({self.url_home})"


class SitesInformation():
    def __init__(self, data_file_path=None):

        if data_file_path is None:
            data_file_path = \
                os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "resources/data.json"
                            )

        if ".json" != data_file_path[-5:].lower():
            raise FileNotFoundError(f"Incorrect JSON file extension for "
                                    f"data file '{data_file_path}'."
                                   )

        if ( ("http://"  == data_file_path[:7].lower()) or
             ("https://" == data_file_path[:8].lower())
           ):
            try:
                response = requests.get(url=data_file_path)
            except Exception as error:
                raise FileNotFoundError(f"Problem while attempting to access "
                                        f"data file URL '{data_file_path}':  "
                                        f"{str(error)}"
                                       )
            if response.status_code == 200:
                try:
                    site_data = response.json()
                except Exception as error:
                    raise ValueError(f"Problem parsing json contents at "
                                     f"'{data_file_path}':  {str(error)}."
                                    )
            else:
                raise FileNotFoundError(f"Bad response while accessing "
                                        f"data file URL '{data_file_path}'."
                                       )
        else:
            try:
                with open(data_file_path, "r", encoding="utf-8") as file:
                    try:
                        site_data = json.load(file)
                    except Exception as error:
                        raise ValueError(f"Problem parsing json contents at "
                                         f"'{data_file_path}':  {str(error)}."
                                        )
            except FileNotFoundError as error:
                raise FileNotFoundError(f"Problem while attempting to access "
                                        f"data file '{data_file_path}'."
                                       )

        self.sites = {}

        for site_name in site_data:
            try:
                popularity_rank = site_data[site_name].get("rank", sys.maxsize)

                self.sites[site_name] = \
                    SiteInformation(site_name,
                                    site_data[site_name]["urlMain"],
                                    site_data[site_name]["url"],
                                    popularity_rank,
                                    site_data[site_name]["username_claimed"],
                                    site_data[site_name]["username_unclaimed"],
                                    site_data[site_name]
                                   )
            except KeyError as error:
                raise ValueError(f"Problem parsing json contents at "
                                 f"'{data_file_path}':  "
                                 f"Missing attribute {str(error)}."
                                )

        return

    def site_name_list(self, popularity_rank=False):

        if popularity_rank:
            site_rank_name = \
                sorted([(site.popularity_rank,site.name) for site in self],
                       key=operator.itemgetter(0)
                      )
            site_names = [name for _,name in site_rank_name]
        else:
            site_names = sorted([site.name for site in self], key=str.lower)

        return site_names

    def __iter__(self):
        for site_name in self.sites:
            yield self.sites[site_name]

    def __len__(self):
        return len(self.sites)
