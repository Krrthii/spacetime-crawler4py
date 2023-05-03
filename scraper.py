import re
from urllib.parse import urlparse, urljoin
from lxml import html, etree
from collections import defaultdict

'''
Function to return all valid links from a webpage inside a list
This function is called later in the worker.py file in order to pass
the collection of valid urls to frontier.py in order for program to scrape text from the links
'''
def scraper(url, resp, report_info, visited_urls_count, visited_urls_hash):
    '''
    Call the `extract_next_links` function to extract all links from the webpage as strings.
    Then, create a new list containing only links that meet certain criteria 
    '''
    links = extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash)
    return [link for link in links if is_valid(link)]

'''
Function is called from scraper function of scraper.py in order 
to extract links from the given webpage's content and return the links in a list
'''
def extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!

    '''
    Call the `check_similarity` function which checks if the content of the webpage at the
    given URL is too similar to any previously visited webpages.
    If the content is too similar to a previously visited webpage,
    return an empty list
    If the content is different enough, continue to
    extract the links from the webpage
    '''
    if not check_similarity(url, resp, visited_urls_hash):
        return list()

    '''
    Create empty list to hold extracted links.
    Then check if the response status is 200 (OK) and if so,
    proceed to extract links from the webpage's content,
    remove fragments from URLs, and increment the unique page count
    in the `report_info` object.
    If response status is not 200, return an empty list.
    '''
    links = []
    try:
        if resp.status == 200:
            #parse page, store stuff for report, find URLs, remove fragments # from URLs
            # code below extracts links from the webpage
            # TO-DO: we still need to handle fragments (DONE, NEEDS TESTING)
            # TO-DO: test getting content
            # incrementing unique_page_count in report_info
            '''
            Increment count of visited urls
            for the current url in the `visited_urls_count` dictionary
            in the report_info object
            '''
            report_info.increment_unique_page_count()
            report_info.add_unique_page(url)

            '''
            Parse the current url using the `urlparse()` method
            of the urllib library, remove the query part, and increment
            the count of the visited url in the `visited_urls_count` dictionary
            '''
            parsed_url = urlparse(url)
            url_without_query = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            visited_urls_count[url_without_query] += 1
            '''
            If current url is a subdomain of ics.uci.edu, increment the count 
            of subdomains in the `report_info` object
            '''
            if ("ics.uci.edu" in parsed_url.netloc):
                sub_domain = parsed_url.scheme + "://" + parsed_url.netloc
                report_info.increment_sub_domains_page_count(sub_domain)
            '''
            Extract the content of the webpage using
            the `resp.raw_response.content` attribute and convert it into
            an HTML string
            '''
            html_string = html.fromstring(resp.raw_response.content)
            '''
            Calculate the hash value of the webpage's content and store it
            in the `visited_urls_hash` dictionary
            '''
            url_content = html_string.text_content()
            visited_urls_hash[url] = hash(url_content)
            '''
            Extract all links from the HTML string and iterate through them
            '''
            full_links = list(html_string.iterlinks())
            '''
            For each link, remove the fragment part and parse the new url.
            Check if the new url has been crawled through less than 11 times,
            and if it doesn't contain another URL inside.
            If both conditions are true, append the new URL to the `links` list
            '''
            for y in full_links:
                if y != "#" and y != "/":
                    new_url = urljoin(url, y[2])
                    fragment_index = new_url.find('#')
                    if fragment_index != -1:
                        new_url = new_url[:fragment_index]
                    parsed_new_url = urlparse(url)
                    new_url_without_query = parsed_new_url.scheme + "://" + parsed_new_url.netloc + parsed_new_url.path
                    # Only adds URL to frontier if it has been crawled through under 11 times.
                    if visited_urls_count[new_url_without_query] < 11:
                        # Check if the url does not have another URL inside it
                        if ("https" not in parsed_new_url.path) and ("http" not in parsed_new_url.path):
                            links.append(new_url)


            # TO-DO: get text content of every webpage crawled (worry about low-info checking later)
            # TO-DO: done: keep some global counter of unique pages found, page with max_words (and a max_words count),
            #        done: a default_dict to count words for the top 50 most common words (ignore English stop words),
            #        a default_dict with each subdomain of ics.uci.edu with a counter of # of unique pages.
            # PLAN: add a new class in worker.py to store all the above, with methods to modify all the above. 
            #counts the # of words in current URL
            url_word_count = 0

            '''
            Extract the text content of the webpage and split it into a list of words
            Iterate trhough the words and check if they are not numeric and have more than one character.
            Increment the word frequency in the `report_info` object for each valid word and update the URL word count
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
        
            '''
            Compare the URL word count with the current maximum word count.
            If the URL word count is greater, update the maximum word count 
            and the corresponding URL in the `report_info` object.
            Then return the `links` list containing the extracted and filtered links
            '''
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
        '''
        Set similarity threshold to 0.0
        '''
        threshold = 0.0
        '''
        Extract the content of the webpage from `resp` object
        using the `content` attribute and the `html` module from the `lxml` library
        Then, convert content to text format using `text_content()` method
        '''
        content = resp.raw_response.content
        parsed_content = html.fromstring(content)
        url_content = parsed_content.text_content()

        '''
        Iterate trhough the values of `visted_urls_hash` which is a dictionary
        containing the hash values of previously visited webpages and calculate
        the absolute difference between the hash of the current webpage's content
        and hash of each previously visited webpage's content
        '''
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
        '''
        ParserError happens when document is empty.
        The function catches and handles two exceptions
        both of which indicate that the webpage content is not parsable
        or is missing.
        In this case, function returns False
        '''
    except etree.ParserError:
        return False
    except AttributeError:
        return False

'''
Function called from the scraper function of scraper.py in order to 
determine whether a URL should be crawled
Returns True if the URL should be crawled or False if not
'''
def is_valid(url):
    '''
    If TypeError happens when the URL could not be parsed properly, return False
    If ValueError happens when "uci" or "." is not found in the URL, return False
    Else, proceed
    '''
    try:
        '''
        Parse the URL by using the `urlparse()` function from the urllib library and check
        if the parsed URL's pattern contains either "http" or "https".
        If not return False.
        '''
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        
        '''
        Check for traps with infinite repeating paths.
        Split the parsed URLs path by the "/" character and count the
        occurances of each path segment using path_count, a default dictionary
        If any path segment appears more than once, return False
        '''
        path_count = defaultdict(int)
        path_words = parsed.path.split("/")
        for x in path_words:
            path_count[x] += 1
        for count in path_count.values():
            if count > 1:
                return False

        '''
        Check if the parsed URL's netloc includes ".[ics, cs, informatics, stat].uci.edu"
        Split the netloc by the "." character and find the index of "uci" in the resulting list
        If the element before "uci" is not in the set of valid subdomains, return False.
        '''
        # parsed.netloc must include ".[ics, cs, informatics, stat].uci.edu"
        split_netloc = parsed.netloc.split(".")
        affiliate_index = split_netloc.index("uci")
        if split_netloc[affiliate_index-1] not in set(["ics", "cs", "informatics", "stat"]):
            return False
        
        '''
        Check if the element after "uci" is "edu".
        If not, return False.
        # Removed the / at the end of "edu/". Since / and # are not part of netloc, "edu" will have nothing after it when you parse the URL.
        '''
        if split_netloc[affiliate_index+1] != "edu":  #edu/, edu#, edu ?? change to regex matching
            return False
        
        ## TO-DO:avoid traps!!: 
        ##       infinite redirections: keep list of visited links
        ##
        ##       duplicates/near-duplicates(fingerprint algorithm using sim-hash)
        ##          # define a similarity threshold
        ##          duplicate = any(abs(hash(content)) - hash(visitedContent) < threshold for vContent in visitedContent)
        ##          if false: add page to list of visited content
        
        '''
        Use regex to match the URL's path against a list of excluded file types
        such as images and executables.
        If the path matches the regular expression, return False.
        Otherwise, return True.
        '''
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
        print ("TypeError for ", parsed)
        #if URL could not be parsed correctly, return False
        return False
    except ValueError:
        #print("ValueError for {}, \"uci\" not found in URL".format(parsed))
        return False
