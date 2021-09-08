import config
from appendageCrawler import *
import cache_site
from webpageNode import WebpageNode
import time
import threading
from typing import List, Deque


def start(base_url: str, num_threads: int = 1):
    # This function determines whether the calling function is passing valid arguments before passing them to the
    # crawler creating function.
    print(f"The crawler has started at {base_url} with {num_threads} threads.")
    if num_threads < 1:
        print(f"  Execution using {num_threads} threads is not possible")
        return None
    else:
        # After confirming that the number of threads > 1, the function generates a list of pages immediately connected
        # to the base url.
        base_node = WebpageNode(url=base_url, base_url=base_url, get_site_data=True)
        print(f"The base URL {base_node.url} crawled with status {base_node.status_code}")
        config.internal_have_visited.append(base_node)

        for link in base_node.get_internal_links():
            if link not in config.internal_links_to_crawl:
                config.internal_links_to_crawl.append(link)

        for link in base_node.get_external_links():
            if link not in config.external_links_to_crawl:
                config.external_links_to_crawl.append(link)

        #####################################################################
        # CRAWL WEBSITE STARTING FROM BASE URL
        # With the base url set, the crawlers follow pages recursively to scan the entire website. Crawlers are made
        # here
        inner_crawlers = make_inner_crawlers(base_node, num_threads)
        for crawler in inner_crawlers:
            crawler.join()

        appendage_crawlers = make_appendage_crawlers(num_threads)
        for crawler in appendage_crawlers:
            crawler.join()

        print(f"  Total Number of internal pages visited are {len(config.internal_have_visited)}")
        print(f"  Total Number of external pages visited are {len(config.external_have_visited)}")

        cache_site.set_nodes()
    print("The crawler has completed. Initialized cache with discovered data")


def make_inner_crawlers(base_url, num_threads):

    # A universal lock is used to avoid racing condition, i.e. two threads access a shared variable at the same time.
    # A single lock prevents a deadlock from occurring. A priority lock ensures quicker tasks are unlocked first.
    enqueue_lock = threading.Lock()
    priority_unlock = threading.Lock()
    crawler_threads = []
    for i in range(num_threads):
        crawler = InnerSiteCrawler(base_url=base_url.url, priority_unlock=priority_unlock, enqueue_lock=enqueue_lock,
                                   internal_links_to_crawl=config.internal_links_to_crawl,
                                   internal_have_visited=config.internal_have_visited,
                                   external_links_to_crawl=config.external_links_to_crawl,
                                   external_have_visited=config.external_have_visited, c_num = i
                                   )
        crawler_threads.append(crawler)
        crawler.start()
    return crawler_threads


class InnerSiteCrawler(threading.Thread):
    def __init__(self, c_num, base_url, priority_unlock, enqueue_lock,
                 internal_links_to_crawl: Deque[str], internal_have_visited: List[WebpageNode],
                 external_links_to_crawl: Deque[str], external_have_visited: List[WebpageNode]):
        threading.Thread.__init__(self)
        self.c_num = c_num
        self.base_url = base_url
        self.priority_unlock = priority_unlock
        self.enqueue_lock = enqueue_lock
        self.internal_links_to_crawl = internal_links_to_crawl
        self.internal_have_visited = internal_have_visited
        self.external_links_to_crawl = external_links_to_crawl
        self.external_have_visited = external_have_visited

    def run(self):
        print(f"Web crawler worker {id(self)} is running")
        while True:
            link: str
            is_internal_link: bool
            try:
                # In this part of the code we create a global lock on accessing link queues so that no two threads will
                # check the same link. A secondary "priority" lock ensures that threads are awaken such that the program
                # is making a maximum number of network requests at any given moment.

                # PRIORITY UNLOCK ###################
                self.priority_unlock.acquire()      # Gets highest priority
                self.enqueue_lock.acquire()         #
                self.priority_unlock.release()      #
                #####################################

                try:
                    if len(self.internal_links_to_crawl) != 0:
                        link = self.internal_links_to_crawl.pop()
                        if link in self.internal_have_visited:
                            continue
                        node = WebpageNode(url=link, base_url=self.base_url)
                        self.internal_have_visited.append(node)

                        print(f"Visited {len(self.internal_have_visited)} / "
                              f"{len(self.internal_have_visited) + len(self.internal_links_to_crawl)} internal pages "
                              f"{len(self.external_have_visited)} / "
                              f"{len(self.external_have_visited) + len(self.external_links_to_crawl)} external pages."
                              f"  node ({self.c_num}) is visiting [{node.url}].")
                    else:
                        print(f"InnerSiteCrawler ({self.c_num}) is rejoining the main thread")
                        break
                finally:
                    self.enqueue_lock.release()

                # Perform HTTP request on link
                node.get_site_data()
                if node.status_code == 600:
                    print(f"The url {node.url} cannot be reached. Trying again")
                    node.get_site_data()
                    if node.status_code == 600:
                        print(f"The url {node.url} cannot be reached")
                if node.status_code < 400:
                    ##### PRIORITY UNLOCK #################
                    self.enqueue_lock.acquire()           #
                    while self.priority_unlock.locked():  #
                        self.enqueue_lock.release()       #
                        time.sleep(.05)                   #
                        self.enqueue_lock.acquire()       #
                    #######################################
                    for link in node.get_internal_links():
                        if link not in self.internal_have_visited and link not in self.internal_links_to_crawl:
                            self.internal_links_to_crawl.append(link)
                    for link in node.get_external_links():
                        if link not in self.external_links_to_crawl:
                            self.external_links_to_crawl.append(link)
                    self.enqueue_lock.release()

            except Exception as e:
                raise e


