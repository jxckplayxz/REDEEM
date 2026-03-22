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
            "id": os.urandom(4).hex(),
            "title": request.form.get('title'),
            "url": request.form.get('url'),
            "thumb": request.form.get('thumb') or "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&q=80&w=1000"
        }
        section = next((s for s in data['sections'] if s['name'] == section_name), None)
        if section:
            section['matches'].append(match_data)
        else:
            data['sections'].append({"name": section_name, "matches": [match_data]})
        save_data(data)
        return redirect(url_for('admin'))
    return render_template('admin.html', sections=data['sections'])

@app.route('/delete/<match_id>')
def delete_match(match_id):
    data = load_data()
    for section in data['sections']:
        section['matches'] = [m for m in section['matches'] if m['id'] != match_id]
    data['sections'] = [s for s in data['sections'] if s['matches']]
    save_data(data)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
r(e)})

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
