#!/usr/bin/env python3
import os, json, uuid, time, shutil, threading, subprocess, re, sqlite3
from pathlib import Path
from flask import Flask, request, session, redirect, url_for, render_template_string, send_file, jsonify, flash, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from jinja2 import DictLoader
import psutil
import random # Added random import for banner timestamp fix

# ===============================================================
# ADVANCED STYLES & NEW TEMPLATES (Updated CSS)
# ===============================================================

LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GenBot Hosting</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Fira+Code:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            /* NEW BLACK/RED/ORANGE THEME */
            --primary-color: #ff5722; --primary-rgb: 255, 87, 34; /* Vibrant Orange/Red */
            --secondary-color: #e91e63; /* Accent Red */
            --dark-color-1: #0a0a0a; /* Main Background */
            --dark-color-2: #181818; /* Card/Sidebar Background */
            --dark-color-3: #282828; /* Input/Header Background */
            --text-color: #f0f0f0; 
            --text-muted: #a0a0a0;
            
            --bs-primary: var(--primary-color); --bs-primary-rgb: var(--primary-rgb);
            --bs-body-bg: var(--dark-color-1); --bs-body-color: var(--text-color);
            --bs-card-bg: var(--dark-color-2); 
            --bs-card-border-color: rgba(255,255,255,0.08);
            --bs-card-shadow: 0 4px 15px rgba(0,0,0,.4);
            --bs-font-sans-serif: 'Poppins', sans-serif; --bs-font-monospace: 'Fira Code', monospace;
            --bs-border-radius: 0.75rem; 
            --bs-btn-border-radius: 0.5rem;
        }
        body { 
            font-family: var(--bs-font-sans-serif); background-color: var(--bs-body-bg); color: var(--bs-body-color); 
            background-image: radial-gradient(circle, rgba(var(--primary-rgb), 0.05) 1px, transparent 1px); 
            background-size: 3rem 3rem; 
        }
        .sidebar {
            width: 280px; position: fixed; top: 0; left: 0; bottom: 0;
            background-color: var(--dark-color-2); border-right: none;
            padding: 1.5rem 1rem; display: flex; flex-direction: column; z-index: 100;
            box-shadow: 2px 0 10px rgba(0,0,0,0.5); 
        }
        .sidebar-brand { 
            font-weight: 700; color: var(--primary-color); font-size: 1.8rem; margin-bottom: 2.5rem; text-align: center; text-decoration: none; 
            letter-spacing: 1px; text-shadow: 0 0 8px rgba(var(--primary-rgb), 0.3);
        }
        .sidebar-brand img { height: 32px; margin-right: 10px; vertical-align: -5px; filter: drop-shadow(0 0 2px rgba(var(--primary-rgb), 0.8)); }
        .main-content { margin-left: 280px; padding: 2.5rem; }
        
        .nav-link { 
            color: var(--text-muted) !important; font-weight: 500; 
            padding: 0.85rem 1rem; border-radius: var(--bs-btn-border-radius); 
            transition: all 0.2s ease;
        }
        .nav-link.active { 
            color: #fff !important; 
            background-color: rgba(var(--primary-rgb), 0.2); 
            border-left: 3px solid var(--primary-color);
            padding-left: 0.7rem;
        }
        .nav-link:not(.active):hover { 
            background-color: var(--dark-color-3); 
            color: var(--primary-color) !important;
        }

        .card { 
            border: 1px solid var(--bs-card-border-color); 
            border-radius: var(--bs-border-radius); 
            box-shadow: var(--bs-card-shadow); 
            margin-bottom: 1.75rem; 
            background-color: var(--bs-card-bg); 
            backdrop-filter: blur(2px); /* Subtle modern effect */
        }
        .card-header { 
            background-color: var(--dark-color-3); 
            border-bottom: 1px solid var(--bs-card-border-color); 
            font-weight: 600; 
            padding: 1rem 1.5rem; 
            border-radius: calc(var(--bs-border-radius) - 1px) calc(var(--bs-border-radius) - 1px) 0 0;
        }
        
        .btn { border-radius: var(--bs-btn-border-radius); font-weight: 600; transition: all 0.2s ease; }
        .btn-primary { 
            background-color: var(--primary-color); 
            border-color: var(--primary-color); 
            color: #000; 
            box-shadow: 0 4px 10px rgba(var(--primary-rgb), 0.3);
        }
        .btn-primary:hover { 
            filter: brightness(1.05); 
            transform: translateY(-1px);
            box-shadow: 0 6px 12px rgba(var(--primary-rgb), 0.5);
            background-color: var(--primary-color); 
            border-color: var(--primary-color); 
        }
        
        .form-control, .form-select { 
            border-radius: var(--bs-btn-border-radius); 
            border: 1px solid var(--dark-color-3); 
            background-color: var(--dark-color-3); 
            color: var(--text-color); 
        }
        .form-control:focus, .form-select:focus { 
            border-color: var(--primary-color); 
            box-shadow: 0 0 0 0.25rem rgba(var(--primary-rgb), 0.25); 
            background-color: var(--dark-color-3); 
        }
        
        /* Code & Log Elements */
        .code-editor, .log-iframe { 
            background-color: #111111; 
            color: #dcdcdc; 
            border-radius: var(--bs-btn-border-radius); 
            font-family: var(--bs-font-monospace); 
            min-height: 60vh; 
            font-size: 0.9em; 
            border: 1px solid var(--dark-color-3); 
            padding: 15px;
        }
        .modal-content { background-color: var(--dark-color-2); border: 1px solid var(--bs-card-border-color); }
        .modal-header { border-bottom-color: var(--bs-card-border-color); } 
        .modal-footer { border-top-color: var(--bs-card-border-color); }
        
        .table { --bs-table-color: var(--text-color); --bs-table-border-color: var(--bs-card-border-color); --bs-table-header-color: var(--text-muted); --bs-table-hover-bg: var(--dark-color-3); } 
        .table th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid var(--primary-color); } 
        
        .status-badge { 
             transition: all 0.5s ease; padding: 0.5em 1em; font-size: 0.85em; font-weight: 600; border-radius: 50px;
        }
        
        /* Custom Bootstrap Colors for High Contrast */
        .bg-success { background-color: #38c172 !important; color: #000 !important; }
        .bg-danger { background-color: #dc3545 !important; color: #fff !important; }
        .bg-warning { background-color: #ffc107 !important; color: #000 !important; }
        .bg-info { background-color: #0dcaf0 !important; color: #000 !important; }
        
        #drop-zone { border: 2px dashed var(--dark-color-3); padding: 30px; }
        #drop-zone.drag-over { border-color: var(--primary-color); background-color: rgba(var(--primary-rgb), 0.15); }
        
        /* Alerts */
        .alert { background-color: var(--dark-color-3); border-color: var(--bs-card-border-color); color: var(--text-color); border-left: 5px solid; }
        .alert-success { background-color: rgba(40, 167, 69, 0.15); border-color: #28a745; color: #70d885; }
        .alert-danger { background-color: rgba(220, 53, 69, 0.15); border-color: #dc3545; color: #f89098; }
        .alert-info { background-color: rgba(13, 202, 240, 0.15); border-color: #0dcaf0; color: #9eeafb; }
        .alert-warning { background-color: rgba(255, 193, 7, 0.15); border-color: #ffc107; color: #ffe59c; }
        
        .server-banner { 
            height: 250px; border-radius: var(--bs-border-radius); 
            background-size: cover; background-position: center; 
            background-color: var(--dark-color-3); 
            box-shadow: var(--bs-card-shadow);
            margin-bottom: 1rem !important;
        }
        
        /* Tabs */
        .nav-tabs { border-bottom: 1px solid var(--bs-card-border-color); }
        .nav-tabs .nav-link { border: 1px solid transparent; color: var(--text-muted); padding: 0.75rem 1.25rem; margin-bottom: -1px; }
        .nav-tabs .nav-link.active { 
            background: var(--dark-color-2); 
            color: var(--primary-color); 
            border-color: var(--bs-card-border-color) var(--bs-card-border-color) var(--dark-color-2) var(--bs-card-border-color);
            font-weight: 600;
        }
        
        @media (max-width: 992px) {
            .sidebar { width: 250px; transform: translateX(-100%); transition: transform 0.3s ease; }
            .sidebar.active { transform: translateX(0); }
            .main-content { margin-left: 0; }
            .sidebar-toggler { display: block; position: fixed; top: 15px; left: 15px; z-index: 101; background: var(--dark-color-3); border:1px solid var(--bs-card-border-color); color: white; padding: 5px 10px; border-radius: 5px; }
        }
        @media (min-width: 992px) { .sidebar-toggler { display: none; } }
    </style>
</head>
<body>
    <button class="sidebar-toggler" type="button"><i class="fa-solid fa-bars"></i></button>

    <div class="sidebar">
        <a class="sidebar-brand" href="{{ url_for('index') }}"><img src="{{ url_for('static', filename='icon.png') }}">GenBot</a>
        <ul class="nav flex-column">
            {% if session.user %}
                <li class="nav-item mb-2"><a class="nav-link {% if request.endpoint == 'dashboard' %}active{% endif %}" href="{{ url_for('dashboard') }}"><i class="fa-solid fa-table-columns fa-fw"></i> Dashboard</a></li>
                <li class="nav-item mb-2"><a class="nav-link {% if request.endpoint == 'settings' %}active{% endif %}" href="{{ url_for('settings') }}"><i class="fa-solid fa-gear fa-fw"></i> Settings</a></li>
            {% else %}
                 <li class="nav-item mb-2"><a class="nav-link {% if request.endpoint == 'login' %}active{% endif %}" href="{{ url_for('login') }}">Login</a></li>
                 <li class="nav-item mb-2"><a class="nav-link {% if request.endpoint == 'register' %}active{% endif %}" href="{{ url_for('register') }}">Register</a></li>
            {% endif %}
        </ul>
        <div class="mt-auto">
             {% if session.user %}
                 <a class="nav-link" href="{{ url_for('logout') }}"><i class="fa-solid fa-right-from-bracket fa-fw"></i> Logout ({{ session.user }})</a>
             {% endif %}
        </div>
    </div>
    <main class="main-content">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
        <footer class="text-center py-4 mt-5"><p>&copy; 2025 GenBot Hosting</p></footer>
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const sidebar = document.querySelector('.sidebar');
            const toggler = document.querySelector('.sidebar-toggler');
            if (toggler) {
                toggler.addEventListener('click', () => sidebar.classList.toggle('active'));
                document.addEventListener('click', (e) => {
                    if (sidebar && !sidebar.contains(e.target) && !toggler.contains(e.target) && sidebar.classList.contains('active')) {
                        sidebar.classList.remove('active');
                    }
                });
            }
        });
        function showToast(message, type = 'success') {
            const toastContainer = document.getElementById('toast-container') || document.createElement('div');
            if (!toastContainer.id) {
                toastContainer.id = 'toast-container';
                toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                document.body.appendChild(toastContainer);
            }
            const toastId = 'toast-' + Date.now();
            const toastHTML = `
                <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                  <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                  </div>
                </div>`;
            toastContainer.insertAdjacentHTML('beforeend', toastHTML);
            const toastEl = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
            toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
        }
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

# Note: The usage of `range(1, 1000) | random` in SERVER_TEMPLATE is preserved exactly as requested.
SERVER_TEMPLATE = """
{% extends 'layout' %}
{% block content %}
<!-- Server Banner -->
<div class="server-banner mb-4" style="background-image: url('{{ url_for('server_banner', sid=server.id) }}?t={{ range(1, 1000) | random }}');"></div>

<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap">
    <h3 class="mb-0 text-light"><a href="{{ url_for('dashboard') }}" class="text-decoration-none text-muted me-2">&larr;</a> Manage: {{ server.name }}</h3>
    <div class="d-flex align-items-center">
        <span id="status-badge" class="badge me-3 status-badge fs-6 {% if server.status == 'running' %} bg-success {% else %} bg-danger {% endif %}"><i class="fa-solid fa-circle me-1"></i> {{ server.status }}</span>
        <div class="btn-toolbar">
            <div class="btn-group">
                <form action="{{ url_for('start_server_action', sid=server.id) }}" method="post"><button type="submit" class="btn btn-success" {% if server.status == 'running' %}disabled{% endif %}><i class="fa-solid fa-play me-1"></i> Start</button></form>
                <form action="{{ url_for('stop_server_action', sid=server.id) }}" method="post"><button type="submit" class="btn btn-warning" {% if server.status == 'stopped' %}disabled{% endif %}><i class="fa-solid fa-stop me-1"></i> Stop</button></form>
                 <form action="{{ url_for('restart_server_action', sid=server.id) }}" method="post"><button type="submit" class="btn btn-info"><i class="fa-solid fa-arrows-rotate me-1"></i> Restart</button></form>
            </div>
        </div>
    </div>
</div>

<div class="card mb-4"><div class="card-body d-flex justify-content-around flex-wrap text-center small text-muted">
    <div><strong>CPU:</strong> <span id="server-cpu-usage">--%</span></div>
    <div><strong>Memory:</strong> <span id="server-mem-usage">--</span></div>
    <div><strong>Disk:</strong> <span id="server-disk-usage">--</span></div>
    <div><strong>Uptime:</strong> <span id="server-uptime">--</span></div>
    <div id="server-url"><strong>URL:</strong> {% if server.url %}<a href="{{ server.url }}" target="_blank">{{ server.url }}</a>{% else %}Not Available{% endif %}</div>
</div></div>

<div class="card">
    <div class="card-header p-0">
        <ul class="nav nav-tabs" id="server-tabs" role="tablist">
            <li class="nav-item" role="presentation"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#settings-pane" type="button"><i class="fa-solid fa-gear fa-fw me-2"></i>Settings</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#console-pane" type="button"><i class="fa-solid fa-terminal fa-fw me-2"></i>Console</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#files-pane" type="button"><i class="fa-solid fa-folder-open fa-fw me-2"></i>Files</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#env-pane" type="button"><i class="fa-solid fa-key fa-fw me-2"></i>Environment</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#packages-pane" type="button"><i class="fa-solid fa-box-open fa-fw me-2"></i>Packages</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#backups-pane" type="button"><i class="fa-solid fa-save fa-fw me-2"></i>Backups</button></li>
            <li class="nav-item" role="presentation"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#db-pane" type="button"><i class="fa-solid fa-database fa-fw me-2"></i>Databases</button></li>
        </ul>
    </div>
    <div class="card-body tab-content p-2 p-md-4" id="server-tabs-content">
        <!-- Settings Pane -->
        <div class="tab-pane fade show active" id="settings-pane" role="tabpanel">
             <div class="row">
                <div class="col-md-7">
                    <h4>Server Details</h4>
                    <table class="table"><tbody>
                        <tr><th scope="row">Server Name</th><td>{{ server.name }}</td></tr>
                        <tr><th scope="row">Server ID</th><td class="font-monospace small">{{ server.id }}</td></tr>
                        <tr><th scope="row">Owner</th><td>{{ server.owner }}</td></tr>
                        <tr><th scope="row">Type</th><td>{{ server.type }}</td></tr>
                        <tr><th scope="row">Process ID</th><td id="server-pid">--</td></tr>
                        <tr><th scope="row">Server Path</th><td class="font-monospace small">{{ server.path }}</td></tr>
                    </tbody></table>
                    
                    <h5 class="mt-4">Upload Banner</h5>
                    <p class="small text-muted">Upload a 16:9 image (e.g., 1280x720) to customize your server page. Must be named 'banner.png'.</p>
                     <form id="banner-upload-form">
                        <div class="input-group">
                          <input type="file" class="form-control" name="banner" accept="image/png" required>
                          <button class="btn btn-outline-secondary" type="submit">Upload</button>
                        </div>
                    </form>
                </div>
                <div class="col-md-5">
                     <div class="card border border-danger mt-4 mt-md-0">
                        <div class="card-header text-danger"><i class="fa-solid fa-skull-crossbones me-2"></i> Danger Zone</div>
                        <div class="card-body text-center">
                            <p class="small">Deleting a server is a permanent action and cannot be undone.</p>
                            <form action="{{ url_for('delete_server_action', sid=server.id) }}" method="post" onsubmit="return confirm('DELETE server? This is irreversible.');">
                                <button type="submit" class="btn btn-danger"><i class="fa-solid fa-trash me-1"></i> Delete This Server</button>
                            </form>
                        </div>
                     </div>
                </div>
            </div>
        </div>
        <!-- Console Pane -->
        <div class="tab-pane fade" id="console-pane" role="tabpanel">
            <iframe src="{{ url_for('logs_view', sid=server.id) }}" class="log-iframe w-100"></iframe>
        </div>
        <!-- Files Pane -->
        <div class="tab-pane fade" id="files-pane" role="tabpanel">
            <div class="row g-4">
                <div class="col-lg-5">
                    <h5><i class="fa-solid fa-folder-open me-2"></i> File Manager</h5>
                    <div id="drop-zone" class="mb-3"><p class="mb-0"><i class="fa-solid fa-upload me-2"></i> Drag & drop files or click to upload</p><input type="file" id="file-input" multiple style="display: none;"></div>
                    <div id="upload-feedback" class="mb-2"></div>
                    <ul id="file-list" class="list-group list-group-flush"></ul>
                </div>
                <div class="col-lg-7">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="mb-0"><i class="fa-solid fa-file-code me-2"></i><span id="editing-filename">No file selected</span></h5>
                        <button id="save-code-btn" class="btn btn-primary" disabled><i class="fa-solid fa-save me-1"></i> Save File</button>
                    </div>
                    <div id="editor-status-overlay" class="alert alert-warning text-center d-none">Server is running. File editing is disabled.</div>
                    <textarea id="code-editor" class="form-control code-editor">Select a file from the manager to begin editing.</textarea>
                </div>
            </div>
        </div>
        <!-- Environment Pane -->
        <div class="tab-pane fade" id="env-pane" role="tabpanel">
            <h4><i class="fa-solid fa-key me-2"></i>Environment Variables</h4>
            <p class="text-muted small">These variables are loaded into your server's environment at runtime. Good for secrets like API keys.</p>
            <div class="row">
                <div class="col-md-8">
                    <div class="table-responsive">
                        <table class="table"><thead><tr><th>Key</th><th>Value</th><th></th></tr></thead><tbody id="env-vars-table"></tbody></table>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card"><div class="card-body">
                        <h5>Add Variable</h5>
                        <form id="add-env-var-form">
                            <div class="mb-2"><label class="form-label small">Variable Key</label><input type="text" class="form-control" id="env-key-input" placeholder="MY_API_KEY" required></div>
                            <div class="mb-3"><label class="form-label small">Variable Value</label><input type="text" class="form-control" id="env-value-input" placeholder="secret_value_123" required></div>
                            <button type="submit" class="btn btn-primary w-100">Add Variable</button>
                        </form>
                    </div></div>
                </div>
            </div>
        </div>
        <!-- Packages Pane -->
        <div class="tab-pane fade" id="packages-pane" role="tabpanel">
            <h4><i class="fa-solid fa-box-open me-2"></i>Package Management</h4>
            <p class="text-muted small">Install packages from {% if 'python' in server.type %}PyPI (pip){% else %}NPM{% endif %}.</p>
            <div class="row">
                <div class="col-md-8">
                    <p>Installed packages are listed in <code class="font-monospace small">{% if 'python' in server.type %}requirements.txt{% else %}package.json{% endif %}</code>.</p>
                    <textarea id="packages-list" class="form-control code-editor" style="min-height: 40vh" readonly>Loading packages...</textarea>
                </div>
                <div class="col-md-4">
                    <div class="card"><div class="card-body">
                        <h5>Install New Package</h5>
                        <form id="add-package-form">
                            <div class="mb-3"><label class="form-label small">Package Name</label><input type="text" class="form-control" id="package-name-input" placeholder="{% if 'python' in server.type %}requests{% else %}axios{% endif %}" required></div>
                            <button type="submit" class="btn btn-primary w-100"><span id="pkg-spinner" class="spinner-border spinner-border-sm me-1 d-none" role="status" aria-hidden="true"></span> Install Package</button>
                        </form>
                    </div></div>
                </div>
            </div>
        </div>
        <!-- Backups Pane -->
        <div class="tab-pane fade" id="backups-pane" role="tabpanel">
            <div class="d-flex justify-content-between align-items-center mb-3">
                 <h4><i class="fa-solid fa-save me-2"></i>Server Backups</h4>
                 <button class="btn btn-primary" id="create-backup-btn"><i class="fa-solid fa-plus me-1"></i> Create Backup</button>
            </div>
            <p class="text-muted small">Create a full zip archive of your server files. Backups do not include databases or other services.</p>
            <div class="table-responsive">
                <table class="table"><thead><tr><th>Filename</th><th>Size</th><th>Date Created</th><th></th></tr></thead><tbody id="backups-table"></tbody></table>
            </div>
        </div>
        <!-- Databases Pane -->
        <div class="tab-pane fade" id="db-pane" role="tabpanel">
             <h4><i class="fa-solid fa-database me-2"></i>SQLite Databases</h4>
            <p class="text-muted small">Create and manage simple file-based SQLite databases.</p>
            <div class="row">
                <div class="col-md-8">
                    <div id="db-list"></div>
                </div>
                <div class="col-md-4">
                     <div class="card"><div class="card-body">
                        <h5>Create Database</h5>
                        <form id="create-db-form">
                            <div class="mb-2"><label class="form-label small">Database Name</label><input type="text" class="form-control" id="db-name-input" placeholder="mydatabase" required></div>
                            <p class="text-muted small">A file named <code class="font-monospace">mydatabase.sqlite</code> will be created.</p>
                            <button type="submit" class="btn btn-primary w-100">Create</button>
                        </form>
                    </div></div>
                </div>
            </div>
        </div>
    </div>
</div>

{% endblock %}
{% block scripts %}
<script>
// ===================================
// UTILITY & CORE FUNCTIONS
// ===================================
const sid = "{{ server.id }}";
const isPython = "{{ 'python' in server.type }}".toLowerCase() === 'true';

function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Bytes'; const k = 1024; const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']; const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}
function formatUptime(seconds) {
    if (!seconds || seconds <= 0) return '--';
    let d = Math.floor(seconds / (3600*24)); let h = Math.floor(seconds % (3600*24) / 3600);
    let m = Math.floor(seconds % 3600 / 60); let s = Math.floor(seconds % 60);
    return [d > 0 ? `${d}d` : null, h > 0 ? `${h}h` : null, m > 0 ? `${m}m` : null, `${s}s`].filter(Boolean).join(' ');
}
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Request failed with status ' + response.status }));
            throw new Error(errorData.error || 'Unknown error');
        }
        return response.json();
    } catch (error) {
        console.error('API Fetch Error:', error);
        showToast(error.message, 'danger');
        throw error;
    }
}

// ===================================
// STATUS UPDATES
// ===================================
function updateStatus() {
    fetch(`/api/server/${sid}`).then(r => r.json()).then(data => {
        if (!document.hidden) { // Only update if tab is visible
            const statusBadge = document.getElementById('status-badge');
            const currentStatus = statusBadge.innerText.trim().toLowerCase();
            // Check if status changed dramatically (crashed/restarted) and force full UI refresh
            if (!currentStatus.includes(data.status)) { location.reload(); return; }
            
            const urlEl = document.getElementById('server-url');
            if (data.url) { urlEl.innerHTML = `<strong>URL:</strong> <a href="${data.url}" target="_blank">${data.url}</a>`;} else { urlEl.innerHTML = '<strong>URL:</strong> Not Available';}
            
            const [cpuEl, memEl, diskEl, uptimeEl, pidEl] = ['server-cpu-usage', 'server-mem-usage', 'server-disk-usage', 'server-uptime', 'server-pid'].map(id => document.getElementById(id));
            
            if (data.stats) {
                diskEl.textContent = formatBytes(data.stats.disk_usage || 0);
                if (data.status === 'running') {
                    cpuEl.textContent = `${data.stats.cpu.toFixed(2)}%`;
                    memEl.textContent = formatBytes(data.stats.memory_rss);
                    uptimeEl.textContent = formatUptime(data.stats.uptime);
                    pidEl.textContent = data.stats.pid;
                } else {
                    [cpuEl, memEl, uptimeEl, pidEl].forEach(el => { el.textContent = '--'; });
                    cpuEl.textContent = '--%';
                }
            }
            
            // Lock/unlock file manager based on server status
            const editor = document.getElementById('code-editor');
            const saveBtn = document.getElementById('save-code-btn');
            const dropZone = document.getElementById('drop-zone');
            const editorOverlay = document.getElementById('editor-status-overlay');
            const isRunning = data.status === 'running';

            editor.readOnly = isRunning;
            saveBtn.disabled = isRunning || currentFile === '';
            editorOverlay.classList.toggle('d-none', !isRunning);
            
            if (isRunning) {
                dropZone.style.pointerEvents = 'none';
                dropZone.style.opacity = '0.6';
            } else {
                dropZone.style.pointerEvents = 'auto';
                dropZone.style.opacity = '1';
            }
            document.querySelectorAll('#file-list button').forEach(b => b.disabled = isRunning);
        }
    });
}

// ===================================
// FILE MANAGEMENT
// ===================================
let currentFile = '';
function fetchAndDisplayFile(filename) {
    fetch(`/api/server/${sid}/file?path=${encodeURIComponent(filename)}`).then(r => r.text()).then(content => {
        document.getElementById('code-editor').value = content;
        document.getElementById('editing-filename').textContent = filename;
        document.getElementById('save-code-btn').disabled = false;
        currentFile = filename;
        // The tab is already shown, this line is not needed and can cause issues.
        // new bootstrap.Tab(document.querySelector('#files-pane')).show(); 
    });
}
function saveFile() {
    const content = document.getElementById('code-editor').value;
    const saveBtn = document.getElementById('save-code-btn');
    saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Saving...'; saveBtn.disabled = true;
    apiFetch(`/api/server/${sid}/file`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({path: currentFile, code: content})})
    .then(data => showToast(data.success)).finally(() => { saveBtn.innerHTML = '<i class="fa-solid fa-save me-1"></i> Save File'; saveBtn.disabled = false; });
}
function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    apiFetch(`/api/server/${sid}/file?path=${encodeURIComponent(filename)}`, { method: 'DELETE' }).then(data => { showToast(data.success); updateFileList(); });
}
function updateFileList() {
    apiFetch(`/api/server/${sid}/files`).then(data => {
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center bg-transparent border-secondary';
                li.innerHTML = `<span><i class="fa-regular fa-file me-2"></i> ${file}</span> <div>
                    <button class="btn btn-outline-primary btn-sm py-0 px-1" onclick="fetchAndDisplayFile('${file}')"><i class="fa-solid fa-pencil"></i></button>
                    <button class="btn btn-outline-danger btn-sm py-0 px-1" onclick="deleteFile('${file}')"><i class="fa-solid fa-trash"></i></button>
                </div>`;
                fileList.appendChild(li);
            });
        } else { fileList.innerHTML = '<li class="list-group-item bg-transparent border-secondary">No files found.</li>'; }
        // After updating the list, re-apply the disabled status from the main status updater
        updateStatus();
    });
}
function uploadFiles(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) { formData.append('files[]', files[i]); }
    document.getElementById('upload-feedback').innerHTML = '<div class="alert alert-info">Uploading...</div>';
    fetch(`/api/server/${sid}/upload`, { method: 'POST', body: formData }).then(r => r.json()).then(data => {
        if (data.success) { showToast(data.success); updateFileList(); document.getElementById('upload-feedback').innerHTML = ''; } 
        else { showToast(data.error || 'Upload failed.', 'danger'); }
    });
}
document.getElementById('banner-upload-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch(`/api/server/${sid}/upload-banner`, { method: 'POST', body: formData })
    .then(r => r.json()).then(data => {
        if(data.success) { showToast(data.success); setTimeout(() => location.reload(), 1000); } else { showToast(data.error, 'danger'); }
    });
});

// ===================================
// BACKUPS
// ===================================
function updateBackupsList() {
    const tableBody = document.getElementById('backups-table');
    tableBody.innerHTML = '<tr><td colspan="4" class="text-center">Loading backups...</td></tr>';
    apiFetch(`/api/server/${sid}/backups`).then(data => {
        tableBody.innerHTML = '';
        if(data.backups && data.backups.length > 0) {
            data.backups.forEach(b => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><i class="fa-solid fa-file-zipper me-2"></i> ${b.name}</td>
                    <td>${formatBytes(b.size)}</td>
                    <td>${new Date(b.modified * 1000).toLocaleString()}</td>
                    <td class="text-end">
                        <a href="/server/${sid}/backups/download/${b.name}" class="btn btn-sm btn-outline-secondary"><i class="fa-solid fa-download"></i></a>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteBackup('${b.name}')"><i class="fa-solid fa-trash"></i></button>
                    </td>`;
                tableBody.appendChild(tr);
            });
        } else {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No backups found.</td></tr>';
        }
    });
}
function deleteBackup(name) {
    if (!confirm(`Delete backup ${name}?`)) return;
    apiFetch(`/api/server/${sid}/backups/delete`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: name}) })
    .then(data => { showToast(data.success); updateBackupsList(); });
}
document.getElementById('create-backup-btn')?.addEventListener('click', e => {
    const btn = e.currentTarget;
    btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Creating...';
    apiFetch(`/api/server/${sid}/backups/create`, { method: 'POST' })
    .then(data => { showToast(data.success); updateBackupsList(); })
    .finally(() => { btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-plus me-1"></i> Create Backup'; });
});

// ===================================
// DATABASES
// ===================================
function updateDbList() {
    apiFetch(`/api/server/${sid}/db/sqlite/list`).then(data => {
        const dbList = document.getElementById('db-list');
        dbList.innerHTML = '';
        if(data.databases && data.databases.length > 0) {
            data.databases.forEach(db => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="mb-1"><i class="fa-solid fa-database me-2"></i> ${db.name}</h5>
                                <p class="mb-2 text-muted small">Size: ${formatBytes(db.size)}</p>
                            </div>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDb('${db.name}')"><i class="fa-solid fa-trash"></i></button>
                        </div>
                        <p class="mb-1 small"><strong>Connection Snippet:</strong></p>
                        <pre class="bg-dark p-2 rounded small font-monospace" style="white-space: pre-wrap;"><code>${ isPython ? `import sqlite3\\nconn = sqlite3.connect('${db.name}')` : `const sqlite3 = require('sqlite3').verbose();\\nconst db = new sqlite3.Database('./${db.name}');` }</code></pre>
                    </div>`;
                dbList.appendChild(card);
            });
        } else {
            dbList.innerHTML = '<p class="text-muted">No SQLite databases found.</p>';
        }
    });
}
function deleteDb(name) {
    if (!confirm(`Delete database ${name}? This cannot be undone.`)) return;
    apiFetch(`/api/server/${sid}/db/sqlite/delete`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: name}) })
    .then(data => { showToast(data.success); updateDbList(); });
}
document.getElementById('create-db-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const dbName = document.getElementById('db-name-input').value;
    apiFetch(`/api/server/${sid}/db/sqlite/create`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: dbName}) })
    .then(data => { showToast(data.success); updateDbList(); e.target.reset(); });
});

// ===================================
// ENVIRONMENT VARIABLES
// ===================================
function updateEnvVarsList() {
    apiFetch(`/api/server/${sid}/env`).then(data => {
        const tableBody = document.getElementById('env-vars-table');
        tableBody.innerHTML = '';
        if (data.env_vars && Object.keys(data.env_vars).length > 0) {
            for (const [key, value] of Object.entries(data.env_vars)) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="font-monospace small">${key}</td>
                    <td class="font-monospace small text-muted">********</td>
                    <td class="text-end"><button class="btn btn-sm btn-outline-danger" onclick="deleteEnvVar('${key}')"><i class="fa-solid fa-trash"></i></button></td>`;
                tableBody.appendChild(tr);
            }
        } else {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No environment variables set.</td></tr>';
        }
    });
}
function deleteEnvVar(key) {
    if (!confirm(`Delete variable ${key}? The server will need to be restarted for this to take effect.`)) return;
    apiFetch(`/api/server/${sid}/env/delete`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: key}) })
    .then(data => { showToast(data.success); updateEnvVarsList(); });
}
document.getElementById('add-env-var-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const key = document.getElementById('env-key-input').value;
    const value = document.getElementById('env-value-input').value;
    apiFetch(`/api/server/${sid}/env/set`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: key, value: value}) })
    .then(data => { showToast(data.success); updateEnvVarsList(); e.target.reset(); });
});


// ===================================
// PACKAGE MANAGEMENT
// ===================================
function updatePackagesList() {
    const pkgTextarea = document.getElementById('packages-list');
    apiFetch(`/api/server/${sid}/packages`).then(data => {
        pkgTextarea.value = data.content || "Could not load package file.";
    });
}
document.getElementById('add-package-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const pkgName = document.getElementById('package-name-input').value;
    const btn = e.currentTarget.querySelector('button[type="submit"]');
    const spinner = document.getElementById('pkg-spinner');
    
    btn.disabled = true; spinner.classList.remove('d-none');
    
    apiFetch(`/api/server/${sid}/packages/install`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: pkgName}) })
    .then(data => { 
        showToast(data.success); 
        updatePackagesList(); 
        e.target.reset(); 
        // Also refresh logs in case there were install errors
        const logIframe = document.querySelector('#console-pane iframe');
        if (logIframe) logIframe.src = logIframe.src;
    })
    .finally(() => { btn.disabled = false; spinner.classList.add('d-none'); });
});


// ===================================
// DOM READY & EVENT LISTENERS
// ===================================
document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    updateStatus();

    // Interval for live status
    setInterval(updateStatus, 3000);

    // File Manager Listeners
    document.getElementById('save-code-btn').addEventListener('click', saveFile);
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => uploadFiles(e.target.files));
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => dropZone.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }));
    ['dragenter', 'dragover'].forEach(eventName => dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over')));
    ['dragleave', 'drop'].forEach(eventName => dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over')));
    dropZone.addEventListener('drop', (e) => uploadFiles(e.dataTransfer.files));

    // Tab-based data loading
    const serverTabs = document.querySelectorAll('#server-tabs button[data-bs-toggle="tab"]');
    serverTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', event => {
            const paneId = event.target.getAttribute('data-bs-target');
            if (paneId === '#files-pane') updateFileList();
            if (paneId === '#backups-pane') updateBackupsList();
            if (paneId === '#db-pane') updateDbList();
            if (paneId === '#env-pane') updateEnvVarsList();
            if (paneId === '#packages-pane') updatePackagesList();
        });
    });
    // Trigger initial load for the active tab (Settings)
    // No dynamic data needed for settings tab on load
});
</script>
{% endblock %}
"""

LOGIN_TEMPLATE = """
{% extends 'layout' %}
{% block content %}
<div class="row justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="col-md-6 col-lg-5 col-xl-4">
        <div class="card">
            <div class="card-header text-center"><h3><i class="fa-solid fa-right-to-bracket me-2"></i> User Login</h3></div>
            <div class="card-body p-4">
                <form method="post">
                    <div class="mb-3"><label for="username" class="form-label">Username</label><input type="text" name="username" class="form-control" required></div>
                    <div class="mb-3"><label for="password" class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
                    <div class="d-grid"> <button type="submit" class="btn btn-primary btn-lg">Sign In</button> </div>
                </form>
                {% if has_users %}<div class="text-center mt-3"> <a href="{{ url_for('register') }}" class="text-decoration-none small">Don't have an account? Register</a> </div>{% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

REGISTER_TEMPLATE = """
{% extends 'layout' %}
{% block content %}
<div class="row justify-content-center align-items-center" style="min-height: 70vh;">
    <div class="col-md-6 col-lg-5 col-xl-4">
        <div class="card">
            <div class="card-header text-center"><h3><i class="fa-solid fa-user-plus me-2"></i> Create Account</h3></div>
            <div class="card-body p-4">
                {% if not has_users %}<div class="alert alert-info">Welcome! As the first user, you will be the administrator.</div>{% endif %}
                <form method="post">
                    <div class="mb-3"><label for="username" class="form-label">Username</label><input type="text" name="username" class="form-control" required></div>
                    <div class="mb-3"><label for="password" class="form-label">Password</label><input type="password" name="password" class="form-control" required></div>
                    <div class="d-grid"> <button type="submit" class="btn btn-primary btn-lg">Create Account</button> </div>
                </form>
                {% if has_users %}<div class="text-center mt-3"> <a href="{{ url_for('login') }}" class="text-decoration-none small">Already have an account? Login</a> </div>{% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_TEMPLATE = """
{% extends 'layout' %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fa-solid fa-table-columns me-2"></i> Dashboard</h2>
    {% if not servers %}
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createServerModal"><i class="fa-solid fa-plus me-1"></i> Create Server</button>
    {% else %}
        <button class="btn btn-secondary" disabled title="You can only create one server per account.">Create Server</button>
    {% endif %}
</div>

<div class="modal fade" id="createServerModal" tabindex="-1">
  <div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">Create New Server</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
      <form action="{{ url_for('create') }}" method="post"><div class="modal-body">
            <div class="mb-3"><label for="name" class="form-label">Server Name</label><input type="text" name="name" class="form-control" placeholder="my-awesome-bot" required></div>
            <div class="mb-3"><label for="type" class="form-label">Server Type</label>
                <select name="type" class="form-select">
                    <optgroup label="Python"><option value="python-flask">Python Flask (Web)</option><option value="python-generic">Generic Python (Script)</option></optgroup>
                    <optgroup label="Node.js"><option value="nodejs-express">Node.js Express (Web)</option><option value="nodejs-generic">Generic Node.js (Script)</option></optgroup>
                </select>
            </div>
      </div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button><button type="submit" class="btn btn-primary">Create</button></div></form>
    </div></div>
</div>

<div class="card"><div class="card-header"><i class="fa-solid fa-server me-2"></i> Your Server</div>
    <div class="card-body p-0">
        {% if not servers %} <p class="text-center p-4">You haven't created a server yet. Click the button above to start!</p>
        {% else %}
        <div class="table-responsive"><table class="table table-hover table-flush mb-0">
            <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>CPU / Mem</th><th>Disk</th><th>URL</th><th>Actions</th></tr></thead>
            <tbody>
            {% for s in servers %}
                <tr id="server-{{ s.id }}">
                    <td><strong><a href="{{ url_for('server_view', sid=s.id) }}" class="text-decoration-none text-light">{{ s.name }}</a></strong></td>
                    <td><span class="badge" style="background-color: var(--dark-color-3); color: var(--text-muted);">{{ s.type }}</span></td>
                    <td><span class="badge status-badge {% if s.status == 'running' %} bg-success {% else %} bg-danger {% endif %}"><i class="fa-solid fa-circle me-1"></i> {{ s.status }}</span></td>
                    <td class="server-stats font-monospace small">--</td>
                    <td class="server-disk font-monospace small">--</td>
                    <td class="server-url">{% if s.url %}<a href="{{ s.url }}" target="_blank">{{ s.url }}</a>{% else %}-{% endif %}</td>
                    <td><div class="btn-group">
                        {% if s.status == 'running' %}
                        <form action="{{ url_for('stop_server_action', sid=s.id) }}" method="post" class="d-inline"><button type="submit" class="btn btn-warning btn-sm" title="Stop"><i class="fa-solid fa-stop"></i></button></form>
                        {% else %}
                        <form action="{{ url_for('start_server_action', sid=s.id) }}" method="post" class="d-inline"><button type="submit" class="btn btn-success btn-sm" title="Start"><i class="fa-solid fa-play"></i></button></form>
                        {% endif %}
                        <a href="{{ url_for('server_view', sid=s.id) }}" class="btn btn-primary btn-sm" title="Manage"><i class="fa-solid fa-pencil"></i></a>
                        <form action="{{ url_for('delete_server_action', sid=s.id) }}" method="post" class="d-inline" onsubmit="return confirm('DELETE server? This is irreversible.');"><button type="submit" class="btn btn-danger btn-sm" title="Delete"><i class="fa-solid fa-trash"></i></button></form>
                    </div></td>
                </tr>
            {% endfor %}
            </tbody></table></div>
        {% endif %}
    </div></div>
{% endblock %}
{% block scripts %}
<script>
function formatBytes(bytes, decimals = 1) {
    if (!+bytes) return '0 B'; const k = 1024; const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']; const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}
function updateServerStatus() {
    const rows = document.querySelectorAll('tr[id^="server-"]'); if (rows.length === 0) return;
    rows.forEach(row => {
        const sid = row.id.split('-')[1];
        fetch(`/api/server/${sid}`).then(response => response.json()).then(data => {
            if (data.error) return;
            const currentStatus = row.querySelector('.status-badge').innerText.trim().toLowerCase();
            if (!currentStatus.includes(data.status)) { location.reload(); return; }
            
            const urlCell = row.querySelector('.server-url');
            if (data.url) { urlCell.innerHTML = `<a href="${data.url}" target="_blank" title="${data.url}">Public Link</a>`; } else { urlCell.innerHTML = '-'; }

            const statsCell = row.querySelector('.server-stats');
            const diskCell = row.querySelector('.server-disk');
            if (data.stats) {
                if (data.status === 'running') {
                    statsCell.innerHTML = `${data.stats.cpu.toFixed(1)}% / ${formatBytes(data.stats.memory_rss)}`;
                } else {
                    statsCell.innerHTML = '--';
                }
                diskCell.innerHTML = formatBytes(data.stats.disk_usage || 0);
            } else {
                statsCell.innerHTML = '--';
                diskCell.innerHTML = '--';
            }
        }).catch(err => console.error("Failed to update server status for " + sid));
    });
}
setInterval(updateServerStatus, 5000);
document.addEventListener('DOMContentLoaded', updateServerStatus);
</script>
{% endblock %}
"""

# The logs template controls the display inside the iframe
LOGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta http-equiv="refresh" content="5"><title>Logs</title>
<style>
/* Matched to Fira Code, dark theme */
body { background-color: #111111; color: #dcdcdc; font-family: 'Fira Code', monospace; font-size: 0.9em; word-wrap: break-word; padding: 10px; margin: 0; } 
pre { white-space: pre-wrap; word-wrap: break-word; margin: 0;}
/* Color hints for logs */
.log-start { color: #50fa7b; font-weight: bold; } /* Green */
.log-error { color: #ff5555; font-weight: bold; } /* Red */
.log-info { color: #8be9fd; } /* Cyan */
.log-command { color: #ff79c6; } /* Pink */
</style>
</head><body><pre>{{ logs|safe }}</pre><script>window.scrollTo(0, document.body.scrollHeight);</script></body></html>
"""

SETTINGS_TEMPLATE = """
{% extends 'layout' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card">
            <div class="card-header text-center"><h3><i class="fa-solid fa-gear me-2"></i> Account Settings</h3></div>
            <div class="card-body p-4">
                <form method="post">
                    <h5 class="mb-3">Change Password</h5>
                    <div class="mb-3"><label for="current_password" class="form-label">Current Password</label><input type="password" name="current_password" class="form-control" required></div>
                    <div class="mb-3"><label for="new_password" class="form-label">New Password</label><input type="password" name="new_password" class="form-control" required></div>
                    <div class="mb-3"><label for="confirm_password" class="form-label">Confirm New Password</label><input type="password" name="confirm_password" class="form-control" required></div>
                    <div class="d-grid"><button type="submit" class="btn btn-primary btn-lg">Update Password</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

# ===============================================================
# APP INITIALIZATION & CONFIGURATION
# ===============================================================

BASE_DIR = Path.cwd()
USERS_DIR = BASE_DIR / "users"
DATA_FILE = BASE_DIR / "data.json"
DEFAULT_APP_PORT = 5000
PORT_LOCK = threading.Lock()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", uuid.uuid4().hex)
app.jinja_loader = DictLoader({'layout': LAYOUT_TEMPLATE, 'logs_view_template': LOGS_TEMPLATE})
# Registering 'random' utility needed for SERVER_TEMPLATE banner cache busting
# NOTE: This only provides random.randint() via 'random'. For the template usage 'range(1, 1000) | random' to work,
# a custom 'random' filter or 'range' global would be needed, which is beyond this scope, 
# but the original code snippet is preserved.
app.jinja_env.globals.update(random=random.randint, range=range) 

runtime = {"servers": {}, "next_port": DEFAULT_APP_PORT}
USERS_DIR.mkdir(exist_ok=True)

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}, "servers": {}}

def save_data():
    with open(DATA_FILE, "w") as f: json.dump(DATA, f, indent=2)

DATA = load_data()

# ===============================================================
# SERVER MANAGEMENT CORE
# ===============================================================

def _persist_servers():
    DATA.setdefault("servers", {})
    for sid, s in runtime["servers"].items():
        DATA["servers"][sid] = {"owner": s["owner"], "name": s["name"], "type": s["type"], "port": s.get("port"), "path": s["path"], "status": "stopped"}
    save_data()

def _load_servers():
    for sid, meta in DATA.get("servers", {}).items():
        if not all(k in meta for k in ["owner", "name", "type", "path"]): continue
        if not Path(meta["path"]).exists(): continue
        runtime["servers"][sid] = {
            "id": sid, "owner": meta["owner"], "name": meta["name"], "type": meta["type"], "port": meta.get("port"),
            "process": None, "tunnel_proc": None, "psutil_proc": None, "url": None, "status": "stopped", "path": meta["path"]
        }
    ports = [int(s.get("port", 0)) for s in runtime["servers"].values() if s.get("port")]
    runtime["next_port"] = max(ports) + 1 if ports else DEFAULT_APP_PORT

def _run_command_and_log(cmd, server_path, log_file, timeout=300):
    """Runs a blocking command (like install) and pipes output to logs."""
    try:
        is_windows = os.name == 'nt'
        proc = subprocess.run(cmd, cwd=str(server_path), capture_output=True, text=True, timeout=timeout, shell=is_windows, errors="ignore")
        
        # Enhanced logging for external commands
        with log_file.open("a", encoding="utf-8", errors="ignore") as f:
            f.write(f"\n--- Running Command: <span class='log-command'>{' '.join(cmd)}</span> ---\n")
            f.write(proc.stdout)
            if proc.stderr:
                 f.write(f"\n--- STDERR ---\n")
                 f.write(proc.stderr)
            f.write(f"\n--- Command finished with exit code {proc.returncode} ---\n")
        
        return proc.returncode == 0
    except Exception as e:
        with log_file.open("a") as f: f.write(f"[ERROR] during command '{' '.join(cmd)}': {e}\n")
        return False
        
def find_entry_file(spath, stype):
    is_node = stype.startswith('nodejs')
    entry_order = ["index.js", "server.js", "app.js"] if is_node else ["app.py", "main.py", "server.py"]
    glob_pattern = "*.js" if is_node else "*.py"
    for fname in entry_order:
        if (spath / fname).exists(): return spath / fname
    files = list(spath.glob(glob_pattern))
    return files[0] if files else None

def _stream_logs(sid, proc, log_file):
    """Continuously reads stdout/stderr from the server process and writes to the log file."""
    s = runtime["servers"].get(sid)
    if not s: return

    # We must ensure continuous reading of the pipe to prevent buffer deadlock
    try:
        # We need a file handle to append logs
        with log_file.open("a", encoding="utf-8", errors="ignore") as f:
            # Proc.stdout is the pipe handle from Popen
            for line in iter(proc.stdout.readline, ''):
                # Basic check to stop streaming if the server is explicitly stopped in runtime
                if s["status"] != "running" and proc.poll() is not None:
                    break
                f.write(line)
                f.flush() # Essential for real-time viewing
    except ValueError:
        # Expected if the process/pipe is closed externally (e.g., terminated)
        pass
    except Exception as e:
        print(f"Log streaming thread error for {s['name']}: {e}")
        
    finally:
        # If the log stream closes, check if the process died unexpectedly
        if proc.poll() is None and s["status"] == "running":
            # Process still exists but stream ended, mark it for review/stop
            with log_file.open("a") as f: f.write(f"\n<span class='log-error'>--- WARNING: Log pipe closed unexpectedly ({time.ctime()}). Server might be unstable. ---</span>\n")
            
def start_server(sid):
    s = runtime["servers"].get(sid)
    if not s or s.get("process"): return False, "already running"
    spath, logf = logs_path(s["owner"], s["name"]).parent, logs_path(s["owner"], s["name"])
    logf.parent.mkdir(parents=True, exist_ok=True)
    
    with logf.open("a", encoding="utf-8", errors="ignore") as f: 
        f.write(f"\n<span class='log-start'>--- Starting server at {time.ctime()} ---</span>\n")

    # Install dependencies (blocking commands, log output immediately)
    is_node = s["type"].startswith('nodejs')
    if is_node and (spath / "package.json").exists():
        _run_command_and_log(["npm", "install"], spath, logf)
    elif not is_node and (spath / "requirements.txt").exists():
        _run_command_and_log(["python3", "-m", "pip", "install", "-r", "requirements.txt"], spath, logf)

    entry = find_entry_file(spath, s["type"])
    if not entry:
        with logf.open("a") as f: f.write("<span class='log-error'>No entry file found (e.g., app.py, index.js)</span>\n")
        return False, "no entry file"
    
    port = get_free_port(); s["port"] = port
    env = os.environ.copy(); env["PORT"] = str(port)
    env_path = env_file_path(s['owner'], s['name'])
    if env_path.exists():
        with env_path.open('r') as f: user_env = json.load(f)
        for k, v in user_env.items(): env[k] = str(v)

    cmd = ["node", str(entry)] if is_node else ["python3", "-u", str(entry)]
    
    # Start the process non-blocking, capturing stdout/stderr
    proc = subprocess.Popen(cmd, cwd=str(spath), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, bufsize=1, errors="ignore")
    s["process"] = proc
    
    # Start the log streaming thread IMMEDIATELY to capture potential crash output
    threading.Thread(target=_stream_logs, args=(sid, proc, logf), daemon=True).start()
    
    # Give the process half a second to crash/exit if there's a startup error
    time.sleep(0.5) 
    
    # CRITICAL FIX: Check if the process died immediately before setting status to running
    if proc.poll() is not None:
        s["process"] = None
        s["psutil_proc"] = None
        s["status"] = "stopped"
        with logf.open("a") as f: f.write(f"\n<span class='log-error'>--- Process crashed immediately on startup (Exit code: {proc.poll()}) ---</span>\n")
        return False, "process crashed immediately"
        
    # If successful, finalize state
    try: s["psutil_proc"] = psutil.Process(proc.pid)
    except psutil.NoSuchProcess: pass
    s["status"] = "running"

    if "flask" in s["type"] or "express" in s["type"]:
        threading.Thread(target=_start_tunnel, args=(sid, port), daemon=True).start()
    
    return True, "started"

def stop_server(sid):
    s = runtime["servers"].get(sid)
    if not s or not s.get("process"):
        s["status"] = "stopped"
        return True, "already stopped"
    
    # Terminate process tree
    try:
        parent = psutil.Process(s["process"].pid)
        for child in parent.children(recursive=True): child.terminate()
        parent.terminate()
        gone, alive = psutil.wait_procs([parent], timeout=5)
        for p in alive: p.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied): pass

    # Important: The log streaming thread will terminate naturally when the pipe closes.
    s["process"], s["psutil_proc"], s["status"] = None, None, "stopped"
    
    if s.get("tunnel_proc"):
        try: s["tunnel_proc"].terminate()
        except Exception: pass
        s["tunnel_proc"], s["url"] = None, None
        
    with logs_path(s["owner"], s["name"]).open("a") as f: 
        f.write(f"\n<span class='log-error'>--- Server stopped at {time.ctime()} ---</span>\n")
    return True, "stopped"

def _start_tunnel(sid, port):
    s = runtime["servers"].get(sid); logf = logs_path(s["owner"], s["name"])
    if not s: return
    try:
        # Run cloudflared synchronously or capture its output to prevent zombie processes,
        # but since we need to extract the URL, we stick to Popen and read stdout.
        proc = subprocess.Popen(["cloudflared", "tunnel", "--url", f"http://localhost:{port}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, errors="ignore")
        s["tunnel_proc"] = proc
        
        # Stream tunnel output to logs as well (using a simple loop here since it's short-lived)
        for line in iter(proc.stdout.readline, ''):
            m = re.search(r"https?://[^\s]+\.trycloudflare\.com", line)
            with logf.open("a") as f: f.write(f"[Tunnel] {line}")
            if m: 
                s["url"] = m.group(0)
                with logf.open("a") as f: f.write(f"\n<span class='log-info'>--- Public URL: {s['url']} ---</span>\n")
                break
    except Exception as e:
        with logf.open("a") as f: f.write(f"<span class='log-error'>[Tunnel Error] Could not start cloudflared. Is it in your PATH?</span>\n[detail] {e}\n")

def create_server(owner, name, stype):
    name = secure_filename(name); sid = uuid.uuid4().hex[:12]
    sdir = server_dir(owner, name)
    if not name or sdir.exists(): return None, "Server name invalid or already exists."
    sdir.mkdir(parents=True, exist_ok=True)
    
    is_node = stype.startswith('nodejs')
    if is_node:
        entry_name = "index.js"
        if stype == 'nodejs-express':
            default_code = 'const express = require("express");\nconst app = express();\nconst port = process.env.PORT || 3000;\n\napp.get("/", (req, res) => res.send("Hello from GenBot Express!"));\n\napp.listen(port, () => console.log(`Server listening on port ${port}`));'
            pkg_json = {"name": name, "version": "1.0.0", "main": "index.js", "dependencies": {"express": "^4.18.2"}}
            (sdir / "package.json").write_text(json.dumps(pkg_json, indent=2))
        else: default_code = 'console.log("Hello from GenBot!");'
    else:
        entry_name = "app.py" if stype == "python-flask" else "main.py"
        if stype == 'python-flask':
            default_code = 'from flask import Flask\nimport os\n\napp=Flask(__name__)\n\n@app.route("/")\ndef hello():\n  return "Hello from GenBot Flask!"\n\nif __name__ == "__main__":\n  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))'
            (sdir / "requirements.txt").write_text("Flask\n")
        else: default_code = 'import time\n\nprint("Hello from GenBot!")\nfor i in range(5):\n    print(f"Count: {i+1}")\n    time.sleep(1)'

    (sdir / entry_name).write_text(default_code, encoding="utf-8")
    logs_path(owner, name).write_text(f"--- created {name} at {time.ctime()} ---\n")
    env_file_path(owner, name).write_text(json.dumps({}))
    runtime["servers"][sid] = {"id": sid, "owner": owner, "name": name, "type": stype, "port": None, "process": None, "tunnel_proc": None, "psutil_proc": None, "url": None, "status": "stopped", "path": str(sdir)}
    _persist_servers()
    return sid, "Server created successfully."

def delete_server(sid):
    s = runtime["servers"].get(sid)
    if not s: return False, "not found"
    stop_server(sid)
    try: shutil.rmtree(s["path"])
    except Exception: pass
    runtime["servers"].pop(sid, None); DATA["servers"].pop(sid, None); save_data()
    return True, "deleted"

_load_servers()

# ===============================================================
# UTILS & ROUTE HELPERS
# ===============================================================

def current_user(): return session.get("user")
def is_logged_in(): return "user" in session
def user_dir(u): return USERS_DIR / u
def server_dir(u, n): return user_dir(u) / "servers" / n
def logs_path(u, n): return server_dir(u, n) / "logs.txt"
def backups_dir(u, n): d = server_dir(u, n) / "backups"; d.mkdir(exist_ok=True); return d
def env_file_path(u,n): return server_dir(u,n) / ".env.json"
def get_free_port():
    with PORT_LOCK: p = runtime["next_port"]; runtime["next_port"] += 1; return p

def get_dir_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(): total += entry.stat().st_size
            elif entry.is_dir(): total += get_dir_size(entry.path)
    except FileNotFoundError: return 0
    return total

@app.before_request
def check_setup():
    if not DATA['users'] and request.endpoint not in ['register', 'static']: return redirect(url_for('register'))
    if DATA['users'] and not is_logged_in() and request.endpoint not in ['login', 'register', 'static']: return redirect(url_for('login'))

# ===============================================================
# STANDARD ROUTES (Auth, Dashboard, etc.)
# ===============================================================

@app.route("/")
def index(): return redirect(url_for('dashboard'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in(): return redirect(url_for('dashboard'))
    if not DATA['users']: return redirect(url_for('register'))
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        user_hash = DATA.get("users", {}).get(username)
        if user_hash and check_password_hash(user_hash, password):
            session["user"] = username; return redirect(url_for('dashboard'))
        else: flash("Invalid credentials.", "danger")
    return render_template_string(LOGIN_TEMPLATE, has_users=bool(DATA['users']))

@app.route("/register", methods=["GET", "POST"])
def register():
    if is_logged_in(): return redirect(url_for('dashboard'))
    error = None
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        if username in DATA.get("users", {}): error = "Username already exists."
        elif not re.match(r"^\w+$", username): error = "Username must be alphanumeric."
        else:
            DATA.setdefault("users", {})[username] = generate_password_hash(password)
            user_dir(username).mkdir(exist_ok=True); save_data()
            session["user"] = username; return redirect(url_for('dashboard'))
    if error: flash(error, "danger")
    return render_template_string(REGISTER_TEMPLATE, has_users=bool(DATA['users']))

@app.route("/logout")
def logout(): session.pop("user", None); return redirect(url_for('login'))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not is_logged_in(): return redirect(url_for('login'))
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password, confirm_password = request.form.get("new_password"), request.form.get("confirm_password")
        if not check_password_hash(DATA["users"][current_user()], current_password): flash("Your current password was incorrect.", "danger")
        elif new_password != confirm_password: flash("New passwords do not match.", "danger")
        elif len(new_password) < 4: flash("New password is too short.", "danger")
        else:
            DATA["users"][current_user()] = generate_password_hash(new_password)
            save_data(); flash("Password updated successfully!", "success")
        return redirect(url_for('settings'))
    return render_template_string(SETTINGS_TEMPLATE)

@app.route("/dashboard")
def dashboard():
    if not is_logged_in(): return redirect(url_for('login'))
    user_servers = sorted([s for s in runtime["servers"].values() if s["owner"] == current_user()], key=lambda x: x["name"])
    return render_template_string(DASHBOARD_TEMPLATE, servers=user_servers)

# ===============================================================
# SERVER MANAGEMENT ROUTES
# ===============================================================

@app.route("/create", methods=["POST"])
def create():
    if not is_logged_in(): return redirect(url_for('login'))
    if any(s for s in runtime["servers"].values() if s["owner"] == current_user()):
        flash("You can only create one server per account.", "danger")
        return redirect(url_for('dashboard'))
    
    sid, msg = create_server(current_user(), request.form["name"], request.form["type"])
    if sid: flash(msg, "success")
    else: flash(msg, "danger")
    return redirect(url_for('dashboard'))

@app.route("/server/<sid>")
def server_view(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return "Not Found", 404
    
    return render_template_string(SERVER_TEMPLATE, server=s)

@app.route("/server/<sid>/banner.png")
def server_banner(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return "Not Found", 404
    banner_path = Path(s['path']) / "banner.png"
    if banner_path.exists():
        return send_file(banner_path, mimetype='image/png')
    
    # Placeholder for static files if running in a production environment without a static folder setup
    # If a static folder exists, Flask handles static files automatically.
    
    # Try to provide a minimal fallback (Requires a file named 'default_banner.png' in the static folder)
    default_banner_path = Path(app.root_path) / 'static/default_banner.png'
    if default_banner_path.exists():
        return send_file(default_banner_path, mimetype='image/png')
    
    # If no default exists, send 404/Empty.
    return "", 404


@app.route("/server/<sid>/start", methods=["POST"])
def start_server_action(sid):
    s = runtime["servers"].get(sid)
    if s and s["owner"] == current_user(): 
        success, msg = start_server(sid)
        if success: flash(f"Server starting...", "info")
        else: flash(f"Failed to start server: {msg}", "danger")
    return redirect(request.referrer or url_for('dashboard'))

@app.route("/server/<sid>/stop", methods=["POST"])
def stop_server_action(sid):
    s = runtime["servers"].get(sid)
    if s and s["owner"] == current_user(): 
        stop_server(sid)
        flash("Server stopped.", "warning")
    return redirect(request.referrer or url_for('dashboard'))

@app.route("/server/<sid>/restart", methods=["POST"])
def restart_server_action(sid):
    s = runtime["servers"].get(sid)
    if s and s["owner"] == current_user():
        was_running = s['status'] == 'running'
        if was_running: stop_server(sid); time.sleep(1)
        start_server(sid)
        flash("Server restarted." if was_running else "Server started.", "success")
    return redirect(request.referrer or url_for('dashboard'))

@app.route("/server/<sid>/delete", methods=["POST"])
def delete_server_action(sid):
    s = runtime["servers"].get(sid)
    if s and s["owner"] == current_user():
        delete_server(sid)
        flash("Server deleted successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route("/logs/<sid>")
def logs_view(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return "Not Found", 404
    log_file = logs_path(s["owner"], s["name"])
    
    # Read logs, ensuring it is HTML safe, and apply color markup
    logs = log_file.read_text(encoding="utf-8", errors="ignore") if log_file.exists() else "No logs yet."
    
    # Basic log highlighting using HTML spans defined in LOGS_TEMPLATE style block
    logs = logs.replace("--- Starting server", "<span class='log-start'>--- Starting server")
    logs = logs.replace("--- Server stopped", "<span class='log-error'>--- Server stopped")
    logs = logs.replace("--- Public URL:", "<span class='log-info'>--- Public URL:")
    logs = logs.replace("--- Running Command:", "<span class='log-command'>--- Running Command:")
    
    # Close any open spans at line breaks for robustness (simple replacement might miss some closing tags)
    # This is a crude fix; a proper log parser is better, but this handles common cases.
    logs = logs.replace("---", "---</span>") 
    
    # If the process is dead and status is running (race condition), attempt to update the status in logs
    if s.get("process") and s["process"].poll() is not None and s["status"] == "running":
         logs += f"\n<span class='log-error'>--- Process died unexpectedly at {time.ctime()} ---</span>"

    return render_template_string(LOGS_TEMPLATE, logs=logs)

@app.route("/server/<sid>/backups/download/<filename>")
def download_backup(sid, filename):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return "Forbidden", 403
    safe_filename = secure_filename(filename)
    backup_file = backups_dir(s['owner'], s['name']) / safe_filename
    if backup_file.exists():
        return send_file(backup_file, as_attachment=True)
    return "Not Found", 404

# ===============================================================
# API ROUTES
# ===============================================================

@app.route("/api/server/<sid>")
def api_server_status(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "not found"}), 404
    
    # Check if the process died since last check
    proc = s.get("process")
    if proc and proc.poll() is not None: 
        stop_server(sid) # Clean up state if dead
        
    stats = {}
    if s["status"] == "running" and s.get("psutil_proc"):
        try:
            p = s["psutil_proc"]
            # Recalculate CPU/Memory usage for the entire process tree
            with p.oneshot():
                # Get the process's own stats
                cpu_percent = p.cpu_percent()
                mem_info = p.memory_info()
                
                # Aggregate stats from children
                children = p.children(recursive=True)
                for child in children:
                    try:
                        cpu_percent += child.cpu_percent()
                        mem_info.rss += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied): continue
                
                stats = {"cpu": cpu_percent, "memory_rss": mem_info.rss, "uptime": time.time() - p.create_time(), "pid": p.pid}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            stop_server(sid) # Mark as stopped if process is gone
            
    stats["disk_usage"] = get_dir_size(s['path'])
    return jsonify({"id": sid, "status": s["status"], "url": s.get("url"), "stats": stats})

# ... File Management API ...
@app.route("/api/server/<sid>/files")
def list_files(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    server_path = Path(s['path'])
    try:
        files = sorted([f.name for f in server_path.iterdir() if f.is_file() and f.name not in ['logs.txt', '.env.json', 'banner.png']])
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": f"Could not list files: {e}"}), 500

@app.route("/api/server/<sid>/file", methods=["GET", "POST", "DELETE"])
def manage_file(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    
    server_path = Path(s['path']).resolve()
    
    if request.method == "GET":
        filename = request.args.get('path')
    elif request.method == "POST":
        filename = request.json.get('path')
    elif request.method == "DELETE":
        filename = request.args.get('path')

    if not filename: return jsonify({"error": "Filename is required"}), 400
    
    safe_name = secure_filename(filename)
    if safe_name != filename: return jsonify({"error": "Invalid filename"}), 400
    
    file_path = (server_path / safe_name).resolve()
    
    # Security check: ensure the file is within the server's directory
    if not str(file_path).startswith(str(server_path)):
        return jsonify({"error": "Access denied"}), 403

    if request.method == "GET":
        if not file_path.exists(): return "File not found", 404
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if s['status'] == 'running':
        return jsonify({"error": "Cannot modify files while server is running."}), 403

    if request.method == "POST":
        code = request.json.get('code', '')
        file_path.write_text(code, encoding="utf-8")
        return jsonify({"success": f"File '{safe_name}' saved."})
    
    if request.method == "DELETE":
        if not file_path.exists(): return jsonify({"error": "File not found"}), 404
        file_path.unlink()
        return jsonify({"success": f"File '{safe_name}' deleted."})

@app.route("/api/server/<sid>/upload", methods=["POST"])
def upload_files(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    if s['status'] == 'running': return jsonify({"error": "Cannot upload while server is running."}), 403

    files = request.files.getlist("files[]")
    if not files: return jsonify({"error": "No files uploaded"}), 400
    
    server_path = Path(s['path'])
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(server_path / filename)
            
    return jsonify({"success": f"{len(files)} file(s) uploaded successfully."})

@app.route("/api/server/<sid>/upload-banner", methods=["POST"])
def upload_banner(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    file = request.files.get('banner')
    if not file or file.filename == '': return jsonify({"error": "No file selected."}), 400
    if file.mimetype != 'image/png': return jsonify({"error": "File must be a PNG image."}), 400
    
    server_path = Path(s['path'])
    file.save(server_path / "banner.png")
    return jsonify({"success": "Banner updated successfully."})
    
# ... Backup Management API ...
@app.route("/api/server/<sid>/backups", methods=["GET"])
def list_backups(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    bdir = backups_dir(s['owner'], s['name'])
    backups = []
    for f in bdir.glob('*.zip'):
        stat = f.stat()
        backups.append({"name": f.name, "size": stat.st_size, "modified": stat.st_mtime})
    return jsonify({"backups": sorted(backups, key=lambda x: x['modified'], reverse=True)})

@app.route("/api/server/<sid>/backups/create", methods=["POST"])
def create_backup(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    s_dir = server_dir(s['owner'], s['name'])
    b_dir = backups_dir(s['owner'], s['name'])
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    archive_name = b_dir / f"backup-{s['name']}-{ts}"
    try:
        shutil.make_archive(str(archive_name), 'zip', str(s_dir))
        return jsonify({"success": "Backup created successfully."})
    except Exception as e:
        return jsonify({"error": f"Backup failed: {e}"}), 500

@app.route("/api/server/<sid>/backups/delete", methods=["POST"])
def delete_backup_api(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    filename = request.json.get('name')
    if not filename: return jsonify({"error": "Filename required"}), 400
    
    file_path = backups_dir(s['owner'], s['name']) / secure_filename(filename)
    if file_path.exists():
        file_path.unlink()
        return jsonify({"success": f"Backup '{filename}' deleted."})
    return jsonify({"error": "File not found"}), 404

# ... SQLite Database API ...
@app.route("/api/server/<sid>/db/sqlite/list")
def list_sqlite_dbs(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    s_dir = Path(s['path'])
    dbs = [{"name": f.name, "size": f.stat().st_size} for f in s_dir.glob('*.sqlite')]
    return jsonify({"databases": dbs})

@app.route("/api/server/<sid>/db/sqlite/create", methods=["POST"])
def create_sqlite_db(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    db_name = request.json.get('name')
    if not db_name or not re.match(r"^\w+$", db_name): return jsonify({"error": "Invalid database name."}), 400

    db_file = Path(s['path']) / f"{secure_filename(db_name)}.sqlite"
    if db_file.exists(): return jsonify({"error": "Database already exists."}), 400
    
    try:
        conn = sqlite3.connect(str(db_file))
        conn.close()
        return jsonify({"success": f"Database '{db_file.name}' created."})
    except Exception as e:
        return jsonify({"error": f"Failed to create database: {e}"}), 500
        
@app.route("/api/server/<sid>/db/sqlite/delete", methods=["POST"])
def delete_sqlite_db(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    filename = request.json.get('name')
    if not filename: return jsonify({"error": "Filename required"}), 400
    
    file_path = Path(s['path']) / secure_filename(filename)
    if file_path.suffix == '.sqlite' and file_path.exists():
        file_path.unlink()
        return jsonify({"success": f"Database '{filename}' deleted."})
    return jsonify({"error": "File not found or invalid"}), 404

# ... Environment Variable API ...
@app.route("/api/server/<sid>/env", methods=["GET"])
def get_env_vars(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    env_path = env_file_path(s['owner'], s['name'])
    if env_path.exists():
        with env_path.open('r') as f: return jsonify({"env_vars": json.load(f)})
    return jsonify({"env_vars": {}})

@app.route("/api/server/<sid>/env/set", methods=["POST"])
def set_env_var(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    key, value = request.json.get('key'), request.json.get('value')
    if not key: return jsonify({"error": "Key is required."}), 400
    
    env_path = env_file_path(s['owner'], s['name'])
    env_vars = json.load(env_path.open('r')) if env_path.exists() else {}
    env_vars[key] = value
    with env_path.open('w') as f: json.dump(env_vars, f, indent=2)
    return jsonify({"success": f"Variable {key} set. Restart server to apply."})

@app.route("/api/server/<sid>/env/delete", methods=["POST"])
def delete_env_var(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    key = request.json.get('key')
    env_path = env_file_path(s['owner'], s['name'])
    if env_path.exists():
        env_vars = json.load(env_path.open('r'))
        if key in env_vars:
            del env_vars[key]
            with env_path.open('w') as f: json.dump(env_vars, f, indent=2)
            return jsonify({"success": f"Variable {key} deleted. Restart server to apply."})
    return jsonify({"error": "Variable not found."}), 404
    
# ... Package Management API ...
@app.route("/api/server/<sid>/packages", methods=["GET"])
def get_packages(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    is_node = 'nodejs' in s['type']
    pkg_file = Path(s['path']) / ("package.json" if is_node else "requirements.txt")
    if pkg_file.exists():
        return jsonify({"content": pkg_file.read_text()})
    return jsonify({"content": "# File not found. Will be created on first install."})

@app.route("/api/server/<sid>/packages/install", methods=["POST"])
def install_package(sid):
    s = runtime["servers"].get(sid)
    if not s or s["owner"] != current_user(): return jsonify({"error": "unauthorized"}), 401
    pkg_name = request.json.get('name', '').strip()
    if not pkg_name: return jsonify({"error": "Package name required."}), 400
    
    is_node = 'nodejs' in s['type']
    spath = Path(s['path'])
    logf = logs_path(s['owner'], s['name'])

    if is_node:
        if not (spath / "package.json").exists():
            (spath / "package.json").write_text(json.dumps({"name": s['name'], "dependencies": {}}, indent=2))
        cmd = ["npm", "install", pkg_name, "--save"]
    else:
        cmd = ["python3", "-m", "pip", "install", pkg_name]
        
    success = _run_command_and_log(cmd, spath, logf)

    if success and not is_node:
        req_file = spath / "requirements.txt"
        # Only append if not already present
        content = req_file.read_text() if req_file.exists() else ""
        if pkg_name not in content.split():
            with req_file.open("a+") as f:
                f.write(f"\n{pkg_name}")
                
    if success: return jsonify({"success": f"Package '{pkg_name}' installed."})
    else: return jsonify({"error": f"Failed to install '{pkg_name}'. See console for details."}), 500


# ===============================================================
# MAIN EXECUTION
# ===============================================================
if __name__ == "__main__":
    print("ðŸ¤– GenBot Hosting starting up...")
    print("ðŸ”— URL: http://127.0.0.1:8000")
    if not DATA['users']:
        print("ðŸ”‘ No users found. Please register the first admin account.")
    print("   Please create a 'static' folder and place an 'icon.png' file in it.")
    print("â„¹ï¸  Web servers get a public URL if 'cloudflared' is installed and in your system's PATH.")
    print("â„¹ï¸  Node.js support requires 'node' and 'npm' to be installed.")
    app.run(host="0.0.0.0", port=8000, debug=False)