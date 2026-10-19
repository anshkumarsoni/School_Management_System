# --------------------------------- IMPORT COMMANDS ---------------------------------

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

def create_attendance_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Attendance_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                ATTENDANCE_DATE DATE NOT NULL,
                STATUS ENUM('Present', 'Absent', 'Leave') NOT NULL,
                REMARKS VARCHAR(100),
                UNIQUE KEY unique_student_date (ROLL_NUMBER, ATTENDANCE_DATE)
            )
        """)
        con.commit()
    except Error as e:
        print("Table Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- HELPER FUNCTIONS ---------------------------------

def get_input_date():
    today = datetime.date.today().strftime('%Y-%m-%d')
    date_input = input(f"Enter Date (YYYY-MM-DD) [Press Enter for Today: {today}]: ").strip()
    if not date_input:
        return today
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d')
        return date_input
    except ValueError:
        print("Invalid date format! Use YYYY-MM-DD.")
        return None

def parse_status(choice):
    choice = choice.upper()
    if choice in ('P', 'PRESENT'):
        return 'Present'
    elif choice in ('A', 'ABSENT'):
        return 'Absent'
    elif choice in ('L', 'LEAVE'):
        return 'Leave'
    return None

# --------------------------------- ATTENDANCE OPERATIONS ----------------------------

def mark_single_attendance():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()
        
        roll = input("Enter Student Roll Number : : ").strip()
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER=%s", (roll,))
        student = cur.fetchone()
        if not student:
            print("Student not found in Students_Details!")
            return
        
        name, student_class = student
        print(f"Student: {name} | Class: {student_class}")
        
        att_date = get_input_date()
        if not att_date:
            return

        status_input = input("Enter Status (P for Present / A for Absent / L for Leave) : : ").strip()
        status = parse_status(status_input)
        if not status:
            print("Invalid status! Choose P, A, or L.")
            return

        remarks = input("Remarks (optional) : : ").strip()

        # Insert or update if already marked on that date
        cur.execute("""
            INSERT INTO Attendance_Details (ROLL_NUMBER, ATTENDANCE_DATE, STATUS, REMARKS)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE STATUS=%s, REMARKS=%s
        """, (roll, att_date, status, remarks, status, remarks))
        con.commit()
        print(f"\nAttendance marked as '{status}' for {name} on {att_date}!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def mark_class_attendance():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        class_name = input("Enter Class Name (e.g. 10, 12-A) : : ").strip()
        cur.execute("SELECT ROLL_NUMBER, NAME FROM Students_Details WHERE CLASS=%s ORDER BY ROLL_NUMBER ASC", (class_name,))
        students = cur.fetchall()

        if not students:
            print(f"No students found in Class '{class_name}'.")
            return

        att_date = get_input_date()
        if not att_date:
            return

        print(f"\nMarking Attendance for Class '{class_name}' ({len(students)} students) on {att_date}:")
        print("Quick options: [P] Present (Default) | [A] Absent | [L] Leave")
        print("-" * 70)

        for roll, name in students:
            val = input(f"Roll: {roll:<10} Name: {name:<25} [P/A/L] (Enter=P): ").strip()
            if not val:
                status = 'Present'
            else:
                status = parse_status(val)
                if not status:
                    print("  Invalid entry, recorded as Present.")
                    status = 'Present'

            cur.execute("""
                INSERT INTO Attendance_Details (ROLL_NUMBER, ATTENDANCE_DATE, STATUS)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE STATUS=%s
            """, (roll, att_date, status, status))

        con.commit()
        print("\nAll class attendance saved successfully!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_attendance_by_date():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        att_date = get_input_date()
        if not att_date:
            return

        cur.execute("""
            SELECT a.ROLL_NUMBER, s.NAME, s.CLASS, a.STATUS, IFNULL(a.REMARKS, '-')
            FROM Attendance_Details a
            JOIN Students_Details s ON a.ROLL_NUMBER = s.ROLL_NUMBER
            WHERE a.ATTENDANCE_DATE = %s
            ORDER BY s.CLASS, a.ROLL_NUMBER
        """, (att_date,))
        rows = cur.fetchall()

        if rows:
            print(f"\nAttendance Record for {att_date}:")
            print(tabulate(
                rows,
                headers=["ROLL", "NAME", "CLASS", "STATUS", "REMARKS"],
                tablefmt="fancy_grid"
            ))
        else:
            print(f"No attendance records found for {att_date}.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_student_summary():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER=%s", (roll,))
        student = cur.fetchone()
        if not student:
            print("Student not found!")
            return

        name, student_class = student

        cur.execute("SELECT STATUS, COUNT(*) FROM Attendance_Details WHERE ROLL_NUMBER=%s GROUP BY STATUS", (roll,))
        records = dict(cur.fetchall())

        present = records.get('Present', 0)
        absent = records.get('Absent', 0)
        leave = records.get('Leave', 0)
        total_days = present + absent + leave

        if total_days == 0:
            print(f"No attendance has been recorded yet for {name}.")
            return

        percentage = (present / total_days) * 100

        summary = [
            ["Student Name", name],
            ["Roll Number", roll],
            ["Class", student_class],
            ["Total Working Days", total_days],
            ["Days Present", present],
            ["Days Absent", absent],
            ["Days on Leave", leave],
            ["Attendance %", f"{percentage:.2f}%"]
        ]

        print("\n" + "=" * 50)
        print("STUDENT ATTENDANCE REPORT".center(50))
        print("=" * 50)
        print(tabulate(summary, tablefmt="fancy_grid"))

        if percentage < 75.0:
            print("\n⚠️  WARNING: Attendance is below 75%! Defaulter notice applicable.")
        else:
            print("\n✅ Attendance status: Good standing.")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def update_attendance_record():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        att_date = get_input_date()
        if not att_date:
            return

        cur.execute("SELECT STATUS FROM Attendance_Details WHERE ROLL_NUMBER=%s AND ATTENDANCE_DATE=%s", (roll, att_date))
        curr = cur.fetchone()
        if not curr:
            print(f"No attendance record found for Roll {roll} on {att_date}.")
            return

        print(f"Current Status: {curr[0]}")
        status_input = input("Enter New Status (P for Present / A for Absent / L for Leave) : : ").strip()
        new_status = parse_status(status_input)
        if not new_status:
            print("Invalid status!")
            return

        new_remarks = input("New Remarks (optional) : : ").strip()

        cur.execute("""
            UPDATE Attendance_Details 
            SET STATUS=%s, REMARKS=%s 
            WHERE ROLL_NUMBER=%s AND ATTENDANCE_DATE=%s
        """, (new_status, new_remarks, roll, att_date))
        con.commit()
        print("Attendance updated successfully!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- MAIN MENU ---------------------------------

def attendance_menu():
    while True:
        clear_screen()
        print("\nATTENDANCE MANAGEMENT".center(100))
        print("-" * 100)
        print("1. Mark Single Student Attendance".center(100))
        print("2. Mark Class Attendance (Quick Batch)".center(100))
        print("3. View Daily Attendance by Date".center(100))
        print("4. Student Attendance Report & % Summary".center(100))
        print("5. Update Attendance Record".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            mark_single_attendance()
        elif choice == "2":
            mark_class_attendance()
        elif choice == "3":
            view_attendance_by_date()
        elif choice == "4":
            view_student_summary()
        elif choice == "5":
            update_attendance_record()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()
