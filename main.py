from flask import Flask, request, redirect, render_template_string, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simulated DB
REDEEMED_CODES = []  # will store IP addresses or session IDs of redeemed users
MAX_CODES = 2

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <title>Redeem</title>
</head>
<body style="background-color:#111;color:white;font-family:sans-serif;text-align:center;padding-top:50px;">
  {% if message %}
    <h2>{{ message }}</h2>
    <a href="/redeem">Go Back</a>
  {% elif show_code_input %}
    <h1>Enter Your Code</h1>
    <form method="POST" action="/redeem">
      <input type="text" name="code" placeholder="Enter Code" required>
      <br><br>
      <button type="submit">Submit</button>
    </form>
  {% else %}
    <h2>Please enter a code to redeem</h2>
    <a href="https://loot-link.com/s?jPAaJ4C1">Get Code</a>
  {% endif %}
</body>
</html>
'''

@app.route('/redeem', methods=['GET', 'POST'])
def redeem():
    referer = request.headers.get("Referer", "")
    ip = request.remote_addr

    # Check if max redemptions reached
    if len(REDEEMED_CODES) >= MAX_CODES:
        return render_template_string(HTML_TEMPLATE, message="Oops! All codes have already been redeemed. You can still support us by completing our LootLabs offer.", show_code_input=False)

    # If POST (user submitting code)
    if request.method == 'POST':
        if ip in REDEEMED_CODES:
            return render_template_string(HTML_TEMPLATE, message="You have already redeemed a code.", show_code_input=False)

        # Here, you could verify the code if you had a real code system
        REDEEMED_CODES.append(ip)
        return render_template_string(HTML_TEMPLATE, message="Code redeemed successfully! Thank you!", show_code_input=False)

    # If GET (user visiting the page)
    if "loot-link.com" in referer or "lootlabs" in referer:
        return render_template_string(HTML_TEMPLATE, show_code_input=True, message=None)

    return render_template_string(HTML_TEMPLATE, show_code_input=False, message=None)

if __name__ == '__main__':
    app.run(debug=True)
