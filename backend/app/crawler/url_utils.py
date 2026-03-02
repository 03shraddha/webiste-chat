import re
from urllib.parse import urlparse, urlunparse, urljoin, parse_qs, urlencode

# Query params that are purely tracking/session noise — not part of page identity
_STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_referrer",
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid",
    "ref", "referrer", "source",
    "PHPSESSID", "jsessionid", "sessionid",
    "_ga", "_gl", "_hsenc", "_hsmi",
    "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Remove fragments, tracking params, normalize trailing slashes, lowercase scheme+host."""
    try:
        parsed = urlparse(url)
        # Strip fragment, lowercase scheme and netloc
        normalized = parsed._replace(
            fragment="",
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
        )
        # Strip tracking/session query params
        if normalized.query:
            qs = parse_qs(normalized.query, keep_blank_values=True)
            filtered = {k: v for k, v in qs.items() if k.lower() not in _STRIP_PARAMS}
            new_query = urlencode(filtered, doseq=True)
            normalized = normalized._replace(query=new_query)
        # Strip trailing slash from path except root
        path = normalized.path.rstrip("/") or "/"
        normalized = normalized._replace(path=path)
        return urlunparse(normalized)
    except Exception:
        return url


def extract_domain(url: str) -> str:
    """Return the netloc (host) of a URL, lowercased."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_same_domain(url: str, base_domain: str) -> bool:
    """True if url belongs to base_domain (handles www. prefix variations)."""
    host = extract_domain(url)
    if not host:
        return False
    # Allow www prefix to be added or removed
    return (
        host == base_domain
        or host == f"www.{base_domain}"
        or f"www.{host}" == base_domain
    )


def is_valid_crawlable_url(url: str) -> bool:
    """Filter out non-HTTP URLs, files, and excessively long URLs."""
    if len(url) > 300:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    # Skip binary file extensions
    skip_exts = {
        ".pdf", ".zip", ".tar", ".gz", ".jpg", ".jpeg", ".png", ".gif",
        ".svg", ".ico", ".mp4", ".mp3", ".avi", ".mov", ".wmv",
        ".exe", ".dmg", ".pkg", ".deb", ".rpm",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    }
    path_lower = parsed.path.lower()
    if any(path_lower.endswith(ext) for ext in skip_exts):
        return False
    return True


def extract_site_name(url: str) -> str:
    """Extract a human-readable site name from URL."""
    domain = extract_domain(url)
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    # Take just the domain name part (before first dot)
    name = domain.split(".")[0]
    return name.capitalize()


async def extract_links(page, base_domain: str) -> list[str]:
    """Extract all <a href> links from current page, filtered to same domain."""
    try:
        hrefs = await page.evaluate(
            "() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"
        )
    except Exception:
        return []

    valid = []
    for href in hrefs:
        if not isinstance(href, str):
            continue
        if is_valid_crawlable_url(href) and is_same_domain(href, base_domain):
            valid.append(href)

    return list(set(valid))
