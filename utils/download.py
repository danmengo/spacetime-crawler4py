import requests
import cbor
import time

from utils.response import Response

def download(url, config, logger=None, timeout=10):
    """Download URL via cache with timeout and retry handling.
    
    Args:
        url: The URL to download
        config: Config object with cache_server and user_agent
        logger: Optional logger
        timeout: Timeout in seconds for the cache request
    """
    host, port = config.cache_server
    
    try:
        # Use timeout to prevent long waits
        resp = requests.get(
            f"http://{host}:{port}/",
            params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
            timeout=timeout)
        
        # Try to decode cache response
        try:
            if resp and resp.content:
                return Response(cbor.loads(resp.content))
        except (EOFError, ValueError) as e:
            if logger:
                logger.warning(
                    f"Cache decode error for {url}: status={resp.status_code}, "
                    f"error={str(e)}, body_preview={resp.content[:200]!r}"
                )

        # Handle 602 (cache error) explicitly
        if resp.status_code == 602:
            if logger:
                logger.warning(f"Cache returned 602 for {url} - possible rate limit or timeout")
            return Response({
                "error": "Cache returned 602 status",
                "status": 602,
                "url": url
            })

    except requests.Timeout:
        if logger:
            logger.warning(f"Cache request timed out after {timeout}s for {url}")
        return Response({
            "error": f"Cache request timed out after {timeout}s",
            "status": 504,  # Gateway Timeout
            "url": url
        })
    except requests.RequestException as e:
        if logger:
            logger.error(f"Cache request failed for {url}: {str(e)}")
        return Response({
            "error": f"Cache request failed: {str(e)}",
            "status": 503,  # Service Unavailable
            "url": url
        })

    # General error case
    if logger:
        logger.error(f"Unexpected cache response for {url}: {resp.status_code}")
    return Response({
        "error": f"Unexpected cache response: {resp.status_code}",
        "status": resp.status_code,
        "url": url
    })
