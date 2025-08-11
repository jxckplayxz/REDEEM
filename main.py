from flask import Flask, request, Response, render_template_string
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import os
import time

app = Flask(__name__)

# ====== CONFIG ======
ALLOWED_DOMAINS = {"*"}  # allow all
PROXY_SECRET = os.environ.get("PROXY_SECRET", "changeme_secret")
_requests = {}

# ====== HELPERS ======
def simple_rate_limit(key, limit=50, per_seconds=60):
    now = time.time()
    lst = _requests.get(key, [])
    lst = [t for t in lst if now - t < per_seconds]
    if len(lst) >= limit:
        return False
    lst.append(now)
    _requests[key] = lst
    return True

def rewrite_html(body, base_url):
    soup = BeautifulSoup(body, "html.parser")
    from urllib.parse import urljoin
    def rewrite_attr(tag, attr):
        if tag.has_attr(attr):
            val = tag[attr]
            if val.startswith(("data:", "javascript:", "#")):
                return
            abs_url = urljoin(base_url, val)
            tag[attr] = "/proxy?url=" + quote(abs_url, safe='')
    for tag in soup.find_all(True):
        for attribute in ("href", "src", "action", "data-src"):
            try:
                rewrite_attr(tag, attribute)
            except Exception:
                pass
    return str(soup)

# ====== HTML ======
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>About · Ghost</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body { font-family: system-ui, sans-serif; margin:0; padding:40px; background:#f7f7f9; }
    .card { max-width:900px; margin:40px auto; padding:28px; background:white; border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,0.06); }
    h1 { margin:0 0 8px 0; font-size:22px; }
    p { color:#555; line-height:1.5; }
    .small { color:#888; font-size:13px; margin-top:14px; }
    .ghost-frame { display:none; position:fixed; inset:60px 40px 40px 40px; background:#fff; border-radius:10px; box-shadow:0 10px 40px rgba(0,0,0,0.2); overflow:hidden; z-index:9999; }
    .ghost-toolbar { padding:8px 12px; background:#0b1220; color:#fff; display:flex; gap:8px; align-items:center; }
    .ghost-toolbar input { flex:1; padding:6px 8px; border-radius:6px; border:none; font-size:14px; }
    .ghost-iframe { width:100%; height:calc(100% - 42px); border:0; display:block; }
    #hotspot { position: fixed; right: 8px; top: 8px; width:28px; height:28px; z-index:10000; opacity:0.02; cursor:pointer; }
    #hotspot:hover { opacity:0.06; }
    .close-btn { background:transparent; color:#fff; border:0; font-weight:700; font-size:14px; cursor:pointer; padding:6px 10px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>About</h1>
    <p>This is just a normal about page.</p>
    <div class="small">Ghost Proxy</div>
  </div>

  <div id="hotspot" title=" "></div>

  <div id="ghost" class="ghost-frame">
    <div class="ghost-toolbar">
      <button class="close-btn" id="closeGhost">✕</button>
      <input id="ghostUrl" placeholder="Enter URL to proxy" />
      <button id="goBtn">Go</button>
    </div>
    <iframe id="ghostIframe" class="ghost-iframe"></iframe>
  </div>

  <script>
    const hotspot = document.getElementById('hotspot');
    const ghost = document.getElementById('ghost');
    const closeBtn = document.getElementById('closeGhost');
    const goBtn = document.getElementById('goBtn');
    const ghostIframe = document.getElementById('ghostIframe');
    const ghostUrl = document.getElementById('ghostUrl');
    const secret = "changeme_secret"; // put your secret here

    hotspot.addEventListener('click', reveal);
    document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'g') reveal(); });

    function reveal() {
      ghost.style.display = 'block';
      ghostIframe.src = "/proxy?url=" + encodeURIComponent("https://example.com") + "&s=" + encodeURIComponent(secret);
    }
    closeBtn.addEventListener('click', () => { ghost.style.display = 'none'; ghostIframe.src = "about:blank"; });
    goBtn.addEventListener('click', () => {
      const u = ghostUrl.value.trim();
      if (!u) return;
      ghostIframe.src = "/proxy?url=" + encodeURIComponent(u) + "&s=" + encodeURIComponent(secret);
    });
  </script>
</body>
</html>
"""

# ====== ROUTES ======
@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/proxy", methods=["GET","POST"])
def proxy():
    url = request.args.get("url")
    secret = request.args.get("s", "")
    if secret != PROXY_SECRET:
        return Response("Forbidden", status=403)
    if not url:
        return Response("No URL", status=400)
    if not simple_rate_limit(request.remote_addr, limit=50, per_seconds=60):
        return Response("Rate limit exceeded", status=429)

    headers = {'User-Agent': "GhostProxy/1.0"}
    try:
        resp = requests.request(request.method, url, headers=headers, data=request.get_data(), timeout=15, stream=True)
    except Exception as e:
        return Response(f"Upstream error: {e}", status=502)

    content_type = resp.headers.get("Content-Type","")
    body = resp.content
    if "text/html" in content_type:
        try:
            body = rewrite_html(resp.text, resp.url).encode(resp.encoding or "utf-8")
            return Response(body, content_type=content_type)
        except:
            pass

    excluded = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers_out = {k:v for k,v in resp.headers.items() if k.lower() not in excluded}
    return Response(resp.raw.read(), headers=headers_out, status=resp.status_code)

if __name__ == "__main__":
    app.run(debug=True)
