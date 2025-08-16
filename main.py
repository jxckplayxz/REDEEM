from flask import Flask, request, jsonify

app = Flask(__name__)

# Store roles (in memory for now, could be database later)
user_roles = {}

# Default roles
default_role = "member"

# ✅ Get role for a user
@app.route("/get_role", methods=["GET"])
def get_role():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "No username provided"}), 400
    
    role = user_roles.get(username, default_role)
    return jsonify({"username": username, "role": role})

# ✅ Set role for a user
@app.route("/set_role", methods=["POST"])
def set_role():
    data = request.get_json()
    username = data.get("username")
    role = data.get("role")

    if not username or not role:
        return jsonify({"error": "Username and role required"}), 400

    user_roles[username] = role
    return jsonify({"message": f"Role for {username} set to {role}."})

# ✅ Create a new role type
@app.route("/create_role", methods=["POST"])
def create_role():
    data = request.get_json()
    role = data.get("role")
    if not role:
        return jsonify({"error": "Role required"}), 400
    # In real use: add to DB
    return jsonify({"message": f"Role '{role}' created."})

# ✅ Update a user's role
@app.route("/update_role", methods=["POST"])
def update_role():
    data = request.get_json()
    username = data.get("username")
    new_role = data.get("new_role")
    
    if username not in user_roles:
        return jsonify({"error": f"{username} not found"}), 404

    user_roles[username] = new_role
    return jsonify({"message": f"{username}'s role updated to {new_role}."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
