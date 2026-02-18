from flask import Flask, request, send_file, render_template_string, jsonify, after_this_request
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>VelociDown</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-white text-black min-h-screen flex items-center justify-center px-4">

<div class="w-full max-w-2xl">

<h1 class="text-3xl font-bold text-center mb-6">VelociDown</h1>

<div class="flex gap-2">
<input id="url" placeholder="Paste video link..."
class="flex-1 p-4 border rounded-l outline-none">
<button onclick="fetchInfo()" class="bg-black text-white px-6 rounded-r">
Fetch
</button>
</div>

<div id="preview" class="hidden mt-6 text-center">
<img id="thumb" class="mx-auto rounded mb-3 max-h-64">
<p id="title" class="font-semibold"></p>
<p id="duration" class="text-sm text-gray-500 mb-4"></p>

<select id="type" class="p-3 border rounded w-full mb-3">
<option value="video">Download Video (MP4)</option>
<option value="audio">Download Audio (MP3)</option>
</select>

<button onclick="download()"
class="w-full bg-black text-white p-4 rounded font-semibold">
Download
</button>
</div>

<p id="error" class="text-red-500 text-sm mt-4 text-center"></p>

</div>

<script>
async function fetchInfo() {
    document.getElementById("error").innerText = ""
    document.getElementById("preview").classList.add("hidden")

    const url = document.getElementById("url").value

    const res = await fetch("/info", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url})
    })

    const data = await res.json()

    if (data.error) {
        document.getElementById("error").innerText = data.error
        return
    }

    document.getElementById("thumb").src = data.thumbnail
    document.getElementById("title").innerText = data.title
    document.getElementById("duration").innerText = data.duration + " seconds"
    document.getElementById("preview").classList.remove("hidden")
}

function download() {
    const url = document.getElementById("url").value
    const type = document.getElementById("type").value

    const form = document.createElement("form")
    form.method = "POST"
    form.action = "/download"

    const u = document.createElement("input")
    u.name = "url"
    u.value = url
    form.appendChild(u)

    const t = document.createElement("input")
    t.name = "type"
    t.value = type
    form.appendChild(t)

    document.body.appendChild(form)
    form.submit()
}
</script>

</body>
</html>
"""

def safe_filename(title):
    return re.sub(r'[\\\\/*?:"<>|]', "", title)

def base_ydl():
    opts = {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
    }
    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"
    return opts

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/info", methods=["POST"])
def info():
    data = request.get_json()
    url = data.get("url")

    try:
        ydl_opts = base_ydl()
        ydl_opts["skip_download"] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration")
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    filetype = request.form.get("type")

    try:
        ydl_opts = base_ydl()

        # unique temp filename
        uid = str(uuid.uuid4())
        ydl_opts["outtmpl"] = uid + ".%(ext)s"

        if filetype == "video":
            # AUTO FORMAT – NEVER FAILS
            ydl_opts["format"] = "best"
            ydl_opts["merge_output_format"] = "mp4"

        else:
            ydl_opts["format"] = "bestaudio"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = safe_filename(info.get("title", "download"))
        ext = "mp3" if filetype == "audio" else "mp4"

        final_name = f"{title}.{ext}"

        # find downloaded file
        for f in os.listdir():
            if f.startswith(uid):
                os.rename(f, final_name)
                file_path = final_name
                break

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            return response

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)