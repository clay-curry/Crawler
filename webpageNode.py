from multiprocessing import Process, Pipe
import re
from typing import List
from html.parser import HTMLParser
from urllib.parse import urlparse

import urllib3
import requests

DEFAULT_TIMEOUT = urllib3.Timeout(connect=5.0, read=8.0)
DEFAULT_HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Content-Type": "text",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "sec-fetch-dest": "document"
}
DEFAULT_RETRY = urllib3.Retry(status_forcelist=[429, 500, 502, 503, 504],
                              allowed_methods=["HEAD", "GET", "OPTIONS"],
                              backoff_factor=2,
                              total=3)
# not working: https://www.the-nhsn.org/


class WebpageNode(object):
    """
    A :class:`WebpageNode` encapsulates data about a web page. It has the following attributes:
        `url`-> :class:`str`: a possible outward facing URL for the resolved page

        `exit_url`-> :class:`str`: the resolved exit url for the URL (after redirects)

        `status_code`-> :class:`int`: the HTTP Status code of the :attr:`exit_url`

        `status_history`-> :class:`List[int]`: an array of HTTP Status Codes for each redirect

        `links`-> :class:`List[str]`: an array of external links on the page

        `text`-> :class:`str`: the actual HTML text

    .. note::

        If the web page is determined to be a child page of the base_url
        (determined by the path of the exit_url) the get_site_data() method will store the text and scrape its links.
        By default, the WebpageNode constructor does not perform an HTTP request, which would significantly increase
        latency. To perform an HTTP request at construction time, use the get_site_data = True constructor parameter. To
        perform an HTTP request at a later time, call the get_site_data() method on the instance. A status_code == 600
        indicates that the HTTP request has not been performed on the WebpageNode.

    :param url: provided url (without redirect) of the given WebpageNode
    :param base_url: url of the root page from which the audited site grows
    :param get_site_data: configures whether the WebpageNode performs an HTTP request at construction time

    """


    def __str__(self):
        return self.url

    def __eq__(self, url):
        if type(url) == WebpageNode:
            url = url.url
        self_path = urlparse(self.url).path.rstrip('/').removesuffix(".html").removesuffix(".htm")
        other_path = urlparse(url).path.rstrip('/').removesuffix(".html").removesuffix(".htm")
        return urlparse(self.url).netloc == urlparse(url).netloc and self_path == other_path

    def __dict__(self):
        return {
            'url': self.url,
            'exit_url': self.exit_url,
            'base_url': self.base_url,
            'status_code': self.status_code,
            'status_history': self.status_history,
            'links': self.links,
            'text': self.text,
        }

    def __hash__(self):
        return self.url.__hash__()

    def __init__(self, url: str, base_url: str = "", get_site_data: bool = False):
        self.url = url
        self.exit_url = url
        self.base_url = base_url
        self.status_code = 600
        self.status_history: List[int] = []
        self.links: List[str] = []
        self.text = ""
        if get_site_data:
            self.get_site_data()

    def __get_links(self):
        try:
            parent_conn, child_conn = Pipe()
            p = Process(target=__get_links__, args=(self.text, child_conn,))
            p.start()
            p.join(timeout=300)

            if p.is_alive():
                p.terminate()
            if parent_conn.poll():
                self.links = parent_conn.recv()
                domain = urlparse(self.exit_url).scheme + "://" + urlparse(self.exit_url).netloc

                for i in range(0, len(self.links)):
                    if self.links[i][0] == '/':
                        self.links[i] = domain + self.links[i]
            else:
                self.text = ""
        finally:
            child_conn.close()
            parent_conn.close()

    def get_site_data(self):
        # Attempts to secure a connection using a plain get-http request. A new process is created so that that the
        # function can be terminated after some specified amount of time. This ensures the program does not get hung on
        # a non-cooperative server or while parsing a corrupt web resource
        connection_established = False

        # PERFORMING HTTP REQUEST using urllib3, scraping page-specific data
        try:
            with requests.Session() as s:
                r = s.get(url=self.url, headers=DEFAULT_HEADERS, timeout=13)
                self.exit_url = r.url
                self.status_code = r.status_code
                for code in r.history:
                    self.status_history.append(code.status_code)
                if self.is_in_base_site():
                    self.text = r.text
                    self.__get_links()

        except requests.Timeout as e:
            try:
                with urllib3.PoolManager(retries=DEFAULT_RETRY)as p:
                    r = p.request(method="GET", url=self.url, headers=DEFAULT_HEADERS)
                    self.exit_url = r.geturl()
                    self.status_code = r.status  # for more details, use requests.codes[self.status_code]
                    for code in r.REDIRECT_STATUSES:
                        self.status_history.append(code)
                    if self.is_in_base_site():
                        self.text = r.data
                        self.__getlinks()
            except:
                print(f" URLLIB3 and REQUESTS failed to establish a connection with [{self.url}].")
                return
        except:
            print(f" REQUESTS catastrophically failed to establish a connection with [{self.url}].")
            return

    def is_in_base_site(self) -> bool:
        return self.exit_url.find(self.base_url) != -1 if self.base_url != "" else False

    def get_internal_links(self) -> List[str]:
        internal = []
        link: str
        for link in self.links:
            if link.find(self.base_url) != -1:
                internal.append(link)
        return internal

    def get_external_links(self) -> List[str]:
        external = []
        link: str
        for link in self.links:
            if link.find(self.base_url) == -1:
                external.append(link)
        return external


def __get_links__(text, pipe: Pipe) -> List[str]:
    links: List[str] = []
    parser = RetrieveLinks()
    parser.feed(text)
    links = parser.get_links()
    pipe.send(links)
    pipe.close()

class RetrieveLinks(HTMLParser):
    links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    href = attr[1].strip()
                    if href[0] == "#":
                        break
                    if href.find("tel") != -1:
                        break
                    if href.find("mailto") != -1:
                        break
                    if href[0:2] == "//":
                        href = "https:" + href
                    self.links.append(href)

    def handle_data(self, data):
        javascript_redirect = re.compile("window\.location.*?=.*?[\'\"].*?[\'\"]")
        javascript_redirect = javascript_redirect.findall(data)
        if len(javascript_redirect):
            url_arg = re.compile("(?<=[\'\"]).*?(?=[\'\"])")
            self.links.append(url_arg.search(javascript_redirect[0].group(0)).group(0))

    @classmethod
    def get_links(cls):
        links = cls.links
        cls.links = []
        return links















