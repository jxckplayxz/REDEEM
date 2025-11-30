# ================================================
# CODEVAULT PRO v8.3 – FINAL CONSOLIDATED CODE
# Ensures correct templating and admin structure.
# ================================================

from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from markupsafe import Markup 
import json 
import html
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ 
from pathlib import Path # Used for ensuring template paths exist

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
    is_admin = db.Column(db.Boolean, default=False)
    admin_note = db.Column(db.Text, nullable=True) 

class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('CodeFile', backref='repo', lazy='dynamic', cascade="all, delete-orphan") 
    owner = db.relationship('User', backref='repositories')

class CodeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, default="")
    repo_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====================== UTILITY / ADMIN DECORATORS ======================
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Forbidden
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def fix_database():
    if not os.path.exists('codevault.db'):
        return
    # Check if new columns exist and add them (manual migration)
    conn = sqlite3.connect('codevault.db')
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_admin' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        if 'admin_note' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN admin_note TEXT NULL")
        if 'auto_save' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN auto_save BOOLEAN DEFAULT 1")
        if 'dark_mode' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN dark_mode BOOLEAN DEFAULT 1")
            
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

# Maps file extension to common language for Prism highlighting and filtering
LANGUAGE_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.mjs': 'JavaScript', '.cjs': 'JavaScript',
    '.ts': 'TypeScript', '.html': 'HTML', '.htm': 'HTML', '.css': 'CSS',
    '.scss': 'CSS', '.less': 'CSS', '.json': 'JSON', '.md': 'Markdown', 
    '.markdown': 'Markdown', '.sh': 'Bash', '.txt': 'Text', '.c': 'C', 
    '.cpp': 'C++', '.java': 'Java', '.php': 'PHP'
}

def get_prism_language(filename):
    ext = os.path.splitext(filename)[1].lower()
    lang = LANGUAGE_MAP.get(ext)
    
    if lang == 'Python': return 'python'
    elif lang == 'JavaScript': return 'javascript'
    elif lang == 'HTML': return 'markup'
    elif lang == 'CSS': return 'css'
    elif lang == 'JSON': return 'json'
    elif lang == 'Markdown': return 'markdown'
    elif lang == 'Bash': return 'bash'
    elif lang in ['C', 'C++', 'Java', 'PHP']: return lang.lower()
    else: return 'clike' 

