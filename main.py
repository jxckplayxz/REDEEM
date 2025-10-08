from flask import Flask, request, jsonify, render_template_string
import json, os

app = Flask(__name__)

ADMIN_PASSWORD = "Admin121"
DB_FILE = "users.json"
MESSAGE_FILE = "message.txt"

def read_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def read_message():
    return open(MESSAGE_FILE, "r").read() if os.path.exists(MESSAGE_FILE) else ""

def write_message(msg):
    with open(MESSAGE_FILE, "w") as f:
        f.write(msg)

@app.route("/click", methods=["POST"])
def click():
    data = request.get_json()
    username = data.get("username")

    users = read_db()
    if username not in users:
        users.append(username)
        write_db(users)

    return jsonify({"success": True, "message": read_message()})

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password != ADMIN_PASSWORD:
            return "Invalid password."

        action = request.form.get("action")
        if action == "delete_all":
            write_db([])
            return "✅ All users deleted."
        elif action == "update_message":
            msg = request.form.get("message")
            write_message(msg)
            return "✅ Message updated."
        else:
            return "❌ Unknown action."

    users = read_db()
    message = read_message()
    return render_template_string('''
        <h1>Admin Panel</h1>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password">
            <button type="submit" name="action" value="delete_all">Delete All Users</button><br><br>
            <textarea name="message" rows="3" cols="40" placeholder="Set message here...">{{ message }}</textarea><br>
            <button type="submit" name="action" value="update_message">Update Message</button>
        </form>
        <h2>Users Who Clicked:</h2>
        <ul>
        {% for u in users %}
            <li>{{ u }}</li>
        {% endfor %}
        </ul>
    ''', users=users, message=message)

@app.route("/")
def home():
    return "Server is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)