# main.py — VIXN — REVAMPED UI (Home, Cart, Admin, Login) — fronts only, backend unchanged
from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vixn_2025_perfect"

PAYPAL_USERNAME = "ContentDeleted939"
ADMIN_USER = "Admin"
ADMIN_PASS = "admin12"

PRODUCTS_FILE = 'products.json'
PURCHASES_FILE = 'purchases.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure data files exist
for f in [PRODUCTS_FILE, PURCHASES_FILE]:
    if not os.path.exists(f):
        with open(f, 'w', encoding='utf-8') as fp:
            json.dump([], fp)

def read_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def write_products(data):
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def read_purchases():
    try:
        with open(PURCHASES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def write_purchases(data):
    with open(PURCHASES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def next_id():
    return max([p.get("id", 0) for p in read_products()], default=0) + 1

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/cart")
def cart_page():
    return render_template_string(CART_HTML)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["logged_in"] = True
        else:
            return render_template_string(LOGIN_HTML, error="Wrong credentials")
    if session.get("logged_in"):
        return render_template_string(ADMIN_HTML, products=read_products(), purchases=read_purchases())
    return render_template_string(LOGIN_HTML)

@app.route("/admin/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/admin")

@app.route("/api/products")
def api_products():
    return jsonify(read_products())

@app.route("/api/add_product", methods=["POST"])
@login_required
def add_product():
    try:
        data = request.form
        image = data.get("image", "").strip()
        if "image_file" in request.files and request.files["image_file"].filename:
            file = request.files["image_file"]
            fn = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, fn))
            image = url_for("uploaded_file", filename=fn)

        name = data.get("name", "").strip()
        price = data.get("price", "").strip()
        desc = data.get("description", "")

        if not name or not price:
            return jsonify({"ok": False, "error": "Name and price required"}), 400

        new_prod = {
            "id": next_id(),
            "name": name,
            "price": price,
            "image": image or "https://via.placeholder.com/320x180?text=No+Image",
            "description": desc
        }
        prods = read_products()
        prods.append(new_prod)
        write_products(prods)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/delete_product", methods=["POST"])
@login_required
def delete_product():
    try:
        pid = request.get_json().get("id")
        if pid is None:
            return jsonify({"ok": False, "error": "No ID"}), 400
        products = [p for p in read_products() if p["id"] != pid]
        write_products(products)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    cart = data.get("cart", [])
    if not email or not cart:
        return jsonify({"ok": False, "error": "Email & cart required"}), 400

    total = sum(float(i["price"]) * i["qty"] for i in cart)
    purchases = read_purchases()
    purchases.append({"timestamp": datetime.now().isoformat(), "email": email, "total": total, "items": cart})
    write_purchases(purchases)

    url = f"https://www.paypal.me/{PAYPAL_USERNAME}/{total}"
    return jsonify({"ok": True, "paypal_url": url})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================================
# UI Templates (revamped)
# ================================

