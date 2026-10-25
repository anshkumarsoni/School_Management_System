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

def create_library_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        
        # 1. Books Details (Catalogue)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Books_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                BOOK_ID VARCHAR(20) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                AUTHOR VARCHAR(100) NOT NULL,
                GENRE VARCHAR(50),
                TOTAL_COPIES INT NOT NULL,
                AVAILABLE_COPIES INT NOT NULL,
                SHELF_LOCATION VARCHAR(50) DEFAULT NULL,
                ISBN VARCHAR(30) DEFAULT NULL,
                PUBLISHER VARCHAR(100) DEFAULT NULL
            )
        """)

        # 2. Book Issues (Issue / Return / Due Dates / Fines)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Book_Issues (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ISSUE_ID VARCHAR(30) UNIQUE NOT NULL,
                BOOK_ID VARCHAR(20) NOT NULL,
                BORROWER_TYPE ENUM('Student', 'Teacher') NOT NULL DEFAULT 'Student',
                BORROWER_ID VARCHAR(30) NOT NULL,
                BORROWER_NAME VARCHAR(100) NOT NULL,
                ISSUE_DATE DATE NOT NULL,
                DUE_DATE DATE NOT NULL,
                RETURN_DATE DATE NULL,
                STATUS ENUM('Issued', 'Returned', 'Overdue') NOT NULL DEFAULT 'Issued',
                FINE_AMOUNT DECIMAL(10, 2) DEFAULT 0.00,
                FINE_STATUS ENUM('None', 'Unpaid', 'Paid', 'Waived') DEFAULT 'None',
                REMARKS VARCHAR(255) NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Book Reservations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Book_Reservations (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                RESERVATION_ID VARCHAR(30) UNIQUE NOT NULL,
                BOOK_ID VARCHAR(20) NOT NULL,
                BORROWER_TYPE ENUM('Student', 'Teacher') NOT NULL DEFAULT 'Student',
                BORROWER_ID VARCHAR(30) NOT NULL,
                BORROWER_NAME VARCHAR(100) NOT NULL,
                RESERVE_DATE DATE NOT NULL,
                EXPIRY_DATE DATE NULL,
                STATUS ENUM('Pending', 'Ready for Pickup', 'Fulfilled', 'Cancelled') NOT NULL DEFAULT 'Pending',
                NOTES VARCHAR(255) NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.commit()
    except Error as e:
        print("Table Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- CATALOGUE CRUD ---------------------------------

def add_book():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()
        
        BOOK_ID = input("Enter Book ID (e.g. BK-101 or ISBN) : : ").strip()
        if not BOOK_ID:
            print("Book ID cannot be empty !")
            return
        cur.execute("SELECT 1 FROM Books_Details WHERE BOOK_ID=%s", (BOOK_ID,))
        if cur.fetchone():
            print("Book ID already exists !")
            return

        TITLE = input("Enter Book Title : : ").strip()
        if not TITLE:
            print("Title cannot be empty !")
            return

        AUTHOR = input("Enter Author Name : : ").strip()
        if not AUTHOR:
            print("Author cannot be empty !")
            return

        GENRE = input("Enter Genre/Subject (e.g. Science, Fiction, History) : : ").strip()
        SHELF = input("Enter Shelf Location (e.g. Rack A-02, optional) : : ").strip() or None
        ISBN = input("Enter ISBN (optional) : : ").strip() or None
        PUBLISHER = input("Enter Publisher (optional) : : ").strip() or None

        try:
            COPIES = int(input("Enter Total Copies : : "))
            if COPIES <= 0:
                print("Total copies must be at least 1 !")
                return
        except ValueError:
            print("Copies must be a number !")
            return

        cur.execute("""
            INSERT INTO Books_Details
            (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES, SHELF_LOCATION, ISBN, PUBLISHER)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (BOOK_ID, TITLE, AUTHOR, GENRE, COPIES, COPIES, SHELF, ISBN, PUBLISHER))
        con.commit()
        print("\nBook added successfully to catalogue!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_book_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES, SHELF_LOCATION FROM Books_Details ORDER BY ID ASC")
        rows = cur.fetchall()
        if rows:
            table_data = []
            for r in rows:
                issued = r['TOTAL_COPIES'] - r['AVAILABLE_COPIES']
                table_data.append([
                    r['BOOK_ID'],
                    r['TITLE'],
                    r['AUTHOR'],
                    r['GENRE'] or 'General',
                    r['TOTAL_COPIES'],
                    r['AVAILABLE_COPIES'],
                    issued,
                    r['SHELF_LOCATION'] or '-'
                ])
            print(tabulate(
                table_data,
                headers=["BOOK ID", "TITLE", "AUTHOR", "GENRE", "TOTAL", "AVAILABLE", "ISSUED", "SHELF"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No books found in the library.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def search_book():
    con = None
    cur = None
    try:
        print("Search by:")
        print("1. Book ID")
        print("2. Title / Author")
        print("3. Genre / Category")
        mode = input("Enter choice : : ").strip()
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor(dictionary=True)
        if mode == "1":
            book_id = input("Enter Book ID : : ").strip()
            cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
        elif mode == "2":
            query = input("Enter Title or Author to search : : ").strip()
            cur.execute(
                "SELECT * FROM Books_Details WHERE TITLE LIKE %s OR AUTHOR LIKE %s",
                (f"%{query}%", f"%{query}%")
            )
        elif mode == "3":
            genre = input("Enter Genre/Category : : ").strip()
            cur.execute("SELECT * FROM Books_Details WHERE GENRE LIKE %s", (f"%{genre}%",))
        else:
            print("Invalid choice.")
            return
        rows = cur.fetchall()
        if rows:
            table_data = []
            for r in rows:
                issued = r['TOTAL_COPIES'] - r['AVAILABLE_COPIES']
                table_data.append([
                    r['BOOK_ID'],
                    r['TITLE'],
                    r['AUTHOR'],
                    r['GENRE'] or 'General',
                    r['TOTAL_COPIES'],
                    r['AVAILABLE_COPIES'],
                    issued,
                    r.get('SHELF_LOCATION') or '-'
                ])
            print(tabulate(
                table_data,
                headers=["BOOK ID", "TITLE", "AUTHOR", "GENRE", "TOTAL", "AVAILABLE", "ISSUED", "SHELF"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No matching books found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def update_book_details():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection Failed !")
            return
        cur = con.cursor()
        book_id = input("Enter Book ID to update : : ").strip()
        cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
        book = cur.fetchone()
        if not book:
            print("Book not found.")
            return
        
        while True:
            clear_screen()
            print("\nUPDATE BOOK DETAILS".center(100))
            print("-" * 100)
            print("1. Update Title".center(100))
            print("2. Update Author".center(100))
            print("3. Update Genre".center(100))
            print("4. Update Shelf Location".center(100))
            print("5. Update Total Copies".center(100))
            print("6. Update Available Copies".center(100))
            print("0. Back".center(100))
            choice = input("\nEnter choice: ")

            if choice == "1":
                new_title = input("Enter new Title : : ").strip()
                if new_title:
                    cur.execute("UPDATE Books_Details SET TITLE=%s WHERE BOOK_ID=%s", (new_title, book_id))
                    con.commit()
                    print("Title updated successfully!")
            elif choice == "2":
                new_author = input("Enter new Author : : ").strip()
                if new_author:
                    cur.execute("UPDATE Books_Details SET AUTHOR=%s WHERE BOOK_ID=%s", (new_author, book_id))
                    con.commit()
                    print("Author updated successfully!")
            elif choice == "3":
                new_genre = input("Enter new Genre : : ").strip()
                cur.execute("UPDATE Books_Details SET GENRE=%s WHERE BOOK_ID=%s", (new_genre, book_id))
                con.commit()
                print("Genre updated successfully!")
            elif choice == "4":
                new_shelf = input("Enter new Shelf Location : : ").strip()
                cur.execute("UPDATE Books_Details SET SHELF_LOCATION=%s WHERE BOOK_ID=%s", (new_shelf, book_id))
                con.commit()
                print("Shelf location updated!")
            elif choice == "5":
                try:
                    new_total = int(input("Enter new Total Copies : : "))
                    if new_total < 0:
                        print("Copies cannot be negative!")
                        continue
                    cur.execute("UPDATE Books_Details SET TOTAL_COPIES=%s WHERE BOOK_ID=%s", (new_total, book_id))
                    con.commit()
                    print("Total copies updated!")
                except ValueError:
                    print("Must be a number!")
            elif choice == "6":
                try:
                    new_avail = int(input("Enter new Available Copies : : "))
                    if new_avail < 0:
                        print("Copies cannot be negative!")
                        continue
                    cur.execute("UPDATE Books_Details SET AVAILABLE_COPIES=%s WHERE BOOK_ID=%s", (new_avail, book_id))
                    con.commit()
                    print("Available copies updated!")
                except ValueError:
                    print("Must be a number!")
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

def delete_book_details():
    con = None
    cur = None
    try:
        book_id = input("Enter Book ID to delete : : ").strip()
        con = get_connection()
        if not con:
            print("Database connection Failed")
            return
        cur = con.cursor(dictionary=True)
        
        # Check active issues
        cur.execute("SELECT COUNT(*) AS c FROM Book_Issues WHERE BOOK_ID=%s AND STATUS='Issued'", (book_id,))
        if cur.fetchone()['c'] > 0:
            print("\nCannot delete book! Copies are currently issued to students or faculty.")
            return

        confirm = input("Are you sure you want to delete this book? (y/n) : : ").lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return

        cur.execute("DELETE FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
        con.commit()
        if cur.rowcount > 0:
            print("Book deleted successfully!")
        else:
            print("Book not found.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- ISSUE & RETURN TRACKING ---------------------------------

def issue_book():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor(dictionary=True)

        book_id = input("Enter Book ID to Issue (e.g. BK-1001) : : ").strip()
        cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
        book = cur.fetchone()
        if not book:
            print("Book ID not found in library catalogue.")
            return

        if book['AVAILABLE_COPIES'] <= 0:
            print(f"\nSorry, no available copies of '{book['TITLE']}'! All {book['TOTAL_COPIES']} copies are currently issued.")
            print("Tip: You can reserve this book in Option 9.")
            return

        print(f"\nBook: {book['TITLE']} by {book['AUTHOR']}")
        print(f"Available Copies: {book['AVAILABLE_COPIES']} / {book['TOTAL_COPIES']}")

        print("\nBorrower Type:")
        print("1. Student")
        print("2. Teacher")
        b_type_choice = input("Select (1 or 2, default 1) : : ").strip()
        borrower_type = "Teacher" if b_type_choice == "2" else "Student"

        borrower_id = input(f"Enter {borrower_type} ID (Roll No / Faculty ID) : : ").strip()
        if not borrower_id:
            print("Borrower ID cannot be empty!")
            return

        borrower_name = ""
        if borrower_type == "Student":
            cur.execute("SELECT NAME FROM Students_Details WHERE ROLL_NUMBER=%s", (borrower_id,))
            st = cur.fetchone()
            if st:
                borrower_name = st['NAME']
                print(f"Found Student: {borrower_name}")
        else:
            cur.execute("SELECT NAME FROM Teachers_Details WHERE TEACHER_ID=%s", (borrower_id,))
            tc = cur.fetchone()
            if tc:
                borrower_name = tc['NAME']
                print(f"Found Teacher: {borrower_name}")

        if not borrower_name:
            borrower_name = input("Enter Borrower Full Name : : ").strip()
            if not borrower_name:
                print("Borrower Name cannot be empty!")
                return

        due_days_str = input("Enter Lending Period in Days (default 14) : : ").strip()
        try:
            due_days = int(due_days_str) if due_days_str else 14
        except ValueError:
            due_days = 14

        remarks = input("Remarks / Course Note (optional) : : ").strip() or None

        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=due_days)

        # Generate unique ISSUE_ID
        cur.execute("SELECT MAX(ID) AS max_id FROM Book_Issues")
        row_id = (cur.fetchone()['max_id'] or 0) + 1
        issue_id = f"ISS-{today.year}-{row_id:04d}"

        cur.execute("""
            INSERT INTO Book_Issues 
            (ISSUE_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, ISSUE_DATE, DUE_DATE, STATUS, REMARKS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Issued', %s)
        """, (issue_id, book_id, borrower_type, borrower_id, borrower_name, today, due_date, remarks))

        # Decrement available copies
        cur.execute("UPDATE Books_Details SET AVAILABLE_COPIES = AVAILABLE_COPIES - 1 WHERE BOOK_ID = %s", (book_id,))
        con.commit()

        print("\n" + "="*60)
        print("BOOK ISSUED SUCCESSFULLY!".center(60))
        print("="*60)
        print(f"Issue ID       : {issue_id}")
        print(f"Book Title     : {book['TITLE']}")
        print(f"Borrower       : {borrower_name} ({borrower_type} - {borrower_id})")
        print(f"Issue Date     : {today.strftime('%b %d, %Y')}")
        print(f"Due Date       : {due_date.strftime('%b %d, %Y')} ({due_days} days)")
        print(f"Remaining Stock: {book['AVAILABLE_COPIES'] - 1} copies available")
        print("="*60)
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def return_book():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor(dictionary=True)

        query = input("Enter Issue ID (e.g. ISS-2026-001) or Book ID : : ").strip()
        if not query:
            print("Search entry cannot be empty!")
            return

        cur.execute("""
            SELECT i.*, b.TITLE, b.AUTHOR 
            FROM Book_Issues i
            JOIN Books_Details b ON i.BOOK_ID = b.BOOK_ID
            WHERE (i.ISSUE_ID = %s OR i.BOOK_ID = %s) AND i.STATUS = 'Issued'
            ORDER BY i.ID DESC
        """, (query, query))
        issues = cur.fetchall()

        if not issues:
            print("No active issued records found matching your entry.")
            return

        target_issue = None
        if len(issues) == 1:
            target_issue = issues[0]
        else:
            print("\nMultiple active issues found:")
            for idx, iss in enumerate(issues, 1):
                print(f"{idx}. {iss['ISSUE_ID']} - {iss['TITLE']} to {iss['BORROWER_NAME']} (Due: {iss['DUE_DATE']})")
            sel = int(input("Select issue number to return : : "))
            target_issue = issues[sel - 1]

        today = datetime.date.today()
        due_date = target_issue['DUE_DATE']
        days_overdue = (today - due_date).days if today > due_date else 0
        fine_rate = 5.00 # Rs 5 per day
        fine_amount = days_overdue * fine_rate

        print("\n" + "="*60)
        print("RETURN SUMMARY".center(60))
        print("="*60)
        print(f"Issue ID   : {target_issue['ISSUE_ID']}")
        print(f"Book Title : {target_issue['TITLE']}")
        print(f"Borrower   : {target_issue['BORROWER_NAME']} ({target_issue['BORROWER_ID']})")
        print(f"Due Date   : {due_date.strftime('%b %d, %Y')}")
        print(f"Return Date: {today.strftime('%b %d, %Y')}")

        fine_status = 'None'
        if days_overdue > 0:
            print(f"STATUS     : OVERDUE by {days_overdue} days!")
            print(f"Fine Amount: Rs. {fine_amount:.2f} (@ Rs. 5/day)")
            pay = input("Is fine collected now? (y/n, default y) : : ").strip().lower()
            fine_status = 'Paid' if pay != 'n' else 'Unpaid'
        else:
            print("STATUS     : On-Time Return (No Fines)")

        confirm = input("\nConfirm return process? (y/n) : : ").strip().lower()
        if confirm != 'y':
            print("Return cancelled.")
            return

        # Update Issue Record
        cur.execute("""
            UPDATE Book_Issues 
            SET RETURN_DATE = %s,
                STATUS = 'Returned',
                FINE_AMOUNT = %s,
                FINE_STATUS = %s
            WHERE ID = %s
        """, (today, fine_amount, fine_status, target_issue['ID']))

        # Increment Available Copies (capped at TOTAL_COPIES)
        cur.execute("""
            UPDATE Books_Details 
            SET AVAILABLE_COPIES = LEAST(TOTAL_COPIES, AVAILABLE_COPIES + 1)
            WHERE BOOK_ID = %s
        """, (target_issue['BOOK_ID'],))

        # Check for pending reservations
        cur.execute("""
            SELECT * FROM Book_Reservations 
            WHERE BOOK_ID = %s AND STATUS = 'Pending' 
            ORDER BY ID ASC LIMIT 1
        """, (target_issue['BOOK_ID'],))
        pending_res = cur.fetchone()
        if pending_res:
            cur.execute("""
                UPDATE Book_Reservations 
                SET STATUS = 'Ready for Pickup' 
                WHERE ID = %s
            """, (pending_res['ID'],))
            print(f"\n[NOTIFICATION]: Book reservation #{pending_res['RESERVATION_ID']} for {pending_res['BORROWER_NAME']} is now READY FOR PICKUP!")

        con.commit()
        print("\nBook returned successfully and catalogue stock updated!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_active_issues():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT i.*, b.TITLE 
            FROM Book_Issues i
            JOIN Books_Details b ON i.BOOK_ID = b.BOOK_ID
            WHERE i.STATUS = 'Issued'
            ORDER BY i.DUE_DATE ASC
        """)
        rows = cur.fetchall()
        today = datetime.date.today()

        if rows:
            table_data = []
            for r in rows:
                due = r['DUE_DATE']
                if today > due:
                    overdue_days = (today - due).days
                    status_text = f"OVERDUE (+{overdue_days}d)"
                    est_fine = f"Rs. {overdue_days * 5:.2f}"
                else:
                    days_left = (due - today).days
                    status_text = f"Active ({days_left}d left)"
                    est_fine = "Rs. 0.00"

                table_data.append([
                    r['ISSUE_ID'],
                    r['BOOK_ID'],
                    r['TITLE'][:28],
                    r['BORROWER_NAME'],
                    r['BORROWER_TYPE'],
                    r['ISSUE_DATE'].strftime('%Y-%m-%d'),
                    r['DUE_DATE'].strftime('%Y-%m-%d'),
                    status_text,
                    est_fine
                ])
            print(tabulate(
                table_data,
                headers=["ISSUE ID", "BOOK ID", "TITLE", "BORROWER", "TYPE", "ISSUED", "DUE DATE", "STATUS", "ACCRUED FINE"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No active book issues found. All books are accounted for in the library!")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- FINES MANAGEMENT ---------------------------------

def manage_fines():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor(dictionary=True)

        cur.execute("""
            SELECT i.*, b.TITLE 
            FROM Book_Issues i
            JOIN Books_Details b ON i.BOOK_ID = b.BOOK_ID
            WHERE i.FINE_AMOUNT > 0 AND i.FINE_STATUS = 'Unpaid'
            ORDER BY i.ID DESC
        """)
        fines = cur.fetchall()

        if not fines:
            print("\nAll fines are cleared! No outstanding unpaid fines in the system.")
            return

        print("\n" + "="*80)
        print("OUTSTANDING UNPAID FINES".center(80))
        print("="*80)
        table_data = []
        for f in fines:
            table_data.append([
                f['ID'],
                f['ISSUE_ID'],
                f['TITLE'][:25],
                f['BORROWER_NAME'],
                f['BORROWER_TYPE'],
                f"Rs. {f['FINE_AMOUNT']:.2f}",
                f['STATUS'],
                f['REMARKS'] or '-'
            ])
        print(tabulate(
            table_data,
            headers=["#", "ISSUE ID", "BOOK TITLE", "BORROWER", "TYPE", "FINE AMOUNT", "BOOK STATUS", "REMARKS"],
            tablefmt="fancy_grid"
        ))

        sel_id = input("\nEnter Record # to resolve fine (or 0 to cancel) : : ").strip()
        if sel_id == "0" or not sel_id:
            return

        cur.execute("SELECT * FROM Book_Issues WHERE ID=%s AND FINE_STATUS='Unpaid'", (sel_id,))
        target = cur.fetchone()
        if not target:
            print("Invalid record ID or fine already resolved.")
            return

        print(f"\nResolving fine of Rs. {target['FINE_AMOUNT']:.2f} for {target['BORROWER_NAME']}")
        print("1. Mark as Paid (Collected)")
        print("2. Waive Fine (Special permission / Exemption)")
        print("0. Cancel")
        act = input("Enter choice : : ").strip()

        if act == "1":
            cur.execute("UPDATE Book_Issues SET FINE_STATUS='Paid' WHERE ID=%s", (sel_id,))
            con.commit()
            print("Fine marked as PAID successfully!")
        elif act == "2":
            cur.execute("UPDATE Book_Issues SET FINE_STATUS='Waived' WHERE ID=%s", (sel_id,))
            con.commit()
            print("Fine WAIVED successfully!")
        else:
            print("Operation cancelled.")
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- RESERVATIONS ---------------------------------

def manage_reservations():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor(dictionary=True)

        while True:
            clear_screen()
            print("\nBOOK RESERVATIONS MANAGEMENT".center(100))
            print("-" * 100)
            print("1. Place New Book Reservation".center(100))
            print("2. View All Reservations".center(100))
            print("3. Fulfill Reservation (Issue Book)".center(100))
            print("4. Cancel Reservation".center(100))
            print("0. Back to Library Menu".center(100))
            print("-" * 100)

            ch = input("\nEnter choice : : ").strip()
            if ch == "1":
                book_id = input("Enter Book ID to Reserve : : ").strip()
                cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
                book = cur.fetchone()
                if not book:
                    print("Book not found.")
                    pause_and_clear()
                    continue

                b_type = "Teacher" if input("Borrower Type (1. Student / 2. Teacher) : : ").strip() == "2" else "Student"
                b_id = input(f"Enter {b_type} ID : : ").strip()
                b_name = input(f"Enter {b_type} Name : : ").strip()
                notes = input("Reservation Notes (optional) : : ").strip() or None

                today = datetime.date.today()
                exp = today + datetime.timedelta(days=7)
                
                cur.execute("SELECT MAX(ID) AS max_id FROM Book_Reservations")
                res_count = (cur.fetchone()['max_id'] or 0) + 1
                res_id = f"RES-{today.year}-{res_count:04d}"

                # Check if available
                res_status = 'Ready for Pickup' if book['AVAILABLE_COPIES'] > 0 else 'Pending'

                cur.execute("""
                    INSERT INTO Book_Reservations
                    (RESERVATION_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, RESERVE_DATE, EXPIRY_DATE, STATUS, NOTES)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (res_id, book_id, b_type, b_id, b_name, today, exp, res_status, notes))
                con.commit()
                print(f"\nReservation {res_id} placed! Status: {res_status}")
                pause_and_clear()

            elif ch == "2":
                cur.execute("""
                    SELECT r.*, b.TITLE 
                    FROM Book_Reservations r
                    JOIN Books_Details b ON r.BOOK_ID = b.BOOK_ID
                    ORDER BY r.ID DESC
                """)
                r_rows = cur.fetchall()
                if r_rows:
                    table_data = []
                    for r in r_rows:
                        table_data.append([
                            r['RESERVATION_ID'],
                            r['BOOK_ID'],
                            r['TITLE'][:25],
                            r['BORROWER_NAME'],
                            r['BORROWER_TYPE'],
                            r['RESERVE_DATE'].strftime('%Y-%m-%d'),
                            r['STATUS'],
                            r['NOTES'] or '-'
                        ])
                    print(tabulate(
                        table_data,
                        headers=["RES ID", "BOOK ID", "BOOK TITLE", "BORROWER", "TYPE", "DATE", "STATUS", "NOTES"],
                        tablefmt="fancy_grid"
                    ))
                else:
                    print("No reservations currently logged.")
                pause_and_clear()

            elif ch == "3":
                # Fulfill
                res_id = input("Enter Reservation ID to Fulfill (e.g. RES-2026-001) : : ").strip()
                cur.execute("SELECT * FROM Book_Reservations WHERE RESERVATION_ID=%s AND STATUS IN ('Pending', 'Ready for Pickup')", (res_id,))
                res_row = cur.fetchone()
                if not res_row:
                    print("Active reservation not found.")
                    pause_and_clear()
                    continue

                cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (res_row['BOOK_ID'],))
                bk = cur.fetchone()
                if bk['AVAILABLE_COPIES'] <= 0:
                    print(f"Cannot fulfill: No available copies for '{bk['TITLE']}' right now!")
                    pause_and_clear()
                    continue

                today = datetime.date.today()
                due = today + datetime.timedelta(days=14)
                cur.execute("SELECT MAX(ID) AS max_id FROM Book_Issues")
                iss_id_num = (cur.fetchone()['max_id'] or 0) + 1
                iss_code = f"ISS-{today.year}-{iss_id_num:04d}"

                cur.execute("""
                    INSERT INTO Book_Issues 
                    (ISSUE_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, ISSUE_DATE, DUE_DATE, STATUS, REMARKS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Issued', %s)
                """, (iss_code, res_row['BOOK_ID'], res_row['BORROWER_TYPE'], res_row['BORROWER_ID'], res_row['BORROWER_NAME'], today, due, f"Fulfilled from {res_id}"))

                cur.execute("UPDATE Book_Reservations SET STATUS='Fulfilled' WHERE ID=%s", (res_row['ID'],))
                cur.execute("UPDATE Books_Details SET AVAILABLE_COPIES = AVAILABLE_COPIES - 1 WHERE BOOK_ID=%s", (res_row['BOOK_ID'],))
                con.commit()
                print(f"\nReservation fulfilled! Created issue record {iss_code} due on {due.strftime('%b %d, %Y')}.")
                pause_and_clear()

            elif ch == "4":
                res_id = input("Enter Reservation ID to Cancel : : ").strip()
                cur.execute("UPDATE Book_Reservations SET STATUS='Cancelled' WHERE RESERVATION_ID=%s AND STATUS IN ('Pending', 'Ready for Pickup')", (res_id,))
                con.commit()
                if cur.rowcount > 0:
                    print("Reservation cancelled successfully!")
                else:
                    print("Active reservation not found.")
                pause_and_clear()

            elif ch == "0":
                break
    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- MAIN MENU ---------------------------------

def library_menu():
    create_library_tables()
    while True:
        clear_screen()
        print("\nLIBRARY & RESOURCE MANAGEMENT SYSTEM".center(100))
        print("=" * 100)
        print("1. Add New Book to Catalogue".center(100))
        print("2. View Book Catalogue".center(100))
        print("3. Search Book in Catalogue".center(100))
        print("4. Update Book Details".center(100))
        print("5. Delete Book Record".center(100))
        print("6. Issue Book (Student / Teacher)".center(100))
        print("7. Return Book & Process Fine".center(100))
        print("8. View Active Issues & Due Dates".center(100))
        print("9. Manage Book Reservations".center(100))
        print("10. Library Fines Management".center(100))
        print("0. Back to Main Menu".center(100))
        print("=" * 100)
        choice = input("\nEnter choice : : ").strip()

        if choice == "1":
            add_book()
        elif choice == "2":
            view_book_details()
        elif choice == "3":
            search_book()
        elif choice == "4":
            update_book_details()
        elif choice == "5":
            delete_book_details()
        elif choice == "6":
            issue_book()
        elif choice == "7":
            return_book()
        elif choice == "8":
            view_active_issues()
        elif choice == "9":
            manage_reservations()
        elif choice == "10":
            manage_fines()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()
