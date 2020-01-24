from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from abc import ABCMeta, abstractmethod
import os, sys, time

class seleniumDriver(object):
    @abstractmethod
    def initDriver(self):
        timeout = 20
        try:
            self.driver = webdriver.Firefox(executable_path=self.driver)
            self.driver.set_page_load_timeout(timeout)
        except Exception as e:
            print('unkown driver error:  {0}'.format(e))
            self.closeDriver()
            return 1
        else:
            return None
    
    def closeDriver(self):
        self.driver.close()

class getRawHtmlFromSelenium(seleniumDriver):
    def __init__(self,driver):
        self.driver = driver
        self.price_time = time.strftime('%I%M')
        self.price_date = time.strftime('%Y%m%d')
        self.error_code = 1

    def getUrl(self, url):
        try:
            self.driver.get(url)
        except TimeoutException:
            self.error_code = 2
        except Exception as message:
            self.error_code, self.error_details = 3, message
        else:
            self.error_code = 0
            return self.driver.page_source
        finally:
            self.closeDriver()

    def getData(self, url):
        url += '?q=&hPP=1000&p=0'
        if not self.initDriver():
            return self.getUrl(url)

