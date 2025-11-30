import os
from flask import Flask, render_template
import json

app = Flask(__name__)

# Route for the main chat page
@app.route('/')
def index():
    """
    Renders the main chat interface, injecting environment-specific
    Firebase configuration into the HTML template.
    """
    # Retrieve mandatory environment variables, providing safe defaults
    app_id = os.environ.get('__app_id', 'default-chat-app-id')
    
    # We must retrieve the config as a JSON string and pass it as a string
    # for the JavaScript to parse.
    firebase_config_json = os.environ.get('__firebase_config', '{}')
    
    initial_auth_token = os.environ.get('__initial_auth_token', '')
    
    return render_template('index.html',
                           app_id=app_id,
                           firebase_config=firebase_config_json,
                           initial_auth_token=initial_auth_token)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"VIXN 2025 AUTO-CONFIRM SHOP RUNNING ON PORT {port}")
    print(f"BTC Wallet: {BTC_WALLET}")
    app.run(host="0.0.0.0", port=port, debug=False)