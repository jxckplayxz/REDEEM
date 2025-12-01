# app.py — CLOUD-DASH CLASSIC UI IS BACK BABY (OLD UI YOU LOVED + FULLY FIXED)
from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cloud-dash-classic-forever"

DB_FILE = "cloud_dash.db"
ADMIN_PASSWORD = "gameadder123"
PLACEHOLDER = "https://placehold.co/200x160/000/facc15?text=CLOUD-DASH"
CATEGORIES = ['Action', 'Puzzle', 'Strategy', 'Arcade', 'Simulation', 'Other']

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY, title TEXT, category TEXT, image TEXT, description TEXT,
        type TEXT, sourceUrl TEXT, htmlContent TEXT, likeCount INTEGER DEFAULT 0,
        reportCount INTEGER DEFAULT 0, createdAt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
              ("announcement", json.dumps({"title": "Cloud-Dash", "message": "Old UI is back — enjoy the classic vibe", "isActive": True})))
    conn.commit()
    conn.close()

init_db()

ICONS = {
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
    "key: '<svg xmlns="http://www.w3.org/2000/svg" class="w-20 h-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
}
def icon(name): return ICONS.get(name, "")

# OLD CLASSIC UI YOU LOVED — FULLY RESTORED
HTML = '''
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>CLOUD-DASH</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .card:hover { transform: translateY(-12px); }
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">

  {% if announcement.isActive %}
  <div class="bg-gradient-to-r from-indigo-600 to-purple-600 py-3 px-6 text-lg font-bold shadow-lg flex justify-between items-center sticky top-0 z-50">
    <div class="flex items-center gap-3">
      {{ icon("zap")|safe }} <span>{{ announcement.title }} — {{ announcement.message }}</span>
    </div>
    <button onclick="this.parentElement.style.display='none'" class="text-2xl">×</button>
  </div>
  {% endif %}

  <div class="max-w-7xl mx-auto p-6">
    <div class="flex justify-between items-center mb-10">
      <h1 class="text-6xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-4">
        {{ icon("cloud")|safe }} CLOUD-DASH
      </h1>
      <a href="/admin" class="bg-purple-600 hover:bg-purple-700 px-8 py-4 rounded-xl text-xl font-bold shadow-xl">
        Admin Panel
      </a>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-8">
      {% for g in games %}
      <div onclick="location.href='/play/{{ g.id }}'" class="bg-gray-800 rounded-2xl overflow-hidden shadow-2xl card transition-all duration-300 border border-gray-700 hover:border-purple-500 cursor-pointer">
        <img src="{{ g.image or placeholder }}" class="w-full h-48 object-cover" onerror="this.src='{{ placeholder }}'">
        <div class="p-5">
          <h3 class="text-xl font-bold mb-2 truncate">{{ g.title }}</h3>
          <p class="text-sm text-gray-400 line-clamp-2 mb-4">{{ g.description or "No description" }}</p>
          <div class="flex justify-between items-center">
            <button onclick="event.stopPropagation(); like('{{ g.id }}')" class="flex items-center gap-2 text-pink-500 hover:text-pink-400">
              {{ icon("heart")|safe }} <span id="l{{ g.id }}">{{ g.likeCount }}</span>
            </button>
            <span class="bg-gray-700 px-3 py-1 rounded-full text-xs">{{ g.category }}</span>
          </div>
        </div>
      </div>
      {% else %}
      <div class="col-span-full text-center py-20">
        <p class="text-4xl text-gray-600">No games yet...</p>
        <p class="text-2xl mt-4">Add some in <a href="/admin" class="text-purple-400 underline">Admin Panel</a></p>
      </div>
      {% endfor %}
    </div>
  </div>

  <script>
    function like(id) {
      fetch("/like/"+id, {method:"POST"})
        .then(r => r.json())
        .then(data => document.getElementById("l"+id).textContent = data.likes);
    }
  </script>
</body>
</html>
'''

