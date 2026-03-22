import json
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"sections": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', sections=data['sections'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    data = load_data()
    if request.method == 'POST':
        section_name = request.form.get('section_name')
        match_data = {
            "title": request.form.get('title'),
            "url": request.form.get('url'),
            "thumb": request.form.get('thumb') or "https://via.placeholder.com/400x225/111827/FFFFFF?text=No+Image"
        }

        # Find section or create it
        section = next((s for s in data['sections'] if s['name'] == section_name), None)
        if section:
            section['matches'].append(match_data)
        else:
            data['sections'].append({"name": section_name, "matches": [match_data]})
        
        save_data(data)
        return redirect(url_for('admin'))
    
    return render_template('admin.html', sections=data['sections'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)

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
