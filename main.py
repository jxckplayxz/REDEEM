from flask import Flask, request, Response, render_template_string, redirect, url_for
import requests
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

# HTML for homepage
home_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Ghost Proxy</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #0d0d0d;
            color: white;
            text-align: center;
            padding: 50px;
        }
        .nav {
            margin-bottom: 30px;
        }
        .nav a {
            color: #00ffcc;
            margin: 0 15px;
            text-decoration: none;
            font-weight: bold;
        }
        input[type=text] {
            width: 60%;
            padding: 10px;
            border-radius: 5px;
            border: none;
        }
        button {
            padding: 10px 20px;
            border: none;
            background: #00ffcc;
            color: black;
            font-weight: bold;
            cursor: pointer;
            border-radius: 5px;
        }
        iframe {
            width: 100%;
            height: 80vh;
            border: none;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/ghost">Ghost</a>
    </div>
    <h1>Welcome to Ghost Proxy</h1>
    <p>Type a website URL below to browse anonymously.</p>
    <form action="/ghost" method="get">
        <input type="text" name="url" placeholder="https://example.com" required>
        <button type="submit">Go</button>
    </form>
</body>
</html>
"""

# About page HTML
about_html = """
<!DOCTYPE html>
<html>
<head>
    <title>About - Ghost Proxy</title>
    <style>
        body {
            background: #0d0d0d;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
        }
        a { color: #00ffcc; }
    </style>
</head>
<body>
    <h1>About Ghost Proxy</h1>
    <p>This proxy hides your real IP by routing requests through our server.</p>
    <p><a href="/">Back to Home</a></p>
</body>
</html>
"""

# Proxy function
@app.route("/ghost")
def ghost():
    target_url = request.args.get("url", "")
    if not target_url:
        return render_template_string(home_html)

    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    try:
        # Fetch content from target
        r = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        content = r.text

        # Rewrite links so they stay in proxy
        parsed_url = urlparse(target_url)
        base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        content = content.replace('href="/', f'href="/ghost?url={base}/')
        content = content.replace('src="/', f'src="/ghost?url={base}/')
        return Response(content, content_type=r.headers.get("Content-Type", "text/html"))

    except Exception as e:
        return f"<h1 style='color:red'>Error loading {target_url}: {e}</h1>"

@app.route("/")
def home():
    return render_template_string(home_html)

@app.route("/about")
def about():
    return render_template_string(about_html)

if __name__ == "__main__":
    app.run(debug=True)
