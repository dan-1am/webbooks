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
        sleep(1)
        link = self.browser.find_element(By.LINK_TEXT, 'Authors list')
        link.click()
        sleep(3)

if __name__ == "__main__":
    unittest.main()
