from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest
import time
import re


class TestSe404Page(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_404(self):
        driver = self.driver
        # Get a page which doesn't exist.
        driver.get(self.base_url + "nonsense-page")
        # Assert that the page contains the phrase
        # "The URL you requested was not found." in th body
        self.assertRegexpMatches(
            driver.find_element_by_css_selector("BODY").text,
            r".*The URL you requested was not found.*")

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
