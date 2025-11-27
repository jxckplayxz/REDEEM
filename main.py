# main.py — VIXN 2025 ULTIMATE EDITION — MODERN UI + REQUEST ITEMS
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
            "price": float(price),
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

# ============================ HOME HTML WITH REQUEST ITEM BUTTON ============================
HOME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Premium Digital Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
:root { --bg:#0a0a0a; --card:rgba(20,20,30,0.6); --border:rgba(255,255,255,0.1); --text:#f0f0f5; --muted:#a0a0c0; --accent:#00ff9d; --accent2:#7b2ff7; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
.wrap { max-width:1300px; margin:0 auto; padding:2rem 1rem; }
header { display:flex; justify-content:space-between; align-items:center; margin-bottom:3rem; }
.logo { font-size:28px; font-weight:800; background:linear-gradient(135deg,var(--accent),var(--accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; display:flex; align-items:center; gap:12px; }
.cart-btn { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border:1px solid var(--border); padding:12px 24px; border-radius:16px; color:white; text-decoration:none; font-weight:600; display:flex; align-items:center; gap:8px; transition: all 0.3s; }
.cart-btn:hover { transform:translateY(-3px); background: rgba(255,255,255,0.2); }
.products { display:grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap:24px; }
.card { background:var(--card); border-radius:20px; overflow:hidden; border:1px solid var(--border); backdrop-filter:blur(12px); transition: all 0.4s; position:relative; }
.card:hover { transform:translateY(-16px) scale(1.02); box-shadow:0 20px 40px rgba(0,0,0,0.4); border-color:var(--accent); }
.card img { width:100%; height:200px; object-fit:cover; }
.card-body { padding:20px; }
.card-body h3 { font-size:18px; margin:0 0 8px; font-weight:600; }
.card-body p { color:var(--muted); font-size:14px; line-height:1.5; margin-bottom:16px; }
.price { font-size:24px; font-weight:700; color:var(--accent); margin-bottom:16px; }
.btn { width:100%; padding:14px; background:linear-gradient(135deg,var(--accent),var(--accent2)); color:black; border:none; border-radius:14px; font-weight:700; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:10px; transition: all 0.3s; }
.btn:hover { transform:scale(1.05); box-shadow:0 10px 20px rgba(0,255,157,0.3); }
.floating-cart { position: fixed; bottom:30px; right:30px; background:linear-gradient(135deg,var(--accent),var(--accent2)); width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 10px 30px rgba(0,0,0,0.5); cursor:pointer; z-index:1000; animation:pulse 2s infinite; }
@keyframes pulse {0% {box-shadow:0 0 0 0 rgba(0,255,157,0.4);} 70% {box-shadow:0 0 0 15px rgba(0,255,157,0);} 100% {box-shadow:0 0 0 0 rgba(0,255,157,0);}}
#requestBtn { margin-top:20px; width:auto; padding:12px 24px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo"><i data-lucide="zap" style="width:36px;height:36px;"></i> VIXN</div>
    <a href="/cart" class="cart-btn">
      <i data-lucide="shopping-cart"></i> Cart (<span id="count">0</span>)
    </a>
  </header>

  <button id="requestBtn" class="btn"><i data-lucide="message-circle"></i> Request Item</button>

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

// Request Item button
document.getElementById("requestBtn").onclick = () => {
    const name = prompt("Item Name:");
    if(!name) return alert("Item name is required!");
    const desc = prompt("Item Description (optional):") || "";
    const contact = prompt("Your Email or Discord (optional):") || "";
    let requests = JSON.parse(localStorage.getItem("requests") || "[]");
    requests.push({ name, desc, contact, date: new Date().toLocaleString() });
    localStorage.setItem("requests", JSON.stringify(requests));
    alert("Your request has been saved!");
    console.log("Item Requests:", requests);
}

// Load products
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
      <img src="${p.image}" alt="${p.name}" loading="lazy">
      <div class="card-body">
        <h3>${p.name}</h3>
        <p>${p.description || "No description"}</p>
        <div class="price">$${parseFloat(p.price).toFixed(2)}</div>
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

# CART_HTML, LOGIN_HTML, ADMIN_HTML remain the same as your previous setup.
# Just make sure to fix price display in CART_HTML as well like this:
# <div class="item-price">$${parseFloat(item.price).toFixed(2)} × ${item.qty} = $${(item.price*item.qty).toFixed(2)}</div>

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)