def get_file_icon(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.py', '.js', '.mjs', '.cjs', '.ts']: return 'file-code'
    elif ext in ['.html', '.htm']: return 'file-html'
    elif ext in ['.css', '.scss', '.less']: return 'file-css'
    elif ext in ['.json']: return 'file-json'
    elif ext in ['.md', '.markdown']: return 'file-text'
    elif ext in ['.sh']: return 'terminal'
    else: return 'file-text'

def get_repo_languages(repo):
    """Returns a list of unique languages present in a repository."""
    languages = set()
    for f in repo.files:
        ext = os.path.splitext(f.name)[1].lower()
        lang = LANGUAGE_MAP.get(ext, 'Other')
        languages.add(lang)
    return sorted(list(languages))

app.jinja_env.globals['get_file_icon'] = get_file_icon
app.jinja_env.globals['get_repo_languages'] = get_repo_languages
app.jinja_env.globals['LANGUAGE_MAP'] = LANGUAGE_MAP


# ====================== STARTUP ======================
with app.app_context():
    # Ensure the templates folder exists to prevent deployment issues
    Path('templates').mkdir(exist_ok=True)
    db.create_all()
    fix_database() # Applies migration logic
    
    # Ensure the first user created is automatically set as the Admin
    first_user = User.query.order_by(User.id.asc()).first()
    if first_user and not first_user.is_admin:
        first_user.is_admin = True
        first_user.display_name = "👑 Admin"
        db.session.commit()
        print(f"User '{first_user.username}' promoted to Admin.")


# ====================== NAVBAR FUNCTION (FIXED) ======================
# This is the function that is called by {% include 'navbar.html' %} inside the template strings
def render_navbar():
    # Renders the content from the dedicated templates/navbar.html file
    # This is the line that will fail if templates/navbar.html is missing
    return render_template('navbar.html', current_user=current_user)

app.jinja_env.globals['navbar'] = render_navbar

# ====================== ADMIN ROUTES ======================

# --- ONLY ONE DEFINITION OF admin_panel IS LEFT, FIXING AssertionError ---
@app.route('/admin')
@admin_required
def admin_panel():
    users = User.query.all()
    repos = Repository.query.order_by(Repository.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Admin Panel</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %} 
        <div class="p-4 sm:p-8 max-w-6xl mx-auto flex-1 w-full">
            <h1 class="text-4xl font-bold mb-8 flex items-center gap-3 text-red-400"><i data-lucide="shield-half" class="w-8 h-8"></i> Admin Panel</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="mb-4 p-4 rounded-xl bg-green-800 text-green-200 flex items-center gap-2 animate-drop-in">
                        <i data-lucide="check-circle" class="w-5 h-5"></i>
                        {% for message in messages %}
                            <p class="text-sm">{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}

            <div class="bg-gray-800 p-6 rounded-xl shadow-xl mb-10 animate-drop-in" style="animation-delay: 0.1s;">
                <h2 class="text-3xl font-semibold mb-6 flex items-center gap-2"><i data-lucide="users" class="w-6 h-6 text-indigo-400"></i> User Accounts</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-700">
                        <thead class="bg-gray-700">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID / User</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Note Status</th>
                                <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700">
                            {% for u in users %}
                            <tr class="hover:bg-gray-700 transition duration-150 {% if u.is_admin %}bg-red-900/20{% endif %}">
                                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-white">
                                    {{ u.id }} - {{ u.username }} 
                                    {% if u.is_admin %}<span class="text-red-400 text-xs">(Admin)</span>{% endif %}
                                </td>
                                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-400">
                                    {% if u.admin_note %}
                                        <i data-lucide="mail-open" class="w-4 h-4 text-yellow-400 inline"></i> Note Pending
                                    {% else %}
                                        <i data-lucide="mail" class="w-4 h-4 text-green-400 inline"></i> Clear
                                    {% endif %}
                                </td>
                                <td class="px-4 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end gap-2">
                                    <a href="/admin/user/edit/{{ u.id }}" class="text-indigo-400 hover:text-indigo-300 transition hover:scale-105"><i data-lucide="settings" class="w-5 h-5"></i></a>
                                    {% if u.id != current_user.id %}
                                    <form method="POST" action="/admin/user/delete/{{ u.id }}" onsubmit="return confirm('ADMIN WARNING: Permanently delete {{ u.username }} and all their data?');">
                                        <button type="submit" class="text-red-500 hover:text-red-400 transition hover:scale-105"><i data-lucide="trash-2" class="w-5 h-5"></i></button>
                                    </form>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="bg-gray-800 p-6 rounded-xl shadow-xl animate-drop-in" style="animation-delay: 0.2s;">
                <h2 class="text-3xl font-semibold mb-6 flex items-center gap-2"><i data-lucide="git-branch" class="w-6 h-6 text-indigo-400"></i> All Repositories</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-700">
                        <thead class="bg-gray-700">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID / Name</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Owner</th>
                                <th class="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Visibility</th>
                                <th class="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700">
                            {% for r in repos %}
                            <tr class="hover:bg-gray-700 transition duration-150">
                                <td class="px-4 py-4 whitespace-nowrap text-sm font-medium text-white">{{ r.id }} - {{ r.name }}</td>
                                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-400">{{ r.owner.username }}</td>
                                <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-400">
                                    <span class="flex items-center gap-1">
                                        <i data-lucide="{% if r.is_public %}globe{% else %}lock{% endif %}" class="w-4 h-4"></i>
                                        {% if r.is_public %}Public{% else %}Private{% endif %}
                                    </span>
                                </td>
                                <td class="px-4 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end gap-2">
                                    <a href="/admin/repo/edit/{{ r.id }}" class="text-indigo-400 hover:text-indigo-300 transition hover:scale-105"><i data-lucide="settings-2" class="w-5 h-5"></i></a>
                                    <form method="POST" action="/admin/repo/delete/{{ r.id }}" onsubmit="return confirm('ADMIN WARNING: Permanently delete repository {{ r.name }} and all its files?');">
                                        <button type="submit" class="text-red-500 hover:text-red-400 transition hover:scale-105"><i data-lucide="trash-2" class="w-5 h-5"></i></button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', users=users, repos=repos, current_user=current_user)

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('You cannot delete your own admin account!', 'error')
        return redirect(url_for('admin_panel'))
    
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'User "{user_to_delete.username}" and all their data have been deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.display_name = html.escape(request.form['display_name'])
        user.is_admin = 'is_admin' in request.form
        
        note = request.form['admin_note'].strip()
        if note:
            user.admin_note = note
            flash(f'User {user.username} edited. Note set and will be displayed on their next login.', 'success')
        else:
            user.admin_note = None
            flash(f'User {user.username} edited.', 'success')
            
        db.session.commit()
        return redirect(url_for('admin_panel'))
        
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Edit User</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %}
        <div class="flex-1 flex items-center justify-center p-4 sm:p-6">
            <form method="post" class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-lg space-y-4 sm:space-y-6 shadow-xl animate-drop-in">
                <h1 class="text-3xl sm:text-4xl font-bold flex items-center gap-3 text-red-400"><i data-lucide="settings-2" class="w-6 h-6 sm:w-8 sm:h-8"></i> Edit User: {{ user.username }}</h1>
                
                <div>
                    <label class="block text-base sm:text-xl mb-2 flex items-center gap-2"><i data-lucide="user" class="w-5 h-5"></i> Display Name</label>
                    <input name="display_name" value="{{ user.display_name }}" required class="w-full px-4 py-3 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500">
                </div>
                
                <label class="flex items-center gap-3 text-base sm:text-lg">
                    <input type="checkbox" name="is_admin" {% if user.is_admin %}checked{% endif %} class="w-5 h-5 accent-red-600"> 
                    <i data-lucide="shield" class="w-5 h-5"></i> Promote to Admin
                </label>
                
                <div>
                    <label class="block text-base sm:text-xl mb-2 flex items-center gap-2 text-yellow-300"><i data-lucide="sticky-note" class="w-5 h-5"></i> Leave a Note for {{ user.username }} (Read on Login)</label>
                    <textarea name="admin_note" placeholder="Enter message here. Leaving blank clears previous note." class="w-full px-4 py-3 bg-gray-700 rounded-xl h-24 focus:ring-2 focus:ring-indigo-500">{{ user.admin_note or '' }}</textarea>
                    {% if user.admin_note %}<p class="text-sm text-yellow-400 mt-1">Current Note: {{ user.admin_note }}</p>{% endif %}
                </div>
                
                <button class="w-full py-3 sm:py-4 bg-red-600 hover:bg-red-700 font-bold rounded-xl text-lg sm:text-xl flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.02]">
                    <i data-lucide="save" class="w-5 h-5"></i> Save Changes
                </button>
                <a href="/admin" class="block text-center text-gray-400 hover:text-white transition">Back to Admin Panel</a>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', user=user, current_user=current_user)

