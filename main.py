from flask import Flask, session, request, redirect, url_for, render_template_string
import secrets
import random

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed for sessions

# Captcha image pools - tuples of (name, url)
captcha_images = [
    ("cat", "https://placekitten.com/80/80"),
    ("bear", "https://placebear.com/80/80"),
    ("beard", "https://placebeard.it/80x80"),
    ("fox", "https://randomfox.ca/images/1.jpg"),
    ("dog", "https://images.dog.ceo/breeds/hound-afghan/n02088094_1007.jpg"),
]

landing_html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Vertex Z - Protected App</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  html, body { margin:0; height:100%; background:#111; color:white; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  header { text-align:center; padding:20px; font-size:2.5rem; font-weight:700; background:rgba(255,255,255,0.07); letter-spacing: 2px; }
  .frame-wrap { display:flex; justify-content:center; align-items:center; height:calc(100% - 80px); }
  iframe { width:1000px; height:700px; border:0; border-radius:16px; box-shadow:0 12px 40px rgba(0,0,0,0.8); }
</style>
<script>
  document.addEventListener('contextmenu', e => e.preventDefault());
  document.onkeydown = e => {
    if(e.keyCode == 123 || (e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0))) return false;
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
<html lang="en">
<head>
<title>Vertex Z - Human Verification</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #eee;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    text-align: center;
    padding: 60px 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  h1 {
    font-weight: 800;
    font-size: 3rem;
    margin-bottom: 0.2em;
    letter-spacing: 1.5px;
  }
  p {
    font-size: 1.2rem;
    margin-bottom: 1.5em;
    color: #a1c4fd;
  }
  .captcha-box {
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 30px 20px;
    max-width: 360px;
    margin: 0 auto;
    box-shadow: 0 8px 30px rgba(0,0,0,0.7);
  }
  form {
    display: flex;
    justify-content: center;
    gap: 15px;
  }
  img {
    width: 90px;
    height: 90px;
    cursor: pointer;
    border-radius: 12px;
    border: 3px solid transparent;
    transition: border-color 0.3s ease;
  }
  img:hover {
    border-color: #00f7ff;
    transform: scale(1.05);
  }
  .error-msg {
    color: #ff6b6b;
    font-weight: 600;
    margin-top: 1em;
    height: 1.2em;
  }
  .footer {
    margin-top: 40px;
    font-size: 0.9rem;
    color: #7f8c8d;
  }
</style>
</head>
<body>

<h1>Human Verification</h1>
<p>Click the <strong>{{ correct_name }}</strong> to continue:</p>
<div class="captcha-box">
  <form method="POST" id="captchaForm">
    <input type="hidden" name="selected" id="selectedInput" value="">
    {% for name, url in images %}
    <img src="{{ url }}" alt="{{ name }}" data-name="{{ name }}">
    {% endfor %}
  </form>
  <div class="error-msg" id="errorMsg"></div>
</div>

<div class="footer">© 2025 Vertex Z</div>

<script>
  const form = document.getElementById('captchaForm');
  const selectedInput = document.getElementById('selectedInput');
  const errorMsg = document.getElementById('errorMsg');

  form.querySelectorAll('img').forEach(img => {
    img.addEventListener('click', () => {
      selectedInput.value = img.getAttribute('data-name');
      errorMsg.textContent = "";
      form.submit();
    });
  });
</script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        selected = request.form.get("selected", "")
        correct = session.get("captcha_correct")
        if selected == correct:
            session["validated"] = True
            # Clear captcha to prevent reuse
            session.pop("captcha_correct", None)
            return redirect(url_for("getkey"))
        else:
            # Wrong answer, reload with error message
            # We'll just reload the page with a new captcha below
            pass

    # Pick 3 random distinct images for captcha
    options = random.sample(captcha_images, 3)
    # Pick one as correct
    correct_image = random.choice(options)
    session["captcha_correct"] = correct_image[0]

    # Render captcha page with random images and correct name
    return render_template_string(key_form_html, images=options, correct_name=correct_image[0])

@app.route("/getkey")
def getkey():
    if not session.get("validated"):
        return redirect(url_for("home"))
    return render_template_string(landing_html, iframe_url="https://loot-link.com/s?jPAaJ4C1")

if __name__ == "__main__":
    app.run(debug=False)
