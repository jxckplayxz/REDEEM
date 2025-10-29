#!/usr/bin/env python3
"""CloudHost Mini – auto-tunnel Flask servers with persistence"""

import os, json, uuid, time, shutil, threading, subprocess, re
from pathlib import Path
from flask import (
    Flask, request, session, redirect, url_for, render_template_string,
    send_file, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# -------------------------------------------------
# Config
# -------------------------------------------------
BASE_DIR = Path.cwd()
USERS_DIR = BASE_DIR / "users"
DATA_FILE = BASE_DIR / "data.json"
DEFAULT_APP_PORT = 5000
PORT_LOCK = threading.Lock()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", uuid.uuid4().hex)

# in-memory runtime
runtime = {
    "servers": {},          # sid → dict
    "next_port": DEFAULT_APP_PORT
}
USERS_DIR.mkdir(exist_ok=True)

# -------------------------------------------------
# Persistence
# -------------------------------------------------
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "servers": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f, indent=2)

DATA = load_data()

def _persist_servers():
    DATA.setdefault("servers", {})
    for sid, s in runtime["servers"].items():
        DATA["servers"][sid] = {
            "owner": s["owner"], "name": s["name"], "type": s["type"],
            "port": s.get("port"), "path": s["path"], "status": s["status"]
        }
    save_data()

def _load_servers():
    for sid, meta in DATA.get("servers", {}).items():
        if not all(k in meta for k in ["owner", "name", "type", "path"]):
            continue
        if not Path(meta["path"]).exists():
            continue
        runtime["servers"][sid] = {
            "id": sid, "owner": meta["owner"], "name": meta["name"],
            "type": meta["type"], "port": meta.get("port"),
            "process": None, "tunnel_proc": None,
            "url": None, "status": "stopped",
            "path": meta["path"]
        }
    ports = [int(s.get("port", 0)) for s in runtime["servers"].values() if s.get("port")]
    runtime["next_port"] = max(ports) + 1 if ports else DEFAULT_APP_PORT

    # Auto-start running servers
    for sid, meta in list(DATA.get("servers", {}).items()):
        if meta.get("status") == "running":
            start_server(sid)

_load_servers()

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def current_user():      return session.get("user")
def require_login():     return "user" in session
def user_dir(u):         return USERS_DIR / u
def server_dir(u, n):    return user_dir(u) / "servers" / n
def logs_path(u, n):     return server_dir(u, n) / "logs.txt"

def safe_join(base, *parts):
    p = base.joinpath(*parts).resolve()
    if str(p).startswith(str(base.resolve())): return p
    raise ValueError("Path escape")

def get_free_port():
    with PORT_LOCK:
        p = runtime["next_port"]
        runtime["next_port"] = p + 1
        return p

# -------------------------------------------------
# Process & Tunnel
# -------------------------------------------------
def _log_reader(proc, logf):
    try:
        with logf.open("a", encoding="utf-8", errors="ignore") as f:
            for line in iter(proc.stdout.readline, ""):
                if not line: break
                f.write(line); f.flush()
    except Exception as e:
        with logf.open("a") as f: f.write(f"[log error] {e}\n")

def start_server(sid):
    s = runtime["servers"].get(sid)
    if not s or s.get("process"): return False, "already running"

    spath = Path(s["path"])
    logf  = logs_path(s["owner"], s["name"])
    logf.parent.mkdir(parents=True, exist_ok=True)

    # ---- find entry file ----
    if s["type"] == "flask":
        entry = spath / "app.py"
        if not entry.exists():
            entry = spath / "server.py"
            if not entry.exists():
                pys = list(spath.glob("*.py"))
                entry = pys[0] if pys else None
        if not entry:
            logf.write_text("No .py file found\n")
            return False, "no entry file"
    else:   # python script
        entry = spath / "main.py"
        if not entry.exists():
            entry = spath / "server.py"
            if not entry.exists():
                pys = list(spath.glob("*.py"))
                entry = pys[0] if pys else None
        if not entry:
            logf.write_text("No .py file found\n")
            return False, "no entry file"

    # ---- start process ----
    port = get_free_port()
    s["port"] = port
    env = os.environ.copy()
    env["PORT"] = str(port)

    proc = subprocess.Popen(
        ["python3", str(entry)], cwd=str(spath),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env, text=True, bufsize=1
    )
    s["process"] = proc
    s["status"]  = "running"
    threading.Thread(target=_log_reader, args=(proc, logf), daemon=True).start()
    _persist_servers()

    # ---- AUTO START TUNNEL for Flask ----
    if s["type"] == "flask":
        threading.Thread(target=_start_tunnel, args=(sid, port), daemon=True).start()

    return True, "started"

