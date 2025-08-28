from datetime import datetime
from typing import Optional, List
import os, shutil, time

from .db import get_conn

# -------- Users --------
def list_students():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC")]

def get_student_by_id(student_id: int):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE id=? AND role='student'", (student_id,))
        r = cur.fetchone()
        return dict(r) if r else None

def add_student(username, password_hash, salt, full_name, uni_id, level, gpa):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO users (username, password_hash, salt, role, full_name, uni_id, level, gpa)
        VALUES (?, ?, ?, 'student', ?, ?, ?, ?)
        """, (username, password_hash, salt, full_name, uni_id, level, gpa))
        conn.commit()
        return c.lastrowid

def update_student(student_id, **kwargs):
    if not kwargs:
        return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(student_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_student(student_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=? AND role='student'", (student_id,))
        conn.commit()

# الساعات المنجزة = مجموع ساعات المقررات التي أفضل علامة فيها >= 50
def compute_completed_credits(student_id: int) -> float:
    with get_conn() as conn:
        q = """
        SELECT c.credits AS cr, MAX(g.grade) AS best
        FROM grades g
        JOIN courses c ON c.id = g.course_id
        WHERE g.student_id=?
        GROUP BY g.course_id
        """
        total = 0.0
        for r in conn.execute(q, (student_id,)):
            if (r["best"] or 0) >= 50:
                total += float(r["cr"] or 0)
        return total

# -------- Courses --------
def list_courses():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM courses ORDER BY code")]

def add_course(code: str, name: str, credits: int = 3):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO courses (code, name, credits) VALUES (?,?,?)", (code, name, credits))
        conn.commit()
        return c.lastrowid

def update_course(course_id: int, **kwargs):
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(course_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE courses SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_course(course_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
        conn.commit()

# -------- Enrollments --------
def list_enrollments(student_id: int):
    with get_conn() as conn:
        q = """
        SELECT e.id, c.id as course_id, c.code, c.name, e.semester
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.student_id=?
        """
        return [dict(r) for r in conn.execute(q, (student_id,))]

def enroll_course(student_id: int, course_id: int, semester: str = "2025S1"):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT OR IGNORE INTO enrollments (student_id, course_id, semester) VALUES (?,?,?)
        """, (student_id, course_id, semester))
        conn.commit()
        return c.lastrowid

def delete_enrollment(student_id: int, course_id: int, semester: str = "2025S1"):
    with get_conn() as conn:
        conn.execute("DELETE FROM enrollments WHERE student_id=? AND course_id=? AND semester=?",
                     (student_id, course_id, semester))
        conn.commit()

# -------- Lectures & Attendance --------
def create_lecture(course_id: int, lecture_date: str, start_time: str, end_time: str, qr_token: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO lectures (course_id, lecture_date, start_time, end_time, qr_token)
        VALUES (?,?,?,?,?)
        """, (course_id, lecture_date, start_time, end_time, qr_token))
        conn.commit()
        return c.lastrowid

def list_lectures(course_id: Optional[int] = None):
    with get_conn() as conn:
        if course_id:
            cur = conn.execute("SELECT * FROM lectures WHERE course_id=? ORDER BY lecture_date DESC", (course_id,))
        else:
            cur = conn.execute("SELECT * FROM lectures ORDER BY lecture_date DESC")
        return [dict(r) for r in cur.fetchall()]

def get_lecture_by_token(token: str):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM lectures WHERE qr_token=?", (token,))
        r = cur.fetchone()
        return dict(r) if r else None

def update_lecture(lecture_id: int, **kwargs):
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(lecture_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE lectures SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_lecture(lecture_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM lectures WHERE id=?", (lecture_id,))
        conn.commit()

def record_attendance(student_id: int, lecture_id: int) -> bool:
    with get_conn() as conn:
        try:
            conn.execute("""
            INSERT INTO attendance (student_id, lecture_id, scanned_at) VALUES (?,?,?)
            """, (student_id, lecture_id, datetime.now().isoformat(timespec='seconds')))
            conn.commit()
            return True
        except Exception:
            return False

# -------- Grades --------
def list_grades(student_id: int):
    with get_conn() as conn:
        q = """
        SELECT g.id, c.code, c.name, g.exam_type, g.grade
        FROM grades g
        JOIN courses c ON c.id = g.course_id
        WHERE g.student_id=?
        ORDER BY c.code
        """
        return [dict(r) for r in conn.execute(q, (student_id,))]

def list_grades_all():
    with get_conn() as conn:
        q = """
        SELECT g.id, g.student_id, u.full_name, c.code, c.name, g.exam_type, g.grade
        FROM grades g
        JOIN users u ON u.id = g.student_id
        JOIN courses c ON c.id = g.course_id
        ORDER BY g.id DESC
        """
        return [dict(r) for r in conn.execute(q)]

def add_grade(student_id: int, course_id: int, exam_type: str, grade: float):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO grades (student_id, course_id, exam_type, grade) VALUES (?,?,?,?)
        """, (student_id, course_id, exam_type, grade))
        conn.commit()

