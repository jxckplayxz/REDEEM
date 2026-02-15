from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Video Downloader</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{font-family:Arial;background:#0f2027;color:white;text-align:center;padding:30px}
.container{max-width:420px;margin:auto;background:#111;padding:20px;border-radius:15px}
input,select,button{width:100%;padding:12px;margin:10px 0;border:none;border-radius:8px}
button{background:#00c6ff;color:black;font-weight:bold;cursor:pointer}
button:hover{background:#00a2d4}
</style>
</head>
<body>
<div class="container">
<h2>🎬 Video Downloader</h2>
<form method="POST">
<input name="url" placeholder="Paste TikTok or YouTube link" required>

<select name="quality">
<option value="best">Best Quality</option>
<option value="1080">1080p</option>
<option value="720">720p</option>
<option value="audio">Audio Only</option>
</select>

<button type="submit">Download</button>
</form>
</div>
</body>
</html>
"""

def detect_platform(url):
    if "tiktok.com" in url:
        return "tiktok"
    return "youtube"

def download_video(url, quality, platform):
    filename = str(uuid.uuid4())
    base = f"/tmp/{filename}"

    if quality == "audio":
        ydl_opts = {
            'outtmpl': base + ".mp3",
            'format': 'bestaudio/best',
            'quiet': True
        }
        ext = ".mp3"
    else:
        if platform == "tiktok":
            fmt = "best"
        else:
            if quality == "1080":
                fmt = "bestvideo[height<=1080]+bestaudio/best"
            elif quality == "720":
                fmt = "bestvideo[height<=720]+bestaudio/best"
            else:
                fmt = "bestvideo+bestaudio/best"

        ydl_opts = {
            'outtmpl': base + ".mp4",
            'format': fmt,
            'merge_output_format': 'mp4',
            'quiet': True
        }
        ext = ".mp4"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return base + ext

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        quality = request.form.get("quality")

        try:
            platform = detect_platform(url)
            file_path = download_video(url, quality, platform)

            response = send_file(file_path, as_attachment=True)

            @response.call_on_close
            def cleanup():
                if os.path.exists(file_path):
                    os.remove(file_path)

            return response

        except Exception as e:
            return f"<h3>Error: {str(e)}</h3>"

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()