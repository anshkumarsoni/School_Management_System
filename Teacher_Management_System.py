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
def create_teacher_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Teachers_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                TEACHER_ID VARCHAR(20) UNIQUE NOT NULL,
                NAME VARCHAR(100) NOT NULL,
                SUBJECT VARCHAR(100),
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
def add_teacher():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed. ")
            return
        cur = con.cursor()
        TEACHER_ID = input("Enter Teacher ID (e.g. T101 or 1001) : : ").strip()
        if not TEACHER_ID:
            print("Teacher ID cannot be empty !! ")
            return
        cur.execute("SELECT 1 FROM Teachers_Details WHERE TEACHER_ID=%s", (TEACHER_ID,))
        if cur.fetchone():
            print("Teacher ID already exists !! ")
            return
        NAME = input("Enter name  : : ").strip()
        if not NAME:
            print("Name cannot be empty !! ")
            return
        SUBJECT = input("Enter subject  : : ").strip()
        if not SUBJECT:
            print("Subject cannot be empty !! ")
            return  
        try:
            AGE = int(input("Enter age  : : "))
            if AGE < 18 or AGE > 120:
                print("Invalid age ! Teacher's age must be between 18 and 120.")
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
        ADDRESS = input("Enter address  : : ").strip()
        cur.execute("""
            INSERT INTO Teachers_Details
            (TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER))
        con.commit()
        print("\nTeacher added successfully!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_teacher_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !! ")
            return
        cur = con.cursor()
        cur.execute("SELECT * FROM Teachers_Details")
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "TEACHER ID", "NAME", "SUBJECT", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
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

def search_teacher():
    con = None
    cur = None
    try:
        print("Search by:")
        print("1. Teacher ID")
        print("2. Name")
        mode = input("Enter choice : : ").strip()
        con = get_connection()
        if not con:
            print("Database connection failed !! ")
            return
        cur = con.cursor()
        if mode == "1":
            teacher_id = input("Enter Teacher ID : : ").strip()
            cur.execute(
                "SELECT * FROM Teachers_Details WHERE TEACHER_ID=%s",
                (teacher_id,)
            )
        elif mode == "2":
            name = input("Enter name to search : : ").strip()
            cur.execute(
                "SELECT * FROM Teachers_Details WHERE NAME LIKE %s",
                (f"%{name}%",)
            )
        else:
            print("Invalid choice.")
            return
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "TEACHER ID", "NAME", "SUBJECT", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No teacher found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()
            
def update_teacher_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection Failed !! ")
            return
        cur = con.cursor()
        teacher_id = input("Enter Teacher ID to update : : ").strip()
        cur.execute(
            "SELECT * FROM Teachers_Details WHERE TEACHER_ID=%s",
            (teacher_id,)
        )
        teacher = cur.fetchone()
        if not teacher:
            print("Teacher not found.")
            return
        while True:
            clear_screen()
            print("\nUPDATE TEACHER DETAILS".center(100))
            print("-" * 100)
            print("1. Update Name".center(100))
            print("2. Update Subject".center(100))
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
                        "UPDATE Teachers_Details SET NAME=%s WHERE TEACHER_ID=%s",
                        (new_name, teacher_id)
                    )
                    con.commit()
                    print("Name updated successfully!")
            elif choice == "2":
                new_subject = input("Enter new subject : : ").strip()
                if not new_subject:
                    print("Subject cannot be empty!")
                else:
                    cur.execute(
                        "UPDATE Teachers_Details SET SUBJECT=%s WHERE TEACHER_ID=%s",
                        (new_subject, teacher_id)
                    )
                    con.commit()
                    print("Subject updated successfully!")
            elif choice == "3":
                try:
                    new_age = int(input("Enter new age : : "))
                    if new_age < 18 or new_age > 120:
                        print("Invalid age! Age must be between 18 and 120.")
                        continue
                    cur.execute(
                        "UPDATE Teachers_Details SET AGE=%s WHERE TEACHER_ID=%s",
                        (new_age, teacher_id)
                    )
                    con.commit()
                    print("Age updated successfully!")
                except ValueError:
                    print("Age must be a number!")
            elif choice == "4":
                new_address = input("Enter new address : : ").strip()
                cur.execute(
                    "UPDATE Teachers_Details SET ADDRESS=%s WHERE TEACHER_ID=%s",
                    (new_address, teacher_id)
                )
                con.commit()
                print("Address updated successfully!")
            elif choice == "5":
                new_phone = input("Enter new phone : : ").strip()
                if not valid_phonenumber(new_phone):
                    continue
                cur.execute("UPDATE Teachers_Details SET PHONE=%s WHERE TEACHER_ID=%s", (new_phone, teacher_id))
                con.commit()
                print("Phone updated!")
            elif choice == "6":
                new_email = input("Enter new email : : ").strip()
                if not valid_email(new_email):
                    continue
                cur.execute("UPDATE Teachers_Details SET EMAIL=%s WHERE TEACHER_ID=%s", (new_email, teacher_id))
                con.commit()
                print("Email updated!")
            elif choice == "7":
                new_gender = input("Gender (Male/Female/Other) : : ").strip()
                if new_gender not in ("Male", "Female", "Other"):
                    print("Invalid gender !")
                    pause_and_clear()
                    continue
                cur.execute("UPDATE Teachers_Details SET GENDER=%s WHERE TEACHER_ID=%s", (new_gender, teacher_id))
                con.commit()
                print("Gender updated!")
            elif choice == "8":
                new_name = input("Enter new name : : ").strip()
                if not new_name:
                    print("Name cannot be empty!")
                    pause_and_clear()
                    continue
                new_subject = input("Enter new subject : : ").strip()
                if not new_subject:
                    print("Subject cannot be empty!")
                    pause_and_clear()
                    continue
                try:
                    new_age = int(input("Enter new age : : "))
                    if new_age < 18 or new_age > 120:
                        print("Invalid age! Age must be between 18 and 120.")
                        pause_and_clear()
                        continue
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
                    pause_and_clear()
                    continue
                new_gender = input("Gender (Male/Female/Other) : : ").strip()
                if new_gender not in ("Male", "Female", "Other"):
                    print("Invalid Gender ! ")
                    pause_and_clear()
                    continue
                
                cur.execute("""
                    UPDATE Teachers_Details
                    SET NAME=%s, SUBJECT=%s, AGE=%s, ADDRESS=%s,
                        PHONE=%s, EMAIL=%s, GENDER=%s
                    WHERE TEACHER_ID=%s"""
                    , (new_name, new_subject, new_age, new_address,
                       new_phone, new_email, new_gender, teacher_id))
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
            
def delete_teacher_details():
    con = None
    cur = None
    try:
        teacher_id = input("Enter Teacher ID to delete  : : ").strip()
        confirm = input("Are you sure? (y/n) : : ").lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return
        con = get_connection()
        if not con:
            print("Database connection Failed")
            return
        cur = con.cursor()
        cur.execute("DELETE FROM Teachers_Details WHERE TEACHER_ID=%s", (teacher_id,))
        con.commit()
        if cur.rowcount > 0:
            print("Teacher deleted successfully!")
        else:
            print("Teacher not found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# -------------------------------- MAIN MENU ----------------------------------------
def teacher_menu():
    while True:
        clear_screen()
        print("\nTEACHER MANAGEMENT".center(100))
        print("-" * 100)
        print("1. Add Teacher".center(100))
        print("2. View All Teachers".center(100))
        print("3. Search Teacher".center(100))
        print("4. Update Teacher Details".center(100))
        print("5. Delete Teacher Record".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            add_teacher()
        elif choice == "2":
            view_teacher_details()
        elif choice == "3":
            search_teacher()
        elif choice == "4":
            update_teacher_details()
        elif choice == "5":
            delete_teacher_details()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()


        
