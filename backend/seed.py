\
from .db import init_db, get_conn
from .auth import create_user, _hash_password
from .models import add_course, add_exam, add_timetable, add_bus
import secrets

def run():
    init_db()

    # Admin
    try:
        create_user("admin", "admin123", "admin", full_name="System Admin")
    except Exception:
        pass

    # Student
    try:
        create_user("s1001", "pass123", "student", full_name="طالب تجريبي", uni_id="20250001", level="السنة الثالثة", gpa=3.14)
    except Exception:
        pass

    # Courses
    courses = [
        ("CS101", "مقدمة في البرمجة", 3),
        ("CS201", "هياكل البيانات", 3),
        ("MATH150", "التفاضل والتكامل", 4),
    ]
    for code, name, cr in courses:
        try:
            add_course(code, name, cr)
        except Exception:
            pass

    # Exam & Timetable examples (use first courses)
    with get_conn() as conn:
        course_rows = list(conn.execute("SELECT * FROM courses ORDER BY id"))
        if course_rows:
            for r in course_rows:
                try:
                    add_exam(r["id"], "2025-09-20", "10:00", "قاعة A")
                except Exception:
                    pass
                try:
                    add_timetable(r["id"], "Mon", "09:00", "10:30", "LAB-1")
                    add_timetable(r["id"], "Wed", "12:00", "13:30", "HALL-3")
                except Exception:
                    pass

    # Buses
    try:
        add_bus("Route A", "07:30", "باب المعظم", "جامعة الرشيد")
        add_bus("Route B", "08:00", "الكرادة", "جامعة الرشيد")
        add_bus("Route C", "15:00", "جامعة الرشيد", "باب المعظم")
    except Exception:
        pass

    print("Seed completed. Default admin/student created, courses/exams/timetable/buses added.")

if __name__ == "__main__":
    run()
