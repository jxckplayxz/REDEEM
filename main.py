# main.py — VIXN 2025 ULTIMATE EDITION — MODERN UI + ICONS + ANIMATIONS
from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vixn_2025_ultra_secret"

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
            "image": image or "https://via.placeholder.com/400x300/1e293b/e6eef8?text=No+Image",
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
        if not pid:
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

# ============================ NEW MODERN UI WITH ICONS ============================

HOME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Premium Digital Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
:root {
  --bg: #0a0a0a;
  --card: rgba(20, 20, 30, 0.6);
  --border: rgba(255, 255, 255, 0.1);
  --text: #f0f0f5;
  --muted: #a0a0c0;
  --accent: #00ff9d;
  --accent2: #7b2ff7;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  background-image: radial-gradient(circle at 10% 20%, rgba(123, 47, 247, 0.15) 0%, transparent 20%),
                    radial-gradient(circle at 90% 80%, rgba(0, 255, 157, 0.15) 0%, transparent 20%);
}
.wrap { max-width: 1300px; margin: 0 auto; padding: 2rem 1rem; }
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3rem;
  position: relative;
}
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.cart-btn {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border);
  padding: 12px 24px;
  border-radius: 16px;
  color: white;
  text-decoration: none;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}
.cart-btn:hover { transform: translateY(-3px); background: rgba(255,255,255,0.2); }
.products {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}
.card {
  background: var(--card);
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid var(--border);
  backdrop-filter: blur(12px);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
}
.card:hover {
  transform: translateY(-16px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  border-color: var(--accent);
}
.card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
}
.card-body {
  padding: 20px;
}
.card-body h3 {
  font-size: 18px;
  margin: 0 0 8px;
  font-weight: 600;
}
.card-body p {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
}
.price {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 16px;
}
.btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: black;
  border: none;
  border-radius: 14px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s;
}
.btn:hover {
  transform: scale(1.05);
  box-shadow: 0 10px 20px rgba(0, 255, 157, 0.3);
}
.floating-cart {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  cursor: pointer;
  z-index: 1000;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(0, 255, 157, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(0, 255, 157, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 255, 157, 0); }
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">
      <i data-lucide="zap" style="width:36px;height:36px;"></i> VIXN
    </div>
    <a href="/cart" class="cart-btn">
      <i data-lucide="shopping-cart"></i> Cart (<span id="count">0</span>)
    </a>
  </header>

  <div id="list" class="products"></div>
</div>

<a href="/cart" class="floating-cart" id="floatingCart">
  <i data-lucide="shopping-bag" style="width:28px;height:28px;color:black;"></i>
  <span style="position:absolute;top:-8px;right:-8px;background:#ff3b5c;color:white;width:24px;height:24px;border-radius:50%;font-size:12px;display:flex;align-items:center;justify-content:center;font-weight:bold;" id="floatCount">0</span>
</a>

<script>
lucide.createIcons();

function $(s){return document.querySelector(s)}
function getCart(){return JSON.parse(localStorage.getItem('cart') || '[]')}
function saveCart(c){
  localStorage.setItem('cart', JSON.stringify(c));
  const totalItems = c.reduce((s,i)=>s+i.qty,0);
  $('#count').textContent = totalItems;
  $('#floatCount').textContent = totalItems;
  document.getElementById('floatingCart').style.display = totalItems > 0 ? 'flex' : 'none';
}
function addToCart(p){
  let c = getCart();
  let ex = c.find(i=>i.id===p.id);
  if(ex) ex.qty++;
  else c.push({...p, qty:1});
  saveCart(c);
  alert("Added to cart!");
}

fetch("/api/products")
.then(r => r.json())
.then(products => {
  const list = $("#list");
  if (products.length === 0) {
    list.innerHTML = `<p style="text-align:center;color:var(--muted);grid-column:1/-1;font-size:18px;">No products available yet</p>`;
    return;
  }
  products.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="\( {p.image}" alt=" \){p.name}" loading="lazy">
      <div class="card-body">
        <h3>${p.name}</h3>
        <p>${p.description || "No description"}</p>
        <div class="price">\[ {p.price}</div>
        <button class="btn" onclick='addToCart(${JSON.stringify(p)})'>
          <i data-lucide="plus"></i> Add to Cart
        </button>
      </div>`;
    list.appendChild(card);
  });
  lucide.createIcons();
})
.catch(() => $("#list").innerHTML = "<p style='text-align:center;color:#888'>Error loading products</p>");

saveCart(getCart());
</script>
</body>
</html>"""

# CART PAGE - ALSO UPGRADED
CART_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Cart</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
:root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:2rem}
.wrap{max-width:800px;margin:auto}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem}
.logo{font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:flex;align-items:center;gap:12px}
.back{color:var(--muted);text-decoration:none;font-weight:600;display:flex;align-items:center;gap:8px}
.item{display:flex;gap:20px;padding:20px;background:var(--card);border:1px solid var(--border);border-radius:16px;margin-bottom:16px}
.item img{width:100px;height:100px;object-fit:cover;border-radius:12px}
.item-info{flex:1}
.item-name{font-size:18px;font-weight:600}
.item-price{color:var(--muted);margin:8px 0}
.total{font-size:32px;font-weight:700;color:var(--accent);text-align:center;margin:2rem 0}
.btn-full{width:100%;padding:18px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:black;border:none;border-radius:16px;font-size:18px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:12px;margin:10px 0;transition:0.3s}
.btn-full:hover{transform:scale(1.02)}
.clear-btn{background:#ef4444 !important;color:white !important}
</style></head><body>
<div class="wrap">
<header>
  <div class="logo"><i data-lucide="zap"></i> VIXN</div>
  <a href="/" class="back"><i data-lucide="arrow-left"></i> Continue Shopping</a>
</header>
<h1 style="text-align:center;margin-bottom:2rem;opacity:0.9">Your Cart</h1>
<div id="items"></div>
<div class="total">Total: <span id="total">$0.00</span></div>
<button id="checkout" class="btn-full"><i data-lucide="credit-card"></i> Checkout with PayPal</button>
<button onclick="if(confirm('Clear cart?')){localStorage.removeItem('cart');location.reload()}" class="btn-full clear-btn"><i data-lucide="trash-2"></i> Clear Cart</button>
</div>
<script>
lucide.createIcons();
function getCart(){return JSON.parse(localStorage.getItem('cart') || '[]')}
function update(){
  const c = getCart();
  const items = document.getElementById("items");
  items.innerHTML = c.length ? "" : `<p style="text-align:center;color:var(--muted);font-size:18px;padding:4rem">Your cart is empty</p>`;
  let total = 0;
  c.forEach(item => {
    total += parseFloat(item.price) * item.qty;
    items.innerHTML += `<div class="item">
      <img src="${item.image}">
      <div class="item-info">
        <div class="item-name">${item.name}</div>
        <div class="item-price"> \]{item.price} × ${item.qty} = $${(item.price * item.qty).toFixed(2)}</div>
      </div>
    </div>`;
  });
  document.getElementById("total").textContent = "$" + total.toFixed(2);
}
update();

document.getElementById("checkout").onclick = () => {
  const cart = getCart();
  if (!cart.length) return alert("Cart is empty!");
  const total = cart.reduce((s,i) => s + parseFloat(i.price) * i.qty, 0).toFixed(2);
  const email = prompt("Total: $" + total + "\nEnter your delivery email:", "");
  if (!email || !email.includes("@")) return alert("Valid email required!");
  fetch("/api/checkout", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email, cart})
  })
  .then(r=>r.json())
  .then(res=>{
    if(res.ok){
      window.open(res.paypal_url,"_blank");
      alert("Payment link opened! Thank you for your purchase!");
      localStorage.removeItem("cart");
      update();
    }
  });
};
</script>
</body></html>"""

# ADMIN & LOGIN - CLEAN & MODERN
LOGIN_HTML = """<!doctype html><html><head><title>VIXN • Admin Login</title><style>
body{background:#0a0a0a;color:#f0f0f5;display:grid;place-items:center;height:100vh;margin:0;font-family:'Inter',sans-serif}
.box{background:rgba(20,20,30,0.8);padding:50px;border-radius:20px;width:380px;border:1px solid rgba(255,255,255,0.1);backdrop-filter:blur(12px)}
h2{text-align:center;margin-bottom:30px;background:linear-gradient(135deg,#00ff9d,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:28px}
input,button{padding:14px;margin:10px 0;width:100%;border-radius:12px;border:none;font-size:16px}
input{background:#1e1e2e;color:white}
button{background:#00ff9d;color:black;font-weight:700;cursor:pointer}
.error{color:#ff6b6b;text-align:center;margin-top:10px}
</style></head><body>
<div class="box">
<h2>VIXN Admin</h2>
<form method=post>
<input name=username placeholder="Username" required>
<input type=password name=password placeholder="Password" required>
<button>Login</button>
{% if error %}<p class="error">{{error}}</p>{% endif %}
</form>
</div></body></html>"""

ADMIN_HTML = """<!doctype html><html><head><title>VIXN • Admin Panel</title><style>
body{background:#0a0a0a;color:#f0f0f5;font-family:'Inter',sans-serif;padding:2rem}
.c{max-width:1200px;margin:auto}
h1{background:linear-gradient(135deg,#00ff9d,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.p{background:rgba(20,20,30,0.6);padding:24px;border-radius:16px;margin:20px 0;border:1px solid rgba(255,255,255,0.1)}
input,textarea,button{padding:12px;margin:8px 0;border-radius:12px;width:100%;background:#1e1e2e;color:white;border:none}
button{background:#00ff9d;color:black;font-weight:700;cursor:pointer}
.del{background:#ef4444 !important;color:white !important;padding:10px 20px;width:auto}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{padding:12px;border-bottom:1px solid rgba(255,255,255,0.1);text-align:left}
img{max-height:80px;border-radius:12px}
a button{float:right;margin-left:10px}
</style></head><body><div class="c">
<h1>VIXN • Admin Panel</h1>
<a href="/admin/logout"><button style="background:#ef4444">Logout</button></a>
<a href="/"><button style="background:#00ff9d;color:black">View Shop</button></a>
<div class="p"><h2>Add New Product</h2>
<form id="f" enctype="multipart/form-data">
<input name=name placeholder="Product Name" required>
<input name=price placeholder="Price (e.g. 29.99)" required>
<input name=image placeholder="Image URL (or upload below)">
<input type=file name=image_file accept="image/*">
<textarea name=description placeholder="Description (optional)" rows="3"></textarea>
<button type=submit>Add Product</button>
</form></div>

<div class="p"><h2>Products ({{products|length}})</h2>
<table><tr><th>Image</th><th>Name</th><th>Price</th><th>Description</th><th>Action</th></tr>
{% for p in products %}
<tr><td><img src="{{p.image}}"></td><td><strong>{{p.name}}</strong></td><td>${{p.price}}</td><td><small>{{p.description}}</small></td>
<td><button class="del" onclick="if(confirm('Delete {{p.name}}?'))fetch('/api/delete_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:{{p.id}}})}).then(()=>location.reload())">Delete</button></td></tr>
{% endfor %}</table></div>

<div class="p"><h2>Recent Purchases ({{purchases|length}})</h2>
<table><tr><th>Time</th><th>Email</th><th>Total</th></tr>
{% for p in purchases|reverse %}
<tr><td>{{p.timestamp[:19].replace('T',' ')}}</td><td>{{p.email}}</td><td>${{p.total}}</td></tr>
{% endfor %}</table></div>

<script>
document.getElementById("f").onsubmit=e=>{e.preventDefault();fetch('/api/add_product',{method:'POST',body:new FormData(e.target)}).then(r=>r.json()).then(d=>d.ok?location.reload():alert("Error: "+d.error))}
</script>
</body></html>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)