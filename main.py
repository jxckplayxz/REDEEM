from flask import Flask, session, request, redirect, url_for, render_template_string
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed for sessions

VALID_KEY = "MYSECRETKEY123"

landing_html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Vertex Z - Protected App</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  html, body { margin:0; height:100%; background:#111; color:white; font-family:sans-serif; }
  header { text-align:center; padding:20px; font-size:2rem; background:rgba(255,255,255,0.05); }
  .frame-wrap { display:flex; justify-content:center; align-items:center; height:calc(100% - 80px); }
  iframe { width:1000px; height:700px; border:0; border-radius:12px; box-shadow:0 8px 30px rgba(0,0,0,0.7); }
</style>
<script>
  document.addEventListener('contextmenu', event => event.preventDefault());
  document.onkeydown = e => {
    if (e.keyCode == 123 || (e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0))) return false;
  };
</script>
</head>
<body>
<header>Vertex Z - Protected App</header>
<div class="frame-wrap">
  <iframe src="{{ iframe_url }}"></iframe>
</div>
</body>
</html>
"""

key_form_html = """
<!doctype html>
<html>
<head><title>Vertex Z - Key Required</title></head>
<body style="background:#111; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
<h1>Enter Access Key</h1>
<form method="POST">
  <input name="key" type="password" placeholder="Enter Key" style="padding:10px;">
  <button type="submit" style="padding:10px;">Unlock</button>
</form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form.get("key") == VALID_KEY:
            session["validated"] = True
            return redirect(url_for("landing"))
    return render_template_string(key_form_html)

@app.route("/landing")
def landing():
    if not session.get("validated"):
        return redirect(url_for("home"))
    return render_template_string(landing_html, iframe_url="https://loot-link.com/s?jPAaJ4C1")

if __name__ == "__main__":
    app.run(debug=False)