# ADMIN PANEL — SEXY LOGIN + CLEAN DASHBOARD
ADMIN_PANEL_HTML = '''
<!DOCTYPE html>
<html class="h-full">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Admin • Cloud-Dash</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-gray-900 to-black min-h-screen flex items-center justify-center p-4">

  <!-- LOGIN -->
  <div class="{% if session.admin %}hidden{% endif %} bg-gray-900 border-4 border-purple-600 rounded-3xl p-12 max-w-lg w-full text-center shadow-2xl">
    <div class="w-32 h-32 bg-purple-600 rounded-full mx-auto flex items-center justify-center mb-8">
      {{ icon("key")|safe }}
    </div>
    <h1 class="text-5xl font-bold mb-8">ADMIN LOGIN</h1>
    <form method="post" class="space-y-6">
      <input type="password" name="pwd" placeholder="password..." class="w-full p-5 text-xl bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 outline-none"/>
      {% if error %}<p class="text-red-500 text-xl font-bold">{{ error }}</p>{% endif %}
      <button class="w-full bg-purple-600 hover:bg-purple-700 py-5 rounded-xl text-2xl font-bold">ENTER</button>
    </form>
  </div>

  <!-- DASHBOARD -->
  <div class="{% if not session.admin %}hidden{% endif %} max-w-5xl w-full mx-auto bg-gray-900 rounded-3xl shadow-2xl overflow-hidden border border-purple-600">
    <div class="bg-gradient-to-r from-purple-600 to-indigo-600 p-10 text-center">
      <h1 class="text-6xl font-bold">CLOUD-DASH ADMIN</h1>
    </div>
    <div class="p-10 space-y-10">

      <div class="bg-gray-800 rounded-2xl p-8">
        <h2 class="text-3xl font-bold mb-6">Announcement</h2>
        <form action="/admin/announcement" method="post" class="space-y-4">
          <input name="title" value="{{ announcement.title }}" class="w-full p-4 bg-gray-700 rounded-lg"/>
          <textarea name="message" rows="3" class="w-full p-4 bg-gray-700 rounded-lg">{{ announcement.message }}</textarea>
          <label class="flex items-center gap-3 text-xl">
            <input type="checkbox" name="active" {{ 'checked' if announcement.isActive else '' }} class="w-6 h-6"/>
            Show Banner
          </label>
          <button class="w-full bg-purple-600 hover:bg-purple-700 py-4 rounded-lg font-bold text-xl">Update</button>
        </form>
      </div>

      <div class="bg-gray-800 rounded-2xl p-8">
        <h2 class="text-3xl font-bold mb-6">Add Game</h2>
        <form action="/admin/add" method="post" class="space-y-4">
          <input name="title" placeholder="Title" required class="w-full p-4 bg-gray-700 rounded-lg"/>
          <select name="category" class="w-full p-4 bg-gray-700 rounded-lg">
            {% for c in categories %}<option>{{ c }}</option>{% endfor %}
          </select>
          <input name="image" value="{{ placeholder }}" class="w-full p-4 bg-gray-700 rounded-lg"/>
          <textarea name="description" rows="3" placeholder="Description" class="w-full p-4 bg-gray-700 rounded-lg"></textarea>
          <div class="flex gap-6 text-lg">
            <label><input type="radio" name="type" value="url" checked> URL</label>
            <label><input type="radio" name="type" value="html"> HTML</label>
          </div>
          <input name="sourceUrl" placeholder="https://..." class="w-full p-4 bg-gray-700 rounded-lg"/>
          <textarea name="htmlContent" placeholder="<iframe..." rows="8" class="w-full p-4 bg-gray-700 rounded-lg font-mono text-sm hidden"></textarea>
          <button class="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 py-5 rounded-lg font-bold text-2xl mt-6">
            PUBLISH GAME
          </button>
        </form>
      </div>

      <a href="/" class="block text-center bg-gray-800 hover:bg-gray-700 py-4 rounded-xl text-xl font-bold">
        {{ icon("home")|safe }} Back to Home
      </a>
    </div>
  </div>

  <script>
    document.querySelectorAll('input[name="type"]').forEach(r => r.onchange = () => {
      let u = document.querySelector('input[name="sourceUrl"]');
      let h = document.querySelector('textarea[name="htmlContent"]');
      if (r.value === 'html') { u.classList.add('hidden'); h.classList.remove('hidden'); }
      else { h.classList.add('hidden'); u.classList.remove('hidden'); }
    });
  </script>
</body>
</html>
'''

