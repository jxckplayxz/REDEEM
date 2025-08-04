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
    <title>Thank You!</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #1f1c2c, #928DAB);
            font-family: 'Segoe UI', sans-serif;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        .thank-you-box {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            max-width: 400px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        p {
            font-size: 1.1rem;
            margin-bottom: 30px;
        }
        a.button {
            display: inline-block;
            padding: 10px 25px;
            background-color: #00c896;
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: 0.3s ease;
        }
        a.button:hover {
            background-color: #00a87a;
        }
    </style>
</head>
<body>
    <div class="thank-you-box">
        <h1>Thank You!</h1>
        <p>Your submission has been completed successfully.</p>
        <a href="/" class="button">Go Back Home</a>
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

@app.route('/', methods=['GET', 'POST'])
def nun():
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
