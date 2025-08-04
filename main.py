from flask import Flask, request, redirect, render_template_string, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

REDEEMED_USERS = []
MAX_REDEMPTIONS = 2
ADMIN_PASSWORD = "vzadmin2025"

# ------------------- HTML Templates -------------------

REDEEM_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Redeem Page - Vertex Z</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background: #0f0f0f;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: #1a1a1a;
            padding: 30px 40px;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.8);
            max-width: 400px;
            width: 90%;
            text-align: center;
        }
        h1 { margin-bottom: 20px; font-size: 26px; }
        input[type="text"] {
            padding: 12px;
            width: 90%;
            border: none;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 16px;
            background-color: #2a2a2a;
            color: white;
        }
        button {
            padding: 12px 25px;
            background-color: #4a90e2;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            color: white;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        button:hover { background-color: #357acb; }
        .alt {
            margin-top: 20px;
            font-size: 14px;
            color: #ccc;
        }
        .alt a {
            color: #4a90e2;
            text-decoration: none;
        }
        .alt a:hover { text-decoration: underline; }
        .message {
            margin-top: 20px;
            color: #ff5555;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Redeem Your Reward</h1>
        {% if show_form %}
        <form method="POST">
            <input type="text" name="username" placeholder="Enter Roblox Username" required><br>
            <input type="text" name="code" placeholder="Enter Redeem Code" required><br>
            <button type="submit">Redeem</button>
        </form>
        {% else %}
        <p>Don’t have a code?</p>
        <a href="https://loot-link.com/s?jPAaJ4C1">
            <button>Get Code</button>
        </a>
        {% endif %}
        {% if message %}
        <div class="message">{{ message }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: white;
            font-family: monospace;
            padding: 30px;
        }
        h1 { margin-bottom: 20px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            border: 1px solid #444;
            padding: 10px;
            text-align: left;
        }
        th { background-color: #222; }
        tr:nth-child(even) {
            background-color: #1a1a1a;
        }
    </style>
</head>
<body>
    <h1>Redeemed Codes - Admin Panel</h1>
    {% if redemptions %}
        <table>
            <tr>
                <th>Username</th>
                <th>IP Address</th>
                <th>Time</th>
            </tr>
            {% for item in redemptions %}
                <tr>
                    <td>{{ item.username }}</td>
                    <td>{{ item.ip }}</td>
                    <td>{{ item.time }}</td>
                </tr>
            {% endfor %}
        </table>
    {% else %}
        <p>No redemptions yet.</p>
    {% endif %}
</body>
</html>
'''

# ------------------- Redeem Route -------------------

@app.route('/redeem', methods=['GET', 'POST'])
def redeem():
    ip = request.remote_addr
    from_param = request.args.get("from", "")

    # Step 1: If redirected from Lootlink, set session flag
    if from_param == "lootlink":
        session["lootlink_verified"] = True

    # Step 2: Check for max redemptions
    if len(REDEEMED_USERS) >= MAX_REDEMPTIONS:
        return render_template_string(REDEEM_TEMPLATE, show_form=False, message="Oops! All codes have been redeemed. You can still support us by completing our LootLabs offer!")

    # Step 3: Handle form submit
    if request.method == 'POST':
        if not session.get("lootlink_verified"):
            return render_template_string(REDEEM_TEMPLATE, show_form=False, message="Oops! You must complete the LootLabs link first.")

        if any(entry["ip"] == ip for entry in REDEEMED_USERS):
            return render_template_string(REDEEM_TEMPLATE, show_form=False, message="You already redeemed a code!")

        username = request.form.get("username", "").strip()
        code = request.form.get("code", "").strip()

        if not username or not code:
            return render_template_string(REDEEM_TEMPLATE, show_form=True, message="Please fill in all fields.")

        # Add to list
        REDEEMED_USERS.append({
            "username": username,
            "ip": ip,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Clear session flag
        session["lootlink_verified"] = False
        return render_template_string(REDEEM_TEMPLATE, show_form=False, message=f"Thanks, {username}! Your code has been redeemed.")

    # Step 4: If GET, show form only if session is verified
    if session.get("lootlink_verified"):
        return render_template_string(REDEEM_TEMPLATE, show_form=True, message=None)

    return render_template_string(REDEEM_TEMPLATE, show_form=False, message=None)

# ------------------- Admin Panel -------------------

@app.route('/admin')
def admin_panel():
    key = request.args.get("key")
    if key != ADMIN_PASSWORD:
        return "Unauthorized", 403
    return render_template_string(ADMIN_TEMPLATE, redemptions=REDEEMED_USERS)

# ------------------- Run App -------------------

if __name__ == '__main__':
    app.run(debug=True)
