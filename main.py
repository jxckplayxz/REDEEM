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
REQUESTS_FILE = 'requests.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

for f in [PRODUCTS_FILE, PURCHASES_FILE, REQUESTS_FILE]:
    if not os.path.exists(f):
        with open(f, 'w', encoding='utf-8') as fp:
            json.dump([], fp)

def read_products():
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_products(data):
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def read_purchases():
    with open(PURCHASES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_purchases(data):
    with open(PURCHASES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def read_requests():
    with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_requests(data):
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def next_id(file):
    data = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        pass
    return max([x.get("id", 0) for x in data], default=0) + 1

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
        return render_template_string(ADMIN_HTML, products=read_products(), purchases=read_purchases(), requests=read_requests())
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

    new_prod = {
        "id": next_id(PRODUCTS_FILE),
        "name": name,
        "price": price,
        "image": image or "https://via.placeholder.com/400x300/1e293b/e6eef8?text=No+Image",
        "description": desc
    }
    prods = read_products()
    prods.append(new_prod)
    write_products(prods)
    return jsonify({"ok": True})

@app.route("/api/delete_product", methods=["POST"])
@login_required
def delete_product():
    pid = request.get_json().get("id")
    if not pid:
        return jsonify({"ok": False, "error": "No ID"}), 400
    products = [p for p in read_products() if p["id"] != pid]
    write_products(products)
    return jsonify({"ok": True})

@app.route("/api/request_item", methods=["POST"])
def request_item():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    price = data.get("price", "").strip()
    email = data.get("email", "").strip()
    if not name or not price or not email:
        return jsonify({"ok": False, "error": "All fields required"}), 400

    req = {
        "id": next_id(REQUESTS_FILE),
        "name": name,
        "price": price,
        "email": email,
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    reqs = read_requests()
    reqs.append(req)
    write_requests(reqs)
    return jsonify({"ok": True, "msg": "Request sent! Admin will review it soon."})

@app.route("/api/approve_request", methods=["POST"])
@login_required
def approve_request():
    rid = request.get_json().get("id")
    req = next((r for r in read_requests() if r["id"] == rid), None)
    if not req:
        return jsonify({"ok": False})

    new_prod = {
        "id": next_id(PRODUCTS_FILE),
        "name": req["name"],
        "price": req["price"],
        "image": "https://via.placeholder.com/400x300/1e293b/e6eef8?text=Requested+Item",
        "description": f"Requested by {req['email']}"
    }
    prods = read_products()
    prods.append(new_prod)
    write_products(prods)

    reqs = [r for r in read_requests() if r["id"] != rid]
    write_requests(reqs)
    return jsonify({"ok": True})

@app.route("/api/deny_request", methods=["POST"])
@login_required
def deny_request():
    rid = request.get_json().get("id")
    reqs = [r for r in read_requests() if r["id"] != rid]
    write_requests(reqs)
    return jsonify({"ok": True})

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

HOME_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIXN • Premium Digital Shop</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>

<style>
/* your UI untouched */
</style>
</head>
<body>

<div class="wrap">
  <header>
    <div class="logo"><i data-lucide="zap"></i> VIXN</div>
    <a href="/cart" class="cart-btn"><i data-lucide="shopping-cart"></i> Cart (<span id="count">0</span>)</a>
  </header>
  <div id="list" class="products"></div>
</div>

<div class="floating-cart" onclick="location.href='/cart'">
  <i data-lucide="shopping-bag"></i>
  <span id="floatCount">0</span>
</div>

<script>
lucide.createIcons();

function $(s){ return document.querySelector(s); }

function getCart(){
  return JSON.parse(localStorage.getItem("cart") || "[]");
}

function saveCart(c){
  localStorage.setItem("cart", JSON.stringify(c));
  const totalItems = c.reduce((n,i)=>n+i.qty,0);
  $("#count").textContent = totalItems;
  $("#floatCount").textContent = totalItems;
}

function addToCart(p){
  let c=getCart();
  let ex=c.find(i=>i.id===p.id);
  if(ex) ex.qty++;
  else c.push({...p, qty:1});
  saveCart(c);
  alert("Added to cart!");
}

fetch("/api/products")
.then(r=>r.json())
.then(products=>{
  const list = $("#list");
  if(products.length===0){
    list.innerHTML = `<p style="text-align:center;color:var(--muted);grid-column:1/-1;">No products yet</p>`;
    return;
  }

  products.forEach(p=>{
    const card=document.createElement("div");
    card.className="card";
    card.innerHTML = `
      <img src="${p.image}" alt="${p.name}">
      <div class="card-body">
        <h3>${p.name}</h3>
        <p>${p.description || "No description"}</p>
        <div class="price">$${p.price}</div>
        <button class="btn" onclick='addToCart(${JSON.stringify(p)})'>
          Add to Cart
        </button>
      </div>`;
    list.appendChild(card);
  });
});
</script>

</body>
</html>
"""

CART_HTML = """<h1 style='color:white;text-align:center'>Cart Page Coming Soon</h1>"""
LOGIN_HTML = """<h1>Login Page</h1>"""
ADMIN_HTML = """<h1>Admin Panel</h1>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)