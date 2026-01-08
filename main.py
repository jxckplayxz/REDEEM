import os
import json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_FILE = "keys.json"
ADMIN_TOKEN = "12345"  # admin token changed

# -------------------------
# Load / Save Keys
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"keys": {}, "banned_users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# -------------------------
# Utils
# -------------------------
def generate_key(prefix="VZ_", length=12):
    import random, string
    return prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# -------------------------
# Dashboard
# -------------------------
@app.route("/")
def dashboard():
    return render_template_string("""
    <h1>Vertex Z Key Dashboard</h1>
    <p>Total Keys: {{ keys|length }}</p>

    <h3>Create Permanent Key</h3>
    <form action="/admin/create_perm" method="post">
        <input name="token" placeholder="Admin token">
        <button>Create</button>
    </form>

    <h3>Revoke Key</h3>
    <form action="/admin/revoke" method="post">
        <input name="token" placeholder="Admin token">
        <input name="key" placeholder="Key">
        <button>Revoke</button>
    </form>

    <h3>Keys</h3>
    <ul>
    {% for k,v in keys.items() %}
        <li>{{ k }} | user={{ v["username"] }} | perm={{ v["permanent"] }}</li>
    {% endfor %}
    </ul>
    """, keys=data["keys"])

# -------------------------
# Validate Key (ROBLOX)
# -------------------------
@app.route("/validate", methods=["POST"])
def validate():
    body = request.get_json()
    key = body.get("key")
    username = body.get("username")

    if username in data["banned_users"]:
        return jsonify(success=False, message="User banned")

    if key not in data["keys"]:
        return jsonify(success=False, message="Invalid key")

    info = data["keys"][key]

    if info["username"] is None:
        info["username"] = username
        save_data(data)
        return jsonify(success=True, message="Key locked to user")

    if info["username"] != username:
        return jsonify(success=False, message="Key used by another user")

    return jsonify(success=True, message="Key valid")

# -------------------------
# Admin: Create Perm Key
# -------------------------
@app.route("/admin/create_perm", methods=["POST"])
def create_perm():
    token = request.form.get("token") or request.json.get("token")
    if token != ADMIN_TOKEN:
        return "Unauthorized", 401

    key = generate_key()
    data["keys"][key] = {
        "username": None,
        "permanent": True
    }
    save_data(data)
    return jsonify(success=True, key=key)

# -------------------------
# Admin: Revoke Key
# -------------------------
@app.route("/admin/revoke", methods=["POST"])
def revoke():
    token = request.form.get("token") or request.json.get("token")
    key = request.form.get("key") or request.json.get("key")

    if token != ADMIN_TOKEN:
        return "Unauthorized", 401

    if key in data["keys"]:
        del data["keys"][key]
        save_data(data)
        return jsonify(success=True)

    return jsonify(success=False)

# -------------------------
# Run Flask (PORT 5050)
# -------------------------
def run_flask():
    port = 5050  # fixed port
    app.run(host="0.0.0.0", port=port)

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    run_flask()