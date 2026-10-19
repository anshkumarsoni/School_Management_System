# ============================== IMPORT COMMANDS ==========================
import time
import pyfiglet

from utils import clear_screen, center_text, create_database, pause_and_clear
from Student_Manegement_System import create_student_table, student_menu
from Teacher_Management_System import create_teacher_tables, teacher_menu
from Library_Management_System import create_library_tables, library_menu
from Attendance_Management_System import create_attendance_tables, attendance_menu
from FeeFinance_Management_System import create_fee_tables, fee_menu
from ExamMarks_Management_System import create_exam_tables, exam_menu
from Export_Management_System import export_menu

# ============================== DATABASE INITIALIZATION ==================
def init_database():
    create_database()
    create_student_table()
    create_teacher_tables()
    create_library_tables()
    create_attendance_tables()
    create_fee_tables()
    create_exam_tables()

# ============================== WELCOME SCREEN ===========================   
def show_welcome_screen():
    clear_screen()
    h1 = pyfiglet.figlet_format("WELCOME TO ", font="doom")
    h2 = pyfiglet.figlet_format("SCHOOL MANAGEMENT SYSTEM", font="doom")
    print(center_text(h1))
    print(center_text(h2))
    print("\n")
    print("Loading Application".center(100), end="")
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="")
    time.sleep(0.5)
    clear_screen()

# ============================ MAIN MENU ==================================
def main():
    init_database()
    show_welcome_screen()
    while True:
        clear_screen()
        print("\n SCHOOL MANAGEMENT SYSTEM".center(100))
        print("=" * 100)
        print("1. Student Management System".center(100))
        print("2. Teacher Management System".center(100))
        print("3. Library Management System".center(100))
        print("4. Attendance Management System".center(100))
        print("5. Fee & Finance Management".center(100))
        print("6. Examination & Marks Management".center(100))
        print("7. Export Reports to CSV / Excel".center(100))
        print("0. Exit".center(100))
        print("=" * 100)
        
        choice = input("\nEnter choice : : ").strip()
        if choice == '1':
            student_menu()
        elif choice == '2':
            teacher_menu()
        elif choice == '3':
            library_menu()
        elif choice == '4':
            attendance_menu()
        elif choice == '5':
            fee_menu()
        elif choice == '6':
            exam_menu()
        elif choice == '7':
            export_menu()
        elif choice == '0':
            clear_screen()
            screen_down = pyfiglet.figlet_format("HAVE A GREAT DAY !!!!", font='doom')
            print(center_text(screen_down))
            print("Thank You For Visiting, Hope You Visit Again !! ".center(100))
            time.sleep(3)
            clear_screen()
            break
        else:
            print("Invalid Entry, Try Again")
            pause_and_clear()

if __name__ == "__main__":
    main()
