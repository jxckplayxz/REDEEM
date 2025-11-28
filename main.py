# main.py — VIXN 2025 Ultimate Edition — Shop + Admin + PayPal + BTC
from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os
from werkzeug.utils import secure_filename
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = "vixn_2025_ultra_secret"

PAYPAL_USERNAME = "ContentDeleted939"
ADMIN_USER = "Admin"
ADMIN_PASS = "admin12"
BTC_WALLET = "bc1qagcaenvmug20thznjtuqselmnjkp4q0yarewqe"

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
        try:
            price_val = float(price)
            price = f"{price_val:.2f}"
        except:
            return jsonify({"ok": False, "error": "Price must be numeric"}), 400
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
    try:
        total = sum(float(i["price"]) * int(i.get("qty", 1)) for i in cart)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid cart prices/quantity"}), 400
    purchases = read_purchases()
    purchases.append({"timestamp": datetime.now().isoformat(), "email": email, "total": round(total, 2), "items": cart})
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
        total_usd = sum(float(i["price"]) * int(i.get("qty", 1)) for i in cart)
    except:
        return jsonify({"ok": False, "error": "Invalid cart prices/quantity"}), 400
    # get BTC price in USD
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        btc_price = r.json()["bitcoin"]["usd"]
        btc_amount = round(total_usd / btc_price, 8)
    except:
        return jsonify({"ok": False, "error": "Failed to fetch BTC price"}), 500
    purchases = read_purchases()
    purchases.append({"timestamp": datetime.now().isoformat(), "email": email, "total": round(total_usd,2), "items": cart, "crypto":"BTC"})
    write_purchases(purchases)
    return jsonify({"ok": True, "btc_amount": btc_amount, "wallet_address": BTC_WALLET})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============================ HTML Templates ============================

HOME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Premium Digital Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
:root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;background-image:radial-gradient(circle at 10% 20%, rgba(123, 47, 247, 0.15) 0%, transparent 20%),radial-gradient(circle at 90% 80%, rgba(0, 255, 157, 0.15) 0%, transparent 20%)}
.wrap{max-width:1300px;margin:0 auto;padding:2rem 1rem}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem;position:relative}
.logo{display:flex;align-items:center;gap:12px;font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.cart-btn{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border:1px solid var(--border);padding:12px 24px;border-radius:16px;color:white;text-decoration:none;font-weight:600;display:flex;align-items:center;gap:8px;transition:all 0.3s}
.cart-btn:hover{transform:translateY(-3px);background:rgba(255,255,255,0.2)}
.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}
.card{background:var(--card);border-radius:20px;overflow:hidden;border:1px solid var(--border);backdrop-filter:blur(12px);transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);position:relative}
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
<a href="/cart" class="floating-cart" id="floatingCart" style="display:none;"><i data-lucide="shopping-bag" style="width:28px;height:28px;color:black"></i><span style="position:absolute;top:-8px;right:-8px;background:#ff3b5c;color:white;width:24px;height:24px;border-radius:50%;font-size:12px;display:flex;align-items:center;justify-content:center;font-weight:bold" id="floatCount">0</span></a>
<script>
lucide.createIcons();
function $(s){return document.querySelector(s)}
function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}
function saveCart(c){localStorage.setItem('cart',JSON.stringify(c));const totalItems=c.reduce((s,i)=>s+(parseInt(i.qty)||0),0);$('#count').textContent=totalItems;$('#floatCount').textContent=totalItems;document.getElementById('floatingCart').style.display=totalItems>0?'flex':'none'}
function addToCart(p){let c=getCart();let ex=c.find(i=>i.id===p.id);if(ex) ex.qty=(parseInt(ex.qty)||0)+1; else c.push({id:p.id,name:p.name,price:p.price,image:p.image,qty:1});saveCart(c);alert("Added to cart!")}
fetch("/api/products").then(r=>r.json()).then(products=>{const list=$("#list");if(!products||products.length===0){list.innerHTML='<p style="text-align:center;color:var(--muted);grid-column:1/-1;font-size:18px;">No products available yet</p>';return;}products.forEach(p=>{const card=document.createElement("div");card.className="card";const img=document.createElement("img");img.src=p.image||"https://via.placeholder.com/400x300/1e293b/e6eef8?text=No+Image";img.alt=p.name||"Product Image";const body=document.createElement("div");body.className="card-body";const h3=document.createElement("h3");h3.textContent=p.name;const desc=document.createElement("p");desc.textContent=p.description||"No description";const price=document.createElement("div");price.className="price";let priceNum=parseFloat(p.price||0);price.textContent="$"+priceNum.toFixed(2);const btn=document.createElement("button");btn.className="btn";btn.innerHTML='<i data-lucide="plus"></i> Add to Cart';btn.addEventListener('click',()=>addToCart(p));body.appendChild(h3);body.appendChild(desc);body.appendChild(price);body.appendChild(btn);card.appendChild(img);card.appendChild(body);list.appendChild(card)});lucide.createIcons()}).catch(()=>$("#list").innerHTML="<p style='text-align:center;color:#888'>Error loading products</p>");
saveCart(getCart());
</script>
</body>
</html>

