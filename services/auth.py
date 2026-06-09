import hashlib
from functools import wraps
from flask import session, redirect, url_for, jsonify, request

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(pw, hashed):
    return hash_password(pw) == hashed

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated

def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden"}), 403
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden"}), 403
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated
