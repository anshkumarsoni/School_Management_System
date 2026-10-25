# ================================================================================
#       STUDENT PERFORMANCE ANALYTICS & INTERVENTION MANAGEMENT SYSTEM
#       (Multi-Term Trends, Subject Diagnostics, Class Benchmarks & Support)
# ================================================================================

import datetime
from decimal import Decimal
import matplotlib.pyplot as plt
import mysql.connector as ms
from tabulate import tabulate

from utils import (
    clear_screen,
    get_connection,
    pause_and_clear,
    center_text
)

# --------------------------------- DATABASE INITIALIZATION ------------------------

def init_analytics_tables():
    """Initializes tables for Marks Details and Academic Interventions with starter data."""
    con = get_connection()
    if not con:
        return False
    cur = con.cursor(dictionary=True)
    try:
        # 1. Marks Details Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Marks_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                EXAM_TYPE VARCHAR(50) NOT NULL,
                SUBJECT VARCHAR(100) NOT NULL,
                MARKS_OBTAINED DECIMAL(5, 2) NOT NULL,
                MAX_MARKS DECIMAL(5, 2) NOT NULL DEFAULT 100.00,
                UNIQUE KEY unique_student_exam_sub (ROLL_NUMBER, EXAM_TYPE, SUBJECT)
            )
        """)

        # 2. Academic Interventions & At-Risk Support Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Academic_Interventions (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                INTERVENTION_CODE VARCHAR(20) UNIQUE NOT NULL,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                CLASS VARCHAR(20) NOT NULL,
                RISK_LEVEL ENUM('Critical', 'Moderate', 'Watchlist') NOT NULL DEFAULT 'Moderate',
                STRUGGLING_SUBJECTS VARCHAR(255) NOT NULL,
                CURRENT_AVERAGE DECIMAL(5, 2) NOT NULL,
                ASSIGNED_MENTOR VARCHAR(100) NOT NULL,
                REMEDIAL_STRATEGY VARCHAR(255) NOT NULL,
                ACTION_PLAN TEXT,
                PARENT_NOTIFIED ENUM('Yes', 'No') DEFAULT 'Yes',
                STATUS ENUM('Open', 'In Progress', 'Under Review', 'Resolved') DEFAULT 'Open',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (ROLL_NUMBER) REFERENCES Students_Details(ROLL_NUMBER) ON DELETE CASCADE
            )
        """)
        con.commit()

        # 3. Check if marks dataset needs population
        cur.execute("SELECT COUNT(*) AS cnt FROM Marks_Details")
        if cur.fetchone()["cnt"] < 50:
            _seed_comprehensive_marks(cur, con)

        # 4. Check if starter interventions need population
        cur.execute("SELECT COUNT(*) AS cnt FROM Academic_Interventions")
        if cur.fetchone()["cnt"] == 0:
            _seed_starter_interventions(cur, con)

        return True
    except ms.Error as e:
        print("Analytics DB Initialization Error:", e)
        return False
    finally:
        cur.close()
        con.close()


