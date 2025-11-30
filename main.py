# ================================================
# CODEVAULT PRO v7 – MOBILE HAMBURGER MENU & UI ENHANCEMENTS
# ================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3
from markupsafe import Markup 
import json 
import html # For escaping HTML in file names
from sqlalchemy.exc import IntegrityError

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

# ====================== UTILITY FUNCTIONS ======================

def fix_database():
    if not os.path.exists('codevault.db'):
        return
    # Database fix logic (omitted for brevity)
    pass

def get_prism_language(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.py']: return 'python'
    elif ext in ['.js', '.mjs', '.cjs']: return 'javascript'
    elif ext in ['.html', '.htm']: return 'markup'
    elif ext in ['.css', '.scss', '.less']: return 'css'
    elif ext in ['.json']: return 'json'
    elif ext in ['.md', '.markdown']: return 'markdown'
    elif ext in ['.sh']: return 'bash'
    else: return 'clike' 

def get_file_icon(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.py']: return 'file-code'
    elif ext in ['.js', '.mjs', '.cjs']: return 'file-code'
    elif ext in ['.html', '.htm']: return 'file-html'
    elif ext in ['.css', '.scss', '.less']: return 'file-css'
    elif ext in ['.json']: return 'file-json'
    elif ext in ['.md', '.markdown']: return 'file-text'
    elif ext in ['.sh']: return 'terminal'
    else: return 'file-text'

app.jinja_env.globals['get_file_icon'] = get_file_icon


# ====================== STARTUP ======================
with app.app_context():
    db.create_all()
    fix_database()


# ====================== NAVBAR TEMPLATE (New Mobile Sidebar) ======================
NAVBAR_TEMPLATE = '''
<style>
    /* Custom styling for smooth sidebar transition */
    .sidebar-transition {
        transition: transform 0.3s ease-in-out;
        transform: translateX(-100%);
    }
    .sidebar-open .sidebar-transition {
        transform: translateX(0);
    }
</style>

<div class="h-20"></div> 
<nav class="bg-gray-900/90 backdrop-blur-sm border border-gray-800 shadow-xl rounded-xl p-4 flex justify-between items-center fixed top-0 left-0 right-0 z-50 mx-auto mt-4 w-[95%] lg:w-[90%] transition duration-300">
    <div class="flex items-center gap-2 lg:gap-3">
        <i data-lucide="code" class="w-6 h-6 lg:w-8 lg:h-8 text-indigo-400 animate-pulse"></i>
        <a href="/" class="text-xl lg:text-2xl font-bold text-indigo-400 hover:text-indigo-300 transition duration-150">CodeVault</a>
    </div>

    <div class="hidden lg:flex items-center gap-6">
        <a href="/explore" class="text-gray-300 hover:text-white flex items-center gap-1 text-base transition duration-150 hover:scale-105">
            <i data-lucide="compass" class="w-5 h-5"></i> Explore
        </a>
        {% if current_user.is_authenticated %}
        <a href="/dashboard" class="text-gray-300 hover:text-white flex items-center gap-1 text-base transition duration-150 hover:scale-105">
            <i data-lucide="folder-kanban" class="w-5 h-5"></i> My Code
        </a>
        <a href="/settings" class="text-gray-300 hover:text-white flex items-center gap-1 text-base transition duration-150 hover:scale-105">
            <i data-lucide="settings" class="w-5 h-5"></i> Settings
        </a>
        <a href="/logout" class="text-red-400 hover:text-red-300 flex items-center gap-1 text-base transition duration-150 hover:scale-105">
            <i data-lucide="log-out" class="w-5 h-5"></i> Logout
        </a>
        {% else %}
        <a href="/login" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg font-bold flex items-center gap-1 text-sm transition duration-150 hover:scale-[1.03]">
            <i data-lucide="log-in" class="w-4 h-4"></i> Login
        </a>
        {% endif %}
    </div>

    <button id="menu-toggle" class="lg:hidden text-white hover:text-indigo-400 transition duration-150 p-1">
        <i data-lucide="menu" class="w-6 h-6"></i>
    </button>
</nav>

<div id="sidebar" class="sidebar-transition fixed top-0 left-0 h-full w-64 bg-gray-900 z-[60] border-r border-gray-700 p-6 pt-24 lg:hidden">
    <div class="space-y-4">
        <a href="/explore" class="block text-gray-300 hover:text-indigo-400 flex items-center gap-3 text-lg p-2 rounded-lg transition duration-150 hover:bg-gray-800">
            <i data-lucide="compass" class="w-5 h-5"></i> Explore
        </a>
        {% if current_user.is_authenticated %}
        <a href="/dashboard" class="block text-gray-300 hover:text-indigo-400 flex items-center gap-3 text-lg p-2 rounded-lg transition duration-150 hover:bg-gray-800">
            <i data-lucide="folder-kanban" class="w-5 h-5"></i> My Code
        </a>
        <a href="/settings" class="block text-gray-300 hover:text-indigo-400 flex items-center gap-3 text-lg p-2 rounded-lg transition duration-150 hover:bg-gray-800">
            <i data-lucide="settings" class="w-5 h-5"></i> Settings
        </a>
        <div class="h-px bg-gray-700 my-4"></div>
        <a href="/logout" class="block text-red-400 hover:text-red-300 flex items-center gap-3 text-lg p-2 rounded-lg transition duration-150 hover:bg-gray-800">
            <i data-lucide="log-out" class="w-5 h-5"></i> Logout
        </a>
        {% else %}
        <a href="/login" class="block bg-indigo-600 hover:bg-indigo-700 px-4 py-3 rounded-lg font-bold text-center flex items-center justify-center gap-2 transition duration-150 hover:scale-[1.02]">
            <i data-lucide="log-in" class="w-5 h-5"></i> Login / Register
        </a>
        {% endif %}
    </div>
</div>

<div id="sidebar-overlay" class="fixed inset-0 bg-black/50 z-[55] opacity-0 pointer-events-none transition duration-300 lg:hidden"></div>

<script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
<script>
    lucide.createIcons();
    
    // Mobile Sidebar Logic
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const body = document.body;

    function toggleSidebar() {
        body.classList.toggle('sidebar-open');
        if (body.classList.contains('sidebar-open')) {
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
            body.style.overflow = 'hidden'; // Prevent scrolling the main content
        } else {
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
            body.style.overflow = 'auto';
        }
    }

    menuToggle.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);
    
    // Close sidebar on link click (important for mobile UX)
    document.querySelectorAll('#sidebar a').forEach(link => {
        link.addEventListener('click', () => {
            if (body.classList.contains('sidebar-open')) {
                toggleSidebar();
            }
        });
    });

</script>
'''

def render_navbar():
    return Markup(render_template_string(NAVBAR_TEMPLATE, current_user=current_user))

app.jinja_env.globals['navbar'] = render_navbar


# ====================== ROUTES ======================

# --- Authentication Routes ---
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
            if check_password_hash(user.password, password):
                login_user(user)
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
        <div class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-md shadow-2xl">
            <h1 class="text-4xl sm:text-5xl font-bold text-center text-indigo-400 mb-6 sm:mb-8 flex items-center justify-center gap-2">
                <i data-lucide="lock-keyhole" class="w-8 h-8"></i> CodeVault
            </h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="mb-4 sm:mb-6 p-4 rounded-xl bg-red-800 text-red-200 flex items-center gap-2 animate-bounce-in">
                        <i data-lucide="alert-triangle" class="w-5 h-5"></i>
                        {% for message in messages %}
                            <p class="text-sm">{{ message }}</p>
                        {% endfor %}
                    </div>
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# --- Main Views ---
@app.route('/explore')
def explore():
    repos = Repository.query.filter_by(is_public=True).order_by(Repository.created_at.desc()).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html class="h-full bg-gray-900 text-white">
    <head><title>Explore</title><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        <div class="p-4 sm:p-6 max-w-6xl mx-auto flex-1 w-full"> 
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-8 flex items-center gap-3"><i data-lucide="globe" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> Public Repositories</h1>
            <div class="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-4 sm:p-6 rounded-xl border border-gray-700 hover:border-indigo-500 transition duration-200 hover:shadow-indigo-500/30 hover:shadow-lg hover:scale-[1.02]">
                    <div class="flex items-center gap-2 sm:gap-3 mb-2">
                        <i data-lucide="git-fork" class="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400"></i>
                        <h3 class="text-xl sm:text-2xl font-bold">{{ r.name }}</h3>
                    </div>
                    <p class="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4">{{ r.description or 'No description' }}</p>
                    <div class="text-xs sm:text-sm text-gray-500 flex items-center gap-3 sm:gap-4">
                        <span class="flex items-center gap-1"><i data-lucide="user" class="w-4 h-4"></i> @{{ r.owner.username }}</span> 
                        <span class="flex items-center gap-1"><i data-lucide="file-text" class="w-4 h-4"></i> {{ r.files|length }} files</span>
                    </div>
                </a>
                {% endfor %}
            </div>
            {% if not repos %}<p class="text-center text-2xl sm:text-3xl text-gray-500 mt-10 sm:mt-20 flex items-center justify-center gap-3"><i data-lucide="folder-open" class="w-6 h-6 sm:w-8 sm:h-8"></i> No public repos yet!</p>{% endif %}
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
        <div class="p-4 sm:p-6 max-w-6xl mx-auto flex-1 w-full">
            <a href="/repo/new" class="inline-block bg-indigo-600 hover:bg-indigo-700 px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold text-lg sm:text-xl mb-6 sm:mb-8 flex items-center gap-2 transition duration-150 hover:scale-[1.03]">
                <i data-lucide="plus-square" class="w-5 h-5 sm:w-6 sm:h-6"></i> New Repository
            </a>
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-8 flex items-center gap-3"><i data-lucide="folder-kanban" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> My Repositories</h1>
            <div class="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for r in repos %}
                <a href="/repo/{{ r.id }}" class="block bg-gray-800 p-4 sm:p-8 rounded-xl border border-gray-700 hover:border-indigo-500 transition duration-200 hover:shadow-indigo-500/30 hover:shadow-lg hover:scale-[1.02] active:scale-95">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-xl sm:text-2xl font-bold">{{ r.name }}</h3>
                        <i data-lucide="{% if r.is_public %}globe{% else %}lock{% endif %}" class="w-4 h-4 sm:w-5 sm:h-5 text-gray-400"></i>
                    </div>
                    <p class="text-gray-400 text-xs sm:text-sm">{{ r.description or 'No description' }}</p>
                    <div class="text-xs sm:text-sm text-gray-500 mt-3 sm:mt-4 flex items-center gap-3 sm:gap-4">
                        <span class="flex items-center gap-1"><i data-lucide="file-text" class="w-4 h-4"></i> {{ r.files|length }} files</span>
                        <span>• {% if r.is_public %}Public{% else %}Private{% endif %}</span>
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

# --- Repository Actions ---
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
        {{ navbar() }}
        <div class="flex-1 flex items-center justify-center p-4 sm:p-6">
            <form method="post" class="bg-gray-800 p-6 sm:p-10 rounded-2xl w-full max-w-lg space-y-4 sm:space-y-6 shadow-xl">
                <h1 class="text-3xl sm:text-4xl font-bold flex items-center gap-3"><i data-lucide="plus-square" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> New Repository</h1>
                <input name="name" placeholder="Repository Name" required class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 transition duration-150">
                <textarea name="description" placeholder="Description (optional)" class="w-full px-4 py-3 sm:px-6 sm:py-4 bg-gray-700 rounded-xl h-24 sm:h-32 focus:ring-2 focus:ring-indigo-500 transition duration-150"></textarea>
                <label class="flex items-center gap-3 text-base sm:text-lg"><input type="checkbox" name="public" checked class="w-5 h-5 sm:w-6 sm:h-6"> <i data-lucide="globe" class="w-4 h-4 sm:w-5 sm:h-5"></i> Public</label>
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

# --- Editor and File Actions ---
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
                z-index: 2; /* Ensure textarea is above highlighting */
            }
            #highlighting {
                pointer-events: none;
                z-index: 1;
            }
            .prism-twilight {
                background-color: #111827 !important; /* gray-900 */
                border-radius: 0;
            }
        </style>
    </head>
    <body class="h-full flex flex-col">
        {{ navbar() }}
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="fixed top-24 right-4 z-50 p-3 rounded-xl bg-green-700 text-white shadow-xl animate-fade-in-down">
                    {% for message in messages %}
                        <p class="text-sm flex items-center gap-2"><i data-lucide="info" class="w-4 h-4"></i>{{ message }}</p>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        <div class="flex-1 flex flex-col lg:flex-row">
            <div class="w-full lg:w-80 bg-gray-800 border-r border-gray-700 p-4 sm:p-6 overflow-y-auto">
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
                <div class="p-3 sm:p-5 bg-gray-800 border-b border-gray-700 flex justify-between items-center flex-wrap gap-2">
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
                
                <div class="flex-1 code-editor-container bg-gray-900">
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

