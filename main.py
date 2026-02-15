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

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Velocidown</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0a0b10] text-white flex items-center justify-center min-h-screen overflow-hidden">

<!-- Background blobs -->
<div class="absolute w-72 h-72 bg-cyan-400/30 blur-3xl rounded-full -top-20 -left-20 animate-pulse"></div>
<div class="absolute w-72 h-72 bg-blue-500/30 blur-3xl rounded-full bottom-0 right-0 animate-pulse"></div>

<div class="w-[92%] max-w-md backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">

<h1 class="text-3xl font-extrabold text-center bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
Velocidown
</h1>

<p class="text-center text-gray-400 text-sm mt-1 mb-3">
Swift, high-quality media extraction
</p>

<!-- Search box -->
<div class="flex gap-2">
<input id="searchBox" placeholder="Search videos (e.g., Ronaldo clips)"
class="flex-1 p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">
<button onclick="searchVideos()"
class="px-4 rounded-xl bg-cyan-400 text-black font-bold hover:scale-105 active:scale-95 transition">🔍</button>
</div>

<!-- Search results -->
<div id="results" class="max-h-40 overflow-y-auto text-sm space-y-1"></div>

<!-- Video info panel -->
<div id="metaPanel" class="hidden bg-white/5 rounded-xl p-3 border border-white/10 space-y-2">
<img id="thumb" class="w-full rounded-lg"/>
<p id="title" class="text-sm font-semibold"></p>
<p id="filesize" class="text-xs text-gray-400"></p>
<div class="w-full bg-white/10 rounded-full h-2">
<div id="bar" class="bg-cyan-400 h-2 w-0"></div>
</div>
<p id="percent" class="text-xs text-gray-400 text-right">0%</p>
</div>

<!-- Video preview -->
<div id="preview" class="hidden">
<iframe id="previewFrame" class="w-full aspect-video rounded-xl border border-white/10" allowfullscreen></iframe>
</div>

<!-- URL input + quality -->
<form method="POST" onsubmit="showLoading();return false;" class="space-y-4">
<input id="urlBox" name="url" required
placeholder="Paste link or pick a search result..."
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">

<select id="quality" name="quality"
class="w-full p-3 rounded-xl bg-black/30 border border-white/10 focus:border-cyan-400 outline-none text-sm">
<option value="video">Video (MP4)</option>
<option value="audio">Audio (MP3)</option>
</select>

<button id="dl-btn"
class="w-full py-3 rounded-xl font-bold text-black bg-gradient-to-r from-cyan-400 to-blue-500 hover:scale-[1.02] active:scale-[0.98] transition">
Download
</button>
</form>

<!-- Loading spinner -->
<div id="loading" class="hidden flex flex-col items-center mt-2">
<div class="w-6 h-6 border-4 border-white/20 border-t-cyan-400 rounded-full animate-spin"></div>
<p class="text-xs text-gray-400 mt-2">Processing…</p>
</div>

{% if error %}
<div class="mt-4 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-2 text-center">
{{error}}
</div>
{% endif %}

</div>

<script>
// Loading
function showLoading(){
document.getElementById("dl-btn").style.display="none";
document.getElementById("loading").style.display="flex";
startDownload();
}

// Preview update
function updatePreview(url){
const frame = document.getElementById("previewFrame");
const preview = document.getElementById("preview");
if(url.includes("youtube") || url.includes("youtu.be")){
let id = url.split("v=")[1]?.split("&")[0] || url.split("/").pop();
frame.src = "https://www.youtube.com/embed/"+id;
preview.classList.remove("hidden");
}else{
preview.classList.add("hidden");
frame.src="";
}
}

// Search functionality
async function searchVideos(){
const query = document.getElementById("searchBox").value;
const resultsDiv = document.getElementById("results");
if(!query) return;
resultsDiv.innerHTML = "<p class='text-gray-400 text-xs'>Searching...</p>";
const res = await fetch("/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query})});
const data = await res.json();
resultsDiv.innerHTML = "";
data.forEach(video=>{
const item = document.createElement("div");
item.className="p-2 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition";
item.innerHTML=`<p class="font-semibold">${video.title}</p><p class="text-xs text-gray-400">${video.duration}</p>`;
item.onclick=()=>{
document.getElementById("urlBox").value=video.webpage_url;
document.getElementById("thumb").src=video.thumbnail;
document.getElementById("title").innerText=video.title;
document.getElementById("metaPanel").classList.remove("hidden");
updatePreview(video.webpage_url);
};
resultsDiv.appendChild(item);
});
}

// Download
async function startDownload(){
const url=document.getElementById("urlBox").value;
const quality=document.getElementById("quality").value;
document.getElementById("metaPanel").classList.remove("hidden");

const res=await fetch("/start",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,quality})});
const data=await res.json();
document.getElementById("filesize").innerText="Size: "+data.filesize;

trackProgress(data.id);
}

// Track progress
async function trackProgress(id){
const res=await fetch("/progress/"+id);
const data=await res.json();
document.getElementById("bar").style.width=data.percent+"%";
document.getElementById("percent").innerText=data.percent+"%";
if(data.percent<100){setTimeout(()=>trackProgress(id),500);}
else{window.location="/download/"+id;}
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

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query")
    opts = base_opts()
    opts.update({"extract_flat": True, "skip_download": True})
    results=[]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch50:{query}", download=False)  # fetch 50 results
        for e in info.get("entries",[]):
            if e:
                results.append({
                    "title": e.get("title"),
                    "webpage_url": e.get("url"),
                    "duration": e.get("duration_string","N/A"),
                    "thumbnail": e.get("thumbnail")
                })
    return jsonify(results)

def get_filesize(url):
    try:
        opts = base_opts()
        opts.update({"skip_download": True})
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            size = info.get("filesize") or info.get("filesize_approx")
            if size: return f"{round(size/(1024*1024),2)} MB"
    except:
        pass
    return "Unknown"

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    url = data["url"]
    quality = data["quality"]
    download_id = str(uuid.uuid4())
    progress_dict[download_id]=0
    filesize = get_filesize(url)

    def hook(d):
        if d["status"]=="downloading":
            try: progress_dict[download_id]=int(float(d.get("_percent_str","0%").replace("%","").strip()))
            except: pass
        if d["status"]=="finished": progress_dict[download_id]=100

    base = os.path.join(DOWNLOAD_DIR,download_id)
    opts = base_opts()
    opts["outtmpl"]=base+".%(ext)s"
    opts["progress_hooks"]=[hook]

    if quality=="audio":
        if not FFMPEG_AVAILABLE: return jsonify({"error":"FFmpeg not installed"})
        opts.update({"format":"bestaudio/best","postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3"}]})
    else:
        opts.update({"format":"bestvideo+bestaudio/best","merge_output_format":"mp4"})

    def run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    threading.Thread(target=run).start()
    return jsonify({"id":download_id,"filesize":filesize})

@app.route("/progress/<id>")
def progress(id):
    return jsonify({"percent":progress_dict.get(id,0)})

@app.route("/download/<id>")
def download(id):
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith(id):
            return send_file(os.path.join(DOWNLOAD_DIR,file),as_attachment=True)
    return "File not found",404

@app.route("/")
def index():
    return render_template_string(HTML,error=None)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)