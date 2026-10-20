# --------------------------------- IMPORT COMMANDS ---------------------------------

import datetime
import matplotlib.pyplot as plt
import mysql.connector as ms
from mysql.connector import Error
from tabulate import tabulate
from utils import get_connection

from utils import (
    get_connection,
    clear_screen,
    pause_and_clear
)

# --------------------------------- TABLE CREATION ---------------------------------

def create_fee_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed !")
            return
        cur = con.cursor()
        
        # Table 1: Fee Structure per Class
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Fee_Structure (
                CLASS VARCHAR(20) PRIMARY KEY,
                ANNUAL_FEE DECIMAL(10, 2) NOT NULL
            )
        """)

        # Table 2: Payment Transactions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Fee_Transactions (
                RECEIPT_NO INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                AMOUNT_PAID DECIMAL(10, 2) NOT NULL,
                PAYMENT_DATE DATE NOT NULL,
                PAYMENT_MODE ENUM('Cash', 'UPI', 'Card', 'Cheque', 'Net Banking') NOT NULL,
                REMARKS VARCHAR(100)
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
    date_input = input(f"Enter Payment Date (YYYY-MM-DD) [Press Enter for Today: {today}]: ").strip()
    if not date_input:
        return today
    try:
        datetime.datetime.strptime(date_input, '%Y-%m-%d')
        return date_input
    except ValueError:
        print("Invalid date format! Using today's date.")
        return today

def get_student_fee_info(cur, roll):
    cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER=%s", (roll,))
    student = cur.fetchone()
    if not student:
        return None

    name, student_class = student

    # Get class standard annual fee (default to 45000 if not configured)
    cur.execute("SELECT ANNUAL_FEE FROM Fee_Structure WHERE CLASS=%s", (student_class,))
    row = cur.fetchone()
    total_fee = float(row[0]) if row else 45000.0

    # Get sum of payments made
    cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) FROM Fee_Transactions WHERE ROLL_NUMBER=%s", (roll,))
    total_paid = float(cur.fetchone()[0])
    balance_due = max(0.0, total_fee - total_paid)

    return {
        "roll": roll,
        "name": name,
        "class": student_class,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "balance_due": balance_due
    }

# --------------------------------- CRUD & FINANCE OPERATIONS -----------------------

def record_fee_payment():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        info = get_student_fee_info(cur, roll)
        if not info:
            print("Student not found!")
            return

        print("\n" + "-" * 50)
        print(f"Student: {info['name']} | Class: {info['class']}")
        print(f"Total Annual Fee : ₹{info['total_fee']:,.2f}")
        print(f"Total Paid So Far: ₹{info['total_paid']:,.2f}")
        print(f"Current Due      : ₹{info['balance_due']:,.2f}")
        print("-" * 50)

        if info['balance_due'] == 0:
            print("Notice: This student has already cleared all fee dues for the year.")
            confirm = input("Do you still want to record an advance payment? (y/n): ").lower()
            if confirm != 'y':
                return

        try:
            amount = float(input("\nEnter Amount to Pay (₹) : : "))
            if amount <= 0:
                print("Payment amount must be greater than zero!")
                return
        except ValueError:
            print("Invalid amount!")
            return

        print("\nPayment Modes:")
        print("1. Cash  2. UPI  3. Card  4. Cheque  5. Net Banking")
        mode_choice = input("Select Payment Mode (1-5) [Default=UPI] : : ").strip()
        modes = {"1": "Cash", "2": "UPI", "3": "Card", "4": "Cheque", "5": "Net Banking"}
        payment_mode = modes.get(mode_choice, "UPI")

        pay_date = get_input_date()
        remarks = input("Remarks (e.g. Term 1, Tuition) : : ").strip()

        cur.execute("""
            INSERT INTO Fee_Transactions (ROLL_NUMBER, AMOUNT_PAID, PAYMENT_DATE, PAYMENT_MODE, REMARKS)
            VALUES (%s, %s, %s, %s, %s)
        """, (roll, amount, pay_date, payment_mode, remarks))
        con.commit()
        receipt_no = cur.lastrowid

        # Print Payment Receipt
        new_due = max(0.0, info['balance_due'] - amount)
        receipt_data = [
            ["Receipt No.", f"REC-{receipt_no}"],
            ["Roll Number", roll],
            ["Student Name", info['name']],
            ["Class", info['class']],
            ["Amount Paid", f"₹{amount:,.2f}"],
            ["Payment Mode", payment_mode],
            ["Payment Date", pay_date],
            ["Remaining Due", f"₹{new_due:,.2f}"]
        ]

        print("\n" + "=" * 55)
        print("FEE PAYMENT RECEIPT".center(55))
        print("=" * 55)
        print(tabulate(receipt_data, tablefmt="fancy_grid"))
        print("\nPayment successfully recorded and receipt generated!")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_student_fee_status():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        roll = input("Enter Student Roll Number : : ").strip()
        info = get_student_fee_info(cur, roll)
        if not info:
            print("Student not found!")
            return

        summary = [
            ["Roll Number", info['roll']],
            ["Student Name", info['name']],
            ["Class", info['class']],
            ["Annual Fee", f"₹{info['total_fee']:,.2f}"],
            ["Total Paid", f"₹{info['total_paid']:,.2f}"],
            ["Balance Due", f"₹{info['balance_due']:,.2f}"],
            ["Status", "CLEARED" if info['balance_due'] == 0 else "PENDING"]
        ]

        print("\n" + "=" * 50)
        print("FEE ACCOUNT SUMMARY".center(50))
        print("=" * 50)
        print(tabulate(summary, tablefmt="fancy_grid"))

        # Show payment transaction history
        cur.execute("""
            SELECT RECEIPT_NO, AMOUNT_PAID, PAYMENT_DATE, PAYMENT_MODE, IFNULL(REMARKS, '-')
            FROM Fee_Transactions
            WHERE ROLL_NUMBER=%s
            ORDER BY PAYMENT_DATE DESC
        """, (roll,))
        transactions = cur.fetchall()

        if transactions:
            print("\nPayment History:")
            print(tabulate(
                transactions,
                headers=["Receipt #", "Amount (₹)", "Date", "Mode", "Remarks"],
                tablefmt="fancy_grid"
            ))
        else:
            print("\nNo payments recorded for this student yet.")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_fee_defaulters():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY CLASS, ROLL_NUMBER")
        students = cur.fetchall()

        defaulters = []
        for roll, name, s_class in students:
            info = get_student_fee_info(cur, roll)
            if info and info['balance_due'] > 0:
                defaulters.append([
                    roll,
                    name,
                    s_class,
                    f"₹{info['total_fee']:,.2f}",
                    f"₹{info['total_paid']:,.2f}",
                    f"₹{info['balance_due']:,.2f}"
                ])

        if defaulters:
            print("\n" + "=" * 80)
            print("FEE DEFAULTERS LIST (STUDENTS WITH PENDING DUES)".center(80))
            print("=" * 80)
            print(tabulate(
                defaulters,
                headers=["Roll", "Name", "Class", "Total Fee", "Paid", "Pending Due"],
                tablefmt="fancy_grid"
            ))
            print(f"\nTotal Defaulters: {len(defaulters)} students.")
        else:
            print("\nNo fee defaulters found! All students have cleared their dues.")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def view_all_transactions():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        cur.execute("""
            SELECT t.RECEIPT_NO, t.ROLL_NUMBER, s.NAME, s.CLASS, t.AMOUNT_PAID, t.PAYMENT_DATE, t.PAYMENT_MODE
            FROM Fee_Transactions t
            JOIN Students_Details s ON t.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY t.RECEIPT_NO DESC
        """)
        rows = cur.fetchall()

        if rows:
            print("\n" + "=" * 90)
            print("ALL FEE TRANSACTIONS".center(90))
            print("=" * 90)
            print(tabulate(
                rows,
                headers=["Receipt #", "Roll", "Name", "Class", "Amount (₹)", "Date", "Mode"],
                tablefmt="fancy_grid"
            ))
        else:
            print("No fee transactions recorded yet.")

    except Error as e:
        print("Error:", e)
    finally:
        if con:
            cur.close()
            con.close()

def manage_class_fee_structure():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        while True:
            clear_screen()
            print("\nCLASS FEE STRUCTURE CONFIGURATION".center(100))
            print("-" * 100)
            print("1. View Current Class Fees".center(100))
            print("2. Set / Update Class Fee".center(100))
            print("0. Back".center(100))
            choice = input("\nEnter choice: ")

            if choice == "1":
                cur.execute("SELECT CLASS, ANNUAL_FEE FROM Fee_Structure ORDER BY CLASS")
                rows = cur.fetchall()
                if rows:
                    formatted_rows = [[c, f"₹{float(f):,.2f}"] for c, f in rows]
                    print("\n" + tabulate(formatted_rows, headers=["Class", "Annual Fee"], tablefmt="fancy_grid"))
                else:
                    print("\nNo custom fee structure configured yet. (Default is ₹45,000.00 for all classes).")
                pause_and_clear()

            elif choice == "2":
                s_class = input("Enter Class (e.g. 10, 11-A) : : ").strip()
                try:
                    fee = float(input(f"Enter Annual Fee for Class '{s_class}' (₹) : : "))
                    if fee < 0:
                        print("Fee cannot be negative!")
                        pause_and_clear()
                        continue
                except ValueError:
                    print("Fee must be a valid number!")
                    pause_and_clear()
                    continue

                cur.execute("""
                    INSERT INTO Fee_Structure (CLASS, ANNUAL_FEE)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE ANNUAL_FEE=%s
                """, (s_class, fee, fee))
                con.commit()
                print(f"Fee for Class '{s_class}' successfully set to ₹{fee:,.2f}!")
                pause_and_clear()

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

# --------------------------- Graphical Representation ------------------------

def plot_fee_financial_analytics():
    con = None
    cur = None
    try:
        con = get_connection
        if not con:
            print("Databases connection failed.")
            return
        cur = con.cursor()
        cur.execute("""
                    SELECT s.CLASS, COUNT(s.ROLL_NUMBER) FROM Students_Details s GROUP BY s.CLASS
                    """)
        class_counts = cur.fetchall()
        if not class_counts:
            print("No students endrolled yet! Cannot generate financial charts.")
            return
        total_expected_fee = 0.0
        for s_class, count in class_counts:
            cur.execute("SELECT ANNUAL_FEE FROM Fee_Structure WHERE CLASS = %s", (s_class,))
            row = cur.fetchone()
            class_fee = float(row[0]) if row else 45000.0
            total_expected_fee += (class_fee * count)

        cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) FROM Fee_Transactions")
        total_collected = float(cur.fetchone()[0])
        total_pendind = max(0.0, total_expected_fee - total_collected)

        cur.execute("""
                    SELECT PAYMENT_MODE, IFNULL(SUM(AMOUNT_PAID), 0) FROM Fee_Transactions GROUP BY PAYMENT_MODE
                    """)
        mode_rows = cur.fetchall()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (14, 6))
        fig.suptitle("School Fee & Finance Analytics Dashboard", fontsize = 15, fontweight = "bold")
        lables_status = ["Collected Fee", "Pending Dues"]
        values_status = [total_collected, total_pendind]
        colors_status = ["#2ecc71","#e74c3c"]

        if total_collected == 0 and total_pendind == 0:
            values_status = [1]
            lables_status = ["No Fee Data"]
            colors_status = ["#95a5a6"]

        wedges, texts, autotexts = ax1.pie(
            values_status,
            labels = lables_status,
            colors=colors_status,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

        collection_pct = (total_collected / total_expected_fee * 100) if total_expected_fee > 0 else 0
        ax1.text(0, 0, f"Recovery\n{collection_pct:.1f}%", ha="center", va="center", fontsize=12, fontweight="bold")
        ax1.set_title(f"Fee Recovery Status\n(Target: ₹{total_expected_fee:,.0f})", fontsize=11, fontweight="bold")

        if mode_rows:
            modes = [r[0] for r in mode_rows]
            mode_amounts = [float(r[1]) for r in mode_rows]
            bar_colors = ["#3498db", "#9b59b6", "#f1c40f", "#e67e22", "#1abc9c"]
            bars = ax2.bar(modes, mode_amounts, color=bar_colors[:len(modes)], edgecolor="black", width=0.5)

            for bar in bars:
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + (max(mode_amounts) * 0.02),
                    f"₹{height:,.0f}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                    fontsize=9
                )
            ax2.set_ylabel("Total Collected (₹)", fontweight="bold")
            ax2.set_title("Collections by Payment Mode", fontsize=11, fontweight="bold")
            ax2.grid(axis="y", linestyle=":", alpha=0.6)
            ax2.set_ylim(0, max(mode_amounts) * 1.18 if mode_amounts else 1000)
        else:
            ax2.text(0.5, 0.5, "No transactions recorded yet", ha="center", va="center", fontsize=11, color="gray")
            ax2.set_title("Collections by Payment Mode", fontsize=11, fontweight="bold")
        plt.tight_layout()
        print("\nOpening Financial Dashboard Chart... (Close the chart window to return)")
        plt.show()
    except Exception as e:
        print("Financial Chart Error:", e)
    finally:
        if con:
            cur.close()
            con.close()
        
# --------------------------------- MAIN MENU ---------------------------------

def fee_menu():
    while True:
        clear_screen()
        print("\nFEE & FINANCE MANAGEMENT".center(100))
        print("-" * 100)
        print("1. Record Fee Payment (Generate Receipt)".center(100))
        print("2. Student Fee Status & History".center(100))
        print("3. View Fee Defaulters (Pending Dues)".center(100))
        print("4. View All Transaction Records".center(100))
        print("5. Configure Class Fee Structure".center(100))
        print("0. Back to Main Menu".center(100))
        choice = input("\nEnter choice: ")

        if choice == "1":
            record_fee_payment()
        elif choice == "2":
            view_student_fee_status()
        elif choice == "3":
            view_fee_defaulters()
        elif choice == "4":
            view_all_transactions()
        elif choice == "5":
            manage_class_fee_structure()
        elif choice == "0":
            return
        else:
            print("Invalid choice!")
        pause_and_clear()