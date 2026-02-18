from flask import Flask, request, send_file, render_template_string, after_this_request
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>VelociDown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#111] text-white min-h-screen flex items-center justify-center">

<div class="w-full max-w-xl bg-[#1a1a1a] p-6 rounded-xl shadow-xl">

<h1 class="text-3xl font-bold text-center mb-6 text-cyan-400">VelociDown</h1>

<form method="POST" action="/download" class="space-y-4">

<input name="url" required placeholder="Paste YouTube or TikTok link..."
class="w-full p-3 rounded bg-[#111] border border-gray-700 focus:border-cyan-400 outline-none">

<select name="type"
class="w-full p-3 rounded bg-[#111] border border-gray-700 focus:border-cyan-400 outline-none">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button class="w-full bg-cyan-500 hover:bg-cyan-600 p-3 rounded font-bold">
Download
</button>

</form>

{% if msg %}
<p class="mt-4 text-red-400 text-sm break-words">{{ msg }}</p>
{% endif %}

</div>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    filetype = request.form.get("type")

    if not url:
        return render_template_string(HTML, msg="No URL provided")

    filename = str(uuid.uuid4())

    try:
        ydl_opts = {
            "outtmpl": filename + ".%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
        }

        # use cookies if present (fixes YouTube bot block)
        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        # VIDEO (works for YouTube + TikTok)
        if filetype == "video":
            ydl_opts["format"] = "bv*+ba/b"
            ydl_opts["merge_output_format"] = "mp4"

        # AUDIO
        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if filetype == "audio":
            file_path = filename + ".mp3"

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            return response

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return render_template_string(HTML, msg=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)