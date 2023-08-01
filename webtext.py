#!/usr/bin/env python3
# coding: utf-8

#   Copyright 2023 hidenorly
#
#   Licensed baseUrl the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed baseUrl the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations baseUrl the License.

import argparse
import os
import re
import string
import json
from urllib.parse import urljoin
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By


class WebLinkEnumerater:
    CONTROL_CHR_PATTERN = re.compile('[\x00-\x1f\x7f]')

    @staticmethod
    def cleanupString(buf):
        buf = str(buf).strip()
        buf = WebLinkEnumerater.CONTROL_CHR_PATTERN.sub(' ', buf)
        buf = buf.encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
        return buf

    @staticmethod
    def isSameDomain(url1, url2, baseUrl=""):
        isSame = urlparse(url1).netloc == urlparse(url2).netloc
        isbaseUrl =  ( (baseUrl=="") or url2.startswith(baseUrl) )
        return isSame and isbaseUrl

    @staticmethod
    def getMetaAndText(driver, url):
        result = {}
        try:
            driver.get(url)
        except:
            pass

        try:
            result["title"] = driver.title
        except:
            pass

        try:
            result["description"] = WebLinkEnumerater.cleanupString(driver.find_element('css selector', 'meta[name="description"]').get_attribute('content'))
        except:
            pass

        try:
            result["keywords"] = WebLinkEnumerater.cleanupString(driver.find_element('css selector', 'meta[name="keywords"]').get_attribute('content'))
        except:
            pass

        try:
            aTags = driver.find_elements('css selector', 'a')
            result["aTags"] = set()
            for aTag in aTags:
                result["aTags"].add(WebLinkEnumerater.cleanupString(aTag.text))
        except:
            pass

        try:
            imgTags = driver.find_elements('tag name', 'img')
            result["imgTags"] = set()
            for imgTag in imgTags:
                altAttribute = imgTag.get_attribute('alt')
                if altAttribute:
                    result["imgTags"].add(WebLinkEnumerater.cleanupString(altAttribute))
                text = WebLinkEnumerater.cleanupString(imgTag.text).strip()
                if text:
                    result["imgTags"].add(text)
        except:
            pass

        try:
            result["body"] = WebLinkEnumerater.cleanupString(driver.find_element('tag name', 'body').text)
        except:
            pass

        return result

    @staticmethod
    def getLinksByFactor(driver, pageUrl, byFactor=By.TAG_NAME, element='a', sameDomain=False, onlyTextExists=False):
        result = {}

        try:
            tag_name_elements = driver.find_elements(byFactor, element)
            for element in tag_name_elements:
                url = element.get_attribute('href')
                title = str(element.text).strip()
                title = WebLinkEnumerater.cleanupString(title)
                if url:
                    if not sameDomain or WebLinkEnumerater.isSameDomain(pageUrl, url, pageUrl):
                        if not onlyTextExists or title:
                            result[url] = title
        except Exception as e: #except NoSuchElementException:
            pass

        return result

    @staticmethod
    def getLinks(driver, url, isSameDomain, onlyTextExists):
        result = {}

        if isVerbose:
            print(url)
        try:
            driver.get(url)
            result = WebLinkEnumerater.getLinksByFactor(driver, url, By.TAG_NAME, 'a', isSameDomain, onlyTextExists)
            result.update( WebLinkEnumerater.getLinksByFactor(driver, url, By.CSS_SELECTOR, 'a.post-link', isSameDomain, onlyTextExists) )
        except Exception as e: #except NoSuchElementException:
            print("Error at "+url)

        return result

    @staticmethod
    def getNewLinks(prevUrlList, newUrlList, stopIfExist = True):
        result = {}
        isFoundNewOne = False
        for aUrl, aTitle in newUrlList.items():
            found = aUrl in prevUrlList
            if not found:
                result[aUrl] = aTitle
                isFoundNewOne = True
            if isFoundNewOne and stopIfExist and found:
                break
        return result


class Reporter:
    def __init__(self, output = None):
        self.stream = None
        if output:
            self.stream = open(output, "a", encoding="utf-8")

    def _print(self, data):
        if self.stream:
            self.stream.write( str(data) + "\n" )
        else:
            print( str(data) )

    def print(self, data):
        for key, value in data.items():
            self._print( str(key) + ":" + str(value) )

    def printHeader(self):
        pass

    def close(self):
        if self.stream:
            self.stream.close()
        self.stream = None

    def __del__(self):
        if self.stream:
            self.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web text extractor', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('pages', metavar='PAGE', type=str, nargs='+', help='Web pages')
    args = parser.parse_args()

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    tempDriver = webdriver.Chrome(options=options)
    userAgent = tempDriver.execute_script("return navigator.userAgent")
    userAgent = userAgent.replace("headless", "")
    userAgent = userAgent.replace("Headless", "")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument(f"user-agent={userAgent}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)


    reporter = Reporter
    reporter = reporter()

    reporter.printHeader()

    for aUrl in args.pages:
        data = WebLinkEnumerater.getMetaAndText(driver, aUrl)
        reporter.print( data )

    reporter.close()
    driver.quit()
    tempDriver.quit()

