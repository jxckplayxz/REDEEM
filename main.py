from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os, requests, uuid, threading, time
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import lru_cache

app = Flask(__name__)
app.secret_key = "vixn_2025_ultra_secret_auto_confirm"

# ========================= CONFIG =========================

ADMIN_USER = "Admin"
ADMIN_PASS = "admin12"

# YOUR BTC WALLET (ALL PAYMENTS GO HERE)
BTC_WALLET = "bc1qagcaenvmug20thznjtuqselmnjkp4q0yarewqe"

PRODUCTS_FILE = 'products.json'
PURCHASES_FILE = 'purchases.json'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create files
for f in [PRODUCTS_FILE, PURCHASES_FILE]:
    if not os.path.exists(f):
        with open(f, 'w', encoding='utf-8') as fp:
            json.dump([], fp)

# In-memory pending payments tracker
pending_payments = {} # token -> {amount_btc, email, cart, paid: False}

# Background checker thread
def payment_watcher():
    while True:
        time.sleep(15)
        for token, data in list(pending_payments.items()):
            if data.get("paid"):
                continue
            amount_btc = data["amount_btc"]
            try:
                tx_url = f"https://blockstream.info/api/address/{BTC_WALLET}/txs"
                recent_txs = requests.get(tx_url, timeout=10).json()
                
                for tx in recent_txs[:10]:
                    txid = tx["txid"]
                    value = 0
                    for vout in tx.get("vout", []):
                        if vout.get("scriptpubkey_address") == BTC_WALLET:
                            value += vout["value"]
                            
                    btc_received = value / 100000000
                    
                    if abs(btc_received - amount_btc) < 0.00005:
                        # PAYMENT FOUND!
                        purchases = read_purchases()
                        for p in purchases:
                            if p.get("token") == token and p.get("status") == "pending":
                                p["status"] = "paid"
                                p["paid_at"] = datetime.now().isoformat()
                                p["txid"] = txid
                                break
                        write_purchases(purchases)
                        pending_payments[token]["paid"] = True
                        print(f"PAYMENT CONFIRMED! {data['email']} paid {amount_btc:.8f} BTC | TX: {txid}")
                        break
            except Exception as e:
                print(f"Error checking payment for token {token}: {e}")
                continue 

# Start background watcher
threading.Thread(target=payment_watcher, daemon=True).start()

# ========================= DATA HELPERS =========================

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

# ========================= AUTH =========================

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/admin")
        return f(*args, **kwargs)
    return wrapper

# ========================= BTC PRICE =========================

@lru_cache(maxsize=1)
def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=8)
        return r.json()["bitcoin"]["usd"]
    except:
        return 95000

# ========================= ROUTES =========================

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/cart")
def cart_page():
    return render_template_string(CART_HTML)

# NEW: Order Status Page
@app.route("/status/<token>")
def order_status(token):
    purchases = read_purchases()
    order = next((p for p in purchases if p.get("token") == token), None)
    
    if not order:
        return render_template_string(STATUS_404_HTML)
        
    return render_template_string(STATUS_HTML, order=order)

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
            price = f"{float(price):.2f}"
        except:
            return jsonify({"ok": False, "error": "Invalid price"}), 400
            
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
        total_usd = sum(float(i["price"]) * int(i.get("qty", 1)) for i in cart)
    except:
        return jsonify({"ok": False, "error": "Invalid cart"}), 400
        
    btc_price = get_btc_price()
    amount_btc = total_usd / btc_price
    token = str(uuid.uuid4())
    
    # Register pending payment
    pending_payments[token] = {
        "amount_btc": round(amount_btc, 8),
        "amount_usd": round(total_usd, 2),
        "email": email,
        "cart": cart,
        "paid": False,
        "created": time.time()
    }
    
    # Save order
    purchases = read_purchases()
    purchases.append({
        "timestamp": datetime.now().isoformat(),
        "email": email,
        "total_usd": round(total_usd, 2),
        "total_btc": round(amount_btc, 8),
        "status": "pending",
        "payment_address": BTC_WALLET,
        "token": token,
        "items": cart
    })
    write_purchases(purchases)
    
    qr = f"https://chart.googleapis.com/chart?chs=380x380&cht=qr&chl=bitcoin:{BTC_WALLET}?amount={amount_btc:.8f}&label=VIXN"
    uri = f"bitcoin:{BTC_WALLET}?amount={amount_btc:.8f}&label=VIXN%20Shop"
    status_url = url_for('order_status', token=token, _external=True) # NEW: Generate status URL
    
    return jsonify({
        "ok": True,
        "payment_address": BTC_WALLET,
        "amount_btc": round(amount_btc, 8),
        "amount_usd": round(total_usd, 2),
        "qr": qr,
        "wallet_uri": uri,
        "token": token,
        "status_url": status_url # NEW: Return status URL
    }) 

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ========================= FULL HTML TEMPLATES =========================

