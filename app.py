from flask import Flask, request, render_template, redirect, url_for
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)


def scrape_url(url):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "webscrvper/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")[:30]]
        links = []
        for a in soup.find_all("a", href=True)[:200]:
            href = urljoin(resp.url, a["href"])
            text = a.get_text(strip=True) or href
            links.append({"href": href, "text": text})
        return {"url": resp.url, "title": title, "paragraphs": paragraphs, "links": links}
    except Exception as e:
        return {"error": str(e)}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["GET", "POST"])
def scrape():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            return redirect(url_for("index"))
        return redirect(url_for("scrape", url=url))

    url = request.args.get("url", "").strip()
    if not url:
        return redirect(url_for("index"))
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "http://" + url

    result = scrape_url(url)
    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