CART_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Cart</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
body{font-family:'Inter',sans-serif;background:#0a0a0a;color:#f0f0f5;padding:2rem}
a{color:#00ff9d;text-decoration:none}
.cart-table{width:100%;border-collapse:collapse;margin-bottom:2rem}
.cart-table th, .cart-table td{border-bottom:1px solid rgba(255,255,255,0.1);padding:12px;text-align:left}
.cart-table th{color:#00ff9d}
.btn{padding:12px 24px;background:linear-gradient(135deg,#00ff9d,#7b2ff7);border:none;border-radius:12px;color:black;font-weight:700;cursor:pointer;display:inline-block;margin-top:1rem}
.btn:hover{transform:scale(1.05);box-shadow:0 8px 20px rgba(0,255,157,0.3)}
.total{font-size:22px;font-weight:700;margin-top:1rem;color:#00ff9d}
</style>
</head>
<body>
<h1>Your Cart</h1>
<table class="cart-table" id="cartTable">
<tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th><th></th></tr>
</table>
<div class="total" id="totalAmount"></div>
<button class="btn" id="paypalBtn">Checkout with PayPal</button>
<button class="btn" id="cryptoBtn">Checkout with BTC</button>
<script>
lucide.createIcons();
function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}
function saveCart(c){localStorage.setItem('cart',JSON.stringify(c))}
function renderCart(){const cart=getCart();const table=document.getElementById("cartTable");table.innerHTML='<tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th><th></th></tr>';let total=0;cart.forEach((p,i)=>{let tr=document.createElement("tr");let price=parseFloat(p.price)||0;let qty=parseInt(p.qty)||1;let line=price*qty;total+=line;tr.innerHTML=`<td>${p.name}</td><td><input type="number" min="1" value="${qty}" data-index="${i}" class="qtyInput" style="width:60px"></td><td>$${price.toFixed(2)}</td><td>$${line.toFixed(2)}</td><td><button data-index="${i}" class="removeBtn">Remove</button></td>`;table.appendChild(tr)});document.getElementById("totalAmount").textContent="Total: $"+total.toFixed(2)}
document.addEventListener("input",function(e){if(e.target.classList.contains("qtyInput")){let c=getCart();c[e.target.dataset.index].qty=parseInt(e.target.value)||1;saveCart(c);renderCart()}})
document.addEventListener("click",function(e){if(e.target.classList.contains("removeBtn")){let c=getCart();c.splice(e.target.dataset.index,1);saveCart(c);renderCart()}})
renderCart();
document.getElementById("paypalBtn").addEventListener("click",()=>{let email=prompt("Enter your email");if(!email)return;fetch("/api/checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:email,cart:getCart()})}).then(r=>r.json()).then(d=>{if(d.ok)window.location.href=d.paypal_url;else alert(d.error)})})
document.getElementById("cryptoBtn").addEventListener("click",()=>{let email=prompt("Enter your email");if(!email)return;fetch("/api/crypto_checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:email,cart:getCart()})}).then(r=>r.json()).then(d=>{if(d.ok)alert("Send "+d.btc_amount+" BTC to wallet:\\n"+d.wallet_address);else alert(d.error)})})
</script>
</body>
</html>
"""

LOGIN_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Admin Login</title>
<style>
body{font-family:sans-serif;background:#0a0a0a;color:#f0f0f5;display:flex;align-items:center;justify-content:center;height:100vh}
.login-box{background:rgba(20,20,30,0.8);padding:2rem;border-radius:16px;width:300px;text-align:center;border:1px solid rgba(255,255,255,0.1)}
input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.2);background:#0a0a0a;color:white}
button{width:100%;padding:12px;margin-top:8px;border:none;border-radius:12px;background:linear-gradient(135deg,#00ff9d,#7b2ff7);color:black;font-weight:700;cursor:pointer}
button:hover{transform:scale(1.05)}
.error{color:#ff3b5c;margin-bottom:8px}
</style>
</head>
<body>
<div class="login-box">
<h2>Admin Login</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>
"""

ADMIN_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Admin Panel</title>
<style>
body{font-family:sans-serif;background:#0a0a0a;color:#f0f0f5;padding:2rem}
h1{margin-bottom:1rem;color:#00ff9d}
table{width:100%;border-collapse:collapse;margin-bottom:2rem}
th,td{border-bottom:1px solid rgba(255,255,255,0.1);padding:10px;text-align:left}
th{color:#00ff9d}
input,textarea{width:100%;padding:8px;margin:4px 0;background:#0a0a0a;color:white;border:1px solid rgba(255,255,255,0.2);border-radius:8px}
button{padding:10px 16px;background:linear-gradient(135deg,#00ff9d,#7b2ff7);border:none;border-radius:10px;color:black;font-weight:700;cursor:pointer;margin-top:4px}
button:hover{transform:scale(1.05)}
a{color:#00ff9d;text-decoration:none}
</style>
</head>
<body>
<h1>Admin Panel</h1>
<a href="/admin/logout">Logout</a>
<h2>Add Product</h2>
<form id="addForm">
<input type="text" name="name" placeholder="Product Name" required>
<input type="text" name="price" placeholder="Price USD" required>
<input type="text" name="image" placeholder="Image URL">
<input type="file" name="image_file">
<textarea name="description" placeholder="Description"></textarea>
<button type="submit">Add Product</button>
</form>
<h2>Products</h2>
<table>
<tr><th>ID</th><th>Name</th><th>Price</th><th>Actions</th></tr>
{% for p in products %}
<tr>
<td>{{ p.id }}</td>
<td>{{ p.name }}</td>
<td>${{ p.price }}</td>
<td><button data-id="{{ p.id }}" class="delBtn">Delete</button></td>
</tr>
{% endfor %}
</table>
<h2>Purchases</h2>
<table>
<tr><th>Time</th><th>Email</th><th>Total</th><th>Items</th></tr>
{% for pur in purchases %}
<tr>
<td>{{ pur.timestamp }}</td>
<td>{{ pur.email }}</td>
<td>${{ pur.total }}</td>
<td>{% for it in pur.items %}{{ it.name }} x{{ it.qty }}{% if not loop.last %}, {% endif %}{% endfor %}</td>
</tr>
{% endfor %}
</table>
<script>
document.getElementById("addForm").addEventListener("submit",function(e){e.preventDefault();let f=new FormData(this);fetch("/api/add_product",{method:"POST",body:f}).then(r=>r.json()).then(d=>{if(d.ok)location.reload();else alert(d.error)})})
document.querySelectorAll(".delBtn").forEach(b=>{b.addEventListener("click",()=>{if(confirm("Delete product?")){fetch("/api/delete_product",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:parseInt(b.dataset.id)})}).then(r=>r.json()).then(d=>{if(d.ok)location.reload();else alert(d.error)})}})})
</script>
</body>
</html>
"""

# ============================ Run App ============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)