from time import sleep
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By



class LibraryTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def testLibrary(self):
        self.browser.get("http://localhost:8001")
        self.assertIn("Library", self.browser.title)
        link = self.browser.find_element(By.LINK_TEXT, 'Authors list')
        link.click()

        self.assertIn("Authors", self.browser.title)
        authors = self.browser.find_element(By.ID, 'author_list')
        first_author = authors.find_element(By.TAG_NAME, 'a')
        first_author.click()

        link = self.browser.find_element(By.LINK_TEXT, '[Read]')
        link.click()
#        sleep(1)

if __name__ == "__main__":
    unittest.main()
