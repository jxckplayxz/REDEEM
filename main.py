from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Store updates in memory (can replace with file or database later)
updates = []

# HTML panel for adding/deleting updates
html_panel = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Updates Admin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; }
        .update { border: 1px solid #ccc; padding: 10px; margin: 10px 0; border-radius: 6px; }
        button { margin-left: 5px; }
    </style>
</head>
<body>
    <h1>Live Updates Admin</h1>
    <form id="updateForm">
        <input type="text" id="newUpdate" placeholder="Enter update message" required>
        <button type="submit">Add Update</button>
    </form>
    <div id="updates"></div>

    <script>
        async function fetchUpdates() {
            let res = await fetch("/updates.json");
            let data = await res.json();
            let container = document.getElementById("updates");
            container.innerHTML = "";
            data.forEach((u, i) => {
                let div = document.createElement("div");
                div.className = "update";
                div.innerHTML = `
                    ${u} 
                    <button onclick="deleteUpdate(${i})">Delete</button>
                `;
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
            await fetch("/add", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify({ update: msg }) 
            });
            document.getElementById("newUpdate").value = "";
            fetchUpdates();
        });

        fetchUpdates();
    </script>
</body>
</html>
"""

@app.route("/")
def admin_panel():
    return render_template_string(html_panel)

@app.route("/updates.json", methods=["GET"])
def get_updates_json():
    # Only return the latest update as a JSON object for Roblox script
    if updates:
        return jsonify({"message": updates[-1]})
    return jsonify({"message": "No updates yet."})

@app.route("/add", methods=["POST"])
def add_update():
    data = request.get_json()
    updates.append(data["update"])
    return jsonify({"success": True})

@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_update(index):
    if 0 <= index < len(updates):
        updates.pop(index)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
