import unittest
from scraper import defragment

class TestScraper(unittest.TestCase):

    def testDeFragmentation(self):
        self.assertEqual(defragment('https://example.com/page.html#section1'), 'https://example.com/page.html')
        self.assertEqual(defragment('https://example.com/page.html?name=Bob#section1'), 'https://example.com/page.html?name=Bob')
        self.assertEqual(defragment('https://example.com/page.html'), 'https://example.com/page.html')


if __name__ == "__main__":
    unittest.main()