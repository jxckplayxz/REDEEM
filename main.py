from flask import Flask, request, jsonify, send_from_directory
import os
import random

app = Flask(__name__)

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Upload endpoint
@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith(".webm"):
        return jsonify({"error": "Only .webm files allowed"}), 400

    save_path = os.path.join(VIDEO_DIR, file.filename)
    file.save(save_path)

    return jsonify({"success": True, "filename": file.filename})

# Endpoint to get random video
@app.route("/random_video")
def random_video():
    videos = os.listdir(VIDEO_DIR)
    if not videos:
        return jsonify({"error": "No videos available"}), 404

    video = random.choice(videos)
    return jsonify({"video": video})

# Endpoint to serve videos
@app.route("/videos/<filename>")
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == "__main__":
    app.run(port=5000)