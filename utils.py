import re
import os
import mysql.connector as ms
from mysql.connector import Error
from dotenv import load_dotenv

# ---------------------------------- DATABASE CONFIG ----------------------------------
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "Student")

# ---------------------------------- SCREEN UTILITIES ---------------------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def center_text(text, width=100):
    return "\n".join(line.center(width) for line in text.split("\n"))

def pause_and_clear():
    input("\nPress Enter to continue...")
    clear_screen()

# ---------------------------------- VALIDATION UTILITIES -----------------------------
def valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, email):
        print("Invalid Email Format !")
        return False
    return True

def valid_phonenumber(phone):
    if not phone:
        print("Phone number cannot be empty. !")
        return False
    if not phone.isdigit():
        print("Phone number only contains digits. !")
        return False
    if len(phone) != 10:
        print("Invalid Phone number. Phone number must be 10 digits.")
        return False
    if phone[0] not in "6789":
        print("Invalid Phone number. Please enter a valid Indian phone number.")
        return False
    return True

# ---------------------------------- DATABASE HELPERS ---------------------------------
def create_database():
    con = None
    cur = None
    try:
        con = ms.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        cur = con.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    except Error as e:
        print("Database Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()

def get_connection():
    try:
        return ms.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    except Error as e:
        print("Connection Error:", e)
        return None