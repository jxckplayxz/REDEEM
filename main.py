# app.py - FINAL VERSION: 100% IDENTICAL TO YOUR REACT APP (NO FIREBASE)
from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cloud-dash-ultimate-2025"

DB_FILE = "cloud_dash.db"
ADMIN_PASSWORD = "admin123."
PLACEHOLDER = "https://placehold.co/200x160/000/facc15?text=CLOUD-DASH"
CATEGORIES = ['Action', 'Puzzle', 'Strategy', 'Arcade', 'Simulation', 'Other']

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id TEXT PRIMARY KEY, title TEXT, category TEXT, image TEXT, description TEXT,
        type TEXT, sourceUrl TEXT, htmlContent TEXT, likeCount INTEGER, reportCount INTEGER,
        createdAt TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, game_id TEXT, reason TEXT, user_id TEXT, timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY, value TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO config VALUES (?, ?)',
              ("announcement", json.dumps({"title": "Welcome!", "message": "to Cloud-Dash", "isActive": True})))
    conn.commit()
    conn.close()

init_db()

ICONS = {
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>',
    "plus": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>',
    "key": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="7.5" cy="12.5" r="4.5"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8l8 8m0-8l-8 8"/></svg>',
    "unlock": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0"/></svg>',
    "flag": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
    "link": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>',
    "code": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
    "x": '<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
    "send": '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>',
    "loader": '<svg class="animate-spin w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>',
}

def icon(name): return ICONS.get(name, "")

