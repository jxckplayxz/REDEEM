from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)

# Store updates in memory (can replace with file or database)
updates = []

# Password for admin panel
ADMIN_PASSWORD = "admin21"

# HTML panel with CSS formatting options
html_panel = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Updates Admin</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e1e;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            min-height: 100vh;
            margin: 0;
            padding: 40px 20px;
        }

        h1 {
            color: #00ffff;
            margin-bottom: 30px;
        }

        form {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 600px;
        }

        input[type="password"], textarea {
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border: none;
            font-size: 16px;
            outline: none;
            width: 100%;
        }

        textarea {
            min-height: 150px;
            resize: vertical;
            background: #2a2a2a;
            color: #fff;
        }

        button {
            padding: 15px;
            background: linear-gradient(90deg, #00ffff, #00cccc);
            border: none;
            border-radius: 8px;
            color: #000;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }

        button:hover {
            transform: scale(1.05);
            background: linear-gradient(90deg, #00cccc, #00aaaa);
        }

        #updates {
            margin-top: 30px;
            width: 100%;
            max-width: 600px;
        }

        .update {
            background: #2a2a2a;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <h1>Live Updates Admin</h1>
    <form id="loginForm">
        <input type="password" id="password" placeholder="Enter password" required>
        <button type="submit">Login</button>
    </form>

    <div id="adminPanel" style="display:none;">
        <form id="updateForm">
            <textarea id="newUpdate" placeholder="Enter your message here..." required></textarea>
            <button type="submit">Add Update</button>
        </form>
        <div id="updates"></div>
    </div>

    <script>
        const loginForm = document.getElementById("loginForm");
        const adminPanel = document.getElementById("adminPanel");

        loginForm.addEventListener("submit", function(e) {
            e.preventDefault();
            if(document.getElementById("password").value === "{{password}}") {
                loginForm.style.display = "none";
                adminPanel.style.display = "block";
                fetchUpdates();
            } else {
                alert("Incorrect password!");
            }
        });

        async function fetchUpdates() {
            let res = await fetch("/updates.json");
            let data = await res.json();
            let container = document.getElementById("updates");
            container.innerHTML = "";
            data.forEach((u, i) => {
                let div = document.createElement("div");
                div.className = "update";
                div.textContent = u.message;
                container.appendChild(div);
            });
        }

        document.getElementById("updateForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let msg = document.getElementById("newUpdate").value;
            await fetch("/add", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify({ message: msg }) 
            });
            document.getElementById("newUpdate").value = "";
            fetchUpdates();
        });
    </script>
</body>
</html>

"""

@app.route("/")
def admin_panel():
    return render_template_string(html_panel, password=ADMIN_PASSWORD)

@app.route("/updates.json", methods=["GET"])
def get_updates_json():

    if updates:
        # Return only the latest update
        return jsonify(updates[-1])
    
    # If no updates exist yet
    return jsonify({
        "message": "No updates yet.",
        "color": "white",
        "size": 16,
        "bold": False
    })


@app.route("/add", methods=["POST"])
def add_update():
    data = request.get_json()
    updates.append(data)
    return jsonify({"success": True})

@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_update(index):
    if 0 <= index < len(updates):
        updates.pop(index)
    return jsonify({"success": True})
    
latest_message = {"message": "No messages yet."}

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    msg = data.get("message")
    if msg:
        updates.append(msg)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No message sent"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
