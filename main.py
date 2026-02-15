from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Gemini Video Downloader</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
body{
    margin:0; padding:0;
    font-family:'Inter',sans-serif;
    background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    display:flex;
    justify-content:center;
    align-items:center;
    min-height:100vh;
    color:#fff;
}
.card{
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    border-radius:20px;
    padding:40px 30px;
    max-width:400px;
    width:90%;
    box-shadow: 0 8px 32px rgba(0,0,0,0.37);
    text-align:center;
}
h2{
    margin-bottom:20px;
    font-weight:600;
    font-size:1.8rem;
}
input, select{
    width:100%;
    padding:12px 15px;
    margin:10px 0;
    border:none;
    border-radius:12px;
    background: rgba(255,255,255,0.1);
    color:#fff;
    font-size:1rem;
}
input::placeholder{color:#ddd;}
button{
    width:100%;
    padding:12px;
    margin-top:15px;
    border:none;
    border-radius:12px;
    background: linear-gradient(90deg,#00c6ff,#0072ff);
    color:#000;
    font-weight:600;
    font-size:1rem;
    cursor:pointer;
    transition:0.3s;
}
button:hover{
    background: linear-gradient(90deg,#00ffff,#005eff);
}
.error{
    margin-top:15px;
    color:#ff6b6b;
    font-size:0.9rem;
}
</style>
</head>
<body>
<div class="card">
<h2>Gemini Video Downloader</h2>
<form method="POST">
<input name="url" placeholder="Paste TikTok or YouTube link" required>
<select name="quality">
<option value="best">Best (720p max)</option>
<option value="audio">Audio Only</option>
</select>
<button type="submit">Download</button>
</form>
{% if error %}
<div class="error">{{error}}</div>
{% endif %}
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

    common_opts = {
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        }
    }

    # AUTO RETRY FORMATS
    if quality == "audio":
        ydl_opts = {
            **common_opts,
            'outtmpl': base + ".mp3",
            'format': 'bestaudio[ext=m4a]/bestaudio/best'
        }
        ext = ".mp3"
    else:
        # Mobile-safe YouTube/TikTok format
        if platform == "tiktok":
            fmt_list = ["best", "bestvideo[height<=720]+bestaudio/best"]
        else:
            fmt_list = ["best[height<=720][ext=mp4]","best[ext=mp4]"]

        ext = ".mp4"
        last_err = None
        for fmt in fmt_list:
            ydl_opts = {
                **common_opts,
                'outtmpl': base + ext,
                'format': fmt
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return base + ext
            except Exception as e:
                last_err = e
        raise last_err

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

            if not os.path.exists(file_path):
                return render_template_string(HTML, error="Download failed. Try a different link or shorter video.")

            response = send_file(file_path, as_attachment=True)

            @response.call_on_close
            def cleanup():
                if os.path.exists(file_path):
                    os.remove(file_path)

            return response

        except Exception as e:
            return render_template_string(HTML, error=str(e))

    return render_template_string(HTML, error=None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)