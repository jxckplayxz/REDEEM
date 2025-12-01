# app.py - Cloud-Dash FULLY OFFLINE (SQLite + JSON) - ONE FILE
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "cloud-dash-secret-2025"

# === DATABASE SETUP (SQLite + JSON fallback) ===
DB_FILE = "cloud_dash.db"
GAMES_FILE = "games.json"  # fallback if no SQLite

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY,
        title TEXT, category TEXT, image TEXT, description TEXT,
        type TEXT, sourceUrl TEXT, htmlContent TEXT,
        likeCount INTEGER DEFAULT 0, reportCount INTEGER DEFAULT 0,
        createdAt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id TEXT, reason TEXT, user_id TEXT, timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    # Default announcement
    c.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)',
              ("announcement", json.dumps({
                  "isActive": True,
                  "title": "Welcome to Cloud-Dash!",
                  "message": "Use Admin Panel (password: gameadder123) to add games."
              })))
    conn.commit()
    conn.close()

init_db()

# === CONFIG ===
ADMIN_PASSWORD = "admin12."
PLACEHOLDER_IMAGE = "https://placehold.co/200x160/000000/facc15?text=CLOUD-DASH"
CATEGORY_OPTIONS = ['Action', 'Puzzle', 'Strategy', 'Arcade', 'Simulation', 'Other']

# === SVG ICONS (same as original) ===
ICONS = {
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h-.01a6 6 0 0 1 5.01 6.32"/></svg>',
    "plus": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "flag": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
    "code": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "link": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.74 1.74"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "x": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "loader": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin"><circle cx="12" cy="12" r="10" opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>',
}

def icon(name, cls="w-5 h-5"):
    svg = ICONS.get(name, "")
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{svg}</svg>'

