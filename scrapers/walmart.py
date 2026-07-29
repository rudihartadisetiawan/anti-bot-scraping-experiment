# scrapers/walmart.py
# Eksperimen scraper Walmart via /browse (bukan /search).
# robots.txt: /search Disallow; /browse tidak di-disallow.

import asyncio
import json
import random
import time
import datetime
import re
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

# ==================== KONFIGURASI ====================
# URL browse kategori Mens Graphic Tees (valid, tidak di-disallow robots.txt)
TARGET_URL = (
    "https://www.walmart.com/browse/clothing/mens-graphic-tees/"
    "5438_133197_6286551_9358077"
)
MAX_PRODUCTS = 30  # ponytail: jangan > 50 sesuai scope eksperimen
MIN_DELAY = 3.0
MAX_DELAY = 5.0
MAX_RETRIES = 2
BACKOFF_BASE = 5.0
PAGE_TIMEOUT = 45000  # ms
SCROLL_STEP = 500
SCROLL_DELAY_MIN = 0.8
SCROLL_DELAY_MAX = 1.5
MAX_SCROLLS = 10

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "walmart_products.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1366, "height": 768}
LOCALE = "en-US"
TIMEZONE = "America/New_York"

# ==================== LOGGING BLOCK DETEKSI ====================
def log_block(event_type: str, detail: str):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] BLOCK_LOG | {event_type}: {detail}")


def log_info(msg: str):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{ts}] INFO: {msg}")

# ==================== RATE LIMIT ====================
async def polite_delay():
    """Delay antar request dengan jitter random."""
    await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

# ==================== ANTI-DETEKSI ====================
async def launch_browser(p):
    """Launch Playwright dengan konfigurasi stealth dasar."""
    browser = await p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # ponytail: kurangi beban, cukup untuk listing
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport=VIEWPORT,
        locale=LOCALE,
        timezone_id=TIMEZONE,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    # ponytail: sembunyikan webdriver flag dasar
    await context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    )
    return browser, context

# ==================== DETEKSI BLOCK ====================
async def detect_block(page, response_status: int | None = None) -> tuple[bool, str]:
    """Deteksi eksplisit: captcha, verify, 403/429, redirect, shadow block."""
    title = (await page.title()).lower()
    url = page.url

    if any(k in title for k in ("captcha", "verify", "robot", "human", "security", "blocked")):
        return True, "CAPTCHA_DETECTED"

    if any(k in url.lower() for k in ("captcha", "verify", "robot", "login", "blocked", "passport", "tmd", "punish")):
        return True, "BLOCK_DETECTED: redirect"

    if response_status in (403, 429):
        return True, f"BLOCK_DETECTED: status={response_status}"

    # ponytail: deteksi shadow block — halaman kosong/tidak ada produk
    has_next = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return false;
        try {
            const data = JSON.parse(el.textContent);
            const items = data?.props?.pageProps?.initialData?.searchResult?.itemStacks?.[0]?.items || [];
            return items.length > 0;
        } catch {
            return false;
        }
    }""")
    has_tiles = await page.query_selector('[data-testid="item-stack"]')
    if not has_next and not has_tiles:
        return True, "EMPTY_PAGE: possible shadow block"

    return False, "OK"

# ==================== SCRAPING ====================
async def scroll_page(page):
    """Scroll perlahan untuk trigger lazy-loading."""
    for i in range(MAX_SCROLLS):
        prev_height = await page.evaluate("() => document.body.scrollHeight")
        await page.evaluate(f"window.scrollBy(0, {SCROLL_STEP})")
        await asyncio.sleep(random.uniform(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX))
        new_height = await page.evaluate("() => document.body.scrollHeight")
        log_info(f"scroll {i+1}/{MAX_SCROLLS}, height={new_height}")
        if new_height == prev_height:
            break


async def _extract_from_next_data(page):
    """Ekstrak produk dari __NEXT_DATA__ (SSR hydration data)."""
    items = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return [];
        try {
            const data = JSON.parse(el.textContent);
            return data?.props?.pageProps?.initialData?.searchResult?.itemStacks?.[0]?.items || [];
        } catch {
            return [];
        }
    }""")
    if not items:
        return []

    products = []
    for item in items:
        title = item.get("name") or item.get("shortDescription") or ""
        title = title.strip().lstrip(",").strip()
        if not title or len(title) < 5:
            continue

        canonical = item.get("canonicalUrl") or ""
        if canonical and not canonical.startswith("http"):
            product_url = "https://www.walmart.com" + canonical
        else:
            product_url = canonical

        # priceInfo dari SSR sering kosong; ambil kalau ada, else None
        price_info = item.get("priceInfo") or {}
        price = (
            price_info.get("itemPrice")
            or price_info.get("linePriceDisplay")
            or price_info.get("linePrice")
            or price_info.get("priceRangeString")
            or None
        )
        if price:
            price = price.strip()
        if not price:
            price = None

        rating = None
        if item.get("rating"):
            avg = item["rating"].get("averageRating")
            reviews = item["rating"].get("numberOfReviews")
            if avg is not None:
                rating = f"{avg}"
                if reviews is not None:
                    rating = f"{avg} ({reviews} reviews)"

        products.append({
            "title": title,
            "price": price,
            "product_url": product_url,
            "rating": rating,
            "sold_count": None,
            "source": "walmart",
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        })

        if len(products) >= MAX_PRODUCTS:
            break

    return products


