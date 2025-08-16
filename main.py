# chat_api.py
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

messages = []  # store all chat messages

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    user = data.get("user")
    text = data.get("text")

    if not user or not text:
        return jsonify({"error": "Invalid data"}), 400

    msg = {
        "user": user,
        "text": text,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    messages.append(msg)
    return jsonify({"success": True, "message": msg})

@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify(messages[-50:])  # send only last 50 for performance

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
