from flask import Flask, request, jsonify, send_file
import os, random

app = Flask(__name__)

UPLOAD_DIR = "ads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def index():
    return """
    <html>
    <head><title>Ad Upload</title></head>
    <body style="background:#111;color:white;font-family:sans-serif">
        <h2>Upload Video Ad</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept=".mp4,.webm" required>
            <br><br>
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    """

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return "No file", 400

    video = request.files["video"]
    if not video.filename.endswith((".mp4", ".webm")):
        return "Invalid format", 400

    path = os.path.join(UPLOAD_DIR, video.filename)
    video.save(path)
    return "Uploaded successfully"

@app.route("/get_ad")
def get_ad():
    ads = [f for f in os.listdir(UPLOAD_DIR) if f.endswith((".mp4", ".webm"))]
    if not ads:
        return jsonify({"error": "No ads"}), 404

    ad = random.choice(ads)
    return jsonify({
        "video_url": f"/video/{ad}"
    })

@app.route("/video/<name>")
def serve_video(name):
    path = os.path.join(UPLOAD_DIR, name)
    return send_file(path, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)