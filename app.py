from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>VelociDown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0b10] text-white min-h-screen overflow-y-auto p-6">

<h1 class="text-3xl font-bold mb-4 text-cyan-400">VelociDown</h1>

<!-- SEARCH -->
<div class="mb-6">
<input id="searchBox" placeholder="Search YouTube (ronaldo, edits, etc)"
class="w-full p-3 rounded bg-gray-800 border border-gray-700">

<button onclick="searchVideos()"
class="mt-2 px-4 py-2 bg-cyan-500 rounded">Search</button>
</div>

<div id="results" class="grid gap-4 mb-10"></div>

<hr class="border-gray-700 my-6">

<!-- DIRECT DOWNLOAD -->
<form method="POST" action="/download" class="space-y-3">

<input name="url" placeholder="Paste video URL..." required
class="w-full p-3 rounded bg-gray-800 border border-gray-700">

<select name="quality"
class="w-full p-3 rounded bg-gray-800 border border-gray-700">
<option value="best">Best Quality</option>
<option value="720">720p</option>
<option value="480">480p</option>
<option value="360">360p</option>
</select>

<select name="type"
class="w-full p-3 rounded bg-gray-800 border border-gray-700">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button class="w-full py-3 bg-cyan-500 rounded font-bold">Download</button>

</form>

{% if msg %}
<p class="mt-4 text-red-400">{{ msg }}</p>
{% endif %}

<script>
async function searchVideos(){
let q = document.getElementById("searchBox").value
let res = await fetch("/search?q=" + encodeURIComponent(q))
let data = await res.json()

let container = document.getElementById("results")
container.innerHTML = ""

data.forEach(v => {
container.innerHTML += `
<div class="bg-gray-900 p-3 rounded border border-gray-700">
<img src="${v.thumb}" class="rounded mb-2">
<p class="font-semibold">${v.title}</p>

<form method="POST" action="/download">
<input type="hidden" name="url" value="${v.url}">

<select name="quality" class="w-full mt-2 p-2 bg-gray-800 rounded">
<option value="best">Best</option>
<option value="720">720p</option>
<option value="480">480p</option>
</select>

<select name="type" class="w-full mt-2 p-2 bg-gray-800 rounded">
<option value="video">Video</option>
<option value="audio">Audio</option>
</select>

<button class="w-full mt-2 bg-cyan-500 py-2 rounded">Download</button>
</form>
</div>`
})
}
</script>

</body>
</html>
"""

# ================= HOME =================
@app.route("/")
def home():
    return render_template_string(HTML)

# ================= SEARCH =================
@app.route("/search")
def search():
    query = request.args.get("q")

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)

        for e in info["entries"]:
            results.append({
                "title": e["title"],
                "url": f"https://www.youtube.com/watch?v={e['id']}",
                "thumb": e["thumbnails"][0]["url"] if e.get("thumbnails") else ""
            })

    return jsonify(results)

# ================= DOWNLOAD =================
@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    quality = request.form.get("quality")
    filetype = request.form.get("type")

    filename = str(uuid.uuid4())

    try:
        ydl_opts = {
            "outtmpl": filename + ".%(ext)s",
            "quiet": True,
        }

        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        # QUALITY LOGIC
        if filetype == "video":
            if quality == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            else:
                ydl_opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best"

            ydl_opts["merge_output_format"] = "mp4"

        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if filetype == "audio":
            file_path = filename + ".mp3"

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return render_template_string(HTML, msg=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)