HOME_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Premium Digital Shop</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;background-image:radial-gradient(circle at 10% 20%,rgba(123,47,247,0.15)0%,transparent 20%),radial-gradient(circle at 90% 80%,rgba(0,255,157,0.15)0%,transparent 20%)}
        .wrap{max-width:1300px;margin:0 auto;padding:2rem 1rem}
        header{display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem}
        .logo{display:flex;align-items:center;gap:12px;font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .cart-btn{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);border:1px solid var(--border);padding:12px 24px;border-radius:16px;color:white;text-decoration:none;font-weight:600;display:flex;align-items:center;gap:8px;transition:all .3s}
        .cart-btn:hover{transform:translateY(-3px);background:rgba(255,255,255,0.2)}
        .products{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px}
        .card{background:var(--card);border-radius:20px;overflow:hidden;border:1px solid var(--border);backdrop-filter:blur(12px);transition:all .4s cubic-bezier(.175,.885,.32,1.275)}
        .card:hover{transform:translateY(-16px) scale(1.02);box-shadow:0 20px 40px rgba(0,0,0,0.4);border-color:var(--accent)}
        .card img{width:100%;height:200px;object-fit:cover}
        .card-body{padding:20px}
        .card-body h3{font-size:18px;margin:0 0 8px;font-weight:600}
        .card-body p{color:var(--muted);font-size:14px;line-height:1.5;margin-bottom:16px}
        .price{font-size:24px;font-weight:700;color:var(--accent);margin-bottom:16px}
        .btn{width:100%;padding:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:black;border:none;border-radius:14px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;transition:all .3s}
        .btn:hover{transform:scale(1.05);box-shadow:0 10px 20px rgba(0,255,157,0.3)}
        .floating-cart{position:fixed;bottom:30px;right:30px;background:linear-gradient(135deg,var(--accent),var(--accent2));width:60px;height:60px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,0.5);cursor:pointer;z-index:1000;animation:pulse 2s infinite}
        @keyframes pulse{0%{box-shadow:0 0 0 0 rgba(0,255,157,0.4)}70%{box-shadow:0 0 0 15px rgba(0,255,157,0)}100%{box-shadow:0 0 0 0 rgba(0,255,157,0)}}
    </style>
