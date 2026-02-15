from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Velocidown</title>
<style>
body{background:#0a0b10;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh}
.container{background:#111;padding:30px;border-radius:15px;width:350px}
input,select,button{width:100%;padding:12px;margin-top:10px;border-radius:10px;border:none}
button{background:#4facfe;color:black;font-weight:bold;cursor:pointer}
.error{color:#ff6b6b;margin-top:10px}
</style>
</head>
<body>
<div class="container">
<h2>Velocidown</h2>
<form method="POST">
<input name="url" placeholder="Paste link" required>
<select name="quality">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>
<button type="submit">Download</button>
</form>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</div>
</body>
</html>"""

DOWNLOAD_DIR = "/tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_media(url, quality):
    uid = str(uuid.uuid4())
    base = os.path.join(DOWNLOAD_DIR, uid)

    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": base + ".%(ext)s",
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

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

    # Fix for mp3 rename after ffmpeg
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