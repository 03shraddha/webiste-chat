import re


# JS to remove boilerplate elements before extracting content
_REMOVE_BOILERPLATE_JS = """
() => {
    const selectors = [
        'nav', 'header', 'footer',
        '[class*="cookie"]', '[class*="banner"]', '[class*="popup"]',
        '[class*="modal"]', '[class*="overlay"]', '[class*="toast"]',
        '[id*="cookie"]', '[id*="banner"]', '[id*="popup"]',
        '.nav', '.navbar', '.sidebar', '.menu',
        '.breadcrumb', '.pagination',
        'script', 'style', 'noscript',
        '[role="navigation"]', '[role="banner"]', '[role="complementary"]',
    ];
    selectors.forEach(sel => {
        try {
            document.querySelectorAll(sel).forEach(el => el.remove());
        } catch(e) {}
    });
}
"""

# JS to extract main content text — tries semantic selectors first
_EXTRACT_CONTENT_JS = """
() => {
    const candidates = [
        'main',
        'article',
        '[role="main"]',
        '.content',
        '#content',
        '.main-content',
        '#main-content',
        '.post-content',
        '.entry-content',
        '.page-content',
        'body'
    ];
    for (const sel of candidates) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.trim().length > 100) {
            return el.innerText.trim().replace(/[\\t ]+/g, ' ').replace(/\\n{3,}/g, '\\n\\n');
        }
    }
    return document.body ? document.body.innerText.trim().replace(/[\\t ]+/g, ' ') : '';
}
"""

_EXTRACT_HEADINGS_JS = """
() => Array.from(document.querySelectorAll('h1,h2,h3'))
    .map(h => h.innerText.trim())
    .filter(t => t.length > 0 && t.length < 200)
    .slice(0, 10)
"""

_EXTRACT_META_JS = """
() => {
    const meta = document.querySelector('meta[name="description"]')
               || document.querySelector('meta[property="og:description"]');
    return meta ? meta.getAttribute('content') || '' : '';
}
"""


_PAGE_SIZE_LIMIT = 5 * 1024 * 1024  # 5 MB


async def extract_page_content(page, url: str) -> dict | None:
    """
    Extracts clean page content after removing boilerplate.
    Returns dict with url, title, content, meta_description, headings.
    Returns None if content is too short to be useful or page is too large.
    """
    try:
        # Skip pages that are too large to avoid memory issues
        page_size = await page.evaluate("() => document.documentElement.innerHTML.length")
        if page_size > _PAGE_SIZE_LIMIT:
            print(f"[EXTRACTOR] Skipping {url}: page too large ({page_size} chars)")
            return None

        # Remove nav/footer/cookie banners before reading text
        await page.evaluate(_REMOVE_BOILERPLATE_JS)

        title = await page.title() or ""
        meta_description = await page.evaluate(_EXTRACT_META_JS) or ""
        headings = await page.evaluate(_EXTRACT_HEADINGS_JS) or []
        content = await page.evaluate(_EXTRACT_CONTENT_JS) or ""

        # Skip pages with very little content
        if len(content.strip()) < 100:
            return None

        return {
            "url": url,
            "title": title.strip(),
            "content": content,
            "meta_description": meta_description.strip(),
            "headings": headings,
        }

    except Exception as e:
        print(f"[EXTRACTOR] Failed to extract {url}: {e}")
        return None
