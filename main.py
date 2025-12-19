from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, unquote

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<title>Python Proxy</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;padding:0;font-family:Arial;background:#0b0b0b;color:white}}
header{{background:#111;padding:10px;display:flex;gap:10px}}
input{{flex:1;padding:10px;background:#1a1a1a;color:white;border:none;border-radius:6px}}
button{{padding:10px 18px;background:#4f46e5;border:none;color:white;border-radius:6px;cursor:pointer}}
</style>
<script>
function loadPage() {{
    var input = document.getElementById("urlInput").value;
    if(!input) return;
    var proxyUrl = "/proxy?url=" + encodeURIComponent(input);
    window.location.href = proxyUrl;
}}
</script>
</head>
<body>
<header>
<input id="urlInput" placeholder="Search or enter URL">
<button onclick="loadPage()">Go</button>
</header>
<main>
<p style="text-align:center;margin-top:50px;">Enter a URL or search term above and click Go</p>
</main>
</body>
</html>
"""

def normalize_url(q):
    if not q:
        return ""
    q = q.strip()
    if " " in q:
        return f"https://duckduckgo.com/html/?q={quote(q)}"
    if not q.startswith("http"):
        return "https://" + q
    return q

@app.route("/")
def home():
    return HTML_TEMPLATE

@app.route("/proxy")
def proxy():
    raw_url = request.args.get("url")
    if not raw_url:
        return "<h2>No URL provided</h2>", 400

    url = unquote(raw_url)
    url = normalize_url(url)

    try:
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    except requests.exceptions.RequestException as e:
        return f"<h2>Failed to load site</h2><pre>{e}</pre>"

    content_type = r.headers.get("Content-Type", "")

    if "text/html" not in content_type:
        return Response(r.content, content_type=content_type)

    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["a", "img", "script", "link", "iframe"]):
            attr = "href" if tag.name in ["a", "link"] else "src"
            if tag.has_attr(attr):
                new_url = urljoin(url, tag[attr])
                tag[attr] = "/proxy?url=" + quote(new_url)

        return Response(
            str(soup),
            headers={
                "Content-Security-Policy": "default-src * data: blob: 'unsafe-inline' 'unsafe-eval';",
                "X-Frame-Options": "ALLOWALL"
            }
        )
    except Exception as e:
        return f"<h2>Error parsing HTML</h2><pre>{e}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)