# ROUTES (ALL FIXED & WORKING)
@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = "user_" + str(uuid.uuid4())[:8]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games ORDER BY createdAt DESC")
    games = []
    for row in c.fetchall():
        games.append({
            "id": row[0], "title": row[1], "category": row[2], "image": row[3] or PLACEHOLDER,
            "description": row[4], "likeCount": row[8], "reportCount": row[9]
        })
    c.execute("SELECT value FROM config WHERE key='announcement'")
    row = c.fetchone()
    announcement = json.loads(row[0]) if row else {"title":"Cloud-Dash","message":"Classic UI is back","isActive":True}
    conn.close()

    return render_template_string(HTML, games=games, announcement=announcement, placeholder=PLACEHOLDER, icon=icon)

@app.route("/play/<game_id>")
def play(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title,type,sourceUrl,htmlContent FROM games WHERE id=?", (game_id,))
    row = c.fetchone()
    conn.close()
    if not row: return "Not found", 404
    title, typ, url, html = row
    src = f"data:text/html;charset=utf-8,{html}" if typ == "html" else url
    return f'''
    <!DOCTYPE html><html><head><title>{title}</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black m-0"><iframe src="{src}" class="w-full h-screen" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen></iframe>
    <a href="/" class="fixed top-4 left-4 bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-full z-50">Back</a>
    </body></html>
    '''

@app.route("/admin", methods=["GET","POST"])
def admin():
    error = None
    if request.method == "POST":
        if request.form.get("pwd") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            error = "Wrong password"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='announcement'")
    row = c.fetchone()
    announcement = json.loads(row[0]) if row else {"title":"Welcome","message":"","isActive":True}
    conn.close()

    return render_template_string(ADMIN_PANEL_HTML, error=error, announcement=announcement,
                                  categories=CATEGORIES, placeholder=PLACEHOLDER, icon=icon, session=session)

@app.route("/admin/announcement", methods=["POST"])
def update_announcement():
    if not session.get("admin"): return redirect("/admin")
    data = json.dumps({"title": request.form["title"], "message": request.form["message"], "isActive": "active" in request.form})
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('announcement', ?)", (data,))
    conn.commit(); conn.close()
    return redirect("/admin")

@app.route("/admin/add", methods=["POST"])
def add_game():
    if not session.get("admin"): return redirect("/admin")
    gid = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''INSERT INTO games (id,title,category,image,description,type,sourceUrl,htmlContent,createdAt) 
                    VALUES (?,?,?,?,?,?,?,?,?)''', (
        gid, request.form["title"], request.form["category"], request.form["image"] or PLACEHOLDER,
        request.form["description"], request.form["type"], request.form.get("sourceUrl",""),
        request.form.get("htmlContent",""), datetime.now().isoformat()
    ))
    conn.commit(); conn.close()
    return redirect("/")

@app.route("/like/<game_id>", methods=["POST"])
def like(game_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE games SET likeCount = likeCount + 1 WHERE id=?", (game_id,))
    c = conn.cursor()
    c.execute("SELECT likeCount FROM games WHERE id=?", (game_id,))
    likes = c.fetchone()[0]
    conn.commit(); conn.close()
    return jsonify({"likes": likes})

if __name__ == "__main__":
    print("CLOUD-DASH CLASSIC UI IS BACK")
    print("http://127.0.0.1:5000")
    print("Password: gameadder123")
    app.run(host="0.0.0.0", port=5000, debug=True)