from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Velocidown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0b10] text-white min-h-screen overflow-y-auto">

<div class="absolute w-72 h-72 bg-cyan-400/30 blur-3xl rounded-full -top-20 -left-20 animate-pulse"></div>
<div class="absolute w-72 h-72 bg-blue-500/30 blur-3xl rounded-full bottom-0 right-0 animate-pulse"></div>

<div class="relative max-w-xl mx-auto p-6">

<h1 class="text-3xl font-extrabold text-center bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
Velocidown
</h1>

<!-- SEARCH -->
<div class="mt-6 flex gap-2">
<input id="searchInput" placeholder="Search videos (e.g. ronaldo clips)"
class="w-full p-3 rounded-xl bg-black/30 border border-white/10">
<button onclick="searchVideos()" class="px-4 bg-cyan-400 text-black rounded-xl">🔍</button>
</div>

<div id="results" class="mt-6 space-y-4"></div>

<!-- DOWNLOAD FORM -->
<form method="POST" class="space-y-4 mt-6">

<input name="url" required placeholder="Paste video link..."
class="w-full p-3 rounded-xl bg-black/30 border border-white/10">

<select name="quality"
class="w-full p-3 rounded-xl bg-black/30 border border-white/10">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button class="w-full py-3 rounded-xl font-bold text-black bg-gradient-to-r from-cyan-400 to-blue-500">
Download
</button>

</form>

{% if preview %}
<div class="mt-6">
<video controls class="rounded-xl w-full">
<source src="{{preview}}">
</video>
</div>
{% endif %}

{% if error %}
<div class="mt-4 text-red-400">{{error}}</div>
{% endif %}

</div>

<script>
async function searchVideos(){
let q = document.getElementById("searchInput").value
let res = await fetch("/search?q="+encodeURIComponent(q))
let data = await res.json()

let results = document.getElementById("results")
results.innerHTML=""

data.forEach(v=>{
results.innerHTML += `
<div class="bg-white/5 p-3 rounded-xl border border-white/10">
<img src="${v.thumb}" class="rounded-lg mb-2">
<p class="text-sm font-bold">${v.title}</p>
<button onclick="download('${v.url}')" class="mt-2 px-3 py-2 bg-cyan-400 text-black rounded-lg">
Download
</button>
</div>`
})
}

function download(url){
let form = document.createElement("form")
form.method="POST"
form.innerHTML=`<input name="url" value="${url}">
<input name="quality" value="video">`
document.body.appendChild(form)
form.submit()
}
</script>

</body>
</html>
"""

def get_opts():
    return {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None
    }

def download_media(url, quality):
    uid = str(uuid.uuid4())
    base = os.path.join(DOWNLOAD_DIR, uid)

    ydl_opts = get_opts()
    ydl_opts["outtmpl"] = base + ".%(ext)s"

    if quality == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        ydl_opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4"
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

    if quality == "audio":
        file = base + ".mp3"

    return file

@app.route("/search")
def search():
    q = request.args.get("q")

    ydl_opts = get_opts()
    ydl_opts.update({"skip_download": True})

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{q}", download=False)

    results = []
    for v in info["entries"]:
        results.append({
            "title": v["title"],
            "url": v["webpage_url"],
            "thumb": v.get("thumbnail")
        })

    return jsonify(results)

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        quality = request.form.get("quality")

        try:
            file_path = download_media(url, quality)

            if not os.path.exists(file_path):
                return render_template_string(HTML, error="Download failed.", preview=None)

            response = send_file(file_path, as_attachment=True)

            @response.call_on_close
            def cleanup():
                if os.path.exists(file_path):
                    os.remove(file_path)

            return response

        except Exception as e:
            print(e)
            return render_template_string(HTML, error=str(e), preview=None)

    return render_template_string(HTML, error=None, preview=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)