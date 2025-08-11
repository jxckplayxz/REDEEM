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

# Captcha form
key_form_html = """
<!doctype html>
<html>
<head>
<title>Vertex Z - Human Verification</title>
<style>
  body {
    background: #111;
    color: white;
    font-family: sans-serif;
    text-align: center;
    padding-top: 100px;
  }
  .captcha-box {
    margin-top: 20px;
    padding: 20px;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    width: 300px;
    margin-left: auto;
    margin-right: auto;
  }
  img {
    width: 80px;
    height: 80px;
    margin: 5px;
    cursor: pointer;
    border-radius: 6px;
    border: 2px solid transparent;
    transition: 0.3s;
  }
  img:hover {
    border: 2px solid #00f7ff;
  }
</style>
</head>
<body>

<h1>Human Verification</h1>
<p>Click the <strong>cat</strong> to continue:</p>
<div class="captcha-box">
  <form method="POST">
    <input type="hidden" name="correct" id="correctInput" value="false">
    <img src="https://placekitten.com/80/80" onclick="document.getElementById('correctInput').value='true'; this.closest('form').submit();">
    <img src="https://placebear.com/80/80" onclick="alert('Wrong image! Try again.')">
    <img src="https://placebeard.it/80x80" onclick="alert('Wrong image! Try again.')">
  </form>
</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form.get("correct") == "true":
            session["validated"] = True
            return redirect(url_for("getkey"))
    return render_template_string(key_form_html)

@app.route("/getkey")
def getkey():
    if not session.get("validated"):
        return redirect(url_for("home"))
    return render_template_string(landing_html, iframe_url="https://loot-link.com/s?jPAaJ4C1")

if __name__ == "__main__":
    app.run(debug=False)
