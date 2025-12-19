from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (AdvancedProxyBrowser)"
}

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Advanced Proxy Browser</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b0b0b;color:white;font-family:Arial}
header{background:#111;padding:10px;display:flex;gap:10px}
input{flex:1;padding:10px;background:#1a1a1a;color:white;border:none;border-radius:6px}
button{padding:10px 18px;background:#4f46e5;border:none;color:white;border-radius:6px;cursor:pointer}
iframe{width:100%;height:calc(100vh - 60px);border:none}
footer{font-size:12px;color:#777;text-align:center;padding:5px}
</style>
</head>
<body>
<header>
<form action="/go" method="get" style="display:flex;width:100%;gap:10px">
<input name="q" placeholder="Search or enter URL">
<button>Go</button>
</form>
</header>
<iframe src="{page}"></iframe>
<footer>Advanced Python Proxy • Single-file</footer>
</body>
</html>
"""

def normalize(target):
    if " " in target:
        return f"https://duckduckgo.com/html/?q={quote(target)}"
    if not target.startswith("http"):
        return "https://" + target
    return target

@app.route("/")
def home():
    return BASE_HTML.format(page="")

@app.route("/go")
def go():
    q = request.args.get("q", "")
    if not q:
        return BASE_HTML.format(page="")
    url = normalize(q)
    return BASE_HTML.format(page="/proxy?url=" + quote(url))

@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return ""

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
    except:
        return "Failed to load page"

    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup.find_all(["a", "img", "script", "link", "iframe"]):
        attr = "href" if tag.name in ["a", "link"] else "src"
        if tag.has_attr(attr):
            tag[attr] = "/proxy?url=" + quote(urljoin(url, tag[attr]))

    return Response(str(soup), headers={
        "Content-Security-Policy": "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)