def update_grade(grade_id: int, **kwargs):
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(grade_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE grades SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_grade(grade_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM grades WHERE id=?", (grade_id,))
        conn.commit()

# -------- Finance --------
def list_finance(student_id: int):
    with get_conn() as conn:
        q = "SELECT * FROM finance WHERE student_id=? ORDER BY COALESCE(due_date, '9999-12-31')"
        return [dict(r) for r in conn.execute(q, (student_id,))]

def list_finance_all():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM finance ORDER BY id DESC")]

def add_finance(student_id: int, description: str, amount: float, due_date: str = None, paid: int = 0):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO finance (student_id, description, amount, due_date, paid) VALUES (?,?,?,?,?)
        """, (student_id, description, amount, due_date, paid))
        conn.commit()

def update_finance(finance_id: int, **kwargs):
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(finance_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE finance SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_finance(finance_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM finance WHERE id=?", (finance_id,))
        conn.commit()

# -------- Timetable & Exams --------
def list_exams_for_student(student_id: int):
    with get_conn() as conn:
        q = """
        SELECT e.exam_date, e.start_time, e.room, c.code, c.name
        FROM exams e
        JOIN enrollments en ON en.course_id = e.course_id AND en.student_id=?
        JOIN courses c ON c.id = e.course_id
        ORDER BY e.exam_date, e.start_time
        """
        return [dict(r) for r in conn.execute(q, (student_id,))]

def add_exam(course_id: int, exam_date: str, start_time: str, room: str):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO exams (course_id, exam_date, start_time, room) VALUES (?,?,?,?)
        """, (course_id, exam_date, start_time, room))
        conn.commit()

def list_timetable_for_student(student_id: int):
    with get_conn() as conn:
        q = """
        SELECT t.day_of_week, t.start_time, t.end_time, t.room, c.code, c.name
        FROM timetable t
        JOIN enrollments en ON en.course_id = t.course_id AND en.student_id=?
        JOIN courses c ON c.id = t.course_id
        ORDER BY CASE t.day_of_week
            WHEN 'Sun' THEN 0 WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
            WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6 ELSE 7 END, t.start_time
        """
        return [dict(r) for r in conn.execute(q, (student_id,))]

def add_timetable(course_id: int, day_of_week: str, start_time: str, end_time: str, room: str):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO timetable (course_id, day_of_week, start_time, end_time, room) VALUES (?,?,?,?,?)
        """, (course_id, day_of_week, start_time, end_time, room))
        conn.commit()

# -------- Buses --------
def list_buses():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM buses ORDER BY depart_time")]

def add_bus(route: str, depart_time: str, origin: str, destination: str):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO buses (route, depart_time, origin, destination) VALUES (?,?,?,?)
        """, (route, depart_time, origin, destination))
        conn.commit()

def update_bus(bus_id: int, **kwargs):
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(bus_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE buses SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_bus(bus_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM buses WHERE id=?", (bus_id,))
        conn.commit()

# -------- College materials (DB + fallback) --------
def ensure_materials_table():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            college TEXT NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

def _safe_name(s: str) -> str:
    s = "".join(ch for ch in s if ch.isalnum() or ch in " _-").strip()
    return s.replace(" ", "_") or f"file_{int(time.time())}"

def add_material(college: str, title: str, src_path: str, dst_root: str = "assets/materials"):
    ensure_materials_table()
    os.makedirs(os.path.join(dst_root, college), exist_ok=True)
    base, ext = os.path.splitext(src_path)
    ext = ext or ".bin"
    filename = f"{_safe_name(title)}_{int(time.time())}{ext}"
    dst_path = os.path.join(dst_root, college, filename)
    shutil.copy(src_path, dst_path)
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO materials (college, title, file_path) VALUES (?,?,?)",
                  (college, title, dst_path))
        conn.commit()
        return c.lastrowid, dst_path

def list_materials(college: Optional[str] = None):
    ensure_materials_table()
    with get_conn() as conn:
        if college:
            cur = conn.execute(
                "SELECT * FROM materials WHERE college=? ORDER BY uploaded_at DESC, id DESC",
                (college,)
            )
        else:
            cur = conn.execute("SELECT * FROM materials ORDER BY uploaded_at DESC, id DESC")
        return [dict(r) for r in cur.fetchall()]

def update_material(material_id: int, **kwargs):
    ensure_materials_table()
    if not kwargs: return
    keys, vals = [], []
    for k, v in kwargs.items():
        keys.append(f"{k}=?"); vals.append(v)
    vals.append(material_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE materials SET {', '.join(keys)} WHERE id=?", vals)
        conn.commit()

def delete_material(material_id: int, delete_file: bool = True):
    ensure_materials_table()
    fp = None
    with get_conn() as conn:
        cur = conn.execute("SELECT file_path FROM materials WHERE id=?", (material_id,))
        row = cur.fetchone()
        if row:
            fp = row["file_path"]
        conn.execute("DELETE FROM materials WHERE id=?", (material_id,))
        conn.commit()
    if delete_file and fp and os.path.exists(fp):
        try:
            os.remove(fp)
        except Exception:
            pass

def list_college_materials_fs(college: str):
    """
    متوافق مع واجهة الطالب: يرجّع ملفات من الجدول،
    وإذا الجدول فاضي يرجع ملفات من مجلد assets/materials/<college>/
    """
    rows = list_materials(college)
    if rows:
        return rows
    base = os.path.join("assets", "materials", college)
    if not os.path.isdir(base):
        return []
    out = []
    for name in os.listdir(base):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            out.append({"id": None, "college": college, "title": os.path.splitext(name)[0], "file_path": p})
    return out