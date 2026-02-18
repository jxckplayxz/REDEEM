from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Velocidown</title>
<style>
body{
    font-family: Arial, sans-serif;
    background:#f4f4f4;
    margin:0;
    padding:0;
}
.container{
    max-width:500px;
    margin:40px auto;
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1);
}
h1{
    text-align:center;
}
input, select, button{
    width:100%;
    padding:12px;
    margin-top:10px;
    border-radius:8px;
    border:1px solid #ccc;
    font-size:16px;
}
button{
    background:black;
    color:white;
    border:none;
}
button:hover{
    background:#333;
}
.footer{
    text-align:center;
    margin-top:20px;
    font-size:12px;
    color:#777;
}
</style>
</head>
<body>
<div class="container">
<h1>Velocidown</h1>

<form action="/download" method="post">
<input type="text" name="url" placeholder="Paste YouTube or TikTok link" required>

<select name="type">
<option value="video">MP4 Video</option>
<option value="audio">MP3 Audio</option>
</select>

<button type="submit">Download</button>
</form>

<div class="footer">Mobile friendly • No login • Fast</div>
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
    dtype = request.form.get("type")

    file_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, file_id)

    if dtype == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path + ".%(ext)s",
            "noplaylist": True,
            "quiet": True
        }
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_path + ".%(ext)s",
            "noplaylist": True,
            "quiet": True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # uses host port if provided
    app.run(host="0.0.0.0", port=port, debug=False)