# === FULL HTML (exact same as React version) ===
HTML = '''
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CLOUD-DASH</title><script src="https://cdn.tailwindcss.com"></script>
<style>
  @keyframes neon-pulse{0%,100%{opacity:1;filter:drop-shadow(0 0 4px #22D3EE)}50%{opacity:0.7;filter:drop-shadow(0 0 15px #0EA5E9)}}
  .neon-text-blue{animation:neon-pulse 2s infinite alternate}
  .line-clamp-2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
</style>
</head>
<body class="min-h-screen bg-gray-50 font-sans flex flex-col">

  {% if announcement.isActive %}
  <div class="sticky top-0 z-50 bg-indigo-600 text-white shadow-xl">
    <div class="max-w-7xl mx-auto py-3 px-6 flex justify-between items-center">
      <div class="flex items-center gap-3">
        {{ icon("zap", "w-6 h-6")|safe }}
        <p><strong>{{ announcement.title }}</strong> {{ announcement.message }}</p>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" class="p-2 hover:bg-indigo-700 rounded">X</button>
    </div>
  </div>
  {% endif %}

  <header class="bg-white shadow-lg p-4 sticky top-0 z-40">
    <div class="text-xl font-bold text-indigo-700">User ID: {{ user_id }}</div>
  </header>

  <main class="flex-grow p-4 md:p-8">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
      <h1 class="text-5xl font-extrabold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
        {{ icon("cloud", "w-12 h-12 inline align-bottom mr-2")|safe }} Cloud-Dash
      </h1>
      <a href="/admin" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg flex items-center gap-2">
        {{ icon("plus")|safe }} Admin Panel
      </a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="relative md:col-span-2">
        <input type="text" id="search" placeholder="Search games..." class="w-full pl-10 pr-4 py-3 rounded-xl border shadow-inner" oninput="filter()">
        {{ icon("search", "absolute left-3 top-3.5 w-5 h-5 text-gray-400")|safe }}
      </div>
      <select id="cat" class="py-3 px-4 rounded-xl border" onchange="filter()">
        <option value="">All Categories</option>
        {% for c in categories %}<option>{{ c }}</option>{% endfor %}
      </select>
    </div>

    <div id="grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {% for g in games %}
      <div class="bg-white rounded-xl shadow-lg overflow-hidden border-t-4 border-indigo-500 hover:scale-105 transition cursor-pointer"
           onclick="location.href='/play/{{ g.id }}'">
        <div class="h-40 bg-gray-900">
          <img src="{{ g.image or placeholder_image }}" class="w-full h-full object-cover" onerror="this.src='{{ placeholder_image }}'">
        </div>
        <div class="p-4 flex flex-col h-full">
          <div class="flex justify-between mb-2">
            <h3 class="text-xl font-bold text-gray-800 truncate">{{ g.title }}</h3>
            <span class="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">{{ g.category or "N/A" }}</span>
          </div>
          <p class="text-sm text-gray-600 line-clamp-2 flex-grow">{{ g.description or "No description" }}</p>
          <div class="flex justify-between items-center mt-4 pt-3 border-t">
            <button onclick="event.stopPropagation(); like('{{ g.id }}')" class="flex items-center text-pink-600">
              {{ icon("heart", "w-5 h-5 mr-1")|safe }} <span id="likes-{{ g.id }}">{{ g.likeCount }}</span>
            </button>
            <button onclick="event.stopPropagation(); report('{{ g.id }}','{{ g.title|e }}')" class="text-xs text-red-600 flex items-center">
              {{ icon("flag", "w-4 h-4 mr-1")|safe }} Report ({{ g.reportCount }})
            </button>
            <button class="bg-indigo-600 text-white px-4 py-1 rounded-full text-sm">Play Now</button>
          </div>
        </div>
      </div>
      {% else %}
      <p class="col-span-full text-center text-gray-500 text-lg py-12">No games yet! Use Admin Panel to add some.</p>
      {% endfor %}
    </div>
  </main>

  <div id="toast" class="fixed bottom-4 right-4 z-50 space-y-2"></div>

  <div id="modal" class="hidden fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-bold text-red-600">{{ icon("flag", "w-6 h-6 inline mr-2")|safe }} Report Game</h3>
        <button onclick="document.getElementById('modal').classList.add('hidden')" class="text-gray-500">X</button>
      </div>
      <p id="title" class="font-medium mb-4"></p>
      <textarea id="reason" rows="4" placeholder="Why are you reporting this?" class="w-full border rounded-lg p-3"></textarea>
      <div class="flex justify-end gap-3 mt-4">
        <button onclick="document.getElementById('modal').classList.add('hidden')" class="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
        <button onclick="submitReport()" class="px-4 py-2 bg-red-600 text-white rounded-lg flex items-center gap-2">
          {{ icon("loader", "hidden w-5 h-5")|safe }} Submit
        </button>
      </div>
    </div>
  </div>

  <script>
    function toast(t,type="success"){const e=document.createElement("div");e.className=`p-4 rounded-lg shadow-2xl text-white flex items-center gap-3 \( {type==="success"?"bg-green-500":"bg-red-500"} animate-in slide-in-from-bottom`;e.innerHTML=` \){type==="success"?"Check":"Cross"} <span class="font-bold">${t}</span> <button onclick="this.parentElement.remove()" class="ml-4">X</button>`;document.getElementById("toast").appendChild(e);setTimeout(()=>e.remove(),3000)}
    function like(id){fetch("/like/"+id,{method:"POST"}).then(r=>r.json()).then(d=>{document.getElementById("likes-"+id).textContent=d.likes;toast("Liked!")})}
    let reportId=""; function report(id,title){reportId=id;document.getElementById("title").textContent="Reporting: "+title;document.getElementById("modal").classList.remove("hidden")}
    function submitReport(){const r=document.getElementById("reason").value.trim();if(!r)return toast("Write a reason","error");fetch("/report/"+reportId,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reason:r})}).then(()=> {toast("Report sent!");document.getElementById("modal").classList.add("hidden")})}
    function filter(){const s=document.getElementById("search").value.toLowerCase(),c=document.getElementById("cat").value;document.querySelectorAll("#grid > div").forEach(d=>{const t=d.querySelector("h3").textContent.toLowerCase(),desc=d.querySelector("p").textContent.toLowerCase(),cat=d.querySelector("span").textContent;(t.includes(s)||desc.includes(s))&&(!c||cat===c)?d.style.display="":d.style.display="none"})}
  </script>
</body></html>
'''

@app.route("/")
def home():
    if "user_id" not in session:
        session["user_id"] = "user_" + str(uuid.uuid4())[:8]

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games ORDER BY createdAt DESC")
    games = [{"id":row[0], "title":row[1], "category":row[2], "image":row[3], "description":row[4],
              "type":row[5], "sourceUrl":row[6], "htmlContent":row[7], "likeCount":row[8], "reportCount":row[9]} 
             for row in c.fetchall()]
    
    c.execute("SELECT value FROM config WHERE key='announcement'")
    ann = c.fetchone()
    announcement = json.loads(ann[0]) if ann else {"isActive":True, "title":"Welcome!", "message":"Use Admin Panel"}
    conn.close()

    return render_template_string(HTML, games=games, announcement=announcement,
                                  user_id=session["user_id"], placeholder_image=PLACEHOLDER_IMAGE,
                                  categories=CATEGORY_OPTIONS, icon=icon)

