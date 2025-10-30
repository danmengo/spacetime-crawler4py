from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            # Pre-check for paths we know we want to skip
            if scraper._is_low_value_by_path(tbd_url):
                self.logger.info(f"Skipping known low-value path without download: {tbd_url}")
                self.frontier.mark_url_complete(tbd_url)
                continue

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            # Get links but check if page was marked as login/restricted
            scraped_urls = scraper.scraper(tbd_url, resp)
            
            # If this was a login/restricted page, mark it complete and move on
            # without processing its URLs (which are likely auth-related variants)
            if not scraped_urls and scraper._is_login_page(resp):
                self.logger.info(f"Marking restricted page as complete without processing links: {tbd_url}")
                self.frontier.mark_url_complete(tbd_url)
                continue

            # Process valid URLs from non-restricted pages
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
