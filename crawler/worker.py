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
        '''report_info stores information to print out for the report'''
        report_info = self.ReportInformation()
        '''visited_urls_count and visited_urls_hash store URLs to check for duplicate pages'''
        visited_urls_count = defaultdict(int)
        visited_urls_hash = dict()
        while True:
            skip_url = False
            max_redirects = 6
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            '''Check resp.status for redirect, and handle if it is between 301 and 308.'''
            while (301 <= resp.status <= 308):
                if max_redirects > 0:
                    next_url = resp.url
                    '''If next_url is not in allowed domains, skips to next URL in the frontier.
                    if it is allowed, downloads it and runs this loop again to check for redirect.'''
                    if ".ics.uci.edu" not in next_url:
                        if ".cs.uci.edu" not in next_url:
                            if ".informatics.uci.edu" not in next_url:
                                if ".stat.uci.edu" not in next_url:
                                    skip_url = True
                                    break

                    resp = download(next_url, self.config, self.logger)
                    self.logger.info(
                        f"Downloaded {next_url}, status <{resp.status}>, "
                        f"using cache {self.config.cache_server}.")
                    max_redirects -= 1
                else:
                    '''If the URL gets redirected more than 6 times, skip to the next URL in the frontier.'''
                    print(f"Error: Max redirects exceeded for URL: {tbd_url}")
                    self.frontier.mark_url_complete(tbd_url)
                    skip_url = True
                    break
                    
            '''If redirected URL not in allowed domains or if max_redirect is hit, skips to the next URL in frontier.'''
            if skip_url:
                time.sleep(self.config.time_delay)
                continue

            scraped_urls = scraper.scraper(tbd_url, resp, report_info, visited_urls_count, visited_urls_hash)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

        '''
        Print out the required information for the report, based on what is gather in report_info.

        #unique pages
        print("unique page count:", report_info.get_unique_page_count())
        #max words and the page with the max words
        print("page with max words:", report_info.get_max_words_url())
        print("page with max words #:", report_info.get_max_words())
        #sorting top 50 words while filtering out stopwords
        word_dict = report_info.get_word_frequency()
        stopwords = "www div http https a about above after again against all am an and any are aren t as at be because been before being below between both but by can't cannot could couldn did didn do does doesn doing don down during each few for from further had hadn has hasn have haven having he he d ll s her here hers herself him himself his how i m ve if in into is isn it its itself let me more most mustn my myself no nor not of off on once only or other ought our ours ourselves out over own same shan she should shouldn so some such than that the their theirs them themselves then there these they this those through to too under until up very was wasn we were weren what when where which while who whom why with won would wouldn you your yours yourself yourselves".split(" ")
        all_words = list(word_dict.keys())
        for word in stopwords:
            try:
                all_words.remove(word)
            except ValueError:
                pass

        all_words_sorted = sorted(all_words, key=(lambda x: (-word_dict[x], x)))

        print("top words:")
        for y in range(300):
            print("{}, {}".format(all_words_sorted[y], word_dict[all_words_sorted[y]]))

        # listing subdomains of ics.uci.edu
        print("all subdomains of ics.uci.edu:")
        all_subdomains = list(report_info.get_sub_domains_page_count().keys())
        all_subdomains_sorted = sorted(all_subdomains)
        for subdomain in all_subdomains_sorted:
            print("{}, {}".format(subdomain, report_info.get_sub_domains_page_count()[subdomain]))
        '''

    class ReportInformation():
        '''Stores all the information we need for our report'''
        def __init__(self):
            self.word_frequency = defaultdict(int) # dict holds (word, int)
            self.unique_pages = []
            self.unique_page_count = 0
            self.max_words = 0
            self.max_words_url = ""
            self.sub_domains_page_count = defaultdict(int) # dict holds (url, int)
            self.urls_failed_count = 0
            self.redirected_urls = {} # dict holds (from_url, to_url)

        '''Methods to store/retrieve above information'''
        def get_max_words(self):
            return self.max_words
        
        def get_max_words_url(self):
            return self.max_words_url
    
        def get_word_frequency(self):
            return self.word_frequency
        
        def increment_word_frequency(self, word):
            self.word_frequency[word] += 1

        def get_unique_page_count(self):
            return self.unique_page_count
        
        def increment_unique_page_count(self):
            self.unique_page_count += 1
        
        def add_unique_page(self, url):
            self.unique_pages.append(url)

        def get_unique_pages(self):
            return self.unique_pages

        def set_max_words_url(self, url, word_count):
            self.max_words_url = url
            self.max_words = word_count

        def increment_sub_domains_page_count(self, url):
            self.sub_domains_page_count[url] += 1    

        def get_sub_domains_page_count(self):
            return self.sub_domains_page_count
            
