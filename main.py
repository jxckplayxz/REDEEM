from flask import Flask, request, redirect, render_template_string
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simulated in-memory data
REDEEMED_USERS = []
MAX_REDEMPTIONS = 2
ADMIN_PASSWORD = "vzadmin2025"  # Secret key for accessing /admin

# HTML templates
REDEEM_TEMPLATE = ''' ... '''  # (same as before – omitted here for brevity)

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
        th {
            background-color: #222;
        }
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

@app.route('/redeem', methods=['GET', 'POST'])
def redeem():
    ip = request.remote_addr
    referer = request.headers.get("Referer", "")

    if len(REDEEMED_USERS) >= MAX_REDEMPTIONS:
        return render_template_string(REDEEM_TEMPLATE, message="Oops! All codes have been redeemed. You can still support us by completing our LootLabs offer!", show_form=False)

    if request.method == 'POST':
        if any(entry["ip"] == ip for entry in REDEEMED_USERS):
            return render_template_string(REDEEM_TEMPLATE, message="You already redeemed a code!", show_form=False)

        username = request.form.get("username", "").strip()
        code = request.form.get("code", "").strip()

        if not username or not code:
            return render_template_string(REDEEM_TEMPLATE, message="Please enter both your username and code.", show_form=True)

        REDEEMED_USERS.append({
            "username": username,
            "ip": ip,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return render_template_string(REDEEM_TEMPLATE, message=f"Thank you, {username}! Your code has been redeemed!", show_form=False)

    if "loot-link.com" in referer or "lootlabs" in referer:
        return render_template_string(REDEEM_TEMPLATE, show_form=True, message=None)

    return render_template_string(REDEEM_TEMPLATE, show_form=False, message=None)

@app.route('/admin')
def admin_panel():
    # Use query string password like /admin?key=YOURPASS
    key = request.args.get("key")
    if key != ADMIN_PASSWORD:
        return "Unauthorized", 403

    return render_template_string(ADMIN_TEMPLATE, redemptions=REDEEMED_USERS)

if __name__ == '__main__':
    app.run(debug=True)