HOME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN — Store</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" rel="stylesheet" />
<style>
:root{
  --bg:#071021;
  --card:#0f1724;
  --muted:#98a2b3;
  --text:#e6eef8;
  --glass: rgba(255,255,255,0.03);
  --accent1: #7b61ff;
  --accent2: #00d4ff;
  --radius:14px;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(180deg,#030416 0%,#071021 100%);color:var(--text)}
.container{max-width:1200px;margin:32px auto;padding:20px}
.header{display:flex;gap:16px;align-items:center;justify-content:space-between;margin-bottom:26px}
.brand{display:flex;gap:14px;align-items:center}
.logo{
  width:56px;height:56px;border-radius:12px;
  background:linear-gradient(135deg,var(--accent1),var(--accent2));
  display:grid;place-items:center;font-weight:800;color:#051422;font-size:22px;
  box-shadow: 0 6px 20px rgba(11,16,40,0.6);
}
.title h1{margin:0;font-size:20px;letter-spacing:0.3px}
.title p{margin:0;color:var(--muted);font-size:13px}
.actions{display:flex;gap:12px;align-items:center}
.icon-btn{
  display:inline-flex;gap:8px;align-items:center;padding:10px 14px;border-radius:12px;background:var(--glass);border:1px solid rgba(255,255,255,0.03);cursor:pointer;color:var(--text)
}
.search{
  display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:12px;background:#071730;border:1px solid rgba(255,255,255,0.02);
  min-width:280px;color:var(--muted)
}
.search input{background:transparent;border:none;outline:none;color:var(--text);width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}
.card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:var(--radius);overflow:hidden;border:1px solid rgba(255,255,255,0.03);transition:transform .25s, box-shadow .25s;display:flex;flex-direction:column}
.card:hover{transform:translateY(-8px);box-shadow:0 20px 40px rgba(3,6,20,0.6)}
.card-media{height:160px;background:#0b1320;display:grid;place-items:center}
.card-media img{width:100%;height:100%;object-fit:cover}
.card-body{padding:16px;display:flex;flex-direction:column;gap:8px}
.row{display:flex;justify-content:space-between;align-items:center}
.name{font-weight:700;font-size:15px}
.desc{font-size:13px;color:var(--muted);min-height:36px}
.price{font-weight:800;font-size:18px;background:linear-gradient(90deg,#a7ffeb,#7b61ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.btn{
  margin-top:8px;padding:10px;border-radius:10px;border:none;cursor:pointer;font-weight:700;background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#051422;
  box-shadow: 0 8px 30px rgba(123,97,255,0.12)
}
.empty{padding:40px;text-align:center;color:var(--muted);border-radius:12px;background:transparent}
.footer{margin-top:28px;text-align:center;color:var(--muted);font-size:13px}
.cart-fab{
  position:fixed;right:26px;bottom:26px;width:64px;height:64px;border-radius:18px;background:linear-gradient(135deg,var(--accent2),var(--accent1));display:grid;place-items:center;color:#051422;font-weight:800;box-shadow:0 14px 40px rgba(8,12,25,0.6);cursor:pointer;border:none
}
.badge{position:absolute;right:8px;top:6px;background:#ff4d6d;color:white;border-radius:999px;padding:4px 8px;font-weight:700;font-size:12px}
@media (max-width:720px){
  .search{min-width:120px}
  .logo{width:48px;height:48px}
}
.material{font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 48}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="brand">
      <div class="logo">V</div>
      <div class="title">
        <h1>VIXN</h1>
        <p>Curated digital goods — clean, fast, reliable</p>
      </div>
    </div>

    <div class="actions">
      <div class="search" title="Search products">
        <span class="material material-symbols-outlined">search</span>
        <input id="q" placeholder="Search products, e.g. scripts or assets">
      </div>
      <button class="icon-btn" onclick="location.href='/admin'">
        <span class="material material-symbols-outlined">admin_panel_settings</span>
        Admin
      </button>
      <button id="cartBtn" class="icon-btn" onclick="location.href='/cart'">
        <span style="position:relative;display:inline-block">
          <span class="material material-symbols-outlined">shopping_cart</span>
        </span>
        <span id="cartLabel">Cart</span>
      </button>
    </div>
  </div>

  <div id="list" class="grid"></div>

  <div id="empty" class="empty" style="display:none">
    <h3>No products yet</h3>
    <p>Admin can add products from the dashboard.</p>
  </div>

  <div class="footer">© VIXN — built with love • PayPal: <strong>paypal.me/{PAYPAL}</strong></div>
</div>

<button class="cart-fab" onclick="location.href='/cart'">
  <span class="material material-symbols-outlined">shopping_bag</span>
  <div id="count" class="badge" style="display:none">0</div>
</button>

<script>
const PAYPAL = "{{PAYPAL}}";
(function init(){
  // Fetch products and render
  fetch('/api/products').then(r=>r.json()).then(products=>{
    const list = document.getElementById('list');
    if(!products || products.length===0){ document.getElementById('empty').style.display='block'; return; }
    products.forEach(p=>{
      const card = document.createElement('div');
      card.className='card';
      card.innerHTML = `
        <div class="card-media"><img src="${p.image}" alt="${p.name}"></div>
        <div class="card-body">
          <div class="row"><div class="name">${escapeHtml(p.name)}</div><div class="price">$${Number(p.price).toFixed(2)}</div></div>
          <div class="desc">${escapeHtml(p.description || '')}</div>
          <button class="btn" onclick='addToCart(${JSON.stringify(p)})'>Add to cart • <span class="material material-symbols-outlined">add_shopping_cart</span></button>
        </div>`;
      list.appendChild(card);
    });
  }).catch(err=>{
    document.getElementById('empty').style.display='block';
  });

  // Search
  document.getElementById('q').addEventListener('input', (e)=>{
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.card').forEach(card=>{
      const txt = card.querySelector('.name').textContent.toLowerCase() + ' ' + card.querySelector('.desc').textContent.toLowerCase();
      card.style.display = txt.includes(q) ? '' : 'none';
    });
  });

  saveCart(getCart());
})();

function escapeHtml(s){ return String(s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]); }

function getCart(){ return JSON.parse(localStorage.getItem('cart')||'[]') }
function saveCart(c){ localStorage.setItem('cart', JSON.stringify(c)); const count = c.reduce((s,i)=>s+i.qty,0); const badge = document.getElementById('count'); if(count){ badge.style.display='block'; badge.textContent = count } else badge.style.display='none'; }

function addToCart(p){
  const c = getCart();
  const ex = c.find(i=>i.id===p.id);
  if(ex) ex.qty++; else c.push({...p, qty:1});
  saveCart(c);
  // small feedback
  const btn = event.currentTarget;
  if(btn){ btn.textContent = 'Added ✓'; setTimeout(()=>btn.textContent='Add to cart • \u{1F6D2}',900) }
}
</script>
</body>
</html>
""".replace("{PAYPAL}", PAYPAL_USERNAME)

CART_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN — Cart</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" rel="stylesheet" />
<style>
:root{
  --bg:#061024;--panel:#081226;--muted:#9aa3b2;--text:#e6eef8;--accent1:#7b61ff;--accent2:#00d4ff;--radius:12px;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(180deg,#030416 0%,#061024 100%);color:var(--text)}
.container{max-width:980px;margin:28px auto;padding:20px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.brand{display:flex;gap:12px;align-items:center}
.logo{width:48px;height:48px;border-radius:10px;background:linear-gradient(135deg,var(--accent1),var(--accent2));display:grid;place-items:center;font-weight:800;color:#051422}
h1{margin:0;font-size:20px}
.main{display:grid;grid-template-columns:1fr 320px;gap:18px}
.panel{background:var(--panel);padding:18px;border-radius:var(--radius);border:1px solid rgba(255,255,255,0.03)}
.item{display:flex;gap:12px;padding:12px;border-radius:10px;background:rgba(255,255,255,0.02);align-items:center}
.item img{width:72px;height:72px;object-fit:cover;border-radius:8px}
.item .meta{flex:1}
.qty{display:flex;gap:8px;align-items:center}
.qty button{padding:6px 10px;border-radius:8px;border:none;background:#0f1724;color:var(--text);cursor:pointer}
.total{font-size:22px;font-weight:800;margin-top:18px;color:transparent;background:linear-gradient(90deg,#a7ffeb,#7b61ff);-webkit-background-clip:text;background-clip:text}
.checkout{width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#051422;font-weight:800;cursor:pointer;margin-top:8px}
.empty{padding:40px;text-align:center;color:var(--muted)}
.info{font-size:13px;color:var(--muted)}
.small{font-size:13px;color:var(--muted)}
.icon{font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 48}
@media (max-width:880px){ .main{grid-template-columns:1fr} }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="brand"><div class="logo">V</div><h1>VIXN • Cart</h1></div>
    <div class="info">Secure checkout • PayPal supported</div>
  </div>

  <div class="main">
    <div id="left" class="panel">
      <div id="items"></div>
      <div id="empty" class="empty" style="display:none">
        <h3>Your cart is empty</h3>
        <p class="small">Add items from the store.</p>
      </div>
    </div>

    <div class="panel">
      <div class="small">Order summary</div>
      <div class="total">Total: <span id="total">$0.00</span></div>
      <div style="margin-top:12px"><input id="email" placeholder="you@example.com" style="width:100%;padding:10px;border-radius:8px;border:none;background:#071428;color:var(--text)"></div>
      <button id="checkout" class="checkout">Pay with PayPal</button>
      <button id="clear" style="margin-top:8px;width:100%;padding:10px;border-radius:8px;border:none;background:#ef4444;color:white;cursor:pointer">Clear Cart</button>
      <div style="margin-top:12px" class="small">Need support? <a style="color:#a7ffeb" href="mailto:contact@example.com">contact us</a></div>
    </div>
  </div>
</div>

<script>
function getCart(){ return JSON.parse(localStorage.getItem('cart')||'[]') }
function saveCart(c){ localStorage.setItem('cart', JSON.stringify(c)) }

function render(){
  const itemsEl = document.getElementById('items');
  const cart = getCart();
  itemsEl.innerHTML = '';
  if(!cart.length){ document.getElementById('empty').style.display='block'; document.getElementById('total').textContent='$0.00'; return }
  document.getElementById('empty').style.display='none';
  let total = 0;
  cart.forEach((it, idx)=>{
    total += parseFloat(it.price || 0) * it.qty;
    const div = document.createElement('div');
    div.className='item';
    div.innerHTML = `
      <img src="${it.image || 'https://via.placeholder.com/72'}">
      <div class="meta">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <div style="font-weight:700">${escapeHtml(it.name)}</div>
            <div style="color:#9aa3b2;font-size:13px">${escapeHtml(it.description || '')}</div>
          </div>
          <div style="text-align:right">
            <div style="font-weight:800">$${Number(it.price).toFixed(2)}</div>
            <div class="small" style="color:#9aa3b2">x${it.qty}</div>
          </div>
        </div>
        <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
          <div class="qty">
            <button onclick="changeQty(${idx}, -1)">-</button>
            <div style="padding:6px 10px;background:#071428;border-radius:8px">${it.qty}</div>
            <button onclick="changeQty(${idx}, 1)">+</button>
          </div>
          <button style="margin-left:auto;background:transparent;border:none;color:#ef4444;cursor:pointer" onclick="removeItem(${idx})">Remove</button>
        </div>
      </div>
    `;
    itemsEl.appendChild(div);
  });
  document.getElementById('total').textContent = '$' + total.toFixed(2);
}

function escapeHtml(s){ return String(s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]); }

function changeQty(i, delta){
  const c = getCart();
  c[i].qty += delta;
  if(c[i].qty < 1) c.splice(i,1);
  saveCart(c);
  render();
}
function removeItem(i){
  const c = getCart();
  c.splice(i,1);
  saveCart(c);
  render();
}

document.getElementById('checkout').addEventListener('click', ()=>{
  const cart = getCart();
  if(!cart.length) return alert('Cart empty!');
  const email = document.getElementById('email').value || prompt('Enter your email:');
  if(!email || !email.includes('@')) return alert('Valid email required');
  fetch('/api/checkout', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, cart})})
    .then(r=>r.json()).then(res=>{
      if(res.ok){ window.open(res.paypal_url,'_blank'); alert('Thank you! Opening PayPal...'); localStorage.removeItem('cart'); render(); }
      else alert('Checkout failed: ' + (res.error||'unknown'));
    });
});

document.getElementById('clear').addEventListener('click', ()=>{
  if(confirm('Clear cart?')){ localStorage.removeItem('cart'); render(); }
});

render();
</script>
</body>
</html>
"""

LOGIN_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN — Admin Login</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#041226;--panel:#071430;--accent:#7b61ff;--muted:#9aa3b2}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(180deg,#01040a,#041226);color:#e6eef8}
.wrap{display:grid;place-items:center;height:100vh}
.box{width:400px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));padding:28px;border-radius:14px;border:1px solid rgba(255,255,255,0.03)}
.box h2{margin:0 0 14px}
input,button{width:100%;padding:12px;border-radius:10px;border:none;background:#071726;color:#e6eef8;margin-top:8px}
button{background:var(--accent);color:#051422;font-weight:700;cursor:pointer}
.error{color:#ffb4b4;margin-top:8px;text-align:center}
.small{font-size:13px;color:#9aa3b2;margin-top:10px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <div class="box">
    <h2>VIXN Admin</h2>
    <form method="post">
      <input name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button>Sign in</button>
    </form>
    {% if error %}<div class="error">{{error}}</div>{% endif %}
    <div class="small">Use your admin account to manage products and view purchases.</div>
  </div>
</div>
</body>
</html>
"""

ADMIN_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,400,0,0" rel="stylesheet" />
<style>
:root{--bg:#041026;--panel:#071430;--muted:#9aa3b2;--text:#e6eef8;--accent1:#7b61ff;--accent2:#00d4ff}
*{box-sizing:border-box}
html,body{height:100%;margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(180deg,#01040a,#041026);color:var(--text)}
.wrap{max-width:1200px;margin:24px auto;padding:20px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
.brand{display:flex;gap:12px;align-items:center}
.logo{width:56px;height:56px;border-radius:12px;background:linear-gradient(135deg,var(--accent1),var(--accent2));display:grid;place-items:center;font-weight:800;color:#051422}
.controls{display:flex;gap:8px;align-items:center}
.btn{padding:10px 14px;border-radius:10px;border:none;cursor:pointer;background:rgba(255,255,255,0.03);color:var(--text)}
.btn.primary{background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#051422;font-weight:800}
.grid{display:grid;grid-template-columns:1fr 420px;gap:18px}
.panel{background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);padding:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.03)}
.form input, .form textarea{width:100%;padding:10px;margin-top:8px;border-radius:8px;border:none;background:#071428;color:var(--text)}
.table{width:100%;border-collapse:collapse;margin-top:10px}
.table th, .table td{padding:10px;border-bottom:1px solid rgba(255,255,255,0.03);text-align:left}
.table img{max-height:60px;border-radius:8px}
.small{font-size:13px;color:var(--muted)}
.search{display:flex;gap:8px;margin-bottom:12px}
.search input{padding:10px;border-radius:10px;border:none;background:#071428;color:var(--text);width:100%}
.actions{display:flex;gap:8px;align-items:center}
@media (max-width:980px){ .grid{grid-template-columns:1fr} }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="brand"><div class="logo">V</div><div><h2 style="margin:0">VIXN Admin</h2><div class="small">Manage products & review purchases</div></div></div>
    <div class="controls">
      <a href="/"><button class="btn">View Store</button></a>
      <a href="/admin/logout"><button class="btn">Logout</button></a>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="panel form">
        <h3 style="margin:0">Add product</h3>
        <form id="addForm" enctype="multipart/form-data">
          <input name="name" placeholder="Product name" required>
          <input name="price" placeholder="Price (number)" required>
          <input name="image" placeholder="Image URL (optional)">
          <input type="file" name="image_file">
          <textarea name="description" placeholder="Description" rows="4"></textarea>
          <div style="display:flex;gap:8px;margin-top:8px">
            <button class="btn primary" type="submit">Add product</button>
            <button type="button" class="btn" onclick="document.getElementById('addForm').reset()">Reset</button>
          </div>
        </form>
      </div>

      <div class="panel" style="margin-top:12px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 style="margin:0">Products ({{products|length}})</h3>
          <div class="actions">
            <input id="prodSearch" placeholder="Search products..." />
            <button class="btn" onclick="downloadProducts()">Export</button>
          </div>
        </div>
        <table class="table" id="prodTable">
          <thead><tr><th>Img</th><th>Product</th><th>Price</th><th>Action</th></tr></thead>
          <tbody>
          {% for p in products %}
            <tr data-name="{{p.name|lower}}">
              <td><img src="{{p.image}}"></td>
              <td><strong>{{p.name}}</strong><br><small class="small">{{p.description}}</small></td>
              <td>${{p.price}}</td>
              <td><button class="btn" onclick="if(confirm('Delete product?')) deleteProduct({{p.id}})">Delete</button></td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <div>
      <div class="panel">
        <h3 style="margin:0">Purchases ({{purchases|length}})</h3>
        <table class="table">
          <thead><tr><th>Time</th><th>Email</th><th>Total</th></tr></thead>
          <tbody>
          {% for p in purchases|reverse %}
            <tr>
              <td>{{p.timestamp[:19].replace('T',' ')}}</td>
              <td>{{p.email}}</td>
              <td>${{p.total}}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="panel" style="margin-top:12px">
        <h3 style="margin:0">Quick actions</h3>
        <div style="display:flex;flex-direction:column;gap:8px;margin-top:12px">
          <button class="btn" onclick="loadSample()">Load sample product</button>
          <button class="btn" onclick="clearProducts()">Clear all products</button>
          <div class="small">Exported JSON can be used to backup or migrate products.</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function escapeHtml(s){ return String(s||'').replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]); }

document.getElementById('addForm').addEventListener('submit', function(e){
  e.preventDefault();
  const fd = new FormData(e.target);
  fetch('/api/add_product', { method:'POST', body: fd }).then(r=>r.json()).then(res=>{
    if(res.ok) location.reload(); else alert('Error: ' + (res.error || 'unknown'));
  }).catch(err=>alert('Network error'));
});

function deleteProduct(id){
  fetch('/api/delete_product', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id})})
    .then(r=>r.json()).then(res=>{ if(res.ok) location.reload(); else alert('Error') })
}

document.getElementById('prodSearch').addEventListener('input', function(e){
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#prodTable tbody tr').forEach(tr=>{
    tr.style.display = (tr.getAttribute('data-name')||'').includes(q) ? '' : 'none';
  });
});

function downloadProducts(){
  fetch('/api/products').then(r=>r.json()).then(data=>{
    const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'products.json';
    a.click();
  });
}

// quick helpers for admin UX
function loadSample(){
  if(!confirm('Add a sample product?')) return;
  const fd = new FormData();
  fd.append('name','Sample Item');
  fd.append('price','9.99');
  fd.append('image','https://via.placeholder.com/640x360?text=Sample');
  fd.append('description','Auto-added sample product');
  fetch('/api/add_product',{method:'POST', body:fd}).then(r=>r.json()).then(res=>location.reload());
}
function clearProducts(){
  if(!confirm('Delete ALL products? This cannot be undone.')) return;
  // fetch current products and delete them one-by-one
  fetch('/api/products').then(r=>r.json()).then(list=>{
    Promise.all(list.map(p=>fetch('/api/delete_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:p.id})})))
    .then(()=>location.reload());
  });
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)