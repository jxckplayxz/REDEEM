# main.py — VIXN 2025 FULL — BTC WALLET CHECKOUT INCLUDED
from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vixn_2025_ultra_secret"

PAYPAL_USERNAME = "ContentDeleted939"
ADMIN_USER = "Admin"
ADMIN_PASS = "admin12"
CRYPTO_WALLET_ADDRESS = "YOUR_BTC_WALLET_ADDRESS_HERE"
CRYPTO_CURRENCY = "BTC"
BTC_PRICE_USD = 30000  # Replace with real-time API if desired

PRODUCTS_FILE = 'products.json'
PURCHASES_FILE = 'purchases.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    prods = read_products()
    if not prods:
        return 1
    return max([p.get("id", 0) for p in prods]) + 1

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
    return render_template_string(CART_HTML, wallet=CRYPTO_WALLET_ADDRESS, currency=CRYPTO_CURRENCY, btc_price=BTC_PRICE_USD)

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
    try:
        price_val = float(price)
        price = f"{price_val:.2f}"
    except:
        return jsonify({"ok": False, "error": "Price must be numeric"}), 400
    new_prod = {"id": next_id(),"name": name,"price": price,"image": image or "https://via.placeholder.com/400x300/1e293b/e6eef8?text=No+Image","description": desc}
    prods = read_products()
    prods.append(new_prod)
    write_products(prods)
    return jsonify({"ok": True})

@app.route("/api/delete_product", methods=["POST"])
@login_required
def delete_product():
    pid = request.get_json().get("id")
    if pid is None:
        return jsonify({"ok": False, "error": "No ID"}), 400
    products = [p for p in read_products() if p["id"] != pid]
    write_products(products)
    return jsonify({"ok": True})

@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    cart = data.get("cart", [])
    if not email or not cart:
        return jsonify({"ok": False, "error": "Email & cart required"}), 400
    try:
        total = sum(float(i["price"]) * int(i.get("qty", 1)) for i in cart)
    except:
        return jsonify({"ok": False, "error": "Invalid cart prices/quantity"}), 400
    purchases = read_purchases()
    purchases.append({"timestamp": datetime.now().isoformat(),"email": email,"total": round(total,2),"items": cart})
    write_purchases(purchases)
    url = f"https://www.paypal.me/{PAYPAL_USERNAME}/{total:.2f}"
    return jsonify({"ok": True, "paypal_url": url})

@app.route("/api/crypto_checkout", methods=["POST"])
def crypto_checkout():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    cart = data.get("cart", [])
    if not email or not cart:
        return jsonify({"ok": False, "error": "Email & cart required"}), 400
    try:
        total_usd = sum(float(i["price"]) * int(i.get("qty",1)) for i in cart)
        total_btc = round(total_usd / BTC_PRICE_USD, 8)
    except:
        return jsonify({"ok": False, "error": "Invalid cart prices/quantity"}), 400
    purchases = read_purchases()
    purchases.append({
        "timestamp": datetime.now().isoformat(),
        "email": email,
        "total": round(total_usd,2),
        "items": cart,
        "status": "pending",
        "wallet_address": CRYPTO_WALLET_ADDRESS,
        "currency": CRYPTO_CURRENCY,
        "btc_amount": total_btc
    })
    write_purchases(purchases)
    return jsonify({"ok": True, "wallet_address": CRYPTO_WALLET_ADDRESS, "btc_amount": total_btc, "currency": CRYPTO_CURRENCY})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ====================== HTML TEMPLATES ======================

