#!/usr/bin/env python3
"""scrape_products.py

Simple product scraper using requests + BeautifulSoup that extracts product
titles and prices from a listing page and saves results to CSV.

Usage examples (see README for more):
python scripts/scrape_products.py "https://example.com/category" --output products.csv \
  --container ".product-card" --title ".product-title" --price ".price" --next ".next"
"""

import argparse
import csv
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {"User-Agent": "webscrvper-product-scraper/1.0"}


def get_soup(url, timeout=10):
    resp = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser"), resp.url


def text_or_none(elem):
    return elem.get_text(strip=True) if elem else None


def heuristic_find_containers(soup):
    # common container tags/classes used on e-commerce listing pages
    candidates = []
    for cls in ("product", "item", "card", "result"):
        candidates.extend(soup.select(f"div[class*='{cls}']"))
        candidates.extend(soup.select(f"li[class*='{cls}']"))
        candidates.extend(soup.select(f"article[class*='{cls}']"))
    # dedupe while preserving order
    seen = set()
    uniq = []
    for c in candidates:
        if id(c) not in seen:
            uniq.append(c)
            seen.add(id(c))
    return uniq


PRICE_RE = re.compile(r"[$£€]\s?\d+[\d,]*(?:\.\d{1,2})?")


def extract_from_container(container, title_sel=None, price_sel=None):
    title = None
    price = None

    if title_sel:
        title = text_or_none(container.select_one(title_sel))
    else:
        # try common title tags
        for sel in (".title", "h2", "h3", "a", ".name", ".product-name"):
            t = container.select_one(sel)
            if t and t.get_text(strip=True):
                title = t.get_text(strip=True)
                break

    if price_sel:
        price = text_or_none(container.select_one(price_sel))
    else:
        # look for elements with price-like text inside container
        text = container.get_text(separator=" \n ", strip=True)
        m = PRICE_RE.search(text)
        if m:
            price = m.group(0)

    return title, price


def scrape_listing(start_url, container_sel=None, title_sel=None, price_sel=None, next_sel=None, max_pages=10, delay=1.0):
    url = start_url
    results = []
    pages = 0

    while url and pages < max_pages:
        print(f"Fetching: {url}")
        soup, final_url = get_soup(url)

        if container_sel:
            containers = soup.select(container_sel)
        else:
            containers = heuristic_find_containers(soup)

        if not containers:
            print("No containers found on page — stopping.")
            break

        for c in containers:
            title, price = extract_from_container(c, title_sel=title_sel, price_sel=price_sel)
            link_tag = c.select_one("a[href]")
            item_url = urljoin(final_url, link_tag["href"]) if link_tag else None
            if title or price:
                results.append({"title": title or "", "price": price or "", "item_url": item_url, "page_url": final_url})

        pages += 1
        # find next page
        next_url = None
        if next_sel:
            a = soup.select_one(next_sel)
            if a and a.has_attr("href"):
                next_url = urljoin(final_url, a["href"])
        else:
            # common heuristics: link with rel=next or class containing next
            a = soup.select_one('a[rel=next]') or soup.select_one("a[class*='next']")
            if a and a.has_attr("href"):
                next_url = urljoin(final_url, a["href"])            

        if not next_url:
            break

        url = next_url
        time.sleep(delay)

    return results


def write_csv(path, rows):
    keys = ("title", "price", "item_url", "page_url")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (r.get(k) or "") for k in keys})


def main():
    p = argparse.ArgumentParser(description="Scrape product titles and prices from a listing page")
    p.add_argument("url", help="Starting listing URL")
    p.add_argument("--output", "-o", default="products.csv", help="CSV output path")
    p.add_argument("--container", help="CSS selector for a single product container (e.g. '.product-card')")
    p.add_argument("--title", help="CSS selector for title within container (e.g. '.title')")
    p.add_argument("--price", help="CSS selector for price within container (e.g. '.price')")
    p.add_argument("--next", help="CSS selector for next-page link (e.g. 'a.next')")
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--delay", type=float, default=1.0)
    args = p.parse_args()

    rows = scrape_listing(args.url, container_sel=args.container, title_sel=args.title, price_sel=args.price, next_sel=args.next, max_pages=args.max_pages, delay=args.delay)
    if rows:
        write_csv(args.output, rows)
        print(f"Wrote {len(rows)} rows to {args.output}")
    else:
        print("No products extracted.")


if __name__ == "__main__":
    main()
