import unittest
from scraper import defragment
from scraper import _valid_domain

class TestScraper(unittest.TestCase):

    def testDeFragmentation(self):
        self.assertEqual(defragment('https://example.com/page.html#section1'), 'https://example.com/page.html')
        self.assertEqual(defragment('https://example.com/page.html?name=Bob#section1'), 'https://example.com/page.html?name=Bob')
        self.assertEqual(defragment('https://example.com/page.html'), 'https://example.com/page.html')

    def testValidDomain(self):
        self.assertEqual(True, _valid_domain('https://www.ics.uci.edu'))
        self.assertEqual(True, _valid_domain('https://www.ics.UCI.edu'))
        self.assertEqual(True, _valid_domain('https://www.ics.uci.edu/test#1'))
        self.assertEqual(False, _valid_domain('https://www.uci.edu/test#1'))


if __name__ == "__main__":
    unittest.main()