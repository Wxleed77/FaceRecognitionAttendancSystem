from flask import Blueprint, jsonify, session, render_template, Response
from services.auth import student_required
from database import (get_student_by_id, get_attendance_by_student,
                      blob_to_emb, mark_attendance)

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@student_required
def student_dashboard():
    return render_template('student_dashboard.html',
                           user_name=session['user_name'])

@student_bp.route('/api/my-attendance')
@student_required
def my_attendance():
    rows = get_attendance_by_student(session['user_id'])
    return jsonify(rows)

@student_bp.route('/api/my-info')
@student_required
def my_info():
    s = get_student_by_id(session['user_id'])
    if not s: return jsonify({}), 404
    return jsonify({k: v for k, v in s.items() if k != 'embedding'})

# Student self-scan stream
@student_bp.route('/video-feed/scan')
@student_required
def scan_feed():
    from services.camera import generate_student_scan
    student = get_student_by_id(session['user_id'])
    if not student or not student.get('embedding'):
        return "No embedding found", 400
    emb = blob_to_emb(student['embedding'])

    def on_match():
        mark_attendance(
            student['id'], student['name'], student['roll_no'],
            student['class_id'], student['teacher_id']
        )

    return Response(
        generate_student_scan(emb, on_match),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
