from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VelociDown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-white min-h-screen flex items-center justify-center">

<div class="w-full max-w-2xl p-6">
<h1 class="text-4xl font-bold mb-6 text-center">⚡ VelociDown</h1>

<!-- DOWNLOAD FORM -->
<form method="POST" action="/download" class="flex gap-2 mb-6">
<input name="url" placeholder="Paste YouTube URL..." required
class="flex-1 p-3 rounded bg-zinc-900 border border-zinc-700 outline-none">
<button class="bg-blue-600 px-6 rounded hover:bg-blue-700">Download</button>
</form>

<!-- SEARCH FORM -->
<form method="POST" action="/search" class="flex gap-2 mb-6">
<input name="query" placeholder="Search videos..." required
class="flex-1 p-3 rounded bg-zinc-900 border border-zinc-700 outline-none">
<button class="bg-green-600 px-6 rounded hover:bg-green-700">Search</button>
</form>

{% if results %}
<div class="space-y-4">
{% for video in results %}
<div class="bg-zinc-900 p-4 rounded flex justify-between items-center">
<div>
<p class="font-semibold">{{ video.title }}</p>
<p class="text-sm text-zinc-400">{{ video.duration }}</p>
</div>
<a href="/download?url={{ video.url }}"
class="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700">DL</a>
</div>
{% endfor %}
</div>
{% endif %}

</div>
</body>
</html>
"""

# 🔎 SEARCH
@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "cookiefile": "cookies.txt",
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)

        for entry in info["entries"]:
            results.append({
                "title": entry.get("title"),
                "url": entry.get("url"),
                "duration": entry.get("duration_string", "N/A"),
            })

    return render_template_string(HTML, results=results)

# ⬇️ DOWNLOAD
@app.route("/download", methods=["GET", "POST"])
def download():
    url = request.values.get("url")

    if not url:
        return "No URL provided"

    filename = f"{uuid.uuid4()}.mp4"

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": filename,
        "cookiefile": "cookies.txt",
        "quiet": True,
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return send_file(filename, as_attachment=True)
    

# 🏠 HOME
@app.route("/")
def home():
    return render_template_string(HTML)