from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from collections import defaultdict


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)


    def run(self):
        report_info = self.ReportInformation()
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp, report_info)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        # report info here? idk
        print("unique page count:", report_info.get_unique_page_count)
        print("page with max words:", report_info.get_max_words_url)
        print("page with max words #:", report_info.get_max_words)
        #sorting top 50 words
        word_dict = report_info.get_word_frequency()
        all_words = list(word_dict)
        all_words_sorted = sorted(all_words, key=(lambda x: (-word_dict[x], x)))

        print("top 50 words:")
        for y in range(50):
            print(all_words_sorted[y])

    class ReportInformation():
        #stores everything we need for our report
        def __init__(self):
            self.word_frequency = defaultdict(int) # dict holds (word, int)
            #self.unique_pages = []
            self.unique_page_count = 0
            self.max_words = 0
            self.max_words_url = ""
            self.sub_domains_page_count = defaultdict(int) # dict holds (url, int)

        #methods to store/retrieve above information
        def get_max_words(self):
            return self.max_words
        
        def get_max_words_url(self):
            return self.max_words_url
    
        def get_word_frequency(self):
            return self.word_frequency
        
        def increment_word_frequency(self, word):
            self.word_frequency[word] += 1

        def get_unique_page_count(self):
            return self.unique_page_count()
        
        def increment_unique_page_count(self):
            self.unique_page_count += 1
        
        def set_max_words_url(self, url, word_count):
            self.max_words_url = url
            self.max_words = word_count

        def increment_sub_domains_page_count(self, url):
            self.sub_domains_page_count[url] += 1    