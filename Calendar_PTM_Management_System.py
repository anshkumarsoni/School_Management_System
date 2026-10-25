# -------------------------------------------------------------------------
# SCHOOL CALENDAR & PARENT-TEACHER MEETINGS (PTM) MANAGEMENT SYSTEM
# Holidays, School Events, Meeting Slots, Parent Bookings & Reminders
# -------------------------------------------------------------------------

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

def create_calendar_ptm_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        # 1. School Holidays
        cur.execute("""
            CREATE TABLE IF NOT EXISTS School_Holidays (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                HOLIDAY_NAME VARCHAR(150) NOT NULL,
                START_DATE DATE NOT NULL,
                END_DATE DATE NOT NULL,
                HOLIDAY_TYPE ENUM('National Holiday', 'Gazetted Holiday', 'Term Break', 'Emergency Closure', 'Restricted Holiday') DEFAULT 'Gazetted Holiday',
                DESCRIPTION TEXT NULL,
                IS_ACADEMIC_OFF BOOLEAN DEFAULT TRUE,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. School Events
        cur.execute("""
            CREATE TABLE IF NOT EXISTS School_Events (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                EVENT_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(200) NOT NULL,
                EVENT_DATE DATE NOT NULL,
                START_TIME TIME NULL,
                END_TIME TIME NULL,
                CATEGORY ENUM('Academic', 'Examination', 'Sports', 'Cultural', 'Meeting', 'Exhibition', 'Workshop', 'Holiday') DEFAULT 'Academic',
                LOCATION VARCHAR(100) DEFAULT 'Main Campus',
                TARGET_AUDIENCE ENUM('All Students', 'Parents & Teachers', 'High School (Grades 10-12)', 'Middle School (Grades 6-9)', 'Faculty Only') DEFAULT 'All Students',
                ORGANIZER VARCHAR(100) NOT NULL,
                DESCRIPTION TEXT NULL,
                STATUS ENUM('Scheduled', 'Ongoing', 'Completed', 'Postponed', 'Cancelled') DEFAULT 'Scheduled',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. PTM Meeting Slots
        cur.execute("""
            CREATE TABLE IF NOT EXISTS PTM_Meeting_Slots (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                SLOT_CODE VARCHAR(30) UNIQUE NOT NULL,
                TEACHER_ID VARCHAR(20) NOT NULL,
                TEACHER_NAME VARCHAR(100) NOT NULL,
                SUBJECT VARCHAR(80) NOT NULL,
                MEETING_DATE DATE NOT NULL,
                START_TIME TIME NOT NULL,
                END_TIME TIME NOT NULL,
                MEETING_MODE ENUM('In-Person (Campus)', 'Virtual (Google Meet / Zoom)', 'Phone Call') DEFAULT 'In-Person (Campus)',
                ROOM_OR_LINK VARCHAR(255) DEFAULT 'Staff Room Block A',
                MAX_CAPACITY INT DEFAULT 1,
                STATUS ENUM('Available', 'Booked', 'Completed', 'Cancelled') DEFAULT 'Available',
                NOTES VARCHAR(255) NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. PTM Bookings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS PTM_Bookings (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                BOOKING_CODE VARCHAR(30) UNIQUE NOT NULL,
                SLOT_CODE VARCHAR(30) NOT NULL,
                STUDENT_ROLL VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                STUDENT_CLASS VARCHAR(50) NOT NULL,
                PARENT_NAME VARCHAR(100) NOT NULL,
                PARENT_PHONE VARCHAR(20) NOT NULL,
                PARENT_EMAIL VARCHAR(100) NULL,
                DISCUSSION_TOPIC TEXT NOT NULL,
                STATUS ENUM('Confirmed', 'Pending Confirmation', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Confirmed',
                REMINDER_SENT BOOLEAN DEFAULT FALSE,
                REMINDER_SENT_AT DATETIME NULL,
                TEACHER_FEEDBACK_NOTES TEXT NULL,
                BOOKED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Calendar Reminders & Alerts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Calendar_Reminders (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                REMINDER_CODE VARCHAR(30) UNIQUE NOT NULL,
                TITLE VARCHAR(150) NOT NULL,
                REMINDER_DATE DATE NOT NULL,
                TARGET_TYPE ENUM('All Parents', 'Specific Student / Parent', 'Faculty', 'All School') DEFAULT 'All School',
                TARGET_ID VARCHAR(50) NULL,
                RECIPIENT_NAME VARCHAR(100) NULL,
                MESSAGE TEXT NOT NULL,
                STATUS ENUM('Active', 'Sent', 'Dismissed') DEFAULT 'Active',
                DELIVERY_CHANNEL ENUM('In-App Notification', 'SMS Alert', 'Email Notice') DEFAULT 'In-App Notification',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.commit()
    except Error as e:
        print("Calendar & PTM Tables Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()


# --------------------------------- STARTER SEED DATA ---------------------------------

def seed_calendar_ptm_data():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            return
        cur = con.cursor(dictionary=True)

        today = datetime.date.today()

        # 1. Seed School Holidays
        cur.execute("SELECT COUNT(*) AS CNT FROM School_Holidays")
        if cur.fetchone()["CNT"] == 0:
            holidays = [
                ("Diwali & Festive Break", today + datetime.timedelta(days=6), today + datetime.timedelta(days=10), "Term Break", "Campus closed for Diwali festivities, Dhanteras, and Govardhan Puja celebration.", True),
                ("Guru Nanak Jayanti", today + datetime.timedelta(days=20), today + datetime.timedelta(days=20), "Gazetted Holiday", "Official holiday commemorating Guru Nanak Gurpurab.", True),
                ("Winter Term Vacation", today + datetime.timedelta(days=58), today + datetime.timedelta(days=70), "Term Break", "Annual winter school break and New Year vacation.", True),
                ("Republic Day", today + datetime.timedelta(days=93), today + datetime.timedelta(days=93), "National Holiday", "Flag hoisting ceremony in main quadrangle at 8:30 AM; academic holiday.", True),
                ("Maha Shivratri", today + datetime.timedelta(days=125), today + datetime.timedelta(days=125), "Gazetted Holiday", "Gazetted religious holiday.", True)
            ]
            cur.executemany("""
                INSERT INTO School_Holidays (HOLIDAY_NAME, START_DATE, END_DATE, HOLIDAY_TYPE, DESCRIPTION, IS_ACADEMIC_OFF)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, holidays)
            con.commit()
            print("Seeded School Holidays.")

        # 2. Seed School Events
        cur.execute("SELECT COUNT(*) AS CNT FROM School_Events")
        if cur.fetchone()["CNT"] == 0:
            events = [
                ("EVT-101", "Mid-Term Examination Period", today + datetime.timedelta(days=3), "09:00:00", "12:30:00", "Examination", "Main Examination Halls A & B", "All Students", "Exam Controller Dr. Khanna", "Half-yearly summative assessments across all grades.", "Scheduled"),
                ("EVT-102", "Annual Science, AI & Robotics Expo", today + datetime.timedelta(days=11), "10:00:00", "16:00:00", "Exhibition", "Campus Auditorium & Labs", "All Students", "Science Department Prof. Menon", "Student scientific project displays, working prototypes, and robotics arena.", "Scheduled"),
                ("EVT-103", "Semester Parent-Teacher Conference (PTM)", today + datetime.timedelta(days=18), "09:00:00", "15:00:00", "Meeting", "Academic Block Classrooms", "Parents & Teachers", "Principal Office", "One-on-one parent conferences to review term academic progress, attendance, and conduct.", "Scheduled"),
                ("EVT-104", "Inter-House Athletics & Track Meet", today + datetime.timedelta(days=25), "08:30:00", "14:00:00", "Sports", "School Sports Arena", "All Students", "Sports Director Joshi", "Track sprints, relay competitions, high jump, and trophy presentations.", "Scheduled"),
                ("EVT-105", "National Mathematics Olympiad Trials", today + datetime.timedelta(days=32), "11:00:00", "13:00:00", "Academic", "Seminar Hall 2", "High School (Grades 10-12)", "Dr. Rajesh Khanna", "Preliminary screening test for the regional mathematics olympiad.", "Scheduled")
            ]
            cur.executemany("""
                INSERT INTO School_Events (EVENT_CODE, TITLE, EVENT_DATE, START_TIME, END_TIME, CATEGORY, LOCATION, TARGET_AUDIENCE, ORGANIZER, DESCRIPTION, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, events)
            con.commit()
            print("Seeded School Events.")

        # 3. Seed PTM Meeting Slots
        cur.execute("SELECT COUNT(*) AS CNT FROM PTM_Meeting_Slots")
        if cur.fetchone()["CNT"] == 0:
            ptm_date = today + datetime.timedelta(days=18)
            slots = [
                ("SLT-201", "T-201", "Dr. Rajesh Khanna", "Mathematics", ptm_date, "09:30:00", "09:50:00", "In-Person (Campus)", "Room 101 - Math Wing", 1, "Booked", "Slot for Grade 10 calculus discussion."),
                ("SLT-202", "T-201", "Dr. Rajesh Khanna", "Mathematics", ptm_date, "10:00:00", "10:20:00", "In-Person (Campus)", "Room 101 - Math Wing", 1, "Available", "Open slot for parent consultation."),
                ("SLT-203", "T-201", "Dr. Rajesh Khanna", "Mathematics", ptm_date, "10:30:00", "10:50:00", "Virtual (Google Meet / Zoom)", "https://meet.google.com/pqr-edupulse-math", 1, "Available", "Virtual slot for working parents."),
                ("SLT-204", "T-202", "Prof. Sunita Menon", "Physics", ptm_date, "09:30:00", "09:50:00", "In-Person (Campus)", "Physics Lab Office", 1, "Booked", "Consultation regarding physics lab derivations."),
                ("SLT-205", "T-202", "Prof. Sunita Menon", "Physics", ptm_date, "10:00:00", "10:20:00", "In-Person (Campus)", "Physics Lab Office", 1, "Available", "Open slot for Grade 9/10 physics."),
                ("SLT-206", "T-204", "Dr. Meenakshi Rao", "Chemistry", ptm_date, "11:00:00", "11:20:00", "In-Person (Campus)", "Chemistry Staff Desk", 1, "Booked", "Chemistry coursework review."),
                ("SLT-207", "T-205", "Mr. Neeraj Joshi", "Computer Science", ptm_date, "11:30:00", "11:50:00", "Virtual (Google Meet / Zoom)", "https://meet.google.com/cs-edupulse-ptm", 1, "Available", "Virtual conference for Python & coding performance.")
            ]
            cur.executemany("""
                INSERT INTO PTM_Meeting_Slots (SLOT_CODE, TEACHER_ID, TEACHER_NAME, SUBJECT, MEETING_DATE, START_TIME, END_TIME, MEETING_MODE, ROOM_OR_LINK, MAX_CAPACITY, STATUS, NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, slots)
            con.commit()
            print("Seeded PTM Meeting Slots.")

        # 4. Seed PTM Bookings
        cur.execute("SELECT COUNT(*) AS CNT FROM PTM_Bookings")
        if cur.fetchone()["CNT"] == 0:
            bookings = [
                ("BKG-301", "SLT-201", "101", "Aarav Sharma", "Grade 10", "Sunil Sharma", "9876543201", "sunil.sharma@example.com", "Review calculus problem-solving speed and mid-term exam performance.", "Confirmed", True, datetime.datetime.now() - datetime.timedelta(hours=6), "Parent is keen on additional Olympiad problem sheets."),
                ("BKG-302", "SLT-204", "102", "Ananya Patel", "Grade 10", "Bhavin Patel", "9876543221", "bhavin.patel@example.com", "Discuss experimental physics lab notes and science expo project guidance.", "Confirmed", True, datetime.datetime.now() - datetime.timedelta(hours=4), "Student is performing exceptionally well in laboratory demonstrations."),
                ("BKG-303", "SLT-206", "103", "Rohan Mehta", "Grade 9", "Ramesh Mehta", "9876543231", "ramesh.mehta@example.com", "Consultation regarding organic reactions formula memorization and classroom focus.", "Confirmed", False, None, None)
            ]
            cur.executemany("""
                INSERT INTO PTM_Bookings (BOOKING_CODE, SLOT_CODE, STUDENT_ROLL, STUDENT_NAME, STUDENT_CLASS, PARENT_NAME, PARENT_PHONE, PARENT_EMAIL, DISCUSSION_TOPIC, STATUS, REMINDER_SENT, REMINDER_SENT_AT, TEACHER_FEEDBACK_NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, bookings)
            con.commit()
            print("Seeded PTM Bookings.")

        # 5. Seed Calendar Reminders
        cur.execute("SELECT COUNT(*) AS CNT FROM Calendar_Reminders")
        if cur.fetchone()["CNT"] == 0:
            reminders = [
                ("REM-401", "Upcoming PTM Meeting Reminder - Dr. Khanna", today + datetime.timedelta(days=17), "Specific Student / Parent", "101", "Sunil Sharma", "Reminder: You have a scheduled Parent-Teacher Meeting tomorrow at 09:30 AM with Dr. Rajesh Khanna in Room 101.", "Active", "SMS Alert"),
                ("REM-402", "Mid-Term Examination Hall Tickets Ready", today + datetime.timedelta(days=2), "All School", "ALL", "All Parents & Students", "Mid-Term examination begins in 3 days. Please ensure students carry authorized stationery and hall tickets.", "Active", "In-App Notification"),
                ("REM-403", "Diwali Vacation Campus Closure Notice", today + datetime.timedelta(days=5), "All School", "ALL", "School Community", "The school campus and administrative offices will remain closed from Nov 01 to Nov 05 for Diwali festivities.", "Active", "Email Notice")
            ]
            cur.executemany("""
                INSERT INTO Calendar_Reminders (REMINDER_CODE, TITLE, REMINDER_DATE, TARGET_TYPE, TARGET_ID, RECIPIENT_NAME, MESSAGE, STATUS, DELIVERY_CHANNEL)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, reminders)
            con.commit()
            print("Seeded Calendar Reminders.")

    except Error as e:
        print("Calendar & PTM Seed Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()


# --------------------------------- CLI FUNCTIONS ---------------------------------

def view_calendar_events_and_holidays():
    clear_screen()
    print("=" * 105)
    print("                     SCHOOL CALENDAR: UPCOMING EVENTS & HOLIDAYS")
    print("=" * 105)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        # Holidays
        print("\n[+] OFFICIAL SCHOOL HOLIDAYS & TERM BREAKS:")
        cur.execute("SELECT HOLIDAY_NAME, START_DATE, END_DATE, HOLIDAY_TYPE, DATEDIFF(END_DATE, START_DATE) + 1 AS DURATION FROM School_Holidays ORDER BY START_DATE ASC")
        hols = cur.fetchall()
        if not hols:
            print("No holidays scheduled.")
        else:
            table_hols = []
            for h in hols:
                table_hols.append([
                    h["HOLIDAY_NAME"][:25],
                    str(h["START_DATE"]),
                    str(h["END_DATE"]),
                    f"{h['DURATION']} day(s)",
                    h["HOLIDAY_TYPE"]
                ])
            print(tabulate(table_hols, headers=["Holiday Name", "Start Date", "End Date", "Duration", "Type"], tablefmt="fancy_grid"))

        # Events
        print("\n[+] SCHEDULED SCHOOL & ACADEMIC EVENTS:")
        cur.execute("SELECT EVENT_CODE, TITLE, EVENT_DATE, START_TIME, LOCATION, CATEGORY, TARGET_AUDIENCE, STATUS FROM School_Events ORDER BY EVENT_DATE ASC")
        evts = cur.fetchall()
        if not evts:
            print("No events scheduled.")
        else:
            table_evts = []
            for e in evts:
                t_str = str(e["START_TIME"])[:5] if e["START_TIME"] else "-"
                table_evts.append([
                    e["EVENT_CODE"],
                    e["TITLE"][:28],
                    str(e["EVENT_DATE"]),
                    t_str,
                    e["LOCATION"][:20],
                    e["CATEGORY"],
                    e["TARGET_AUDIENCE"][:20],
                    e["STATUS"]
                ])
            print(tabulate(table_evts, headers=["Code", "Event Title", "Date", "Time", "Location", "Category", "Audience", "Status"], tablefmt="fancy_grid"))

    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def add_school_holiday():
    clear_screen()
    print("=" * 80)
    print("                     ADD NEW SCHOOL HOLIDAY / VACATION")
    print("=" * 80)
    name = input("Holiday Name (e.g. Winter Vacation, Eid Break): ").strip()
    if not name:
        print("Holiday name is required.")
        pause_and_clear()
        return

    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    end_date = input("End Date (YYYY-MM-DD): ").strip() or start_date
    if not start_date:
        print("Start date is required.")
        pause_and_clear()
        return

    print("\nHoliday Types:")
    print("1. Gazetted Holiday   2. National Holiday   3. Term Break   4. Restricted Holiday")
    t_opt = input("Choice [1]: ").strip()
    types_map = {"1": "Gazetted Holiday", "2": "National Holiday", "3": "Term Break", "4": "Restricted Holiday"}
    holiday_type = types_map.get(t_opt, "Gazetted Holiday")

    description = input("Description / Circular note: ").strip()

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO School_Holidays (HOLIDAY_NAME, START_DATE, END_DATE, HOLIDAY_TYPE, DESCRIPTION, IS_ACADEMIC_OFF)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (name, start_date, end_date, holiday_type, description))
        con.commit()
        print(f"\n[SUCCESS] Holiday '{name}' added to school calendar successfully!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def add_school_event():
    clear_screen()
    print("=" * 85)
    print("                        CREATE NEW SCHOOL EVENT")
    print("=" * 85)
    title = input("Event Title (e.g. Annual Sports Day): ").strip()
    if not title:
        print("Title is required.")
        pause_and_clear()
        return

    event_date = input("Event Date (YYYY-MM-DD): ").strip()
    if not event_date:
        print("Event date is required.")
        pause_and_clear()
        return

    start_time = input("Start Time (HH:MM) [09:00]: ").strip() or "09:00:00"
    end_time = input("End Time (HH:MM) [12:00]: ").strip() or "12:00:00"

    print("\nEvent Categories:")
    print("1. Academic   2. Examination   3. Sports   4. Cultural   5. Meeting   6. Exhibition")
    c_opt = input("Choice [1]: ").strip()
    cats_map = {"1": "Academic", "2": "Examination", "3": "Sports", "4": "Cultural", "5": "Meeting", "6": "Exhibition"}
    category = cats_map.get(c_opt, "Academic")

    location = input("Campus Location [Main Auditorium]: ").strip() or "Main Auditorium"
    organizer = input("Organizer / Department: ").strip() or "Faculty Council"
    description = input("Event Description / Agenda: ").strip()

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT MAX(ID) AS MAX_ID FROM School_Events")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 101
        event_code = f"EVT-{next_num}"

        cur.execute("""
            INSERT INTO School_Events (EVENT_CODE, TITLE, EVENT_DATE, START_TIME, END_TIME, CATEGORY, LOCATION, TARGET_AUDIENCE, ORGANIZER, DESCRIPTION, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'All Students', %s, %s, 'Scheduled')
        """, (event_code, title, event_date, start_time, end_time, category, location, organizer, description))
        con.commit()
        print(f"\n[SUCCESS] School event '{title}' scheduled as {event_code}!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_meeting_slots():
    clear_screen()
    print("=" * 110)
    print("                     PARENT-TEACHER MEETING (PTM) SLOTS")
    print("=" * 110)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT SLOT_CODE, TEACHER_NAME, SUBJECT, MEETING_DATE, START_TIME, END_TIME, MEETING_MODE, ROOM_OR_LINK, STATUS FROM PTM_Meeting_Slots ORDER BY MEETING_DATE ASC, START_TIME ASC")
        slots = cur.fetchall()
        if not slots:
            print("No meeting slots available.")
        else:
            table_slots = []
            for s in slots:
                time_range = f"{str(s['START_TIME'])[:5]} - {str(s['END_TIME'])[:5]}"
                table_slots.append([
                    s["SLOT_CODE"],
                    s["TEACHER_NAME"][:20],
                    s["SUBJECT"][:15],
                    str(s["MEETING_DATE"]),
                    time_range,
                    s["MEETING_MODE"][:18],
                    s["ROOM_OR_LINK"][:25],
                    s["STATUS"]
                ])
            print(tabulate(table_slots, headers=["Slot #", "Teacher", "Subject", "Date", "Time Range", "Mode", "Room / Link", "Status"], tablefmt="fancy_grid"))
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def create_meeting_slot():
    clear_screen()
    print("=" * 85)
    print("                 CREATE PTM CONSULTATION MEETING SLOT")
    print("=" * 85)
    tid = input("Enter Teacher ID (e.g. T-201): ").strip()
    if not tid:
        print("Teacher ID is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT NAME, SUBJECT FROM Teachers_Details WHERE TEACHER_ID = %s", (tid,))
        teacher = cur.fetchone()
        if not teacher:
            print(f"Teacher with ID {tid} not found.")
            pause_and_clear()
            return

        t_name = teacher["NAME"]
        t_subj = teacher["SUBJECT"]
        print(f"Teacher: {t_name} ({t_subj})")

        m_date = input("Meeting Date (YYYY-MM-DD): ").strip()
        if not m_date:
            print("Date is required.")
            pause_and_clear()
            return

        s_time = input("Start Time (HH:MM) [10:00]: ").strip() or "10:00:00"
        e_time = input("End Time (HH:MM) [10:20]: ").strip() or "10:20:00"

        print("\nMeeting Mode:")
        print("1. In-Person (Campus)   2. Virtual (Google Meet / Zoom)   3. Phone Call")
        m_opt = input("Choice [1]: ").strip()
        modes_map = {"1": "In-Person (Campus)", "2": "Virtual (Google Meet / Zoom)", "3": "Phone Call"}
        mode = modes_map.get(m_opt, "In-Person (Campus)")

        room_or_link = input("Room or Virtual Meeting Link: ").strip() or "Staff Consultation Room"

        cur.execute("SELECT MAX(ID) AS MAX_ID FROM PTM_Meeting_Slots")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 201
        slot_code = f"SLT-{next_num}"

        cur.execute("""
            INSERT INTO PTM_Meeting_Slots (SLOT_CODE, TEACHER_ID, TEACHER_NAME, SUBJECT, MEETING_DATE, START_TIME, END_TIME, MEETING_MODE, ROOM_OR_LINK, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available')
        """, (slot_code, tid, t_name, t_subj, m_date, s_time, e_time, mode, room_or_link))
        con.commit()
        print(f"\n[SUCCESS] Meeting slot {slot_code} created for {t_name} on {m_date} ({s_time} - {e_time})!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def book_meeting_slot():
    clear_screen()
    print("=" * 85)
    print("                    BOOK PTM CONSULTATION SLOT")
    print("=" * 85)
    slot_code = input("Enter Available Slot Code (e.g. SLT-202): ").strip().upper()
    if not slot_code:
        print("Slot code is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM PTM_Meeting_Slots WHERE SLOT_CODE = %s AND STATUS = 'Available'", (slot_code,))
        slot = cur.fetchone()
        if not slot:
            print(f"Slot {slot_code} is not available for booking.")
            pause_and_clear()
            return

        print(f"Booking Slot: {slot['SLOT_CODE']} with {slot['TEACHER_NAME']} ({slot['SUBJECT']}) on {slot['MEETING_DATE']}")

        roll = input("Enter Student Roll Number: ").strip()
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        st = cur.fetchone()
        if not st:
            print(f"Student with Roll Number {roll} not found.")
            pause_and_clear()
            return

        st_name = st["NAME"]
        st_class = st["CLASS"]
        print(f"Student: {st_name} ({st_class})")

        # Check parent details for auto-fill
        cur.execute("SELECT FATHER_NAME, PRIMARY_CONTACT, EMAIL FROM Parents_Details WHERE ROLL_NUMBER = %s", (roll,))
        parent = cur.fetchone()

        default_p_name = parent["FATHER_NAME"] if parent else "Parent"
        default_p_phone = parent["PRIMARY_CONTACT"] if parent else "9876543210"
        default_p_email = parent["EMAIL"] if parent else "parent@example.com"

        p_name = input(f"Parent / Guardian Name [{default_p_name}]: ").strip() or default_p_name
        p_phone = input(f"Contact Phone [{default_p_phone}]: ").strip() or default_p_phone
        p_email = input(f"Email [{default_p_email}]: ").strip() or default_p_email
        topic = input("Discussion Agenda / Key Inquiries: ").strip()
        if not topic:
            topic = "General academic progress and classroom engagement review."

        cur.execute("SELECT MAX(ID) AS MAX_ID FROM PTM_Bookings")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 301
        bkg_code = f"BKG-{next_num}"

        cur.execute("""
            INSERT INTO PTM_Bookings (BOOKING_CODE, SLOT_CODE, STUDENT_ROLL, STUDENT_NAME, STUDENT_CLASS, PARENT_NAME, PARENT_PHONE, PARENT_EMAIL, DISCUSSION_TOPIC, STATUS, REMINDER_SENT)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', FALSE)
        """, (bkg_code, slot_code, roll, st_name, st_class, p_name, p_phone, p_email, topic))

        # Mark slot as booked
        cur.execute("UPDATE PTM_Meeting_Slots SET STATUS = 'Booked' WHERE SLOT_CODE = %s", (slot_code,))
        con.commit()
        print(f"\n[SUCCESS] Meeting confirmed! Booking Code: {bkg_code}")
        print(f"Appointment with {slot['TEACHER_NAME']} on {slot['MEETING_DATE']} ({slot['START_TIME']} - {slot['END_TIME']}).")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_ptm_bookings():
    clear_screen()
    print("=" * 115)
    print("                     CONFIRMED PTM APPOINTMENT BOOKINGS")
    print("=" * 115)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT b.BOOKING_CODE, b.SLOT_CODE, b.STUDENT_ROLL, b.STUDENT_NAME, b.PARENT_NAME, b.PARENT_PHONE,
                   s.TEACHER_NAME, s.SUBJECT, s.MEETING_DATE, s.START_TIME, s.MEETING_MODE, b.STATUS, b.REMINDER_SENT
            FROM PTM_Bookings b
            JOIN PTM_Meeting_Slots s ON b.SLOT_CODE = s.SLOT_CODE
            ORDER BY s.MEETING_DATE ASC, s.START_TIME ASC
        """)
        rows = cur.fetchall()
        if not rows:
            print("No PTM bookings found.")
        else:
            table_bkgs = []
            for r in rows:
                rem_str = "Sent" if r["REMINDER_SENT"] else "Pending"
                table_bkgs.append([
                    r["BOOKING_CODE"],
                    f"{r['STUDENT_NAME'][:15]} ({r['STUDENT_ROLL']})",
                    r["PARENT_NAME"][:15],
                    r["TEACHER_NAME"][:16],
                    r["SUBJECT"][:12],
                    f"{r['MEETING_DATE']} {str(r['START_TIME'])[:5]}",
                    r["MEETING_MODE"][:16],
                    r["STATUS"],
                    rem_str
                ])
            print(tabulate(table_bkgs, headers=["Booking #", "Student", "Parent", "Teacher", "Subject", "Date & Time", "Mode", "Status", "Reminder"], tablefmt="fancy_grid"))
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_and_send_reminders():
    clear_screen()
    print("=" * 105)
    print("                      CALENDAR & PTM REMINDERS HUB")
    print("=" * 105)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT REMINDER_CODE, TITLE, REMINDER_DATE, TARGET_TYPE, RECIPIENT_NAME, MESSAGE, DELIVERY_CHANNEL, STATUS FROM Calendar_Reminders ORDER BY ID DESC")
        rows = cur.fetchall()
        if not rows:
            print("No reminders active.")
        else:
            table_rem = []
            for r in rows:
                table_rem.append([
                    r["REMINDER_CODE"],
                    r["TITLE"][:25],
                    str(r["REMINDER_DATE"]),
                    r["TARGET_TYPE"][:15],
                    r["RECIPIENT_NAME"][:18] or "All",
                    r["MESSAGE"][:30],
                    r["DELIVERY_CHANNEL"],
                    r["STATUS"]
                ])
            print(tabulate(table_rem, headers=["Code", "Title", "Date", "Target", "Recipient", "Notice Message", "Channel", "Status"], tablefmt="fancy_grid"))

        print("\nOptions:")
        print("1. Send / Dispatch Automated Reminders for Upcoming PTMs")
        print("2. Create New Custom Calendar Reminder")
        print("0. Return to Menu")
        c = input("\nEnter choice: ").strip()
        if c == "1":
            cur.execute("""
                UPDATE PTM_Bookings
                SET REMINDER_SENT = TRUE, REMINDER_SENT_AT = NOW()
                WHERE STATUS = 'Confirmed' AND REMINDER_SENT = FALSE
            """)
            con.commit()
            print("\n[SUCCESS] Automated meeting reminder dispatches completed for all confirmed bookings!")
        elif c == "2":
            title = input("Reminder Title: ").strip()
            r_date = input("Alert Date (YYYY-MM-DD): ").strip()
            msg = input("Reminder Notice Body: ").strip()
            if title and r_date and msg:
                cur.execute("SELECT MAX(ID) AS MAX_ID FROM Calendar_Reminders")
                row = cur.fetchone()
                next_num = (row["MAX_ID"] or 0) + 401
                rem_code = f"REM-{next_num}"
                cur.execute("""
                    INSERT INTO Calendar_Reminders (REMINDER_CODE, TITLE, REMINDER_DATE, TARGET_TYPE, TARGET_ID, RECIPIENT_NAME, MESSAGE, STATUS, DELIVERY_CHANNEL)
                    VALUES (%s, %s, %s, 'All School', 'ALL', 'School Community', %s, 'Active', 'In-App Notification')
                """, (rem_code, title, r_date, msg))
                con.commit()
                print(f"\n[SUCCESS] Reminder notice {rem_code} created!")
            else:
                print("Incomplete fields; reminder not created.")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


# --------------------------------- CLI MAIN MENU ---------------------------------

def calendar_ptm_menu():
    create_calendar_ptm_tables()
    seed_calendar_ptm_data()
    while True:
        clear_screen()
        print("\n" + "=" * 80)
        print("      SCHOOL CALENDAR & PARENT-TEACHER MEETINGS (PTM) SYSTEM".center(80))
        print("      (Holidays, School Events, Meeting Slots & Booking Engine)".center(80))
        print("=" * 80)
        print("1. View School Calendar Events & Holidays".center(80))
        print("2. Add School Holiday / Vacation".center(80))
        print("3. Schedule New School Event".center(80))
        print("4. View PTM Consultation Meeting Slots".center(80))
        print("5. Create Teacher PTM Meeting Slot".center(80))
        print("6. Book PTM Meeting Slot (Parents / Students)".center(80))
        print("7. View Confirmed PTM Bookings".center(80))
        print("8. Calendar & PTM Reminders Hub".center(80))
        print("0. Return to Main Menu".center(80))
        print("=" * 80)

        choice = input("\nEnter choice : : ").strip()
        if choice == "1":
            view_calendar_events_and_holidays()
        elif choice == "2":
            add_school_holiday()
        elif choice == "3":
            add_school_event()
        elif choice == "4":
            view_meeting_slots()
        elif choice == "5":
            create_meeting_slot()
        elif choice == "6":
            book_meeting_slot()
        elif choice == "7":
            view_ptm_bookings()
        elif choice == "8":
            view_and_send_reminders()
        elif choice == "0":
            break
        else:
            print("Invalid Choice, Try Again!")
            pause_and_clear()


if __name__ == "__main__":
    calendar_ptm_menu()
