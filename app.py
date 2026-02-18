from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TikTok Downloader</title>
<style>
body {
  margin:0;
  font-family: system-ui;
  background:#0f0f10;
  color:white;
  display:flex;
  justify-content:center;
  align-items:center;
  min-height:100vh;
}

.card {
  width:95%;
  max-width:420px;
  background:#18181b;
  border-radius:20px;
  padding:20px;
  box-shadow:0 0 25px rgba(0,0,0,0.5);
}

h1 {
  font-size:22px;
  margin-bottom:15px;
  text-align:center;
}

input, select, button {
  width:100%;
  padding:14px;
  margin-top:10px;
  border:none;
  border-radius:12px;
  font-size:15px;
}

input, select {
  background:#0f0f10;
  color:white;
}

button {
  background:#22c55e;
  color:black;
  font-weight:bold;
  cursor:pointer;
}

button:hover {
  background:#16a34a;
}

.preview {
  margin-top:15px;
  text-align:center;
}

.preview img {
  width:100%;
  border-radius:12px;
}

.spinner {
  display:none;
  margin:15px auto;
  border:4px solid #333;
  border-top:4px solid #22c55e;
  border-radius:50%;
  width:30px;
  height:30px;
  animation:spin 1s linear infinite;
}

@keyframes spin {
  100% { transform:rotate(360deg); }
}

.icon {
  width:18px;
  vertical-align:middle;
  margin-right:6px;
}
</style>
</head>
<body>
<div class="card">

<h1>📥 TikTok Downloader</h1>

<form method="POST" action="/preview" onsubmit="showSpinner()">
  <input name="url" placeholder="Paste TikTok link" required>
  <button type="submit">🔍 Preview</button>
</form>

{% if thumbnail %}
<div class="preview">
  <img src="{{ thumbnail }}">
  <p>{{ title }}</p>
</div>

<form method="POST" action="/download" onsubmit="showSpinner()">
  <input type="hidden" name="url" value="{{ url }}">

  <select name="type">
    <option value="video">🎬 Video (MP4)</option>
    <option value="audio">🎵 Audio (MP3)</option>
  </select>

  <button type="submit">⬇️ Download</button>
</form>
{% endif %}

<div class="spinner" id="spinner"></div>

</div>

<script>
function showSpinner(){
  document.getElementById("spinner").style.display = "block";
}
</script>

</body>
</html>
"""

def get_info(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)

@app.route("/preview", methods=["POST"])
def preview():
    url = request.form["url"]

    try:
        info = get_info(url)
        thumbnail = info.get("thumbnail")
        title = info.get("title")

        return render_template_string(
            HTML,
            thumbnail=thumbnail,
            title=title,
            url=url
        )
    except:
        return "Invalid TikTok URL"

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    filetype = request.form["type"]

    unique_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)

    if filetype == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path + ".%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True
        }
        final_file = output_path + ".mp3"
    else:
        ydl_opts = {
            "format": "mp4",
            "outtmpl": output_path + ".%(ext)s",
            "quiet": True
        }
        final_file = output_path + ".mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        response = send_file(final_file, as_attachment=True)

        @response.call_on_close
        def cleanup():
            if os.path.exists(final_file):
                os.remove(final_file)

        return response

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run()