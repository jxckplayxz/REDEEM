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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Velocidown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0b10] text-white flex items-center justify-center min-h-screen overflow-hidden">

<div class="absolute w-72 h-72 bg-cyan-400/30 blur-3xl rounded-full -top-20 -left-20 animate-pulse"></div>
<div class="absolute w-72 h-72 bg-blue-500/30 blur-3xl rounded-full bottom-0 right-0 animate-pulse"></div>

<div class="w-[95%] max-w-md backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">

<h1 class="text-3xl font-extrabold text-center bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
Velocidown
</h1>

<!-- SEARCH -->
<div class="flex gap-2">
<input id="searchBox" placeholder="Search ronaldo clips..."
class="flex-1 p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">

<button onclick="searchVideos()"
class="px-4 rounded-xl bg-cyan-400 text-black font-bold hover:scale-105 active:scale-95 transition">
🔍
</button>
</div>

<!-- RESULTS -->
<div id="results" class="space-y-2 max-h-40 overflow-y-auto text-sm"></div>

<form method="POST" onsubmit="showLoading()" class="space-y-4">

<input id="urlBox" name="url" required
placeholder="Paste link or pick a search result..."
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">

<select name="quality"
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button id="dl-btn"
class="w-full py-3 rounded-xl font-bold text-black bg-gradient-to-r from-cyan-400 to-blue-500 hover:scale-[1.02] active:scale-[0.98] transition">
Download
</button>

</form>

<div id="loading" class="hidden flex flex-col items-center mt-2">
<div class="w-6 h-6 border-4 border-white/20 border-t-cyan-400 rounded-full animate-spin"></div>
<p class="text-xs text-gray-400 mt-2">Processing…</p>
</div>

{% if error %}
<div class="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-2 text-center">
{{error}}
</div>
{% endif %}

</div>

<script>
function showLoading(){
document.getElementById("dl-btn").style.display="none";
document.getElementById("loading").style.display="flex";
}

async function searchVideos(){
const query = document.getElementById("searchBox").value;
const resultsDiv = document.getElementById("results");

if(!query) return;

resultsDiv.innerHTML = "<p class='text-gray-400 text-xs'>Searching...</p>";

const res = await fetch("/search", {
method: "POST",
headers: {"Content-Type": "application/json"},
body: JSON.stringify({query})
});

const data = await res.json();

resultsDiv.innerHTML = "";

data.forEach(video => {
const item = document.createElement("div");
item.className = "p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition";
item.innerHTML = `
<p class="font-semibold">${video.title}</p>
<p class="text-xs text-gray-400">${video.duration}</p>
`;

item.onclick = () => {
document.getElementById("urlBox").value = video.url;
};

resultsDiv.appendChild(item);
});
}
</script>

</body>
</html>
"""

def ydl_base_opts():
    return {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    }

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query")

    ydl_opts = ydl_base_opts()
    ydl_opts.update({
        "extract_flat": True,
        "skip_download": True
    })

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch8:{query}", download=False)
        for entry in info["entries"]:
            if entry:
                results.append({
                    "title": entry.get("title"),
                    "url": entry.get("url"),
                    "duration": entry.get("duration_string", "N/A")
                })

    return jsonify(results)

def download_media(url, quality):
    uid = str(uuid.uuid4())
    base = os.path.join(DOWNLOAD_DIR, uid)

    ydl_opts = ydl_base_opts()
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
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4"
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if quality == "audio":
        filename = base + ".mp3"

    return filename

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        quality = request.form.get("quality")

        try:
            file_path = download_media(url, quality)

            if not os.path.exists(file_path):
                return render_template_string(HTML, error="Download failed.")

            response = send_file(file_path, as_attachment=True)

            @response.call_on_close
            def cleanup():
                if os.path.exists(file_path):
                    os.remove(file_path)

            return response

        except Exception as e:
            print(e)
            return render_template_string(HTML, error="Invalid link or FFmpeg missing.")

    return render_template_string(HTML, error=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)