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
<title>FluxDL</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#07090f] text-white min-h-screen overflow-y-auto">

<div class="max-w-xl mx-auto p-6">

<h1 class="text-4xl font-extrabold text-center bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
FluxDL
</h1>

<p class="text-center text-gray-400 text-sm mt-1 mb-6">Fast media search & downloader</p>

<!-- SEARCH -->
<div class="flex gap-2">
<input id="searchInput" placeholder="Search videos..."
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none">
<button onclick="searchVideos()" class="px-4 bg-gradient-to-r from-cyan-400 to-blue-500 text-black rounded-xl font-bold">🔍</button>
</div>

<div id="results" class="mt-6 space-y-6"></div>

</div>

<script>
async function searchVideos(){
let q = document.getElementById("searchInput").value
if(!q) return

let res = await fetch("/search?q="+encodeURIComponent(q))
let data = await res.json()

let results = document.getElementById("results")
results.innerHTML=""

if(data.length === 0){
results.innerHTML="<p class='text-gray-400 text-sm'>No results</p>"
return
}

data.forEach(v=>{
results.innerHTML += `
<div class="bg-white/5 p-3 rounded-xl border border-white/10">

<img src="${v.thumb}" class="rounded-lg mb-2">

<p class="text-sm font-bold">${v.title}</p>

<video controls class="w-full mt-2 rounded-lg">
<source src="${v.preview}">
</video>

<div class="grid grid-cols-2 gap-2 mt-3">

<button onclick="download('${v.url}','360')" class="bg-cyan-400 text-black py-2 rounded-lg text-sm">360p</button>
<button onclick="download('${v.url}','720')" class="bg-cyan-400 text-black py-2 rounded-lg text-sm">720p</button>
<button onclick="download('${v.url}','1080')" class="bg-cyan-400 text-black py-2 rounded-lg text-sm">1080p</button>
<button onclick="download('${v.url}','mp3')" class="bg-purple-400 text-black py-2 rounded-lg text-sm">MP3</button>

</div>

</div>`
})
}

function download(url, quality){
let form = document.createElement("form")
form.method="POST"
form.action="/download"
form.innerHTML=`
<input name="url" value="${url}">
<input name="quality" value="${quality}">
`
document.body.appendChild(form)
form.submit()
}
</script>

</body>
</html>
"""

def base_opts():
    opts = {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"}
    }

    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"

    return opts

@app.route("/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify([])

    try:
        ydl_opts = base_opts()
        ydl_opts.update({"skip_download": True})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch8:{q}", download=False)

        results = []
        for v in info.get("entries", []):
            results.append({
                "title": v.get("title"),
                "url": v.get("webpage_url"),
                "thumb": v.get("thumbnail"),
                "preview": v.get("url")
            })

        return jsonify(results)

    except Exception as e:
        print(e)
        return jsonify([])

def download_media(url, quality):
    uid = str(uuid.uuid4())
    base = os.path.join(DOWNLOAD_DIR, uid)

    ydl_opts = base_opts()
    ydl_opts["outtmpl"] = base + ".%(ext)s"

    if quality == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        height = quality
        ydl_opts.update({
            "format": f"bestvideo[height<={height}]+bestaudio/best",
            "merge_output_format": "mp4"
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

    if quality == "mp3":
        file = base + ".mp3"

    return file

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    quality = request.form.get("quality")

    try:
        file_path = download_media(url, quality)

        if not os.path.exists(file_path):
            return "Download failed"

        response = send_file(file_path, as_attachment=True)

        @response.call_on_close
        def cleanup():
            if os.path.exists(file_path):
                os.remove(file_path)

        return response

    except Exception as e:
        print(e)
        return "Download error"

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)