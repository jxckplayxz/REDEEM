from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import os, json

app = Flask(__name__)
CORS(app)

app.secret_key = "super_secret_key_123"
DB_FILE = "clicks.json"
ADMIN_PASS = "Admin121"

# Admin panel HTML
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body {
            background: #0e0e0e;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
        }
        .box {
            background: #1b1b1b;
            border-radius: 10px;
            display: inline-block;
            padding: 20px;
            margin-top: 50px;
            box-shadow: 0 0 10px #0ff;
        }
        input, button, textarea {
            padding: 8px;
            margin: 5px;
            border: none;
            border-radius: 5px;
        }
        button {
            background-color: #0ff;
            color: black;
            cursor: pointer;
        }
        button:hover {
            background-color: #08f;
            color: white;
        }
        textarea {
            width: 80%;
            height: 80px;
        }
        a {
            color: #0ff;
            text-decoration: none;
        }
    </style>
</head>
<body>
    {% if not session.get('logged_in') %}
        <div class="box">
            <h2>Admin Login</h2>
            <form method="POST" action="/login">
                <input type="password" name="password" placeholder="Enter Admin Password" required><br>
                <button type="submit">Login</button>
            </form>
        </div>
    {% else %}
        <div class="box">
            <h2>Users Who Clicked</h2>
            <ul>
                {% for user in users %}
                    <li>{{ user }} <a href="/delete/{{ user }}">[Delete]</a></li>
                {% endfor %}
            </ul>
            <form action="/delete_all" method="POST">
                <button type="submit" style="background:red;color:white;">Delete All Users</button>
            </form>
            <h2>Set Announcement</h2>
            <form method="POST" action="/set_message">
                <textarea name="message" placeholder="Enter your message here...">{{ message }}</textarea><br>
                <button type="submit">Update Message</button>
            </form>
            <br>
            <a href="/logout"><button>Logout</button></a>
        </div>
    {% endif %}
</body>
</html>
"""

# Utility functions
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"users": [], "message": ""}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.after_request
def add_headers(response):
    response.headers["Content-Type"] = "application/json"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# Routes
@app.route('/')
def index():
    return jsonify({"status": "running"})

@app.route('/click', methods=['POST'])
def click():
    data = request.get_json()
    username = data.get("username")
    db = load_db()
    if username and username not in db["users"]:
        db["users"].append(username)
        save_db(db)
    return jsonify({"success": True})

@app.route('/check')
def check():
    username = request.args.get("username")
    db = load_db()
    clicked = username in db["users"]
    return jsonify({"clicked": clicked, "message": db.get("message", "")})

@app.route('/admin')
def admin():
    db = load_db()
    return render_template_string(ADMIN_HTML, users=db["users"], message=db["message"])

@app.route('/login', methods=['POST'])
def login():
    if request.form.get("password") == ADMIN_PASS:
        session["logged_in"] = True
        return redirect(url_for("admin"))
    return "Wrong password."

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("admin"))

@app.route('/delete/<username>')
def delete_user(username):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))
    db = load_db()
    if username in db["users"]:
        db["users"].remove(username)
        save_db(db)
    return redirect(url_for("admin"))

@app.route('/delete_all', methods=['POST'])
def delete_all():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))
    db = load_db()
    db["users"] = []
    save_db(db)
    return redirect(url_for("admin"))

@app.route('/set_message', methods=['POST'])
def set_message():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))
    msg = request.form.get("message", "")
    db = load_db()
    db["message"] = msg
    save_db(db)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))