@app.route('/admin/repo/delete/<int:repo_id>', methods=['POST'])
@admin_required
def admin_delete_repo(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    repo_name = repo.name
    owner_username = repo.owner.username
    
    # Notify the user whose repo was deleted
    repo.owner.admin_note = f"⚠️ Your repository '{repo_name}' was deleted by the administrator."
    
    db.session.delete(repo)
    db.session.commit()
    flash(f'Repository "{repo_name}" belonging to @{owner_username} has been deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/repo/edit/<int:repo_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_repo(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if request.method == 'POST':
        repo.name = html.escape(request.form['name'].strip())
        repo.description = html.escape(request.form.get('description', ''))
        repo.is_public = 'is_public' in request.form
        
        note = request.form['admin_note'].strip()
        if note:
            repo.owner.admin_note = f"🚨 Administrator edit to your repository '{repo.name}': {note}"
            flash(f'Repository {repo.name} edited. Notification sent to user.', 'success')
        else:
            flash(f'Repository {repo.name} edited.', 'success')
            
        db.session.commit()
        return redirect(url_for('admin_panel'))
        
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Edit Repository</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %}
        <div class="flex-1 flex items-center justify-center p-4 sm:p-6">
            <form method="post" class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-lg space-y-4 sm:space-y-6 shadow-xl animate-drop-in">
                <h1 class="text-3xl sm:text-4xl font-bold flex items-center gap-3 text-red-400"><i data-lucide="settings-2" class="w-6 h-6 sm:w-8 sm:h-8"></i> Edit Repo: {{ repo.name }}</h1>
                
                <div>
                    <label class="block text-base sm:text-xl mb-2 flex items-center gap-2"><i data-lucide="git-branch" class="w-5 h-5"></i> Repository Name</label>
                    <input name="name" value="{{ repo.name }}" required class="w-full px-4 py-3 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-base sm:text-xl mb-2 flex items-center gap-2"><i data-lucide="align-left" class="w-5 h-5"></i> Description</label>
                    <textarea name="description" class="w-full px-4 py-3 bg-gray-700 rounded-xl h-24 focus:ring-2 focus:ring-indigo-500">{{ repo.description or '' }}</textarea>
                </div>
                
                <label class="flex items-center gap-3 text-base sm:text-lg">
                    <input type="checkbox" name="is_public" {% if repo.is_public %}checked{% endif %} class="w-5 h-5 accent-red-600"> 
                    <i data-lucide="globe" class="w-5 h-5"></i> Public (Uncheck for Private)
                </label>
                
                <div>
                    <label class="block text-base sm:text-xl mb-2 flex items-center gap-2 text-yellow-300"><i data-lucide="sticky-note" class="w-5 h-5"></i> Note for Owner ({{ repo.owner.username }})</label>
                    <textarea name="admin_note" placeholder="Enter reason for edit. This will be displayed to the user." class="w-full px-4 py-3 bg-gray-700 rounded-xl h-24 focus:ring-2 focus:ring-indigo-500"></textarea>
                </div>
                
                <button class="w-full py-3 sm:py-4 bg-red-600 hover:bg-red-700 font-bold rounded-xl text-lg sm:text-xl flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.02]">
                    <i data-lucide="save" class="w-5 h-5"></i> Save Repo Changes
                </button>
                <a href="/admin" class="block text-center text-gray-400 hover:text-white transition">Back to Admin Panel</a>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repo=repo, current_user=current_user)


# ====================== USER ROUTES ======================

