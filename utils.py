import re
import os
import mysql.connector as ms
from mysql.connector import Error
from dotenv import load_dotenv

# ---------------------------------- DATABASE CONFIG ----------------------------------
# Load .env file reliably from project directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

# Primary Database defaults to Cloud MySQL configuration
DB_HOST = os.getenv("DB_HOST", "mysql-3a9349bd-anshstudy115-7eee.i.aivencloud.com")
DB_USER = os.getenv("DB_USER", "avnadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "defaultdb")
DB_PORT = int(os.getenv("DB_PORT", "23236"))

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
def _resolve_ssl_ca():
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        if not os.path.isabs(ssl_ca):
            candidate = os.path.join(os.path.dirname(os.path.abspath(__file__)), ssl_ca)
            if os.path.exists(candidate):
                return candidate
        if os.path.exists(ssl_ca):
            return ssl_ca
    local_ca = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ca.pem")
    if os.path.exists(local_ca):
        return local_ca
    if os.path.exists("/etc/secrets/ca.pem"):
        return "/etc/secrets/ca.pem"
    return None

def create_database():
    con = None
    cur = None
    try:
        conn_kwargs = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD
        }
        resolved_ca = _resolve_ssl_ca()
        if resolved_ca:
            conn_kwargs["ssl_ca"] = resolved_ca
            conn_kwargs["ssl_verify_cert"] = True

        con = ms.connect(**conn_kwargs)
        cur = con.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    except Error as e:
        print("Database Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()

def get_connection():
    try:
        conn_kwargs = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME
        }
        resolved_ca = _resolve_ssl_ca()
        if resolved_ca:
            conn_kwargs["ssl_ca"] = resolved_ca
            conn_kwargs["ssl_verify_cert"] = True
        elif os.getenv("DB_SSL_MODE", "").upper() == "DISABLED":
            conn_kwargs["ssl_disabled"] = True

        return ms.connect(**conn_kwargs)
    except Error as e:
        print(f"Database Connection Error: {e} (Target Host: {DB_HOST}:{DB_PORT}, User: {DB_USER}, DB: {DB_NAME})")
        return None
