import re
from urllib.parse import urlparse, urljoin
from lxml import html

def scraper(url, resp):
    links = extract_next_links(url, resp)
    print(links) #DEBUG REMOVE THIS LATER
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
        # however, it is a mix of relative and absolute URLs
        # so we need to convert relatives into absolutes

        html_string = html.fromstring(resp.raw_response.content)
        full_links = list(html_string.iterlinks())
        for y in full_links:
            if y != "#" and y != "/":
                new_url = urljoin(url, y[2])
                links.append(new_url)
        
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
        affiliate_index = split_netloc.find("uci")
        if affiliate_index == -1:
            return False
        if split_netloc[affiliate_index-1] not in set(["ics", "cs", "informatics", "stat"]):
            return False
        if split_netloc[affiliate_index+1] != "edu/":
            return False

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
