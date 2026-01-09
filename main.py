from flask import Flask, request, jsonify, render_template_string, redirect
import threading
import random
import string
import time

app = Flask(__name__)

# -----------------------------
# Key system database (in-memory)
# -----------------------------
keys_db = []  # stores dicts: {key, user, perm, used}

# -----------------------------
# Helper functions
# -----------------------------
def generate_key(length=8, perm=False):
    """Generate a key starting with VZ_"""
    k = "VZ_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    keys_db.append({"key": k, "user": None, "perm": perm, "used": False})
    return k

def find_key(k):
    for key in keys_db:
        if key["key"] == k:
            return key
    return None

# -----------------------------
# Admin dashboard HTML
# -----------------------------
DASHBOARD_HTML = """
<!doctype html>
<title>Vertex-Z Admin</title>
<h1>Vertex-Z Key Dashboard</h1>
<h2>Generate Keys</h2>
<button onclick="fetch('/generate_key').then(r => r.json()).then(d => alert('Key: '+d.key))">Generate Key</button>
<button onclick="fetch('/generate_perm_key_admin').then(r => r.json()).then(d => alert('Perm Key: '+d.key))">Generate Perm Key</button>

<h2>Current Keys</h2>
<ul>
{% for k in keys %}
    <li>{{k.key}} | Perm: {{k.perm}} | Used: {{k.used}} | Locked to: {{k.user}}
        {% if not k.perm %}<button onclick="fetch('/revoke_key?key={{k.key}}').then(()=>location.reload())">Revoke</button>{% endif %}
    </li>
{% endfor %}
</ul>
"""

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return redirect("/admin")

@app.route("/admin")
def admin():
    return render_template_string(DASHBOARD_HTML, keys=keys_db)

# Generate a normal key (anyone hitting this directly is fine)
@app.route("/generate_key")
def generate_normal_key():
    k = generate_key(perm=False)
    return jsonify({"key": k})

# Generate perm key from admin panel (no token needed from button)
@app.route("/generate_perm_key_admin")
def generate_perm_key_admin():
    k = generate_key(perm=True)
    return jsonify({"key": k})

# Revoke a key
@app.route("/revoke_key")
def revoke_key():
    k = request.args.get("key")
    key_obj = find_key(k)
    if key_obj:
        keys_db.remove(key_obj)
    return jsonify({"status": "ok"})

# LootLabs & Roblox validation
@app.route("/validate")
def validate():
    username = request.args.get("username")
    key = request.args.get("key")
    key_obj = find_key(key)
    if not key_obj:
        return jsonify({"status": "invalid"}), 401
    if key_obj["used"] and not key_obj["perm"]:
        return jsonify({"status": "used"}), 403
    # lock key to user if not already
    if not key_obj["user"]:
        key_obj["user"] = username
    # mark used if not perm
    if not key_obj["perm"]:
        key_obj["used"] = True
    return jsonify({"status": "ok", "key": key, "user": username})

# -----------------------------
# Start Flask in a thread
# -----------------------------
def run_flask():
    app.run(host="0.0.0.0", port=5050)

# -----------------------------
# Main execution
# -----------------------------
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    # Roblox bot or executor logic would run here
    print("Flask running on port 5050. Dashboard: /admin")