</head>
<body>
    <div class="wrap">
        <header>
            <div class="logo">
                <i data-lucide="gem"></i>
                VIXN
            </div>
            <a href="/cart" class="cart-btn">
                <i data-lucide="shopping-cart"></i>
                Cart (<span id="count">0</span>)
            </a>
        </header>

        <div class="products" id="list">
            </div>
    </div>

    <a href="/cart" class="floating-cart" id="floatingCart" style="display:none;">
        <i data-lucide="shopping-cart" style="color:black;"></i>
    </a>

    <script>
        lucide.createIcons();

        function getCart(){
            return JSON.parse(localStorage.getItem('cart') || '[]');
        }

        function saveCart(cart){
            localStorage.setItem('cart', JSON.stringify(cart));
            const n = cart.reduce((sum, item) => sum + (item.qty || 1), 0);
            document.getElementById('count').textContent = n;
            document.getElementById('floatingCart').style.display = n > 0 ? 'flex' : 'none';
        }

        function addToCart(p){
            let c = getCart();
            let ex = c.find(i => i.id === p.id);
            
            if(ex) {
                ex.qty = (ex.qty || 0) + 1;
            } else {
                c.push({...p, qty: 1});
            }
            
            saveCart(c);
            alert("Added!");
        }

        fetch("/api/products")
            .then(r => r.json())
            .then(p => {
                const l = document.getElementById("list");
                
                if(!p.length){
                    l.innerHTML = `<p style="text-align:center;color:var(--muted);grid-column:1/-1;font-size:18px;">No products yet</p>`;
                    return;
                }
                
                p.forEach(x => {
                    const d = document.createElement("div");
                    d.className = "card";
                    
                    d.innerHTML = `
                        <img src="${x.image}" alt="${x.name}">
                        <div class="card-body">
                            <h3>${x.name}</h3>
                            <p>${x.description || "No description"}</p>
                            <div class="price">$ ${(parseFloat(x.price)||0).toFixed(2)}</div>
                            <button class="btn" onclick='addToCart(${JSON.stringify(x)})'>
                                <i data-lucide="plus"></i> Add to Cart
                            </button>
                        </div>
                    `;
                    l.appendChild(d);
                });
                lucide.createIcons();
            });

        saveCart(getCart());
    </script>
</body>
</html>
""" 

CART_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Cart</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
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
        .btn-full{width:100%;padding:18px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:black;border:none;border-radius:16px;font-size:18px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:12px;margin:10px 0;transition:.3s}
        .btn-full:hover{transform:scale(1.02)}
        .clear-btn{background:#ef4444!important;color:white!important}
        #payment{display:none;flex-direction:column;align-items:center;background:var(--card);padding:30px;border-radius:20px;border:2px solid var(--accent);margin:20px 0;gap:16px}
        #payment img{border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,0.5)}
        .address{font-family:monospace;background:#1e1e2e;padding:14px;border-radius:10px;font-size:15px;word-break:break-all;text-align:center}
        .success{background:#10b981;color:white;padding:20px;border-radius:16px;text-align:center;font-size:18px}
        .status-link{margin-top:20px;font-size:16px;background:#1e1e2e;padding:15px;border-radius:10px;text-align:center;word-break:break-all;}
        .status-link a{color:var(--accent);text-decoration:underline;}
    </style>
</head>
<body>
    <div class="wrap">
        <header>
            <div class="logo">
                <i data-lucide="gem"></i>
                VIXN
            </div>
            <a href="/" class="back">
                <i data-lucide="arrow-left"></i>
                Continue Shopping
            </a>
        </header>

        <h2>Your Cart</h2>
        <div id="items">
            </div>

        <div class="total">
            Total: <span id="total">$0.00</span>
        </div>

        <button id="checkout" class="btn-full">Pay with Bitcoin</button>
        <button id="clearCart" class="btn-full clear-btn">Clear Cart</button>

        <div id="payment">
            <h3>Send Bitcoin to Complete Order</h3>
            <div style="text-align: center;">
                Amount: <span id="btcAmount">0 BTC</span> ≈ <span id="usdAmount">$0.00</span>
            </div>
            <img id="qrCode" src="" alt="QR Code">
            <div class="address" id="btcAddress"></div>
            <a id="walletLink" class="btn-full" target="_blank">
                <i data-lucide="wallet"></i> Open in Wallet
            </a>
            <p style="text-align:center;color:var(--muted)">Payment auto-detected in ~10–60s<br>Do not close this page</p>
        </div>

        <div id="success" class="success" style="display:none;">
            PAYMENT CONFIRMED!
            <p style="font-size:16px;margin-top:10px">Your order is being processed. Check your email.</p>
        </div>
        
        <div id="statusLinkContainer" class="status-link" style="display:none;">
            Track your order: <a href="#" id="statusUrl">Loading...</a>
        </div>
    </div>

    <script>
        lucide.createIcons();
        
        function getCart(){
            return JSON.parse(localStorage.getItem('cart') || '[]');
        }

        function update(){
            const c = getCart();
            const i = document.getElementById("items");
            i.innerHTML = '';
            
            if(!c.length){
                i.innerHTML = `<p style="text-align:center;color:var(--muted);font-size:18px;padding:4rem">Empty cart</p>`;
                document.getElementById("total").textContent = "$0.00";
                return;
            }
            
            let t = 0;
            c.forEach(x => {
                const q = x.qty || 1;
                const p = parseFloat(x.price) || 0;
                t += p * q;
                
                i.innerHTML += `
                    <div class="item">
                        <img src="${x.image}">
                        <div class="item-info">
                            <div class="item-name">${x.name}</div>
                            <div class="item-price"> $${p.toFixed(2)} × ${q} = $ ${(p * q).toFixed(2)}</div>
                        </div>
                    </div>
                `;
            });
            document.getElementById("total").textContent = "$" + t.toFixed(2);
        }

        update();

        document.getElementById("checkout").onclick = async () => {
            const c = getCart();
            if(!c.length) return alert("Cart empty!");
            
            const total = c.reduce((s, x) => s + (parseFloat(x.price) || 0) * (x.qty || 1), 0).toFixed(2);
            
            const email = prompt(\`Total: $${total}\\nDelivery email:\`, ""); 
            
            if(!email || !email.includes("@")) return alert("Valid email required!");

            const res = await fetch("/api/checkout", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({email, cart: c})
            }).then(r => r.json());

            if(!res.ok) return alert("Error: " + (res.error || "Unknown"));

            document.getElementById("btcAmount").textContent = res.amount_btc + " BTC";
            document.getElementById("usdAmount").textContent = "$" + res.amount_usd;
            document.getElementById("btcAddress").textContent = res.payment_address;
            document.getElementById("qrCode").src = res.qr;
            document.getElementById("walletLink").href = res.wallet_uri;
            document.getElementById("payment").style.display = "flex";
            document.getElementById("checkout").style.display = "none";
            document.getElementById("clearCart").style.display = "none";
            
            // NEW: Display the status URL
            const statusLinkElement = document.getElementById("statusUrl");
            statusLinkElement.href = res.status_url;
            statusLinkElement.textContent = res.status_url;
            document.getElementById("statusLinkContainer").style.display = "block";

            localStorage.removeItem("cart");
            update();

            alert("Send exactly " + res.amount_btc + " BTC\\nAuto-confirm in seconds!");

            let check = setInterval(async() => {
                try {
                    const r = await fetch(res.status_url).then(r => r.text()); 
                    
                    if (r.includes("PAID")) { // Check for the paid status on the new page
                         clearInterval(check);
                         document.getElementById("payment").style.display = "none";
                         document.getElementById("success").style.display = "block";
                         document.getElementById("statusLinkContainer").style.display = "none";
                    }
                } catch {}
            }, 5000);
        };

        document.getElementById("clearCart").onclick = () => {
            if(confirm("Clear cart?")){
                localStorage.removeItem("cart");
                update();
            }
        }
    </script>
</body>
</html>
""" 