def _seed_comprehensive_marks(cur, con):
    """Internal helper to seed realistic 4-term marks across 10 students and 6 subjects."""
    marks_seed = [
        # Roll 101 - Aarav Sharma (Grade 10)
        ('101', 'Term 1 Exam', 'Mathematics', 90.0, 100.0),
        ('101', 'Term 1 Exam', 'Physics', 85.0, 100.0),
        ('101', 'Term 1 Exam', 'Chemistry', 88.0, 100.0),
        ('101', 'Term 1 Exam', 'English Literature', 82.0, 100.0),
        ('101', 'Term 1 Exam', 'Computer Science', 95.0, 100.0),

        ('101', 'Mid-Term Examination', 'Mathematics', 92.5, 100.0),
        ('101', 'Mid-Term Examination', 'Physics', 88.0, 100.0),
        ('101', 'Mid-Term Examination', 'Chemistry', 89.0, 100.0),
        ('101', 'Mid-Term Examination', 'English Literature', 84.0, 100.0),
        ('101', 'Mid-Term Examination', 'Computer Science', 97.5, 100.0),

        ('101', 'Term 2 Exam', 'Mathematics', 94.0, 100.0),
        ('101', 'Term 2 Exam', 'Physics', 90.0, 100.0),
        ('101', 'Term 2 Exam', 'Chemistry', 91.0, 100.0),
        ('101', 'Term 2 Exam', 'English Literature', 86.0, 100.0),
        ('101', 'Term 2 Exam', 'Computer Science', 98.0, 100.0),

        ('101', 'Final Examination', 'Mathematics', 96.0, 100.0),
        ('101', 'Final Examination', 'Physics', 92.0, 100.0),
        ('101', 'Final Examination', 'Chemistry', 93.0, 100.0),
        ('101', 'Final Examination', 'English Literature', 88.0, 100.0),
        ('101', 'Final Examination', 'Computer Science', 99.0, 100.0),

        # Roll 102 - Ananya Patel (Grade 10)
        ('102', 'Term 1 Exam', 'Mathematics', 92.0, 100.0),
        ('102', 'Term 1 Exam', 'Physics', 84.0, 100.0),
        ('102', 'Term 1 Exam', 'Chemistry', 87.0, 100.0),
        ('102', 'Term 1 Exam', 'English Literature', 91.0, 100.0),
        ('102', 'Term 1 Exam', 'Computer Science', 90.0, 100.0),

        ('102', 'Mid-Term Examination', 'Mathematics', 95.0, 100.0),
        ('102', 'Mid-Term Examination', 'Physics', 86.5, 100.0),
        ('102', 'Mid-Term Examination', 'Chemistry', 89.5, 100.0),
        ('102', 'Mid-Term Examination', 'English Literature', 93.0, 100.0),
        ('102', 'Mid-Term Examination', 'Computer Science', 92.0, 100.0),

        ('102', 'Term 2 Exam', 'Mathematics', 94.0, 100.0),
        ('102', 'Term 2 Exam', 'Physics', 88.0, 100.0),
        ('102', 'Term 2 Exam', 'Chemistry', 92.0, 100.0),
        ('102', 'Term 2 Exam', 'English Literature', 95.0, 100.0),
        ('102', 'Term 2 Exam', 'Computer Science', 94.0, 100.0),

        ('102', 'Final Examination', 'Mathematics', 96.5, 100.0),
        ('102', 'Final Examination', 'Physics', 89.0, 100.0),
        ('102', 'Final Examination', 'Chemistry', 94.0, 100.0),
        ('102', 'Final Examination', 'English Literature', 96.0, 100.0),
        ('102', 'Final Examination', 'Computer Science', 95.0, 100.0),

        # Roll 103 - Rohan Mehta (Grade 9) - Struggling / Dropping
        ('103', 'Term 1 Exam', 'Mathematics', 68.0, 100.0),
        ('103', 'Term 1 Exam', 'Physics', 58.0, 100.0),
        ('103', 'Term 1 Exam', 'Chemistry', 52.0, 100.0),
        ('103', 'Term 1 Exam', 'English Literature', 75.0, 100.0),
        ('103', 'Term 1 Exam', 'Computer Science', 80.0, 100.0),

        ('103', 'Mid-Term Examination', 'Mathematics', 64.0, 100.0),
        ('103', 'Mid-Term Examination', 'Physics', 50.0, 100.0),
        ('103', 'Mid-Term Examination', 'Chemistry', 44.0, 100.0),
        ('103', 'Mid-Term Examination', 'English Literature', 78.0, 100.0),
        ('103', 'Mid-Term Examination', 'Computer Science', 82.0, 100.0),

        ('103', 'Term 2 Exam', 'Mathematics', 60.0, 100.0),
        ('103', 'Term 2 Exam', 'Physics', 46.0, 100.0),
        ('103', 'Term 2 Exam', 'Chemistry', 38.0, 100.0),
        ('103', 'Term 2 Exam', 'English Literature', 72.0, 100.0),
        ('103', 'Term 2 Exam', 'Computer Science', 79.0, 100.0),

        ('103', 'Final Examination', 'Mathematics', 65.0, 100.0),
        ('103', 'Final Examination', 'Physics', 48.0, 100.0),
        ('103', 'Final Examination', 'Chemistry', 42.0, 100.0),
        ('103', 'Final Examination', 'English Literature', 76.0, 100.0),
        ('103', 'Final Examination', 'Computer Science', 84.0, 100.0),

        # Roll 104 - Pooja Iyer (Grade 11)
        ('104', 'Term 1 Exam', 'Mathematics', 70.0, 100.0),
        ('104', 'Term 1 Exam', 'Physics', 62.0, 100.0),
        ('104', 'Term 1 Exam', 'Chemistry', 68.0, 100.0),
        ('104', 'Term 1 Exam', 'English Literature', 86.0, 100.0),
        ('104', 'Term 1 Exam', 'Biology', 88.0, 100.0),

        ('104', 'Mid-Term Examination', 'Mathematics', 72.0, 100.0),
        ('104', 'Mid-Term Examination', 'Physics', 64.0, 100.0),
        ('104', 'Mid-Term Examination', 'Chemistry', 70.0, 100.0),
        ('104', 'Mid-Term Examination', 'English Literature', 88.0, 100.0),
        ('104', 'Mid-Term Examination', 'Biology', 84.5, 100.0),

        ('104', 'Term 2 Exam', 'Mathematics', 75.0, 100.0),
        ('104', 'Term 2 Exam', 'Physics', 66.0, 100.0),
        ('104', 'Term 2 Exam', 'Chemistry', 72.0, 100.0),
        ('104', 'Term 2 Exam', 'English Literature', 90.0, 100.0),
        ('104', 'Term 2 Exam', 'Biology', 92.0, 100.0),

        ('104', 'Final Examination', 'Mathematics', 78.0, 100.0),
        ('104', 'Final Examination', 'Physics', 68.0, 100.0),
        ('104', 'Final Examination', 'Chemistry', 75.0, 100.0),
        ('104', 'Final Examination', 'English Literature', 92.0, 100.0),
        ('104', 'Final Examination', 'Biology', 94.0, 100.0),

        # Roll 105 - Vikram Singh (Grade 12)
        ('105', 'Term 1 Exam', 'Mathematics', 88.0, 100.0),
        ('105', 'Term 1 Exam', 'Physics', 86.0, 100.0),
        ('105', 'Term 1 Exam', 'Chemistry', 84.0, 100.0),
        ('105', 'Term 1 Exam', 'English Literature', 80.0, 100.0),
        ('105', 'Term 1 Exam', 'Computer Science', 94.0, 100.0),

        ('105', 'Mid-Term Examination', 'Mathematics', 90.0, 100.0),
        ('105', 'Mid-Term Examination', 'Physics', 89.0, 100.0),
        ('105', 'Mid-Term Examination', 'Chemistry', 86.0, 100.0),
        ('105', 'Mid-Term Examination', 'English Literature', 82.0, 100.0),
        ('105', 'Mid-Term Examination', 'Computer Science', 96.0, 100.0),

        ('105', 'Term 2 Exam', 'Mathematics', 92.0, 100.0),
        ('105', 'Term 2 Exam', 'Physics', 91.0, 100.0),
        ('105', 'Term 2 Exam', 'Chemistry', 88.0, 100.0),
        ('105', 'Term 2 Exam', 'English Literature', 85.0, 100.0),
        ('105', 'Term 2 Exam', 'Computer Science', 97.0, 100.0),

        ('105', 'Final Examination', 'Mathematics', 95.0, 100.0),
        ('105', 'Final Examination', 'Physics', 93.0, 100.0),
        ('105', 'Final Examination', 'Chemistry', 90.0, 100.0),
        ('105', 'Final Examination', 'English Literature', 88.0, 100.0),
        ('105', 'Final Examination', 'Computer Science', 98.0, 100.0),

        # Roll 106 - Sneha Kulkarni (Grade 9)
        ('106', 'Term 1 Exam', 'Mathematics', 80.0, 100.0),
        ('106', 'Term 1 Exam', 'Physics', 72.0, 100.0),
        ('106', 'Term 1 Exam', 'Chemistry', 76.0, 100.0),
        ('106', 'Term 1 Exam', 'English Literature', 84.0, 100.0),
        ('106', 'Term 1 Exam', 'Computer Science', 88.0, 100.0),

        ('106', 'Mid-Term Examination', 'Mathematics', 82.0, 100.0),
        ('106', 'Mid-Term Examination', 'Physics', 74.0, 100.0),
        ('106', 'Mid-Term Examination', 'Chemistry', 78.0, 100.0),
        ('106', 'Mid-Term Examination', 'English Literature', 86.0, 100.0),
        ('106', 'Mid-Term Examination', 'Computer Science', 90.0, 100.0),

        ('106', 'Term 2 Exam', 'Mathematics', 85.0, 100.0),
        ('106', 'Term 2 Exam', 'Physics', 76.0, 100.0),
        ('106', 'Term 2 Exam', 'Chemistry', 80.0, 100.0),
        ('106', 'Term 2 Exam', 'English Literature', 88.0, 100.0),
        ('106', 'Term 2 Exam', 'Computer Science', 92.0, 100.0),

        ('106', 'Final Examination', 'Mathematics', 88.0, 100.0),
        ('106', 'Final Examination', 'Physics', 79.0, 100.0),
        ('106', 'Final Examination', 'Chemistry', 82.0, 100.0),
        ('106', 'Final Examination', 'English Literature', 90.0, 100.0),
        ('106', 'Final Examination', 'Computer Science', 94.0, 100.0),

        # Roll 107 - Aditya Verma (Grade 8) - Struggling Math & Science
        ('107', 'Term 1 Exam', 'Mathematics', 35.0, 100.0),
        ('107', 'Term 1 Exam', 'Physics', 42.0, 100.0),
        ('107', 'Term 1 Exam', 'Chemistry', 45.0, 100.0),
        ('107', 'Term 1 Exam', 'English Literature', 62.0, 100.0),
        ('107', 'Term 1 Exam', 'Biology', 58.0, 100.0),

        ('107', 'Mid-Term Examination', 'Mathematics', 38.0, 100.0),
        ('107', 'Mid-Term Examination', 'Physics', 40.0, 100.0),
        ('107', 'Mid-Term Examination', 'Chemistry', 46.0, 100.0),
        ('107', 'Mid-Term Examination', 'English Literature', 65.0, 100.0),
        ('107', 'Mid-Term Examination', 'Biology', 60.0, 100.0),

        ('107', 'Term 2 Exam', 'Mathematics', 42.0, 100.0),
        ('107', 'Term 2 Exam', 'Physics', 45.0, 100.0),
        ('107', 'Term 2 Exam', 'Chemistry', 48.0, 100.0),
        ('107', 'Term 2 Exam', 'English Literature', 68.0, 100.0),
        ('107', 'Term 2 Exam', 'Biology', 62.0, 100.0),

        ('107', 'Final Examination', 'Mathematics', 46.0, 100.0),
        ('107', 'Final Examination', 'Physics', 48.0, 100.0),
        ('107', 'Final Examination', 'Chemistry', 52.0, 100.0),
        ('107', 'Final Examination', 'English Literature', 70.0, 100.0),
        ('107', 'Final Examination', 'Biology', 65.0, 100.0),

        # Roll 108 - Diya Sen (Grade 11) - Borderline Math
        ('108', 'Term 1 Exam', 'Mathematics', 45.0, 100.0),
        ('108', 'Term 1 Exam', 'Physics', 62.0, 100.0),
        ('108', 'Term 1 Exam', 'Chemistry', 72.0, 100.0),
        ('108', 'Term 1 Exam', 'English Literature', 82.0, 100.0),
        ('108', 'Term 1 Exam', 'Biology', 78.0, 100.0),

        ('108', 'Mid-Term Examination', 'Mathematics', 48.0, 100.0),
        ('108', 'Mid-Term Examination', 'Physics', 65.0, 100.0),
        ('108', 'Mid-Term Examination', 'Chemistry', 75.0, 100.0),
        ('108', 'Mid-Term Examination', 'English Literature', 85.0, 100.0),
        ('108', 'Mid-Term Examination', 'Biology', 80.0, 100.0),

        ('108', 'Term 2 Exam', 'Mathematics', 50.0, 100.0),
        ('108', 'Term 2 Exam', 'Physics', 68.0, 100.0),
        ('108', 'Term 2 Exam', 'Chemistry', 78.0, 100.0),
        ('108', 'Term 2 Exam', 'English Literature', 86.0, 100.0),
        ('108', 'Term 2 Exam', 'Biology', 82.0, 100.0),

        ('108', 'Final Examination', 'Mathematics', 55.0, 100.0),
        ('108', 'Final Examination', 'Physics', 70.0, 100.0),
        ('108', 'Final Examination', 'Chemistry', 80.0, 100.0),
        ('108', 'Final Examination', 'English Literature', 88.0, 100.0),
        ('108', 'Final Examination', 'Biology', 85.0, 100.0),

        # Roll 109 - Kabir Das (Grade 12) - CRITICAL AT-RISK
        ('109', 'Term 1 Exam', 'Mathematics', 48.0, 100.0),
        ('109', 'Term 1 Exam', 'Physics', 38.0, 100.0),
        ('109', 'Term 1 Exam', 'Chemistry', 42.0, 100.0),
        ('109', 'Term 1 Exam', 'English Literature', 58.0, 100.0),
        ('109', 'Term 1 Exam', 'Computer Science', 60.0, 100.0),

        ('109', 'Mid-Term Examination', 'Mathematics', 44.0, 100.0),
        ('109', 'Mid-Term Examination', 'Physics', 32.0, 100.0),
        ('109', 'Mid-Term Examination', 'Chemistry', 36.0, 100.0),
        ('109', 'Mid-Term Examination', 'English Literature', 55.0, 100.0),
        ('109', 'Mid-Term Examination', 'Computer Science', 58.0, 100.0),

        ('109', 'Term 2 Exam', 'Mathematics', 42.0, 100.0),
        ('109', 'Term 2 Exam', 'Physics', 30.0, 100.0),
        ('109', 'Term 2 Exam', 'Chemistry', 35.0, 100.0),
        ('109', 'Term 2 Exam', 'English Literature', 52.0, 100.0),
        ('109', 'Term 2 Exam', 'Computer Science', 54.0, 100.0),

        ('109', 'Final Examination', 'Mathematics', 46.0, 100.0),
        ('109', 'Final Examination', 'Physics', 35.0, 100.0),
        ('109', 'Final Examination', 'Chemistry', 40.0, 100.0),
        ('109', 'Final Examination', 'English Literature', 56.0, 100.0),
        ('109', 'Final Examination', 'Computer Science', 58.0, 100.0),

        # Roll 110 - Tanvi Reddy (Grade 8) - Solid All-Rounder
        ('110', 'Term 1 Exam', 'Mathematics', 76.0, 100.0),
        ('110', 'Term 1 Exam', 'Physics', 72.0, 100.0),
        ('110', 'Term 1 Exam', 'Chemistry', 74.0, 100.0),
        ('110', 'Term 1 Exam', 'English Literature', 82.0, 100.0),
        ('110', 'Term 1 Exam', 'Biology', 80.0, 100.0),

        ('110', 'Mid-Term Examination', 'Mathematics', 78.0, 100.0),
        ('110', 'Mid-Term Examination', 'Physics', 75.0, 100.0),
        ('110', 'Mid-Term Examination', 'Chemistry', 76.0, 100.0),
        ('110', 'Mid-Term Examination', 'English Literature', 84.0, 100.0),
        ('110', 'Mid-Term Examination', 'Biology', 82.0, 100.0),

        ('110', 'Term 2 Exam', 'Mathematics', 80.0, 100.0),
        ('110', 'Term 2 Exam', 'Physics', 78.0, 100.0),
        ('110', 'Term 2 Exam', 'Chemistry', 80.0, 100.0),
        ('110', 'Term 2 Exam', 'English Literature', 86.0, 100.0),
        ('110', 'Term 2 Exam', 'Biology', 85.0, 100.0),

        ('110', 'Final Examination', 'Mathematics', 84.0, 100.0),
        ('110', 'Final Examination', 'Physics', 80.0, 100.0),
        ('110', 'Final Examination', 'Chemistry', 82.0, 100.0),
        ('110', 'Final Examination', 'English Literature', 88.0, 100.0),
        ('110', 'Final Examination', 'Biology', 88.0, 100.0)
    ]

    for roll, exam, sub, marks, max_m in marks_seed:
        cur.execute("""
            INSERT INTO Marks_Details (ROLL_NUMBER, EXAM_TYPE, SUBJECT, MARKS_OBTAINED, MAX_MARKS)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE MARKS_OBTAINED = VALUES(MARKS_OBTAINED), MAX_MARKS = VALUES(MAX_MARKS)
        """, (roll, exam, sub, marks, max_m))
    con.commit()


