from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Store updates in memory
updates = []

html_panel = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Updates Admin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; background: #f0f2f5; }
        h1 { text-align: center; }
        .update { border: 1px solid #ccc; padding: 10px; margin: 10px 0; border-radius: 6px; background: #fff; }
        button { margin-left: 5px; }
        input, select { margin: 5px; }
    </style>
</head>
<body>
    <h1>Live Updates Admin</h1>
    <form id="updateForm">
        <input type="text" id="newUpdate" placeholder="Enter update message" required>
        <select id="textColor">
            <option value="black">Black</option>
            <option value="red">Red</option>
            <option value="green">Green</option>
            <option value="blue">Blue</option>
            <option value="orange">Orange</option>
            <option value="purple">Purple</option>
        </select>
        <select id="textSize">
            <option value="16px">Normal</option>
            <option value="20px">Large</option>
            <option value="24px">Extra Large</option>
        </select>
        <label>
            <input type="checkbox" id="bold"> Bold
        </label>
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
                div.style.color = u.color;
                div.style.fontSize = u.size;
                div.style.fontWeight = u.bold ? 'bold' : 'normal';
                div.textContent = u.text;
                let btn = document.createElement("button");
                btn.textContent = "Delete";
                btn.onclick = () => deleteUpdate(i);
                div.appendChild(btn);
                container.appendChild(div);
            });
        }

        async function deleteUpdate(index) {
            await fetch("/delete/" + index, { method: "DELETE" });
            fetchUpdates();
        }

        document.getElementById("updateForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let text = document.getElementById("newUpdate").value;
            let color = document.getElementById("textColor").value;
            let size = document.getElementById("textSize").value;
            let bold = document.getElementById("bold").checked;
            await fetch("/add", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify({ text, color, size, bold }) 
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
    # Return latest update with formatting
    if updates:
        return jsonify(updates[-1])
    return jsonify({"text": "No updates yet.", "color": "black", "size": "16px", "bold": False})

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
