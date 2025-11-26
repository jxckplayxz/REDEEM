# main.py — VIXN — FINAL 100% WORKING (Cart error fixed + Render ready)
from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os, requests
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vixn_render_fixed_2025"
PAYPAL_USERNAME = "ContentDeleted939"
ADMIN_USER = "Admin"
ADMIN_PASS = "admin12"

PRODUCTS_FILE = 'products.json'
PURCHASES_FILE = 'purchases.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

for f in [PRODUCTS_FILE, PURCHASES_FILE]:
    if not os.path.exists(f):
        with open(f, 'w', encoding='utf-8') as fp:
            json.dump([] if f == PRODUCTS_FILE else [], fp)

def read_products():
    with open(PRODUCTS_FILE, encoding='utf-8') as f: return json.load(f)
def write_products(data):
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)
def read_purchases():
    with open(PURCHASES_FILE, encoding='utf-8') as f: return json.load(f)
def write_purchases(data):
    with open(PURCHASES_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)
def next_id():
    return max([p.get("id", 0) for p in read_products()], default=0) + 1

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"): return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper

# Routes
@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/cart")
def cart_page():
    return render_template_string(CART_HTML)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
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
        price = float(data.get("price", 0))
        desc = data.get("description", "")

        if not name or price <= 0:
            return jsonify({"ok": False, "error": "Invalid"}), 400

        new_prod = {"id": next_id(), "name": name, "price": round(price, 2),
                    "image": image or "https://via.placeholder.com/320x180?text=No+Image",
                    "description": desc}
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
        if not pid: return jsonify({"ok": False, "error": "No ID"}), 400
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

    total = sum(i["price"] * i["qty"] for i in cart)
    purchases = read_purchases()
    purchases.append({"timestamp": datetime.now().isoformat(), "email": email, "total": round(total, 2), "items": cart})
    write_purchases(purchases)

    url = f"https://www.paypal.me/{PAYPAL_USERNAME}/{total:.2f}"
    return jsonify({"ok": True, "paypal_url": url})

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# FULL TEMPLATES — ALL FIXED
HOME_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIXN</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>:root{--bg:#09090b;--card:#0f1720;--text:#e6eef8;--muted:#9aa3b2;--accent:linear-gradient(135deg,#6ee7b7,#3b82f6)}*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:'Poppins',sans-serif}.wrap{max-width:1200px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}.logo{width:48px;height:48px;border-radius:12px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#052131}h1{font-size:28px;margin:0;font-weight:600}.cart-btn{background:var(--accent);color:#052131;padding:10px 20px;border-radius:10px;font-weight:600;text-decoration:none;font-size:14px}.products{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}.card{background:var(--card);border-radius:14px;overflow:hidden;transition:.3s}.card:hover{transform:translateY(-8px)}.card img{width:100%;height:160px;object-fit:cover}.card-body{padding:16px}.card-body h3{font-size:16px;margin:0 0 6px}.card-body p{font-size:13px;color:var(--muted);margin:0 0 10px}.price{font-size:20px;font-weight:700;color:#a7f3d0}.btn{padding:12px;background:var(--accent);color:#052131;border:none;border-radius:10px;font-weight:600;cursor:pointer;width:100%}</style></head><body>
<div class="wrap"><header><div style="display:flex;gap:12px;align-items:center"><div class="logo">V</div><h1>VIXN</h1></div><a href="/cart" class="cart-btn">Cart (<span id="count">0</span>)</a></header><div id="list" class="products"></div></div>
<script>function \( (s){return document.querySelector(s)}function esc(s){return s?s.toString().replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])):''}function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}function saveCart(c){localStorage.setItem('cart',JSON.stringify(c)); \)('#count').textContent=c.reduce((s,i)=>s+i.qty,0)}function addToCart(p){let c=getCart();let ex=c.find(i=>i.id===p.id);if(ex)ex.qty++;else c.push({...p,qty:1});saveCart(c)}fetch("/api/products").then(r=>r.json()).then(products=>{const list=\( ("#list");products.forEach(p=>{const card=document.createElement("div");card.className="card";card.innerHTML=`<img src=" \){esc(p.image)}" loading="lazy"><div class="card-body"><h3>\( {esc(p.name)}</h3><p> \){esc(p.description||"")}</p><div class="price">\[ {Number(p.price).toFixed(2)}</div><button class="btn" onclick='addToCart(${JSON.stringify(p)})'>Add to Cart</button></div>`;list.appendChild(card);});});saveCart(getCart());</script></body></html>"""

CART_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIXN • Cart</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>:root{--bg:#09090b;--text:#e6eef8;--muted:#9aa3b2;--accent:linear-gradient(135deg,#6ee7b7,#3b82f6)}*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:'Poppins',sans-serif}.wrap{max-width:700px;margin:40px auto;padding:20px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}.logo{width:48px;height:48px;border-radius:12px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#052131}.back{color:var(--muted);text-decoration:none;font-weight:600;font-size:14px}.item{display:flex;gap:16px;margin:16px 0;padding:14px;background:rgba(255,255,255,.03);border-radius:12px}.item img{width:80px;height:80px;object-fit:cover;border-radius:10px}.total{font-size:28px;font-weight:700;margin:24px 0;color:#a7f3d0}.btn{width:100%;padding:16px;font-size:16px;background:var(--accent);color:#052131;border:none;border-radius:12px;font-weight:600;cursor:pointer}.clear{background:#ef4444;margin-top:10px}</style></head><body>
<div class="wrap"><header><div style="display:flex;gap:12px;align-items:center"><div class="logo">V</div><h1 style="margin:0;font-size:24px">VIXN • Cart</h1></div><a href="/" class="back">Back</a></header><div id="items"></div><div class="total">Total: <span id="total">$0.00</span></div><button id="checkout" class="btn">Pay with PayPal</button><button onclick="if(confirm('Clear cart?')){localStorage.removeItem('cart');location.reload()}" class="btn clear">Clear Cart</button></div>
<script>function esc(s){return s?s.toString().replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])):''}function getCart(){return JSON.parse(localStorage.getItem('cart')||'[]')}function update(){const c=getCart();const items=document.getElementById("items");items.innerHTML=c.length?"":"<p style='text-align:center;color:var(--muted);font-size:16px'>Cart is empty</p>";let total=0;c.forEach(item=>{total+=item.price*item.qty;items.innerHTML+=`<div class="item"><img src="\( {esc(item.image)}"><div style="flex:1"><h3 style="margin:0;font-size:16px"> \){esc(item.name)}</h3><p style="margin:4px 0 0;font-size:14px;color:var(--muted)"> \]{item.price.toFixed(2)} × \( {item.qty}</p></div></div>`;});document.getElementById("total").textContent=" \)"+total.toFixed(2);}update();document.getElementById("checkout").onclick=()=>{const cart=getCart();if(!cart.length)return alert("Cart empty!");const total=cart.reduce((s,i)=>s+i.price*i.qty,0).toFixed(2);const email=prompt("Total: $"+total+"\\nEnter your email:", "");if(!email||!email.includes("@"))return alert("Valid email required");fetch("/api/checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,cart})}).then(r=>r.json()).then(res=>{if(res.ok){window.open(res.paypal_url,"_blank");alert("Thank you! Opening PayPal...");localStorage.removeItem("cart");update();}else alert("Error");});};</script></body></html>"""

LOGIN_HTML = """<!doctype html><html><head><title>VIXN • Admin</title><style>body{background:#09090b;color:#e6eef8;display:grid;place-items:center;height:100vh;margin:0;font-family:system-ui}.box{background:#0f172a;padding:40px;border-radius:16px;width:360px}input,button{padding:12px;margin:8px 0;width:100%;border-radius:8px;border:none;background:#1e293b;color:white}button{background:#3b82f6;cursor:pointer;font-weight:600}</style></head><body><div class="box"><h2>VIXN Admin</h2><form method=post><input name=username placeholder=Username required><input type=password name=password placeholder=Password required><button>Login</button>{% if error %}<p style="color:#f87171;text-align:center">{{error}}</p>{% endif %}</form></div></body></html>"""

ADMIN_HTML = """<!doctype html><html><head><title>VIXN • Admin</title><style>body{background:#09090b;color:#e6eef8;font-family:system-ui;padding:20px}.c{max-width:1100px;margin:auto}.p{background:#0f172a;padding:20px;border-radius:12px;margin:20px 0}input,textarea,button{padding:10px;margin:5px 0;border-radius:8px;width:100%;background:#1e293b;color:white;border:none}button{background:#3b82f6;cursor:pointer}.del{background:#ef4444;padding:8px 16px;width:auto}table{width:100%;border-collapse:collapse;margin-top:10px}th,td{padding:10px;border-bottom:1px solid #334155;text-align:left}img{max-height:60px;border-radius:8px}</style></head><body><div class="c"><h1>VIXN • Admin Panel</h1><a href="/admin/logout"><button style="background:#ef4444">Logout</button></a><a href="/"><button style="float:right">View Shop</button></a><div class="p"><h2>Add Product</h2><form id="f" enctype="multipart/form-data"><input name=name placeholder="Name" required><input name=price type=number step=0.01 placeholder="Price" required><input name=image placeholder="Image URL"><input type=file name=image_file><textarea name=description placeholder="Description"></textarea><button type=submit>Add</button></form></div><div class="p"><h2>Products ({{products|length}})</h2><table><tr><th>Img</th><th>Name</th><th>Price</th><th>Action</th></tr>{% for p in products %}<tr><td><img src="{{p.image}}"></td><td><strong>{{p.name}}</strong><br><small style="color:#9aa3b2">{{p.description}}</small></td><td>\( {{p.price}}</td><td><button class="del" onclick="if(confirm('Delete?'))fetch('/api/delete_product',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:{{p.id}}})}).then(()=>location.reload())">Delete</button></td></tr>{% endfor %}</table></div><div class="p"><h2>Purchases ({{purchases|length}})</h2><table><tr><th>Time</th><th>Email</th><th>Total</th></tr>{% for p in purchases|reverse %}<tr><td>{{p.timestamp[:19].replace("T"," ")}}</td><td>{{p.email}}</td><td> \){{p.total}}</td></tr>{% endfor %}</table></div><script>document.getElementById("f").onsubmit=e=>{e.preventDefault();fetch("/api/add_product",{method:"POST",body:new FormData(e.target)}).then(()=>location.reload())}</script></body></html>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)