def _seed_starter_interventions(cur, con):
    """Internal helper to seed realistic academic support intervention action plans."""
    interventions = [
        (
            'SUP-2026-001', '109', 'Kabir Das', 'Grade 12', 'Critical',
            'Physics, Chemistry, Mathematics', 46.00, 'Prof. Sunita Menon',
            'Bi-weekly 1-on-1 problem clinics, remedial lab assignments, weekly mock tests',
            'Student exhibits severe conceptual blockage in Electromagnetism and Organic Chemistry synthesis. Mandatory 45-min post-school remedial problem clinic every Tuesday and Thursday.',
            'Yes', 'In Progress'
        ),
        (
            'SUP-2026-002', '107', 'Aditya Verma', 'Grade 8', 'Moderate',
            'Mathematics, Physics', 51.90, 'Dr. Rajesh Khanna',
            'Foundational algebra drills, peer-tutoring partnership with Tanvi Reddy',
            'Difficulty with linear equations, algebraic identities, and unit conversions. Assigned peer-study partner (Tanvi) during zero period. Weekly review by Dr. Khanna.',
            'Yes', 'In Progress'
        ),
        (
            'SUP-2026-003', '103', 'Rohan Mehta', 'Grade 9', 'Moderate',
            'Chemistry, Physics', 63.10, 'Dr. Meenakshi Rao',
            'Chemical bonding revision modules, weekly laboratory concept assistance',
            'Term 2 marks dropped significantly by 11.5% due to missed stoichiometry sessions. Enrolled in 3-week Chemistry catch-up workshop. Teacher to monitor daily practice homework.',
            'Yes', 'Open'
        )
    ]
    cur.executemany("""
        INSERT INTO Academic_Interventions 
        (INTERVENTION_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, RISK_LEVEL, STRUGGLING_SUBJECTS, CURRENT_AVERAGE, ASSIGNED_MENTOR, REMEDIAL_STRATEGY, ACTION_PLAN, PARENT_NOTIFIED, STATUS)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, interventions)
    con.commit()


# --------------------------------- ANALYTICS AGGREGATIONS -------------------------

def get_performance_kpis():
    """Returns top-level executive KPI metrics for dashboard summary cards."""
    con = get_connection()
    if not con:
        return {}
    cur = con.cursor(dictionary=True)
    kpis = {
        "overall_average": 0.0,
        "term_delta": "+2.4%",
        "top_class": "Grade 10",
        "top_class_avg": 91.3,
        "struggling_subject": "Physics",
        "struggling_subject_avg": 67.6,
        "struggling_subject_fail_rate": 10.0,
        "flagged_students_count": 0,
        "critical_count": 0,
        "moderate_count": 0,
        "watchlist_count": 0,
        "total_evaluations": 0,
        "total_students": 0
    }
    try:
        cur.execute("SELECT COUNT(*) AS total_evals, ROUND(AVG(MARKS_OBTAINED), 1) as overall_avg FROM Marks_Details")
        row = cur.fetchone()
        if row and row["total_evals"]:
            kpis["total_evaluations"] = row["total_evals"]
            kpis["overall_average"] = float(row["overall_avg"])

        # Top class
        cur.execute("""
            SELECT s.CLASS, ROUND(AVG(m.MARKS_OBTAINED), 1) as class_avg
            FROM Marks_Details m
            JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
            GROUP BY s.CLASS
            ORDER BY class_avg DESC LIMIT 1
        """)
        c_row = cur.fetchone()
        if c_row:
            kpis["top_class"] = c_row["CLASS"]
            kpis["top_class_avg"] = float(c_row["class_avg"])

        # Struggling subject (lowest average and highest failure rate)
        cur.execute("""
            SELECT SUBJECT, ROUND(AVG(MARKS_OBTAINED), 1) as sub_avg,
                   ROUND(SUM(CASE WHEN MARKS_OBTAINED < 40 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as fail_pct
            FROM Marks_Details
            GROUP BY SUBJECT
            ORDER BY fail_pct DESC, sub_avg ASC LIMIT 1
        """)
        s_row = cur.fetchone()
        if s_row:
            kpis["struggling_subject"] = s_row["SUBJECT"]
            kpis["struggling_subject_avg"] = float(s_row["sub_avg"])
            kpis["struggling_subject_fail_rate"] = float(s_row["fail_pct"])

        # Student support counts
        at_risk = get_at_risk_students_registry()
        kpis["flagged_students_count"] = len(at_risk)
        kpis["critical_count"] = sum(1 for s in at_risk if s["risk_tier"] == "Critical")
        kpis["moderate_count"] = sum(1 for s in at_risk if s["risk_tier"] == "Moderate")
        kpis["watchlist_count"] = sum(1 for s in at_risk if s["risk_tier"] == "Watchlist")

        cur.execute("SELECT COUNT(*) AS cnt FROM Students_Details")
        kpis["total_students"] = cur.fetchone()["cnt"]

    except ms.Error as e:
        print("KPI Computation Error:", e)
    finally:
        cur.close()
        con.close()
    return kpis


def get_multi_term_trends(class_filter=None):
    """Calculates term-over-term averages schoolwide, per-class, and per-student."""
    con = get_connection()
    if not con:
        return {"terms": [], "school_trends": [], "class_trends": {}, "student_trajectories": []}
    cur = con.cursor(dictionary=True)
    terms = ["Term 1 Exam", "Mid-Term Examination", "Term 2 Exam", "Final Examination"]
    school_trends = []
    class_trends = {}
    student_trajectories = []

    try:
        # 1. School-wide term averages
        cur.execute("""
            SELECT EXAM_TYPE, ROUND(AVG(MARKS_OBTAINED), 1) as avg_marks
            FROM Marks_Details
            GROUP BY EXAM_TYPE
            ORDER BY FIELD(EXAM_TYPE, 'Term 1 Exam', 'Mid-Term Examination', 'Term 2 Exam', 'Final Examination')
        """)
        school_dict = {r["EXAM_TYPE"]: float(r["avg_marks"]) for r in cur.fetchall()}
        school_trends = [school_dict.get(t, 0.0) for t in terms]

        # 2. Class-specific term trends
        cur.execute("""
            SELECT s.CLASS, m.EXAM_TYPE, ROUND(AVG(m.MARKS_OBTAINED), 1) as avg_marks
            FROM Marks_Details m
            JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
            GROUP BY s.CLASS, m.EXAM_TYPE
            ORDER BY s.CLASS, FIELD(m.EXAM_TYPE, 'Term 1 Exam', 'Mid-Term Examination', 'Term 2 Exam', 'Final Examination')
        """)
        for row in cur.fetchall():
            c_name = row["CLASS"]
            if c_name not in class_trends:
                class_trends[c_name] = {}
            class_trends[c_name][row["EXAM_TYPE"]] = float(row["avg_marks"])

        # 3. Student-level multi-term progression
        where_clause = "WHERE s.CLASS = %s" if class_filter and class_filter != "All" else ""
        params = (class_filter,) if class_filter and class_filter != "All" else ()
        cur.execute(f"""
            SELECT s.ROLL_NUMBER, s.NAME, s.CLASS, m.EXAM_TYPE, ROUND(AVG(m.MARKS_OBTAINED), 1) as term_avg
            FROM Students_Details s
            LEFT JOIN Marks_Details m ON s.ROLL_NUMBER = m.ROLL_NUMBER
            {where_clause}
            GROUP BY s.ROLL_NUMBER, s.NAME, s.CLASS, m.EXAM_TYPE
            ORDER BY s.ROLL_NUMBER ASC
        """, params)

        student_dict = {}
        for r in cur.fetchall():
            roll = r["ROLL_NUMBER"]
            if roll not in student_dict:
                student_dict[roll] = {
                    "roll": roll,
                    "name": r["NAME"],
                    "class": r["CLASS"],
                    "term1": None,
                    "midterm": None,
                    "term2": None,
                    "final": None,
                    "overall_avg": 0.0
                }
            etype = r["EXAM_TYPE"]
            avg_val = float(r["term_avg"]) if r["term_avg"] is not None else 0.0
            if etype == "Term 1 Exam":
                student_dict[roll]["term1"] = avg_val
            elif etype == "Mid-Term Examination":
                student_dict[roll]["midterm"] = avg_val
            elif etype == "Term 2 Exam":
                student_dict[roll]["term2"] = avg_val
            elif etype == "Final Examination":
                student_dict[roll]["final"] = avg_val

        for roll, data in student_dict.items():
            valid_scores = [v for v in [data["term1"], data["midterm"], data["term2"], data["final"]] if v is not None]
            data["overall_avg"] = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0
            
            # Trajectory calculation (first term vs last term)
            first_term = data["term1"] or data["midterm"] or 0.0
            last_term = data["final"] or data["term2"] or 0.0
            delta = round(last_term - first_term, 1)
            data["delta"] = delta
            if delta >= 3.0:
                data["trajectory"] = "Improving"
                data["trajectory_icon"] = "fa-arrow-trend-up"
                data["trajectory_badge"] = "badge-emerald"
            elif delta <= -3.0:
                data["trajectory"] = "Declining"
                data["trajectory_icon"] = "fa-arrow-trend-down"
                data["trajectory_badge"] = "badge-rose"
            else:
                data["trajectory"] = "Stable"
                data["trajectory_icon"] = "fa-minus"
                data["trajectory_badge"] = "badge-blue"

            student_trajectories.append(data)

    except ms.Error as e:
        print("Trends Query Error:", e)
    finally:
        cur.close()
        con.close()

    return {
        "terms": terms,
        "school_trends": school_trends,
        "class_trends": class_trends,
        "student_trajectories": student_trajectories
    }


def get_subject_struggle_diagnostics(term_filter=None, class_filter=None):
    """Identifies curriculum subjects where students are struggling most with failure rates."""
    con = get_connection()
    if not con:
        return []
    cur = con.cursor(dictionary=True)
    diagnostics = []

    # Faculty in-charge and pedagogical recommendation mappings
    subject_meta = {
        "Physics": {
            "faculty": "Prof. Sunita Menon",
            "department": "Department of Physical Sciences",
            "struggle_focus": "Numerical derivations, Electromagnetism, Kinematics vectors",
            "recommendation": "Institute bi-weekly practical problem-solving clinics; provide visual simulation applets."
        },
        "Chemistry": {
            "faculty": "Dr. Meenakshi Rao",
            "department": "Department of Chemical Sciences",
            "struggle_focus": "Stoichiometry, Chemical equation balancing, Organic mechanisms",
            "recommendation": "Conduct weekly 1-on-1 laboratory balance workshops; distribute formula cheat-sheets."
        },
        "Mathematics": {
            "faculty": "Dr. Rajesh Khanna",
            "department": "Department of Pure Mathematics",
            "struggle_focus": "Algebraic factorization, Coordinate geometry, Calculus limits",
            "recommendation": "Implement peer-assisted study circles and daily 15-minute foundational drill sheets."
        },
        "Biology": {
            "faculty": "Ms. Priya Deshmukh",
            "department": "Department of Life Sciences",
            "struggle_focus": "Botanical taxonomy terminology, Physiology diagrams",
            "recommendation": "Reinforce with interactive 3D anatomy models and structured concept-mapping flashcards."
        },
        "English Literature": {
            "faculty": "Mr. Amitav Ghosh",
            "department": "Department of Humanities & Arts",
            "struggle_focus": "Critical literary essays, Poetry analysis, Lexical precision",
            "recommendation": "Organize structured essay drafting peer-reviews and weekly editorial vocabulary readings."
        },
        "Computer Science": {
            "faculty": "Mr. Neeraj Joshi",
            "department": "Department of Computing & Information Tech",
            "struggle_focus": "Algorithmic recursion, Dynamic data structures, Syntax debugging",
            "recommendation": "Encourage paired-programming laboratory sessions and unit-tested code repos."
        }
    }

    try:
        where_clauses = []
        params = []
        if term_filter and term_filter != "All":
            where_clauses.append("m.EXAM_TYPE = %s")
            params.append(term_filter)
        if class_filter and class_filter != "All":
            where_clauses.append("s.CLASS = %s")
            params.append(class_filter)
        
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT m.SUBJECT,
                   ROUND(AVG(m.MARKS_OBTAINED), 1) as avg_marks,
                   ROUND(MIN(m.MARKS_OBTAINED), 1) as min_marks,
                   ROUND(MAX(m.MARKS_OBTAINED), 1) as max_marks,
                   COUNT(*) as total_evals,
                   SUM(CASE WHEN m.MARKS_OBTAINED < 40 THEN 1 ELSE 0 END) as fail_count,
                   SUM(CASE WHEN m.MARKS_OBTAINED >= 40 THEN 1 ELSE 0 END) as pass_count,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED < 40 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as fail_pct,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED >= 40 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pass_pct,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED >= 80 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as distinction_pct
            FROM Marks_Details m
            JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
            {where_sql}
            GROUP BY m.SUBJECT
            ORDER BY fail_pct DESC, avg_marks ASC
        """
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        for r in rows:
            sub_name = r["SUBJECT"]
            avg_m = float(r["avg_marks"])
            fail_p = float(r["fail_pct"])
            pass_p = float(r["pass_pct"])

            # Determine struggle severity
            if avg_m < 68.0 or fail_p >= 10.0:
                struggle_tier = "High Struggle"
                struggle_badge = "badge-rose"
                difficulty_score = "8.8 / 10"
                urgency = "Action Required"
            elif avg_m < 75.0 or fail_p > 0.0:
                struggle_tier = "Moderate Concern"
                struggle_badge = "badge-amber"
                difficulty_score = "6.9 / 10"
                urgency = "Monitor & Assist"
            else:
                struggle_tier = "Strong Mastery"
                struggle_badge = "badge-emerald"
                difficulty_score = "4.2 / 10"
                urgency = "On Track"

            meta = subject_meta.get(sub_name, {
                "faculty": "Faculty Staff",
                "department": "Academic Department",
                "struggle_focus": "Core curriculum competencies",
                "recommendation": "Review formative assessment milestones and provide tutorial exercises."
            })

            diagnostics.append({
                "subject": sub_name,
                "avg_marks": avg_m,
                "min_marks": float(r["min_marks"]),
                "max_marks": float(r["max_marks"]),
                "total_evals": r["total_evals"],
                "fail_count": int(r["fail_count"]),
                "pass_count": int(r["pass_count"]),
                "fail_pct": fail_p,
                "pass_pct": pass_p,
                "distinction_pct": float(r["distinction_pct"]),
                "struggle_tier": struggle_tier,
                "struggle_badge": struggle_badge,
                "difficulty_score": difficulty_score,
                "urgency": urgency,
                "faculty": meta["faculty"],
                "department": meta["department"],
                "struggle_focus": meta["struggle_focus"],
                "recommendation": meta["recommendation"]
            })

    except ms.Error as e:
        print("Subject Diagnostics Error:", e)
    finally:
        cur.close()
        con.close()

    return diagnostics


def get_class_comparative_benchmarks(term_filter=None):
    """Compares class averages, pass percentages, top performers, and struggling areas."""
    con = get_connection()
    if not con:
        return []
    cur = con.cursor(dictionary=True)
    benchmarks = []

    try:
        where_clause = "WHERE m.EXAM_TYPE = %s" if term_filter and term_filter != "All" else ""
        params = (term_filter,) if term_filter and term_filter != "All" else ()

        cur.execute(f"""
            SELECT s.CLASS,
                   ROUND(AVG(m.MARKS_OBTAINED), 1) as class_avg,
                   COUNT(DISTINCT s.ROLL_NUMBER) as student_count,
                   COUNT(m.ID) as total_papers,
                   ROUND(MAX(m.MARKS_OBTAINED), 1) as max_score,
                   ROUND(MIN(m.MARKS_OBTAINED), 1) as min_score,
                   SUM(CASE WHEN m.MARKS_OBTAINED >= 40 THEN 1 ELSE 0 END) as passed_papers,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED >= 40 THEN 1 ELSE 0 END) * 100.0 / COUNT(m.ID), 1) as class_pass_pct,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED >= 80 THEN 1 ELSE 0 END) * 100.0 / COUNT(m.ID), 1) as distinction_pct,
                   ROUND(SUM(CASE WHEN m.MARKS_OBTAINED < 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(m.ID), 1) as struggle_rate
            FROM Students_Details s
            LEFT JOIN Marks_Details m ON s.ROLL_NUMBER = m.ROLL_NUMBER
            {where_clause}
            GROUP BY s.CLASS
            ORDER BY class_avg DESC
        """, params)

        rows = cur.fetchall()

        # Identify top subject and struggling subject for each class
        for r in rows:
            c_name = r["CLASS"]
            sub_params = [c_name]
            sub_where = "WHERE s.CLASS = %s"
            if term_filter and term_filter != "All":
                sub_where += " AND m.EXAM_TYPE = %s"
                sub_params.append(term_filter)

            cur.execute(f"""
                SELECT m.SUBJECT, ROUND(AVG(m.MARKS_OBTAINED), 1) as sub_avg
                FROM Marks_Details m
                JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
                {sub_where}
                GROUP BY m.SUBJECT
                ORDER BY sub_avg DESC
            """, tuple(sub_params))
            sub_rows = cur.fetchall()

            top_sub = f"{sub_rows[0]['SUBJECT']} ({sub_rows[0]['sub_avg']}%)" if sub_rows else "N/A"
            low_sub = f"{sub_rows[-1]['SUBJECT']} ({sub_rows[-1]['sub_avg']}%)" if sub_rows else "N/A"

            # Top student in class
            cur.execute(f"""
                SELECT s.NAME, ROUND(AVG(m.MARKS_OBTAINED), 1) as student_avg
                FROM Students_Details s
                JOIN Marks_Details m ON s.ROLL_NUMBER = m.ROLL_NUMBER
                {sub_where}
                GROUP BY s.ROLL_NUMBER, s.NAME
                ORDER BY student_avg DESC LIMIT 1
            """, tuple(sub_params))
            top_stud_row = cur.fetchone()
            top_student = f"{top_stud_row['NAME']} ({top_stud_row['student_avg']}%)" if top_stud_row else "N/A"

            benchmarks.append({
                "class_name": c_name,
                "class_avg": float(r["class_avg"]) if r["class_avg"] is not None else 0.0,
                "student_count": r["student_count"],
                "total_papers": r["total_papers"],
                "max_score": float(r["max_score"]) if r["max_score"] is not None else 0.0,
                "min_score": float(r["min_score"]) if r["min_score"] is not None else 0.0,
                "class_pass_pct": float(r["class_pass_pct"]) if r["class_pass_pct"] is not None else 0.0,
                "distinction_pct": float(r["distinction_pct"]) if r["distinction_pct"] is not None else 0.0,
                "struggle_rate": float(r["struggle_rate"]) if r["struggle_rate"] is not None else 0.0,
                "top_subject": top_sub,
                "struggling_subject": low_sub,
                "top_student": top_student
            })

    except ms.Error as e:
        print("Class Benchmark Error:", e)
    finally:
        cur.close()
        con.close()

    return benchmarks


def get_at_risk_students_registry():
    """Identifies and flags students who require additional support and academic intervention."""
    con = get_connection()
    if not con:
        return []
    cur = con.cursor(dictionary=True)
    at_risk_list = []

    try:
        cur.execute("""
            SELECT s.ROLL_NUMBER, s.NAME, s.CLASS, s.GENDER, s.PHONE, s.EMAIL,
                   ROUND(AVG(m.MARKS_OBTAINED), 1) as overall_avg,
                   SUM(CASE WHEN m.MARKS_OBTAINED < 40 THEN 1 ELSE 0 END) as failed_papers_count,
                   COUNT(m.ID) as total_papers,
                   ai.INTERVENTION_CODE,
                   ai.STATUS as intervention_status,
                   ai.ASSIGNED_MENTOR,
                   ai.REMEDIAL_STRATEGY
            FROM Students_Details s
            LEFT JOIN Marks_Details m ON s.ROLL_NUMBER = m.ROLL_NUMBER
            LEFT JOIN Academic_Interventions ai ON s.ROLL_NUMBER = ai.ROLL_NUMBER AND ai.STATUS != 'Resolved'
            GROUP BY s.ROLL_NUMBER, s.NAME, s.CLASS, s.GENDER, s.PHONE, s.EMAIL, ai.INTERVENTION_CODE, ai.STATUS, ai.ASSIGNED_MENTOR, ai.REMEDIAL_STRATEGY
            ORDER BY overall_avg ASC
        """)
        students = cur.fetchall()

        for s in students:
            avg_m = float(s["overall_avg"]) if s["overall_avg"] is not None else 0.0
            failed_cnt = int(s["failed_papers_count"]) if s["failed_papers_count"] is not None else 0

            # Determine struggling subjects for this student
            cur.execute("""
                SELECT SUBJECT, ROUND(AVG(MARKS_OBTAINED), 1) as sub_avg,
                       SUM(CASE WHEN MARKS_OBTAINED < 40 THEN 1 ELSE 0 END) as fails
                FROM Marks_Details
                WHERE ROLL_NUMBER = %s
                GROUP BY SUBJECT
                HAVING sub_avg < 52.0 OR fails > 0
                ORDER BY sub_avg ASC
            """, (s["ROLL_NUMBER"],))
            weak_subs = cur.fetchall()
            weak_sub_list = [f"{w['SUBJECT']} ({w['sub_avg']}%)" for w in weak_subs]

            # Flagging logic
            is_at_risk = False
            risk_tier = None
            risk_badge = None
            primary_reason = None

            if avg_m < 50.0 or failed_cnt >= 2:
                is_at_risk = True
                risk_tier = "Critical"
                risk_badge = "badge-rose"
                primary_reason = f"High failure count ({failed_cnt} failed papers) & low composite average ({avg_m}%)."
            elif avg_m < 65.0 and (failed_cnt >= 1 or len(weak_subs) >= 2):
                is_at_risk = True
                risk_tier = "Moderate"
                risk_badge = "badge-amber"
                primary_reason = f"Struggling in core STEM areas with {failed_cnt} failed exam papers."
            elif len(weak_subs) >= 1 or avg_m < 72.0:
                is_at_risk = True
                risk_tier = "Watchlist"
                risk_badge = "badge-blue"
                primary_reason = f"Borderline subject performance in {weak_subs[0]['SUBJECT'] if weak_subs else 'academic subjects'}."

            if is_at_risk:
                at_risk_list.append({
                    "roll": s["ROLL_NUMBER"],
                    "name": s["NAME"],
                    "class": s["CLASS"],
                    "gender": s["GENDER"],
                    "phone": s["PHONE"],
                    "email": s["EMAIL"],
                    "overall_avg": avg_m,
                    "failed_count": failed_cnt,
                    "weak_subjects": ", ".join(weak_sub_list) if weak_sub_list else "Borderline Passing",
                    "risk_tier": risk_tier,
                    "risk_badge": risk_badge,
                    "primary_reason": primary_reason,
                    "intervention_code": s["INTERVENTION_CODE"],
                    "intervention_status": s["intervention_status"] or "Action Needed",
                    "assigned_mentor": s["ASSIGNED_MENTOR"] or "Unassigned",
                    "remedial_strategy": s["REMEDIAL_STRATEGY"] or "Pending Plan"
                })

    except ms.Error as e:
        print("At-Risk Student Registry Error:", e)
    finally:
        cur.close()
        con.close()

    return at_risk_list


def get_academic_interventions_list():
    """Returns the full ledger of recorded Academic Support Plans."""
    con = get_connection()
    if not con:
        return []
    cur = con.cursor(dictionary=True)
    interventions = []
    try:
        cur.execute("""
            SELECT * FROM Academic_Interventions 
            ORDER BY FIELD(STATUS, 'Open', 'In Progress', 'Under Review', 'Resolved'), ID DESC
        """)
        interventions = cur.fetchall()
        for i in interventions:
            rl = i["RISK_LEVEL"]
            i["risk_badge"] = "badge-rose" if rl == "Critical" else ("badge-amber" if rl == "Moderate" else "badge-blue")
            st = i["STATUS"]
            i["status_badge"] = "status-active" if st == "Resolved" else ("badge-amber" if st == "In Progress" else "badge-rose")
    except ms.Error as e:
        print("Interventions Ledger Error:", e)
    finally:
        cur.close()
        con.close()
    return interventions


def create_academic_intervention(roll, mentor, strategy, action_plan, risk_level="Moderate", parent_notified="Yes"):
    """Creates a new student academic support intervention record."""
    con = get_connection()
    if not con:
        return False, "Database connection failed."
    cur = con.cursor(dictionary=True)
    try:
        # Validate student
        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        stud = cur.fetchone()
        if not stud:
            return False, f"Student with Roll Number {roll} not found."

        # Compute current overall average & struggling subjects
        cur.execute("""
            SELECT ROUND(AVG(MARKS_OBTAINED), 2) as current_avg
            FROM Marks_Details
            WHERE ROLL_NUMBER = %s
        """, (roll,))
        avg_row = cur.fetchone()
        curr_avg = float(avg_row["current_avg"]) if avg_row and avg_row["current_avg"] else 0.0

        cur.execute("""
            SELECT SUBJECT, ROUND(AVG(MARKS_OBTAINED), 1) as sub_avg
            FROM Marks_Details
            WHERE ROLL_NUMBER = %s
            GROUP BY SUBJECT
            HAVING sub_avg < 55.0
            ORDER BY sub_avg ASC
        """, (roll,))
        weaks = [f"{r['SUBJECT']} ({r['sub_avg']}%)" for r in cur.fetchall()]
        struggle_str = ", ".join(weaks) if weaks else "General Academic Support"

        # Generate unique code
        code = f"SUP-2026-{datetime.datetime.now().strftime('%f')[:4]}"

        cur.execute("""
            INSERT INTO Academic_Interventions 
            (INTERVENTION_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, RISK_LEVEL, STRUGGLING_SUBJECTS, CURRENT_AVERAGE, ASSIGNED_MENTOR, REMEDIAL_STRATEGY, ACTION_PLAN, PARENT_NOTIFIED, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Open')
        """, (code, roll, stud["NAME"], stud["CLASS"], risk_level, struggle_str, curr_avg, mentor, strategy, action_plan, parent_notified))
        con.commit()
        return True, f"Academic Support Plan {code} created successfully for {stud['NAME']}!"
    except ms.Error as e:
        return False, f"Database Error: {e}"
    finally:
        cur.close()
        con.close()


def update_intervention_status(intervention_id, new_status, notes=""):
    """Updates the lifecycle status of an intervention record."""
    con = get_connection()
    if not con:
        return False, "Database connection failed."
    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Academic_Interventions WHERE ID = %s", (intervention_id,))
        rec = cur.fetchone()
        if not rec:
            return False, "Intervention record not found."

        updated_plan = rec["ACTION_PLAN"]
        if notes:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            updated_plan = f"{updated_plan}\n[{timestamp} Progress Note]: {notes}"

        cur.execute("""
            UPDATE Academic_Interventions 
            SET STATUS = %s, ACTION_PLAN = %s 
            WHERE ID = %s
        """, (new_status, updated_plan, intervention_id))
        con.commit()
        return True, f"Intervention {rec['INTERVENTION_CODE']} updated to '{new_status}'."
    except ms.Error as e:
        return False, f"Database Error: {e}"
    finally:
        cur.close()
        con.close()


def delete_intervention(intervention_id):
    """Deletes an intervention record by ID."""
    con = get_connection()
    if not con:
        return False, "Database connection failed."
    cur = con.cursor()
    try:
        cur.execute("DELETE FROM Academic_Interventions WHERE ID = %s", (intervention_id,))
        con.commit()
        return True, "Intervention record deleted successfully."
    except ms.Error as e:
        return False, f"Database Error: {e}"
    finally:
        cur.close()
        con.close()


# --------------------------------- MATPLOTLIB CHARTS ------------------------------

def plot_performance_analytics():
    """Generates rich 3-in-1 graphical charts displaying trends, subject struggles, and class benchmarks."""
    trends = get_multi_term_trends()
    subjects = get_subject_struggle_diagnostics()
    classes = get_class_comparative_benchmarks()

    if not trends["terms"] or not subjects:
        print("Insufficient examination marks data to generate performance charts.")
        pause_and_clear()
        return

    try:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(
            "Student Performance Analytics Executive Report\n(Multi-Term Trends, Subject Struggles & Class Benchmarks)",
            fontsize=14, fontweight="bold"
        )

        # 1. Multi-Term Trajectories Line Chart
        terms = trends["terms"]
        ax1.plot(terms, trends["school_trends"], marker="o", linewidth=2.5, color="#2563eb", label="School Overall Avg")
        color_palette = ["#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
        for idx, (c_name, c_dict) in enumerate(trends["class_trends"].items()):
            c_vals = [c_dict.get(t, None) for t in terms]
            ax1.plot(terms, c_vals, marker="s", linestyle="--", linewidth=1.5, color=color_palette[idx % len(color_palette)], label=c_name)

        ax1.set_title("Academic Performance Trends Across Terms", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Average Score (%)", fontweight="bold")
        ax1.set_ylim(40, 100)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="lower right", fontsize=8)
        plt.setp(ax1.get_xticklabels(), rotation=15, ha="right")

        # 2. Subject Struggle Rate & Average Score
        sub_names = [s["subject"] for s in reversed(subjects)]
        sub_avgs = [s["avg_marks"] for s in reversed(subjects)]
        sub_fails = [s["fail_pct"] for s in reversed(subjects)]

        y_pos = range(len(sub_names))
        bar_colors = ["#e11d48" if f >= 10.0 else ("#f59e0b" if f > 0 else "#10b981") for f in sub_fails]
        bars = ax2.barh(y_pos, sub_avgs, color=bar_colors, edgecolor="black", height=0.6)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(sub_names, fontweight="bold")
        ax2.set_title("Subject Performance & Struggle Severity\n(Red: High Struggle | Amber: Concern | Green: Mastery)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Subject Average Score (%)", fontweight="bold")
        ax2.set_xlim(0, 100)
        ax2.grid(axis="x", linestyle=":", alpha=0.6)

        for bar, avg_v, fail_v in zip(bars, sub_avgs, sub_fails):
            ax2.text(
                avg_v + 1.5, bar.get_y() + bar.get_height() / 2.0,
                f"{avg_v}% (Fail: {fail_v}%)",
                va="center", ha="left", fontsize=8, fontweight="bold"
            )

        # 3. Class Averages Comparison
        c_labels = [c["class_name"] for c in classes]
        c_avgs = [c["class_avg"] for c in classes]
        c_colors = ["#10b981" if a >= 80 else ("#3b82f6" if a >= 70 else "#f59e0b") for a in c_avgs]
        cbars = ax3.bar(c_labels, c_avgs, color=c_colors, edgecolor="black", width=0.55)
        ax3.set_title("Comparative Class Averages & Benchmarks", fontsize=11, fontweight="bold")
        ax3.set_ylabel("Class Average (%)", fontweight="bold")
        ax3.set_ylim(0, 105)
        ax3.grid(axis="y", linestyle=":", alpha=0.6)

        for bar in cbars:
            h = bar.get_height()
            ax3.text(
                bar.get_x() + bar.get_width() / 2.0, h + 1.5,
                f"{h}%",
                ha="center", va="bottom", fontsize=9, fontweight="bold"
            )

        plt.tight_layout()
        print("\nOpening Student Performance Analytics Dashboard... (Close window to return)")
        plt.show()

    except Exception as e:
        print("Performance Chart Error:", e)
        pause_and_clear()


def plot_school_demographics():
    """Preserved: Plots school demographics and gender distribution."""
    con = get_connection()
    if not con:
        print("Database connection failed.")
        return
    cur = con.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Students_Details")
        total_students = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Teachers_Details")
        total_teachers = cur.fetchone()[0]

        if total_students == 0:
            print("No student records available to generate demographics.")
            pause_and_clear()
            return

        cur.execute("SELECT CLASS, COUNT(*) FROM Students_Details GROUP BY CLASS ORDER BY CLASS")
        class_data = cur.fetchall()
        classes = [r[0] for r in class_data]
        student_counts = [r[1] for r in class_data]

        cur.execute("SELECT GENDER, COUNT(*) FROM Students_Details GROUP BY GENDER")
        gender_data = cur.fetchall()
        genders = [r[0] for r in gender_data]
        gender_counts = [r[1] for r in gender_data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(
            f"School Demographics & Executive Overview\n(Total Students: {total_students} | Faculty: {total_teachers})",
            fontsize=14, fontweight="bold"
        )

        bars = ax1.bar(classes, student_counts, color="#3498db", edgecolor="black", width=0.55)
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2.0, height + 0.1, f"{int(height)}", ha="center", va="bottom", fontweight="bold")
        ax1.set_title("Student Enrollment by Class", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Class / Grade", fontweight="bold")
        ax1.set_ylabel("Number of Students", fontweight="bold")
        ax1.grid(axis="y", linestyle=":", alpha=0.6)

        gender_colors_map = {"Male": "#2980b9", "Female": "#e84393", "Other": "#9b59b6"}
        pie_colors = [gender_colors_map.get(g, "#95a5a6") for g in genders]

        ax2.pie(
            gender_counts,
            labels=[f"{g} ({c})" for g, c in zip(genders, gender_counts)],
            colors=pie_colors,
            autopct="%1.1f%%",
            startangle=140,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
        )
        ax2.set_title("Gender Ratio Breakdown", fontsize=11, fontweight="bold")
        plt.tight_layout()
        print("\nOpening Demographics Dashboard... (Close window to return)")
        plt.show()
    except Exception as e:
        print("Demographics Chart Error:", e)
        pause_and_clear()
    finally:
        cur.close()
        con.close()


# --------------------------------- INTERACTIVE TERMINAL CLI MENU ------------------

def analytics_menu():
    """Terminal CLI user interface for Performance Analytics & Student Support."""
    init_analytics_tables()
    while True:
        clear_screen()
        center_text("=" * 80)
        center_text("STUDENT PERFORMANCE ANALYTICS & INTERVENTION HUB")
        center_text("(Trends Across Terms, Subject Struggles, Class Benchmarks & Support)")
        center_text("=" * 80)
        print("\n1. View Academic Performance Trends Across Terms")
        print("2. Subject Struggle Diagnostic & Difficult Areas Report")
        print("3. Class-by-Class Comparative Benchmarks")
        print("4. View Flagged At-Risk Students Requiring Support")
        print("5. Manage Academic Intervention & Remedial Action Plans")
        print("6. Launch Visual Analytics Charts (Matplotlib Visualizer)")
        print("7. Launch School Demographics & Enrollment Overview")
        print("0. Return to Main Menu\n")

        choice = input("Enter your choice (0-7): ").strip()

        if choice == "1":
            _cli_view_trends()
        elif choice == "2":
            _cli_view_subject_diagnostics()
        elif choice == "3":
            _cli_view_class_benchmarks()
        elif choice == "4":
            _cli_view_at_risk_students()
        elif choice == "5":
            _cli_manage_interventions()
        elif choice == "6":
            plot_performance_analytics()
        elif choice == "7":
            plot_school_demographics()
        elif choice == "0":
            break
        else:
            print("\nInvalid choice. Please try again.")
            pause_and_clear()


def _cli_view_trends():
    clear_screen()
    center_text("=" * 80)
    center_text("ACADEMIC PERFORMANCE TRENDS ACROSS TERMS")
    center_text("=" * 80)
    trends = get_multi_term_trends()
    
    print("\n[ SCHOOL-WIDE TERM PROGRESSION ]")
    term_table = [[t, f"{score:.1f}%"] for t, score in zip(trends["terms"], trends["school_trends"])]
    print(tabulate(term_table, headers=["Examination Term", "School Overall Average"], tablefmt="fancy_grid"))

    print("\n[ INDIVIDUAL STUDENT PROGRESSION TRAJECTORIES ]")
    rows = []
    for s in trends["student_trajectories"]:
        t1 = f"{s['term1']:.1f}%" if s['term1'] else "--"
        mid = f"{s['midterm']:.1f}%" if s['midterm'] else "--"
        t2 = f"{s['term2']:.1f}%" if s['term2'] else "--"
        fin = f"{s['final']:.1f}%" if s['final'] else "--"
        rows.append([s['roll'], s['name'], s['class'], t1, mid, t2, fin, f"{s['overall_avg']:.1f}%", s['trajectory']])
    print(tabulate(rows, headers=["Roll", "Name", "Class", "Term 1", "Mid-Term", "Term 2", "Final", "Overall", "Trajectory"], tablefmt="fancy_grid"))
    pause_and_clear()


def _cli_view_subject_diagnostics():
    clear_screen()
    center_text("=" * 80)
    center_text("SUBJECT STRUGGLE DIAGNOSTIC & HIGH-DIFFICULTY REPORT")
    center_text("=" * 80)
    diagnostics = get_subject_struggle_diagnostics()
    table = []
    for d in diagnostics:
        table.append([
            d["subject"],
            d["faculty"],
            f"{d['avg_marks']:.1f}%",
            f"{d['pass_pct']:.1f}%",
            f"{d['fail_pct']:.1f}%",
            d["struggle_tier"],
            d["difficulty_score"]
        ])
    print(tabulate(table, headers=["Subject", "Faculty Lead", "Avg Score", "Pass Rate", "Fail Rate", "Struggle Tier", "Difficulty"], tablefmt="fancy_grid"))
    print("\n[ RECOMMENDED PEDAGOGICAL INTERVENTIONS ]")
    for d in diagnostics:
        if d["struggle_tier"] in ("High Struggle", "Moderate Concern"):
            print(f"\n• {d['subject'].upper()} ({d['struggle_tier']}):")
            print(f"  - Key Blockages: {d['struggle_focus']}")
            print(f"  - Recommendation: {d['recommendation']}")
    pause_and_clear()


def _cli_view_class_benchmarks():
    clear_screen()
    center_text("=" * 80)
    center_text("CLASS-BY-CLASS COMPARATIVE BENCHMARKS")
    center_text("=" * 80)
    classes = get_class_comparative_benchmarks()
    table = []
    for c in classes:
        table.append([
            c["class_name"],
            c["student_count"],
            f"{c['class_avg']:.1f}%",
            f"{c['class_pass_pct']:.1f}%",
            c["top_student"],
            c["top_subject"],
            c["struggling_subject"]
        ])
    print(tabulate(table, headers=["Class", "Enrolled", "Class Avg", "Pass Rate", "Top Student", "Highest Subject", "Lowest Subject"], tablefmt="fancy_grid"))
    pause_and_clear()


def _cli_view_at_risk_students():
    clear_screen()
    center_text("=" * 80)
    center_text("FLAGGED AT-RISK STUDENTS REQUIRING ACADEMIC SUPPORT")
    center_text("=" * 80)
    at_risk = get_at_risk_students_registry()
    table = []
    for s in at_risk:
        table.append([
            s["roll"],
            s["name"],
            s["class"],
            f"{s['overall_avg']:.1f}%",
            s["risk_tier"],
            s["weak_subjects"][:35] + ("..." if len(s["weak_subjects"]) > 35 else ""),
            s["intervention_status"]
        ])
    print(tabulate(table, headers=["Roll", "Name", "Class", "Average", "Risk Level", "Struggling Subjects", "Support Status"], tablefmt="fancy_grid"))
    pause_and_clear()


def _cli_manage_interventions():
    clear_screen()
    center_text("=" * 80)
    center_text("ACADEMIC INTERVENTION & REMEDIAL ACTION PLANS LEDGER")
    center_text("=" * 80)
    interventions = get_academic_interventions_list()
    table = []
    for i in interventions:
        table.append([
            i["ID"],
            i["INTERVENTION_CODE"],
            f"{i['STUDENT_NAME']} ({i['ROLL_NUMBER']})",
            i["CLASS"],
            i["RISK_LEVEL"],
            i["ASSIGNED_MENTOR"],
            i["STATUS"]
        ])
    print(tabulate(table, headers=["ID", "Code", "Student", "Class", "Risk", "Faculty Mentor", "Status"], tablefmt="fancy_grid"))

    print("\n1. Create New Academic Support Plan")
    print("2. Update Intervention Status")
    print("0. Back to Analytics Menu")
    sub = input("\nEnter choice: ").strip()

    if sub == "1":
        roll = input("Enter Student Roll Number: ").strip()
        mentor = input("Enter Assigned Faculty Mentor: ").strip()
        strategy = input("Enter Remedial Strategy: ").strip()
        plan = input("Enter Action Plan Notes: ").strip()
        risk = input("Enter Risk Level (Critical/Moderate/Watchlist) [Moderate]: ").strip().capitalize() or "Moderate"
        parent = input("Notify Parents? (Yes/No) [Yes]: ").strip().capitalize() or "Yes"
        ok, msg = create_academic_intervention(roll, mentor, strategy, plan, risk, parent)
        print(f"\n{msg}")
        pause_and_clear()
    elif sub == "2":
        try:
            iid = int(input("Enter Intervention ID to update: ").strip())
            new_st = input("Enter New Status (Open/In Progress/Under Review/Resolved): ").strip()
            notes = input("Enter Progress Update Notes: ").strip()
            ok, msg = update_intervention_status(iid, new_st, notes)
            print(f"\n{msg}")
        except ValueError:
            print("Invalid ID format.")
        pause_and_clear()

