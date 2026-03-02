import asyncio
import random
from collections import deque
from typing import Callable, Awaitable

from playwright.async_api import async_playwright, Page, BrowserContext

from app.crawler.extractor import extract_page_content
from app.crawler.url_utils import (
    normalize_url,
    extract_domain,
    extract_links,
    is_valid_crawlable_url,
)


async def crawl_site(
    start_url: str,
    max_pages: int,
    max_depth: int,
    progress_callback: Callable[[int, str], Awaitable[None]],
) -> list[dict]:
    """
    BFS crawl of a website using Playwright.

    Args:
        start_url: The seed URL to start crawling from.
        max_pages: Maximum number of pages to crawl.
        max_depth: Maximum BFS depth from the seed URL.
        progress_callback: Async callable(pages_crawled, current_url).

    Returns:
        List of page dicts: {url, title, content, meta_description, headings}
    """
    base_domain = extract_domain(start_url)
    queue: deque[tuple[str, int]] = deque([(normalize_url(start_url), 0)])
    visited: set[str] = set()
    pages: list[dict] = []
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 5

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

                # Enqueue child links within depth limit
                if depth < max_depth:
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
