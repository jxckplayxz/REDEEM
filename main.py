from flask import Flask, request, jsonify, send_from_directory
import os
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Allowed extension
ALLOWED_EXTENSIONS = {"webm"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------
# Upload Endpoint
# ------------------------
@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only .webm files allowed"}), 400

    # Secure the filename and lowercase it
    filename = secure_filename(file.filename).lower()
    save_path = os.path.join(VIDEO_DIR, filename)
    file.save(save_path)
    return jsonify({"success": True, "filename": filename})

# ------------------------
# Random Video Endpoint
# ------------------------
@app.route("/random_video")
def random_video():
    videos = [v for v in os.listdir(VIDEO_DIR) if allowed_file(v)]
    if not videos:
        return jsonify({"error": "No videos available"}), 404
    video = random.choice(videos)
    return jsonify({"video": video})

# ------------------------
# Serve Video Files
# ------------------------
@app.route("/videos/<filename>")
def serve_video(filename):
    filename = filename.lower()
    if not os.path.isfile(os.path.join(VIDEO_DIR, filename)):
        return "File not found", 404
    return send_from_directory(VIDEO_DIR, filename)

# ------------------------
# Run Server
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)