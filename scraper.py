import re
from urllib.parse import urlparse, urljoin
from lxml import html, etree
from collections import defaultdict

'''Returns all the links found in the given URL's webpage.
Checks each link and returns the ones that are valid.'''
def scraper(url, resp, report_info, visited_urls_count, visited_urls_hash):
    links = extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash)
    return [link for link in links if is_valid(link)]


'''Given a URL and response, extracts all the links found in the URL and stores information for the report.'''
def extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash):
    links = []
    try:
        if resp.status == 200:
            '''Increment count of unique_pages and adds the current url in the `unique_pages`
            dictionary in the report_info object'''
            report_info.increment_unique_page_count()
            report_info.add_unique_page(url)

            if not check_similarity(url, resp, visited_urls_hash):
                return list()

            '''Parse the current url using the `urlparse()` method of the urllib library, remove the query part, 
            and increment the count of the visited url in the `visited_urls_count` dictionary'''
            parsed_url = urlparse(url)
            url_without_query = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            visited_urls_count[url_without_query] += 1

            '''If current url is a subdomain of ics.uci.edu, increment the count of that subdomain in the report_info object'''
            if ("ics.uci.edu" in parsed_url.netloc):
                sub_domain = parsed_url.scheme + "://" + parsed_url.netloc
                report_info.increment_sub_domains_page_count(sub_domain)
                
            html_string = html.fromstring(resp.raw_response.content)
            '''Calculate the hash value of the webpage's content and store it in the `visited_urls_hash` dictionary'''
            url_content = html_string.text_content()
            visited_urls_hash[url] = hash(url_content)
            '''Extract all links from the HTML string and iterate through them'''
            full_links = list(html_string.iterlinks())
            for y in full_links:
                if y != "#" and y != "/":
                    new_url = urljoin(url, y[2])
                    '''Remove fragment from URL if it exists'''
                    fragment_index = new_url.find('#')
                    if fragment_index != -1:
                        new_url = new_url[:fragment_index]
                    parsed_new_url = urlparse(url)
                    new_url_without_query = parsed_new_url.scheme + "://" + parsed_new_url.netloc + parsed_new_url.path
                    '''only adds URL to frontier if it has been crawled through under 11 times and there is not a URL inside the URL'''
                    if visited_urls_count[new_url_without_query] < 11:
                        if ("https" not in parsed_new_url.path) and ("http" not in parsed_new_url.path):
                            links.append(new_url)


            url_word_count = 0

            '''Extract the text content of the webpage. Iterate through the words and increment the
            number if times that word is found in all webpages (word_frequency) and the number of words 
            in the current URL (url_word_count).
            '''
            site_text_list = html_string.xpath('//p')
            # counts words in the URL and adds each word into the word_frequency dict in ReportInformation().
            for body in site_text_list:
                for word in re.split('[^a-zA-z0-9]+', body.text_content()):
                    lowercase_word = word.lower()
                    if lowercase_word != "":
                        if len(lowercase_word) > 1:
                            if not lowercase_word.isnumeric():
                                report_info.increment_word_frequency(lowercase_word)
                                url_word_count += 1
        
            '''If the url_word_count is higher than the current max number of words in a URL, update it'''
            if url_word_count > report_info.get_max_words():
                report_info.set_max_words_url(url, url_word_count)
        return links
    except:
        return list()

'''
Function that checks whether the content of a webpage located at the given url 
is similar or nearly identical to any previously visited webpages, based 
on a similarity threshold.
'''
def check_similarity(url, resp, visited_urls_hash):
    try:
        threshold = 0.0
        content = resp.raw_response.content
        parsed_content = html.fromstring(content)
        url_content = parsed_content.text_content()
        '''
        If the absolute difference is less than or equal to the similarity threshold,
        function returns False which shows that the current webpage is too similar
        to a previously visited webpage
        '''
        for page_hash in visited_urls_hash.values():
            is_similar = abs(hash(url_content) - page_hash)
            if (is_similar <= threshold):
                return False
        return True

    except etree.ParserError:
        '''If the page content is empty, return False'''
        return False
    except AttributeError:
        '''If the hash cannot be retrieved, return False'''
        return False

'''Function called from the scraper function of scraper.py in order to 
determine whether a URL should be crawled
Returns True if the URL should be crawled or False if not'''
def is_valid(url):
    try:
        '''check if the scheme contains http or https'''
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        
        '''Check for traps with infinite repeating paths.
        Split the parsed URLs path by the "/" character and count the
        occurances of each path segment using path_count, a default dictionary
        If any path segment appears more than once, return False'''
        path_count = defaultdict(int)
        path_words = parsed.path.split("/")
        for x in path_words:
            path_count[x] += 1
        for count in path_count.values():
            if count > 1:
                return False

        '''Check if the parsed URL's netloc includes ".[ics, cs, informatics, stat].uci.edu"
        Split the netloc by the "." character and find the index of "uci" in the resulting list
        If the element before "uci" is not in the set of valid subdomains, return False.'''
        # parsed.netloc must include ".[ics, cs, informatics, stat].uci.edu"
        split_netloc = parsed.netloc.split(".")
        affiliate_index = split_netloc.index("uci")
        if split_netloc[affiliate_index-1] not in set(["ics", "cs", "informatics", "stat"]):
            return False
        
        '''Check if the element after "uci" is "edu".
        If not, return False.'''
        if split_netloc[affiliate_index+1] != "edu":
            return False
        
        
        '''Use regex to match the URL's path against a list of excluded file typessuch as images and executables.
        If the path matches the regular expression, return False. Otherwise, return True.'''
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        '''If the URL could not be parsed correctly, return False'''
        print ("TypeError for ", parsed)
        return False
    except ValueError:
        '''If 'uci' could not be found in the netloc, return False'''
        return False
