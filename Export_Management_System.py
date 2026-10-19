# --------------------------------- IMPORT COMMANDS ---------------------------------

import os
import csv
import datetime
import mysql.connector as ms
from mysql.connector import Error

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear
)

EXPORT_DIR = "exports"

# --------------------------------- HELPER FUNCTIONS ---------------------------------

def get_export_filepath(prefix):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.csv"
    return os.path.join(EXPORT_DIR, filename)

def save_to_csv(filepath, headers, rows):
    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        print("\n" + "=" * 60)
        print(f"✅ EXPORT SUCCESSFUL!")
        print(f"File saved at: {os.path.abspath(filepath)}")
        print("You can open this file directly in Microsoft Excel.")
        print("=" * 60)
    except Exception as e:
        print("File Writing Error:", e)

# --------------------------------- EXPORT MODULES -----------------------------------

def export_students():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        print("\nExport Options:")
        print("1. Export All Students")
        print("2. Export Students by Specific Class")
        opt = input("Enter choice (1/2) [Default=1]: ").strip()

        if opt == "2":
            s_class = input("Enter Class name (e.g. 10, 12-A): ").strip()
            cur.execute("""
                SELECT ID, ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER 
                FROM Students_Details WHERE CLASS=%s ORDER BY ROLL_NUMBER
            """, (s_class,))
            prefix = f"students_class_{s_class}"
        else:
            cur.execute("""
                SELECT ID, ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER 
                FROM Students_Details ORDER BY CLASS, ROLL_NUMBER
            """)
            prefix = "students_all"

        rows = cur.fetchall()
        if not rows:
            print("No student records found to export.")
            return

        headers = ["ID", "Roll Number", "Name", "Class", "Age", "Address", "Phone", "Email", "Gender"]
        filepath = get_export_filepath(prefix)
        save_to_csv(filepath, headers, rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_teachers():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        cur.execute("""
            SELECT ID, TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER 
            FROM Teachers_Details ORDER BY NAME
        """)
        rows = cur.fetchall()

        if not rows:
            print("No teacher records found to export.")
            return

        headers = ["ID", "Teacher ID", "Name", "Subject", "Age", "Address", "Phone", "Email", "Gender"]
        filepath = get_export_filepath("teachers_directory")
        save_to_csv(filepath, headers, rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_library_books():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        cur.execute("""
            SELECT ID, BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES 
            FROM Books_Details ORDER BY BOOK_ID
        """)
        rows = cur.fetchall()

        if not rows:
            print("No book records found to export.")
            return

        headers = ["ID", "Book ID", "Title", "Author", "Genre", "Total Copies", "Available Copies"]
        filepath = get_export_filepath("library_inventory")
        save_to_csv(filepath, headers, rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_fee_defaulters():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY CLASS, ROLL_NUMBER")
        students = cur.fetchall()

        defaulter_rows = []
        for roll, name, s_class in students:
            # Get class fee
            cur.execute("SELECT ANNUAL_FEE FROM Fee_Structure WHERE CLASS=%s", (s_class,))
            fee_res = cur.fetchone()
            total_fee = float(fee_res[0]) if fee_res else 45000.0

            # Get paid fee
            cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) FROM Fee_Transactions WHERE ROLL_NUMBER=%s", (roll,))
            paid_fee = float(cur.fetchone()[0])
            balance_due = max(0.0, total_fee - paid_fee)

            if balance_due > 0:
                defaulter_rows.append([roll, name, s_class, f"{total_fee:.2f}", f"{paid_fee:.2f}", f"{balance_due:.2f}"])

        if not defaulter_rows:
            print("No fee defaulters found! All students have cleared dues.")
            return

        headers = ["Roll Number", "Name", "Class", "Total Annual Fee (INR)", "Amount Paid (INR)", "Pending Due (INR)"]
        filepath = get_export_filepath("fee_defaulters_list")
        save_to_csv(filepath, headers, defaulter_rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_attendance():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        today = datetime.date.today().strftime('%Y-%m-%d')
        date_input = input(f"Enter Attendance Date (YYYY-MM-DD) [Default={today}]: ").strip()
        att_date = date_input if date_input else today

        cur.execute("""
            SELECT a.ATTENDANCE_DATE, a.ROLL_NUMBER, s.NAME, s.CLASS, a.STATUS, IFNULL(a.REMARKS, '-')
            FROM Attendance_Details a
            JOIN Students_Details s ON a.ROLL_NUMBER = s.ROLL_NUMBER
            WHERE a.ATTENDANCE_DATE = %s
            ORDER BY s.CLASS, a.ROLL_NUMBER
        """, (att_date,))
        rows = cur.fetchall()

        if not rows:
            print(f"No attendance records found for {att_date}.")
            return

        headers = ["Date", "Roll Number", "Name", "Class", "Status", "Remarks"]
        filepath = get_export_filepath(f"attendance_{att_date}")
        save_to_csv(filepath, headers, rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_exam_merit_list():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        class_name = input("Enter Class (e.g. 10, 12-A): ").strip()
        exam_type = input("Enter Exam Name (e.g. Final Exam, Mid-Term Exam) [Default=Final Exam]: ").strip()
        if not exam_type:
            exam_type = "Final Exam"

        cur.execute("""
            SELECT s.ROLL_NUMBER, s.NAME, 
                   SUM(m.MARKS_OBTAINED) as TOTAL_OBT, 
                   SUM(m.MAX_MARKS) as TOTAL_MAX
            FROM Students_Details s
            JOIN Marks_Details m ON s.ROLL_NUMBER = m.ROLL_NUMBER
            WHERE s.CLASS=%s AND m.EXAM_TYPE=%s
            GROUP BY s.ROLL_NUMBER, s.NAME
        """, (class_name, exam_type))
        rows = cur.fetchall()

        if not rows:
            print(f"No marks found for Class '{class_name}' in '{exam_type}'.")
            return

        merit_data = []
        for roll, name, obt, max_m in rows:
            pct = (float(obt) / float(max_m)) * 100 if float(max_m) > 0 else 0.0
            grade = "A+" if pct >= 90 else ("A" if pct >= 80 else ("B+" if pct >= 70 else ("B" if pct >= 60 else ("C" if pct >= 50 else ("D" if pct >= 40 else "F")))))
            merit_data.append({
                "roll": roll,
                "name": name,
                "obtained": float(obt),
                "max": float(max_m),
                "pct": pct,
                "grade": grade
            })

        merit_data.sort(key=lambda x: x["pct"], reverse=True)

        export_rows = []
        for rank, item in enumerate(merit_data, start=1):
            export_rows.append([
                rank,
                item["roll"],
                item["name"],
                class_name,
                exam_type,
                f"{item['obtained']:.2f}",
                f"{item['max']:.2f}",
                f"{item['pct']:.2f}%",
                item["grade"]
            ])

        headers = ["Rank", "Roll Number", "Name", "Class", "Exam Type", "Marks Obtained", "Total Max Marks", "Percentage", "Grade"]
        filepath = get_export_filepath(f"merit_list_class_{class_name}")
        save_to_csv(filepath, headers, export_rows)

    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def export_all_tables():
    print("\n--- Starting Full School Database Export to CSV ---")
    export_students()
    export_teachers()
    export_library_books()
    export_fee_defaulters()
    print("\n🎉 Full database backup completed! All files saved in the 'exports/' folder.")

# --------------------------------- MAIN MENU ---------------------------------

def export_menu():
    while True:
        clear_screen()
        print("\nDATA EXPORT TO CSV / EXCEL".center(100))
        print("-" * 100)
        print("1. Export Students List (All or by Class)".center(100))
        print("2. Export Teachers Directory".center(100))
        print("3. Export Library Books Inventory".center(100))
        print("4. Export Fee Defaulters List".center(100))
        print("5. Export Daily Attendance by Date".center(100))
        print("6. Export Class Exam Merit List".center(100))
        print("7. Export ALL Tables (Complete School Export)".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            export_students()
        elif choice == "2":
            export_teachers()
        elif choice == "3":
            export_library_books()
        elif choice == "4":
            export_fee_defaulters()
        elif choice == "5":
            export_attendance()
        elif choice == "6":
            export_exam_merit_list()
        elif choice == "7":
            export_all_tables()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()