HOME_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Premium Digital Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
:root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.wrap{max-width:1300px;margin:0 auto;padding:2rem 1rem}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem}
.logo{display:flex;align-items:center;gap:12px;font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.cart-btn{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border:1px solid var(--border);padding:12px 24px;border-radius:16px;color:white;text-decoration:none;font-weight:600;display:flex;align-items:center;gap:8px;transition:all 0.3s}
.cart-btn:hover{transform:translateY(-3px);background:rgba(255,255,255,0.2)}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}
.card{background:var(--card);border-radius:20px;overflow:hidden;border:1px solid var(--border);backdrop-filter:blur(12px);transition:all 0.4s;position:relative}
.card:hover{transform:translateY(-16px) scale(1.02);box-shadow:0 20px 40px rgba(0,0,0,0.4);border-color:var(--accent)}
.card img{width:100%;height:200px;object-fit:cover}
.card-body{padding:20px}
.card-body h3{font-size:18px;margin:0 0 8px;font-weight:600}
.card-body p{color:var(--muted);font-size:14px;line-height:1.5;margin-bottom:16px}
.price{font-size:24px;font-weight:700;color:var(--accent);margin-bottom:16px}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:black;border:none;border-radius:14px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;transition:all 0.3s}
.btn:hover{transform:scale(1.05);box-shadow:0 10px 20px rgba(0,255,157,0.3)}
.floating-cart{position:fixed;bottom:30px;right:30px;background:linear-gradient(135deg,var(--accent),var(--accent2));width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,0.5);cursor:pointer;z-index:1000;animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(0,255,157,0.4)}70%{box-shadow:0 0 0 15px rgba(0,255,157,0)}100%{box-shadow:0 0 0 0 rgba(0,255,157,0)}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo"><i data-lucide="zap" style="width:36px;height:36px;"></i> VIXN</div>
    <a href="/cart" class="cart-btn"><i data-lucide="shopping-cart"></i> Cart (<span id="count">0</span>)</a>
  </header>
  <div id="list" class="products"></div>
</div>

<a href="/cart" class="floating-cart" id="floatingCart" style="display:none;">
  <i data-lucide="shopping-bag" style="width:28px;height:28px;color:black;"></i>
  <span style="position:absolute;top:-8px;right:-8px;background:#ff3b5c;color:white;width:24px;height:24px;border-radius:50%;font-size:12px;display:flex;align-items:center;justify-content:center;font-weight:bold;" id="floatCount">0</span>
</a>

<script>
lucide.createIcons();
function $(s){return document.querySelector(s)}
function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}
function saveCart(c){
  localStorage.setItem('cart',JSON.stringify(c))
  const totalItems=c.reduce((s,i)=>s+(parseInt(i.qty)||0),0)
  $('#count').textContent=totalItems
  $('#floatCount').textContent=totalItems
  document.getElementById('floatingCart').style.display=totalItems>0?'flex':'none'
}
function addToCart(p){
  let c=getCart()
  let ex=c.find(i=>i.id===p.id)
  if(ex) ex.qty=(parseInt(ex.qty)||0)+1
  else c.push({id:p.id,name:p.name,price:p.price,image:p.image,qty:1})
  saveCart(c)
  alert("Added to cart!")
}
fetch("/api/products").then(r=>r.json()).then(products=>{
  const list=$("#list")
  if(!products||products.length===0){list.innerHTML=`<p style="text-align:center;color:var(--muted);grid-column:1/-1;font-size:18px;">No products available yet</p>`;return;}
  products.forEach(p=>{
    const card=document.createElement("div");card.className="card"
    const img=document.createElement("img");img.src=p.image||"https://via.placeholder.com/400x300/1e293b/e6eef8?text=No+Image";img.alt=p.name||"Product Image"
    const body=document.createElement("div");body.className="card-body"
    const h3=document.createElement("h3");h3.textContent=p.name
    const desc=document.createElement("p");desc.textContent=p.description||"No description"
    const price=document.createElement("div");price.className="price";let priceNum=parseFloat(p.price||0);price.textContent="$"+priceNum.toFixed(2)
    const btn=document.createElement("button");btn.className="btn";btn.innerHTML=`<i data-lucide="plus"></i> Add to Cart`;btn.addEventListener('click',()=>addToCart(p))
    body.appendChild(h3);body.appendChild(desc);body.appendChild(price);body.appendChild(btn)
    card.appendChild(img);card.appendChild(body)
    list.appendChild(card)
  })
  lucide.createIcons()
}).catch(()=>$("#list").innerHTML="<p style='text-align:center;color:#888'>Error loading products</p>")
saveCart(getCart())
</script>
</body></html>"""

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
<button id="paypalCheckout" class="btn-full"><i data-lucide="credit-card"></i> Checkout with PayPal</button>
<button id="cryptoCheckout" class="btn-full"><i data-lucide="hexagon"></i> Checkout with BTC</button>
<button id=">Clear Cart</button>
<script>
lucide.createIcons();
function $(s){return document.querySelector(s)}
function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}
function saveCart(c){localStorage.setItem('cart',JSON.stringify(c))}
function renderCart(){
    const cart=getCart();const items=$("#items");items.innerHTML="";let total=0;
    cart.forEach(p=>{
        let div=document.createElement("div");div.className="item";
        div.innerHTML=`<img src="${p.image}" alt="${p.name}"><div class="item-info">
        <div class="item-name">${p.name}</div>
        <div class="item-price">$${(parseFloat(p.price)*parseInt(p.qty||1)).toFixed(2)} (${p.qty} pcs)</div>
        <button style="padding:6px 12px;border:none;border-radius:8px;background:#ef4444;color:white;cursor:pointer;">Remove</button></div>`;
        div.querySelector("button").onclick=()=>{let c=getCart();c=c.filter(i=>i.id!==p.id);saveCart(c);renderCart()};
        items.appendChild(div);
        total+=parseFloat(p.price)*(parseInt(p.qty)||1);
    });
    $("#total").textContent="$"+total.toFixed(2);
}
renderCart();

$("#clearCart").onclick=()=>{localStorage.removeItem("cart");renderCart()};

async function paypalCheckout(){
    let email=prompt("Enter your email for the receipt:");
    if(!email)return;
    let res=await fetch("/api/checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,cart:getCart()})});
    let data=await res.json();
    if(data.ok){window.location.href=data.paypal_url}else{alert(data.error||"Error during checkout")}
}

async function cryptoCheckout(){
    let email=prompt("Enter your email for the receipt:");
    if(!email)return;
    let res=await fetch("/api/crypto_checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,cart:getCart()})});
    let data=await res.json();
    if(data.ok){
        let msg=`Send exactly ${data.btc_amount} ${data.currency} to wallet:\n${data.wallet_address}`;
        alert(msg);
    } else {alert(data.error||"Error during BTC checkout")}
}

$("#paypalCheckout").onclick=paypalCheckout;
$("#cryptoCheckout").onclick=cryptoCheckout;
</script>
</body></html>
"""

LOGIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Login</title>
<style>
body{background:#0a0a0a;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh}
form{background:#111;padding:2rem;border-radius:12px;display:flex;flex-direction:column;gap:1rem;width:300px}
input{padding:12px;border-radius:8px;border:none;font-size:16px}
button{padding:12px;background:#00ff9d;color:black;font-weight:bold;border:none;border-radius:8px;cursor:pointer}
.error{color:#ff4b5c;text-align:center}
</style>
</head><body>
<form method="POST">
<h2 style="text-align:center;">Admin Login</h2>
<input name="username" placeholder="Username">
<input name="password" type="password" placeholder="Password">
<button>Login</button>
{% if error %}<div class="error">{{error}}</div>{% endif %}
</form>
</body></html>"""

ADMIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Panel</title>
<style>body{font-family:sans-serif;background:#0a0a0a;color:white;padding:2rem}h1{margin-bottom:1rem}table{width:100%;border-collapse:collapse}td,th{border:1px solid #444;padding:8px;text-align:left}a{color:#00ff9d}</style>
</head><body>
<h1>Products</h1>
<form method="POST" action="/api/add_product" enctype="multipart/form-data">
<input name="name" placeholder="Name">
<input name="price" placeholder="Price USD">
<input name="description" placeholder="Description">
<input type="file" name="image_file">
<button>Add Product</button>
</form>
<table><tr><th>ID</th><th>Name</th><th>Price</th><th>Action</th></tr>
{% for p in products %}
<tr><td>{{p.id}}</td><td>{{p.name}}</td><td>${{p.price}}</td><td><button onclick="fetch('/api/delete_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:{{p.id}}})}).then(()=>location.reload())">Delete</button></td></tr>
{% endfor %}
</table>
<h1>Purchases</h1>
<table><tr><th>Email</th><th>Total</th><th>Items</th><th>Timestamp</th></tr>
{% for pur in purchases %}
<tr><td>{{pur.email}}</td><td>${{pur.total}}</td><td>{{pur.items}}</td><td>{{pur.timestamp}}</td></tr>
{% endfor %}
</table>
<a href="/admin/logout">Logout</a>
</body></html>"""

if __name__=="__main__":
    app.run(debug=True, port=5000)