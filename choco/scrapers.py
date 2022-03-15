"""
"""
import os
import re
import csv
import logging
import requests
from time import sleep
from random import randint

from urllib.request import urljoin
from bs4 import BeautifulSoup

DEBUG = True
MAX_PAGES = 300
FORUM_BASE_URL = "https://www.irealb.com/forums/"

logger = logging.getLogger("choco.scrapers")
log = print if DEBUG else logger.info


def request(url, headers=None, timeout=None, min_wait=0, max_wait=0):

    max_wait = min_wait + 1 if max_wait <= min_wait else max_wait
    sleep(randint(min_wait, max_wait))  # wait before request
    page = requests.get(url, headers=headers, timeout=timeout)

    return page


def write_chart_data(fname, results):

    header = ["name", 'songs', "ireal_charts"]
    with open(fname+'.csv', 'w') as chart_file:
        write = csv.writer(chart_file)
        write.writerow(header)
        write.writerows(results)


def process_forum_page(page_url, out_dir, wait=(1,1)):
    """
    Find threads in a forum page and process them separately to retrieve
    iReal charts of playlists and single tracks. Pinned posts are not repeated.
    """
    history = set()  # forum pages processed so far (to avoid re-visits)

    for i in range(1, MAX_PAGES):

        full_page_url = page_url + f"/page{i}"
        log(f"Processing forum page {i}: {full_page_url}")
        # Retrieve the current forum page to extract all threads found
        page = request(full_page_url, min_wait=wait[0], max_wait=wait[1])
        tree = BeautifulSoup(page.content, features="lxml")
        threads = tree.findAll("a", attrs={"class": "title"})

        for j, thread in enumerate(threads):
            thread_name = thread.text  # adapted later to be used as file name
            thread_url = urljoin(FORUM_BASE_URL, thread.get("href"))
            if thread_url not in history:  # avoid pinned or sticky threads
                log(f"Retrieving charts for thread {j}: {thread_name}")
                thread_charts = process_thread_page(thread_url, wait)
                # Writing everything in a thread-specific CSV file
                file_name = thread_name.replace('/', '-').lower()  # XXX
                write_chart_data(os.path.join(out_dir, file_name), thread_charts)
                history.add(thread_url)  # keep here to avoid inconsistencies
        
        if not tree.findAll("img", attrs={"alt": "Next"}): break


def process_thread_page(thread_url, wait=(1,1)):
    """
    Retrieve all ireal-pro charts from a given forum page. Iteratively, inspects
    all pages in the thread and accumulate results (no checks are performed).
    """
    page_charts = []

    for i in range(1, MAX_PAGES):
        new_url = thread_url + f"/page{i}"
        log(f"Processing thread page {new_url}")
        page = request(new_url, min_wait=wait[0], max_wait=wait[1])
        tree = BeautifulSoup(page.content, features="lxml")
        # Update the current page chart and check termination
        page_charts = page_charts + extract_ireal_charts(tree)
        if not tree.findAll("img", attrs={"alt": "Next"}): break

    return page_charts


def extract_ireal_charts(tree):

    ireal_links = []
    num_charts = lambda url: len(re.findall("===", url))
    for link in tree.findAll("a", attrs={"href": re.compile("^irealb://")}):
        ireal_chart = link.get("href")  # the actual encoded chord annotation
        ireal_links.append((link.text, num_charts(ireal_chart), ireal_chart))
    
    return ireal_links