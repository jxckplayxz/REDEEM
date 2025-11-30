# ================================================
# CODEVAULT PRO v4 – FULL SINGLE-FILE (FLOATY NAVBAR + AUTO-REGISTER)
# ================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from markupsafe import Markup 

# ====================== APP SETUP ======================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'codevault-final-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///codevault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ====================== MODELS ======================
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(100), default="Coder")
    password = db.Column(db.String(200))
    auto_save = db.Column(db.Boolean, default=True)
    dark_mode = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship('User', backref='repositories')

class CodeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, default="")
    repo_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    repo = db.relationship('Repository', backref='files')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====================== FIX OLD DB ======================
def fix_database():
    if not os.path.exists('codevault.db'):
        return
    conn = sqlite3.connect('codevault.db')
    c = conn.cursor()
    for col, sql in [
        ("auto_save", "BOOLEAN DEFAULT 1"),
        ("dark_mode", "BOOLEAN DEFAULT 1")
    ]:
        try:
            c.execute(f"ALTER TABLE user ADD COLUMN {col} {sql}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

# ====================== STARTUP (Removed demo user) ======================
with app.app_context():
    db.create_all()
    fix_database()
    # Removed the creation of 'demo' user to make it a real-user system.

# ====================== NAVBAR (Floaty CSS Applied) ======================
NAVBAR_TEMPLATE = '''
<div class="h-20"></div> <nav class="bg-gray-900/90 backdrop-blur-sm border border-gray-800 shadow-xl rounded-xl p-4 flex justify-between items-center fixed top-0 left-0 right-0 z-50 mx-auto mt-4 w-[95%] lg:w-[90%]">
    <div class="flex items-center gap-3">
        <i data-lucide="code" class="w-8 h-8 text-indigo-400"></i>
        <a href="/" class="text-2xl font-bold text-indigo-400 hover:text-indigo-300">CodeVault</a>
    </div>
    <div class="flex items-center gap-6">
        <a href="/explore" class="text-gray-300 hover:text-white flex items-center gap-1">
            <i data-lucide="compass" class="w-5 h-5"></i> Explore
        </a>
        {% if current_user.is_authenticated %}
        <a href="/dashboard" class="text-gray-300 hover:text-white flex items-center gap-1">
            <i data-lucide="folder" class="w-5 h-5"></i> My Code
        </a>
        <a href="/settings" class="text-gray-300 hover:text-white flex items-center gap-1">
            <i data-lucide="settings" class="w-5 h-5"></i> Settings
        </a>
        <a href="/logout" class="text-red-400 hover:text-red-300 flex items-center gap-1">
            <i data-lucide="log-out" class="w-5 h-5"></i> Logout
        </a>
        {% else %}
        <a href="/login" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg font-bold flex items-center gap-1">
            <i data-lucide="log-in" class="w-5 h-5"></i> Login
        </a>
        {% endif %}
    </div>
</nav>
<script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
<script>lucide.createIcons();</script>
'''

def render_navbar():
    # render_template_string executes the Jinja logic, and we use Markup to mark it as safe HTML
    return Markup(render_template_string(NAVBAR_TEMPLATE, current_user=current_user))

app.jinja_env.globals['navbar'] = render_navbar


# ====================== ROUTES ======================
@app.route('/')
def index():
    return redirect('/explore')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            # SCENARIO 1 & 2: User exists
            if check_password_hash(user.password, password):
                # SCENARIO 1: Successful login
                login_user(user)
                flash('Login successful!')
                return redirect('/dashboard')
            else:
                # SCENARIO 2: Incorrect password
                flash('Incorrect password for existing account.')
                return redirect(url_for('login'))
        else:
            # SCENARIO 3: User does not exist, auto-register them
            if len(username) < 3 or len(password) < 6:
                flash('Username must be at least 3 characters and password at least 6 characters.')
                return redirect(url_for('login'))
                
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                display_name=username.capitalize() # Default display name
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Log the newly created user in
            login_user(new_user)
            flash(f'Welcome! Account for "{username}" created and you are logged in.')
            return redirect('/dashboard')

    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Login/Register - CodeVault</title><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex items-center justify-center p-4">
        <div class="bg-gray-800 p-10 rounded-2xl w-full max-w-md shadow-2xl">
            <h1 class="text-5xl font-bold text-center text-indigo-400 mb-8">CodeVault</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="mb-6 p-4 rounded-xl bg-red-800 text-red-200">
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="post" class="space-y-6">
                <input name="username" placeholder="Username (3+ chars)" required class="w-full px-6 py-4 bg-gray-700 rounded-xl text-lg">
                <input name="password" type="password" placeholder="Password (6+ chars)" required class="w-full px-6 py-4 bg-gray-700 rounded-xl text-lg">
                <button class="w-full py-4 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-xl">Login / Register</button>
            </form>
            <p class="text-gray-400 text-sm mt-4 text-center">If the username is new, an account will be automatically created.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/explore')
def explore():
    repos = Repository.query.filter_by(is_public=True).order_by(Repository.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Explore</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="p-6 max-w-6xl mx-auto flex-1 w-full"> 
            <h1 class="text-4xl font-bold mb-8">Public Repositories</h1>
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-indigo-500 transition">
                    <h3 class="text-2xl font-bold mb-2">{{ r.name }}</h3>
                    <p class="text-gray-400 text-sm mb-4">{{ r.description or 'No description' }}</p>
                    <div class="text-sm text-gray-500">@{{ r.owner.username }} • {{ r.files|length }} files</div>
                </a>
                {% endfor %}
            </div>
            {% if not repos %}<p class="text-center text-3xl text-gray-500 mt-20">No public repos yet!</p>{% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repos=repos, current_user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    repos = Repository.query.filter_by(owner_id=current_user.id).order_by(Repository.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Dashboard</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="p-6 max-w-6xl mx-auto flex-1 w-full">
            <a href="/repo/new" class="inline-block bg-indigo-600 hover:bg-indigo-700 px-8 py-4 rounded-xl font-bold text-xl mb-8">+ New Repository</a>
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-8 rounded-xl border border-gray-700 hover:border-indigo-500 transition">
                    <h3 class="text-2xl font-bold mb-2">{{ r.name }}</h3>
                    <p class="text-gray-400 text-sm">{{ r.description or 'No description' }}</p>
                    <div class="text-sm text-gray-500 mt-4">{{ r.files|length }} files • {% if r.is_public %}Public{% else %}Private{% endif %}</div>
                </a>
                {% endfor %}
            </div>
            {% if not repos %}<p class="text-center text-3xl text-gray-500 mt-20">You haven't created any repositories yet.</p>{% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repos=repos, current_user=current_user)

# ====================== NEW REPO ======================
@app.route('/repo/new', methods=['GET', 'POST'])
@login_required
def new_repo():
    if request.method == 'POST':
        repo = Repository(
            name=request.form['name'] or 'Untitled Repo',
            description=request.form.get('description', ''),
            is_public='public' in request.form,
            owner_id=current_user.id
        )
        db.session.add(repo)
        db.session.flush()
        db.session.add(CodeFile(name="main.txt", content="# Welcome to your repo!", repo=repo))
        db.session.commit()
        return redirect(f'/repo/{repo.id}')
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>New Repo</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="flex-1 flex items-center justify-center p-6">
            <form method="post" class="bg-gray-800 p-10 rounded-2xl w-full max-w-lg space-y-6">
                <h1 class="text-4xl font-bold">New Repository</h1>
                <input name="name" placeholder="Repository Name" required class="w-full px-6 py-4 bg-gray-700 rounded-xl">
                <textarea name="description" placeholder="Description (optional)" class="w-full px-6 py-4 bg-gray-700 rounded-xl h-32"></textarea>
                <label class="flex items-center gap-3 text-lg"><input type="checkbox" name="public" checked class="w-6 h-6"> Public</label>
                <button class="w-full py-4 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-xl">Create Repository</button>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', current_user=current_user)

# ====================== REPO EDITOR ======================
@app.route('/repo/<int:repo_id>')
@login_required
def editor(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.owner_id != current_user.id:
        abort(403)
    file_id = request.args.get('file', type=int)
    current_file = CodeFile.query.get(file_id) if file_id else (repo.files[0] if repo.files else None)
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>{{ repo.name }} - CodeVault</title><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="flex-1 flex flex-col lg:flex-row">
            <div class="w-full lg:w-80 bg-gray-800 border-r border-gray-700 p-6 overflow-y-auto">
                <h2 class="text-2xl font-bold mb-6">{{ repo.name }}</h2>
                <div class="space-y-3">
                    {% for f in repo.files %}
                    <a href="/repo/{{ repo.id }}?file={{ f.id }}" class="block p-4 rounded-lg font-medium {% if f.id == (current_file.id if current_file else 0) %}bg-indigo-600 text-white{% else %}bg-gray-700 hover:bg-gray-600{% endif %}">
                        {{ f.name }}
                    </a>
                    {% endfor %}
                    <form action="/file/new" method="post" class="mt-8">
                        <input type="hidden" name="repo_id" value="{{ repo.id }}">
                        <div class="flex gap-2">
                            <input name="name" placeholder="new-file.txt" required class="flex-1 px-4 py-3 bg-gray-700 rounded-l-lg">
                            <button class="px-6 bg-indigo-600 hover:bg-indigo-700 rounded-r-lg font-bold">+</button>
                        </div>
                    </form>
                </div>
            </div>
            <div class="flex-1 flex flex-col">
                {% if current_file %}
                <div class="p-5 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
                    <h3 class="text-2xl font-mono font-bold">{{ current_file.name }}</h3>
                    <div class="flex items-center gap-4">
                        <button onclick="copyRaw()" class="px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium">Copy Raw Link</button>
                        <span id="status" class="text-green-400 font-medium">Saved</span>
                    </div>
                </div>
                <textarea id="code" class="flex-1 p-6 font-mono text-sm bg-gray-900 outline-none" spellcheck="false">{{ current_file.content }}</textarea>
                <script>
                    const autoSave = {{ 'true' if current_user.auto_save else 'false' }};
                    let timer;
                    document.getElementById('code').addEventListener('input', function() {
                        if (!autoSave) return;
                        document.getElementById('status').textContent = 'saving...';
                        clearTimeout(timer);
                        timer = setTimeout(() => {
                            fetch('/file/save', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                                body: 'file_id={{ current_file.id }}&content=' + encodeURIComponent(this.value)
                            }).then(() => document.getElementById('status').textContent = 'saved');
                        }, 1000);
                    });
                    function copyRaw() {
                        navigator.clipboard.writeText(location.origin + '/raw/{{ repo.id }}/{{ current_file.id }}');
                        alert('Raw link copied to clipboard!');
                    }
                </script>
                {% else %}
                <div class="flex-1 flex items-center justify-center text-gray-500 text-3xl">
                    Create a file to start coding!
                </div>
                {% endif %}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repo=repo, current_file=current_file, current_user=current_user)

# ====================== SAVE FILE ======================
@app.route('/file/save', methods=['POST'])
@login_required
def save_file():
    f = CodeFile.query.get_or_404(request.form['file_id'])
    if f.repo.owner_id != current_user.id:
        abort(403)
    f.content = request.form['content']
    db.session.commit()
    return 'saved'

# ====================== NEW FILE ======================
@app.route('/file/new', methods=['POST'])
@login_required
def new_file():
    repo = Repository.query.get_or_404(request.form['repo_id'])
    if repo.owner_id != current_user.id:
        abort(403)
    filename = request.form['name'].strip()
    if not filename:
        flash("Filename cannot be empty.")
        return redirect(f'/repo/{repo.id}')
    f = CodeFile(name=filename, content="", repo=repo)
    db.session.add(f)
    db.session.commit()
    return redirect(f'/repo/{repo.id}?file={f.id}')

# ====================== RAW FILE DOWNLOAD ======================
@app.route('/raw/<int:repo_id>/<int:file_id>')
def raw(repo_id, file_id):
    f = CodeFile.query.get_or_404(file_id)
    # Only allow if public or owner
    if not f.repo.is_public and (not current_user.is_authenticated or f.repo.owner_id != current_user.id):
        abort(403)

    # CRITICAL: Force download to prevent XSS
    return Response(
        f.content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename="{f.name}"'
        }
    )

# ====================== SETTINGS ======================
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.display_name = request.form['display_name']
        current_user.auto_save = 'auto_save' in request.form
        if request.form.get('password'):
            current_user.password = generate_password_hash(request.form['password'])
        db.session.commit()
        flash('Settings saved!')
        return redirect(url_for('settings'))

    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head>
        <title>Settings - CodeVault</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="p-10 max-w-2xl mx-auto flex-1 w-full">
            <h1 class="text-4xl font-bold mb-10">Settings</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="mb-6 p-4 rounded-xl bg-green-800 text-green-200">
                        {% for message in messages %}
                            <p>{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="post" class="bg-gray-800 p-8 rounded-2xl space-y-8">
                <div>
                    <label class="block text-xl mb-3">Display Name</label>
                    <input name="display_name" value="{{ current_user.display_name }}" class="w-full px-6 py-4 bg-gray-700 rounded-xl">
                </div>
                <div>
                    <label class="block text-xl mb-3">New Password (optional)</label>
                    <input name="password" type="password" placeholder="Leave blank to keep current" class="w-full px-6 py-4 bg-gray-700 rounded-xl">
                </div>
                <label class="flex items-center gap-4 text-xl">
                    <input type="checkbox" name="auto_save" {% if current_user.auto_save %}checked{% endif %} class="w-8 h-8">
                    <span>Enable Auto-save</span>
                </label>
                <button class="w-full py-5 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-xl">Save Settings</button>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', current_user=current_user)

# ====================== MAIN ======================
if __name__ == '__main__':
    print("CodeVault PRO v4 is running! (Real User System)")
    print("Visit: http://127.0.0.1:5000")
    print("To get started, use any username/password to auto-register.")
    app.run(host='0.0.0.0', port=5000, debug=False)
