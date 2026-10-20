# --------------------------------- IMPORT COMMANDS ---------------------------------

import os
import csv
import mysql.connector as ms
from mysql.connector import Error

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear
)

TEMPLATES_DIR = "import_templates"

# --------------------------------- HELPER FUNCTIONS ---------------------------------

def normalize_dict_keys(row):
    """Normalizes column names to lowercase with underscores (e.g., 'Roll Number' -> 'roll_number')."""
    return {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}

def generate_csv_templates():
    """Generates ready-to-use blank Excel/CSV template sheets for easy data entry."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    templates = {
        "template_students.csv": [
            ["ROLL_NUMBER", "NAME", "CLASS", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
            ["1001", "Aarav Sharma", "10-A", "15", "12 Park Street, Delhi", "9876543210", "aarav@example.com", "Male"],
            ["1002", "Diya Patel", "10-A", "15", "45 Green Road, Mumbai", "9876543211", "diya@example.com", "Female"]
        ],
        "template_teachers.csv": [
            ["TEACHER_ID", "NAME", "SUBJECT", "AGE", "ADDRESS", "PHONE", "EMAIL", "GENDER"],
            ["T101", "Dr. Rajesh Verma", "Mathematics", "42", "7 Civil Lines, Jaipur", "9812345678", "rajesh@school.com", "Male"],
            ["T102", "Anita Roy", "English", "35", "18 Lake Road, Kolkata", "9812345679", "anita@school.com", "Female"]
        ],
        "template_books.csv": [
            ["BOOK_ID", "TITLE", "AUTHOR", "GENRE", "TOTAL_COPIES"],
            ["B101", "Concepts of Physics", "H.C. Verma", "Science", "25"],
            ["B102", "To Kill a Mockingbird", "Harper Lee", "Fiction", "15"]
        ]
    }

    for filename, rows in templates.items():
        filepath = os.path.join(TEMPLATES_DIR, filename)
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    print("\n" + "=" * 65)
    print("✅ CSV TEMPLATES GENERATED SUCCESSFULLY!")
    print(f"Folder location: {os.path.abspath(TEMPLATES_DIR)}")
    print("=" * 65)
    print("You can open these template files in Microsoft Excel, fill in")
    print("your school's data, and import them directly!")

# --------------------------------- IMPORT OPERATIONS -------------------------------

def import_students_from_csv():
    filepath = input("\nEnter the CSV file path (e.g. import_templates/template_students.csv) : : ").strip().strip('"')
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found!")
        return

    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        imported_count = 0
        skipped_count = 0

        with open(filepath, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row_num, raw_row in enumerate(reader, start=2):
                row = normalize_dict_keys(raw_row)
                
                roll = row.get("roll_number") or row.get("roll")
                name = row.get("name")
                s_class = row.get("class")
                age_val = row.get("age", "0")
                address = row.get("address", "")
                phone = row.get("phone", "")
                email = row.get("email", "")
                gender = row.get("gender", "Other")

                if not roll or not name:
                    print(f"Row {row_num}: Skipping (Missing Roll Number or Name)")
                    skipped_count += 1
                    continue

                try:
                    age = int(age_val) if age_val.isdigit() else 15
                except ValueError:
                    age = 15

                cur.execute("""
                    INSERT INTO Students_Details 
                    (ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        NAME=VALUES(NAME), CLASS=VALUES(CLASS), AGE=VALUES(AGE),
                        ADDRESS=VALUES(ADDRESS), PHONE=VALUES(PHONE), EMAIL=VALUES(EMAIL), GENDER=VALUES(GENDER)
                """, (roll, name, s_class, age, address, phone, email, gender))
                imported_count += 1

        con.commit()
        print("\n" + "=" * 55)
        print("STUDENT IMPORT SUMMARY".center(55))
        print("=" * 55)
        print(f"✅ Records Imported / Updated: {imported_count}")
        print(f"⚠️  Records Skipped           : {skipped_count}")
        print("=" * 55)

    except Error as e:
        print("Database Error:", e)
    except Exception as e:
        print("File Processing Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def import_teachers_from_csv():
    filepath = input("\nEnter the CSV file path (e.g. import_templates/template_teachers.csv) : : ").strip().strip('"')
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found!")
        return

    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        imported_count = 0
        skipped_count = 0

        with open(filepath, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row_num, raw_row in enumerate(reader, start=2):
                row = normalize_dict_keys(raw_row)

                teacher_id = row.get("teacher_id") or row.get("id")
                name = row.get("name")
                subject = row.get("subject", "General")
                age_val = row.get("age", "30")
                address = row.get("address", "")
                phone = row.get("phone", "")
                email = row.get("email", "")
                gender = row.get("gender", "Other")

                if not teacher_id or not name:
                    print(f"Row {row_num}: Skipping (Missing Teacher ID or Name)")
                    skipped_count += 1
                    continue

                age = int(age_val) if age_val.isdigit() else 30

                cur.execute("""
                    INSERT INTO Teachers_Details 
                    (TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        NAME=VALUES(NAME), SUBJECT=VALUES(SUBJECT), AGE=VALUES(AGE),
                        ADDRESS=VALUES(ADDRESS), PHONE=VALUES(PHONE), EMAIL=VALUES(EMAIL), GENDER=VALUES(GENDER)
                """, (teacher_id, name, subject, age, address, phone, email, gender))
                imported_count += 1

        con.commit()
        print("\n" + "=" * 55)
        print("TEACHER IMPORT SUMMARY".center(55))
        print("=" * 55)
        print(f"✅ Records Imported / Updated: {imported_count}")
        print(f"⚠️  Records Skipped           : {skipped_count}")
        print("=" * 55)

    except Error as e:
        print("Database Error:", e)
    except Exception as e:
        print("File Processing Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def import_books_from_csv():
    filepath = input("\nEnter the CSV file path (e.g. import_templates/template_books.csv) : : ").strip().strip('"')
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found!")
        return

    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        imported_count = 0
        skipped_count = 0

        with open(filepath, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row_num, raw_row in enumerate(reader, start=2):
                row = normalize_dict_keys(raw_row)

                book_id = row.get("book_id") or row.get("isbn")
                title = row.get("title")
                author = row.get("author", "Unknown")
                genre = row.get("genre", "General")
                copies_val = row.get("total_copies") or row.get("copies", "1")

                if not book_id or not title:
                    print(f"Row {row_num}: Skipping (Missing Book ID or Title)")
                    skipped_count += 1
                    continue

                copies = int(copies_val) if copies_val.isdigit() else 1

                cur.execute("""
                    INSERT INTO Books_Details 
                    (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        TITLE=VALUES(TITLE), AUTHOR=VALUES(AUTHOR), GENRE=VALUES(GENRE),
                        TOTAL_COPIES=VALUES(TOTAL_COPIES), AVAILABLE_COPIES=VALUES(AVAILABLE_COPIES)
                """, (book_id, title, author, genre, copies, copies))
                imported_count += 1

        con.commit()
        print("\n" + "=" * 55)
        print("LIBRARY IMPORT SUMMARY".center(55))
        print("=" * 55)
        print(f"✅ Books Imported / Updated : {imported_count}")
        print(f"⚠️  Records Skipped          : {skipped_count}")
        print("=" * 55)

    except Error as e:
        print("Database Error:", e)
    except Exception as e:
        print("File Processing Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- MAIN MENU ---------------------------------

def import_menu():
    while True:
        clear_screen()
        print("\nBULK DATA IMPORT FROM CSV / EXCEL".center(100))
        print("-" * 100)
        print("1. Import Students from CSV".center(100))
        print("2. Import Teachers from CSV".center(100))
        print("3. Import Library Books from CSV".center(100))
        print("4. Generate Blank CSV Templates (for Excel)".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            import_students_from_csv()
        elif choice == "2":
            import_teachers_from_csv()
        elif choice == "3":
            import_books_from_csv()
        elif choice == "4":
            generate_csv_templates()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()