@app.before_request
def check_admin_note():
    # Flashes and clears the admin note before rendering any user page (except /login)
    if current_user.is_authenticated and current_user.admin_note and request.endpoint not in ['login']:
        flash(Markup(f"🛑 **ADMIN NOTE:** {current_user.admin_note}"), 'admin_note')
        current_user.admin_note = None
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                
                if user.admin_note:
                    flash(Markup(f"🛑 **ADMIN NOTE:** {user.admin_note}"), 'admin_note')
                    user.admin_note = None
                    db.session.commit()
                
                flash('Login successful!')
                return redirect('/dashboard')
            else:
                flash('Incorrect password for existing account.')
                return redirect(url_for('login'))
        else:
            if len(username) < 3 or len(password) < 6:
                flash('Username must be at least 3 characters and password at least 6 characters.')
                return redirect(url_for('login'))
                
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                display_name=username.capitalize()
            )
            try:
                if User.query.count() == 0:
                     new_user.is_admin = True
                     new_user.display_name = "👑 Admin"

                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash(f'Welcome! Account for "{username}" created and you are logged in.')
                return redirect('/dashboard')
            except IntegrityError:
                db.session.rollback()
                flash('Username already taken.')
                return redirect(url_for('login'))

    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Login/Register - CodeVault</title><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex items-center justify-center p-4">
        <div class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-md shadow-2xl animate-drop-in">
            <h1 class="text-4xl sm:text-5xl font-bold text-center text-indigo-400 mb-6 sm:mb-8 flex items-center justify-center gap-2">
                <i data-lucide="lock-keyhole" class="w-8 h-8"></i> CodeVault Pro
            </h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="mb-4 sm:mb-6 p-4 rounded-xl bg-red-800 text-red-200 flex items-center gap-2 animate-bounce-in">
                            <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                            <p class="text-sm">{{ message }}</p>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="post" class="space-y-4 sm:space-y-6">
                <input name="username" placeholder="Username (3+ chars)" required class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl text-base sm:text-lg focus:ring-2 focus:ring-indigo-500 transition duration-150">
                <input name="password" type="password" placeholder="Password (6+ chars)" required class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl text-base sm:text-lg focus:ring-2 focus:ring-indigo-500 transition duration-150">
                <button class="w-full py-3 sm:py-4 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-lg sm:text-xl flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.03]">
                    <i data-lucide="log-in" class="w-5 h-5"></i> Login / Register
                </button>
            </form>
            <p class="text-gray-400 text-xs sm:text-sm mt-4 text-center">If the username is new, an account will be automatically created.</p>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''')


@app.route('/dashboard')
@login_required
def dashboard():
    repos = Repository.query.filter_by(owner_id=current_user.id).order_by(Repository.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Dashboard</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    {% if category == 'admin_note' %}
                        <div class="fixed top-24 right-4 z-50 p-4 rounded-xl bg-yellow-800 text-yellow-200 shadow-xl animate-drop-in max-w-sm">
                            <p class="text-sm">{{ message }}</p>
                        </div>
                    {% else %}
                        <div class="fixed top-24 right-4 z-50 p-3 rounded-xl bg-green-700 text-white shadow-xl animate-drop-in">
                            <p class="text-sm flex items-center gap-2"><i data-lucide="info" class="w-4 h-4"></i>{{ message }}</p>
                        </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
        {% endwith %}
        <div class="p-4 sm:p-6 max-w-6xl mx-auto flex-1 w-full">
            <a href="/repo/new" class="inline-block bg-indigo-600 hover:bg-indigo-700 px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold text-lg sm:text-xl mb-6 sm:mb-8 flex items-center gap-2 transition duration-150 hover:scale-[1.03] active:scale-95 animate-drop-in" style="animation-delay: 0.1s;">
                <i data-lucide="plus-square" class="w-5 h-5 sm:w-6 sm:h-6"></i> New Repository
            </a>
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-8 flex items-center gap-3"><i data-lucide="folder-kanban" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> My Repositories</h1>
            <div class="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-4 sm:p-8 rounded-xl border border-gray-700 hover:border-indigo-500 transition duration-200 hover:shadow-indigo-500/30 hover:shadow-lg hover:scale-[1.02] active:scale-95 animate-drop-in" style="animation-delay: {{ loop.index * 0.1 }}s;">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-xl sm:text-2xl font-bold">{{ r.name }}</h3>
                        <i data-lucide="{% if r.is_public %}globe{% else %}lock{% endif %}" class="w-4 h-4 sm:w-5 sm:h-5 text-gray-400"></i>
                    </div>
                    <p class="text-gray-400 text-xs sm:text-sm">{{ r.description or 'No description' }}</p>
                    <div class="text-xs sm:text-sm text-gray-500 mt-3 sm:mt-4 flex items-center gap-3 sm:gap-4">
                        <span class="flex items-center gap-1"><i data-lucide="file-text" class="w-4 h-4"></i> {{ r.files|length }} files</span>
                        <span>• {% if r.is_public %}Public{% else %}Private{% endif %}</span>
                        <div class="flex flex-wrap gap-1 mt-1">
                            {% for lang in get_repo_languages(r) %}
                                <span class="text-xs px-2 py-0.5 rounded-full bg-purple-900/50 text-purple-300">{{ lang }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
            {% if not repos %}<p class="text-center text-2xl sm:text-3xl text-gray-500 mt-10 sm:mt-20 flex items-center justify-center gap-3"><i data-lucide="folder-open" class="w-6 h-6 sm:w-8 sm:h-8"></i> Get started by creating your first repository!</p>{% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repos=repos, current_user=current_user)

@app.route('/explore')
def explore():
    # Get search and filter parameters
    search_query = request.args.get('q', '').strip()
    language_filter = request.args.get('lang', '').strip()
    
    # Base query for public repos
    query = Repository.query.filter_by(is_public=True)
    
    # Apply search filter
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(or_(
            Repository.name.ilike(search_pattern),
            Repository.description.ilike(search_pattern),
            User.username.ilike(search_pattern) 
        )).join(User)

    # Apply language filter
    if language_filter:
        extensions = [ext for ext, lang in LANGUAGE_MAP.items() if lang == language_filter]
        ext_filters = [CodeFile.name.ilike(f'%{ext}') for ext in extensions]
        if ext_filters:
            query = query.filter(Repository.files.any(or_(*ext_filters)))

    # Final result set
    repos = query.order_by(Repository.created_at.desc()).all()
    
    # Get a list of all unique languages across all public repositories for filter dropdown
    all_languages = sorted(list(set(LANGUAGE_MAP.values())))


    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Explore</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %}
        <div class="p-4 sm:p-6 max-w-6xl mx-auto flex-1 w-full"> 
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-8 flex items-center gap-3"><i data-lucide="globe" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> Public Repositories</h1>
            
            <form method="GET" class="mb-8 flex flex-col sm:flex-row gap-4 bg-gray-800 p-4 rounded-xl shadow-lg animate-drop-in" style="animation-delay: 0.1s;">
                <div class="flex-1 relative">
                    <input type="text" name="q" placeholder="Search repos by name, description, or owner..." value="{{ search_query }}" class="w-full px-4 py-3 bg-gray-700 rounded-xl text-white pl-10 focus:ring-2 focus:ring-indigo-500 transition duration-150">
                    <i data-lucide="search" class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"></i>
                </div>
                
                <div class="flex flex-shrink-0 gap-2">
                    <select name="lang" class="px-4 py-3 bg-gray-700 rounded-xl text-white appearance-none focus:ring-2 focus:ring-indigo-500 transition duration-150">
                        <option value="">All Languages</option>
                        {% for lang in all_languages %}
                        <option value="{{ lang }}" {% if lang == language_filter %}selected{% endif %}>{{ lang }}</option>
                        {% endfor %}
                    </select>
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 px-5 py-3 rounded-xl font-bold flex items-center gap-2 transition duration-150 hover:scale-[1.03] active:scale-95">
                        <i data-lucide="filter" class="w-5 h-5"></i> Filter
                    </button>
                </div>
            </form>

            <div class="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-4 sm:p-6 rounded-xl border border-gray-700 hover:border-indigo-500 transition duration-200 hover:shadow-indigo-500/30 hover:shadow-lg hover:scale-[1.02] animate-drop-in" style="animation-delay: {{ loop.index * 0.1 }}s;">
                    <div class="flex items-center gap-2 sm:gap-3 mb-2">
                        <i data-lucide="git-fork" class="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400"></i>
                        <h3 class="text-xl sm:text-2xl font-bold">{{ r.name }}</h3>
                    </div>
                    <p class="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4">{{ r.description or 'No description' }}</p>
                    <div class="text-xs sm:text-sm text-gray-500 flex flex-col gap-2">
                        <span class="flex items-center gap-1"><i data-lucide="user" class="w-4 h-4"></i> Owner: @{{ r.owner.username }}</span> 
                        <div class="flex flex-wrap gap-1">
                            {% for lang in get_repo_languages(r) %}
                                <span class="text-xs px-2 py-0.5 rounded-full bg-purple-900/50 text-purple-300">{{ lang }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
            
            {% if not repos and (search_query or language_filter) %}
            <p class="text-center text-2xl sm:text-3xl text-gray-500 mt-10 sm:mt-20 flex items-center justify-center gap-3">
                <i data-lucide="search-x" class="w-6 h-6 sm:w-8 sm:h-8"></i> No results found for your filters.
            </p>
            {% elif not repos %}
            <p class="text-center text-2xl sm:text-3xl text-gray-500 mt-10 sm:mt-20 flex items-center justify-center gap-3">
                <i data-lucide="folder-open" class="w-6 h-6 sm:w-8 sm:h-8"></i> No public repos yet!
            </p>
            {% endif %}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repos=repos, current_user=current_user, search_query=search_query, language_filter=language_filter, all_languages=all_languages)

@app.route('/repo/delete/<int:repo_id>', methods=['POST'])
@login_required
def delete_repo(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.owner_id != current_user.id:
        abort(403)
    
    db.session.delete(repo)
    db.session.commit()
    flash(f'Repository "{repo.name}" and all associated files deleted successfully.')
    return redirect(url_for('dashboard'))

@app.route('/repo/new', methods=['GET', 'POST'])
@login_required
def new_repo():
    if request.method == 'POST':
        repo_name = html.escape(request.form['name'].strip()) or 'Untitled Repo'
        
        repo = Repository(
            name=repo_name,
            description=html.escape(request.form.get('description', '')),
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
        {% include 'navbar.html' %}
        <div class="flex-1 flex items-center justify-center p-4 sm:p-6">
            <form method="post" class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-lg space-y-4 sm:space-y-6 shadow-xl animate-drop-in">
                <h1 class="text-3xl sm:text-4xl font-bold flex items-center gap-3"><i data-lucide="plus-square" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> New Repository</h1>
                <input name="name" placeholder="Repository Name" required class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 transition duration-150">
                <textarea name="description" placeholder="Description (optional)" class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl h-24 sm:h-32 focus:ring-2 focus:ring-indigo-500 transition duration-150"></textarea>
                <label class="flex items-center gap-3 text-base sm:text-lg"><input type="checkbox" name="public" checked class="w-5 h-5 sm:w-6 sm:h-6 accent-indigo-500"> <i data-lucide="globe" class="w-4 h-4 sm:w-5 sm:h-5"></i> Public</label>
                <button class="w-full py-3 sm:py-4 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-lg sm:text-xl flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.02]">
                    <i data-lucide="check-circle" class="w-5 h-5 sm:w-6 sm:h-6"></i> Create Repository
                </button>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', current_user=current_user)

@app.route('/repo/<int:repo_id>')
@login_required
def editor(repo_id):
    repo = Repository.query.get_or_404(repo_id)
    if repo.owner_id != current_user.id:
        abort(403)
    
    file_id = request.args.get('file', type=int)
    current_file = CodeFile.query.get(file_id) if file_id else (repo.files.first() if repo.files.count() > 0 else None)
    
    file_content_json = json.dumps(current_file.content) if current_file else '""'
    file_content_safe = current_file.content if current_file else ''
    prism_language = get_prism_language(current_file.name) if current_file else 'clike'

    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head>
        <title>{{ repo.name }} - CodeVault</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/themes/prism-twilight.min.css" rel="stylesheet" />
        <style>
            .code-editor-container {
                position: relative;
                font-family: monospace;
                font-size: 14px;
                line-height: 1.5;
            }
            #code, #highlighting {
                padding: 1rem;
                border: 0;
                margin: 0;
                box-sizing: border-box;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            #code {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                color: transparent;
                background: transparent;
                caret-color: white;
                resize: none;
                z-index: 2;
            }
            #highlighting {
                pointer-events: none;
                z-index: 1;
            }
            .prism-twilight {
                background-color: #111827 !important;
                border-radius: 0;
            }
        </style>
    </head>
    <body class="h-full flex flex-col">
        {% include 'navbar.html' %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    {% if category == 'admin_note' %}
                        <div class="fixed top-24 right-4 z-50 p-4 rounded-xl bg-yellow-800 text-yellow-200 shadow-xl animate-drop-in max-w-sm">
                            <p class="text-sm">{{ message }}</p>
                        </div>
                    {% else %}
                        <div class="fixed top-24 right-4 z-50 p-3 rounded-xl bg-green-700 text-white shadow-xl animate-drop-in">
                            <p class="text-sm flex items-center gap-2"><i data-lucide="info" class="w-4 h-4"></i>{{ message }}</p>
                        </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
        {% endwith %}
        <div class="flex-1 flex flex-col lg:flex-row">
            <div class="w-full lg:w-80 bg-gray-800 border-r border-gray-700 p-4 sm:p-6 overflow-y-auto animate-drop-in" style="animation-delay: 0.1s;">
                <h2 class="text-xl sm:text-2xl font-bold mb-4 sm:mb-6 flex items-center gap-2"><i data-lucide="folder-tree" class="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400"></i> {{ repo.name }}</h2>
                
                <form method="POST" action="/repo/delete/{{ repo.id }}" onsubmit="return confirm('WARNING: This will permanently delete the repository and ALL files inside it. Are you sure?');" class="mb-6">
                    <button type="submit" class="w-full px-3 py-2 bg-red-800 hover:bg-red-700 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.01] active:scale-95">
                        <i data-lucide="archive-restore" class="w-4 h-4"></i> Delete Repository
                    </button>
                </form>

                <div class="space-y-3">
                    {% for f in repo.files %}
                    <a href="/repo/{{ repo.id }}?file={{ f.id }}" class="block p-3 rounded-lg font-medium flex items-center gap-3 transition duration-150 {% if f.id == (current_file.id if current_file else 0) %}bg-indigo-600 text-white shadow-md{% else %}bg-gray-700 hover:bg-gray-600 hover:shadow-sm{% endif %} hover:scale-[1.01] active:scale-95">
                        <i data-lucide="{{ get_file_icon(f.name) }}" class="w-5 h-5"></i>
                        <span class="truncate">{{ f.name }}</span>
                    </a>
                    {% endfor %}
                    
                    <form action="/file/new" method="post" class="mt-6 sm:mt-8">
                        <input type="hidden" name="repo_id" value="{{ repo.id }}">
                        <div class="flex gap-2">
                            <input name="name" placeholder="new-file.txt" required class="flex-1 px-3 py-2 bg-gray-700 rounded-l-lg text-sm focus:ring-2 focus:ring-indigo-500 transition duration-150">
                            <button class="px-4 bg-indigo-600 hover:bg-indigo-700 rounded-r-lg font-bold transition duration-150 hover:scale-[1.05] active:scale-95"><i data-lucide="file-plus" class="w-5 h-5"></i></button>
                        </div>
                    </form>
                </div>
            </div>
            <div class="flex-1 flex flex-col">
                {% if current_file %}
                <div class="p-3 sm:p-5 bg-gray-800 border-b border-gray-700 flex justify-between items-center flex-wrap gap-2 animate-drop-in" style="animation-delay: 0.2s;">
                    <h3 class="text-xl sm:text-2xl font-mono font-bold flex items-center gap-2"><i data-lucide="code" class="w-5 h-5 sm:w-6 sm:h-6 text-purple-400"></i> {{ current_file.name }}</h3>
                    <div class="flex items-center gap-2 sm:gap-4">
                        <form method="POST" action="/file/delete/{{ current_file.id }}" onsubmit="return confirm('Are you sure you want to delete {{ current_file.name }}?');">
                            <button type="submit" class="px-3 sm:px-5 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium text-sm flex items-center gap-2 transition duration-150 hover:scale-[1.03] active:scale-95">
                                <i data-lucide="trash-2" class="w-4 h-4 sm:w-5 sm:h-5"></i> Delete
                            </button>
                        </form>
                        <button onclick="copyRaw()" class="px-3 sm:px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium text-sm flex items-center gap-2 transition duration-150 hover:scale-[1.03] active:scale-95">
                            <i data-lucide="copy" class="w-4 h-4 sm:w-5 sm:h-5"></i> Raw Link
                        </button>
                        <span id="status" class="text-green-400 font-medium text-sm flex items-center gap-1"><i data-lucide="check" class="w-4 h-4"></i> Saved</span>
                    </div>
                </div>
                
                <div class="flex-1 code-editor-container bg-gray-900 animate-drop-in" style="animation-delay: 0.3s;">
                    <pre id="highlighting" class="language-{{ prism_language }}"><code class="language-{{ prism_language }}"></code></pre>
                    <textarea id="code" class="outline-none" spellcheck="false">{{ file_content_safe }}</textarea>
                </div>

                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/prism.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-clike.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-markup.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-javascript.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-css.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-python.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-json.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-markdown.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-bash.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-c.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-cpp.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-java.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-php.min.js"></script>

                <script>
                    const codeEl = document.getElementById('code');
                    const statusEl = document.getElementById('status');
                    const highlightingPreEl = document.getElementById('highlighting');
                    const highlightingCodeEl = highlightingPreEl.querySelector('code');
                    const autoSave = {{ 'true' if current_user.auto_save else 'false' }};
                    const prismLanguage = '{{ prism_language }}';
                    let timer;

                    function updateHighlight() {
                        const content = codeEl.value;
                        highlightingCodeEl.textContent = content;
                        
                        // Set the correct language class before highlighting
                        highlightingCodeEl.className = 'language-' + prismLanguage;
                        highlightingPreEl.className = 'language-' + prismLanguage;

                        Prism.highlightElement(highlightingCodeEl);
                        
                        highlightingPreEl.scrollTop = codeEl.scrollTop;
                        highlightingPreEl.scrollLeft = codeEl.scrollLeft;
                    }
                    
                    codeEl.value = JSON.parse({{ file_content_json }});
                    updateHighlight();

                    codeEl.addEventListener('input', function() {
                        updateHighlight();
                        if (!autoSave) return;

                        statusEl.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> saving...';
                        lucide.createIcons();
                        clearTimeout(timer);
                        
                        timer = setTimeout(() => {
                            fetch('/file/save', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({
                                    file_id: {{ current_file.id }},
                                    content: this.value
                                })
                            })
                            .then(response => {
                                if (response.ok) {
                                    statusEl.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i> saved';
                                } else {
                                    statusEl.innerHTML = '<i data-lucide="alert-triangle" class="w-4 h-4"></i> save failed';
                                }
                                lucide.createIcons();
                            })
                            .catch(error => {
                                statusEl.innerHTML = '<i data-lucide="alert-triangle" class="w-4 h-4"></i> error';
                                lucide.createIcons();
                                console.error('Save error:', error);
                            });
                        }, 1000);
                    });

                    codeEl.addEventListener('scroll', updateHighlight);

                    function copyRaw() {
                        navigator.clipboard.writeText(location.origin + '/raw/{{ current_file.id }}');
                        alert('Raw link copied to clipboard!');
                    }
                </script>
                {% else %}
                <div class="flex-1 flex items-center justify-center text-gray-500 text-3xl flex-col gap-4">
                    <i data-lucide="pencil" class="w-12 h-12"></i>
                    Create a file to start coding!
                </div>
                {% endif %}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', repo=repo, current_file=current_file, current_user=current_user, file_content_json=file_content_json, file_content_safe=file_content_safe, prism_language=prism_language)

@app.route('/file/save', methods=['POST'])
@login_required
def save_file():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        content = data.get('content')
    except:
        return 'Invalid JSON', 400

    f = CodeFile.query.get(file_id)
    if not f or f.repo.owner_id != current_user.id:
        abort(403)
    
    f.content = content
    db.session.commit()
    return 'saved'

@app.route('/file/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    f = CodeFile.query.get_or_404(file_id)
    if f.repo.owner_id != current_user.id:
        abort(403)
    
    repo_id = f.repo.id
    db.session.delete(f)
    db.session.commit()
    flash(f'File "{f.name}" deleted successfully.')
    return redirect(url_for('editor', repo_id=repo_id))

@app.route('/file/new', methods=['POST'])
@login_required
def new_file():
    repo = Repository.query.get_or_404(request.form['repo_id'])
    if repo.owner_id != current_user.id:
        abort(403)
    
    filename = html.escape(request.form['name'].strip())
    
    if not filename:
        flash("Filename cannot be empty.")
        return redirect(f'/repo/{repo.id}')
    
    f = CodeFile(name=filename, content="", repo=repo)
    db.session.add(f)
    db.session.commit()
    return redirect(f'/repo/{repo.id}?file={f.id}')

@app.route('/raw/<int:file_id>')
def raw(file_id):
    f = CodeFile.query.get_or_404(file_id)
    if not f.repo.is_public and (not current_user.is_authenticated or f.repo.owner_id != current_user.id):
        abort(403)

    return Response(
        f.content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename="{f.name}"'
        }
    )

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.display_name = html.escape(request.form['display_name'])
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
        {% include 'navbar.html' %}
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    {% if category == 'admin_note' %}
                        <div class="fixed top-24 right-4 z-50 p-4 rounded-xl bg-yellow-800 text-yellow-200 shadow-xl animate-drop-in max-w-sm">
                            <p class="text-sm">{{ message }}</p>
                        </div>
                    {% else %}
                        <div class="fixed top-24 right-4 z-50 p-3 rounded-xl bg-green-700 text-white shadow-xl animate-drop-in">
                            <p class="text-sm flex items-center gap-2"><i data-lucide="info" class="w-4 h-4"></i>{{ message }}</p>
                        </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
        {% endwith %}
        <div class="p-4 sm:p-10 max-w-2xl mx-auto flex-1 w-full">
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-10 flex items-center gap-3"><i data-lucide="settings" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> Settings</h1>
            
            <form method="post" class="bg-gray-800 p-6 sm:p-8 rounded-2xl space-y-6 sm:space-y-8 shadow-xl animate-drop-in">
                <div>
                    <label class="block text-base sm:text-xl mb-3 flex items-center gap-2"><i data-lucide="user" class="w-5 h-5"></i> Display Name</label>
                    <input name="display_name" value="{{ current_user.display_name }}" class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 transition duration-150">
                </div>
                <div>
                    <label class="block text-base sm:text-xl mb-3 flex items-center gap-2"><i data-lucide="key" class="w-5 h-5"></i> New Password (optional)</label>
                    <input name="password" type="password" placeholder="Leave blank to keep current" class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 transition duration-150">
                </div>
                <label class="flex items-center gap-4 text-base sm:text-xl cursor-pointer">
                    <input type="checkbox" name="auto_save" {% if current_user.auto_save %}checked{% endif %} class="w-6 h-6 sm:w-8 sm:h-8 accent-indigo-500">
                    <span class="flex items-center gap-2"><i data-lucide="save" class="w-5 h-5 sm:w-6 sm:h-6"></i> Enable Auto-save</span>
                </label>
                <button class="w-full py-4 sm:py-5 bg-indigo-600 hover:bg-indigo-700 font-bold rounded-xl text-lg sm:text-xl flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.03] active:scale-95">
                    <i data-lucide="disc-3" class="w-5 h-5 sm:w-6 sm:h-6"></i> Save Settings
                </button>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# ====================== MAIN ======================
if __name__ == '__main__':
    print("CodeVault PRO v8.3 is running! (Final fixed code)")
    print("Visit: http://127.0.0.1:5000")
    print("CRITICAL: Ensure 'templates/navbar.html' exists in your project.")
    app.run(host='0.0.0.0', port=5000, debug=False)
