# webscrvper — simple navigable scraper

This is a minimal web scraper with a simple navigable UI built with Flask.

Quick start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open http://localhost:5000 in your browser.

Usage

- Enter a URL in the form (you can omit the scheme, e.g. `example.com`).
- The scraper shows page title, paragraphs and a list of links.
- Click any link in the results to navigate and scrape that page.

Notes

- This is a small demo. For production use add rate-limiting, robots.txt respect, error handling, and caching.
# webscrvper
Simple Web Scraper
