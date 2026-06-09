import sqlite3, os, numpy as np
from config import DATABASE_PATH

os.makedirs("database", exist_ok=True)

def connect():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    try:
        conn = connect(); c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            email    TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'teacher'
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS classes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            subject    TEXT NOT NULL,
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            roll_no    TEXT NOT NULL,
            email      TEXT UNIQUE,
            password   TEXT,
            class_id   INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            embedding  BLOB NOT NULL,
            FOREIGN KEY(class_id)   REFERENCES classes(id),
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id   INTEGER NOT NULL,
            student_name TEXT,
            roll_no      TEXT,
            class_id     INTEGER NOT NULL,
            teacher_id   INTEGER NOT NULL,
            date         TEXT NOT NULL,
            time         TEXT NOT NULL,
            status       TEXT DEFAULT 'Present',
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(class_id)   REFERENCES classes(id)
        )""")

        conn.commit()

        # ── Migration: add missing columns to old DB files safely ──────────────────
        _add_column_if_missing(conn, "students",   "class_id",   "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "students",   "teacher_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "attendance", "class_id",   "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "attendance", "teacher_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "attendance", "student_id", "INTEGER NOT NULL DEFAULT 0")

        conn.commit(); conn.close()
        print("✅ Database ready.")
    except sqlite3.Error as e:
        print(f"❌ Database init error: {e}")
        if conn:
            conn.close()
        raise

def _add_column_if_missing(conn, table, column, col_def):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    cols = [row["name"] for row in c.fetchall()]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        print(f"  ↳ Migrated: added {table}.{column}")

# ── Embedding ──────────────────────────────────────────────────────────────────
def emb_to_blob(e): return np.array(e, dtype=np.float64).tobytes()
def blob_to_emb(b): return np.frombuffer(b, dtype=np.float64)

# ── Users ──────────────────────────────────────────────────────────────────────
def create_user(name, email, password_hash, role="teacher"):
    conn = connect(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                  (name, email, password_hash, role))
        conn.commit(); return c.lastrowid
    except sqlite3.IntegrityError: return None
    finally: conn.close()

def get_user_by_email(email):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def get_user_by_id(uid):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

# ── Classes ────────────────────────────────────────────────────────────────────
def create_class(name, subject, teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("INSERT INTO classes (name,subject,teacher_id) VALUES (?,?,?)",
              (name, subject, teacher_id))
    conn.commit(); cid = c.lastrowid; conn.close(); return cid

def get_classes_by_teacher(teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM classes WHERE teacher_id=?", (teacher_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_all_classes():
    """All classes — for student registration dropdown."""
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT c.id, c.name, c.subject, u.name as teacher_name
                 FROM classes c JOIN users u ON c.teacher_id = u.id
                 ORDER BY u.name, c.name""")
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_class(class_id):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM classes WHERE id=?", (class_id,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def delete_class(class_id, teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("DELETE FROM classes WHERE id=? AND teacher_id=?", (class_id, teacher_id))
    conn.commit(); conn.close()

# ── Students ───────────────────────────────────────────────────────────────────
def create_student(name, roll_no, email, password_hash, class_id, teacher_id, embedding):
    conn = connect(); c = conn.cursor()
    try:
        c.execute("""INSERT INTO students
                     (name,roll_no,email,password,class_id,teacher_id,embedding)
                     VALUES (?,?,?,?,?,?,?)""",
                  (name, roll_no, email, password_hash,
                   class_id, teacher_id, emb_to_blob(embedding)))
        conn.commit(); return c.lastrowid
    except sqlite3.IntegrityError: return None
    finally: conn.close()

def get_students_by_class(class_id):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM students WHERE class_id=?", (class_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_students_by_teacher(teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT s.*, c.name as class_name FROM students s
                 JOIN classes c ON s.class_id=c.id
                 WHERE s.teacher_id=?""", (teacher_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_student_by_email(email):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM students WHERE email=?", (email,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def get_student_by_id(sid):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (sid,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def delete_student(student_id, teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=? AND teacher_id=?", (student_id, teacher_id))
    conn.commit(); conn.close()

def load_embeddings_for_teacher(teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT id,name,roll_no,class_id,embedding FROM students WHERE teacher_id=?",
              (teacher_id,))
    rows = c.fetchall(); conn.close()
    return [(r['id'], r['name'], r['roll_no'], r['class_id'], blob_to_emb(r['embedding']))
            for r in rows]

# ── Attendance ─────────────────────────────────────────────────────────────────
def mark_attendance(student_id, student_name, roll_no, class_id, teacher_id):
    from datetime import datetime
    conn = connect(); c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")
    c.execute("SELECT id FROM attendance WHERE student_id=? AND date=?", (student_id, today))
    if c.fetchone(): conn.close(); return False
    c.execute("""INSERT INTO attendance
                 (student_id,student_name,roll_no,class_id,teacher_id,date,time,status)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (student_id, student_name, roll_no, class_id, teacher_id, today, now, "Present"))
    conn.commit(); conn.close(); return True

def get_attendance_by_class(class_id, date=None):
    conn = connect(); c = conn.cursor()
    if date:
        c.execute("SELECT * FROM attendance WHERE class_id=? AND date=? ORDER BY time DESC",
                  (class_id, date))
    else:
        c.execute("SELECT * FROM attendance WHERE class_id=? ORDER BY date DESC, time DESC",
                  (class_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_attendance_by_teacher(teacher_id, date=None):
    conn = connect(); c = conn.cursor()
    if date:
        c.execute("SELECT * FROM attendance WHERE teacher_id=? AND date=? ORDER BY time DESC",
                  (teacher_id, date))
    else:
        c.execute("SELECT * FROM attendance WHERE teacher_id=? ORDER BY date DESC, time DESC",
                  (teacher_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_attendance_by_student(student_id):
    conn = connect(); c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE student_id=? ORDER BY date DESC", (student_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_weekly_stats(teacher_id):
    conn = connect(); c = conn.cursor()
    c.execute("""SELECT date, COUNT(*) as cnt FROM attendance
                 WHERE teacher_id=?
                 GROUP BY date ORDER BY date DESC LIMIT 7""", (teacher_id,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def get_class_today_stats(class_id):
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    conn = connect(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM students WHERE class_id=?", (class_id,))
    total = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) as present FROM attendance WHERE class_id=? AND date=?",
              (class_id, today))
    present = c.fetchone()["present"]
    conn.close()
    return {"total": total, "present": present, "absent": total - present}
