import threading
import random
import string
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

# -----------------------
# Key system storage
# -----------------------
keys = {}  # format: key: {"perm": bool, "used_by": None or username}
used_keys = {}  # key: username

# -----------------------
# Helper functions
# -----------------------
def generate_key(perm=False):
    """Generates a VZ_ key"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    key = f"VZ_{random_part}"
    keys[key] = {"perm": perm, "used_by": None}
    return key

def validate_key(input_key, username):
    """Check if key is valid and lock to username"""
    if input_key not in keys:
        return False
    if keys[input_key]["used_by"] is not None and keys[input_key]["used_by"] != username:
        return False
    keys[input_key]["used_by"] = username
    return True

def revoke_key(key):
    if key in keys:
        del keys[key]

# -----------------------
# Routes
# -----------------------

# Home page
@app.route("/")
def home():
    return render_template_string("""
        <html>
            <head><title>Vertex-Z Key System</title></head>
            <body style="font-family:sans-serif;">
                <h1>Welcome to Vertex-Z Key System</h1>
                <p>Use <code>/validate?key=YOUR_KEY&user=USERNAME</code> to validate your key in Roblox.</p>
                <p>Admin? Visit <a href="/admin?token=1234t">Admin Panel</a></p>
            </body>
        </html>
    """)

# Key validation route (Roblox)
@app.route("/validate")
def validate():
    key = request.args.get("key")
    username = request.args.get("user")
    if not key or not username:
        return "Missing key or username", 400

    if validate_key(key, username):
        return f"Key valid! Locked to {username}."
    else:
        return "Invalid or already used key!", 403

# Admin panel
@app.route("/admin")
def admin():
    token = request.args.get("token")
    if token != "1234t":
        return "Unauthorized", 401

    # Admin dashboard page
    html = """
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {font-family:sans-serif; background:#1a1a1a; color:#fff; padding:20px;}
            button {padding:10px 20px; margin:5px; cursor:pointer;}
            table {border-collapse: collapse; margin-top: 20px;}
            th, td {border:1px solid #fff; padding:5px 10px;}
        </style>
    </head>
    <body>
        <h1>Admin Panel</h1>
        <form method="POST" action="/admin/generate">
            <button type="submit">Generate PERM Key</button>
        </form>

        <h2>All Keys</h2>
        <table>
            <tr><th>Key</th><th>Permanent</th><th>Used By</th><th>Revoke</th></tr>
            {% for k,v in keys.items() %}
            <tr>
                <td>{{k}}</td>
                <td>{{v.perm}}</td>
                <td>{{v.used_by}}</td>
                <td><a href="/admin/revoke?token=1234t&key={{k}}">Revoke</a></td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, keys=keys)

# Generate perm key
@app.route("/admin/generate", methods=["POST"])
def admin_generate():
    token = request.args.get("token")
    if token != "1234t":
        return "Unauthorized", 401

    new_key = generate_key(perm=True)
    return redirect("/admin?token=1234t")

# Revoke key
@app.route("/admin/revoke")
def admin_revoke():
    token = request.args.get("token")
    if token != "1234t":
        return "Unauthorized", 401

    key = request.args.get("key")
    if key:
        revoke_key(key)
    return redirect("/admin?token=1234t")

# -----------------------
# Run Flask
# -----------------------
def run_flask():
    app.run(host="0.0.0.0", port=5050)

# -----------------------
# Main execution
# -----------------------
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()