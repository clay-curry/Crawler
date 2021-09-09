from typing import List, Deque
from webpageNode import WebpageNode

DEFAULT_BASE_URL = "https://ou.edu/cas/physics-astronomy/"
DEFAULT_NUM_THREADS = 1

internal_links_to_crawl: Deque[str] = []
external_links_to_crawl: Deque[str] = []


internal_have_visited: List[WebpageNode] = []
"""
A List of :class:`WebpageNode` objects containing detected internal sites.     
A :class:`WebpageNode` encapsulates data about a web page. It has the following attributes:
        `url`-> :class:`str`: a possible outward facing URL for the resolved page

        `exit_url`-> :class:`str`: the resolved exit url for the URL (after redirects)

        `status_code`-> :class:`int`: the HTTP Status code of the :attr:`exit_url`

        `status_history`-> :class:`List[int]`: an array of HTTP Status Codes for each redirect

        `links`-> :class:`List[str]`: an array of external links on the page

        `text`-> :class:`str`: the actual HTML text 
"""
external_have_visited: List[WebpageNode] = []
"""
A List of :class:`WebpageNode` objects containing detected external sites.     
A :class:`WebpageNode` encapsulates data about a web page. It has the following attributes:
        `url`-> :class:`str`: a possible outward facing URL for the resolved page

        `exit_url`-> :class:`str`: the resolved exit url for the URL (after redirects)

        `status_code`-> :class:`int`: the HTTP Status code of the :attr:`exit_url`

        `status_history`-> :class:`List[int]`: an array of HTTP Status Codes for each redirect

        `links`-> :class:`List[str]`: an array of external links on the page

        `text`-> :class:`str`: the actual HTML text 
"""

prev_cache_file_name: str = ""
"stores the name of the previous cache file"
next_cache_file_name: str = "cache/data.txt"
"stores the name of the next cache file"

persistent_data = {
    'last_checked': None,
    'reports': None,
    'excluded_urls': [],
    'internal': [],
    'external': []
}


def get_yes_no(msg: str = "") -> bool:
    """
    The message prints to the console and waits for the user to provide a valid indication of yes or no.

    If the user indicates yes, get_yes_no == True

    If the user indicates no, get_yes_no == False
    """
    y_n = input(msg)
    y_n = y_n.lower()
    while y_n != "yes" and y_n != "y" and y_n != "no" and y_n != "n":
        y_n = input("invalid response, please type 'yes' ('y') or 'no' ('no')")
        print()
        y_n = y_n.lower()
    return True if y_n == "yes" or y_n == "y" else False