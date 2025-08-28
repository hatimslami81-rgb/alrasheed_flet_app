\
import os
import sqlite3
from contextlib import closing

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "university.db")
DB_PATH = os.path.abspath(DB_PATH)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn, conn:
        c = conn.cursor()
        # Users
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','student')),
            full_name TEXT,
            uni_id TEXT,     -- الرقم الجامعي
            level TEXT,      -- المستوى/السنة
            gpa REAL         -- المعدل
        );
        """)

        # Courses
        c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credits INTEGER DEFAULT 3
        );
        """)

        # Enrollments
        c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            semester TEXT DEFAULT '2025S1',
            UNIQUE(student_id, course_id, semester),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
        """)

        # Lectures
        c.execute("""
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            lecture_date TEXT NOT NULL,   -- YYYY-MM-DD
            start_time TEXT NOT NULL,     -- HH:MM
            end_time TEXT NOT NULL,       -- HH:MM
            qr_token TEXT UNIQUE,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
        """)

        # Attendance
        c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            lecture_id INTEGER NOT NULL,
            scanned_at TEXT NOT NULL,     -- ISO datetime
            UNIQUE(student_id, lecture_id),
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(lecture_id) REFERENCES lectures(id)
        );
        """)

        # Grades
        c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            exam_type TEXT DEFAULT 'Final',
            grade REAL NOT NULL,
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
        """)

        # Finance
        c.execute("""
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT,  -- YYYY-MM-DD
            paid INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES users(id)
        );
        """)

        # Exams
        c.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            exam_date TEXT NOT NULL,     -- YYYY-MM-DD
            start_time TEXT NOT NULL,
            room TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
        """)

        # Timetable
        c.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,   -- e.g., 'Mon'
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
        """)

        # Buses
        c.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route TEXT NOT NULL,
            depart_time TEXT NOT NULL,   -- HH:MM
            origin TEXT NOT NULL,
            destination TEXT NOT NULL
        );
        """)
