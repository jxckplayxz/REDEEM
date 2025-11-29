from flask import Flask, request, jsonify, send_from_directory
import os, uuid, base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs("uploads", exist_ok=True)


# Allowed file types
ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED


# ------------------------------------------------------
#                MAIN HTML PAGE (INLINE)
# ------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Cloud Tools</title>
<style>
body {
    margin: 0;
    background: #f7f7f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    text-align: center;
}

.header {
    padding: 60px;
    font-size: 60px;
    font-weight: 700;
    animation: fadeIn 1.4s ease-out;
}

.sub {
    font-size: 22px;
    opacity: 0.7;
}

.card {
    background: white;
    width: 85%;
    max-width: 550px;
    margin: 35px auto;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    animation: slideUp 1s ease-out;
}

button {
    padding: 14px 26px;
    font-size: 17px;
    border-radius: 14px;
    border: none;
    cursor: pointer;
    background: black;
    color: white;
    transition: 0.2s;
}
button:hover {
    transform: scale(1.05);
    background:#333;
}

input[type=file] {
    margin: 14px;
}

#dropZone {
    padding: 40px;
    border: 3px dashed #bbb;
    margin: 20px;
    border-radius: 20px;
    transition: 0.3s;
}
#dropZone:hover {
    border-color: black;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(40px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(60px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
</head>

<body>

<div class='header'>Cloud Tools</div>
<div class='sub'>Upload • Remove BG • Compress • Share Anywhere</div>

<!-- Upload Card -->
<div class='card'>
    <h2>Upload Image</h2>
    <div id="dropZone">Drag & Drop File Here</div>
    <input type="file" id="uploadFile">
    <button onclick="upload()">Upload</button>
    <p id="uploadResult"></p>
</div>

<!-- Remove BG -->
<div class='card'>
    <h2>Remove Background</h2>
    <input type="file" id="bgFile">
    <button onclick="removeBG()">Remove</button>
    <p id="bgResult"></p>
</div>

<!-- Base64 tool -->
<div class='card'>
    <h2>Convert Image to Base64</h2>
    <input type="file" id="b64File">
    <button onclick="toBase64()">Convert</button>
    <p id="b64Output"></p>
</div>

<!-- Compression -->
<div class='card'>
    <h2>Compress Image</h2>
    <input type="file" id="compressFile">
    <button onclick="compress()">Compress</button>
    <p id="compressResult"></p>
</div>

<script>
// -------------------- UPLOAD --------------------
function upload() {
    let file = document.getElementById("uploadFile").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/upload", { method:"POST", body:form })
    .then(res => res.json())
    .then(data => {
        document.getElementById("uploadResult").innerHTML =
        "Embed Link:<br><a href='" + data.url + "' target='_blank'>" + data.url + "</a>";
    });
}

// Drag & Drop
let zone = document.getElementById("dropZone");

zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.style.borderColor = "black";
});
zone.addEventListener("dragleave", () => zone.style.borderColor="#bbb");

zone.addEventListener("drop", e => {
    e.preventDefault();
    let file = e.dataTransfer.files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/upload", {method:"POST", body:form})
    .then(r => r.json())
    .then(d => {
        document.getElementById("uploadResult").innerHTML =
            "Embed Link:<br><a href='" + d.url + "' target='_blank'>" + d.url + "</a>";
    });
});

// -------------------- REMOVE BG --------------------
function removeBG() {
    let file = document.getElementById("bgFile").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/remove_bg", {method:"POST", body:form})
    .then(r => r.json())
    .then(d => {
        document.getElementById("bgResult").innerHTML =
            "Result:<br><a href='" + d.url + "' target='_blank'>" + d.url + "</a>";
    });
}

// -------------------- Base64 --------------------
function toBase64() {
    let file = document.getElementById("b64File").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/base64", {method:"POST", body:form})
    .then(r => r.json())
    .then(d => {
        document.getElementById("b64Output").innerHTML =
        "<textarea style='width:90%;height:120px'>" + d.base64 + "</textarea>";
    });
}

// -------------------- Compression --------------------
function compress() {
    let file = document.getElementById("compressFile").files[0];
    let form = new FormData();
    form.append("file", file);

    fetch("/compress", {method:"POST", body:form})
    .then(r => r.json())
    .then(d => {
        document.getElementById("compressResult").innerHTML =
            "Compressed Image:<br><a href='" + d.url + "' target='_blank'>" + d.url + "</a>";
    });
}
</script>

</body>
</html>
"""

# ------------------------------------------------------
#                    ROUTES
# ------------------------------------------------------

@app.route("/")
def index():
    return HTML_PAGE


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f or not allowed_file(f.filename):
        return jsonify({"error": "invalid file"}), 400

    ext = f.filename.rsplit(".",1)[1].lower()
    name = f"{uuid.uuid4()}.{ext}"

    f.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
    return jsonify({"url": f"/i/{name}"})


@app.route("/i/<filename>")
def serve_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/remove_bg", methods=["POST"])
def remove_bg():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "missing"}), 400

    ext = f.filename.rsplit(".",1)[1].lower()
    name = f"bg_removed_{uuid.uuid4()}.{ext}"

    # Placeholder logic
    # Replace later with real AI background removal
    f.save(os.path.join("uploads", name))

    return jsonify({"url": f"/i/{name}"})


@app.route("/base64", methods=["POST"])
def base64_convert():
    f = request.files.get("file")
    data = base64.b64encode(f.read()).decode("utf-8")
    return jsonify({"base64": data})


@app.route("/compress", methods=["POST"])
def compress():
    # Fake compression: just re-save file
    f = request.files.get("file")
    ext = f.filename.rsplit(".",1)[1].lower()
    name = f"compressed_{uuid.uuid4()}.{ext}"
    f.save(os.path.join("uploads", name))
    return jsonify({"url": f"/i/{name}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)