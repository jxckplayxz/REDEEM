from flask import Flask, request, send_file, render_template_string
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Rebranded Modern UI with Glassmorphism and Animations
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Velocidown | Premium Media Downloader</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/js/all.min.js"></script>
    <style>
        :root {
            --primary: #00f2fe;
            --secondary: #4facfe;
            --bg: #0a0b10;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: radial-gradient(circle at top right, #16213e, #0a0b10);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            overflow: hidden;
        }

        /* Animated Background Blobs */
        .blob {
            position: absolute;
            width: 300px;
            height: 300px;
            background: var(--secondary);
            filter: blur(80px);
            border-radius: 50%;
            z-index: -1;
            opacity: 0.2;
            animation: move 10s infinite alternate;
        }

        @keyframes move {
            from { transform: translate(-50%, -50%); }
            to { transform: translate(50%, 50%); }
        }

        .container {
            background: var(--glass);
            backdrop-filter: blur(15px);
            border: 1px solid var(--glass-border);
            padding: 40px;
            border-radius: 24px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            animation: fadeIn 0.8s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        p { color: #94a3b8; font-size: 0.9rem; margin-bottom: 30px; }

        .input-group { position: relative; margin-bottom: 20px; }

        input, select {
            width: 100%;
            padding: 14px 16px;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: white;
            box-sizing: border-box;
            transition: 0.3s;
            outline: none;
        }

        input:focus { border-color: var(--primary); box-shadow: 0 0 15px rgba(0, 242, 254, 0.2); }

        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(45deg, var(--secondary), var(--primary));
            border: none;
            border-radius: 12px;
            color: #000;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(79, 172, 254, 0.4);
        }

        button:active { transform: translateY(0); }

        .loading { display: none; margin-top: 20px; }
        .spinner {
            width: 24px; height: 24px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: auto;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .error {
            background: rgba(255, 107, 107, 0.1);
            color: #ff6b6b;
            padding: 10px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.85rem;
            border: 1px solid rgba(255, 107, 107, 0.2);
        }
    </style>
</head>
<body>
    <div class="blob"></div>
    <div class="container">
        <h1>Velocidown</h1>
        <p>Swift, high-quality media extraction.</p>

        <form method="POST" onsubmit="showLoading()">
            <div class="input-group">
                <input type="text" name="url" placeholder="Paste link here..." required>
            </div>

            <select name="quality" style="margin-bottom: 20px;">
                <option value="best">Video (MP4 High)</option>
                <option value="audio">Audio (MP3 High)</option>
            </select>

            <button type="submit" id="dl-btn">
                <i class="fas fa-download"></i> Fetch Content
            </button>
        </form>

        <div id="loading-state" class="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; font-size: 0.8rem;">Processing your request...</p>
        </div>

        {% if error %}
        <div class="error">
            <i class="fas fa-exclamation-circle"></i> {{error}}
        </div>
        {% endif %}
    </div>

    <script>
        function showLoading() {
            document.getElementById('dl-btn').style.display = 'none';
            document.getElementById('loading-state').style.display = 'block';
        }
    </script>
</body>
</html>
"""

# Rest of the logic remains the same as your functional original
def detect_platform(url):
    return "tiktok" if "tiktok.com" in url else "youtube"

def download_video(url, quality, platform):
    filename = str(uuid.uuid4())
    base = f"/tmp/{filename}"
    
    common_opts = {
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        }
    }

    if quality == "audio":
        ydl_opts = {**common_opts, 'outtmpl': base + ".mp3", 'format': 'bestaudio/best'}
        ext = ".mp3"
    else:
        fmt = "best" if platform == "tiktok" else "best[height<=720][ext=mp4]"
        ydl_opts = {**common_opts, 'outtmpl': base + ".mp4", 'format': fmt}
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
            if not os.path.exists(file_path):
                return render_template_string(HTML, error="Resource unreachable. Check link.")
            
            response = send_file(file_path, as_attachment=True)
            @response.call_on_close
            def cleanup():
                if os.path.exists(file_path): os.remove(file_path)
            return response
        except Exception as e:
            return render_template_string(HTML, error="An error occurred processing the media.")
    return render_template_string(HTML, error=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
