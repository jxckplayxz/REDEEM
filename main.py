from flask import Flask, request, send_file, render_template_string, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# THE UI CODE
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Velocidown | TikTok</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg: #f9fafb;
            --card: #ffffff;
            --text: #111827;
            --border: #e5e7eb;
            --primary: #000000;
            --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
            --smooth: cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex; align-items: center; justify-content: center;
            min-height: 100vh; margin: 0;
        }

        #notification {
            position: fixed; top: -100px; left: 50%; transform: translateX(-50%);
            background: #1f2937; color: white; padding: 16px 24px;
            border-radius: 16px; font-weight: 600; font-size: 14px;
            display: flex; align-items: center; gap: 10px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            transition: transform 0.6s var(--spring), opacity 0.3s;
            z-index: 9999; opacity: 0;
        }
        #notification.show { transform: translateX(-50%) translateY(130px); opacity: 1; }

        .container {
            max-width: 420px; width: 92%;
            background: var(--card);
            padding: 45px 40px; border-radius: 32px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
            border: 1px solid var(--border);
            text-align: center;
        }

        .header { margin-bottom: 35px; }
        .header i { font-size: 48px; color: var(--primary); margin-bottom: 12px; }
        h1 { margin: 0; font-weight: 800; font-size: 1.8rem; letter-spacing: -0.04em; }

        #previewCard {
            max-height: 0; opacity: 0; visibility: hidden;
            background: #f3f4f6; border-radius: 20px;
            transition: max-height 0.5s var(--spring), opacity 0.3s, margin 0.4s;
            display: flex; align-items: center; gap: 15px;
            overflow: hidden; text-align: left;
        }
        #previewCard.active { max-height: 150px; opacity: 1; visibility: visible; margin-bottom: 24px; padding: 15px; }

        #thumb { width: 50px; height: 65px; object-fit: cover; border-radius: 10px; background: #ddd; }

        .quality-toggle { display: flex; background: #e5e7eb; padding: 4px; border-radius: 12px; margin-top: 6px; gap: 4px; }
        .q-btn { flex: 1; padding: 8px; font-size: 12px; font-weight: 700; border-radius: 9px; border: none; color: #6b7280; background: transparent; cursor: pointer; transition: 0.2s; }
        .q-btn.active { background: white; color: black; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

        .input-group { position: relative; margin-bottom: 16px; }
        input {
            width: 100%; background: white;
            border: 2px solid var(--border); padding: 18px 60px 18px 20px;
            border-radius: 18px; color: var(--text); font-size: 15px; outline: none;
            box-sizing: border-box; transition: all 0.3s var(--smooth);
        }
        input:focus { border-color: var(--primary); }

        .paste-btn {
            position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
            color: #6b7280; cursor: pointer; font-size: 13px; font-weight: 700;
        }

        button.dl-btn {
            width: 100%; height: 64px; background: var(--primary); color: white;
            border: none; border-radius: 18px; font-weight: 700; font-size: 16px;
            cursor: pointer; position: relative; overflow: hidden;
            transition: transform 0.3s var(--spring), background 0.3s;
        }
        button.dl-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        
        .progress-fill { position: absolute; left: 0; top: 0; height: 100%; width: 0%; background: rgba(255, 255, 255, 0.2); transition: width 0.4s var(--smooth); }
        .btn-content { position: relative; z-index: 2; display: flex; align-items: center; justify-content: center; gap: 10px; }

        .footer { text-align: center; margin-top: 24px; font-size: 11px; color: #9ca3af; font-weight: 600; letter-spacing: 0.8px; }
    </style>
</head>
<body>

<div id="notification">
    <i class="fa-solid fa-circle-exclamation"></i>
    <span id="notifMsg"></span>
</div>

<div class="container">
    <div class="header">
        <i class="fa-brands fa-tiktok"></i>
        <h1>Velocidown</h1>
    </div>

    <div id="previewCard">
        <img id="thumb" src="" alt="">
        <div style="flex: 1; overflow: hidden;">
            <div id="videoTitle" style="font-size: 12px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">Fetching...</div>
            <div class="quality-toggle">
                <button class="q-btn active" onclick="setQ(this, 'HD')">HD</button>
                <button class="q-btn" onclick="setQ(this, 'SD')">SD</button>
                <button class="q-btn" onclick="setQ(this, 'MP3')">MP3</button>
            </div>
        </div>
    </div>

    <div class="input-group">
        <input type="url" id="tikUrl" placeholder="Paste link here..." oninput="handleInput()">
        <span class="paste-btn" onclick="doPaste()">PASTE</span>
    </div>

    <button class="dl-btn" id="dlBtn" onclick="startDownload()">
        <div class="progress-fill" id="pFill"></div>
        <div class="btn-content" id="btnTxt">
            Download <i class="fa-solid fa-arrow-right"></i>
        </div>
    </button>

    <div class="footer">TIKTOK • NO WATERMARK • FAST</div>
</div>

<script>
    let selectedQuality = 'HD';
    const input = document.getElementById('tikUrl');
    const preview = document.getElementById('previewCard');

    function notify(msg) {
        document.getElementById('notifMsg').innerText = msg;
        const n = document.getElementById('notification');
        n.classList.add('show');
        setTimeout(() => n.classList.remove('show'), 3000);
    }

    function setQ(el, q) {
        document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
        el.classList.add('active');
        selectedQuality = q;
    }

    async function handleInput() {
        const url = input.value.trim();
        if (url.includes('tiktok.com')) {
            preview.classList.add('active');
            fetchMeta(url);
        } else {
            preview.classList.remove('active');
        }
    }

    async function fetchMeta(url) {
        try {
            const res = await fetch("/meta", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({url})
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            document.getElementById('thumb').src = data.thumbnail;
            document.getElementById('videoTitle').innerText = data.title;
        } catch (e) {
            document.getElementById('videoTitle').innerText = "Video Found";
        }
    }

    async function doPaste() {
        try {
            const text = await navigator.clipboard.readText();
            input.value = text;
            handleInput();
        } catch(e) { notify("Clipboard access denied"); }
    }

    async function startDownload() {
        const url = input.value.trim();
        if (!url.includes('tiktok.com')) {
            notify("Only TikTok links are supported!");
            return;
        }

        const btn = document.getElementById('dlBtn');
        const btnTxt = document.getElementById('btnTxt');
        const fill = document.getElementById('pFill');

        btn.disabled = true;
        btnTxt.innerHTML = `Processing...`;
        fill.style.width = "40%";

        const formData = new FormData();
        formData.append("url", url);
        formData.append("quality", selectedQuality);

        try {
            const res = await fetch("/download", {method: "POST", body: formData});
            if (!res.ok) throw new Error("Download failed");

            fill.style.width = "100%";
            const blob = await res.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            
            const ext = selectedQuality === 'MP3' ? 'mp3' : 'mp4';
            a.download = `velocidown_${Date.now()}.${ext}`;
            a.click();

            btnTxt.innerHTML = `Success! <i class="fa-solid fa-check"></i>`;
        } catch (e) {
            notify("Download failed. Check your connection.");
            btnTxt.innerHTML = "Download";
        } finally {
            setTimeout(() => {
                btn.disabled = false;
                fill.style.width = "0%";
                btnTxt.innerHTML = `Download <i class="fa-solid fa-arrow-right"></i>`;
            }, 3000);
        }
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
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title": info.get("title", "TikTok Video"),
            "thumbnail": info.get("thumbnail", ""),
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
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    elif quality == "SD":
        ydl_opts = {"format": "worst[ext=mp4]/worst", "outtmpl": output_path + ".mp4"}
    else:
        ydl_opts = {"format": "best[ext=mp4]/best", "outtmpl": output_path + ".mp4"}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Adjust filename for MP3 post-processing
            if quality == "MP3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