def stop_server(sid):
    s = runtime["servers"].get(sid)
    if not s: return False, "not found"
    proc = s.get("process")
    if not proc:
        s["status"] = "stopped"
        _persist_servers()
        return True, "already stopped"

    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill()
    s["process"] = None
    s["status"]  = "stopped"

    # kill tunnel if exists
    tproc = s.get("tunnel_proc")
    if tproc:
        try: tproc.terminate()
        except Exception: pass
        s["tunnel_proc"] = None
    s["url"] = None
    _persist_servers()
    return True, "stopped"

def _start_tunnel(sid, port):
    s = runtime["servers"].get(sid)
    if not s: return
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        s["tunnel_proc"] = proc
        logf = logs_path(s["owner"], s["name"])

        # capture the public URL
        for line in proc.stdout:
            m = re.search(r"https?://[^\s]+\.trycloudflare\.com", line)
            if m:
                url = m.group(0)
                s["url"] = url
                with logf.open("a") as f: f.write(f"[tunnel] {url}\n")
                break

        # keep logging the rest
        with logf.open("a") as f:
            for line in proc.stdout:
                f.write(f"[tunnel] {line}")
    except Exception as e:
        with logs_path(s["owner"], s["name"]).open("a") as f:
            f.write(f"[tunnel error] {e}\n")

# -------------------------------------------------
# Server CRUD
# -------------------------------------------------
def create_server(owner, name, stype, code=""):
    name = secure_filename(name)
    sid  = uuid.uuid4().hex[:12]
    sdir = server_dir(owner, name)
    sdir.mkdir(parents=True, exist_ok=True)

    entry = sdir / ("app.py" if stype == "flask" else "main.py")
    entry.write_text(code or "# your code here\n", encoding="utf-8")

    logs_path(owner, name).write_text(f"--- created {name} at {time.ctime()} ---\n")

    runtime["servers"][sid] = {
        "id": sid, "owner": owner, "name": name, "type": stype,
        "port": None, "process": None, "tunnel_proc": None,
        "url": None, "status": "stopped", "path": str(sdir)
    }
    _persist_servers()
    return sid

def delete_server(sid):
    s = runtime["servers"].get(sid)
    if not s: return False, "not found"
    stop_server(sid)
    try: shutil.rmtree(s["path"])
    except Exception: pass
    runtime["servers"].pop(sid, None)
    DATA["servers"].pop(sid, None)
    save_data()
    return True, "deleted"

