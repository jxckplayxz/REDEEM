import json
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
# Render uses /opt/render/project/src/ by default, so we ensure the path is solid
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
    return render_template('index.html', sections=data['sections'])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    data = load_data()
    if request.method == 'POST':
        section_name = request.form.get('section_name')
        match_data = {
            "id": os.urandom(4).hex(),
            "title": request.form.get('title'),
            "url": request.form.get('url'),
            "thumb": request.form.get('thumb') or "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&q=80&w=1000"
        }
        
        # Logic to append to existing section or create new one
        section = next((s for s in data['sections'] if s['name'] == section_name), None)
        if section:
            section['matches'].append(match_data)
        else:
            data['sections'].append({"name": section_name, "matches": [match_data]})
        
        save_data(data)
        return redirect(url_for('admin'))
    
    return render_template('admin.html', sections=data['sections'])

@app.route('/delete/<match_id>')
def delete_match(match_id):
    data = load_data()
    for section in data['sections']:
        section['matches'] = [m for m in section['matches'] if m['id'] != match_id]
    
    # Remove empty sections
    data['sections'] = [s for s in data['sections'] if s['matches']]
    save_data(data)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    # Using port 5000 as requested
    app.run(debug=False, host='0.0.0.0', port=5000)
    
