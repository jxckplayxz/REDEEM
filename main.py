from flask import Flask, session, redirect, url_for, render_template_string, request, make_response
import os, secrets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(16))

outer_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Landing - Protected App</title>
  <style>
    html,body{height:100%;margin:0;}
    .frame-wrap { width:100%; height:100vh; border:0; display:flex; align-items:center; justify-content:center; background:#111; }
    iframe { width: 1000px; height: 700px; border-radius:12px; border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 8px 30px rgba(0,0,0,0.7); }
  </style>
</head>
<body>
  <div class="frame-wrap">
    <iframe src="/content" sandbox="allow-scripts allow-same-origin"></iframe>
  </div>
</body>
</html>
"""

protected_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Protected UI</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root { --bg:#0e0f12; --fg:#e6eef8; --muted:#9aa7b7; }
    html,body{height:100%;margin:0;background:var(--bg);color:var(--fg);font-family:Inter,system-ui,Segoe UI,Roboto,Arial;}
    .app{padding:28px; max-width:900px; margin:24px auto; background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:12px; position:relative;}
    h1{margin:0 0 8px 0; font-weight:600;}
    p{color:var(--muted);margin-top:0;}
    * { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
    .block-overlay { position: absolute; inset:0; pointer-events:auto; }
    .msg { display:none; position:fixed; bottom:18px; right:18px; background:#222; color: #fff; padding:10px 14px; border-radius:8px; box-shadow:0 6px 20px rgba(0,0,0,0.6); }
    .msg.show { display:block; animation:fade 0.3s ease; }
    @keyframes fade { from {opacity:0; transform:translateY(6px)} to {opacity:1; transform:none} }
  </style>
</head>
<body>
  <div class="app" id="app">
    <h1>VZ</h1>
    <p>VZ.</p>
    <div style="margin-top:20px;">
      <button onclick="doAction()" style="padding:10px 14px;border-radius:8px;border:none;background:#3478f6;color:#fff;cursor:pointer;">Action</button>
    </div>
    <div class="block-overlay" id="blockOverlay" aria-hidden="true"></div>
    <div class="msg" id="msg">Oops — can't copy that.</div>
  </div>
  <script>
    (function(){
      document.addEventListener('contextmenu', function(e){ e.preventDefault(); showMsg(); });
      document.addEventListener('keydown', function(e){
        if ((e.ctrlKey || e.metaKey) && ['u','s','c'].includes(e.key.toLowerCase())) { e.preventDefault(); showMsg(); }
        if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i')) { e.preventDefault(); showMsg(); }
      });
      document.addEventListener('copy', function(e){ e.preventDefault(); showMsg(); });
      const msg = document.getElementById('msg');
      let msgTimer = null;
      function showMsg(){
        msg.classList.add('show');
        if (msgTimer) clearTimeout(msgTimer);
        msgTimer = setTimeout(()=> msg.classList.remove('show'), 2200);
      }
      let overlay = document.getElementById('blockOverlay');
      overlay.style.pointerEvents = 'auto';
      overlay.addEventListener('mousedown', function(e){ showMsg(); e.preventDefault(); });
      let devtoolsOpen = false;
      setInterval(function(){
        const widthThreshold = window.outerWidth - window.innerWidth > 160;
        const heightThreshold = window.outerHeight - window.innerHeight > 160;
        if (widthThreshold || heightThreshold) {
          if (!devtoolsOpen) { devtoolsOpen = true; showMsg(); }
        } else {
          devtoolsOpen = false;
        }
      }, 1000);
      window.doAction = function(){
        alert("Action executed.");
      };
    })();
  </script>
</body>
</html>
"""

# Oops page for unauthorized access
oops_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Access Denied</title>
  <style>
    body{font-family:Arial,Helvetica,sans-serif;background:#111;color:#eee;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
    .card{padding:28px;border-radius:12px;background:#151515;text-align:center;max-width:520px;}
    h1{margin:0 0 8px 0;} p{color:#9aa7b7;margin:0;}
  </style>
</head>
<body>
  <div class="card">
    <h1>Oops — can't show that</h1>
    <p>It looks like you tried to access this resource directly. Please open the page from the official site.</p>
  </div>
</body>
</html>
"""

@app.route("/")
def index():
    session['allowed'] = True
    return render_template_string(outer_html)

@app.route("/content")
def content():
    if not session.get('allowed'):
        return render_template_string(oops_html), 403
    resp = make_response(render_template_string(protected_html))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route("/clear")
def clear():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
