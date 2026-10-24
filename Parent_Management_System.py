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


# --------------------------------- TABLE CREATION ----------------------------------
def create_parent_tables():
    """Creates the Parents_Details database table if it doesn't already exist."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Parents_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                FATHER_NAME VARCHAR(100),
                FATHER_OCCUPATION VARCHAR(100),
                FATHER_PHONE VARCHAR(15),
                MOTHER_NAME VARCHAR(100),
                MOTHER_OCCUPATION VARCHAR(100),
                MOTHER_PHONE VARCHAR(15),
                GUARDIAN_NAME VARCHAR(100),
                RELATION VARCHAR(50) DEFAULT 'Parent',
                PRIMARY_CONTACT VARCHAR(15) NOT NULL,
                EMAIL VARCHAR(100),
                RESIDENTIAL_ADDRESS VARCHAR(255),
                EMERGENCY_CONTACT VARCHAR(15),
                ANNUAL_INCOME DECIMAL(12,2) DEFAULT 0.00,
                UNIQUE KEY unique_student_parent (ROLL_NUMBER)
            )
        """)
        con.commit()
    except Error as e:
        print("Parent Table Creation Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


# --------------------------------- CRUD FUNCTIONS ----------------------------------

def add_parent_details():
    """Adds or links parent and guardian details to an enrolled student."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        if not roll:
            print("Roll number cannot be empty!")
            return

        cur.execute("SELECT NAME, CLASS, ADDRESS, PHONE, EMAIL FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        student = cur.fetchone()
        if not student:
            print(f"Student with Roll Number '{roll}' not found in Students_Details! Please enroll student first.")
            return

        s_name, s_class, s_address, s_phone, s_email = student
        print(f"\nStudent Verified: {s_name} | Class: {s_class}")

        cur.execute("SELECT ID FROM Parents_Details WHERE ROLL_NUMBER = %s", (roll,))
        existing = cur.fetchone()
        if existing:
            overwrite = input("Parent details already exist for this student. Update them? (Y/N) : : ").strip().upper()
            if overwrite != 'Y':
                print("Operation cancelled.")
                return

        print("\n--- Enter Father's Details ---")
        father_name = input("Father's Name : : ").strip()
        father_occ = input("Father's Occupation : : ").strip()
        father_phone = input("Father's Phone Number : : ").strip()
        if father_phone and not valid_phonenumber(father_phone):
            return

        print("\n--- Enter Mother's Details ---")
        mother_name = input("Mother's Name : : ").strip()
        mother_occ = input("Mother's Occupation : : ").strip()
        mother_phone = input("Mother's Phone Number : : ").strip()
        if mother_phone and not valid_phonenumber(mother_phone):
            return

        print("\n--- Guardian Details (Optional if Father/Mother provided) ---")
        guardian_name = input("Guardian's Name (Leave blank if Father/Mother) : : ").strip()
        relation = input("Relationship with Student (e.g. Father, Mother, Guardian, Uncle) : : ").strip()
        if not relation:
            relation = "Father" if father_name else ("Mother" if mother_name else "Guardian")

        print("\n--- Contact & Address Information ---")
        primary_contact = input(f"Primary Contact Phone (Defaults to {father_phone or mother_phone or s_phone}) : : ").strip()
        if not primary_contact:
            primary_contact = father_phone or mother_phone or s_phone
        if not valid_phonenumber(primary_contact):
            return

        email = input("Parent Email Address : : ").strip()
        if email and not valid_email(email):
            return

        address = input(f"Residential Address (Defaults to: '{s_address}') : : ").strip()
        if not address:
            address = s_address or "Not specified"

        emergency_contact = input("Emergency Contact Number : : ").strip()
        if emergency_contact and not valid_phonenumber(emergency_contact):
            return

        income_raw = input("Annual Family Income (INR, Optional) : : ").strip()
        try:
            annual_income = float(income_raw) if income_raw else 0.00
        except ValueError:
            annual_income = 0.00

        cur.execute("""
            INSERT INTO Parents_Details (
                ROLL_NUMBER, FATHER_NAME, FATHER_OCCUPATION, FATHER_PHONE,
                MOTHER_NAME, MOTHER_OCCUPATION, MOTHER_PHONE,
                GUARDIAN_NAME, RELATION, PRIMARY_CONTACT,
                EMAIL, RESIDENTIAL_ADDRESS, EMERGENCY_CONTACT, ANNUAL_INCOME
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                FATHER_NAME = %s, FATHER_OCCUPATION = %s, FATHER_PHONE = %s,
                MOTHER_NAME = %s, MOTHER_OCCUPATION = %s, MOTHER_PHONE = %s,
                GUARDIAN_NAME = %s, RELATION = %s, PRIMARY_CONTACT = %s,
                EMAIL = %s, RESIDENTIAL_ADDRESS = %s, EMERGENCY_CONTACT = %s, ANNUAL_INCOME = %s
        """, (
            roll, father_name, father_occ, father_phone,
            mother_name, mother_occ, mother_phone,
            guardian_name, relation, primary_contact,
            email, address, emergency_contact, annual_income,
            father_name, father_occ, father_phone,
            mother_name, mother_occ, mother_phone,
            guardian_name, relation, primary_contact,
            email, address, emergency_contact, annual_income
        ))
        con.commit()
        print(f"\nParent & Guardian details successfully linked to student '{s_name}' (Roll #{roll})!")
    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


def view_parent_details():
    """Displays all parent and guardian records with linked student information."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()
        cur.execute("""
            SELECT 
                p.ROLL_NUMBER,
                COALESCE(s.NAME, 'N/A') AS STUDENT_NAME,
                COALESCE(s.CLASS, 'N/A') AS CLASS,
                COALESCE(p.FATHER_NAME, '-') AS FATHER,
                COALESCE(p.FATHER_OCCUPATION, '-') AS F_OCCUPATION,
                COALESCE(p.MOTHER_NAME, '-') AS MOTHER,
                COALESCE(p.PRIMARY_CONTACT, '-') AS CONTACT,
                COALESCE(p.EMAIL, '-') AS EMAIL,
                COALESCE(p.EMERGENCY_CONTACT, '-') AS EMERGENCY
            FROM Parents_Details p
            LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY p.ROLL_NUMBER ASC
        """)
        rows = cur.fetchall()
        if rows:
            print("\n" + "=" * 105)
            print("STUDENT PARENT & GUARDIAN DIRECTORY".center(105))
            print("=" * 105)
            print(tabulate(
                rows,
                headers=["Roll #", "Student Name", "Class", "Father's Name", "Occupation", "Mother's Name", "Primary Phone", "Email", "Emergency Contact"],
                tablefmt="fancy_grid"
            ))
            print(f"\nTotal Parent Records Listed: {len(rows)}")
        else:
            print("\nNo parent/guardian records found in the database.")
    except Error as e:
        print("Database Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


def search_parent_details():
    """Searches for parent details by student roll number, student name, or parent name."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        print("\nSearch Parent Details By:")
        print("1. Student Roll Number")
        print("2. Student Name")
        print("3. Father's Name")
        print("4. Mother's Name")
        print("5. Primary Phone Number")
        choice = input("Enter choice (1-5) : : ").strip()

        query_field = ""
        param = ""

        if choice == "1":
            val = input("Enter Student Roll Number : : ").strip()
            query_field = "p.ROLL_NUMBER = %s"
            param = val
        elif choice == "2":
            val = input("Enter Student Name : : ").strip()
            query_field = "s.NAME LIKE %s"
            param = f"%{val}%"
        elif choice == "3":
            val = input("Enter Father's Name : : ").strip()
            query_field = "p.FATHER_NAME LIKE %s"
            param = f"%{val}%"
        elif choice == "4":
            val = input("Enter Mother's Name : : ").strip()
            query_field = "p.MOTHER_NAME LIKE %s"
            param = f"%{val}%"
        elif choice == "5":
            val = input("Enter Phone Number : : ").strip()
            query_field = "(p.PRIMARY_CONTACT LIKE %s OR p.FATHER_PHONE LIKE %s OR p.MOTHER_PHONE LIKE %s)"
            param = f"%{val}%"
        else:
            print("Invalid search choice.")
            return

        if choice == "5":
            sql = f"""
                SELECT 
                    p.ROLL_NUMBER,
                    COALESCE(s.NAME, 'N/A') AS STUDENT_NAME,
                    COALESCE(s.CLASS, 'N/A') AS CLASS,
                    p.FATHER_NAME, p.FATHER_PHONE,
                    p.MOTHER_NAME, p.MOTHER_PHONE,
                    p.PRIMARY_CONTACT, p.EMAIL, p.RESIDENTIAL_ADDRESS, p.EMERGENCY_CONTACT
                FROM Parents_Details p
                LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER
                WHERE {query_field}
            """
            cur.execute(sql, (param, param, param))
        else:
            sql = f"""
                SELECT 
                    p.ROLL_NUMBER,
                    COALESCE(s.NAME, 'N/A') AS STUDENT_NAME,
                    COALESCE(s.CLASS, 'N/A') AS CLASS,
                    p.FATHER_NAME, p.FATHER_PHONE,
                    p.MOTHER_NAME, p.MOTHER_PHONE,
                    p.PRIMARY_CONTACT, p.EMAIL, p.RESIDENTIAL_ADDRESS, p.EMERGENCY_CONTACT
                FROM Parents_Details p
                LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER
                WHERE {query_field}
            """
            cur.execute(sql, (param,))

        rows = cur.fetchall()
        if rows:
            print("\nSearch Results Found:")
            print(tabulate(
                rows,
                headers=["Roll #", "Student", "Class", "Father", "Father Phone", "Mother", "Mother Phone", "Primary Phone", "Email", "Address", "Emergency"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No matching parent/guardian records found.")
    except Error as e:
        print("Search Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


def update_parent_details():
    """Updates fields of an existing parent/guardian record."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)

        roll = input("Enter Student Roll Number to update parent details : : ").strip()
        cur.execute("""
            SELECT p.*, s.NAME AS STUDENT_NAME 
            FROM Parents_Details p 
            LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER 
            WHERE p.ROLL_NUMBER = %s
        """, (roll,))
        parent = cur.fetchone()

        if not parent:
            print(f"No parent details found for Roll #{roll}. Use 'Add Parent Details' to create one.")
            return

        print(f"\nEditing Parent Details for: {parent.get('STUDENT_NAME', 'Student')} (Roll #{roll})")

        while True:
            clear_screen()
            print("\n" + "=" * 90)
            print(f"UPDATE PARENT DETAILS: {parent.get('STUDENT_NAME')} (Roll #{roll})".center(90))
            print("=" * 90)
            print("1. Update Father's Name & Occupation")
            print("2. Update Father's Phone Number")
            print("3. Update Mother's Name & Occupation")
            print("4. Update Mother's Phone Number")
            print("5. Update Guardian Name & Relation")
            print("6. Update Primary Contact Phone")
            print("7. Update Email Address")
            print("8. Update Residential Address")
            print("9. Update Emergency Contact & Annual Income")
            print("0. Back to Parent Menu")
            print("-" * 90)

            choice = input("\nEnter choice : : ").strip()

            if choice == "1":
                fn = input("New Father's Name : : ").strip()
                fo = input("New Father's Occupation : : ").strip()
                if fn:
                    cur.execute("UPDATE Parents_Details SET FATHER_NAME = %s, FATHER_OCCUPATION = %s WHERE ROLL_NUMBER = %s", (fn, fo, roll))
                    con.commit()
                    print("Father's details updated successfully!")
            elif choice == "2":
                fp = input("New Father's Phone (10 digits) : : ").strip()
                if valid_phonenumber(fp):
                    cur.execute("UPDATE Parents_Details SET FATHER_PHONE = %s WHERE ROLL_NUMBER = %s", (fp, roll))
                    con.commit()
                    print("Father's phone updated successfully!")
            elif choice == "3":
                mn = input("New Mother's Name : : ").strip()
                mo = input("New Mother's Occupation : : ").strip()
                if mn:
                    cur.execute("UPDATE Parents_Details SET MOTHER_NAME = %s, MOTHER_OCCUPATION = %s WHERE ROLL_NUMBER = %s", (mn, mo, roll))
                    con.commit()
                    print("Mother's details updated successfully!")
            elif choice == "4":
                mp = input("New Mother's Phone (10 digits) : : ").strip()
                if valid_phonenumber(mp):
                    cur.execute("UPDATE Parents_Details SET MOTHER_PHONE = %s WHERE ROLL_NUMBER = %s", (mp, roll))
                    con.commit()
                    print("Mother's phone updated successfully!")
            elif choice == "5":
                gn = input("New Guardian's Name : : ").strip()
                rel = input("New Relationship : : ").strip()
                cur.execute("UPDATE Parents_Details SET GUARDIAN_NAME = %s, RELATION = %s WHERE ROLL_NUMBER = %s", (gn, rel, roll))
                con.commit()
                print("Guardian details updated successfully!")
            elif choice == "6":
                p_contact = input("New Primary Contact Phone (10 digits) : : ").strip()
                if valid_phonenumber(p_contact):
                    cur.execute("UPDATE Parents_Details SET PRIMARY_CONTACT = %s WHERE ROLL_NUMBER = %s", (p_contact, roll))
                    con.commit()
                    print("Primary contact phone updated successfully!")
            elif choice == "7":
                new_email = input("New Email Address : : ").strip()
                if valid_email(new_email):
                    cur.execute("UPDATE Parents_Details SET EMAIL = %s WHERE ROLL_NUMBER = %s", (new_email, roll))
                    con.commit()
                    print("Email address updated successfully!")
            elif choice == "8":
                new_addr = input("New Residential Address : : ").strip()
                if new_addr:
                    cur.execute("UPDATE Parents_Details SET RESIDENTIAL_ADDRESS = %s WHERE ROLL_NUMBER = %s", (new_addr, roll))
                    con.commit()
                    print("Residential address updated successfully!")
            elif choice == "9":
                em_phone = input("New Emergency Contact Phone : : ").strip()
                inc_raw = input("Annual Family Income (INR) : : ").strip()
                try:
                    inc = float(inc_raw) if inc_raw else None
                except ValueError:
                    inc = None

                if em_phone and valid_phonenumber(em_phone):
                    cur.execute("UPDATE Parents_Details SET EMERGENCY_CONTACT = %s WHERE ROLL_NUMBER = %s", (em_phone, roll))
                if inc is not None:
                    cur.execute("UPDATE Parents_Details SET ANNUAL_INCOME = %s WHERE ROLL_NUMBER = %s", (inc, roll))
                con.commit()
                print("Emergency contact & income updated successfully!")
            elif choice == "0":
                print("Returning to Parent Menu...")
                break
            else:
                print("Invalid option selected!")

            pause_and_clear()
    except Error as e:
        print("Database Update Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


def delete_parent_details():
    """Deletes parent details record for a specified student roll number."""
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor(dictionary=True)

        roll = input("Enter Student Roll Number whose parent details you want to delete : : ").strip()
        cur.execute("""
            SELECT p.*, s.NAME AS STUDENT_NAME 
            FROM Parents_Details p 
            LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER 
            WHERE p.ROLL_NUMBER = %s
        """, (roll,))
        row = cur.fetchone()

        if not row:
            print(f"No parent details record found for Roll #{roll}.")
            return

        print(f"\nStudent: {row.get('STUDENT_NAME', 'Student')} (Roll #{roll})")
        print(f"Father: {row.get('FATHER_NAME', '-')} | Mother: {row.get('MOTHER_NAME', '-')} | Primary: {row.get('PRIMARY_CONTACT')}")

        confirm = input("\nAre you SURE you want to delete this parent record? (Y/N) : : ").strip().upper()
        if confirm == 'Y':
            cur.execute("DELETE FROM Parents_Details WHERE ROLL_NUMBER = %s", (roll,))
            con.commit()
            print("Parent record deleted successfully!")
        else:
            print("Deletion cancelled.")
    except Error as e:
        print("Delete Error:", e)
    finally:
        if con:
            cur.close()
            con.close()


# --------------------------------- MENU ----------------------------------------

def parent_menu():
    """Interactive Command Line Interface Menu for Parent & Guardian Management."""
    create_parent_tables()
    while True:
        clear_screen()
        print("\n" + "=" * 100)
        print("PARENT & GUARDIAN MANAGEMENT SYSTEM".center(100))
        print("=" * 100)
        print("1. View All Parent & Guardian Details".center(100))
        print("2. Search Parent Record".center(100))
        print("3. Add / Link Parent Details to Student".center(100))
        print("4. Update Parent Information".center(100))
        print("5. Delete Parent Record".center(100))
        print("0. Back to Main Menu".center(100))
        print("=" * 100)

        choice = input("\nEnter choice (0-5) : : ").strip()

        if choice == "1":
            view_parent_details()
        elif choice == "2":
            search_parent_details()
        elif choice == "3":
            add_parent_details()
        elif choice == "4":
            update_parent_details()
        elif choice == "5":
            delete_parent_details()
        elif choice == "0":
            print("Returning to Main Menu...")
            break
        else:
            print("Invalid choice, please select between 0 and 5.")

        pause_and_clear()


if __name__ == "__main__":
    parent_menu()
