from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid
import shutil
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

progress_dict = {}
history = []

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Velocidown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-[#0a0b10] text-white min-h-screen flex justify-center items-start p-6">

<div class="w-full max-w-md space-y-4">

<h1 class="text-3xl font-extrabold text-center bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
Velocidown
</h1>

<!-- INPUT -->
<div id="dropZone"
class="p-4 border-2 border-dashed border-white/20 rounded-xl text-center text-sm text-gray-400">
Drag & drop links or paste below
</div>

<input id="urlBox" placeholder="Paste multiple links (one per line)..."
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 text-sm">

<select id="quality"
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 text-sm">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button onclick="startQueue()"
class="w-full py-3 rounded-xl font-bold text-black bg-gradient-to-r from-cyan-400 to-blue-500">
Start Download Queue
</button>

<!-- QUEUE -->
<div id="queue" class="space-y-2"></div>

<!-- HISTORY -->
<h2 class="text-lg font-bold mt-6">History</h2>
<div id="history" class="space-y-2 text-xs text-gray-300"></div>

</div>

<script>
const queueDiv = document.getElementById("queue");
const historyDiv = document.getElementById("history");

document.getElementById("dropZone").addEventListener("dragover", e=>{
e.preventDefault();
e.target.classList.add("border-cyan-400");
});

document.getElementById("dropZone").addEventListener("dragleave", e=>{
e.target.classList.remove("border-cyan-400");
});

document.getElementById("dropZone").addEventListener("drop", e=>{
e.preventDefault();
e.target.classList.remove("border-cyan-400");
document.getElementById("urlBox").value = e.dataTransfer.getData("text");
});

function detectPlatform(url){
if(url.includes("youtube")) return "YouTube";
if(url.includes("tiktok")) return "TikTok";
if(url.includes("instagram")) return "Instagram";
if(url.includes("twitter") || url.includes("x.com")) return "Twitter/X";
return "Media";
}

async function startQueue(){
const urls = document.getElementById("urlBox").value.split("\\n").filter(u=>u.trim());
const quality = document.getElementById("quality").value;

for(const url of urls){
const res = await fetch("/start", {
method: "POST",
headers: {"Content-Type": "application/json"},
body: JSON.stringify({url, quality})
});

const data = await res.json();

createQueueItem(data.id, url, data.filesize);
trackProgress(data.id);
}
}

function createQueueItem(id, url, size){
const item = document.createElement("div");
item.id = id;
item.className = "p-3 bg-white/5 rounded-xl text-xs";

item.innerHTML = `
<p class="font-semibold">${detectPlatform(url)} • ${size}</p>
<div class="w-full bg-white/10 rounded-full h-2 mt-1">
<div class="bg-cyan-400 h-2 w-0" id="bar-${id}"></div>
</div>
<p id="percent-${id}" class="text-gray-400">0%</p>
`;

queueDiv.appendChild(item);
}

async function trackProgress(id){
const res = await fetch("/progress/" + id);
const data = await res.json();

document.getElementById("bar-"+id).style.width = data.percent + "%";
document.getElementById("percent-"+id).innerText = data.percent + "%";

if(data.percent < 100){
setTimeout(()=>trackProgress(id), 500);
}else{
window.location = "/download/" + id;
addHistory(id);
}
}

async function addHistory(id){
const res = await fetch("/history");
const data = await res.json();

historyDiv.innerHTML = "";
data.reverse().forEach(item=>{
const div = document.createElement("div");
div.innerText = item;
historyDiv.appendChild(div);
});
}
</script>

</body>
</html>
"""

def base_opts():
    return {
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"}
    }

def get_filesize(url):
    try:
        opts = base_opts()
        opts.update({"skip_download": True})
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            size = info.get("filesize") or info.get("filesize_approx")
            if size:
                return f"{round(size/(1024*1024),2)} MB"
    except:
        pass
    return "Unknown size"

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    url = data["url"]
    quality = data["quality"]

    download_id = str(uuid.uuid4())
    progress_dict[download_id] = 0

    filesize = get_filesize(url)

    def hook(d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%").replace("%","").strip()
            try:
                progress_dict[download_id] = int(float(percent))
            except:
                pass
        if d["status"] == "finished":
            progress_dict[download_id] = 100

    base = os.path.join(DOWNLOAD_DIR, download_id)

    opts = base_opts()
    opts["outtmpl"] = base + ".%(ext)s"
    opts["progress_hooks"] = [hook]

    if quality == "audio":
        if not FFMPEG_AVAILABLE:
            return jsonify({"error": "FFmpeg not installed"})
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3"
            }]
        })
    else:
        opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4"
        })

    def run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        history.append(url)

    threading.Thread(target=run).start()

    return jsonify({"id": download_id, "filesize": filesize})

@app.route("/progress/<id>")
def progress(id):
    return jsonify({"percent": progress_dict.get(id, 0)})

@app.route("/download/<id>")
def download(id):
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith(id):
            return send_file(os.path.join(DOWNLOAD_DIR, file), as_attachment=True)
    return "File not found", 404

@app.route("/history")
def get_history():
    return jsonify(history)

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)