# --- Remaining Backend Routes (same as V6) ---
@app.route('/file/save', methods=['POST'])
@login_required
def save_file():
    # ... (same logic as V6)
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
    # ... (same logic as V6)
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
    # ... (same logic as V6)
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
    # ... (same logic as V6)
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
        {{ navbar() }}
        <div class="p-4 sm:p-10 max-w-2xl mx-auto flex-1 w-full">
            <h1 class="text-3xl sm:text-4xl font-bold mb-6 sm:mb-10 flex items-center gap-3"><i data-lucide="settings" class="w-6 h-6 sm:w-8 sm:h-8 text-indigo-400"></i> Settings</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="mb-4 sm:mb-6 p-4 rounded-xl bg-green-800 text-green-200 flex items-center gap-2 animate-fade-in-down">
                        <i data-lucide="check-circle" class="w-5 h-5"></i>
                        {% for message in messages %}
                            <p class="text-sm">{{ message }}</p>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="post" class="bg-gray-800 p-6 sm:p-8 rounded-2xl space-y-6 sm:space-y-8 shadow-xl">
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
                    <i data-lucide="disc-3" class="w-5 h-5 sm:w-6 sm:h-6 animate-spin-slow"></i> Save Settings
                </button>
            </form>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/lucide/dist/lucide.min.js"></script>
        <script>lucide.createIcons();</script>
    </body>
    </html>
    ''', current_user=current_user)


# ====================== MAIN ======================
if __name__ == '__main__':
    print("CodeVault PRO v7 is running! (Mobile Hamburger Menu & UI polish applied)")
    print("Visit: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
