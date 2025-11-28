from flask import Flask, jsonify, request, send_from_directory, render_template_string, redirect, session, url_for
import json, os, requests, uuid, threading, time
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import lru_cache

# --- Mock Email Library (REMOVED) ---

app = Flask(__name__)
# WARNING: In production, change this to a complex, randomly generated key and keep it secret!
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
        time.sleep(120) 
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

@app.route("/admin", methods=["GET", "POST"])
def admin():
    status_message = None
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USER and request.form.get("password") == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(url_for('admin')) 
        else:
            status_message = {"type": "error", "message": "Wrong credentials"}
            return render_template_string(LOGIN_HTML, status=status_message)
            
    if session.get("logged_in"):
        # Check for email content in session and clear it
        staged_email = session.pop('staged_email', None)
        
        # Check for a general status message (e.g., from product deletion)
        status_param = request.args.get('status')
        if status_param == 'product_deleted':
            status_message = {"type": "success", "message": "Product deleted successfully!"}
        
        return render_template_string(ADMIN_HTML, 
                                      products=read_products(), 
                                      purchases=read_purchases(),
                                      staged_email=staged_email, # Pass the email data to the template
                                      status=status_message)
    return render_template_string(LOGIN_HTML, status=status_message)

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
            price_float = float(price)
            price = f"{price_float:.2f}"
        except ValueError:
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
        print(f"Error adding product: {e}")
        return jsonify({"ok": False, "error": "Server error while adding product."}), 500 

@app.route("/api/delete_product", methods=["POST"])
@login_required
def delete_product():
    pid = request.get_json().get("id")
    if pid is None:
        return jsonify({"ok": False, "error": "No ID"}), 400
    try:
        pid = int(pid)
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid ID format"}), 400
        
    products = [p for p in read_products() if p["id"] != pid]
    write_products(products)
    # Redirect with a status to show confirmation (better UX)
    return jsonify({"ok": True, "redirect": url_for('admin', status='product_deleted')})

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
        return jsonify({"ok": False, "error": "Invalid cart/price format"}), 400
        
    btc_price = get_btc_price()
    if btc_price == 0:
        return jsonify({"ok": False, "error": "BTC price unavailable"}), 500
        
    amount_btc = total_usd / btc_price
    token = str(uuid.uuid4())
    
    pending_payments[token] = {
        "amount_btc": round(amount_btc, 8),
        "amount_usd": round(total_usd, 2),
        "email": email,
        "cart": cart,
        "paid": False,
        "created": time.time()
    }
    
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
    
    return jsonify({
        "ok": True,
        "payment_address": BTC_WALLET,
        "amount_btc": round(amount_btc, 8),
        "amount_usd": round(total_usd, 2),
        "qr": qr,
        "wallet_uri": uri,
        "token": token
    }) 

