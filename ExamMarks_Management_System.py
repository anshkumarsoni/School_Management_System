# --------------------------------- IMPORT COMMANDS ---------------------------------

import mysql.connector as ms
import matplotlib.pyplot as plt
from mysql.connector import Error
from tabulate import tabulate
from utils import get_connection

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear,
    center_text
)

# --------------------------------- TABLE CREATION ---------------------------------

def create_exam_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
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
        con.commit()
    except Error as e:
        print("Table Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- GRADING UTILITIES -------------------------------

def calculate_grade(percentage):
    if percentage >= 90:
        return "A+", "Outstanding"
    elif percentage >= 80:
        return "A", "Excellent"
    elif percentage >= 70:
        return "B+", "Very Good"
    elif percentage >= 60:
        return "B", "Good"
    elif percentage >= 50:
        return "C", "Average"
    elif percentage >= 40:
        return "D", "Pass"
    else:
        return "F", "Fail"

def select_exam_type():
    print("\nSelect Exam Type:")
    print("1. Unit Test 1")
    print("2. Mid-Term Exam")
    print("3. Unit Test 2")
    print("4. Final / Annual Exam")
    print("5. Custom Name")
    choice = input("Enter choice (1-5) [Default=Final]: ").strip()
    exams = {
        "1": "Unit Test 1",
        "2": "Mid-Term Exam",
        "3": "Unit Test 2",
        "4": "Final Exam"
    }
    if choice in exams:
        return exams[choice]
    elif choice == "5":
        custom = input("Enter Custom Exam Name : : ").strip()
        return custom if custom else "Final Exam"
    return "Final Exam"

# --------------------------------- OPERATIONS --------------------------------------

def enter_marks():
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
        print(f"\nEntering Marks for: {name} | Class: {student_class}")

        exam_type = select_exam_type()

        try:
            num_subjects = int(input("\nHow many subjects do you want to enter marks for? : : "))
            if num_subjects <= 0:
                print("Must enter at least 1 subject!")
                return
        except ValueError:
            print("Invalid number!")
            return

        for i in range(1, num_subjects + 1):
            print(f"\n--- Subject #{i} ---")
            subject = input("Subject Name (e.g. Mathematics, English, Science) : : ").strip()
            if not subject:
                print("Subject name cannot be empty. Skipping...")
                continue

            try:
                max_marks = float(input("Max Marks [Default=100] : : ") or 100)
                marks_obtained = float(input(f"Marks Obtained (out of {max_marks}) : : "))
                if marks_obtained < 0 or marks_obtained > max_marks:
                    print("Marks obtained cannot be negative or exceed Max Marks! Skipping...")
                    continue
            except ValueError:
                print("Invalid numeric marks! Skipping...")
                continue

            cur.execute("""
                INSERT INTO Marks_Details (ROLL_NUMBER, EXAM_TYPE, SUBJECT, MARKS_OBTAINED, MAX_MARKS)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE MARKS_OBTAINED=%s, MAX_MARKS=%s
            """, (roll, exam_type, subject, marks_obtained, max_marks, marks_obtained, max_marks))

        con.commit()
        print(f"\nAll marks successfully saved for {name} ({exam_type})!")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def generate_report_card():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        cur.execute("SELECT NAME, CLASS, GENDER FROM Students_Details WHERE ROLL_NUMBER=%s", (roll,))
        student = cur.fetchone()
        if not student:
            print("Student not found!")
            return

        name, student_class, gender = student
        exam_type = select_exam_type()

        cur.execute("""
            SELECT SUBJECT, MARKS_OBTAINED, MAX_MARKS
            FROM Marks_Details
            WHERE ROLL_NUMBER=%s AND EXAM_TYPE=%s
            ORDER BY SUBJECT
        """, (roll, exam_type))
        rows = cur.fetchall()

        if not rows:
            print(f"\nNo marks records found for {name} for '{exam_type}'.")
            return

        total_obtained = sum(float(r[1]) for r in rows)
        total_max = sum(float(r[2]) for r in rows)
        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0.0
        grade, remark = calculate_grade(percentage)
        result_status = "PASSED" if percentage >= 40 else "FAILED"

        subject_table = []
        for sub, obt, max_m in rows:
            sub_pct = (float(obt) / float(max_m)) * 100
            sub_grade, _ = calculate_grade(sub_pct)
            subject_table.append([sub, f"{float(obt):.2f}", f"{float(max_m):.2f}", f"{sub_pct:.1f}%", sub_grade])

        clear_screen()
        print("=" * 65)
        print("ACADEMIC REPORT CARD".center(65))
        print("=" * 65)
        print(f" Student Name : {name:<25} Roll Number : {roll}")
        print(f" Class        : {student_class:<25} Exam        : {exam_type}")
        print("-" * 65)
        print(tabulate(subject_table, headers=["Subject", "Marks", "Max", "Percentage", "Grade"], tablefmt="fancy_grid"))
        print("-" * 65)
        print(f" Total Marks : {total_obtained:.2f} / {total_max:.2f}")
        print(f" Overall %   : {percentage:.2f}%")
        print(f" Final Grade : {grade} ({remark})")
        print(f" Result      : {result_status}")
        print("=" * 65)

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_class_merit_list():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        class_name = input("Enter Class (e.g. 10, 12-A) : : ").strip()
        exam_type = select_exam_type()

        cur.execute("""
            SELECT s.ROLL_NUMBER, s.NAME, 
                   SUM(m.MARKS_OBTAINED) as TOTAL_OBTAINED, 
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
            pct = (float(obt) / float(max_m)) * 100 if float(max_m) > 0 else 0
            grade, _ = calculate_grade(pct)
            merit_data.append({
                "roll": roll,
                "name": name,
                "total": f"{float(obt):.1f}/{float(max_m):.1f}",
                "pct": pct,
                "grade": grade
            })

        merit_data.sort(key=lambda x: x["pct"], reverse=True)

        final_table = []
        for rank, item in enumerate(merit_data, start=1):
            badge = "🏆 Rank 1" if rank == 1 else ("🥈 Rank 2" if rank == 2 else ("🥉 Rank 3" if rank == 3 else f"Rank {rank}"))
            final_table.append([
                badge,
                item["roll"],
                item["name"],
                item["total"],
                f"{item['pct']:.2f}%",
                item["grade"]
            ])

        print("\n" + "=" * 75)
        print(f"CLASS {class_name} MERIT & RANK LIST - {exam_type}".center(75))
        print("=" * 75)
        print(tabulate(final_table, headers=["Rank", "Roll", "Name", "Total Marks", "Percentage", "Grade"], tablefmt="fancy_grid"))

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def update_marks():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        exam_type = select_exam_type()
        subject = input("Enter Subject Name to update : : ").strip()

        cur.execute("""
            SELECT MARKS_OBTAINED, MAX_MARKS 
            FROM Marks_Details 
            WHERE ROLL_NUMBER=%s AND EXAM_TYPE=%s AND SUBJECT=%s
        """, (roll, exam_type, subject))
        record = cur.fetchone()

        if not record:
            print("No matching record found to update!")
            return

        print(f"Current Marks: {record[0]} / {record[1]}")
        try:
            new_marks = float(input(f"Enter New Marks (out of {record[1]}) : : "))
            if new_marks < 0 or new_marks > float(record[1]):
                print("Invalid marks range!")
                return
        except ValueError:
            print("Must be a number!")
            return

        cur.execute("""
            UPDATE Marks_Details 
            SET MARKS_OBTAINED=%s 
            WHERE ROLL_NUMBER=%s AND EXAM_TYPE=%s AND SUBJECT=%s
        """, (new_marks, roll, exam_type, subject))
        con.commit()
        print("Marks updated successfully!")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def delete_marks_record():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        exam_type = select_exam_type()

        confirm = input(f"Are you sure you want to delete all marks of Roll {roll} for '{exam_type}'? (y/n) : : ").lower()
        if confirm != 'y':
            print("Deletion cancelled.")
            return

        cur.execute("DELETE FROM Marks_Details WHERE ROLL_NUMBER=%s AND EXAM_TYPE=%s", (roll, exam_type))
        con.commit()
        if cur.rowcount > 0:
            print(f"Deleted {cur.rowcount} subject mark entries successfully!")
        else:
            print("No records found to delete.")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# ------------------------- Graphical Representation -------------------------

def plot_student_subject_marks():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection falied.")
            return
        cur = con.cursor()
        roll = input("Eneter Student roll numberr : : ").strip()
        cur.execute("SELECT NAME,CLASS FROM Students_Details WHERE ROLL_NUMBER = %s",(roll,))
        student = cur.fetchone()
        if not student:
            print("Student not found !")
            return
        name, student_class = student

        exam_type = input("Enter Exam Name (e.g. Final Exam, Mid-Term Exam)[Default=Final Exam] : : ").strip()
        if not exam_type:
            exam_type = "Final Exam"

        cur.execute("""SELECT SUBJECT, MARKS_OBTAINED, MAX_MARKS FROM Marks_Details WHERE ROLL_NUMBER = %s AND EXAM_TYPE = %s ORDER BY SUBJECT""", (roll, exam_type)) 
        rows = cur.fetchall()
        if not rows:
            print(f"No marks records found for {name ({roll})} in '{exam_type}'.")
            return
        subjects = [r[0] for r in rows]
        marks_obtained = [float(r[1]) for r in rows]
        max_marks = [float(r[2]) for r in rows]

        colours = []
        for marks, max_m in zip(marks_obtained, max_marks):
            percentage = (marks/max_m) * 100 if max_m > 0 else 0
            if percentage >= 75:
                print("#2ecc71")
            elif percentage >= 40:
                print("#f39c12")
            else:
                colours.append("#e74c3c")

        plt.figure(figsize=(9,6))
        bars = plt.bar(subjects, marks_obtained, colour=colours, width=0.5, edgecolor = 'black', linewidth = 1.2)
        plt.axhline(y=40, color = "red", linestyle = "--", linewidth = 1.5, lable = "Passing Marks (40%)")
        for bar, marks, max_m in zip(bars, marks_obtained, max_marks):
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.0,
                height + 1.5,
                f"{marks:.1f}/{max_m:.0f}",
                ha = "center",
                va = "bottom",
                fontweight = "bold",
                fontsize = 10
            )

            plt.tittle(f"Academic Performance: {name}(Roll:{roll})\nClass:{student_class} | Exam: {exam_type},fontsize = 13", frontweight = "bold", pad = 15)
            plt.xlable("Subjects", fontsize = 11,fontweigth = "bold")
            plt.ylable("Marks Obtained", fontsize = 11, fontweigth = "bold")
            plt.ylim(0, max(max_marks) + 15 if max_marks else 115)
            plt.grid(axis="y", linestyle=":", alpha=0.6)
            plt.legend(loc="upper right")
            plt.tight_layout()
            print("\nOpening bar chart window... (Close the chart window to return)")
            plt.show()
    except Exception as e:
        print("Chart Generation Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- MAIN MENU ---------------------------------

def exam_menu():
    while True:
        clear_screen()
        print("\nEXAMINATION & MARKS MANAGEMENT".center(100))
        print("-" * 100)
        print("1. Enter Student Marks".center(100))
        print("2. Generate Student Report Card / Marksheet".center(100))
        print("3. View Class Performance & Merit List".center(100))
        print("4. Update / Rectify Marks".center(100))
        print("5. Delete Marks Record".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            enter_marks()
        elif choice == "2":
            generate_report_card()
        elif choice == "3":
            view_class_merit_list()
        elif choice == "4":
            update_marks()
        elif choice == "5":
            delete_marks_record()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()