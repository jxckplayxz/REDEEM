from flask import Flask, request, session, redirect, url_for, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
import os
import time

app = Flask(__name__)
app.secret_key = 'super-secret-key'

# Upload config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Main executor code and key system code
main_code = '''loadstring(game:HttpGet("https://voidy-script.neocities.org/JujutsuInfinite"))()'''
ks_code = '''loadstring(game:HttpGet("https://vertex-z.onrender.com/main?key=skidder"))()'''
za_code = '''loadstring(game:HttpGet("https://voidy-script.neocities.org/script"))() -- btw this is just the loader so its useless :)'''
error_code = '''Bro why you tryna see source you a skid or sum? oh yea btw join our server --> https://discord.gg/zMPJxeMMrK'''

# HTML templates
home_page = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/png" href="https://voidy-script.neocities.org/IMG_3803.jpeg">
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta property="og:title" content="Vertex Z Script - #1 Roblox Script for Steal a Brainrot" />
  <meta property="og:description" content="Trusted, OP, and lightning-fast. Dominate in Steal a Brainrot with Vertex Z Script." />
  <meta property="og:image" content="https://voidy-script.neocities.org/IMG_3803.jpeg" />
  <meta property="og:url" content="https://vertex-z.onrender.com/" />
  <meta name="theme-color" content="#ff4d4f">
  <title>Vertex Z Script</title>
  <meta name="robots" content="index, follow">
  <meta name="description" content="Vertex Z - #1 Roblox script for Steal a Brainrot. OP features, auto-hit, music, and more. Trusted and powerful.">
  <meta name="keywords" content="Vertex Z, Roblox script, Steal a Brainrot, Roblox executor, auto-hit, brainrot script, roblox cheats">

  <meta name="google-site-verification" content="aTXgP6WHLWMaIBkTMUiCuD2kXmdEH3gMxqeOsHQeXq0" />
