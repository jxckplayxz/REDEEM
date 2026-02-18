from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Velocidown</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<style>
body{font-family:Inter;background:#f9fafb;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;}
.container{max-width:420px;width:92%;background:#fff;padding:40px;border-radius:28px;
box-shadow:0 10px 20px rgba(0,0,0,.05);text-align:center;}
h1{margin:0 0 15px;font-weight:800;}

input{width:100%;padding:16px;border-radius:14px;border:2px solid #e5e7eb;font-size:14px;}
input:focus{border-color:black;outline:none;}

.preview{margin:15px 0;padding:10px;border-radius:16px;background:#f3f4f6;display:none;text-align:left;}
.preview img{width:100%;border-radius:12px;margin-bottom:8px;}
.preview-title{font-size:14px;font-weight:700;}
.preview-meta{font-size:12px;color:#6b7280;}

.quality-toggle{display:flex;background:#e5e7eb;padding:4px;border-radius:12px;margin:12px 0;}
.q-btn{flex:1;padding:10px;font-size:12px;font-weight:700;border:none;background:transparent;border-radius:9px;cursor:pointer;}
.q-btn.active{background:white;}

button{width:100%;height:56px;background:black;color:white;border:none;border-radius:14px;
font-weight:700;font-size:15px;cursor:pointer;position:relative;overflow:hidden;margin-top:10px;}

.progress{position:absolute;left:0;top:0;height:100%;width:0;background:rgba(255,255,255,.2);transition:.3s;}
.footer{margin-top:15px;font-size:11px;color:#9ca3af;font-weight:600;}
</style>
</head>

<body>

<div class="container">
<h1>Velocidown</h1>

<input type="url" id="url" placeholder="Paste TikTok or YouTube link">

<div class="preview" id="preview">
<img id="thumb">
<div class="preview-title" id="title"></div>
<div class="preview-meta" id="meta"></div>
</div>

<div class="quality-toggle">
<button class="q-btn active" onclick="setQ(this,'HD')">HD</button>
<button class="q-btn" onclick="setQ(this,'SD')">SD</button>
<button class="q-btn" onclick="setQ(this,'MP3')">MP3</button>
</div>

<button onclick="fetchMeta()">Fetch Info</button>

<button onclick="download()" id="dlBtn">
<div class="progress" id="progress"></div>
<span id="btnTxt">Download</span>
</button>

<div class="footer">SECURE • FAST • UNLIMITED</div>
</div>

<script>
let quality="HD";

function setQ(el,q){
document.querySelectorAll('.q-btn').forEach(b=>b.classList.remove('active'));
el.classList.add('active');
quality=q;
}

async function fetchMeta(){
const url=document.getElementById("url").value;
if(!url) return;

const res=await fetch("/meta",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({url})});

const data=await res.json();

if(data.error){
alert(data.error);
return;
}

document.getElementById("preview").style.display="block";
document.getElementById("thumb").src=data.thumbnail;
document.getElementById("title").innerText=data.title;
document.getElementById("meta").innerText=data.duration || "";
}

async function download(){
const url=document.getElementById("url").value;
const btnTxt=document.getElementById("btnTxt");
const prog=document.getElementById("progress");

btnTxt.innerText="Processing...";
prog.style.width="40%";

const formData=new FormData();
formData.append("url",url);
formData.append("quality",quality);

const res=await fetch("/download",{method:"POST",body:formData});

prog.style.width="80%";

if(!res.ok){
btnTxt.innerText="Error";
prog.style.width="0%";
return;
}

const blob=await res.blob();
prog.style.width="100%";

const a=document.createElement("a");
a.href=URL.createObjectURL(blob);

let filename="video.mp4";
const cd=res.headers.get("Content-Disposition");
if(cd && cd.includes("filename=")){
filename=cd.split("filename=")[1].replace(/"/g,"");
}

a.download=filename;
a.click();

btnTxt.innerText="Success ✓";

setTimeout(()=>{
prog.style.width="0%";
btnTxt.innerText="Download";
},2000);
}
</script>

</body>
</html>
"""

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)