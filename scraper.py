import re
from urllib.parse import urlparse, urldefrag, urljoin, parse_qs

from lxml import html, etree

from report import Report

def scraper(url, resp):
    links = extract_next_links(url, resp)
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
    Report.update_report(resp)

    if resp.status != 200:
        return list()
    elif resp.raw_response is None or resp.raw_response.content is None or _is_dead_url(resp):
        return list()

    try:
        tree = html.fromstring(resp.raw_response.content)
    except etree.ParserError:
        return list()
        
    # Gather all links from a page
    hrefs = tree.xpath('//a/@href')
    
    valid_hrefs = list()

    for href in hrefs:
        try:
            absolute_url = urljoin(resp.url, href) # Handle instances where href is a destination (i.e. `href=/target`)
            if is_valid(absolute_url) and not _is_low_value_by_path(absolute_url) and not _is_low_value_by_query(absolute_url) and not _is_low_level_by_regex(absolute_url): 
                valid_hrefs.append(_defragment(absolute_url))
        except:
            continue

    return valid_hrefs


# Removes the fragment part from URLs
def _defragment(url) -> str:
    clean_url, _ = urldefrag(url)
    return clean_url

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        elif not _is_valid_domain(url):
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
        raise

# Returns True if the following url is considered a domain
def _is_valid_domain(url):
    allowed = [
        '.ics.uci.edu',
        '.cs.uci.edu',
        '.informatics.uci.edu',
        '.stat.uci.edu'
    ]

    parsed_url = urlparse(url)

    for domains in allowed:
        #netloc is network location aka domain
        if parsed_url.netloc.lower().endswith(domains): 
            return True
    
    return False    

# Determines if the URL is a dead URL (returns 200 status but no data)
def _is_dead_url(resp):
    if resp.status != 200:
        return False
    elif (len(resp.raw_response.content)) <= 100: # May need to tune 100 
        return True
    return False

# Determines if the pages are similar with no information
# TODO: Try removing idx and do at the end
def _is_low_value_by_query(url):
    ignoredKeys = set([
        'tab_files', 'tab_details', 'tab_upload', 
        'idx', 'do', 'view', 'action',
        'expanded', 'ref_tags', 'format', 'sort',
        'tribe-bar-date',
        'ical', 'outlook-ical', 'eventDisplay',
        'share', 'display', 'redirect_to',
        'from'
    ])

    parsed_url = urlparse(url)
    query_dict = parse_qs(parsed_url.query)

    for key in query_dict.keys():
        if key in ignoredKeys:
            return True
        
    return False

def _is_low_value_by_path(url):
    
    ignored_paths = [
        '/-/issues',
        '/-/merge_requests',
        '/-/forks',
        '/-/starrers',
        '/-/branches',
        '/-/tags',
        '/-/commit',
        '/-/tree',
    ]

    parsed_url = urlparse(url)
    path = parsed_url.path

    for pattern in ignored_paths:
        if re.search(pattern, path):
            return True
    return False

# Removes low level by regex
def _is_low_level_by_regex(url):
    parsed_url = urlparse(url)
    regexes = [
        re.compile(r"/day/\d{4}-\d{2}-\d{2}(/|$)"), # /day/2025-20-10
        re.compile(r"/events/\d{4}-\d{2}-\d{2}(/|$)"),
        re.compile(r"/events/month/\d{4}-\d{2}(/|$)"),
        re.compile(r"/events/category(?:/[^/]+)?/\d{4}-\d{2}(/|$)"),
        re.compile(r"/events/tag/talks/\d{4}-\d{2}(/|$)"),    
        re.compile(r"/project-meeting/\d{4}-\d{2}(/|$)"),
        re.compile(r"/talks/\d{4}-\d{2}(/|$)"),
        re.compile(r"/talk/\d{4}-\d{2}(/|$)"),
        re.compile(r"/~eppstein/pix"),
        re.compile(r"/research/seminarseries/(\d{4}-\d{4})"),
        re.compile(r"flamingo.ics.uci.edu/\d+\.\d+(?:\.\d+)?")
    ]

    for regex in regexes:
        if regex.search(parsed_url.path):
            return True
        
    return False