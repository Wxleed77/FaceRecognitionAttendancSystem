from database import connect_db
from datetime import datetime

def mark_attendance(name, roll_no):
    conn = connect_db()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    now   = datetime.now().strftime("%H:%M:%S")
    c.execute("SELECT id FROM attendance WHERE roll_no=? AND date=?", (roll_no, today))
    if c.fetchone():
        print(f"⚠️  Already marked: {name}")
    else:
        c.execute(
            "INSERT INTO attendance (student_name,roll_no,date,time,status) VALUES (?,?,?,?,?)",
            (name, roll_no, today, now, "Present"))
        conn.commit()
        print(f"✅ Marked present: {name} at {now}")
    conn.close()

def get_today_attendance():
    conn = connect_db()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM attendance WHERE date=?", (today,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_attendance():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM attendance ORDER BY date DESC, time DESC")
    rows = c.fetchall()
    conn.close()
    return rows