LOGIN_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Admin Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body{background:#0a0a0a;color:#f0f0f5;display:grid;place-items:center;height:100vh;margin:0;font-family:'Inter',sans-serif}
        .box{background:rgba(20,20,30,0.8);padding:50px;border-radius:20px;width:380px;border:1px solid rgba(255,255,255,0.1);backdrop-filter:blur(12px)}
        h2{text-align:center;margin-bottom:30px;background:linear-gradient(135deg,#00ff9d,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:28px}
        input,button{padding:14px;margin:10px 0;width:100%;border-radius:12px;border:none;font-size:16px}
        input{background:#1e1e2e;color:white}
        button{background:#00ff9d;color:black;font-weight:700;cursor:pointer}
        .error{color:#ff6b6b;text-align:center;margin-top:10px}
    </style>
</head>
<body>
    <div class="box">
        <h2>VIXN Admin</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password" placeholder="Password">
            <button type="submit">Login</button>
            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}
        </form>
    </div>
</body>
</html>
""" 

ADMIN_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        body{background:#0a0a0a;color:#f0f0f5;font-family:'Inter',sans-serif;padding:2rem}
        .c{max-width:1200px;margin:auto}
        h1{background:linear-gradient(135deg,#00ff9d,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .p{background:rgba(20,20,30,0.6);padding:24px;border-radius:16px;margin:20px 0;border:1px solid rgba(255,255,255,0.1)}
        input,textarea,button{padding:12px;margin:8px 0;border-radius:12px;width:100%;background:#1e1e2e;color:white;border:none}
        button{background:#00ff9d;color:black;font-weight:700;cursor:pointer}
        .del{background:#ef4444!important;color:white!important;padding:10px 20px;width:auto}
        table{width:100%;border-collapse:collapse;margin-top:20px}
        th,td{padding:12px;border-bottom:1px solid rgba(255,255,255,0.1);text-align:left}
        img{max-height:80px;border-radius:12px}
        .paid{color:#10b981;font-weight:bold}
        .pending{color:#fb923c}
        .actions-btn{display:flex;gap:10px;}
        .delete-btn{background:red;color:white;border:none;padding:5px 10px;border-radius:8px;cursor:pointer;}
    </style>
</head>
<body>
    <div class="c">
        <h1>VIXN • Admin Panel</h1>
        <div style="display:flex;justify-content:space-between;margin-bottom:20px;">
            <a href="/admin/logout" class="del">Logout</a>
            <a href="/" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:8px;">View Shop</a>
        </div>

        <div class="p">
            <h2>Add Product</h2>
            <form id="f" enctype="multipart/form-data">
                <input type="text" name="name" placeholder="Name" required>
                <input type="number" name="price" placeholder="Price (USD)" step="0.01" required>
                <textarea name="description" placeholder="Description"></textarea>
                <input type="url" name="image" placeholder="Image URL (optional)">
                <label style="display:block;margin:10px 0;color:#a0a0c0;">OR Upload Image File:</label>
                <input type="file" name="image_file" accept="image/*" style="background:#2e2e3e;border:1px solid #3e3e4e;">
                <button type="submit">Add Product</button>
            </form>
        </div>

        <div class="p">
            <h2>Products ({{ products|length }})</h2>
            <table>
                <thead>
                    <tr><th>Img</th><th>Name</th><th>Price</th><th>Action</th></tr>
                </thead>
                <tbody id="products-list">
                    {% for p in products %}
                    <tr id="prod-{{ p.id }}">
                        <td><img src="{{ p.image }}" alt="{{ p.name }}"></td>
                        <td>{{ p.name }}</td>
                        <td>${{ p.price }}</td>
                        <td>
                            <button class="delete-btn" onclick="deleteProduct({{ p.id }})">Delete</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="p">
            <h2>Purchases ({{ purchases|length }})</h2>
            <table>
                <thead>
                    <tr><th>Date</th><th>Email</th><th>USD</th><th>BTC</th><th>Status</th><th>TXID</th></tr>
                </thead>
                <tbody>
                    {% for p in purchases | reverse %}
                    <tr>
                        <td>{{ p.timestamp[:16].replace('T', ' ') }}</td>
                        <td>{{ p.email }}</td>
                        <td>${{ p.total_usd }}</td>
                        <td>{{ p.total_btc }}</td>
                        <td class="{{ 'paid' if p.status == 'paid' else 'pending' }}">{{ p.status.upper() }}</td>
                        <td>{% if p.txid %}{{ p.txid[:8] }}...{% else %}-{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        lucide.createIcons();

        document.getElementById("f").onsubmit = e => {
            e.preventDefault();
            fetch('/api/add_product', {
                method: 'POST',
                body: new FormData(e.target)
            })
            .then(r => r.json())
            .then(d => d.ok ? location.reload() : alert("Error: " + d.error))
            .catch(err => alert("Network Error: " + err));
        }
        
        function deleteProduct(id) {
            if (confirm("Are you sure you want to delete product ID " + id + "?")) {
                fetch('/api/delete_product', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id})
                })
                .then(r => r.json())
                .then(d => d.ok ? location.reload() : alert("Error deleting: " + d.error))
                .catch(err => alert("Network Error: " + err));
            }
        }
    </script>
</body>
</html>
"""

STATUS_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Order Status</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7;--status-pending:#fb923c;--status-paid:#10b981}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:grid;place-items:center;padding:2rem;}
        .wrap{max-width:600px;width:100%;background:var(--card);padding:40px;border-radius:20px;border:1px solid var(--border);backdrop-filter:blur(12px);text-align:center;}
        .logo{font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:30px;}
        h2{font-size:24px;margin-bottom:20px;}
        .status-badge{font-size:36px;font-weight:800;padding:15px 30px;border-radius:15px;margin:20px 0;display:inline-block;
            background:{% if order.status == 'paid' %}var(--status-paid){% else %}var(--status-pending){% endif %};
            color:black;text-transform:uppercase;
        }
        .detail{text-align:left;margin-top:20px;padding:15px;background:#1e1e2e;border-radius:10px;font-size:16px;}
        .detail strong{color:var(--accent);}
        .item-list{text-align:left;margin-top:20px;border-top:1px solid var(--border);padding-top:15px;}
        .item-list div{margin-bottom:5px;font-size:14px;color:var(--muted);}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="logo"><i data-lucide="gem"></i>VIXN</div>
        <h2>Order Status: {{ order.token[:8] }}...</h2>
        
        <div class="status-badge">
            {% if order.status == 'paid' %}
                <i data-lucide="check-circle" style="width:30px;height:30px;"></i> PAID
            {% else %}
                <i data-lucide="clock" style="width:30px;height:30px;"></i> PENDING
            {% endif %}
        </div>
        
        <div class="detail">
            <p><strong>Total:</strong> ${{ order.total_usd }} ({{ order.total_btc }} BTC)</p>
            <p><strong>Email:</strong> {{ order.email }}</p>
            <p><strong>Time:</strong> {{ order.timestamp[:16].replace('T', ' ') }}</p>
            {% if order.txid %}<p><strong>Transaction ID:</strong> <a href="https://blockstream.info/tx/{{ order.txid }}" target="_blank">{{ order.txid[:10] }}...</a></p>{% endif %}
        </div>

        <div class="item-list">
            <strong>Items Ordered:</strong>
            {% for item in order.items %}
                <div>{{ item.name }} x {{ item.qty }} (${{ (item.price|float * item.qty)|round(2) }})</div>
            {% endfor %}
        </div>
        
        {% if order.status == 'pending' %}
            <p style="margin-top:20px;color:var(--status-pending);font-weight:600;">Waiting for blockchain confirmation. Refresh to check for updates.</p>
        {% else %}
            <p style="margin-top:20px;color:var(--status-paid);font-weight:600;">Your digital goods will be delivered to your email shortly.</p>
        {% endif %}

    </div>
    <script>lucide.createIcons();</script>
</body>
</html>
"""

STATUS_404_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Order Not Found</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root{--bg:#0a0a0a;--card:rgba(20,20,30,0.6);--border:rgba(255,255,255,0.1);--text:#f0f0f5;--muted:#a0a0c0;--accent:#00ff9d;--accent2:#7b2ff7}
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:grid;place-items:center;padding:2rem;}
        .wrap{max-width:600px;width:100%;background:var(--card);padding:40px;border-radius:20px;border:1px solid var(--border);backdrop-filter:blur(12px);text-align:center;}
        .logo{font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:30px;}
        h2{font-size:24px;margin-bottom:20px;color:#ef4444;}
        p{color:var(--muted);}
        a{color:var(--accent);text-decoration:underline;}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="logo"><i data-lucide="gem"></i>VIXN</div>
        <h2>Order Not Found</h2>
        <i data-lucide="search-x" style="width:50px;height:50px;margin:20px auto;color:#ef4444;"></i>
        <p>The transaction ID or order token you provided is invalid or could not be found.</p>
        <p style="margin-top:15px;">Please check the link again or return to the <a href="/">home page</a>.</p>
    </div>
    <script>lucide.createIcons();</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"VIXN 2025 AUTO-CONFIRM SHOP RUNNING ON PORT {port}")
    print(f"BTC Wallet: {BTC_WALLET}")
    app.run(host="0.0.0.0", port=port, debug=False)
