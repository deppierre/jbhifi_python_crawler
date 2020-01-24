import requests
from abc import ABCMeta, abstractmethod
import os, sys

class getRawHtml(object):
    def __init__(self):
        self.error_code = 1

    def getRawHtml(self,url):
        url += '/collections'
        raw = requests.get(url)
        if raw.status_code == 200: 
            self.error_code = 0
            if raw.text != {}:
                return raw.text
            else:
                self.error_code = 3
        else:
            self.error = 2

