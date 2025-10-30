import re
from urllib.parse import urlparse, urldefrag, urljoin, parse_qs, parse_qsl, urlencode

from lxml import html, etree
from utils import get_logger

logger = get_logger("SCRAPER")

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

    if resp.raw_response is None or resp.raw_response.content is None or _is_dead_url(resp):
        return list()

    try:
        tree = html.fromstring(resp.raw_response.content)
    except etree.ParserError:
        return list()
    # Skip login/auth or access-restricted pages (DokuWiki and similar)
    if _is_login_page(resp, tree):
        logger.info(f"Skipping restricted/login page: {getattr(resp, 'url', url)}")
        return list()
        
    # Gather all links from a page
    hrefs = tree.xpath('//a/@href')
    
    valid_hrefs = list()

    for href in hrefs:
        # absolute_url = urljoin(resp.url, href) # Handle instances where href is a destination (i.e. `href=/target`)

        # if is_valid(absolute_url) and not _is_low_value_by_path(absolute_url) and not _is_low_value_by_query(absolute_url): 
        #     valid_hrefs.append(_defragment(absolute_url))

        # resolve and canonicalize
        absolute_url = urljoin(resp.url, href)
        normalized = _normalize_url(absolute_url)
        normalized = _defragment(normalized)

        # cheap low-value filters
        if _is_low_value_by_path(normalized) or _is_low_value_by_query(normalized):
            continue

        # final validity check
        if not is_valid(normalized):
            continue

        # Collect normalized links; frontier decides enqueueing (caps/dedupe)
        valid_hrefs.append(normalized)


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
        # Exclude user home directories (e.g. /~username/) which often host personal pages
        # that are not valuable for this crawl and can be traps (lots of image galleries, duplicate content).
        # Example: http://www.ics.uci.edu/~eppstein/...
        if re.match(r"^/~[^/]+", parsed.path):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|"
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
        'tribe-bar-date', 'ical', 'outlook-ical', 'eventDisplay'
    ])

    parsed_url = urlparse(url)
    query_dict = parse_qs(parsed_url.query)

    for key in query_dict.keys():
        if key in ignoredKeys:
            return True
        
    return False

def _normalize_url(url):
    parsed = urlparse(url)
    # filter out ignored keys (same set as in _is_low_value_by_query)
    ignored = set([
        'tab_files', 'tab_details', 'tab_upload',
        'idx', 'do', 'view', 'action',
        'expanded', 'ref_tags', 'format', 'sort',
        'tribe-bar-date', 'ical', 'outlook-ical', 'eventDisplay'
    ])

    qsl = parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [(k, v) for (k, v) in qsl if k not in ignored]

    new_query = urlencode(filtered, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return new_parsed.geturl()

def _is_low_value_by_path(url):
    """
    Determine if a URL path should be excluded from crawling.
    Uses host-specific rules for known systems and exact matches for general auth paths.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    netloc = parsed_url.netloc.lower()

    # Known authentication/restricted systems - be aggressive only for specific hosts
    if netloc == 'gradinfo.ics.uci.edu':
        # GradInfo auth paths - known to be login-only
        auth_paths = ('login', 'auth', 'signin', 'site/index')
        if any(p in path for p in auth_paths):
            logger.debug(f"Skipping gradinfo auth path: {url}")
            return True
    
    if netloc.endswith('.ics.uci.edu'):
        # DokuWiki account pages are always restricted
        if '/doku.php/accounts' in path:
            logger.debug(f"Skipping DokuWiki account path: {url}")
            return True

    # Common version control / issue tracker paths (exact matches)
    vcs_paths = [
        '/-/issues',
        '/-/merge_requests',
        '/-/forks',
        '/-/starrers',
        '/-/branches',
        '/-/tags',
        '/-/commit',
        '/-/tree'
    ]
    
    # Event calendar paths that can create URL traps
    if '/events/' in path:
        # Check for date-based event URLs that can create infinite combinations
        if any(x in path for x in ['/day/', '/month/', '/category/', 'event-deadline']):
            logger.debug(f"Skipping event calendar path: {url}")
            return True
    
    # Auth paths - use exact matches with optional trailing slash
    auth_paths = [
        '^/login/?$',
        '^/auth/?$',
        '^/signin/?$',
        '^/signout/?$',
        '^/logout/?$'
    ]
    
    # Check VCS paths
    for pattern in vcs_paths:
        if pattern in path:  # simple contains for VCS
            logger.debug(f"Skipping VCS path: {url}")
            return True
            
    # Check exact auth paths
    for pattern in auth_paths:
        if re.search(pattern, path):  # regex for exact auth matches
            logger.debug(f"Skipping exact auth path match: {url}")
            return True
            
    return False


def _is_login_page(resp, tree=None):
    """Return True if the page looks like a login/authentication page.

    We accept an optional lxml `tree` (already parsed) to avoid reparsing.
    """
    # prefer using the parsed tree when available
    if tree is None:
        try:
            tree = html.fromstring(resp.raw_response.content)
        except Exception:
            return False
    # quick status-based check: 401/403 usually indicate restricted access
    try:
        if getattr(resp, 'status', None) in (401, 403):
            return True
    except Exception:
        pass

    # look for password input fields and common login markers
    try:
        if tree.xpath("//input[@type='password']"):
            return True

        # look for forms with login/auth in the action or id/name
        forms = tree.xpath('//form')
        for f in forms:
            action = (f.get('action') or '').lower()
            fid = (f.get('id') or '').lower()
            fname = (f.get('name') or '').lower()
            if any(k in action for k in ('login', 'auth', 'signin')):
                return True
            if any(k in fid for k in ('login', 'auth', 'signin')):
                return True
            if any(k in fname for k in ('login', 'auth', 'signin')):
                return True

        # title or headings contain login / access-denied markers
        title = tree.xpath('//title/text()')
        headings = tree.xpath('//h1/text() | //h2/text() | //h3/text()')
        text_candidates = [t.lower() for t in (title + headings) if t]
        joined = ' '.join(text_candidates)
        bad_phrases = (
            'login', 'sign in', 'insufficient access',
            'insufficient access privileges', 'access denied', 'permission denied'
        )
        if any(p in joined for p in bad_phrases):
            return True

        # also check a short body preview for access-denied phrases
        body_texts = tree.xpath('//body//text()')
        if body_texts:
            preview = ' '.join(body_texts[:50]).lower()
            if any(p in preview for p in ('insufficient access', 'access denied', 'permission denied')):
                return True
    except Exception:
        # XPath errors or unexpected tree shapes => don't treat as login
        return False

    return False