# FULL HTML WITH EXACT REACT UI
HTML = '''
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CLOUD-DASH</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    @keyframes neon-pulse { 0%,100%{text-shadow: 0 0 10px #22D3EE} 50%{text-shadow: 0 0 20px #0EA5E9} }
    .neon-text-blue { animation: neon-pulse 2s infinite alternate; }
  </style>
</head>
<body class="min-h-screen bg-gray-50 font-sans flex flex-col">

  {% if announcement.isActive %}
  <div class="sticky top-0 z-50 bg-indigo-600 text-white shadow-xl">
    <div class="max-w-7xl mx-auto py-3 px-6 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <span class="p-2 bg-indigo-800 rounded-lg">{{ icon("zap")|safe }}</span>
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
        {{ icon("cloud")|safe }} Cloud-Dash
      </h1>
      <a href="/admin" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg flex items-center gap-2">
        {{ icon("plus")|safe }} Admin Panel
      </a>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="relative md:col-span-2">
        <input type="text" id="search" placeholder="Search games..." class="w-full pl-10 pr-4 py-3 rounded-xl border shadow-inner" oninput="filter()">
        <span class="absolute left-3 top-3.5">{{ icon("search")|safe }}</span>
      </div>
      <select id="cat" class="py-3 px-4 rounded-xl border shadow-inner" onchange="filter()">
        <option value="">All Categories</option>
        {% for c in categories %}<option>{{ c }}</option>{% endfor %}
      </select>
    </div>

    <div id="grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {% for g in games %}
      <div class="bg-white rounded-xl shadow-lg overflow-hidden border-t-4 border-indigo-500 hover:scale-105 transition cursor-pointer"
           onclick="location.href='/play/{{ g.id }}'">
        <img src="{{ g.image or placeholder }}" class="w-full h-40 object-cover" onerror="this.src='{{ placeholder }}'">
        <div class="p-4">
          <div class="flex justify-between mb-2">
            <h3 class="text-xl font-bold truncate">{{ g.title }}</h3>
            <span class="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">{{ g.category }}</span>
          </div>
          <p class="text-sm text-gray-600 line-clamp-2 mb-4">{{ g.description or "No description" }}</p>
          <div class="flex justify-between items-center pt-3 border-t">
            <button onclick="event.stopPropagation(); like('{{ g.id }}')" class="flex items-center text-pink-600">
              {{ icon("heart")|safe }} <span id="l{{ g.id }}">{{ g.likeCount }}</span>
            </button>
            <button onclick="event.stopPropagation(); openReport('{{ g.id }}','{{ g.title|e }}')" class="text-red-600 text-sm flex items-center">
              {{ icon("flag")|safe }} Report ({{ g.reportCount }})
            </button>
            <button class="bg-indigo-600 text-white px-4 py-1 rounded-full text-sm">Play Now</button>
          </div>
        </div>
      </div>
      {% else %}
      <p class="col-span-full text-center text-gray-500 text-lg py-12">No games yet! Use Admin Panel.</p>
      {% endfor %}
    </div>
  </main>

  <!-- Toast -->
  <div id="toast" class="fixed bottom-4 right-4 z-50 space-y-2"></div>

  <!-- Report Modal -->
  <div id="modal" class="hidden fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full">
      <div class="flex justify-between items-center mb-4 border-b pb-3">
        <h3 class="text-xl font-bold text-red-600 flex items-center">{{ icon("flag")|safe }} Report Game</h3>
        <button onclick="document.getElementById('modal').classList.add('hidden')" class="text-gray-500 hover:text-black">{{ icon("x")|safe }}</button>
      </div>
      <p id="reportTitle" class="font-medium mb-4"></p>
      <textarea id="reason" rows="4" placeholder="Why are you reporting this game?" class="w-full border rounded-lg p-3"></textarea>
      <div class="flex justify-end gap-3 mt-6">
        <button onclick="document.getElementById('modal').classList.add('hidden')" class="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
        <button onclick="submitReport()" class="px-4 py-2 bg-red-600 text-white rounded-lg flex items-center gap-2">
          {{ icon("loader")|safe }} Submit Report
        </button>
      </div>
    </div>
  </div>

  <script>
    function toast(t, type="success"){
      const d = document.createElement("div");
      d.className = `p-4 rounded-lg shadow-2xl text-white flex items-center gap-3 ${type==="success"?"bg-green-500":"bg-red-500"} animate-in slide-in-from-bottom`;
      d.innerHTML = `<span>${t}</span><button onclick="this.parentElement.remove()" class="ml-auto">X</button>`;
      document.getElementById("toast").appendChild(d);
      setTimeout(()=>d.remove(), 3000);
    }
    function like(id){fetch("/like/"+id,{method:"POST"}).then(r=>r.json()).then(d=> {document.getElementById("l"+id).textContent=d.likes; toast("Liked!");})}
    let rid=""; function openReport(id,title){rid=id;document.getElementById("reportTitle").textContent="Reporting: "+title;document.getElementById("modal").classList.remove("hidden")}
    function submitReport(){let r=document.getElementById("reason").value.trim();if(!r)return toast("Need a reason","error");fetch("/report/"+rid,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reason:r})}).then(()=>{toast("Report sent!");document.getElementById("modal").classList.add("hidden")})}
    function filter(){
      let s=document.getElementById("search").value.toLowerCase(), c=document.getElementById("cat").value;
      document.querySelectorAll("#grid > div").forEach(card=>{
        let t=card.querySelector("h3").textContent.toLowerCase(), d=card.querySelector("p").textContent.toLowerCase(), cat=card.querySelector("span").textContent;
        card.style.display = (t.includes(s)||d.includes(s)) && (!c||cat===c) ? "" : "none";
      });
    }
  </script>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-100 min-h-screen p-8">
<div class="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden">
  <div class="p-8">
    <h2 class="text-3xl font-extrabold text-gray-800 mb-6 border-b pb-4 flex items-center">
      {{ icon("unlock")|safe if session.admin else icon("key")|safe }} Admin Control Panel
    </h2>

    {% if not session.admin %}
    <div class="max-w-md mx-auto text-center py-12">
      <h3 class="text-2xl font-bold text-red-600 mb-6 flex items-center justify-center">
        {{ icon("zap")|safe }} Admin Access Required
      </h3>
      <form method="post">
        <input type="password" name="pwd" placeholder="Enter password" class="w-full p-4 border rounded-lg text-lg mb-4"/>
        {% if error %}<p class="text-red-600 mb-4">{{ error }}</p>{% endif %}
        <button class="w-full bg-red-600 hover:bg-red-700 text-white py-4 rounded-lg text-xl font-bold flex items-center justify-center gap-3">
          {{ icon("key")|safe }} Submit Password
        </button>
      </form>
    </div>
    {% else %}
    <div class="flex border-b mb-6">
      <button onclick="show('game')" id="tab-game" class="px-6 py-3 font-bold text-indigo-600 border-b-4 border-indigo-600">Game & Announcement</button>
      <button onclick="show('reports')" id="tab-reports" class="px-6 py-3 font-bold text-gray-500">Reported Games</button>
    </div>

    <!-- Game & Announcement Tab -->
    <div id="game" class="space-y-10">
      <!-- Announcement Editor -->
      <div class="p-6 bg-yellow-50 border-2 border-yellow-300 rounded-xl">
        <h3 class="text-2xl font-bold text-yellow-800 mb-4 flex items-center">{{ icon("zap")|safe }} Global Announcement</h3>
        <form action="/admin/announcement" method="post">
          <input name="title" value="{{ announcement.title }}" placeholder="Title" class="w-full p-3 border rounded-lg mb-3"/>
          <textarea name="message" placeholder="Message" class="w-full p-3 border rounded-lg mb-3" rows="2">{{ announcement.message }}</textarea>
          <label class="flex items-center gap-3 mb-4">
            <input type="checkbox" name="active" {{ 'checked' if announcement.isActive else '' }} class="w-5 h-5"/>
            <span>Show announcement banner</span>
          </label>
          <button class="w-full bg-yellow-600 hover:bg-yellow-700 text-white py-3 rounded-lg font-bold flex items-center justify-center gap-2">
            {{ icon("send")|safe }} Update Announcement
          </button>
        </form>
      </div>

      <!-- Add Game Form -->
      <div class="p-6 bg-indigo-50 border-2 border-indigo-300 rounded-xl">
        <h3 class="text-2xl font-bold text-indigo-800 mb-6 flex items-center">{{ icon("plus")|safe }} Add New Game</h3>
        <form action="/admin/add" method="post">
          <input name="title" placeholder="Title" required class="w-full p-3 border rounded-lg mb-3"/>
          <select name="category" class="w-full p-3 border rounded-lg mb-3 w-full">
            {% for c in categories %}<option>{{ c }}</option>{% endfor %}
          </select>
          <input name="image" placeholder="Image URL" value="{{ placeholder }}" class="w-full p-3 border rounded-lg mb-3"/>
          <textarea name="description" placeholder="Description" class="w-full p-3 border rounded-lg mb-3" rows="3"></textarea>
          <div class="flex gap-6 mb-4">
            <label class="flex items-center"><input type="radio" name="type" value="url" checked onclick="toggleType()"> URL</label>
            <label class="flex items-center"><input type="radio" name="type" value="html" onclick="toggleType()"> HTML</label>
          </div>
          <input id="url" name="sourceUrl" placeholder="https://" class="w-full p-3 border rounded-lg mb-3"/>
          <textarea id="html" name="htmlContent" placeholder="<html>..." rows="10" class="w-full p-3 border rounded-lg font-mono text-sm hidden"></textarea>
          <button class="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-4 rounded-lg text-xl font-bold">
            Publish Game
          </button>
        </form>
      </div>
    </div>

    <!-- Reports Tab -->
    <div id="reports" class="hidden">
      <h3 class="text-2xl font-bold text-red-700 mb-6">Reported Games</h3>
      {% if reports %}
      {% for game in reports %}
      <div class="border-2 border-red-300 bg-red-50 rounded-xl p-6 mb-6">
        <div class="flex justify-between items-center mb-3">
          <h4 class="text-xl font-bold text-red-800">{{ game.title }}</h4>
          <span class="text-2xl font-bold text-red-600">{{ game.reportCount }} reports</span>
        </div>
        <p class="text-gray-700 mb-4">{{ game.description }}</p>
        <details class="bg-white p-4 rounded-lg">
          <summary class="font-bold cursor-pointer">Show {{ game.reports|length }} reports</summary>
          {% for r in game.reports %}
          <div class="border-l-4 border-red-500 pl-4 py-2 mt-2 bg-gray-50">
            <p class="text-sm">"<i>{{ r.reason }}</i>"</p>
            <p class="text-xs text-gray-500">by {{ r.user_id }} • {{ r.timestamp }}</p>
          </div>
          {% endfor %}
        </details>
      </div>
      {% endfor %}
      {% else %}
      <p class="text-gray-600 text-lg py-8 text-center">No reports yet — all clear!</p>
      {% endif %}
    </div>
    {% endif %}

    <a href="/" class="mt-8 inline-block text-indigo-600 hover:underline flex items-center gap-2">
      {{ icon("home")|safe }} Back to Home
    </a>
  </div>
</div>

<script>
function toggleType(){
  document.getElementById('url').classList.toggle('hidden', document.querySelector('[name="type"]:checked').value !== 'url');
  document.getElementById('html').classList.toggle('hidden', document.querySelector('[name="type"]:checked').value !== 'html');
}
function show(tab){
  document.getElementById('game').classList.add('hidden');
  document.getElementById('reports').classList.add('hidden');
  document.getElementById(tab).classList.remove('hidden');
  document.querySelectorAll('button[id^="tab-"]').forEach(b=>b.classList.remove('text-indigo-600','border-b-4','border-indigo-600'));
  document.querySelectorAll('button[id^="tab-"]').forEach(b=>b.classList.add('text-gray-500'));
  document.getElementById('tab-'+tab).classList.add('text-indigo-600','border-b-4','border-indigo-600');
  document.getElementById('tab-'+tab).classList.remove('text-gray-500');
}
{% if session.admin %}show('game'); toggleType();{% endif %}
</script>
</body></html>
'''

