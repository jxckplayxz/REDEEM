from flask import Flask, session, request, redirect, url_for, render_template_string
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

landing_html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>V-Z</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  html, body {
    margin:0; height:100%; background:#111; color:white; font-family:sans-serif;
    -webkit-user-select:none; /* Disable text selection */
    -moz-user-select:none;
    -ms-user-select:none;
    user-select:none;
  }
  header { text-align:center; padding:20px; font-size:2rem; background:rgba(255,255,255,0.05); }
  .frame-wrap {
    display:flex; justify-content:center; align-items:center; height:calc(100% - 80px);
    position: relative;
  }
  iframe {
    width:1000px; height:700px; border:0; border-radius:12px; box-shadow:0 8px 30px rgba(0,0,0,0.7);
    pointer-events: auto;
  }
  /* Optional overlay to prevent clicks on iframe (comment out if annoying) */
  #overlay {
    position: absolute;
    top:0; left:0; width:1000px; height:700px;
    z-index: 10;
    /* background: rgba(0,0,0,0); transparent */
  }
</style>
<script>
  // Block right click
  document.addEventListener('contextmenu', event => event.preventDefault());

  // Block keys for DevTools, view source, save, print, etc
  document.onkeydown = function(e) {
    // F12
    if(e.keyCode == 123) return false;
    // Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C
    if(e.ctrlKey && e.shiftKey && (e.keyCode == 73 || e.keyCode == 74 || e.keyCode == 67)) return false;
    // Ctrl+U (view source), Ctrl+S (save), Ctrl+P (print), Ctrl+Shift+K
    if(e.ctrlKey && (e.keyCode == 85 || e.keyCode == 83 || e.keyCode == 80 || e.keyCode == 75)) return false;
  };
</script>
</head>
<body>
<header>V-Z</header>
<div class="frame-wrap">
  <iframe src="{{ iframe_url }}" sandbox="allow-scripts"></iframe>
  <!-- Optional overlay to block clicks on iframe -->
  <div id="overlay"></div>
</div>
</body>
</html>
"""

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
    -webkit-user-select:none;
    -moz-user-select:none;
    -ms-user-select:none;
    user-select:none;
  }
  .captcha-box {
    margin-top: 20px;
    padding: 20px;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    width: 320px;
    margin-left: auto;
    margin-right: auto;
  }
  #captcha-code {
    font-size: 28px;
    letter-spacing: 8px;
    font-family: monospace;
    user-select: none;
    margin-bottom: 20px;
  }
  input[type="text"] {
    width: 180px;
    font-size: 18px;
    padding: 6px 10px;
    border-radius: 5px;
    border: none;
    margin-bottom: 12px;
    text-align: center;
  }
  button {
    background: #00f7ff;
    border: none;
    color: black;
    font-weight: bold;
    padding: 8px 20px;
    border-radius: 5px;
    cursor: pointer;
    transition: 0.3s;
  }
  button:hover {
    background: #00b2bf;
  }
  .error {
    color: #ff5555;
    margin-top: 10px;
  }
  .success {
    color: #55ff55;
    margin-top: 10px;
  }
</style>
<script>
  // Block right click
  document.addEventListener('contextmenu', event => event.preventDefault());
  
  // Block DevTools and view source keys
  document.onkeydown = function(e) {
    if(e.keyCode == 123) return false;
    if(e.ctrlKey && e.shiftKey && (e.keyCode == 73 || e.keyCode == 74 || e.keyCode == 67)) return false;
    if(e.ctrlKey && (e.keyCode == 85 || e.keyCode == 83 || e.keyCode == 80 || e.keyCode == 75)) return false;
  };
</script>
</head>
<body>

<h1>Human Verification</h1>
<p>Type the characters you see below to continue:</p>

<div class="captcha-box">
  <div id="captcha-code">Loading...</div>
  <form id="captcha-form" autocomplete="off" method="POST">
    <input type="hidden" name="validated" id="validatedInput" value="false">
    <input type="text" id="captcha-input" placeholder="Type code here" required autofocus>
    <br>
    <button type="submit">Verify</button>
  </form>
  <div id="message"></div>
</div>

<script>
  const captchaCodeElem = document.getElementById('captcha-code');
  const captchaInput = document.getElementById('captcha-input');
  const captchaForm = document.getElementById('captcha-form');
  const messageElem = document.getElementById('message');
  const validatedInput = document.getElementById('validatedInput');

  let currentCode = '';

  function generateCode(length = 9) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for(let i = 0; i < length; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code.match(/.{1,3}/g).join(' ');
  }

  function normalizeCode(code) {
    return code.replace(/\s+/g, '');
  }

  function newCaptcha() {
    currentCode = generateCode();
    captchaCodeElem.textContent = currentCode;
    captchaInput.value = '';
    messageElem.textContent = '';
    validatedInput.value = 'false';
    captchaInput.focus();
  }

  captchaForm.addEventListener('submit', e => {
    e.preventDefault();
    const userInput = captchaInput.value.toUpperCase().replace(/\s+/g, '');
    if (userInput === normalizeCode(currentCode)) {
      messageElem.textContent = '✅ Verified! Redirecting...';
      messageElem.className = 'success';
      validatedInput.value = 'true';
      captchaForm.submit();
    } else {
      messageElem.textContent = '❌ Wrong code. Try again.';
      messageElem.className = 'error';
      newCaptcha();
    }
  });

  newCaptcha();
</script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if request.form.get("validated") == "true":
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
