import re
from urllib.parse import urlparse, urljoin
from lxml import html
from collections import defaultdict

def scraper(url, resp):
    links = extract_next_links(url, resp)
    #print(links) #DEBUG REMOVE THIS LATER
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = []
    if resp.status == 200:
        #parse page, store stuff for report, find URLs, remove fragments # from URLs
        
        # code below extracts links from the webpage
        # TO-DO: we still need to handle fragments (DONE, NEEDS TESTING)
        # TO-DO: test getting content

        html_string = html.fromstring(resp.raw_response.content)
        full_links = list(html_string.iterlinks())
        for y in full_links:
            if y != "#" and y != "/":
                new_url = urljoin(url, y[2])
                fragment_index = new_url.find('#')
                if fragment_index != -1:
                    new_url = new_url[:fragment_index]
                links.append(new_url)


        # TO-DO: get text content of every webpage crawled (worry about low-info checking later)
        # TO-DO: keep some global counter of unique pages found, page with max_words (and a max_words count),
        #        a default_dict to count words for the top 50 most common words (ignore English stop words),
        #        a default_dict with each subdomain of ics.uci.edu with a counter of # of unique pages.

        # PLAN: add a new class in worker.py to store all the above, with methods to modify all the above. 
        
        site_text_list = html_string.xpath('//p')
        #We will move word_counts to the worker.py module later. Just testing for each URL right now.
        word_counts = defaultdict(int)
        for body in site_text_list:
            for word in re.split('[^a-zA-z0-9]+', body):
                if word != "":
                    word_counts[word] += 1
        



        
        """
        links = html.fromstring(resp.raw_response.content)
        links = re.findall(r'https://+', html.fromstring(resp.raw_response.content))
        for x in range(len(links)):
            print(x)
            fragment_index = links[x].find('#')
            if fragment_index != -1:
                links[x] = links[x][:fragment_index]
        """
    # else:
    #     #resp.error to check error
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # parsed.netloc must include ".[ics, cs, informatics, stat].uci.edu"
        split_netloc = parsed.netloc.split(".")
        affiliate_index = split_netloc.index("uci")
        if split_netloc[affiliate_index-1] not in set(["ics", "cs", "informatics", "stat"]):
            return False
        
        # Removed the / at the end of "edu/". Since / and # are not part of netloc, "edu" will have nothing after it when you parse the URL.
        if split_netloc[affiliate_index+1] != "edu":  #edu/, edu#, edu ?? change to regex matching
            return False
        
        ## how to avoid traps??

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