async def _extract_from_dom(page):
    """Fallback ekstrak dari DOM kalau __NEXT_DATA__ tidak ada."""
    products = []
    cards = await page.query_selector_all('[data-testid="item-stack"]')
    log_info(f"DOM fallback found {len(cards)} item-stack cards")

    for card in cards:
        try:
            title_el = await card.query_selector('[data-automation-id="product-title"]')
            if not title_el:
                continue
            title = await title_el.inner_text()
            title = title.strip()
            if not title or len(title) < 5:
                continue

            link_el = await card.query_selector('a[href^="/ip/"]')
            if not link_el:
                continue
            href = await link_el.get_attribute("href")
            if not href:
                continue
            product_url = "https://www.walmart.com" + href.split("?")[0]

            price_el = await card.query_selector('[data-testid="unified-global-product-price"]')
            price = await price_el.inner_text() if price_el else None
            price = price.strip() if price else None

            rating = None
            reviews_el = await card.query_selector('[data-testid="product-reviews"]')
            if reviews_el:
                rev_text = await reviews_el.inner_text()
                rating = rev_text.strip() if rev_text else None

            products.append({
                "title": title,
                "price": price,
                "product_url": product_url,
                "rating": rating,
                "sold_count": None,
                "source": "walmart",
                "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            })

            if len(products) >= MAX_PRODUCTS:
                break
        except Exception as e:
            log_info(f"skip card: {e}")
            continue

    return products


async def extract_products(page):
    """Ekstrak data produk dari halaman kategori."""
    products = await _extract_from_next_data(page)
    if products:
        log_info(f"extracted {len(products)} products from __NEXT_DATA__")
        return products

    products = await _extract_from_dom(page)
    if products:
        log_info(f"extracted {len(products)} products from DOM fallback")
    return products


async def scrape_walmart():
    """Main scraping flow dengan retry + graceful degradation."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    products = []
    block_count = 0
    retry_count = 0

    async with async_playwright() as p:
        browser, context = await launch_browser(p)
        page = await context.new_page()

        for attempt in range(MAX_RETRIES + 1):
            try:
                log_info(f"attempt {attempt + 1}/{MAX_RETRIES + 1} -> {TARGET_URL}")
                response = await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

                await polite_delay()
                await scroll_page(page)

                if response:
                    status = response.status
                    if status in (403, 429):
                        block_count += 1
                        log_block("BLOCK_DETECTED", f"status={status}, attempt={attempt + 1}")
                        if attempt < MAX_RETRIES:
                            wait = BACKOFF_BASE * (2 ** attempt)
                            log_info(f"backoff {wait}s before retry")
                            await asyncio.sleep(wait)
                            continue
                        break

                is_blocked, reason = await detect_block(page, response.status if response else None)
                if is_blocked:
                    block_count += 1
                    log_block(reason, f"attempt={attempt + 1}")
                    if attempt < MAX_RETRIES:
                        wait = BACKOFF_BASE * (2 ** attempt)
                        log_info(f"backoff {wait}s before retry")
                        await asyncio.sleep(wait)
                        continue
                    break

                products = await extract_products(page)
                if products:
                    log_info(f"extracted {len(products)} products")
                    break
                else:
                    block_count += 1
                    log_block("EMPTY_PAGE", "no products extracted")
                    if attempt < MAX_RETRIES:
                        wait = BACKOFF_BASE * (2 ** attempt)
                        log_info(f"backoff {wait}s before retry")
                        await asyncio.sleep(wait)
                        continue
                    break

            except PWTimeoutError:
                retry_count += 1
                block_count += 1
                log_block("BLOCK_DETECTED", f"timeout on attempt={attempt + 1}")
                if attempt < MAX_RETRIES:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    log_info(f"backoff {wait}s before retry")
                    await asyncio.sleep(wait)
                    continue
                break
            except Exception as e:
                retry_count += 1
                log_block("ERROR", f"attempt={attempt + 1}, error={e}")
                if attempt < MAX_RETRIES:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    log_info(f"backoff {wait}s before retry")
                    await asyncio.sleep(wait)
                    continue
                break

        await context.close()
        await browser.close()

    # Simpan hasil
    if products:
        OUTPUT_FILE.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
        log_info(f"saved {len(products)} products to {OUTPUT_FILE}")
    else:
        OUTPUT_FILE.write_text("[]", encoding="utf-8")
        log_info(f"no products, saved empty array to {OUTPUT_FILE}")

    # Statistik akhir
    print("\n========== SCRAPING STATISTICS ==========")
    print(f"Target URL        : {TARGET_URL}")
    print(f"Products scraped  : {len(products)}")
    print(f"Block/captcha     : {block_count}")
    print(f"Retries used      : {retry_count}")
    print(f"Output file       : {OUTPUT_FILE}")
    print("=========================================\n")

    return products


if __name__ == "__main__":
    asyncio.run(scrape_walmart())
