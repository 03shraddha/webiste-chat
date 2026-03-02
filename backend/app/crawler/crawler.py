import asyncio
import random
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from typing import Callable, Awaitable
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, BrowserContext

from app.crawler.extractor import extract_page_content
from app.crawler.url_utils import (
    normalize_url,
    extract_domain,
    extract_links,
    is_valid_crawlable_url,
    is_same_domain,
)

_SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
_SITEMAP_CANDIDATES = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap/sitemap.xml"]


def _fetch_sitemap_urls_sync(base_url: str, base_domain: str, max_urls: int) -> list[str]:
    """
    Synchronous sitemap fetch (run in executor).
    Tries common sitemap paths, parses <loc> elements, returns same-domain URLs.
    Handles both sitemap index files and regular sitemaps.
    """
    found: list[str] = []

    def _parse_sitemap_xml(content: str) -> list[str]:
        urls = []
        try:
            root = ET.fromstring(content)
            # Try with namespace first, then without
            for ns_prefix in [f"{{{_SITEMAP_NS}}}", ""]:
                locs = root.findall(f".//{ns_prefix}loc")
                if locs:
                    for loc in locs:
                        u = (loc.text or "").strip()
                        if u:
                            urls.append(u)
                    break
        except ET.ParseError:
            pass
        return urls

    def _fetch_url(url: str) -> str | None:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; SitemapBot/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    ct = resp.headers.get("Content-Type", "")
                    if "html" in ct and "xml" not in ct:
                        return None  # Skip HTML pages masquerading as sitemap
                    return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        return None

    for path in _SITEMAP_CANDIDATES:
        sitemap_url = urljoin(base_url, path)
        content = _fetch_url(sitemap_url)
        if not content:
            continue

        raw_urls = _parse_sitemap_xml(content)
        if not raw_urls:
            continue

        print(f"[CRAWLER] Sitemap found at {sitemap_url} ({len(raw_urls)} entries)")

        for u in raw_urls:
            if len(found) >= max_urls:
                break
            # Sitemap index files contain links to other sitemaps — recurse one level
            if u.endswith(".xml"):
                sub_content = _fetch_url(u)
                if sub_content:
                    for sub_u in _parse_sitemap_xml(sub_content):
                        if (
                            len(found) < max_urls
                            and is_same_domain(sub_u, base_domain)
                            and is_valid_crawlable_url(sub_u)
                        ):
                            found.append(sub_u)
            elif is_same_domain(u, base_domain) and is_valid_crawlable_url(u):
                found.append(u)

        if found:
            break  # Stop at first working sitemap

    return found


async def crawl_site(
    start_url: str,
    max_pages: int,
    max_depth: int,
    progress_callback: Callable[[int, str], Awaitable[None]],
) -> list[dict]:
    """
    BFS crawl of a website using Playwright.
    Seeds queue from sitemap.xml if available, falls back to link-following BFS.

    Args:
        start_url: The seed URL to start crawling from.
        max_pages: Maximum number of pages to crawl.
        max_depth: Maximum BFS depth from the seed URL.
        progress_callback: Async callable(pages_crawled, current_url).

    Returns:
        List of page dicts: {url, title, content, sections, meta_description, headings}
    """
    base_domain = extract_domain(start_url)
    visited: set[str] = set()
    pages: list[dict] = []
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5

    # Try sitemap first — much more efficient than BFS for well-structured sites
    loop = asyncio.get_event_loop()
    sitemap_urls = await loop.run_in_executor(
        None, _fetch_sitemap_urls_sync, start_url, base_domain, max_pages * 2
    )

    if sitemap_urls:
        # Seed queue from sitemap (depth=1 since we already know the URLs)
        queue: deque[tuple[str, int]] = deque(
            [(normalize_url(u), 1) for u in sitemap_urls]
        )
        # Always include start URL at depth 0
        queue.appendleft((normalize_url(start_url), 0))
        print(f"[CRAWLER] Seeded queue with {len(sitemap_urls)} sitemap URLs")
    else:
        queue = deque([(normalize_url(start_url), 0)])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context: BrowserContext = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        # Block heavy resources that don't affect text content
        await context.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot,mp4,mp3,avi,webp,webm}",
            lambda route: route.abort(),
        )

        while queue and len(pages) < max_pages:
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"[CRAWLER] Bailing out after {MAX_CONSECUTIVE_ERRORS} consecutive errors")
                break

            url, depth = queue.popleft()
            norm_url = normalize_url(url)

            if norm_url in visited:
                continue
            visited.add(norm_url)

            page = await context.new_page()
            try:
                # Attempt networkidle first for JS-heavy SPAs
                response = None
                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=20000)
                except Exception:
                    # Fall back to domcontentloaded if networkidle times out
                    try:
                        response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    except Exception as e:
                        print(f"[CRAWLER] Navigation failed {url}: {e}")
                        consecutive_errors += 1
                        await page.close()
                        continue

                # Handle HTTP error status codes
                if response is not None:
                    status = response.status
                    if status == 429:
                        print(f"[CRAWLER] Rate limited on {url}, backing off 8s")
                        await page.close()
                        await asyncio.sleep(8)
                        continue
                    elif status in (401, 403):
                        print(f"[CRAWLER] Access denied ({status}) for {url}, skipping")
                        await page.close()
                        continue
                    elif status == 404:
                        await page.close()
                        continue
                    elif status >= 500:
                        print(f"[CRAWLER] Server error ({status}) for {url}")
                        consecutive_errors += 1
                        await page.close()
                        continue
                    elif status >= 400:
                        print(f"[CRAWLER] Client error ({status}) for {url}, skipping")
                        await page.close()
                        continue

                # Let dynamic content settle
                await page.wait_for_timeout(500)

                content_data = await extract_page_content(page, url)
                if content_data:
                    pages.append(content_data)
                    consecutive_errors = 0  # reset on success
                    await progress_callback(len(pages), url)

                # Enqueue child links within depth limit (skip if sitemap already seeded)
                if depth < max_depth and not sitemap_urls:
                    links = await extract_links(page, base_domain)
                    for link in links:
                        norm_link = normalize_url(link)
                        if norm_link not in visited and is_valid_crawlable_url(link):
                            queue.append((link, depth + 1))

            except Exception as e:
                print(f"[CRAWLER] Error processing {url}: {e}")
                consecutive_errors += 1
            finally:
                await page.close()

            # Polite crawl delay
            await asyncio.sleep(0.5 + random.uniform(0, 0.3))

        await browser.close()

    print(f"[CRAWLER] Done. Crawled {len(pages)} pages from {start_url}")
    return pages
