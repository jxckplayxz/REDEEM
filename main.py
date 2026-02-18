from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """YOUR_HTML_HERE"""  # keep your existing HTML exactly as-is

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/meta", methods=["POST"])
def meta():
    data = request.get_json()
    url = data.get("url")

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        duration = info.get("duration")
        if duration:
            mins = duration // 60
            secs = duration % 60
            duration = f"{mins}:{secs:02d}"

        return jsonify({
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": duration
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    quality = request.form.get("quality")

    file_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_FOLDER, file_id)

    if quality == "MP3":
        ydl_opts = {"format": "bestaudio/best","outtmpl": output_path + ".%(ext)s","quiet": True}
    elif quality == "SD":
        ydl_opts = {"format": "worst[ext=mp4]/worst","outtmpl": output_path + ".%(ext)s","quiet": True}
    else:
        ydl_opts = {"format": "best[ext=mp4]/best","outtmpl": output_path + ".%(ext)s","quiet": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == "__main__":
    # 🔥 DEFAULT LOCAL PORT = 5000
    # Hosting services will override with their own PORT env var
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)