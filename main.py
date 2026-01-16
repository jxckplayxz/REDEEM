# app.py (HTML EMBEDDED)
from flask import Flask, request, jsonify, render_template_string
import random, string, json, os

app = Flask(__name__)
KEY_FILE = "keys.json"

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "w") as f:
        json.dump({}, f)

def load_keys():
    with open(KEY_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f)

def gen_key():
    return "VZ-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Your Key</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;display:flex;align-items:center;justify-content:center;height:100vh}
.box{background:#1b1b1b;padding:25px;border-radius:10px;text-align:center}
.key{background:#000;padding:12px;margin-top:10px;font-size:18px;user-select:all}
</style>
</head>
<body>
<div class="box">
<h2>Your Key</h2>
<div class="key">{{ key }}</div>
<p>Paste this into the executor</p>
</div>
</body>
</html>
"""

@app.route("/getkey")
def getkey():
    keys = load_keys()
    key = gen_key()
    keys[key] = True
    save_keys(keys)
    return render_template_string(HTML, key=key)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("key")
    keys = load_keys()
    return jsonify({"valid": key in keys})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)