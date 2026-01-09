from flask import Flask, request, render_template_string
import random, string

app = Flask(__name__)

ADMIN_TOKEN = "1234t"

# key -> {"perm": bool}
KEYS = {}

# ======================
# KEY GENERATION
# ======================
def generate_key(perm=False):
    key = "VZ_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    KEYS[key] = {"perm": perm}
    return key

# ======================
# VALIDATE (ROBLOX)
# ======================
@app.route("/validate")
def validate():
    key = request.args.get("key")
    if key in KEYS:
        return "VALID"
    return "INVALID"

# ======================
# LOOTLABS GENERATE
# ======================
@app.route("/generate")
def generate():
    if request.args.get("from") != "lootlabs":
        return "Invalid source"

    key = generate_key(perm=False)
    return render_template_string(GENERATE_HTML, key=key)

# ======================
# ADMIN DASHBOARD
# ======================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    token = request.args.get("token")
    if token != ADMIN_TOKEN:
        return "Unauthorized"

    new_key = None
    if request.method == "POST":
        new_key = generate_key(perm=True)

    return render_template_string(ADMIN_HTML, key=new_key, keys=KEYS)

# ======================
# HOME
# ======================
@app.route("/")
def home():
    return "Vertex Z Key Server Online"

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)

# ======================
# HTML BELOW (EMBEDDED)
# ======================

GENERATE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Your Key</title>
<style>
body {
    background:#0e0e0e;
    color:white;
    font-family:Arial;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}
.box {
    background:#151515;
    padding:30px;
    border-radius:14px;
    text-align:center;
    animation:pop .5s ease;
    box-shadow:0 0 25px rgba(76,175,80,.2);
}
@keyframes pop {
    from {transform:scale(.8); opacity:0}
    to {transform:scale(1); opacity:1}
}
.key {
    font-size:24px;
    margin-top:15px;
    color:#4caf50;
    font-weight:bold;
}
</style>
</head>
<body>
<div class="box">
<h2>Your Key</h2>
<div class="key">{{ key }}</div>
<p>Paste this into the Roblox script</p>
</div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Admin Panel</title>
<style>
body {
    background:#0e0e0e;
    color:white;
    font-family:Arial;
}
.container {
    width:650px;
    margin:40px auto;
    background:#151515;
    padding:25px;
    border-radius:14px;
}
button {
    background:#4caf50;
    border:none;
    padding:10px 15px;
    font-weight:bold;
    border-radius:8px;
    cursor:pointer;
}
.key {
    color:#4caf50;
    margin:5px 0;
}
</style>
</head>
<body>
<div class="container">
<h2>Admin Dashboard</h2>

<form method="POST">
<button type="submit">Generate Permanent Key</button>
</form>

{% if key %}
<p>New PERM key:</p>
<div class="key">{{ key }}</div>
{% endif %}

<h3>All Keys</h3>
{% for k,v in keys.items() %}
<div class="key">{{ k }} {% if v.perm %}(PERM){% endif %}</div>
{% endfor %}

</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)