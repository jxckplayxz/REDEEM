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
        body { font-family: Arial, sans-serif; margin: 30px; background: #121212; color: #eee; }
        h1 { color: #00ffff; }
        .update { border: 1px solid #00ffff; padding: 10px; margin: 10px 0; border-radius: 6px; }
        input, select { padding: 6px; margin: 5px 0; }
        button { padding: 6px 10px; background: #00ffff; border: none; color: #000; cursor: pointer; border-radius: 4px; }
        button:hover { background: #00cccc; }
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
            <input type="text" id="newUpdate" placeholder="Enter update message" required>
            <select id="color">
                <option value="white">White</option>
                <option value="yellow">Yellow</option>
                <option value="cyan">Cyan</option>
                <option value="red">Red</option>
                <option value="green">Green</option>
            </select>
            <select id="size">
                <option value="16">Normal</option>
                <option value="20">Large</option>
                <option value="24">Bigger</option>
            </select>
            <label><input type="checkbox" id="bold"> Bold</label>
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
                div.innerHTML = `<span style="color:${u.color}; font-size:${u.size}px; font-weight:${u.bold?'bold':'normal'};">${u.message}</span>
                <button onclick="deleteUpdate(${i})">Delete</button>`;
                container.appendChild(div);
            });
        }

        async function deleteUpdate(index) {
            await fetch("/delete/" + index, { method: "DELETE" });
            fetchUpdates();
        }

        document.getElementById("updateForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let msg = document.getElementById("newUpdate").value;
            let color = document.getElementById("color").value;
            let size = parseInt(document.getElementById("size").value);
            let bold = document.getElementById("bold").checked;
            await fetch("/add", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify({ message: msg, color: color, size: size, bold: bold }) 
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
