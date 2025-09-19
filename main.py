from flask import Flask, request, render_template_string, jsonify
import os, json, random, time

app = Flask(__name__)

DB_FILE = "keys.json"
ALLOWED_SOURCES = ["lootdest.org", "loot-link.com", "lootlabs.net"]
DEFAULT_EXPIRY_HOURS = 35

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def generate_key(n=12):
    return ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(n))

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>VERTEX Z</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          margin: 0; padding: 0;
          background: #000;
          color: #fff;
          min-height: 100vh;
          display: flex; justify-content: center; align-items: center;
        }
        .container {
          text-align: center;
          background: rgba(20,20,20,0.95);
          padding: 2rem;
          border-radius: 12px;
          box-shadow: 0 8px 25px rgba(0,0,0,0.7);
        }
        h1 { color: #ace9ff; margin-bottom: 1rem; }
        .btn {
          display: inline-block;
          padding: 12px 24px;
          border-radius: 8px;
          background: linear-gradient(90deg,#00ffc3,#00e0b0);
          color: #000; font-weight: bold; text-decoration: none;
          transition: 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>VERTEX Z</h1>
        <p>Click below to get your key</p>
        <a href="https://lootdest.org/s?zsW5sQch" target="_blank" class="btn">Get Key</a>
      </div>
    </body>
    </html>
    """

@app.route("/completed")
def get_key():
    referer = request.headers.get("Referer", "")
    if not any(src in (referer or "") for src in ALLOWED_SOURCES):
        return "<h1 style='color:red;text-align:center'>❌ Access Denied</h1>", 403

    db = load_db()
    key = generate_key()
    db[key] = {
        "created_at": int(time.time()),
        "expiry": DEFAULT_EXPIRY_HOURS * 3600,
        "redeemed": False
    }
    save_db(db)

    # Your theme template with key injected
    template = open("theme.html").read()
    return template.replace("PLACE_HOLDER_KEY", key)

def _corsify(resp, code=200):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp, code

@app.route("/validate", methods=["GET", "POST", "OPTIONS"])
def validate():
    if request.method == "OPTIONS":
        return _corsify(jsonify({}), 204)

    key = None
    if request.is_json:
        data = request.get_json(silent=True) or {}
        key = data.get("key")
    if not key:
        key = request.args.get("key") or request.form.get("key")

    db = load_db()
    record = db.get(key)
    ok = False

    if record:
        created = record.get("created_at", 0)
        expiry = record.get("expiry", DEFAULT_EXPIRY_HOURS * 3600)
        if not record.get("redeemed") and (time.time() - created) < expiry:
            ok = True

    resp = jsonify({"success": ok, "message": "Key is valid!" if ok else "Invalid or expired key!"})
    return _corsify(resp, 200 if ok else 400)

@app.route("/redeem", methods=["POST"])
def redeem():
    data = request.get_json(silent=True) or {}
    key = data.get("key")

    db = load_db()
    record = db.get(key)
    if record and not record["redeemed"]:
        record["redeemed"] = True
        save_db(db)
        return jsonify({"success": True, "message": "Key redeemed!"})
    return jsonify({"success": False, "message": "Invalid or already used key!"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=20092)