</head>


  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet" />
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: 'Inter', sans-serif;
      background: linear-gradient(to right, #fff, #fff3f3);
      color: #0f0f0f;
      overflow-x: hidden;
      transition: background 0.3s ease, color 0.3s ease;
    }
    body.dark {
      background: linear-gradient(to right, #0f0f0f, #1a1a1a);
      color: #eee;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      align-items: center;
      padding: 20px 20px;
      background-color: #fff;
      transition: background-color 0.3s ease;
    }
    body.dark header {
      background-color: #121212;
    }
    .logo {
      font-size: 24px;
      font-weight: 900;
      color: #0f0f0f;
      margin-right: auto;
      transition: color 0.3s ease;
    }
    body.dark .logo {
      color: #eee;
    }
    .logo span {
      color: #ff4d4f;
    }
    nav {
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      align-items: center;
    }
    nav a {
      text-decoration: none;
      color: #0f0f0f;
      font-weight: 500;
      transition: color 0.3s ease;
    }
    body.dark nav a {
      color: #eee;
    }
    .cta-btn {
      background: #ff4d4f;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      transition: transform 0.2s ease, background-color 0.3s ease;
      margin-left: 10px;
    }
    .cta-btn:hover {
      transform: scale(1.05);
      background-color: #e04343;
    }
    body.dark .cta-btn {
      background: #ff6b6b;
    }
    body.dark .cta-btn:hover {
      background-color: #ff4d4d;
    }

    /* Dropdown styling */
    .theme-select {
      padding: 10px 15px;
      border-radius: 6px;
      border: 1px solid #ff4d4f;
      background: white;
      color: #ff4d4f;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.3s ease, color 0.3s ease;
      margin-left: 10px;
    }
    body.dark .theme-select {
      background: #1e1e1e;
      color: #ff6b6b;
      border-color: #ff6b6b;
    }
    .hero {
      text-align: center;
      padding: 80px 20px 60px;
      animation: fadeIn 1.2s ease;
    }
    .badge {
      background: #ffeaea;
      color: #ff4d4f;
      padding: 6px 14px;
      border-radius: 20px;
      display: inline-block;
      font-weight: 600;
      margin-bottom: 20px;
      animation: slideDown 0.8s ease;
    }
    body.dark .badge {
      background: #3a1a1a;
      color: #ff6b6b;
    }
    .hero h1 {
      font-size: 2.8em;
      font-weight: 900;
      margin: 10px 0;
    }
    .hero p {
      max-width: 600px;
      margin: 0 auto 30px;
      font-size: 18px;
      color: #555;
      transition: color 0.3s ease;
    }
    body.dark .hero p {
      color: #bbb;
    }
    .button-group {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 15px;
    }
    .features {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      padding: 40px 20px;
      gap: 20px;
    }
    .feature-box {
      background: white;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
      text-align: center;
      flex: 1 1 260px;
      animation: fadeInUp 1s ease;
      transition: background 0.3s ease, color 0.3s ease;
    }
    body.dark .feature-box {
      background: #222;
      color: #ddd;
      box-shadow: 0 4px 15px rgba(0, 255, 255, 0.15);
    }
    .feature-box h3 {
      margin-bottom: 10px;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (max-width: 768px) {
      .hero h1 {
        font-size: 2.2em;
      }
      nav {
        justify-content: center;
        margin-top: 10px;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="logo">Vertex<span>Z</span></div>
    <nav>
      <a href="# "> </a>
      <a href="# ">V-Z</a>
      <a href="# "> </a>
    </nav>
    <button class="cta-btn" onclick="window.open('https://discord.com/invite/hCTCQwPKd3', '_blank')">Join Discord</button>
    <select class="theme-select" id="themeSelect" aria-label="Select Theme">
      <option value="system">System</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </header>

  <section class="hero">
    <div class="badge">⚡ The Ultimate Brainrot Script</div>
    <h1>The #1 Script<br />For Steal a Brainrot</h1>
    <p>Trusted by many. Lightning fast. Built for domination. 24/7 uptime and updates.</p>
    <div class="button-group">
      <button class="cta-btn" onclick="document.getElementById('features').scrollIntoView({behavior: 'smooth'})">View Features</button>
      <button class="cta-btn" style="background: white; color: #ff4d4f; border: 2px solid #ff4d4f" onclick="window.open('https://discord.gg/hCTCQwPKd3', '_blank')">Join Discord</button>
      <button class="cta-btn" onclick="window.open('https://vertex-z.onrender.com/script', '_blank')">Get Script</button>
    </div>
  </section>

  <section class="features" id="features">
    <div class="feature-box">
      <h3>⚔️ OP Performance</h3>
      <p>auto hit, music player,speed boost, and more.</p>
    </div>
    <div class="feature-box">
      <h3>⚡ Instant Execution</h3>
      <p>Run our script and dominate in seconds.</p>
    </div>
    <div class="feature-box">
      <h3>✅ Trusted by many+</h3>
      <p>Community-approved and always improving.</p>
    </div>
  </section>

  <script>
    const themeSelect = document.getElementById('themeSelect');

    function applyTheme(theme) {
      if (theme === 'light') {
        document.body.classList.remove('dark');
        setMetaThemeColor('#ff4d4f');
      } else if (theme === 'dark') {
        document.body.classList.add('dark');
        setMetaThemeColor('#222222');
      } else if (theme === 'system') {
        // Match system preference
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDark) {
          document.body.classList.add('dark');
          setMetaThemeColor('#222222');
        } else {
          document.body.classList.remove('dark');
          setMetaThemeColor('#ff4d4f');
        }
      }
      // Save preference
      localStorage.setItem('themePreference', theme);
    }

    function setMetaThemeColor(color) {
      let meta = document.querySelector('meta[name="theme-color"]');
      if (!meta) {
        meta = document.createElement('meta');
        meta.name = "theme-color";
        document.head.appendChild(meta);
      }
      meta.content = color;
    }

    // Load saved preference or default to system
    const savedTheme = localStorage.getItem('themePreference') || 'system';
    themeSelect.value = savedTheme;
    applyTheme(savedTheme);

    // Listen for changes in dropdown
    themeSelect.addEventListener('change', (e) => {
      applyTheme(e.target.value);
    });

    // Listen for system theme changes if system is selected
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (themeSelect.value === 'system') {
        applyTheme('system');
      }
    });
  </script>
</body>
</html>

'''
 
locked_page = '''...'''  # keep your current locked_page string

@app.route('/')
def home():
    return render_template_string(home_page)

@app.route('/verify', methods=['POST'])
def verify():
    key = request.form.get('key')
    if key == "voidy-skid-off":
        session['verified'] = True
        return redirect('/212')
    return redirect('/')

def is_executor():
    user_agent = request.headers.get('User-Agent', '').lower()
    executor_keywords = ['synapse', 'Delta IOS/2.0', 'krnl', 'fluxus', 'executor', 'Delta Android/2.0']
    return any(exec in user_agent for exec in executor_keywords)

@app.route('/212')
def hidden():
    query_key = request.args.get("key", "")
    is_exec = is_executor()
    verified = session.get('verified')

    if not verified and not is_exec:
        return redirect('/')

    if is_exec:
        if query_key == "skidder":
            return render_template_string(locked_page, code=main_code, can_see_code=True)
        else:
            return render_template_string(locked_page, code="", can_see_code=False)

    return render_template_string(locked_page, code="", can_see_code=False)

@app.route('/script')
def execute():
    script_code = f'loadstring(game:HttpGet("https://{request.host}/error?key=skidder"))()'
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Vertex Z Script</title>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://vertex-z.onrender.com/</loc>
    <lastmod>2025-08-04</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://vertex-z.onrender.com/script</loc>
    <lastmod>2025-08-04</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
    <link rel="icon" type="image/png" href="favicon.png" />
    <style>
        body {
            background: radial-gradient(circle at center, #0f0f0f 0%, #1a1a1a 100%);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }
        .container {
            max-width: 800px;
            margin: 60px auto;
            padding: 20px;
            text-align: center;
        }
        h1 {
            font-size: 2.5em;
            color: #7f5af0;
            margin-bottom: 0.2em;
        }
        p {
            font-size: 1.2em;
            margin-bottom: 2em;
            color: #ccc;
        }
        .button {
            background-color: #7f5af0;
            color: white;
            padding: 12px 24px;
            margin: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .button:hover {
            background-color: #9c7ff0;
            transform: scale(1.05);
        }
        .top-right {
            position: absolute;
            top: 15px;
            right: 15px;
        }

        /* Reviews Section Styles */
        .reviews-section {
            margin-top: 40px;
            text-align: left;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
        }
        .reviews-title {
            font-size: 1.8em;
            color: #7f5af0;
            margin-bottom: 20px;
            font-weight: 600;
            text-align: center;
        }
        .review-item {
            background-color: #1e1e1e;
            border: 1px solid #2a2a2a;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .review-user {
            font-weight: bold;
            color: #7f5af0;
            margin-bottom: 8px;
        }
        .review-text {
            font-size: 1em;
            color: #ccc;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 2em;
            }
            .button {
                padding: 10px 20px;
                font-size: 0.9em;
            }
        }
        #maintenanceOverlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 15, 15, 0.95);
      color: #ff4d4f;
      font-family: 'Inter', sans-serif;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      font-size: 1.8rem;
      text-align: center;
      padding: 20px;
      user-select: none;
    }
    body.no-scroll {
      overflow: hidden;
    }
    </style>
</head>
<body>
    <a href="/" class="button top-right">Go Back</a>
    <div class="container">
        <h1>Vertex Z Script</h1>
        <p>The #1 Roblox script for Steal a Brainrot. Trusted, powerful, and optimized for domination.</p>
        <button class="button" onclick="copyScript()">Get Script</button>

        <div class="reviews-section">
            <div class="reviews-title">💬 User Reviews</div>
            <div class="review-list" id="reviewContainer"></div>
        </div>
    </div>

    <script>
        const reviews = [
            { user: "Lilbabby87", text: "10/10 best script known to man and it get better and better every update" },
            { user: "manman01901", text: "1of the best script I ever used!" },
            { user: "elitelyex", text: "really recommend, i like to play music while playing." },
            { user: "thegrinch04616", text: "The script is insanely good in sab for a free script! THERES also other games that i have yet to try." },
        ];

        const container = document.getElementById("reviewContainer");
        reviews.forEach(review => {
            const div = document.createElement("div");
            div.className = "review-item";

            const user = document.createElement("div");
            user.className = "review-user";
            user.innerText = review.user;

            const text = document.createElement("div");
            text.className = "review-text";
            text.innerText = review.text;

            div.appendChild(user);
            div.appendChild(text);
            container.appendChild(div);
        });

        function copyScript() {
            const scriptText = `loadstring(game:HttpGet("https://{request.host}/error?key=skidder"))()
`;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(scriptText).then(() => {
                    alert('Script copied!');
                }).catch(err => {
                    alert('Failed to copy script');
                    console.error(err);
                });
            } else {
                const textArea = document.createElement('textarea');
                textArea.value = scriptText;
                document.body.appendChild(textArea);
                textArea.select();
                try {
                    document.execCommand('copy');
                    alert('Script copied!');
                } catch (err) {
                    alert('Failed to copy script');
                    console.error(err);
                }
                document.body.removeChild(textArea);
            }
        }
    </script>
</body>
</html>

'''


executed_keys = {}

@app.route('/track', methods=['POST'])
def track():
    key = request.form.get("key", "")
    executed_keys[key] = time.time()
    return "Tracked", 200

@app.route('/raw')
def raw():
    key = request.args.get("key", "")
    last_exec = executed_keys.get(key)

    if last_exec and time.time() - last_exec < 10:
        return ks_code, 200, {'Content-Type': 'text/plain'}
    else:
        return error_code, 200, {'Content-Type': 'text/plain'}

@app.route('/error')
def error():
    if is_executor() and request.args.get("key") == "skidder":
        return za_code, 200, {'Content-Type': 'text/plain'}
    return "Error page has been deleted or moved", 403

@app.route('/main')
def main():
    if is_executor() and request.args.get("key") == "skidder":
        return main_code, 200, {'Content-Type': 'text/plain'}
    return "Unauthorized", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