# -------------------------------------------------
# UI Templates
# -------------------------------------------------
INDEX_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CloudHost Mini</title>
<style>
  body{font-family:sans-serif;background:#f4f4f9;color:#222;margin:0;padding:1rem;}
  .container{max-width:960px;margin:auto;}
  .card{background:#fff;padding:1rem;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.1);margin-bottom:1rem;}
  input,select,button,textarea{font:inherit;margin:0.2rem 0;padding:0.4rem;}
  button{cursor:pointer;background:#0066cc;color:#fff;border:none;border-radius:4px;transition:background 0.3s;}
  button:hover{background:#0055aa;}
  button.stop{background:#c33;}
  button.stop:hover{background:#b22;}
  .link{color:#0066cc;text-decoration:underline;}
  .log{font-family:monospace;background:#222;color:#0f0;padding:0.5rem;overflow:auto;max-height:120px;font-size:0.9rem;}
  .row{display:flex;gap:0.5rem;align-items:center;}
  .server-item{opacity:0;animation:fadeIn 0.5s forwards;}
  @keyframes fadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
  .loader{display:none;border:4px solid #f3f3f3;border-top:4px solid #3498db;border-radius:50%;width:20px;height:20px;animation:spin 1s linear infinite;}
  @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
  .website-btn{background:#28a745;color:white;padding:0.4rem 0.8rem;border-radius:4px;text-decoration:none;transition:background 0.3s;}
  .website-btn:hover{background:#218838;}
</style></head><body>
<div class="container">
<h1>CloudHost Mini</h1>
{% if user %}
  <p>Signed in: <b>{{user}}</b> | <a href="/logout">Logout</a></p>
{% else %}
  <p><a href="/login">Login</a> • <a href="/register">Register</a></p>
{% endif %}

{% if not user %}
<div class="card"><p>Welcome – create a free account and host Python/Flask apps.</p></div>
{% else %}

<div class="card"><h2>Create Server</h2>
<form method="post" action="/create" enctype="multipart/form-data">
  <input name="name" placeholder="Server name" required>
  <select name="type"><option value="flask">Flask (auto-tunnel)</option><option value="python">Python script</option></select><br>
  <input type="file" name="zipfile"><br>
  <textarea name="code" rows="6" cols="60" placeholder="Paste code (optional)"></textarea><br>
  <button type="submit">Create</button>
</form>
</div>

<div class="card"><h2>Your Servers</h2>
{% for s in servers %}
<div class="server-item" style="border-bottom:1px solid #ddd;padding:0.5rem 0;animation-delay:{{loop.index0 * 0.1}}s;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <b>{{s.name}}</b> <small>({{s.type}})</small><br>
      {% if s.port %} local port {{s.port}}{% endif %}
      {% if s.url %} <a href="{{s.url}}" class="website-btn" target="_blank">Website</a>{% endif %}
    </div>
    <div class="row">
      <div id="loader-{{s.id}}" class="loader"></div>
      {% if s.status == 'running' %}
        <button class="stop" onclick="toggle('{{s.id}}','stop')">Stop</button>
      {% else %}
        <button onclick="toggle('{{s.id}}','start')">Play</button>
      {% endif %}
      <button style="background:#555;" onclick="delSrv('{{s.id}}')">Delete</button>
    </div>
  </div>
  <div style="margin-top:0.5rem;">
    <div class="log" id="log-{{s.id}}">{{s.log_preview}}</div>
    <div style="margin-top:0.3rem;">
      <a class="link" href="/files/{{s.id}}">File Manager</a> |
      <a class="link" href="/editor/{{s.id}}">Edit Code</a>
    </div>
  </div>
</div>
{% else %}
<p>No servers yet.</p>
{% endfor %}
</div>

<script>
function api(p,m='POST',b=null){return fetch(p,{method:m,body:b}).then(r=>r.json());}
function toggle(id,act){
  const btn=document.querySelector(`button[onclick*="toggle('${id}','${act}')"]`);
  const loader=document.getElementById(`loader-${id}`);
  btn.disabled=true; loader.style.display='block';
  api('/api/server/'+id+'/'+act).then(d=>{
    if(d.ok) location.reload();
    else {btn.disabled=false; loader.style.display='none';}
  });
}
function delSrv(id){if(confirm('Delete?'))api('/api/server/'+id+'/delete').then(d=>location.reload());}
function refreshLogs(){
  document.querySelectorAll('[id^="log-"]').forEach(el=>{
    const sid=el.id.split('-')[1];
    fetch('/api/server/'+sid+'/logs').then(r=>r.text()).then(txt=>{
      el.innerText=txt.split('\\n').slice(-30).join('\\n');
    });
  });
}
setInterval(refreshLogs,3000); refreshLogs();
</script>

{% endif %}
</div></body></html>"""

LOGIN_HTML = """<!DOCTYPE html><html><head><title>Login</title></head><body>
<h2>Login</h2><form method=post>
<input name=username placeholder=Username required><br>
<input name=password type=password placeholder=Password required><br>
<button>Login</button>
</form><p>No account? <a href="/register">Register</a></p></body></html>"""

REGISTER_HTML = """<!DOCTYPE html><html><head><title>Register</title></head><body>
<h2>Register</h2><form method=post>
<input name=username placeholder=Username required><br>
<input name=password type=password placeholder=Password required><br>
<button>Create account</button>
</form><p>Have an account? <a href="/login">Login</a></p></body></html>"""

FILE_MGR = """<!DOCTYPE html><html><head><title>File Manager – {{server.name}}</title>
<style>
  body{font-family:sans-serif;}
  .file-list{list-style:none;padding:0;}
  .file-item{margin-bottom:0.5rem;}
</style>
</head><body>
<h2>File Manager – {{user}} / {{server.name}}</h2>
<a href="/">Back</a><hr>
<ul class="file-list">
{% for f in files %}
<li class="file-item">
  {% if f.is_dir %}
    📁 <b>{{f.name}}</b> – <a href="/files/{{sid}}/{{f.rel}}/">Open</a>
  {% else %}
    📄 {{f.name}} – <a href="/files/{{sid}}/download/{{f.rel}}">Download</a> |
    <a href="/files/{{sid}}/edit/{{f.rel}}">Edit</a> |
    <a href="/files/{{sid}}/delete/{{f.rel}}" onclick="return confirm('Delete?')">Delete</a>
  {% endif %}
</li>
{% endfor %}
</ul>
<h4>Upload</h4>
<form method=post enctype=multipart/form-data action="/files/{{sid}}/upload">
  <input type=file name=file><button>Upload</button>
</form>
<h4>Create folder</h4>
<form method=post action="/files/{{sid}}/mkdir">
  <input name=folder placeholder="folder name"><button>Create</button>
</form>
<script>
// Auto-refresh file list every 5s
setInterval(()=>location.reload(),5000);
</script>
</body></html>"""

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/")
def index():
    user = current_user()
    servers = []
    if user:
        for sid, s in runtime["servers"].items():
            if s["owner"] != user: continue
            lp = ""
            p = logs_path(user, s["name"])
            if p.exists():
                try:
                    lp = "\n".join(p.read_text(errors="ignore").splitlines()[-60:])
                except Exception: lp = "[log error]"
            servers.append({
                "id": sid, "name": s["name"], "type": s["type"],
                "status": s["status"], "port": s.get("port"),
                "url": s.get("url"), "log_preview": lp
            })
    return render_template_string(INDEX_HTML, user=user, servers=servers)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        if u not in DATA.get("users",{}): return "invalid",400
        if not check_password_hash(DATA["users"][u],p): return "invalid",400
        session["user"]=u
        return redirect(url_for("index"))
    return render_template_string(LOGIN_HTML)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        if not u or not p: return "required",400
        if u in DATA.get("users",{}): return "exists",400
        DATA.setdefault("users",{})[u] = generate_password_hash(p)
        user_dir(u).mkdir(parents=True, exist_ok=True)
        save_data()
        return redirect(url_for("login"))
    return render_template_string(REGISTER_HTML)

@app.route("/logout", methods=["GET","POST"])
def logout():
    session.pop("user",None)
    return redirect(url_for("index"))

@app.route("/create", methods=["POST"])
def create():
    if not require_login(): return redirect(url_for("login"))
    user = current_user()
    name = request.form.get("name","").strip()
    typ  = request.form.get("type","python")
    code = request.form.get("code","").strip()
    zipf = request.files.get("zipfile")
    if not name: return "name required",400
    sid = create_server(user, name, typ, code)
    sdir = Path(runtime["servers"][sid]["path"])
    if zipf and zipf.filename:
        import zipfile
        tmp = sdir / "upload.zip"
        zipf.save(tmp)
        try: zipfile.ZipFile(tmp).extractall(sdir)
        finally: tmp.unlink(missing_ok=True)
    return redirect(url_for("index"))

# ----- API -----
@app.route("/api/server/<sid>/start", methods=["POST"])
def api_start(sid):
    if not require_login(): return jsonify({"ok":False,"error":"auth"}),403
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return jsonify({"ok":False,"error":"forbidden"}),403
    ok,msg = start_server(sid)
    return jsonify({"ok":ok,"msg":msg})

@app.route("/api/server/<sid>/stop", methods=["POST"])
def api_stop(sid):
    if not require_login(): return jsonify({"ok":False,"error":"auth"}),403
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return jsonify({"ok":False,"error":"forbidden"}),403
    ok,msg = stop_server(sid)
    return jsonify({"ok":ok,"msg":msg})

@app.route("/api/server/<sid>/delete", methods=["POST"])
def api_delete(sid):
    if not require_login(): return jsonify({"ok":False,"error":"auth"}),403
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return jsonify({"ok":False,"error":"forbidden"}),403
    ok,msg = delete_server(sid)
    return jsonify({"ok":ok,"msg":msg})

@app.route("/api/server/<sid>/logs")
def api_logs(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "forbidden",403
    p = logs_path(s["owner"], s["name"])
    return p.read_text(errors="ignore") if p.exists() else ""

# ----- File manager -----
@app.route("/files/<sid>/", defaults={"path":""})
@app.route("/files/<sid>/<path:path>")
def browse(sid, path):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "unauthorized",403
    base = Path(s["path"])
    target = safe_join(base, path) if path else base
    if not target.exists(): return "not found",404
    files = []
    for child in sorted(target.iterdir(), key=lambda p:(not p.is_dir(), p.name.lower())):
        files.append({"name":child.name, "is_dir":child.is_dir(),
                      "rel":str(child.relative_to(base))})
    return render_template_string(FILE_MGR, user=current_user(), server=s, files=files, sid=sid)

@app.route("/files/<sid>/upload", methods=["POST"])
def upload(sid):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    f = request.files.get("file")
    if not f: return "no file",400
    dest = Path(s["path"]) / secure_filename(f.filename)
    f.save(dest)
    return redirect(url_for("browse", sid=sid, path=request.args.get("path", "")))

@app.route("/files/<sid>/download/<path:path>")
def download(sid, path):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    target = safe_join(Path(s["path"]), path)
    if not target.is_file(): return "not found",404
    return send_file(str(target), as_attachment=True)

@app.route("/files/<sid>/edit/<path:path>", methods=["GET","POST"])
def edit(sid, path):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    target = safe_join(Path(s["path"]), path)
    if request.method=="POST":
        target.write_text(request.form.get("content",""), encoding="utf-8")
        return redirect(url_for("browse", sid=sid, path=request.args.get("path", "")))
    return render_template_string(
        "<h2>Editing {{path}}</h2><form method=post><textarea name=content rows=25 cols=80>"
        "{{content}}</textarea><br><button>Save</button></form><a href='/files/{{sid}}'>Back</a>",
        path=path, content=target.read_text(encoding="utf-8", errors="ignore"), sid=sid)

@app.route("/files/<sid>/delete/<path:path>")
def delete(sid, path):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    target = safe_join(Path(s["path"]), path)
    if target.is_dir(): shutil.rmtree(target)
    else: target.unlink(missing_ok=True)
    return redirect(url_for("browse", sid=sid, path=request.args.get("path", "")))

@app.route("/files/<sid>/mkdir", methods=["POST"])
def mkdir(sid):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    folder = request.form.get("folder","").strip()
    if not folder: return "bad",400
    safe_join(Path(s["path"]), folder).mkdir(parents=True, exist_ok=True)
    return redirect(url_for("browse", sid=sid, path=request.args.get("path", "")))

# ----- Quick editor -----
@app.route("/editor/<sid>", methods=["GET","POST"])
def editor(sid):
    if not require_login(): return redirect(url_for("login"))
    s = runtime["servers"].get(sid)
    if not s or s["owner"]!=current_user(): return "nope",403
    base = Path(s["path"])
    candidates = ["app.py","main.py","server.py"]
    target = next((base/c for c in candidates if (base/c).exists()), None)
    if not target:
        pys = list(base.glob("*.py"))
        target = pys[0] if pys else None
    if not target:
        target = base / ("app.py" if s["type"]=="flask" else "main.py")
        target.write_text("# your code here\n")
    if request.method=="POST":
        target.write_text(request.form.get("content",""), encoding="utf-8")
        return redirect(url_for("index"))
    return render_template_string(
        "<h2>Editing {{target.name}}</h2><form method=post><textarea name=content rows=30 cols=100>"
        "{{content}}</textarea><br><button>Save</button></form><a href='/'>Back</a>",
        target=target, content=target.read_text(encoding="utf-8", errors="ignore"))

# ----- Demo admin -----
if "admin" not in DATA.get("users", {}):
    DATA.setdefault("users", {})["admin"] = generate_password_hash("admin")
    save_data()

# -------------------------------------------------
# Run
# -------------------------------------------------
if __name__ == "__main__":
    print("CloudHost Mini – http://0.0.0.0:8000")
    print("Flask servers get an auto-tunnel to *.trycloudflare.com")
    app.run(host="0.0.0.0", port=8000, debug=False)