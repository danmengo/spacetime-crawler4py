from collections import defaultdict, Counter
from scraper import _defragment
from urllib.parse import urlparse

class Page:
    def __init__(self, url, numWords):
        self.url = url
        self.numWords = numWords

class Report:
    unique_pages = set()
    longestPage = Page("", float('-inf'))
    commonWords = Counter()
    subdomains = defaultdict(int)

    @classmethod
    def add_unique_pages(cls, url):
        cls.unique_pages.add(_defragment(url))

    @classmethod
    def update_longest_page(cls, page):
        if page.numWords > cls.longestPage.numWords:
            cls.longestPage = page

    @classmethod
    def add_common_words(cls, words_counter):
        cls.commonWords.update(words_counter)

    @classmethod
    def add_subdomain(cls, url):
        url_obj = urlparse(url)
        if url_obj.hostname:
            cls.subdomains[url_obj.hostname] += 1
