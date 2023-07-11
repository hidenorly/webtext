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



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web text extractor', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('pages', metavar='PAGE', type=str, nargs='+', help='Web pages')
    #parser.add_argument('-i', '--input', dest='inputPath', type=str, default='.', help='list.csv title,url,sameDomain true or false')
    #parser.add_argument('-d', '--diff', dest='diff', action='store_true', default=False, help='Specify if you want to list up new links')
    #parser.add_argument('-s', '--sameDomain', dest='sameDomain', action='store_true', default=False, help='Specify if you want to restrict in the same url')
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

    for aUrl in args.pages:
        data = WebLinkEnumerater.getMetaAndText(driver, aUrl)
        print( data )

    driver.quit()
    tempDriver.quit()

