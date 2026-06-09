from flask import Blueprint, jsonify, session, render_template, request, Response
from services.auth import teacher_required
from services.auth import hash_password
from database import (
    create_class, get_classes_by_teacher, get_class, delete_class,
    create_student, get_students_by_class, get_students_by_teacher,
    delete_student, get_attendance_by_class, get_attendance_by_teacher,
    get_weekly_stats, get_class_today_stats, load_embeddings_for_teacher
)

teacher = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher.route('/dashboard')
@teacher_required
def dashboard():
    return render_template('teacher_dashboard.html',
                           user_name=session['user_name'])

# ── Classes ────────────────────────────────────────────────────────────────────
@teacher.route('/api/classes', methods=['GET'])
@teacher_required
def get_classes():
    classes = get_classes_by_teacher(session['user_id'])
    result = []
    for cls in classes:
        stats = get_class_today_stats(cls['id'])
        result.append({**cls, **stats})
    return jsonify(result)

@teacher.route('/api/classes', methods=['POST'])
@teacher_required
def add_class():
    d = request.json
    name    = d.get('name', '').strip()
    subject = d.get('subject', '').strip()
    if not name or not subject:
        return jsonify({"error": "Name and subject required."}), 400
    cid = create_class(name, subject, session['user_id'])
    return jsonify({"id": cid, "name": name, "subject": subject,
                    "total": 0, "present": 0, "absent": 0})

@teacher.route('/api/classes/<int:class_id>', methods=['DELETE'])
@teacher_required
def remove_class(class_id):
    delete_class(class_id, session['user_id'])
    return jsonify({"message": "Class deleted."})

# ── Students ───────────────────────────────────────────────────────────────────
@teacher.route('/api/classes/<int:class_id>/students', methods=['GET'])
@teacher_required
def get_students(class_id):
    students = get_students_by_class(class_id)
    # Don't send embedding blob to frontend
    return jsonify([{k: v for k, v in s.items() if k != 'embedding'} for s in students])

@teacher.route('/api/students/<int:student_id>', methods=['DELETE'])
@teacher_required
def remove_student(student_id):
    delete_student(student_id, session['user_id'])
    return jsonify({"message": "Student removed."})

@teacher.route('/api/register-student', methods=['POST'])
@teacher_required
def register_student_api():
    from services.register_face import get_final_embedding, reg_state
    d          = request.json
    name       = d.get('name', '').strip()
    roll_no    = d.get('roll_no', '').strip()
    email      = d.get('email', '').strip().lower()
    password   = d.get('password', '').strip()
    class_id   = d.get('class_id')

    if not all([name, roll_no, email, password, class_id]):
        return jsonify({"error": "All fields required."}), 400

    # Verify class belongs to this teacher
    cls = get_class(class_id)
    if not cls or cls['teacher_id'] != session['user_id']:
        return jsonify({"error": "Class not found."}), 404

    embedding = get_final_embedding()
    if embedding is None:
        return jsonify({"error": "Face not captured yet. Complete face scan first."}), 400

    sid = create_student(name, roll_no, email, hash_password(password),
                         class_id, session['user_id'], embedding)
    if sid is None:
        return jsonify({"error": "Email already registered."}), 409

    return jsonify({"message": f"{name} registered successfully.", "id": sid})

# ── Attendance ─────────────────────────────────────────────────────────────────
@teacher.route('/api/attendance', methods=['GET'])
@teacher_required
def get_attendance():
    class_id = request.args.get('class_id', type=int)
    date     = request.args.get('date')
    if class_id:
        rows = get_attendance_by_class(class_id, date)
    else:
        rows = get_attendance_by_teacher(session['user_id'], date)
    return jsonify(rows)

@teacher.route('/api/stats/weekly', methods=['GET'])
@teacher_required
def weekly_stats():
    return jsonify(get_weekly_stats(session['user_id']))

@teacher.route('/api/stats/class/<int:class_id>', methods=['GET'])
@teacher_required
def class_stats(class_id):
    return jsonify(get_class_today_stats(class_id))

# ── Camera stream (teacher starts for a class) ─────────────────────────────────
@teacher.route('/video-feed/<int:class_id>')
@teacher_required
def video_feed(class_id):
    from services.camera import generate_frames
    known = load_embeddings_for_teacher(session['user_id'])
    # Filter to this class only
    known_class = [(sid, name, roll, cid, emb)
                   for (sid, name, roll, cid, emb) in known if cid == class_id]
    return Response(
        generate_frames(known_class, session['user_id']),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ── Registration camera stream ──────────────────────────────────────────────────
@teacher.route('/video-feed/register')
@teacher_required
def reg_video_feed():
    from services.register_face import generate_registration_stream
    return Response(
        generate_registration_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@teacher.route('/api/capture-frame', methods=['POST'])
@teacher_required
def capture_frame():
    from services.register_face import trigger_capture, reg_state
    ok, msg = trigger_capture()
    with reg_state.lock:
        status = reg_state.status
        n      = len(reg_state.embeddings)
    return jsonify({"success": ok, "message": msg,
                    "status": status, "captured": n})
