from flask import Flask, request, redirect, render_template_string, session
import sqlite3, random, string, time

app = Flask(__name__)
app.secret_key = "super_secret"  # change this

DB_FILE = "whitelist.db"

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist (
                    username TEXT,
                    key TEXT,
                    expiry INTEGER
                )''')
    conn.commit()
    conn.close()

init_db()

def generate_key(username):
    rand_nums = ''.join(random.choices(string.digits, k=5))
    return f"{username}_{rand_nums}"

@app.route("/getkey/<username>")
def getkey(username):
    key = generate_key(username)
    expiry = int(time.time()) + (35 * 3600)  # 35 hours
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO whitelist VALUES (?, ?, ?)", (username, key, expiry))
    conn.commit()
    conn.close()
    # redirect user to lootlink with their key encoded
    return redirect(f"https://loot-link.com/task?return_url=http://yourdomain.com/whitelist/{key}")

@app.route("/whitelist/<key>")
def whitelist(key):
    # validate referer (anti-bypass)
    referer = request.headers.get("Referer", "")
    if "loot-link.com" not in referer and "lootlabs.net" not in referer:
        return "⚠️ Please complete our key system first!"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, expiry FROM whitelist WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "❌ Invalid key!"
    username, expiry = row
    if int(time.time()) > expiry:
        return "⏰ Key expired! Please get a new one."

    # HTML squircle UI
    html = f"""
    <html>
    <head>
      <style>
        body {{
          background: #111;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          font-family: Arial, sans-serif;
        }}
        .squircle {{
          background: #222;
          padding: 40px;
          border-radius: 30% / 20%;
          text-align: center;
          color: white;
          box-shadow: 0 0 20px rgba(0,255,255,0.5);
        }}
        button {{
          background: cyan;
          border: none;
          padding: 10px 20px;
          border-radius: 10px;
          font-size: 16px;
          cursor: pointer;
        }}
      </style>
    </head>
    <body>
      <div class="squircle">
        <h2>Your Key</h2>
        <p><b>{key}</b></p>
        <form method="POST" action="/validate/{key}">
            <button type="submit">Whitelist Me</button>
        </form>
        <p>✅ Your key will expire in 35 hours.</p>
      </div>
    </body>
    </html>
    """
    return html

@app.route("/validate/<key>", methods=["POST"])
def validate(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, expiry FROM whitelist WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "❌ Invalid key!"
    username, expiry = row
    if int(time.time()) > expiry:
        return "⏰ Key expired!"

    return f"✅ {username} has been whitelisted successfully!"
