from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, unquote

app = Flask(__name__)

# Strong browser-like headers
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

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Advanced Proxy Browser</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#0b0b0b;color:white;font-family:Arial}
header{background:#111;padding:10px}
form{display:flex;gap:10px}
input{flex:1;padding:10px;background:#1a1a1a;color:white;border:none;border-radius:6px}
button{padding:10px 18px;background:#4f46e5;border:none;color:white;border-radius:6px;cursor:pointer}
iframe{width:100%;height:calc(100vh - 70px);border:none}
footer{text-align:center;font-size:12px;color:#666;padding:5px}
</style>
</head>
<body>
<header>
<form action="/go" method="get">
<input name="q" placeholder="Search or enter URL">
<button>Go</button>
</form>
</header>
<iframe src="{page}"></iframe>
<footer>Python Advanced Proxy</footer>
</body>
</html>
"""

def normalize(q):
    if not q:
        return None
    if " " in q:
        return f"https://duckduckgo.com/html/?q={quote(q)}"
    if not q.startswith("http"):
        return "https://" + q
    return q

@app.route("/")
def home():
    return HTML.format(page="")

@app.route("/go")
def go():
    q = request.args.get("q", "")
    url = normalize(q)
    if not url:
        return HTML.format(page="")
    return HTML.format(page="/proxy?url=" + quote(url))

@app.route("/proxy")
def proxy():
    raw_url = request.args.get("url")
    if not raw_url:
        return "No URL provided", 400

    url = unquote(raw_url)

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=25,
            allow_redirects=True
        )
    except requests.exceptions.RequestException as e:
        return f"<h2>Failed to load site</h2><pre>{e}</pre>"

    content_type = r.headers.get("Content-Type", "")

    # If not HTML (images, fonts, etc), stream raw
    if "text/html" not in content_type:
        return Response(r.content, content_type=content_type)

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup.find_all(["a", "img", "script", "link", "iframe"]):
        attr = "href" if tag.name in ["a", "link"] else "src"
        if tag.has_attr(attr):
            new_url = urljoin(url, tag[attr])
            tag[attr] = "/proxy?url=" + quote(new_url)

    return Response(
        str(soup),
        headers={
            "Content-Security-Policy":
                "default-src * data: blob: 'unsafe-inline' 'unsafe-eval';",
            "X-Frame-Options": "ALLOWALL"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)