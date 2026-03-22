import json
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATA_FILE = os.path.join(os.getcwd(), 'data.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"sections": []}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"sections": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    data = load_data()
    # Check for the secret access: ?admin=stream
    is_admin = request.args.get('admin') == 'stream'
    
    if is_admin:
        return render_template('admin.html', sections=data['sections'])
    return render_template('index.html', sections=data['sections'])

@app.route('/add_match', methods=['POST'])
def add_match():
    data = load_data()
    section_name = request.form.get('section_name')
    match_data = {
        "id": os.urandom(4).hex(),
        "title": request.form.get('title'),
        "url": request.form.get('url'),
        "thumb": request.form.get('thumb') or "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&q=80&w=1000"
    }
    
    section = next((s for s in data['sections'] if s['name'] == section_name), None)
    if section:
        section['matches'].append(match_data)
    else:
        data['sections'].append({"name": section_name, "matches": [match_data]})
    
    save_data(data)
    # Redirect back to the hidden admin view
    return redirect(url_for('index', admin='stream'))

@app.route('/delete/<match_id>')
def delete_match(match_id):
    data = load_data()
    for section in data['sections']:
        section['matches'] = [m for m in section['matches'] if m['id'] != match_id]
    data['sections'] = [s for s in data['sections'] if s['matches']]
    save_data(data)
    return redirect(url_for('index', admin='stream'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    
