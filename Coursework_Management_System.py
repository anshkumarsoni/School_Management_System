# -------------------------------------------------------------------------
# COURSEWORK, ASSIGNMENTS & E-LEARNING MANAGEMENT SYSTEM
# -------------------------------------------------------------------------

import datetime
import mysql.connector as ms
from mysql.connector import Error
from tabulate import tabulate

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear
)

# --------------------------------- TABLE CREATION ---------------------------------

def create_coursework_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        # 1. Assignments
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Assignments (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ASSIGNMENT_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                SUBJECT VARCHAR(80) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                TEACHER_NAME VARCHAR(100) NOT NULL,
                DESCRIPTION TEXT NOT NULL,
                ATTACHMENT_URL VARCHAR(255) NULL,
                ASSIGNED_DATE DATE NOT NULL,
                DUE_DATE DATE NOT NULL,
                MAX_MARKS INT NOT NULL DEFAULT 100,
                STATUS ENUM('Active', 'Closed') DEFAULT 'Active',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Study_Materials
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Study_Materials (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                MATERIAL_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                SUBJECT VARCHAR(80) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                TOPIC VARCHAR(100) NOT NULL,
                RESOURCE_TYPE ENUM('Lecture Notes', 'Worksheet', 'Reference Guide', 'Video Lecture', 'Syllabus') DEFAULT 'Lecture Notes',
                RESOURCE_URL VARCHAR(255) NULL,
                CONTENT_TEXT TEXT NULL,
                UPLOADED_BY VARCHAR(100) NOT NULL,
                UPLOAD_DATE DATE NOT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Assignment_Submissions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Assignment_Submissions (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                SUBMISSION_CODE VARCHAR(30) UNIQUE NOT NULL,
                ASSIGNMENT_CODE VARCHAR(30) NOT NULL,
                STUDENT_ROLL VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                STUDENT_CLASS VARCHAR(50) NOT NULL,
                SUBMISSION_TEXT TEXT NOT NULL,
                FILE_URL VARCHAR(255) NULL,
                SUBMITTED_DATE DATE NOT NULL,
                STATUS ENUM('Submitted', 'Late Submission', 'Graded') DEFAULT 'Submitted',
                MARKS_OBTAINED DECIMAL(5, 2) NULL,
                GRADE VARCHAR(10) NULL,
                TEACHER_FEEDBACK TEXT NULL,
                REVIEWED_BY VARCHAR(100) NULL,
                REVIEWED_DATE DATE NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Learning_Courses
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Learning_Courses (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                COURSE_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                SUBJECT VARCHAR(80) NOT NULL,
                INSTRUCTOR VARCHAR(100) NOT NULL,
                LEVEL ENUM('Beginner', 'Intermediate', 'Advanced') DEFAULT 'Intermediate',
                TOTAL_LESSONS INT DEFAULT 10,
                DURATION_WEEKS INT DEFAULT 12,
                DESCRIPTION TEXT NOT NULL,
                SYLLABUS TEXT NULL,
                STATUS ENUM('Active', 'Upcoming', 'Archived') DEFAULT 'Active',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Online_Quizzes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Online_Quizzes (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                QUIZ_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                SUBJECT VARCHAR(80) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                TIME_MINUTES INT DEFAULT 15,
                PASS_PERCENTAGE INT DEFAULT 60,
                TOTAL_QUESTIONS INT DEFAULT 5,
                CREATED_BY VARCHAR(100) NOT NULL,
                STATUS ENUM('Active', 'Draft', 'Closed') DEFAULT 'Active',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Quiz_Questions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Quiz_Questions (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                QUIZ_CODE VARCHAR(30) NOT NULL,
                QUESTION_NUMBER INT NOT NULL,
                QUESTION_TEXT TEXT NOT NULL,
                OPTION_A VARCHAR(200) NOT NULL,
                OPTION_B VARCHAR(200) NOT NULL,
                OPTION_C VARCHAR(200) NOT NULL,
                OPTION_D VARCHAR(200) NOT NULL,
                CORRECT_OPTION CHAR(1) NOT NULL,
                EXPLANATION TEXT NULL
            )
        """)

        # 7. Quiz_Attempts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Quiz_Attempts (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ATTEMPT_CODE VARCHAR(30) UNIQUE NOT NULL,
                QUIZ_CODE VARCHAR(30) NOT NULL,
                STUDENT_ROLL VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                SCORE INT NOT NULL,
                TOTAL_QUESTIONS INT NOT NULL,
                PERCENTAGE DECIMAL(5, 2) NOT NULL,
                PASSED BOOLEAN NOT NULL,
                ATTEMPT_DATE DATE NOT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.commit()
    except Error as e:
        print("Coursework Tables Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- 1. ASSIGNMENTS ---------------------------------

def view_assignments():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT a.*, 
                   COUNT(s.ID) AS total_submissions,
                   SUM(CASE WHEN s.STATUS = 'Graded' THEN 1 ELSE 0 END) AS graded_count
            FROM Assignments a
            LEFT JOIN Assignment_Submissions s ON a.ASSIGNMENT_CODE = s.ASSIGNMENT_CODE
            GROUP BY a.ID
            ORDER BY a.ID DESC
        """)
        rows = cur.fetchall()
        today = datetime.date.today()

        if rows:
            table_data = []
            for r in rows:
                due = r['DUE_DATE']
                is_due_passed = today > due
                due_status = f"{due.strftime('%Y-%m-%d')} (Past Due)" if is_due_passed else f"{due.strftime('%Y-%m-%d')} ({(due - today).days}d left)"
                table_data.append([
                    r['ASSIGNMENT_CODE'],
                    r['TITLE'][:28],
                    r['SUBJECT'],
                    r['CLASS'],
                    r['TEACHER_NAME'][:18],
                    due_status,
                    r['MAX_MARKS'],
                    f"{r['total_submissions']} ({r['graded_count'] or 0} graded)",
                    r['STATUS']
                ])
            print(tabulate(
                table_data,
                headers=["CODE", "TITLE", "SUBJECT", "CLASS", "TEACHER", "DUE DATE", "MAX", "SUBMISSIONS", "STATUS"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No assignments currently published.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def add_assignment():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        title = input("Enter Assignment Title : : ").strip()
        if not title:
            print("Title cannot be empty!")
            return

        subject = input("Enter Subject (e.g. Physics, Mathematics, Computer Science) : : ").strip()
        cls = input("Enter Class / Standard (e.g. Grade 10, Grade 11) : : ").strip()
        teacher = input("Enter Teacher / Faculty Name : : ").strip()
        desc = input("Enter Assignment Instructions / Problem Set : : ").strip()
        url = input("Reference URL / Resource Link (optional) : : ").strip() or None

        try:
            max_marks = int(input("Enter Maximum Marks (default 50) : : ") or "50")
        except ValueError:
            max_marks = 50

        days = int(input("Days until submission deadline (default 14) : : ") or "14")
        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=days)

        cur.execute("SELECT MAX(ID) FROM Assignments")
        max_id = (cur.fetchone()[0] or 0) + 1
        code = f"ASN-{max_id:03d}"

        cur.execute("""
            INSERT INTO Assignments 
            (ASSIGNMENT_CODE, TITLE, SUBJECT, CLASS, TEACHER_NAME, DESCRIPTION, ATTACHMENT_URL, ASSIGNED_DATE, DUE_DATE, MAX_MARKS, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (code, title, subject, cls, teacher, desc, url, today, due_date, max_marks))
        con.commit()

        print(f"\nAssignment '{title}' ({code}) published successfully! Due date: {due_date.strftime('%b %d, %Y')}")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- 2. STUDY MATERIALS ---------------------------------

def view_study_materials():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Study_Materials ORDER BY ID DESC")
        rows = cur.fetchall()

        if rows:
            table_data = []
            for r in rows:
                table_data.append([
                    r['MATERIAL_CODE'],
                    r['TITLE'][:28],
                    r['SUBJECT'],
                    r['CLASS'],
                    r['TOPIC'],
                    r['RESOURCE_TYPE'],
                    r['UPLOADED_BY'][:18],
                    r['RESOURCE_URL'][:24] if r['RESOURCE_URL'] else '-'
                ])
            print(tabulate(
                table_data,
                headers=["CODE", "TITLE", "SUBJECT", "CLASS", "TOPIC", "TYPE", "UPLOADED BY", "LINK"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No study materials uploaded yet.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def add_study_material():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        title = input("Enter Material Title : : ").strip()
        if not title:
            print("Title cannot be empty!")
            return

        subject = input("Enter Subject : : ").strip()
        cls = input("Enter Class : : ").strip()
        topic = input("Enter Specific Topic / Chapter : : ").strip()

        print("\nSelect Resource Type:")
        print("1. Lecture Notes")
        print("2. Worksheet")
        print("3. Reference Guide")
        print("4. Video Lecture")
        print("5. Syllabus")
        r_type_ch = input("Enter choice (1-5, default 1) : : ").strip()
        r_types = {
            "1": "Lecture Notes",
            "2": "Worksheet",
            "3": "Reference Guide",
            "4": "Video Lecture",
            "5": "Syllabus"
        }
        res_type = r_types.get(r_type_ch, "Lecture Notes")

        url = input("Resource Link / PDF URL (optional) : : ").strip() or None
        notes = input("Key Summary / Notes Description : : ").strip() or None
        uploader = input("Uploaded By (Teacher Name) : : ").strip() or "Faculty"

        today = datetime.date.today()
        cur.execute("SELECT MAX(ID) FROM Study_Materials")
        max_id = (cur.fetchone()[0] or 0) + 1
        code = f"MAT-{max_id:03d}"

        cur.execute("""
            INSERT INTO Study_Materials 
            (MATERIAL_CODE, TITLE, SUBJECT, CLASS, TOPIC, RESOURCE_TYPE, RESOURCE_URL, CONTENT_TEXT, UPLOADED_BY, UPLOAD_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (code, title, subject, cls, topic, res_type, url, notes, uploader, today))
        con.commit()

        print(f"\nStudy Material '{title}' ({code}) uploaded successfully!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- 3. SUBMISSIONS & GRADING ---------------------------------

def view_submissions_and_grade():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)

        cur.execute("""
            SELECT s.*, a.TITLE AS ASSIGNMENT_TITLE, a.MAX_MARKS
            FROM Assignment_Submissions s
            JOIN Assignments a ON s.ASSIGNMENT_CODE = a.ASSIGNMENT_CODE
            ORDER BY s.ID DESC
        """)
        rows = cur.fetchall()

        if not rows:
            print("No student assignment submissions found.")
            return

        table_data = []
        for r in rows:
            marks_display = f"{r['MARKS_OBTAINED']:.1f}/{r['MAX_MARKS']} ({r['GRADE']})" if r['MARKS_OBTAINED'] is not None else "Pending"
            table_data.append([
                r['ID'],
                r['SUBMISSION_CODE'],
                r['ASSIGNMENT_TITLE'][:22],
                r['STUDENT_NAME'],
                r['STUDENT_ROLL'],
                r['SUBMITTED_DATE'].strftime('%Y-%m-%d'),
                r['STATUS'],
                marks_display,
                r['TEACHER_FEEDBACK'][:20] if r['TEACHER_FEEDBACK'] else '-'
            ])
        print(tabulate(
            table_data,
            headers=["#", "CODE", "ASSIGNMENT", "STUDENT", "ROLL", "SUBMITTED", "STATUS", "GRADE/MARKS", "FEEDBACK"],
            tablefmt="fancy_grid"
        ))

        sub_id = input("\nEnter Submission # to Grade / Review (or 0 to cancel) : : ").strip()
        if sub_id == "0" or not sub_id:
            return

        cur.execute("""
            SELECT s.*, a.TITLE AS ASSIGNMENT_TITLE, a.MAX_MARKS
            FROM Assignment_Submissions s
            JOIN Assignments a ON s.ASSIGNMENT_CODE = a.ASSIGNMENT_CODE
            WHERE s.ID = %s
        """, (sub_id,))
        sub = cur.fetchone()
        if not sub:
            print("Invalid submission record ID.")
            return

        print("\n" + "="*70)
        print("STUDENT SUBMISSION DETAILS".center(70))
        print("="*70)
        print(f"Assignment : {sub['ASSIGNMENT_TITLE']} (Max: {sub['MAX_MARKS']} marks)")
        print(f"Student    : {sub['STUDENT_NAME']} (Roll No: {sub['STUDENT_ROLL']})")
        print(f"Submitted  : {sub['SUBMITTED_DATE']} - Status: {sub['STATUS']}")
        print(f"Work Text  : {sub['SUBMISSION_TEXT']}")
        if sub['FILE_URL']:
            print(f"Work Link  : {sub['FILE_URL']}")
        print("="*70)

        try:
            marks = float(input(f"Enter Marks Awarded (out of {sub['MAX_MARKS']}) : : "))
            if marks < 0 or marks > sub['MAX_MARKS']:
                print(f"Marks must be between 0 and {sub['MAX_MARKS']}!")
                return
        except ValueError:
            print("Invalid numeric marks entry!")
            return

        pct = (marks / sub['MAX_MARKS']) * 100
        if pct >= 90:
            grade = "A+"
        elif pct >= 80:
            grade = "A"
        elif pct >= 70:
            grade = "B"
        elif pct >= 60:
            grade = "C"
        elif pct >= 40:
            grade = "Pass"
        else:
            grade = "Fail"

        feedback = input("Enter Teacher Feedback / Constructive Comments : : ").strip() or "Reviewed and graded."
        reviewer = input("Teacher Name : : ").strip() or "Faculty"

        today = datetime.date.today()
        cur.execute("""
            UPDATE Assignment_Submissions 
            SET MARKS_OBTAINED = %s,
                GRADE = %s,
                TEACHER_FEEDBACK = %s,
                REVIEWED_BY = %s,
                REVIEWED_DATE = %s,
                STATUS = 'Graded'
            WHERE ID = %s
        """, (marks, grade, feedback, reviewer, today, sub_id))
        con.commit()

        print(f"\nSubmission graded successfully! Grade: {grade} ({marks}/{sub['MAX_MARKS']})")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- 4. LEARNING COURSES ---------------------------------

def view_learning_courses():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Learning_Courses ORDER BY ID ASC")
        rows = cur.fetchall()

        if rows:
            table_data = []
            for r in rows:
                table_data.append([
                    r['COURSE_CODE'],
                    r['TITLE'],
                    r['SUBJECT'],
                    r['INSTRUCTOR'],
                    r['LEVEL'],
                    f"{r['TOTAL_LESSONS']} lessons",
                    f"{r['DURATION_WEEKS']} weeks",
                    r['STATUS']
                ])
            print(tabulate(
                table_data,
                headers=["CODE", "COURSE TITLE", "SUBJECT", "INSTRUCTOR", "LEVEL", "LESSONS", "DURATION", "STATUS"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No learning courses currently published.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- 5. INTERACTIVE ONLINE QUIZZES ---------------------------------

def run_interactive_quiz():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)

        cur.execute("SELECT * FROM Online_Quizzes WHERE STATUS = 'Active' ORDER BY ID ASC")
        quizzes = cur.fetchall()

        if not quizzes:
            print("No active quizzes available.")
            return

        print("\n" + "="*70)
        print("AVAILABLE ONLINE QUIZZES".center(70))
        print("="*70)
        for idx, q in enumerate(quizzes, 1):
            print(f"{idx}. [{q['QUIZ_CODE']}] {q['TITLE']} ({q['SUBJECT']} - {q['CLASS']})")
            print(f"   Time: {q['TIME_MINUTES']} mins | Total Questions: {q['TOTAL_QUESTIONS']} | Pass Mark: {q['PASS_PERCENTAGE']}%")
        print("="*70)

        choice = input("\nSelect Quiz number to take (or 0 to cancel) : : ").strip()
        if choice == "0" or not choice:
            return

        try:
            sel_idx = int(choice) - 1
            selected_quiz = quizzes[sel_idx]
        except (ValueError, IndexError):
            print("Invalid quiz selection!")
            return

        student_name = input("Enter Student Full Name : : ").strip()
        student_roll = input("Enter Student Roll Number : : ").strip()
        if not student_name or not student_roll:
            print("Student details required to attempt quiz!")
            return

        # Fetch questions
        cur.execute("""
            SELECT * FROM Quiz_Questions 
            WHERE QUIZ_CODE = %s 
            ORDER BY QUESTION_NUMBER ASC
        """, (selected_quiz['QUIZ_CODE'],))
        questions = cur.fetchall()

        if not questions:
            print("No questions configured for this quiz.")
            return

        clear_screen()
        print("\n" + "="*70)
        print(f"QUIZ: {selected_quiz['TITLE']}".center(70))
        print(f"Candidate: {student_name} (Roll: {student_roll}) | Total Questions: {len(questions)}".center(70))
        print("="*70 + "\n")

        score = 0
        answers_review = []

        for q in questions:
            print(f"\nQuestion {q['QUESTION_NUMBER']}: {q['QUESTION_TEXT']}")
            print(f"  [A] {q['OPTION_A']}")
            print(f"  [B] {q['OPTION_B']}")
            print(f"  [C] {q['OPTION_C']}")
            print(f"  [D] {q['OPTION_D']}")

            ans = input("Your Answer (A / B / C / D) : : ").strip().upper()
            is_correct = (ans == q['CORRECT_OPTION'])
            if is_correct:
                score += 1
            answers_review.append({
                "num": q['QUESTION_NUMBER'],
                "text": q['QUESTION_TEXT'],
                "chosen": ans,
                "correct": q['CORRECT_OPTION'],
                "is_correct": is_correct,
                "explanation": q.get('EXPLANATION') or ''
            })

        total_q = len(questions)
        percentage = (score / total_q) * 100
        passed = (percentage >= selected_quiz['PASS_PERCENTAGE'])

        # Record attempt in database
        today = datetime.date.today()
        cur.execute("SELECT MAX(ID) FROM Quiz_Attempts")
        att_num = (cur.fetchone()['MAX(ID)'] or 0) + 1
        att_code = f"ATT-{today.year}-{att_num:04d}"

        cur.execute("""
            INSERT INTO Quiz_Attempts 
            (ATTEMPT_CODE, QUIZ_CODE, STUDENT_ROLL, STUDENT_NAME, SCORE, TOTAL_QUESTIONS, PERCENTAGE, PASSED, ATTEMPT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (att_code, selected_quiz['QUIZ_CODE'], student_roll, student_name, score, total_q, percentage, passed, today))
        con.commit()

        # Display Result
        print("\n" + "="*70)
        print("QUIZ RESULT & ASSESSMENT REPORT".center(70))
        print("="*70)
        print(f"Attempt ID : {att_code}")
        print(f"Student    : {student_name} ({student_roll})")
        print(f"Score      : {score} out of {total_q} ({percentage:.1f}%)")
        status_banner = "PASSED (CONGRATULATIONS!)" if passed else "NEEDS IMPROVEMENT (BELOW PASS MARK)"
        print(f"Status     : {status_banner}")
        print("="*70)

        print("\nDETAILED QUESTION REVIEW:")
        for r in answers_review:
            symbol = "✓ CORRECT" if r['is_correct'] else f"✗ WRONG (Correct: [{r['correct']}])"
            print(f"Q{r['num']}: {r['text'][:55]}... -> Your answer: [{r['chosen']}] | {symbol}")
            if r['explanation']:
                print(f"     Explanation: {r['explanation']}")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- MAIN MENU ---------------------------------

def coursework_menu():
    create_coursework_tables()
    while True:
        clear_screen()
        print("\nACADEMICS, ASSIGNMENTS & E-LEARNING SYSTEM".center(100))
        print("=" * 100)
        print("1. View Active Assignments".center(100))
        print("2. Publish New Assignment (Teachers)".center(100))
        print("3. View Study Materials & Lecture Notes".center(100))
        print("4. Upload Study Material (Teachers)".center(100))
        print("5. Review & Grade Student Submissions".center(100))
        print("6. Browse Learning Courses Catalogue".center(100))
        print("7. Take Interactive Online Quiz (Students)".center(100))
        print("0. Back to Main Menu".center(100))
        print("=" * 100)

        choice = input("\nEnter choice : : ").strip()
        if choice == "1":
            view_assignments()
        elif choice == "2":
            add_assignment()
        elif choice == "3":
            view_study_materials()
        elif choice == "4":
            add_study_material()
        elif choice == "5":
            view_submissions_and_grade()
        elif choice == "6":
            view_learning_courses()
        elif choice == "7":
            run_interactive_quiz()
        elif choice == "0":
            break
        else:
            print("Invalid choice, please try again.")
        pause_and_clear()
