from collections import defaultdict, Counter
from urllib.parse import urlparse, urldefrag
from lxml import html
import re

class Page:
    def __init__(self, url, numWords):
        self.url = url
        self.numWords = numWords

    def __repr__(self):
        return f"Page({self.url}, {self.numWords})" 

class Report:
    unique_pages = set()
    longestPage = Page("", float('-inf'))
    commonWords = Counter()
    subdomains = defaultdict(int)

    # Taken from Default English stopwords list 
    # https://www.ranks.nl/stopwords
    stop_words = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
        "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
        "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
        "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
        "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
        "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
        "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not",
        "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
        "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's",
        "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
        "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
        "you've", "your", "yours", "yourself", "yourselves"
    }

    @classmethod
    def update_report(cls, resp):
        cls._add_unique_pages(resp.url)
        cls.add_subdomain(resp.url)

        words_count = cls.parse_words(cls._get_text_from_resp(resp))
        newPage = Page(resp.url, words_count)
        cls.update_longest_page(newPage)
          

    @classmethod
    def _add_unique_pages(cls, url):
        clean_url, _ = urldefrag(url)
        cls.unique_pages.add(clean_url)

    @classmethod
    def update_longest_page(cls, page):
        if page.numWords > cls.longestPage.numWords:
            cls.longestPage = page

    @classmethod
    def parse_words(cls, words_iter):
        count = 0
        pattern = re.compile(r"^[A-Za-z'-]+$")
        for word in words_iter:
            if word in cls.stop_words:
                continue
            elif not pattern.match(word):
                continue
            else:
                cls.commonWords[word] += 1
                count += 1

        return count
        
    @classmethod
    def add_subdomain(cls, url):
        url_obj = urlparse(url)
        if url_obj.hostname:
            cls.subdomains[url_obj.hostname.lower().strip()] += 1

    @classmethod
    def _get_text_from_resp(cls, resp):
        ignored_tags = {'script', 'style', 'noscript', 'head', 'meta', 'link', 'iframe', 'code', 'pre'}
        try:
            content_type = resp.raw_response.headers.get('Content-Type', '').lower()
            content_disp = resp.raw_response.headers.get('Content-Disposition', '').lower()
            if 'attachment' in content_disp or not content_type.startswith('text/html'):
                return []

            tree = html.fromstring(resp.raw_response.content.decode('utf-8', errors='ignore'))
            body = tree.find('body')

            if body is None:
                return []
            
            html.etree.strip_elements(body, *ignored_tags, with_tail=True)

            for text in body.itertext():
                text = text.strip()
                if text:
                    for word in text.split():
                        yield word.lower()

        except:
            return []
        
    @classmethod
    def write_report_to_file(cls, filename = "Logs/report_output.txt"):
        with open(filename, 'w', encoding = 'utf-8') as f:
            f.write("=========Unique Pages=========\n")
            f.write(str(len(cls.unique_pages)))
            f.write("\n============ Page=========\n")
            f.write(repr(cls.longestPage))
            f.write("\n=========50 Most Common Words=========\n")
            for key, value in cls.commonWords.most_common(50):
                f.write(f"{key}: {value}\n")
            f.write("=========Subdomains Found=========\n")
            for domain in sorted(cls.subdomains.keys()):
                f.write(f"{domain}, {cls.subdomains[domain]}\n")


        
