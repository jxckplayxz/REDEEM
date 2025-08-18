from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        body {
            font-family: 'Inter', sans-serif;
            background: #121212;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            margin: 0;
            min-height: 100vh;
        }

        h1 {
            color: #00ffff;
            margin-bottom: 20px;
            font-size: 2.2rem;
            text-shadow: 0 0 8px #00ffff;
        }

        form {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 700px;
        }

        input[type="password"], textarea {
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 12px;
            border: none;
            font-size: 16px;
            outline: none;
            width: 100%;
            background: #1e1e1e;
            color: #fff;
            box-shadow: inset 0 0 8px #000;
        }

        textarea {
            min-height: 80px;
            resize: vertical;
        }

        button {
            padding: 15px;
            background: linear-gradient(90deg, #00ffff, #00cccc);
            border: none;
            border-radius: 12px;
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

        #adminPanel {
            width: 100%;
            max-width: 700px;
            margin-top: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        #updateForm {
            display: flex;
            flex-direction: column;
        }

        .section {
            background: #1f1f1f;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
        }

        .section h2 {
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.5rem;
            color: #00ffff;
            text-shadow: 0 0 6px #00ffff;
        }

        #updates, #previousMessages {
            max-height: 250px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .update {
            background: #2a2a2a;
            padding: 12px 18px;
            border-radius: 12px;
            word-wrap: break-word;
            box-shadow: 0 0 8px rgba(0, 255, 255, 0.2);
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
        <div class="section">
            <h2>Add New Update</h2>
            <form id="updateForm">
                <textarea id="newUpdate" placeholder="Enter update text..." required></textarea>
                <textarea id="newNotification" placeholder="Enter notification text (optional)"></textarea>
                <button type="submit">Add Update</button>
            </form>
        </div>

        <div class="section">
            <h2>Recent Updates</h2>
            <div id="updates"></div>
        </div>

        <div class="section">
            <h2>Previous Messages</h2>
            <div id="previousMessages"></div>
        </div>
    </div>

    <script>
        const loginForm = document.getElementById("loginForm");
        const adminPanel = document.getElementById("adminPanel");

        loginForm.addEventListener("submit", function(e) {
            e.preventDefault();
            if(document.getElementById("password").value === "{{password}}") {
                loginForm.style.display = "none";
                adminPanel.style.display = "flex";
                fetchUpdates();
            } else {
                alert("Incorrect password!");
            }
        });

        async function fetchUpdates() {
            let res = await fetch("/updates.json");
            let data = await res.json();
            const container = document.getElementById("updates");
            const previousContainer = document.getElementById("previousMessages");
            container.innerHTML = "";
            previousContainer.innerHTML = "";

            if (Array.isArray(data) && data.length > 0) {
                data.forEach((u) => {
                    let div = document.createElement("div");
                    div.className = "update";
                    div.textContent = "Update: " + u.message + (u.notification ? " | Notification: " + u.notification : "");
                    container.appendChild(div);

                    let prevDiv = document.createElement("div");
                    prevDiv.className = "update";
                    prevDiv.textContent = "Update: " + u.message + (u.notification ? " | Notification: " + u.notification : "");
                    previousContainer.prepend(prevDiv);
                });
            } else {
                container.innerHTML = "<div class='update'>No updates yet.</div>";
            }
        }

        document.getElementById("updateForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            let msg = document.getElementById("newUpdate").value;
            let notif = document.getElementById("newNotification").value;
            await fetch("/add", { 
                method: "POST", 
                headers: {"Content-Type": "application/json"}, 
                body: JSON.stringify({ message: msg, notification: notif }) 
            });
            document.getElementById("newUpdate").value = "";
            document.getElementById("newNotification").value = "";
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
        return jsonify(updates[-1])  # send only the latest update
    return jsonify({"message": "", "notification": ""})


@app.route("/add", methods=["POST"])
def add_update():
    data = request.get_json()
    update = {"message": data.get("message", "")}
    notif = data.get("notification", "")
    if notif.strip():  # only save if not blank
        update["notification"] = notif
    updates.append(update)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
