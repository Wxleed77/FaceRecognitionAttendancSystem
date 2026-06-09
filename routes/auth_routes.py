from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from database import (create_user, get_user_by_email, get_student_by_email,
                      get_all_classes, get_class)
from services.auth import hash_password, check_password

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('teacher.dashboard') if session.get('role') == 'teacher'
                        else url_for('student.student_dashboard'))
    return render_template('login.html')

@auth.route('/register')
def register_page():
    return render_template('register.html')

@auth.route('/register-student')
def register_student_page():
    return render_template('register_student.html')

@auth.route('/api/classes/public')
def public_classes():
    """Available for student registration — no auth needed."""
    return jsonify(get_all_classes())

@auth.route('/api/auth/register-teacher', methods=['POST'])
def register_teacher():
    d = request.json
    name  = d.get('name', '').strip()
    email = d.get('email', '').strip().lower()
    pw    = d.get('password', '')
    if not all([name, email, pw]):
        return jsonify({"error": "All fields required."}), 400
    if len(pw) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    uid = create_user(name, email, hash_password(pw), role='teacher')
    if not uid:
        return jsonify({"error": "Email already registered."}), 409
    return jsonify({"message": "Account created. Please log in."})

@auth.route('/api/auth/register-student', methods=['POST'])
def register_student_api():
    """Student self-registration with face capture."""
    from services.register_face import get_final_embedding, reg_state
    d        = request.json
    name     = d.get('name', '').strip()
    roll_no  = d.get('roll_no', '').strip()
    email    = d.get('email', '').strip().lower()
    password = d.get('password', '').strip()
    class_id = d.get('class_id')

    if not all([name, roll_no, email, password, class_id]):
        return jsonify({"error": "All fields required."}), 400

    cls = get_class(int(class_id))
    if not cls:
        return jsonify({"error": "Class not found."}), 404

    embedding = get_final_embedding()
    if embedding is None:
        return jsonify({"error": "Face capture incomplete. Capture 3 photos first."}), 400

    from database import create_student
    sid = create_student(name, roll_no, email, hash_password(password),
                         cls['id'], cls['teacher_id'], embedding)
    if sid is None:
        return jsonify({"error": "Email already registered."}), 409

    return jsonify({"message": "Registered! You can now log in.", "redirect": "/login"})

@auth.route('/api/auth/login', methods=['POST'])
def login():
    d     = request.json
    email = d.get('email', '').strip().lower()
    pw    = d.get('password', '')
    role  = d.get('role', 'teacher')

    if role == 'teacher':
        user = get_user_by_email(email)
        if not user or not check_password(pw, user['password']):
            return jsonify({"error": "Invalid email or password."}), 401
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        session['role']      = 'teacher'
        return jsonify({"redirect": "/teacher/dashboard"})

    elif role == 'student':
        student = get_student_by_email(email)
        if not student or not check_password(pw, student['password']):
            return jsonify({"error": "Invalid email or password."}), 401
        session['user_id']   = student['id']
        session['user_name'] = student['name']
        session['role']      = 'student'
        session['class_id']  = student['class_id']
        session['teacher_id']= student['teacher_id']
        return jsonify({"redirect": "/student/dashboard"})

    return jsonify({"error": "Invalid role."}), 400

@auth.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"redirect": "/login"})

@auth.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return redirect(url_for('teacher.dashboard') if session.get('role') == 'teacher'
                    else url_for('student.student_dashboard'))

# ── Registration camera endpoints (no teacher session needed) ──────────────────
@auth.route('/register-student/video-feed')
def reg_student_video():
    from services.register_face import generate_registration_stream
    from flask import Response
    return Response(generate_registration_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@auth.route('/api/register-student/capture', methods=['POST'])
def reg_student_capture():
    from services.register_face import trigger_capture, reg_state
    ok, msg = trigger_capture()
    return jsonify({"success": ok, "message": msg,
                    "status": reg_state.status,
                    "captured": len(reg_state.embeddings)})