@app.route("/api/stage_email", methods=["POST"])
@login_required
def stage_email_route():
    """Captures email data and stages it for display in the admin panel."""
    data = request.form
    recipient = data.get("recipient", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()

    if not recipient or not subject or not body:
        session['staged_email'] = {"error": "All email fields are required."}
        return redirect(url_for('admin'))

    # Store the email details in the session for the next page load
    session['staged_email'] = {
        "recipient": recipient,
        "subject": subject,
        "body": body
    }
    
    # Redirect back to the admin page to display the staged email
    return redirect(url_for('admin'))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ========================= FULL HTML TEMPLATES (IMPROVED UI) =========================

# --- SHARED STYLES ---
# Factored out the core color variables and base styles for consistency.
SHARED_STYLE = """
    :root{
        --bg:#0a0a0a;
        --card:#1a1a2a;
        --border:rgba(255,255,255,0.1);
        --text:#e0e0f0;
        --muted:#a0a0c0;
        --accent:#00ff9d;
        --accent2:#7b2ff7;
        --danger:#ef4444;
        --success:#10b981;
    }
    *{margin:0;padding:0;box-sizing:border-box}
    body{
        font-family:'Inter',sans-serif;
        background:var(--bg);
        color:var(--text);
        min-height:100vh;
        background-image:radial-gradient(circle at 10% 20%,rgba(123,47,247,0.08)0%,transparent 20%),radial-gradient(circle at 90% 80%,rgba(0,255,157,0.08)0%,transparent 20%);
        transition: background-color 0.3s ease;
    }
    .wrap{max-width:1300px;margin:0 auto;padding:2rem 1rem}
    .logo{
        display:flex;align-items:center;gap:12px;font-size:32px;font-weight:900;
        background:linear-gradient(135deg,var(--accent),var(--accent2));
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        letter-spacing: -1px;
    }
    .btn, .btn-full {
        padding: 14px 24px;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
        text-decoration: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .btn:hover, .btn-full:hover{
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0,255,157,0.3);
    }
    .btn-primary, .btn-full {
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        color: black;
    }
    .btn-secondary{
        background: rgba(255,255,255,0.1);
        color: var(--text);
        border: 1px solid var(--border);
        backdrop-filter: blur(5px);
    }
    .btn-secondary:hover{
        background: rgba(255,255,255,0.2);
        box-shadow: 0 4px 10px rgba(123,47,247,0.2);
    }
    @keyframes pulse{
        0% {box-shadow:0 0 0 0 rgba(0,255,157,0.4)}
        70% {box-shadow:0 0 0 15px rgba(0,255,157,0)}
        100% {box-shadow:0 0 0 0 rgba(0,255,157,0)}
    }
"""

HOME_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Premium Digital Shop</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        {SHARED_STYLE}
        header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4rem;padding-top:1rem}}
        .products{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:30px}}
        .card{{
            background:var(--card);
            border-radius:24px;
            overflow:hidden;
            border:1px solid var(--border);
            backdrop-filter:blur(10px);
            transition:all .4s cubic-bezier(.175,.885,.32,1.275);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }}
        .card:hover{{
            transform:translateY(-12px);
            box-shadow:0 25px 50px rgba(0,0,0,0.5), 0 0 0 2px var(--accent);
        }}
        .card img{{width:100%;height:250px;object-fit:cover;border-bottom:1px solid var(--border)}}
        .card-body{{padding:24px}}
        .card-body h3{{font-size:20px;margin:0 0 8px;font-weight:700}}
        .card-body p{{color:var(--muted);font-size:15px;line-height:1.6;margin-bottom:18px}}
        .price{{font-size:28px;font-weight:800;color:var(--accent);margin-bottom:20px;text-shadow: 0 0 5px rgba(0,255,157,0.4)}}
        .floating-cart{{
            position:fixed;bottom:30px;right:30px;
            background:linear-gradient(135deg,var(--accent),var(--accent2));
            width:64px;height:64px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;
            box-shadow:0 15px 35px rgba(0,0,0,0.6);
            cursor:pointer;z-index:1000;
            animation:pulse 2s infinite;
        }}
        .floating-cart i{{color:black;width:28px;height:28px}}
    </style>
</head>
<body>
    <div class="wrap">
        <header>
            <div class="logo">
                <i data-lucide="gem"></i>
                VIXN
            </div>
            <a href="/cart" class="btn btn-secondary">
                <i data-lucide="shopping-cart"></i>
                Cart (<span id="count">0</span>)
            </a>
        </header>

        <div class="products" id="list">
        </div>
    </div>

    <a href="/cart" class="floating-cart" id="floatingCart" style="display:none;">
        <i data-lucide="shopping-cart"></i>
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
            const btn = event.currentTarget;
            btn.innerHTML = '<i data-lucide="check"></i> Added!';
            btn.style.backgroundColor = 'var(--success)';
            setTimeout(() => {
                btn.innerHTML = '<i data-lucide="plus"></i> Add to Cart';
                btn.style.backgroundColor = ''; 
            }, 1000);
            lucide.createIcons();
        }

        fetch("/api/products")
            .then(r => r.json())
            .then(p => {
                const l = document.getElementById("list");
                
                if(!p.length){
                    l.innerHTML = `<p style="text-align:center;color:var(--muted);grid-column:1/-1;font-size:18px;margin-top:50px;">No products available at the moment.</p>`;
                    return;
                }
                
                p.forEach(x => {
                    const d = document.createElement("div");
                    d.className = "card";
                    
                    const price = (parseFloat(x.price)||0).toFixed(2); 
                    
                    d.innerHTML = `
                        <img src="${x.image}" alt="${x.name}">
                        <div class="card-body">
                            <h3>${x.name}</h3>
                            <p>${x.description || "A premium digital asset with high utility."}</p>
                            <div class="price">$${price}</div>
                            <button class="btn btn-primary" onclick='addToCart(${JSON.stringify(x)})'>
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

CART_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Cart</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        {SHARED_STYLE}
        body{{padding:2rem}}
        .wrap{{max-width:900px;margin:auto}}
        header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3rem}}
        h2{{font-size:36px;font-weight:800;margin-bottom:20px}}
        .back{{color:var(--muted);text-decoration:none;font-weight:600;display:flex;align-items:center;gap:8px;transition:color .3s}}
        .back:hover{{color:var(--accent)}}
        .item{{
            display:flex;gap:20px;padding:20px;
            background:var(--card);border:1px solid var(--border);
            border-radius:18px;margin-bottom:16px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            align-items:center;
        }}
        .item img{{width:120px;height:120px;object-fit:cover;border-radius:12px}}
        .item-info{{flex:1}}
        .item-name{{font-size:20px;font-weight:700}}
        .item-price{{color:var(--muted);margin:8px 0;font-size:15px}}
        .total{{font-size:40px;font-weight:900;color:var(--accent);text-align:right;margin:3rem 0;text-shadow:0 0 10px rgba(0,255,157,0.5)}}
        .total span{{font-size:inherit}}
        .btn-full{{margin:15px 0}}
        .clear-btn{{
            background:var(--danger)!important;
            color:white!important;
        }}
        .clear-btn:hover{
            background: #dc2626!important;
            box-shadow: 0 8px 15px rgba(239, 68, 68, 0.3);
        }
        #payment{{
            display:none;flex-direction:column;align-items:center;
            background:var(--card);padding:40px;border-radius:24px;
            border:2px solid var(--accent);margin:30px 0;gap:20px;
        }}
        #payment h3{font-size:24px;margin-bottom:10px}
        #payment img{{
            width: 250px; height: 250px;
            border-radius:16px;box-shadow:0 15px 35px rgba(0,0,0,0.5);
        }}
        .address{{
            font-family:monospace;background:#1e1e2e;
            padding:16px;border-radius:12px;font-size:16px;
            word-break:break-all;text-align:center;
            border:1px dashed var(--accent);
        }}
        .address i{margin-right:8px;vertical-align:middle;}
        .success{{
            background:var(--success);color:black;
            padding:30px;border-radius:18px;text-align:center;
            font-size:24px;font-weight:700;
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.5);
        }}
        .success p{{font-size:16px;margin-top:10px;font-weight:400;}}
        .qty-controls{
            display:flex;align-items:center;gap:10px;
            font-weight:600;
        }
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

        <button id="checkout" class="btn-full btn-primary">
            <i data-lucide="bitcoin"></i> Pay with Bitcoin
        </button>
        <button id="clearCart" class="btn-full clear-btn">
            <i data-lucide="x"></i> Clear Cart
        </button>

        <div id="payment">
            <h3>Complete Your Payment</h3>
            <div style="text-align: center; font-size: 18px;">
                Send **exactly**
                <strong id="btcAmount" style="color:var(--accent); margin: 0 5px;">0 BTC</strong> 
                (approx. <span id="usdAmount" style="color:var(--muted);">$0.00</span>)
            </div>
            <img id="qrCode" src="" alt="QR Code">
            <div class="address" id="btcAddress">
                <i data-lucide="qr-code"></i>
            </div>
            <a id="walletLink" class="btn-full btn-primary" target="_blank">
                <i data-lucide="wallet"></i> Open in Wallet App
            </a>
            <p style="text-align:center;color:var(--muted);font-size:14px">Payment auto-detected in ~10–60 seconds.<br>Do not close this page until confirmed.</p>
        </div>

        <div id="success" class="success" style="display:none;">
            <i data-lucide="check-circle" style="width:36px; height:36px; margin-bottom:10px;"></i>
            PAYMENT CONFIRMED!
            <p>Your order is being processed. Check your email for delivery details.</p>
        </div>
    </div>

    <script>
        lucide.createIcons();
        
        function getCart(){
            return JSON.parse(localStorage.getItem('cart') || '[]');
        }

        function saveCart(cart){
             cart = cart.filter(item => (item.qty || 1) > 0);
             localStorage.setItem('cart', JSON.stringify(cart));
             update();
        }

        function updateQty(id, change) {
            let c = getCart();
            let ex = c.find(i => i.id === id);
            if(ex) {
                ex.qty = (ex.qty || 1) + change;
                if(ex.qty <= 0) {
                    c = c.filter(i => i.id !== id);
                }
            }
            saveCart(c);
        }

        function update(){
            const c = getCart();
            const i = document.getElementById("items");
            i.innerHTML = '';
            
            if(!c.length){
                i.innerHTML = `<p style="text-align:center;color:var(--muted);font-size:18px;padding:4rem">Your cart is empty. Time to find some gems!</p>`;
                document.getElementById("total").textContent = "$0.00";
                document.getElementById("checkout").disabled = true;
                document.getElementById("clearCart").disabled = true;
                return;
            }

            document.getElementById("checkout").disabled = false;
            document.getElementById("clearCart").disabled = false;
            
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
                            <div class="item-price"> $${p.toFixed(2)} × ${q} = **$ ${(p * q).toFixed(2)}**</div>
                            <div class="qty-controls">
                                <button onclick="updateQty(${x.id}, -1)" class="btn-secondary" style="padding: 5px 10px; border-radius: 8px;">-</button>
                                <span>${q}</span>
                                <button onclick="updateQty(${x.id}, 1)" class="btn-secondary" style="padding: 5px 10px; border-radius: 8px;">+</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            document.getElementById("total").textContent = "$" + t.toFixed(2);
            lucide.createIcons();
        }

        update();

        document.getElementById("checkout").onclick = async () => {
            const c = getCart();
            if(!c.length) return alert("Cart empty!");
            
            const total = c.reduce((s, x) => s + (parseFloat(x.price) || 0) * (x.qty || 1), 0).toFixed(2);
            
            const email = prompt(`Total: $${total}\nEnter your delivery email:`, ""); 
            
            if(!email || !email.includes("@")) return alert("A valid email address is required for delivery!");

            document.getElementById("checkout").disabled = true;
            document.getElementById("checkout").innerHTML = '<i data-lucide="loader"></i> Processing...';
            lucide.createIcons();

            const res = await fetch("/api/checkout", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({email, cart: c})
            }).then(r => r.json());

            document.getElementById("checkout").innerHTML = '<i data-lucide="bitcoin"></i> Pay with Bitcoin';
            lucide.createIcons();
            
            if(!res.ok) {
                 document.getElementById("checkout").disabled = false;
                 return alert("Error during checkout: " + (res.error || "Unknown"));
            }

            document.getElementById("btcAmount").textContent = res.amount_btc + " BTC";
            document.getElementById("usdAmount").textContent = "$" + res.amount_usd;
            document.getElementById("btcAddress").innerHTML = '<i data-lucide="qr-code"></i>' + res.payment_address;
            document.getElementById("qrCode").src = res.qr;
            document.getElementById("walletLink").href = res.wallet_uri;
            document.getElementById("payment").style.display = "flex";
            document.getElementById("checkout").style.display = "none";
            document.getElementById("clearCart").style.display = "none";
            
            localStorage.removeItem("cart"); 
            update();

            alert("Please send exactly " + res.amount_btc + " BTC to the address shown. Payment will be auto-confirmed.");

            let check = setInterval(async() => {
                try {
                    // This is a proxy check - a dedicated /api/check_payment?token=... would be better.
                    // For now, relies on the payment watcher thread changing server state.
                    const r = await fetch("/api/products").then(r => r.text()); 
                    
                    if (document.title.includes("paid")) {
                         clearInterval(check);
                         document.getElementById("payment").style.opacity = 0;
                         setTimeout(() => {
                             document.getElementById("payment").style.display = "none";
                             document.getElementById("success").style.display = "block";
                             document.getElementById("success").style.opacity = 1;
                         }, 300);
                    }
                } catch {}
            }, 5000);
        };

        document.getElementById("clearCart").onclick = () => {
            if(confirm("Are you sure you want to clear your entire cart?")){
                localStorage.removeItem("cart");
                update();
            }
        }
    </script>
</body>
</html>
""" 

LOGIN_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Admin Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        {SHARED_STYLE}
        body{{display:grid;place-items:center;height:100vh;margin:0;}}
        .box{{
            background:var(--card);
            padding:50px;
            border-radius:24px;
            width:420px;
            border:1px solid var(--border);
            backdrop-filter:blur(10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            animation: fadeIn 0.5s ease-out;
        }}
        h2{{
            text-align:center;margin-bottom:30px;
            background:linear-gradient(135deg,var(--accent),var(--accent2));
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            font-size:32px;font-weight:900;
        }}
        input,button{{
            padding:16px;margin:12px 0;width:100%;
            border-radius:14px;border:1px solid #3e3e4e;
            font-size:16px;transition:all 0.3s;
        }}
        input{{
            background:#1e1e2e;color:white;
        }}
        input:focus{{
            border-color:var(--accent);
            box-shadow:0 0 0 3px rgba(0,255,157,0.3);
            outline:none;
        }}
        button{{
            background:var(--accent);color:black;font-weight:800;cursor:pointer;
        }}
        .status-message{{
            padding:15px;border-radius:12px;margin-bottom:15px;font-weight:600;
            text-align:center;
        }}
        .error{{background:#451a1a;color:var(--danger);border:1px solid var(--danger)}}
        .success{{background:#123a2a;color:var(--success);border:1px solid var(--success)}}
        @keyframes fadeIn {from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
    </style>
</head>
<body>
    <div class="box">
        <div class="logo" style="justify-content:center; margin-bottom: 20px;">
            <i data-lucide="gem"></i>
            VIXN
        </div>
        {% if status %}
            <div class="status-message {{ 'error' if status.type == 'error' else 'success' }}">
                {{ status.message }}
            </div>
        {% endif %}
        <h2>Admin Panel</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">
                <i data-lucide="log-in"></i> Login
            </button>
        </form>
    </div>
    <script>lucide.createIcons();</script>
</body>
</html>
""" 

ADMIN_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIXN • Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        {SHARED_STYLE}
        body{{padding:2rem}}
        .c{{max-width:1400px;margin:auto}}
        h1{{
            font-size:40px;margin-bottom:30px;font-weight:900;
            background:linear-gradient(135deg,var(--accent),var(--accent2));
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        }}
        .header-actions{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;gap:10px;}}
        .p{{
            background:var(--card);
            padding:30px;
            border-radius:20px;
            margin:20px 0;
            border:1px solid var(--border);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}
        .p:hover{{border-color:var(--accent2);}}
        h2{{font-size:24px;margin-bottom:20px;font-weight:700;}}
        input,textarea,button{{
            padding:16px;margin:10px 0;border-radius:14px;
            width:100%;background:#1e1e2e;color:white;
            border:1px solid #3e3e4e;transition:all 0.3s;
        }}
        input:focus, textarea:focus{{
            border-color:var(--accent);
            box-shadow:0 0 0 3px rgba(0,255,157,0.2);
            outline:none;
        }}
        button[type="submit"]{{
            background:var(--accent);color:black;font-weight:800;cursor:pointer;
        }}
        .del{{background:var(--danger)!important;color:white!important;}}
        .del:hover{{background:#dc2626!important;box-shadow: 0 8px 15px rgba(239, 68, 68, 0.3);}}
        table{{width:100%;border-collapse:separate;border-spacing:0;margin-top:20px;border-radius:14px;overflow:hidden;}}
        th,td{{padding:15px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05);}}
        th{{background:#12121e;font-weight:700;text-transform:uppercase;font-size:14px;letter-spacing:0.5px;}}
        tr:last-child td{{border-bottom:none;}}
        img{{width:60px;height:60px;object-fit:cover;border-radius:10px;}}
        .paid{{color:var(--success);font-weight:700;}}
        .pending{{color:#fb923c;font-weight:700;}}
        .delete-btn{{
            background:var(--danger);color:white;border:none;
            padding:8px 16px;border-radius:10px;cursor:pointer;font-weight:600;
            transition:opacity 0.3s;
        }}
        .delete-btn:hover{{opacity:0.8;}}
        .status-message{{
            padding:15px;border-radius:12px;margin-bottom:20px;font-weight:600;
            text-align:center;
            animation: slideIn 0.5s ease-out;
        }}
        .error-status{{background:#451a1a;color:var(--danger);border:1px solid var(--danger)}}
        .success-status{{background:#123a2a;color:var(--success);border:1px solid var(--success)}}
        @keyframes slideIn {from{opacity:0;transform:translateY(-10px);}to{opacity:1;transform:translateY(0);}}
        .col-span-2 {grid-column: span 2;}
        .grid-2 {display: grid; grid-template-columns: 1fr 1fr; gap: 20px;}
        
        .staged-email {
            background: #2e2e4e;
            border: 2px solid var(--accent2);
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 20px;
        }
        .staged-email p {margin-bottom: 10px;}
        .staged-email strong {color: var(--accent);}
        .staged-email textarea {
            background: #1e1e2e;
            border: 1px solid #4e4e6e;
            color: white;
            padding: 10px;
            border-radius: 8px;
            width: 100%;
            min-height: 150px;
            font-family: monospace;
            white-space: pre-wrap; /* Preserve wrapping */
        }
    </style>
</head>
<body>
    <div class="c">
        <h1>VIXN • Admin Panel</h1>
        
        <div class="header-actions">
            <a href="/admin/logout" class="btn del">
                <i data-lucide="log-out"></i> Logout
            </a>
            <a href="/" class="btn btn-secondary">
                <i data-lucide="store"></i> View Shop
            </a>
        </div>
        
        {% if status %}
            <div class="status-message {{ 'error-status' if status.type == 'error' else 'success-status' }}">
                {{ status.message }}
            </div>
        {% endif %}

        {% if staged_email %}
        <div class="staged-email">
            {% if staged_email.error %}
                <div class="status-message error-status">
                    <i data-lucide="alert-triangle"></i> Email Staging Error: {{ staged_email.error }}
                </div>
            {% else %}
                <div class="status-message success-status">
                    <i data-lucide="mail"></i> Email Drafted! **Copy the content below to send it yourself.**
                </div>
                <p><strong>To:</strong> {{ staged_email.recipient }}</p>
                <p><strong>Subject:</strong> {{ staged_email.subject }}</p>
                <p><strong>Body:</strong></p>
                <textarea readonly rows="10">{{ staged_email.body }}</textarea>
            {% endif %}
        </div>
        {% endif %}

        <div class="grid-2">
            <div class="p">
                <h2>Add New Product</h2>
                <form id="f" enctype="multipart/form-data">
                    <input type="text" name="name" placeholder="Name" required>
                    <input type="number" name="price" placeholder="Price (USD)" step="0.01" required>
                    <textarea name="description" placeholder="Description" rows="3"></textarea>
                    <input type="url" name="image" placeholder="Image URL (Optional)">
                    <label style="display:block;margin:10px 0;color:var(--muted);font-size:14px;">OR Upload Image File:</label>
                    <input type="file" name="image_file" accept="image/*" style="background:#2e2e3e;">
                    <button type="submit">
                        <i data-lucide="plus"></i> Add Product
                    </button>
                </form>
            </div>

            <div class="p">
                <h2>Draft Customer Email</h2>
                <form id="email-f" method="POST" action="{{ url_for('stage_email_route') }}">
                    <input type="email" name="recipient" placeholder="Recipient Email (e.g., customer@example.com)" required>
                    <input type="text" name="subject" placeholder="Subject" required>
                    <textarea name="body" placeholder="Email Body/Message" rows="5" required></textarea>
                    <button type="submit">
                        <i data-lucide="file-text"></i> Draft Email
                    </button>
                </form>
            </div>
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
                            <button class="delete-btn" onclick="deleteProduct({{ p.id }})">
                                <i data-lucide="trash-2" style="width:18px;height:18px;"></i>
                            </button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="p col-span-2">
            <h2>Purchases ({{ purchases|length }})</h2>
            <div style="max-height: 500px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr><th>Date</th><th>Email</th><th>USD</th><th>BTC</th><th>Status</th><th>TXID</th></tr>
                    </thead>
                    <tbody>
                        {% for p in purchases | reverse %}
                        <tr>
                            <td>{{ p.timestamp[:10] }}<br>{{ p.timestamp[11:16] }}</td>
                            <td>{{ p.email }}</td>
                            <td>${{ p.total_usd }}</td>
                            <td>{{ p.total_btc }}</td>
                            <td class="{{ 'paid' if p.status == 'paid' else 'pending' }}">{{ p.status.upper() }}</td>
                            <td>{% if p.txid %}<a href="https://blockstream.info/tx/{{ p.txid }}" target="_blank" style="color:var(--accent); text-decoration:none;">{{ p.txid[:8] }}...</a>{% else %}-{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        lucide.createIcons();

        document.getElementById("f").onsubmit = e => {
            e.preventDefault();
            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> Adding...';
            lucide.createIcons();

            fetch('/api/add_product', {
                method: 'POST',
                body: new FormData(e.target)
            })
            .then(r => r.json())
            .then(d => {
                if(d.ok) {
                    location.reload();
                } else {
                    alert("Error: " + d.error);
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i data-lucide="plus"></i> Add Product';
                    lucide.createIcons();
                }
            })
            .catch(err => {
                 alert("Network Error: " + err);
                 submitBtn.disabled = false;
                 submitBtn.innerHTML = '<i data-lucide="plus"></i> Add Product';
                 lucide.createIcons();
            });
        }
        
        function deleteProduct(id) {
            if (confirm("Permanently delete product ID " + id + "?")) {
                fetch('/api/delete_product', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id})
                })
                .then(r => r.json())
                .then(d => {
                    if (d.ok) {
                        // Use the provided redirect if available (for better status message handling)
                        window.location.href = d.redirect || '/admin'; 
                    } else {
                        alert("Error deleting: " + d.error);
                    }
                })
                .catch(err => alert("Network Error: " + err));
            }
        }
    </script>
</body>
</html>
""" 

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"VIXN 2025 AUTO-CONFIRM SHOP RUNNING ON PORT {port}")
    print(f"BTC Wallet: {BTC_WALLET}")
    app.run(host="0.0.0.0", port=port, debug=False)