@app.route("/")
def home():
    if "user_id" not in session: session["user_id"] = "user_" + str(uuid.uuid4())[:8]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games ORDER BY createdAt DESC")
    games = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
    c.execute("SELECT value FROM config WHERE key='announcement'")
    ann = json.loads(c.fetchone()[0]) if c.fetchone() else {"title":"Welcome!","message":"Use Admin Panel","isActive":True}
    conn.close()
    return render_template_string(HTML, games=games, announcement=ann, user_id=session["user_id"], placeholder=PLACEHOLDER, categories=CATEGORIES, icon=icon)

@app.route("/play/<game_id>")
def play(game_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE id=?", (game_id,))
    g = c.fetchone()
    conn.close()
    if not g: return "Not found", 404
    game = dict(zip([d[0] for d in c.description], g))
    src = f"data:text/html;charset=utf-8,{game['htmlContent']}" if game['type']=="html" else game['sourceUrl']
    return f'''
    <!DOCTYPE html><html><head><title>{game['title']}</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white min-h-screen flex flex-col">
      <header class="bg-gray-800 p-4 flex justify-between items-center">
        <h1 class="text-xl font-bold">Playing: {game['title']}</h1>
        <a href="/" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-full">Exit</a>
      </header>
      <div class="p-4 bg-yellow-100 text-yellow-800 rounded-lg m-4 text-sm">
        Warning: { "Embedded HTML" if game['type']=="html" else "External URL" }
      </div>
      <iframe src="{src}" class="flex-grow w-full border-4 border-indigo-600 rounded-xl" sandbox="allow-scripts allow-same-origin allow-popups allow-forms" allowfullscreen></iframe>
    </body></html>
    '''

@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST" and request.form.get("pwd") == ADMIN_PASSWORD:
        session["admin"] = True
    if not session.get("admin"):
        return render_template_string(ADMIN_HTML.replace("{% if not session.admin %}", "").split("{% else %}")[0], error=error, icon=icon)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key='announcement'")
    ann = json.loads(c.fetchone()[0])
    c.execute("SELECT g.*, COUNT(r.id) as reportCount FROM games g LEFT JOIN reports r ON g.id=r.game_id GROUP BY g.id HAVING reportCount > 0")
    reported = []
    for row in c.fetchall():
        game = dict(zip([d[0] for d in c.description], row))
        c.execute("SELECT reason, user_id, timestamp FROM reports WHERE game_id=?", (game['id'],))
        game['reports'] = [dict(zip(['reason','user_id','timestamp'], r)) for r in c.fetchall()]
        reported.append(game)
    conn.close()

    return render_template_string(ADMIN_HTML, session=session, announcement=ann, reports=reported, categories=CATEGORIES, placeholder=PLACEHOLDER, icon=icon)

@app.route("/admin/announcement", methods=["POST"])
def update_announcement():
    if not session.get("admin"): return redirect("/admin")
    active = "active" in request.form
    data = {"title": request.form["title"], "message": request.form["message"], "isActive": active}
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE config SET value=? WHERE key='announcement'", (json.dumps(data),))
    conn.commit(); conn.close()
    return redirect("/admin")

@app.route("/admin/add", methods=["POST"])
def add():
    if not session.get("admin"): return redirect("/admin")
    game_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (game_id, request.form["title"], request.form["category"], request.form["image"],
         request.form["description"], request.form["type"], request.form.get("sourceUrl"), request.form.get("htmlContent"),
         0, 0, datetime.now().isoformat()))
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

@app.route("/report/<game_id>", methods=["POST"])
def report(game_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO reports (game_id, reason, user_id, timestamp) VALUES (?,?,?,?)",
                (game_id, data["reason"], session.get("user_id", "anon"), datetime.now().isoformat()))
    conn.execute("UPDATE games SET reportCount = reportCount + 1 WHERE id=?", (game_id,))
    conn.commit(); conn.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    print("Cloud-Dash Ultimate Offline Edition")
    print("→ http://localhost:5000")
    print("Admin password: gameadder123")
    app.run(host="0.0.0.0", port=True)