@app.route("/play/<game_id>")
def play(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE id=?", (game_id,))
    g = c.fetchone()
    conn.close()
    if not g: return "Game not found", 404
    game = {"id":g[0], "title":g[1], "type":g[5], "sourceUrl":g[6], "htmlContent":g[7]}
    src = f"data:text/html;charset=utf-8,{game['htmlContent']}" if game["type"]=="html" else game["sourceUrl"]
    return f'''
    <!DOCTYPE html><html><head><title>{game["title"]}</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white min-h-screen flex flex-col">
      <header class="bg-gray-800 p-4 flex justify-between"><h1 class="text-xl font-bold">Playing: {game["title"]}</h1>
      <a href="/" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-full">Exit</a></header>
      <div class="p-4 bg-yellow-100 text-yellow-800 rounded-lg m-4 text-sm">Warning: { "Embedded HTML" if game["type"]=="html" else "External URL" }</div>
      <iframe src="{src}" class="flex-grow w-full border-4 border-indigo-600 rounded-xl" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen></iframe>
    </body></html>
    '''

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and request.form.get("pwd") == ADMIN_PASSWORD:
        session["admin"] = True
    if not session.get("admin"):
        return '''
        <form method="post" class="max-w-md mx-auto mt-32 text-center">
          <input type="password" name="pwd" placeholder="Admin Password" class="border p-4 rounded text-2xl w-full"/>
          <button class="mt-4 bg-red-600 text-white py-4 px-8 rounded-xl text-xl">Enter Admin</button>
        </form>
        '''
    return f'''
    <div class="max-w-4xl mx-auto p-8 bg-white rounded-xl shadow-2xl mt-8">
      <h1 class="text-4xl font-bold text-indigo-700 mb-8">Admin Panel</h1>
      <form method="post" action="/add">
        <input name="title" placeholder="Title" required class="border p-3 w-full rounded mb-3"/>
        <select name="category" class="border p-3 w-full rounded mb-3">{''.join(f"<option>{c}</option>" for c in CATEGORY_OPTIONS)}</select>
        <input name="image" placeholder="Image URL" required class="border p-3 w-full rounded mb-3"/>
        <textarea name="description" placeholder="Description" class="border p-3 w-full rounded mb-3" rows="3"></textarea>
        <div class="flex gap-4 mb-3">
          <label><input type="radio" name="type" value="url" checked onclick="document.getElementById('html').classList.add('hidden');document.getElementById('url').classList.remove('hidden')"> URL</label>
          <label><input type="radio" name="type" value="html" onclick="document.getElementById('url').classList.add('hidden');document.getElementById('html').classList.remove('hidden')"> HTML</label>
        </div>
        <input id="url" name="sourceUrl" placeholder="https://game.com" class="border p-3 w-full rounded mb-3"/>
        <textarea id="html" name="htmlContent" placeholder="<html>..." rows="10" class="border p-3 w-full rounded mb-3 hidden font-mono text-sm"></textarea>
        <button class="bg-indigo-600 text-white py-4 px-8 rounded-xl text-xl hover:bg-indigo-700">Publish Game</button>
      </form>
      <a href="/" class="mt-8 inline-block text-indigo-600">Back to Games</a>
    </div>
    '''

@app.route("/add", methods=["POST"])
def add():
    if not session.get("admin"): return redirect("/admin")
    game_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO games (id, title, category, image, description, type, sourceUrl, htmlContent, likeCount, reportCount, createdAt)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
              (game_id, request.form["title"], request.form["category"], request.form["image"], request.form["description"],
               request.form["type"], request.form.get("sourceUrl"), request.form.get("htmlContent"), datetime.now().isoformat()))
    conn.commit(); conn.close()
    return redirect("/")

@app.route("/like/<game_id>", methods=["POST"])
def like(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE games SET likeCount = likeCount + 1 WHERE id=?", (game_id,))
    c.execute("SELECT likeCount FROM games WHERE id=?", (game_id,))
    likes = c.fetchone()[0]
    conn.commit(); conn.close()
    return jsonify({"likes": likes})

@app.route("/report/<game_id>", methods=["POST"])
def report(game_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO reports (game_id, reason, user_id, timestamp) VALUES (?, ?, ?, ?)",
              (game_id, data["reason"], session.get("user_id", "anonymous"), datetime.now().isoformat()))
    c.execute("UPDATE games SET reportCount = reportCount + 1 WHERE id=?", (game_id,))
    conn.commit(); conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    print("Cloud-Dash Offline Edition Running!")
    print("→ http://localhost:5000")
    print("Admin password: gameadder123")
    app.run(host="0.0.0.0", port=5000, debug=True)