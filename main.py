from flask import Flask, request, session, redirect, render_template_string, url_for
import json, os, uuid, time

app = Flask(__name__)
app.secret_key = "CLOUD_DASH_SECRET_2025"

# --------------------------
# JSON SAVE / LOAD HELPERS
# --------------------------

def load_json(path, fallback):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(fallback, f, indent=4)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# JSON “database”
GAMES = "games.json"
REPORTS = "reports.json"
LIKES = "likes.json"

games = load_json(GAMES, [])
reports = load_json(REPORTS, [])
likes = load_json(LIKES, {})

# --------------------------
# HTML TEMPLATE
# --------------------------

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Cloud Dash</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://unpkg.com/lucide-static@latest/font/lucide.css" rel="stylesheet">
</head>

<body class="bg-neutral-900 text-white">

<div class="p-4 bg-neutral-800 shadow-lg flex justify-between">
    <h1 class="text-3xl font-bold">☁️ Cloud Dash</h1>
    <div class="space-x-4">
        <a href="/" class="hover:text-yellow-400">Home</a>
        <a href="/admin" class="hover:text-yellow-400">Admin</a>
    </div>
</div>

<div class="p-6">
    {{ content }}
</div>

</body>
</html>
"""

# --------------------------
# HOME PAGE
# --------------------------

@app.route("/")
def home():
    q = request.args.get("q", "").lower()

    filtered = []
    for g in games:
        if q in g["title"].lower():
            filtered.append(g)

    html = """
    <form method='get' class='mb-6'>
        <input name='q' placeholder='Search...' class='px-4 py-2 w-full rounded bg-neutral-800'>
    </form>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    """

    for g in filtered if q else games:
        html += f"""
        <div class="bg-neutral-800 p-4 rounded-lg shadow-lg">
            <img src="{g['image']}" class="rounded mb-3 border border-neutral-700 w-full h-32 object-cover">
            <h2 class="font-bold text-lg">{g['title']}</h2>
            <p class="text-sm text-neutral-400">{g['category']}</p>

            <div class="flex justify-between mt-4">
                <a href="/play/{g['id']}" class="text-blue-400">Play</a>
                <a href="/like/{g['id']}" class="text-red-400">
                    ❤ {likes.get(g['id'], 0)}
                </a>
            </div>

            <a href="/report/{g['id']}" class="text-yellow-400 text-sm block mt-2">Report</a>
        </div>
        """

    html += "</div>"

    return render_template_string(BASE, content=html)

# --------------------------
# PLAY GAME
# --------------------------

@app.route("/play/<id>")
def play(id):
    g = next((x for x in games if x["id"] == id), None)
    if not g:
        return "Game not found"

    html = f"""
    <h1 class="text-3xl font-bold mb-4">{g['title']}</h1>
    <iframe src="{g['url']}" class="w-full h-[600px] rounded-lg border-2 border-neutral-700"></iframe>
    """

    return render_template_string(BASE, content=html)

# --------------------------
# LIKE GAME
# --------------------------

@app.route("/like/<id>")
def like(id):
    likes[id] = likes.get(id, 0) + 1
    save_json(LIKES, likes)
    return redirect("/")

# --------------------------
# REPORT GAME
# --------------------------

@app.route("/report/<id>")
def report(id):
    reports.append({"id": id, "time": time.time()})
    save_json(REPORTS, reports)
    return redirect("/")

# --------------------------
# ADMIN LOGIN
# --------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == "gameadder123":
            session["admin"] = True
            return redirect("/admin")

    if not session.get("admin"):
        return render_template_string(BASE, content="""
            <h1 class="text-xl font-bold mb-4">Admin Login</h1>
            <form method="post">
                <input name="password" type="password" placeholder="Password"
                    class="px-4 py-2 rounded bg-neutral-800 w-full mb-4">
                <button class="px-4 py-2 bg-blue-500 rounded w-full">Login</button>
            </form>
        """)

    # Admin panel
    html = """
    <h1 class="text-3xl font-bold mb-6">Admin Dashboard</h1>

    <h2 class="text-xl font-bold mb-2">Add Game</h2>

    <form method="post" action="/add_game" class="mb-10">
        <input name="title" placeholder="Game Title" class="w-full mb-3 px-4 py-2 bg-neutral-800 rounded">
        <input name="image" placeholder="Image URL" class="w-full mb-3 px-4 py-2 bg-neutral-800 rounded">
        <input name="url" placeholder="Game URL" class="w-full mb-3 px-4 py-2 bg-neutral-800 rounded">
        <input name="category" placeholder="Category" class="w-full mb-3 px-4 py-2 bg-neutral-800 rounded">
        <button class="px-4 py-2 bg-yellow-500 text-black rounded w-full font-bold">Add Game</button>
    </form>

    <h2 class="text-xl font-bold mb-4">All Games</h2>
    <ul>
    """

    for g in games:
        html += f"<li>{g['title']} — <a class='text-red-400' href='/delete/{g['id']}'>Delete</a></li>"

    html += "</ul>"

    return render_template_string(BASE, content=html)

# --------------------------
# ADD GAME
# --------------------------

@app.route("/add_game", methods=["POST"])
def add_game():
    if not session.get("admin"):
        return "Unauthorized"

    games.append({
        "id": str(uuid.uuid4()),
        "title": request.form["title"],
        "image": request.form["image"],
        "url": request.form["url"],
        "category": request.form["category"]
    })

    save_json(GAMES, games)
    return redirect("/admin")

# --------------------------
# DELETE GAME
# --------------------------

@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return "Unauthorized"

    global games
    games = [g for g in games if g["id"] != id]
    save_json(GAMES, games)
    return redirect("/admin")


# --------------------------
# RUN
# --------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
