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
<body class="bg-gray-900 text-white p-6">

<h1 class="text-3xl mb-4 font-bold">VelociDown</h1>

<form method="POST" action="/download" class="space-y-3">
<input name="url" placeholder="Paste video URL..." required
class="w-full p-3 rounded bg-gray-800">

<select name="type" class="w-full p-3 rounded bg-gray-800">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button class="bg-blue-600 px-6 py-2 rounded hover:bg-blue-700">Download</button>
</form>

{% if msg %}
<p class="mt-4 text-red-400">{{ msg }}</p>
{% endif %}

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
        # base options
        ydl_opts = {
            "outtmpl": filename + ".%(ext)s",
            "quiet": True,
        }

        # add cookies if available
        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        # audio mode
        if filetype == "audio":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }]
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # fix filename for audio conversion
        if filetype == "audio":
            file_path = filename + ".mp3"

        # delete file after sending (Render disk safe)
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
        return render_template_string(HTML, msg=f"Error: {str(e)}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)