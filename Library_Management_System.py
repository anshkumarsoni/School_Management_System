# --------------------------------- IMPORT COMMANDS ---------------------------------

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Books_Details (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                BOOK_ID VARCHAR(20) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                AUTHOR VARCHAR(100) NOT NULL,
                GENRE VARCHAR(50),
                TOTAL_COPIES INT NOT NULL,
                AVAILABLE_COPIES INT NOT NULL
            )
        """)
        con.commit()
    except Error as e:
        print("Table Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

# --------------------------------- CRUD FUNCTIONS ---------------------------------

def add_book():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()
        
        BOOK_ID = input("Enter Book ID (e.g. B101 or ISBN) : : ").strip()
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
            (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (BOOK_ID, TITLE, AUTHOR, GENRE, COPIES, COPIES))
        con.commit()
        print("\nBook added successfully!")
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
        cur = con.cursor()
        cur.execute("SELECT * FROM Books_Details")
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "BOOK ID", "TITLE", "AUTHOR", "GENRE", "TOTAL COPIES", "AVAILABLE COPIES"],
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
        mode = input("Enter choice : : ").strip()
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        if mode == "1":
            book_id = input("Enter Book ID : : ").strip()
            cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID=%s", (book_id,))
        elif mode == "2":
            query = input("Enter Title or Author to search : : ").strip()
            cur.execute(
                "SELECT * FROM Books_Details WHERE TITLE LIKE %s OR AUTHOR LIKE %s",
                (f"%{query}%", f"%{query}%")
            )
        else:
            print("Invalid choice.")
            return
        rows = cur.fetchall()
        if rows:
            print(tabulate(
                rows,
                headers=["ID", "BOOK ID", "TITLE", "AUTHOR", "GENRE", "TOTAL COPIES", "AVAILABLE COPIES"],
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
            print("4. Update Total Copies".center(100))
            print("5. Update Available Copies".center(100))
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
            elif choice == "5":
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
        confirm = input("Are you sure? (y/n) : : ").lower()
        if confirm != "y":
            print("Deletion cancelled.")
            return
        con = get_connection()
        if not con:
            print("Database connection Failed")
            return
        cur = con.cursor()
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

# --------------------------------- MAIN MENU ---------------------------------

def library_menu():
    while True:
        clear_screen()
        print("\nLIBRARY MANAGEMENT".center(100))
        print("-" * 100)
        print("1. Add New Book".center(100))
        print("2. View All Books".center(100))
        print("3. Search Book".center(100))
        print("4. Update Book Details".center(100))
        print("5. Delete Book Record".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

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
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()
