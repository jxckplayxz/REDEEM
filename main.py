from flask import Flask, request, jsonify, render_template_string, redirect
import random, string, json, os, time

app = Flask(__name__)

KEY_FILE = "keys.json"
STATS_FILE = "stats.json"
ADMIN_PASSWORD = "vzadmin212"
DAY = 86400

ALLOWED_REFERRERS = [
    "lootlabs.gg",
    "lootdest.org",
    "lootlink.com"
]

RICKROLL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Initialize files if missing
def init_file(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)

init_file(KEY_FILE, {})
init_file(STATS_FILE, {"getkey": 0, "verifications": 0, "perm_generated": 0})

def load(path):
    with open(path, "r") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def gen_key(prefix):
    return prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))

def valid_referrer(ref):
    if not ref:
        return False
    return any(x in ref for x in ALLOWED_REFERRERS)

# ---------- HTML TEMPLATES ----------

KEY_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Vertex Z Key</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {
    margin:0; padding:0;
    background: linear-gradient(135deg, #0f0f0f, #1a1a1a);
    color:white; font-family: 'Segoe UI', Arial, sans-serif;
    display:flex; align-items:center; justify-content:center; height:100vh;
}
.box {
    background:#1e1e1e;
    padding:25px 20px;
    border-radius:18px;
    text-align:center;
    width:90%;
    max-width:420px;
    box-shadow:0 8px 25px rgba(0,0,0,0.6);
    border: 1px solid #333;
}
.key {
    background:#000;
    padding:14px;
    margin-top:15px;
    font-size:20px;
    user-select:all;
    border-radius:10px;
    border:1px solid #444;
}
h2 {
    margin:0; font-size:26px; color:#ffd700;
}
p {
    margin-top:10px; font-size:15px; color:#bbb;
}
button {
    margin-top:15px; padding:10px 0; width:100%;
    background:#444; color:white; font-size:16px;
    border:none; border-radius:10px; cursor:pointer;
    transition: all 0.2s;
}
button:hover {
    background:#666;
}
</style>
</head>
<body>
<div class="box">
<h2>Vertex Z Key 🔑</h2>
<p>Here is your key! Save it somewhere safe.</p>
<div class="key">{{ key }}</div>
<p>Expires in 24 hours</p>
<a href="https://lootlabs.gg" target="_blank"><button>Go Back to LootLabs</button></a>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Vertex Z Admin</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;padding:20px;background:#0e0e0e;color:white;font-family:Arial, sans-serif}
.box{background:#1c1c1c;padding:15px;border-radius:12px;margin-bottom:20px}
h2,h3{margin:0 0 10px 0}
input,button,select{width:100%;padding:10px;margin:6px 0;border:none;border-radius:8px;font-size:16px}
button{background:#333;color:white;cursor:pointer}
.stat{margin:6px 0}
.key-list{max-height:200px;overflow-y:auto;margin-top:10px}
.key-item{display:flex;justify-content:space-between;padding:6px;border-bottom:1px solid #333;align-items:center}
.key-item span{word-break:break-all;font-size:14px}
.key-item button{width:auto;padding:6px 10px;font-size:12px;background:#b33;color:white;border-radius:6px;cursor:pointer}
</style>
</head>
<body>
<div class="box">
<h2>Vertex Z Admin Dashboard</h2>
<div class="stat">🔑 Daily keys generated: {{ stats.getkey }}</div>
<div class="stat">✅ Verifications: {{ stats.verifications }}</div>
<div class="stat">♾️ Permanent keys created: {{ stats.perm_generated }}</div>
<form method="POST">
<button name="gen" value="1">Generate Permanent Key</button>
</form>
{% if perm %}
<p>New Permanent Key:</p>
<b>{{ perm }}</b>
{% endif %}
</div>

<div class="box">
<h3>All Keys (Click Revoke to invalidate)</h3>
<div class="key-list">
{% for k, v in keys.items() %}
<div class="key-item">
<span>{{ k }} ({{ v.type }})</span>
<form method="POST" style="margin:0">
<input type="hidden" name="revoke" value="{{ k }}">
<button>Revoke</button>
</form>
</div>
{% endfor %}
</div>
</div>
</body>
</html>
"""

# ---------- ROUTES ----------

@app.route("/getkey")
def getkey():
    ref = request.referrer
    if not valid_referrer(ref):
        return redirect(RICKROLL)

    keys = load(KEY_FILE)
    stats = load(STATS_FILE)

    key = gen_key("DAY")
    keys[key] = {"type": "daily", "created": int(time.time())}
    stats["getkey"] += 1

    save(KEY_FILE, keys)
    save(STATS_FILE, stats)

    return render_template_string(KEY_HTML, key=key)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    key = data.get("key")
    keys = load(KEY_FILE)
    stats = load(STATS_FILE)

    stats["verifications"] += 1

    if key not in keys:
        save(STATS_FILE, stats)
        return jsonify({"valid": False})

    info = keys[key]
    if info["type"] == "daily" and time.time() - info["created"] > DAY:
        del keys[key]
        save(KEY_FILE, keys)
        save(STATS_FILE, stats)
        return jsonify({"valid": False})

    save(STATS_FILE, stats)
    return jsonify({"valid": True})

@app.route("/admin", methods=["GET","POST"])
def admin():
    pw = request.args.get("pw") or request.form.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Unauthorized", 401

    stats = load(STATS_FILE)
    keys = load(KEY_FILE)
    perm = None

    # Generate permanent key
    if request.method=="POST" and request.form.get("gen"):
        perm = gen_key("PERM")
        keys[perm] = {"type": "permanent", "created": int(time.time())}
        stats["perm_generated"] += 1

    # Revoke key
    if request.method=="POST" and request.form.get("revoke"):
        k = request.form.get("revoke")
        if k in keys:
            del keys[k]

    save(KEY_FILE, keys)
    save(STATS_FILE, stats)

    return render_template_string(DASHBOARD_HTML, stats=stats, perm=perm, keys=keys)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)