import config
from threading import Thread, Lock
from webpageNode import WebpageNode
from typing import Deque, List


def make_appendage_crawlers(num_threads):
    enqueue_lock = Lock()
    crawler_threads = []
    for i in range(num_threads):
        crawler = AppendageCrawler(enqueue_lock=enqueue_lock, c_num=i)
        crawler_threads.append(crawler)
        crawler.start()
    return crawler_threads


class AppendageCrawler(Thread):
    def __init__(self, c_num, enqueue_lock,
                 external_links_to_crawl: Deque[str] = config.external_links_to_crawl,
                 external_sites_visited: List[WebpageNode] = config.external_have_visited):
        Thread.__init__(self)
        self.c_num = c_num
        self.enqueue_lock = enqueue_lock
        self.external_links_to_crawl = external_links_to_crawl
        self.external_sites_visited = external_sites_visited

    def run(self):
        while len(self.external_links_to_crawl) > 0:
            self.enqueue_lock.acquire()
            try:
                link = self.external_links_to_crawl.pop()
                if link in self.external_sites_visited:
                    continue
                print(f"Visited {len(self.external_sites_visited)} / "
                      f"{len(self.external_sites_visited) + len(self.external_links_to_crawl)} external pages. "
                      f"  node ({self.c_num}) is visiting [{link}]."
                      )
                node = WebpageNode(url=link)
                self.external_sites_visited.append(node)
            finally:
                self.enqueue_lock.release()

            node.get_site_data()

            if node.status_code == 600:
                print(f"The url {node.url} cannot be reached. Trying again")
                node.get_site_data()
                if node.status_code == 600:
                    print(f"The url {node.url} cannot be reached")

        print(f"AppendageCrawler ({self.c_num}) is rejoining the main thread")