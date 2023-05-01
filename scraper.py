import re
from urllib.parse import urlparse, urljoin
from lxml import html
from collections import defaultdict

def scraper(url, resp, report_info, visited_urls_count, visited_urls_hash, max_redirects):
    links = extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash, max_redirects)
    #print(links) #DEBUG REMOVE THIS LATER
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp, report_info, visited_urls_count, visited_urls_hash, max_redirects):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if not check_similarity(url, resp, visited_urls_hash):
        return list()

    links = []
    try:
        if resp.status == 200:
            #parse page, store stuff for report, find URLs, remove fragments # from URLs
            
            # code below extracts links from the webpage
            # TO-DO: we still need to handle fragments (DONE, NEEDS TESTING)
            # TO-DO: test getting content
            
            # incrementing unique_page_count in report_info
            report_info.increment_unique_page_count()

            #add current url increment to visited_urls
            parsed_url = urlparse(url)
            url_without_query = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            visited_urls_count[url_without_query] += 1
            # check if url is a subdomain of ics.uci.edu (for report)
            if ("ics.uci.edu" in parsed_url.netloc):
                sub_domain = parsed_url.scheme + "://" + parsed_url.netloc
                report_info.increment_sub_domains_page_count(sub_domain)

            html_string = html.fromstring(resp.raw_response.content)
            # hashing webpage and storing it
            url_content = html_string.text_content()
            visited_urls_hash[url] = hash(url_content)
            # getting a list of links found in the webpage
            full_links = list(html_string.iterlinks())
            for y in full_links:
                if y != "#" and y != "/":
                    new_url = urljoin(url, y[2])
                    fragment_index = new_url.find('#')
                    if fragment_index != -1:
                        new_url = new_url[:fragment_index]
                    parsed_new_url = urlparse(url)
                    new_url_without_query = parsed_new_url.scheme + "://" + parsed_new_url.netloc + parsed_new_url.path
                    # Only adds URL to frontier if it has been crawled through under 20 times.
                    if visited_urls_count[new_url_without_query] < 21:
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

            site_text_list = html_string.xpath('//p')
            # counts words in the URL and adds each word into the word_frequency dict in ReportInformation().
            for body in site_text_list:
                for word in re.split('[^a-zA-z0-9]+', body.text_content()):
                    if word != "":
                        report_info.increment_word_frequency(word)
                        url_word_count += 1
        
            # Compares the # of words in this URL to the current max.
            # Replaces the max_url and the max_words if the current URL has more words.
            if url_word_count > report_info.get_max_words():
                report_info.set_max_words_url(url, url_word_count)

            
            """
            links = html.fromstring(resp.raw_response.content)
            links = re.findall(r'https://+', html.fromstring(resp.raw_response.content))
            for x in range(len(links)):
                print(x)
                fragment_index = links[x].find('#')
                if fragment_index != -1:
                    links[x] = links[x][:fragment_index]
            """
        
        # new code for redirection, handled in report as well
        #this means there is a redirection
        #set max_redirects and keep redirection count
        """
        elif (resp.status == 302):
            if max_redirects > 0:
                next_url = resp.headers.get("location")
                report_info.add_redirected_url(url, new_url)
                links.append(next_url)
                extract_next_links(next_url, requests.get(next_url), report_info, visited_urls_count, visited_urls_hash, max_redirects-1)
            else:
                print("Max redirects exceeded for URL: ", url)
                report_info.log_error(url, "Max redirects exceeded")
                report_info.increment_urls_failed()
        """
                

        return links
    except:
        return list()

def check_similarity(url, resp, visited_urls_hash):
    #checks for duplicates and near-duplicates
    #find similarity score, compare with similarity threshold
    #return true/false if pass similarity test
    try:
        threshold = 0.0

        # first check if there is no content on the page
        content = resp.raw_response.content
        if not content:
            return False

        parsed_content = html.fromstring(content)
        url_content = parsed_content.text_content()

        for page_hash in visited_urls_hash.values():
            is_similar = abs(hash(url_content) - page_hash)
            if (is_similar < threshold):
                return False
            
        return True
    except AttributeError:
        return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # not valid if file is empty
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        
        #check for traps with infinite repeating paths
        path_count = defaultdict(int)
        path_words = parsed.path.split("/")
        for x in path_words:
            path_count[x] += 1
        for count in path_count.values():
            if count > 4:
                return False


        # parsed.netloc must include ".[ics, cs, informatics, stat].uci.edu"
        split_netloc = parsed.netloc.split(".")
        affiliate_index = split_netloc.index("uci")
        if split_netloc[affiliate_index-1] not in set(["ics", "cs", "informatics", "stat"]):
            return False
        
        # Removed the / at the end of "edu/". Since / and # are not part of netloc, "edu" will have nothing after it when you parse the URL.
        if split_netloc[affiliate_index+1] != "edu":  #edu/, edu#, edu ?? change to regex matching
            return False
        
        ## TO-DO:avoid traps!!: 
        ##       infinite redirections: keep list of visited links
        ##
        ##       duplicates/near-duplicates(fingerprint algorithm using sim-hash)
        ##          # define a similarity threshold
        ##          duplicate = any(abs(hash(content)) - hash(visitedContent) < threshold for vContent in visitedContent)
        ##          if false: add page to list of visited content
        

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
