from flask import Flask, session, redirect, url_for, render_template_string, request
import time

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Special Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #121212;
            color: white;
            text-align: center;
            padding-top: 100px;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 14px 28px;
            font-size: 18px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        button:disabled {
            background: grey;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <h1>Welcome to the Secret Button Page</h1>
    <p>Click the button when it's ready.</p>
    <form method="post">
        <button type="submit" {{ 'disabled' if not ready else '' }}>Do Action</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    # Check if first visit
    if "visited_once" not in session:
        session["visited_once"] = True
        return redirect(url_for("step_two"))

    # Check if timer is set
    if "start_time" not in session:
        session["start_time"] = time.time()
        return redirect(url_for("index"))

    elapsed = time.time() - session["start_time"]
    ready = elapsed >= 60  # 1 min wait

    if request.method == "POST" and ready:
        return "✅ Button Action Executed!"

    return render_template_string(HTML_TEMPLATE, ready=ready)


@app.route("/step-two")
def step_two():
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
