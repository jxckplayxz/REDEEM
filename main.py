import os
from flask import Flask, render_template_string

app = Flask(__name__)

# Basic Python Flask application to serve the single HTML file.
# All application logic (Firebase, UI rendering) is handled client-side
# in the index.html using JavaScript.

@app.route('/')
def index():
    """
    Renders the index.html content.
    The HTML content is read directly from the index.html file.
    """
    try:
        # Read the content of the index.html file
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "Error: index.html not found.", 404
    except Exception as e:
        return f"An error occurred: {e}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
