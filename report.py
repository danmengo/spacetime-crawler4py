from collections import defaultdict, Counter
from scraper import _defragment
from urllib.parse import urlparse

class Page:
    def __init__(self, url, numWords):
        self.url = url
        self.numWords = numWords

class Report:

    def __init__(self):
        self.unique_pages = set()
        self.longestPage = Page("", float('-inf'))
        self.commonWords = Counter()
        self.subdomains = defaultdict(int)

    def add_unique_pages(self, url):
        self.unique_pages.add(_defragment(url))

    def update_longest_page(self, page):
        if page.numWords > self.longestPage.numWords:
            self.longestPage = page
    
    def add_common_words(self, resp):
        # self.commonWords.update(words_counter)
        pass

    def add_subdomain(self, url):
        url = urlparse(url)
        if url.hostname:
            self.subdomains[url.hostname] += 1
