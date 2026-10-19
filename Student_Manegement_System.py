# --------------------------------- IMPORT COMMANDS ---------------------------------

import mysql.connector as ms
from mysql.connector import Error
from tabulate import tabulate

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear,
    valid_email,
    valid_phonenumber
)

#----------------------------------- TABLE CREATION FUNCTION ----------------------

def create_student_table():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Students_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) UNIQUE NOT NULL,
                NAME VARCHAR(100) NOT NULL,
                CLASS VARCHAR(20),
                AGE INT,
                ADDRESS VARCHAR(255),
                PHONE VARCHAR(15),
                EMAIL VARCHAR(100),
                GENDER ENUM("Male","Female","Other")
            )
        """)
        con.commit()
    except Error as e:
        print("Table Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# -------------------------------- CRUD FUNCTIONS -----------------------------------

def add_student():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()
        ROLL_NUMBER = input("Enter roll number : : ").strip()
        if not ROLL_NUMBER.isdigit():
            print("Roll number must be numeric only !")
            return
        cur.execute("SELECT 1 FROM Students_Details WHERE ROLL_NUMBER=%s", (ROLL_NUMBER,))
        if cur.fetchone():
            print("Roll number already exists !")
            return
        NAME = input("Enter name  : : ").strip()
        if not NAME:
            print("Name cannot be empty !")
            return
        CLASS_NAME = input("Enter class  : : ")
        try:
            AGE = int(input("Enter age  : : "))
            if AGE <= 0 or AGE > 120:
                print("Invalid age !")
                return
        except ValueError:
            print("Age must be a number !")
            return
        PHONE = input("Enter phone number : : ").strip()
        if not valid_phonenumber(PHONE):
            return
        EMAIL = input("Enter email : : ").strip()
        if not valid_email(EMAIL):
            return
        GENDER = input("Gender (Male/Female/Other) : : ").strip()
        if GENDER not in ("Male", "Female", "Other"):
            print("Invalid gender !")
            return
        ADDRESS = input("Enter address  : : ")
        cur.execute("""
            INSERT INTO Students_Details
            (ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ROLL_NUMBER, NAME, CLASS_NAME, AGE, ADDRESS, PHONE, EMAIL, GENDER))
        con.commit()
        print("\nStudent added successfully!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_student_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        cur.execute("SELECT * FROM Students_Details")
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "ROLL", "NAME", "CLASS", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No records found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def search_student():
    con = None
    cur = None
    try:
        print("Search by:")
        print("1. Roll Number")
        print("2. Name")
        mode = input("Enter choice : : ").strip()
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        if mode == "1":
            roll = input("Enter roll number : : ").strip()
            cur.execute(
                "SELECT * FROM Students_Details WHERE ROLL_NUMBER=%s",
                (roll,)
            )
        elif mode == "2":
            name = input("Enter name to search : : ").strip()
            cur.execute(
                "SELECT * FROM Students_Details WHERE NAME LIKE %s",
                (f"%{name}%",)
            )
        else:
            print("Invalid choice.")
            return
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "ROLL", "NAME", "CLASS", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No student found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()
            
def update_student_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection Failed !")
            return
        cur = con.cursor()
        roll = input("Enter roll number to update : : ").strip()
        cur.execute(
            "SELECT * FROM Students_Details WHERE ROLL_NUMBER=%s",
            (roll,)
        )
        student = cur.fetchone()
        if not student:
            print("Student not found.")
            return
        while True:
            clear_screen()
            print("\nUPDATE STUDENT DETAILS".center(100))
            print("-" * 100)
            print("1. Update Name".center(100))
            print("2. Update Class".center(100))
            print("3. Update Age".center(100))
            print("4. Update Address".center(100))
            print("5. Update Phone".center(100))
            print("6. Update Email".center(100))
            print("7. Update Gender".center(100))
            print("8. Update All Details".center(100))
            print("0. Back".center(100))
            choice = input("\nEnter choice: ")
            if choice == "1":
                new_name = input("Enter new name : : ").strip()
                if not new_name:
                    print("Name cannot be empty!")
                else:
                    cur.execute(
                        "UPDATE Students_Details SET NAME=%s WHERE ROLL_NUMBER=%s",
                        (new_name, roll)
                    )
                    con.commit()
                    print("Name updated successfully!")
            elif choice == "2":
                new_class = input("Enter new class : : ").strip()
                cur.execute(
                    "UPDATE Students_Details SET CLASS=%s WHERE ROLL_NUMBER=%s",
                    (new_class, roll)
                )
                con.commit()
                print("Class updated successfully!")
            elif choice == "3":
                try:
                    new_age = int(input("Enter new age : : "))
                    if new_age <= 0 or new_age > 120:
                        print("Invalid age!")
                        continue
                    cur.execute(
                        "UPDATE Students_Details SET AGE=%s WHERE ROLL_NUMBER=%s",
                        (new_age, roll)
                    )
                    con.commit()
                    print("Age updated successfully!")
                except ValueError:
                    print("Age must be a number!")
            elif choice == "4":
                new_address = input("Enter new address : : ").strip()
                cur.execute(
                    "UPDATE Students_Details SET ADDRESS=%s WHERE ROLL_NUMBER=%s",
                    (new_address, roll)
                )
                con.commit()
                print("Address updated successfully!")
            elif choice == "5":
                new_phone = input("Enter new phone : : ").strip()
                if not valid_phonenumber(new_phone):
                    continue
                cur.execute("UPDATE Students_Details SET PHONE=%s WHERE ROLL_NUMBER=%s", (new_phone, roll))
                con.commit()
                print("Phone updated!")
            elif choice == "6":
                new_email = input("Enter new email : : ").strip()
                if not valid_email(new_email):
                    continue
                cur.execute("UPDATE Students_Details SET EMAIL=%s WHERE ROLL_NUMBER=%s", (new_email, roll))
                con.commit()
                print("Email updated!")
            elif choice == "7":
                new_gender = input("Gender (Male/Female/Other) : : ").strip()
                if new_gender not in ("Male", "Female", "Other"):
                    print("Invalid gender !")
                    pause_and_clear()
                    continue
                cur.execute("UPDATE Students_Details SET GENDER=%s WHERE ROLL_NUMBER=%s", (new_gender, roll))
                con.commit()
                print("Gender updated!")
            elif choice == "8":
                new_name = input("Enter new name : : ").strip()
                if not new_name:
                    print("Name cannot be Empty")
                    pause_and_clear()
                    continue
                new_class = input("Enter new class : : ").strip()
                try:
                    new_age = int(input("Enter new age : : "))
                except ValueError:
                    print("Age must be a number!")
                    pause_and_clear()
                    continue
                new_address = input("Enter new address : : ").strip()
                new_phone = input("Enter new phone : : ").strip()
                if not valid_phonenumber(new_phone):
                    pause_and_clear()
                    continue
                new_email = input("Enter new email : : ").strip()
                if not valid_email(new_email):
                    continue
                new_gender = input("Gender (Male/Female/Other) : : ").strip()
                if new_gender not in ("Male", "Female", "Other"):
                    print("Invalid Gender !")
                    pause_and_clear()
                    continue
                else:
                    cur.execute("""
                        UPDATE Students_Details
                        SET NAME=%s, CLASS=%s, AGE=%s, ADDRESS=%s,
                        PHONE=%s, EMAIL=%s, GENDER=%s
                        WHERE ROLL_NUMBER=%s"""
                        , (new_name, new_class, new_age, new_address,
                           new_phone, new_email, new_gender, roll))
                    con.commit()
                    print("All details updated successfully!")
            elif choice == "0":
                return
            else:
                print("Invalid choice!")
            pause_and_clear()
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()
            
def delete_student_details():
    con = None
    cur = None
    try:
        roll = input("Enter roll number to delete  : : ").strip()
        confirm = input("Are you sure? (y/n) : : ").lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return
        con = get_connection()
        if not con:
            print("Database connection Failed")
            return
        cur = con.cursor()
        cur.execute("DELETE FROM Students_Details WHERE ROLL_NUMBER=%s", (roll,))
        con.commit()
        if cur.rowcount > 0:
            print("Student deleted successfully!")
        else:
            print("Student not found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# -------------------------------- MAIN MENU ----------------------------------------

def student_menu():
    while True:
        clear_screen()
        print("\nSTUDENT MANAGEMENT SYSTEM".center(100))
        print("-" * 100)
        print("1. View Students Details".center(100))
        print("2. Search Student".center(100))
        print("3. Add New Student".center(100))
        print("4. Update Student Details".center(100))
        print("5. Delete Student Record".center(100))
        print("0. Exit".center(100))
        choice = input("\nEnter choice: ")
        
        if choice == "1":
            view_student_details()
        elif choice == "2":
            search_student()
        elif choice == "3":
            add_student()
        elif choice == "4":
            update_student_details()
        elif choice == "5":
            delete_student_details()
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice!")
        pause_and_clear()

