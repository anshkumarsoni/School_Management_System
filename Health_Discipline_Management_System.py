# -------------------------------------------------------------------------
# STUDENT HEALTH & DISCIPLINE MANAGEMENT SYSTEM
# Medical-Room Visits, Health Profiles, Behaviour Incidents & Follow-ups
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

def create_health_discipline_tables():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed!")
            return
        cur = con.cursor()

        # 1. Student Health Profiles (Restricted Access)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Student_Health_Profiles (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                ROLL_NUMBER VARCHAR(20) UNIQUE NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                BLOOD_GROUP VARCHAR(10) DEFAULT 'Unknown',
                ALLERGIES TEXT NULL,
                CHRONIC_CONDITIONS TEXT NULL,
                MEDICATIONS TEXT NULL,
                EMERGENCY_DOCTOR_NAME VARCHAR(100) NULL,
                EMERGENCY_DOCTOR_PHONE VARCHAR(20) NULL,
                INSURANCE_POLICY_NO VARCHAR(50) NULL,
                SPECIAL_CARE_INSTRUCTIONS TEXT NULL,
                VACCINATION_STATUS ENUM('Up to Date', 'Partially Vaccinated', 'Pending Records') DEFAULT 'Up to Date',
                RESTRICTED_ACCESS BOOLEAN DEFAULT TRUE,
                LAST_UPDATED TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # 2. Medical Room Visits (Clinic / Infirmary Log)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Medical_Room_Visits (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                VISIT_CODE VARCHAR(30) UNIQUE NOT NULL,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                VISIT_DATE DATE NOT NULL,
                VISIT_TIME TIME NOT NULL,
                SYMPTOMS TEXT NOT NULL,
                DIAGNOSIS_OBSERVATION TEXT NULL,
                TREATMENT_GIVEN TEXT NOT NULL,
                ATTENDING_STAFF VARCHAR(100) NOT NULL,
                PARENT_NOTIFIED ENUM('Yes', 'No', 'Attempted / No Answer') DEFAULT 'No',
                OUTCOME ENUM('Returned to Class', 'Sent Home with Parent', 'Referred to Hospital', 'Admitted to Medical Bay') NOT NULL DEFAULT 'Returned to Class',
                CONFIDENTIAL_NOTES TEXT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Behaviour / Discipline Incidents
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Discipline_Incidents (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                INCIDENT_CODE VARCHAR(30) UNIQUE NOT NULL,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                CLASS VARCHAR(50) NOT NULL,
                INCIDENT_DATE DATE NOT NULL,
                CATEGORY ENUM('Disruptive Behaviour', 'Academic Dishonesty', 'Bullying / Harassment', 'Vandalism / Property Damage', 'Late Attendance / Truancy', 'Uniform / Dress Code Violation', 'Physical Altercation', 'Substance Abuse', 'Other') NOT NULL DEFAULT 'Disruptive Behaviour',
                SEVERITY ENUM('Minor', 'Moderate', 'Major', 'Critical') NOT NULL DEFAULT 'Minor',
                LOCATION VARCHAR(100) DEFAULT 'Classroom',
                REPORTED_BY VARCHAR(100) NOT NULL,
                DESCRIPTION TEXT NOT NULL,
                WITNESSES VARCHAR(200) NULL,
                STATUS ENUM('Reported', 'Under Investigation', 'Action Pending', 'Follow-up Scheduled', 'Resolved', 'Closed') DEFAULT 'Reported',
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Follow-up Actions & Interventions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Discipline_Followups (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                FOLLOWUP_CODE VARCHAR(30) UNIQUE NOT NULL,
                INCIDENT_CODE VARCHAR(30) NOT NULL,
                ROLL_NUMBER VARCHAR(20) NOT NULL,
                STUDENT_NAME VARCHAR(100) NOT NULL,
                ACTION_TYPE ENUM('Verbal Counseling', 'Written Warning', 'Parent-Teacher Meeting', 'Student Counselor Session', 'After-School Detention', 'Campus Community Service', 'Suspension (Short-term)', 'Behavioral Contract') NOT NULL DEFAULT 'Verbal Counseling',
                ASSIGNED_TO VARCHAR(100) NOT NULL,
                SCHEDULED_DATE DATE NOT NULL,
                COMPLETION_DATE DATE NULL,
                STATUS ENUM('Scheduled', 'In Progress', 'Completed', 'Escalated') DEFAULT 'Scheduled',
                OUTCOME_NOTES TEXT NULL,
                PARENT_ACKNOWLEDGED BOOLEAN DEFAULT FALSE,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.commit()
    except Error as e:
        print("Health & Discipline Tables Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()


# --------------------------------- STARTER SEED DATA ---------------------------------

def seed_health_discipline_data():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            return
        cur = con.cursor(dictionary=True)

        # 1. Seed Health Profiles
        cur.execute("SELECT COUNT(*) AS CNT FROM Student_Health_Profiles")
        if cur.fetchone()["CNT"] == 0:
            profiles = [
                ("101", "Aarav Sharma", "Grade 10", "B+", "Peanuts, Dust mites", "Mild Asthma", "Salbutamol Inhaler (PRN)", "Dr. S. K. Kapoor", "9876501122", "MAX-HLTH-9921", "Keep inhaler in school bag during sports; avoid strenuous outdoor runs on high pollen days.", "Up to Date"),
                ("102", "Ananya Patel", "Grade 10", "O+", "None", "None", "None", "Dr. Meera Nambiar", "9876502233", "STAR-MED-3341", "Front bench seating recommended for mild astigmatism.", "Up to Date"),
                ("103", "Rohan Mehta", "Grade 9", "A+", "Penicillin, Shellfish", "None", "None", "Dr. Rajesh Gupta", "9876503344", "HDFC-ERGO-7712", "Allergic to Penicillin antibiotics; alert infirmary during prescription.", "Up to Date"),
                ("104", "Pooja Iyer", "Grade 11", "AB+", "Latex", "Type 1 Diabetes Mellitus", "Insulin glargine (morning)", "Dr. Arvind Swaminathan", "9876504455", "ICICI-LOMB-8823", "Carries glucometer; permitted to have glucose biscuits/juice in class if feeling dizzy.", "Up to Date"),
                ("105", "Vikram Singh", "Grade 12", "O-", "Sulfa drugs", "None", "None", "Dr. Sunita Bansal", "9876505566", "CARE-HLTH-1190", "Universal blood donor (O-); sports team captain (football).", "Up to Date"),
                ("106", "Sneha Kulkarni", "Grade 9", "B-", "Pollen, Seasonal rhinitis", "None", "Cetirizine 5mg (seasonal)", "Dr. Aniket Joshi", "9876506677", "REL-GEN-4432", "Keep antihistamine in medical room during spring season.", "Up to Date"),
                ("107", "Aditya Verma", "Grade 8", "A-", "None", "None", "None", "Dr. Vinod Batra", "9876507788", "NIV-BUPA-6611", "Annual dental checkup up to date.", "Up to Date"),
                ("108", "Diya Sen", "Grade 11", "AB-", "Dairy / Lactose Intolerance", "Migraines (mild)", "None", "Dr. Shalini Roy", "9876508899", "TATA-AIG-5509", "Allow 15 min quiet rest in medical bay during intense headaches.", "Up to Date")
            ]
            cur.executemany("""
                INSERT INTO Student_Health_Profiles 
                (ROLL_NUMBER, STUDENT_NAME, CLASS, BLOOD_GROUP, ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS, EMERGENCY_DOCTOR_NAME, EMERGENCY_DOCTOR_PHONE, INSURANCE_POLICY_NO, SPECIAL_CARE_INSTRUCTIONS, VACCINATION_STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, profiles)
            con.commit()
            print("Seeded Student Health Profiles.")

        # 2. Seed Medical Room Visits
        cur.execute("SELECT COUNT(*) AS CNT FROM Medical_Room_Visits")
        if cur.fetchone()["CNT"] == 0:
            today = datetime.date.today()
            visits = [
                ("MED-101", "101", "Aarav Sharma", "Grade 10", today - datetime.timedelta(days=4), "11:20:00", "Shortness of breath and wheezing after 400m race", "Exercise-induced bronchospasm (Mild asthma flare-up)", "2 puffs of Salbutamol administered; student rested for 25 mins; vitals stabilized SpO2 99%", "Nurse Anita Roy", "Yes", "Returned to Class", "Student felt much better after nebulization rest; reminded to take inhaler prior to PE."),
                ("MED-102", "103", "Rohan Mehta", "Grade 9", today - datetime.timedelta(days=3), "14:15:00", "Blunt trauma and mild swelling to left wrist during basketball scrimmage", "Suspected grade-1 ligament strain left carpal area", "Cold gel ice compress applied for 20 mins; crepe bandage support wrapped; paracetamol 500mg given", "Dr. Meenakshi Rao", "Yes", "Sent Home with Parent", "Parent Bhavin Mehta came to pick up; advised orthopaedic X-ray to rule out hairline fracture."),
                ("MED-103", "104", "Pooja Iyer", "Grade 11", today - datetime.timedelta(days=2), "10:05:00", "Mild dizziness, perspiration, blood sugar dipped to 68 mg/dL", "Hypoglycemia (Type 1 Diabetes)", "Administered 150ml apple juice and 2 glucose biscuits; re-tested blood sugar at 20 mins: 104 mg/dL", "Nurse Anita Roy", "Yes", "Returned to Class", "Advised student to maintain mid-morning snack schedule; informed class teacher."),
                ("MED-104", "105", "Vikram Singh", "Grade 12", today - datetime.timedelta(days=1), "13:30:00", "Throat irritation, low-grade fever (99.8°F), slight headache", "Acute viral pharyngitis (early stage)", "Warm saline gargle provided; oral paracetamol 650mg administered; temperature checked", "Nurse Anita Roy", "No", "Returned to Class", "Advised plenty of fluids; will follow up if temperature exceeds 101°F tomorrow."),
                ("MED-105", "108", "Diya Sen", "Grade 11", today, "09:40:00", "Severe throbbing headache with photophobia and mild nausea", "Acute Migraine headache attack", "Rest in dark quiet medical bay for 45 mins; oral hydration; menthol balm applied", "Nurse Anita Roy", "Yes", "Admitted to Medical Bay", "Resting comfortably under observation; mother notified via phone.")
            ]
            cur.executemany("""
                INSERT INTO Medical_Room_Visits 
                (VISIT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, VISIT_DATE, VISIT_TIME, SYMPTOMS, DIAGNOSIS_OBSERVATION, TREATMENT_GIVEN, ATTENDING_STAFF, PARENT_NOTIFIED, OUTCOME, CONFIDENTIAL_NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, visits)
            con.commit()
            print("Seeded Medical Room Visits.")

        # 3. Seed Discipline Incidents
        cur.execute("SELECT COUNT(*) AS CNT FROM Discipline_Incidents")
        if cur.fetchone()["CNT"] == 0:
            today = datetime.date.today()
            incidents = [
                ("DIS-201", "103", "Rohan Mehta", "Grade 9", today - datetime.timedelta(days=8), "Disruptive Behaviour", "Minor", "Classroom 9-B", "Prof. Sunita Menon", "Repeatedly interrupted physics lecture by making disruptive sound effects and distracting neighbouring desks.", "Aarav Sharma, Ananya Patel", "Resolved"),
                ("DIS-202", "105", "Vikram Singh", "Grade 12", today - datetime.timedelta(days=5), "Late Attendance / Truancy", "Moderate", "Campus Main Gate", "Mr. Neeraj Joshi", "Arrived 40 minutes late to school for the 3rd consecutive Friday without written parent leave or bus delay note.", "Gate Security Guard", "Follow-up Scheduled"),
                ("DIS-203", "107", "Aditya Verma", "Grade 8", today - datetime.timedelta(days=3), "Bullying / Harassment", "Major", "Junior Corridor", "Ms. Priya Deshmukh", "Intimidated a Grade 7 junior student during recess and took their art supplies without consent.", "Tanvi Reddy, Kabir Das", "Under Investigation"),
                ("DIS-204", "109", "Kabir Das", "Grade 12", today - datetime.timedelta(days=1), "Academic Dishonesty", "Major", "Chemistry Laboratory", "Dr. Meenakshi Rao", "Caught with unauthorized formula cheat-sheet concealed inside lab workbook during mid-term practical viva.", "Lab Assistant Sharma", "Action Pending")
            ]
            cur.executemany("""
                INSERT INTO Discipline_Incidents 
                (INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, INCIDENT_DATE, CATEGORY, SEVERITY, LOCATION, REPORTED_BY, DESCRIPTION, WITNESSES, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, incidents)
            con.commit()
            print("Seeded Discipline Incidents.")

        # 4. Seed Discipline Follow-ups
        cur.execute("SELECT COUNT(*) AS CNT FROM Discipline_Followups")
        if cur.fetchone()["CNT"] == 0:
            today = datetime.date.today()
            followups = [
                ("FOL-301", "DIS-201", "103", "Rohan Mehta", "Verbal Counseling", "Prof. Sunita Menon", today - datetime.timedelta(days=7), today - datetime.timedelta(days=7), "Completed", "Student acknowledged classroom disturbance, apologized to the teacher, and promised full focus in lectures.", True),
                ("FOL-302", "DIS-202", "105", "Vikram Singh", "Parent-Teacher Meeting", "Mr. Neeraj Joshi", today + datetime.timedelta(days=2), None, "Scheduled", "Conference scheduled with father Mr. Rajendra Singh to address repetitive morning attendance tardiness.", True),
                ("FOL-303", "DIS-203", "107", "Aditya Verma", "Student Counselor Session", "School Counselor Mrs. Shalini", today + datetime.timedelta(days=1), None, "Scheduled", "Structured behavioral counseling session to understand peer conflicts and cultivate empathy; returned seized supplies.", False),
                ("FOL-304", "DIS-204", "109", "Kabir Das", "Behavioral Contract", "Principal Dr. Rajesh Khanna", today + datetime.timedelta(days=3), None, "Scheduled", "Disciplinary board review with student and parents to sign zero-tolerance academic honesty undertaking.", True)
            ]
            cur.executemany("""
                INSERT INTO Discipline_Followups 
                (FOLLOWUP_CODE, INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, ACTION_TYPE, ASSIGNED_TO, SCHEDULED_DATE, COMPLETION_DATE, STATUS, OUTCOME_NOTES, PARENT_ACKNOWLEDGED)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, followups)
            con.commit()
            print("Seeded Discipline Follow-ups.")

    except Error as e:
        print("Health & Discipline Seed Error:", e)
    finally:
        if con and con.is_connected():
            cur.close()
            con.close()


# --------------------------------- CLI FUNCTIONS ---------------------------------

def view_health_profiles():
    clear_screen()
    print("=" * 105)
    print("                       STUDENT HEALTH PROFILES (RESTRICTED ACCESS)")
    print("=" * 105)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT ROLL_NUMBER, STUDENT_NAME, CLASS, BLOOD_GROUP, ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS, EMERGENCY_DOCTOR_PHONE FROM Student_Health_Profiles ORDER BY ROLL_NUMBER ASC")
        rows = cur.fetchall()
        if not rows:
            print("No health profiles found.")
        else:
            table_data = []
            for r in rows:
                table_data.append([
                    r["ROLL_NUMBER"],
                    r["STUDENT_NAME"][:18],
                    r["CLASS"],
                    r["BLOOD_GROUP"],
                    (r["ALLERGIES"] or "None")[:22],
                    (r["CHRONIC_CONDITIONS"] or "None")[:22],
                    (r["MEDICATIONS"] or "None")[:20],
                    r["EMERGENCY_DOCTOR_PHONE"] or "-"
                ])
            headers = ["Roll #", "Student Name", "Class", "Blood", "Allergies", "Chronic Cond.", "Medications", "Doctor Ph."]
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    except Error as e:
        print("Error fetching health profiles:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def add_or_update_health_profile():
    clear_screen()
    print("=" * 90)
    print("               ADD / UPDATE STUDENT HEALTH PROFILE")
    print("=" * 90)
    roll = input("Enter Student Roll Number: ").strip()
    if not roll:
        print("Roll number is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        # Check student exists in Students_Details
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        st = cur.fetchone()
        if not st:
            print(f"Student with Roll Number {roll} not found in student registry!")
            pause_and_clear()
            return

        name = st["NAME"]
        cls = st["CLASS"]
        print(f"Student: {name} ({cls})")

        # Check if profile already exists
        cur.execute("SELECT * FROM Student_Health_Profiles WHERE ROLL_NUMBER = %s", (roll,))
        existing = cur.fetchone()

        blood_group = input(f"Blood Group [{existing['BLOOD_GROUP'] if existing else 'Unknown'}]: ").strip() or (existing['BLOOD_GROUP'] if existing else "Unknown")
        allergies = input(f"Allergies [{existing['ALLERGIES'] if existing else 'None'}]: ").strip() or (existing['ALLERGIES'] if existing else "None")
        chronic = input(f"Chronic Conditions [{existing['CHRONIC_CONDITIONS'] if existing else 'None'}]: ").strip() or (existing['CHRONIC_CONDITIONS'] if existing else "None")
        medications = input(f"Current Medications [{existing['MEDICATIONS'] if existing else 'None'}]: ").strip() or (existing['MEDICATIONS'] if existing else "None")
        doc_name = input(f"Emergency Doctor Name [{existing['EMERGENCY_DOCTOR_NAME'] if existing else 'Dr. Clinic'}]: ").strip() or (existing['EMERGENCY_DOCTOR_NAME'] if existing else "Dr. Clinic")
        doc_phone = input(f"Emergency Doctor Phone [{existing['EMERGENCY_DOCTOR_PHONE'] if existing else '9876543210'}]: ").strip() or (existing['EMERGENCY_DOCTOR_PHONE'] if existing else "9876543210")
        insurance = input(f"Insurance Policy No [{existing['INSURANCE_POLICY_NO'] if existing else 'N/A'}]: ").strip() or (existing['INSURANCE_POLICY_NO'] if existing else "N/A")
        special_care = input(f"Special Care Instructions [{existing['SPECIAL_CARE_INSTRUCTIONS'] if existing else 'None'}]: ").strip() or (existing['SPECIAL_CARE_INSTRUCTIONS'] if existing else "None")

        if existing:
            cur.execute("""
                UPDATE Student_Health_Profiles
                SET BLOOD_GROUP = %s, ALLERGIES = %s, CHRONIC_CONDITIONS = %s, MEDICATIONS = %s,
                    EMERGENCY_DOCTOR_NAME = %s, EMERGENCY_DOCTOR_PHONE = %s, INSURANCE_POLICY_NO = %s,
                    SPECIAL_CARE_INSTRUCTIONS = %s
                WHERE ROLL_NUMBER = %s
            """, (blood_group, allergies, chronic, medications, doc_name, doc_phone, insurance, special_care, roll))
            print(f"\n[SUCCESS] Health profile updated for {name} ({roll})!")
        else:
            cur.execute("""
                INSERT INTO Student_Health_Profiles
                (ROLL_NUMBER, STUDENT_NAME, CLASS, BLOOD_GROUP, ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS, EMERGENCY_DOCTOR_NAME, EMERGENCY_DOCTOR_PHONE, INSURANCE_POLICY_NO, SPECIAL_CARE_INSTRUCTIONS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (roll, name, cls, blood_group, allergies, chronic, medications, doc_name, doc_phone, insurance, special_care))
            print(f"\n[SUCCESS] Health profile created for {name} ({roll})!")

        con.commit()
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_medical_visits():
    clear_screen()
    print("=" * 110)
    print("                        RESTRICTED MEDICAL-ROOM / CLINIC VISITS LOG")
    print("=" * 110)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT VISIT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, VISIT_DATE, VISIT_TIME, SYMPTOMS, TREATMENT_GIVEN, ATTENDING_STAFF, PARENT_NOTIFIED, OUTCOME FROM Medical_Room_Visits ORDER BY ID DESC")
        rows = cur.fetchall()
        if not rows:
            print("No medical visits recorded.")
        else:
            table_data = []
            for r in rows:
                time_str = str(r["VISIT_TIME"])[:5] if r["VISIT_TIME"] else ""
                table_data.append([
                    r["VISIT_CODE"],
                    f"{r['STUDENT_NAME'][:15]} ({r['ROLL_NUMBER']})",
                    r["CLASS"],
                    f"{r['VISIT_DATE']} {time_str}",
                    r["SYMPTOMS"][:22],
                    r["TREATMENT_GIVEN"][:22],
                    r["ATTENDING_STAFF"][:15],
                    r["PARENT_NOTIFIED"],
                    r["OUTCOME"][:18]
                ])
            headers = ["Code", "Student", "Class", "Date & Time", "Symptoms", "Treatment", "Attending", "Parent Notif.", "Outcome"]
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    except Error as e:
        print("Error fetching medical visits:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def log_medical_visit():
    clear_screen()
    print("=" * 90)
    print("                  RECORD MEDICAL-ROOM VISIT (INFIRMARY)")
    print("=" * 90)
    roll = input("Enter Student Roll Number: ").strip()
    if not roll:
        print("Roll number is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        st = cur.fetchone()
        if not st:
            print(f"Student with Roll Number {roll} not found.")
            pause_and_clear()
            return

        name = st["NAME"]
        cls = st["CLASS"]
        print(f"Patient: {name} ({cls})")

        symptoms = input("Observed Symptoms / Complaint: ").strip()
        diagnosis = input("Preliminary Diagnosis / Observation: ").strip()
        treatment = input("Treatment Given (Medication, ice compress, rest, etc.): ").strip()
        attending = input("Attending Staff / Nurse: ").strip() or "Nurse Anita Roy"
        
        print("\nParent Notified Options:")
        print("1. Yes  2. No  3. Attempted / No Answer")
        p_opt = input("Choice [1]: ").strip()
        parent_notified = "Yes" if p_opt == "1" else ("Attempted / No Answer" if p_opt == "3" else "No")

        print("\nVisit Outcome:")
        print("1. Returned to Class")
        print("2. Sent Home with Parent")
        print("3. Referred to Hospital")
        print("4. Admitted to Medical Bay")
        out_opt = input("Choice [1]: ").strip()
        outcomes_map = {
            "1": "Returned to Class",
            "2": "Sent Home with Parent",
            "3": "Referred to Hospital",
            "4": "Admitted to Medical Bay"
        }
        outcome = outcomes_map.get(out_opt, "Returned to Class")
        conf_notes = input("Confidential Medical Remarks: ").strip()

        # Generate visit code
        cur.execute("SELECT MAX(ID) AS MAX_ID FROM Medical_Room_Visits")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 101
        visit_code = f"MED-{next_num}"

        today = datetime.date.today()
        now_time = datetime.datetime.now().strftime("%H:%M:%S")

        cur.execute("""
            INSERT INTO Medical_Room_Visits
            (VISIT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, VISIT_DATE, VISIT_TIME, SYMPTOMS, DIAGNOSIS_OBSERVATION, TREATMENT_GIVEN, ATTENDING_STAFF, PARENT_NOTIFIED, OUTCOME, CONFIDENTIAL_NOTES)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (visit_code, roll, name, cls, today, now_time, symptoms, diagnosis, treatment, attending, parent_notified, outcome, conf_notes))
        con.commit()
        print(f"\n[SUCCESS] Medical room visit recorded successfully as {visit_code}!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_discipline_incidents():
    clear_screen()
    print("=" * 115)
    print("                        STUDENT BEHAVIOUR & DISCIPLINE INCIDENTS")
    print("=" * 115)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, INCIDENT_DATE, CATEGORY, SEVERITY, LOCATION, REPORTED_BY, STATUS FROM Discipline_Incidents ORDER BY ID DESC")
        rows = cur.fetchall()
        if not rows:
            print("No discipline incidents on record.")
        else:
            table_data = []
            for r in rows:
                table_data.append([
                    r["INCIDENT_CODE"],
                    f"{r['STUDENT_NAME'][:15]} ({r['ROLL_NUMBER']})",
                    r["CLASS"],
                    str(r["INCIDENT_DATE"]),
                    r["CATEGORY"][:20],
                    r["SEVERITY"],
                    r["LOCATION"][:16],
                    r["REPORTED_BY"][:15],
                    r["STATUS"]
                ])
            headers = ["Code", "Student", "Class", "Date", "Category", "Severity", "Location", "Reported By", "Status"]
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    except Error as e:
        print("Error fetching discipline incidents:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def log_discipline_incident():
    clear_screen()
    print("=" * 90)
    print("                  REPORT BEHAVIOUR / DISCIPLINE INCIDENT")
    print("=" * 90)
    roll = input("Enter Student Roll Number: ").strip()
    if not roll:
        print("Roll number is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        st = cur.fetchone()
        if not st:
            print(f"Student with Roll Number {roll} not found.")
            pause_and_clear()
            return

        name = st["NAME"]
        cls = st["CLASS"]
        print(f"Student Involved: {name} ({cls})")

        print("\nCategory Options:")
        print("1. Disruptive Behaviour")
        print("2. Academic Dishonesty")
        print("3. Bullying / Harassment")
        print("4. Vandalism / Property Damage")
        print("5. Late Attendance / Truancy")
        print("6. Uniform / Dress Code Violation")
        print("7. Physical Altercation")
        print("8. Other")
        cat_opt = input("Choice [1]: ").strip()
        cats_map = {
            "1": "Disruptive Behaviour",
            "2": "Academic Dishonesty",
            "3": "Bullying / Harassment",
            "4": "Vandalism / Property Damage",
            "5": "Late Attendance / Truancy",
            "6": "Uniform / Dress Code Violation",
            "7": "Physical Altercation",
            "8": "Other"
        }
        category = cats_map.get(cat_opt, "Disruptive Behaviour")

        print("\nSeverity Level:")
        print("1. Minor   2. Moderate   3. Major   4. Critical")
        sev_opt = input("Choice [1]: ").strip()
        sevs_map = {"1": "Minor", "2": "Moderate", "3": "Major", "4": "Critical"}
        severity = sevs_map.get(sev_opt, "Minor")

        location = input("Location (e.g. Science Lab, Corridor, Cafeteria): ").strip() or "Classroom"
        reported_by = input("Reporting Teacher / Staff: ").strip() or "Faculty Member"
        description = input("Incident Description (Objective account): ").strip()
        witnesses = input("Witnesses (if any): ").strip() or "None"

        # Generate incident code
        cur.execute("SELECT MAX(ID) AS MAX_ID FROM Discipline_Incidents")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 201
        inc_code = f"DIS-{next_num}"

        today = datetime.date.today()

        cur.execute("""
            INSERT INTO Discipline_Incidents
            (INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, INCIDENT_DATE, CATEGORY, SEVERITY, LOCATION, REPORTED_BY, DESCRIPTION, WITNESSES, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Reported')
        """, (inc_code, roll, name, cls, today, category, severity, location, reported_by, description, witnesses))
        con.commit()
        print(f"\n[SUCCESS] Behaviour incident recorded successfully as {inc_code}!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def view_followup_actions():
    clear_screen()
    print("=" * 115)
    print("                     DISCIPLINARY INTERVENTIONS & FOLLOW-UP ACTIONS")
    print("=" * 115)
    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT FOLLOWUP_CODE, INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, ACTION_TYPE, ASSIGNED_TO, SCHEDULED_DATE, STATUS, PARENT_ACKNOWLEDGED FROM Discipline_Followups ORDER BY ID DESC")
        rows = cur.fetchall()
        if not rows:
            print("No follow-up actions recorded.")
        else:
            table_data = []
            for r in rows:
                ack_str = "Yes" if r["PARENT_ACKNOWLEDGED"] else "No"
                table_data.append([
                    r["FOLLOWUP_CODE"],
                    r["INCIDENT_CODE"],
                    f"{r['STUDENT_NAME'][:15]} ({r['ROLL_NUMBER']})",
                    r["ACTION_TYPE"],
                    r["ASSIGNED_TO"][:18],
                    str(r["SCHEDULED_DATE"]),
                    r["STATUS"],
                    ack_str
                ])
            headers = ["Follow-up #", "Incident #", "Student", "Action Type", "Assigned To", "Scheduled Date", "Status", "Parent Ack."]
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    except Error as e:
        print("Error fetching follow-up actions:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


def schedule_followup_action():
    clear_screen()
    print("=" * 90)
    print("               SCHEDULE DISCIPLINARY FOLLOW-UP / COUNSELING")
    print("=" * 90)
    inc_code = input("Enter Incident Code (e.g. DIS-201): ").strip().upper()
    if not inc_code:
        print("Incident code is required.")
        pause_and_clear()
        return

    con = get_connection()
    if not con:
        print("Database connection failed!")
        pause_and_clear()
        return

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT ROLL_NUMBER, STUDENT_NAME, CLASS FROM Discipline_Incidents WHERE INCIDENT_CODE = %s", (inc_code,))
        inc = cur.fetchone()
        if not inc:
            print(f"Incident {inc_code} not found.")
            pause_and_clear()
            return

        roll = inc["ROLL_NUMBER"]
        name = inc["STUDENT_NAME"]
        print(f"Student: {name} (Roll: {roll})")

        print("\nAction Types:")
        print("1. Verbal Counseling")
        print("2. Written Warning")
        print("3. Parent-Teacher Meeting")
        print("4. Student Counselor Session")
        print("5. After-School Detention")
        print("6. Campus Community Service")
        print("7. Suspension (Short-term)")
        print("8. Behavioral Contract")
        act_opt = input("Choice [1]: ").strip()
        acts_map = {
            "1": "Verbal Counseling",
            "2": "Written Warning",
            "3": "Parent-Teacher Meeting",
            "4": "Student Counselor Session",
            "5": "After-School Detention",
            "6": "Campus Community Service",
            "7": "Suspension (Short-term)",
            "8": "Behavioral Contract"
        }
        action_type = acts_map.get(act_opt, "Verbal Counseling")

        assigned_to = input("Assigned Staff / Counselor: ").strip() or "School Counselor"
        sched_date_raw = input("Scheduled Date (YYYY-MM-DD) [Tomorrow]: ").strip()
        if not sched_date_raw:
            sched_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            sched_date = sched_date_raw

        outcome_notes = input("Preliminary Notes / Objectives: ").strip()

        cur.execute("SELECT MAX(ID) AS MAX_ID FROM Discipline_Followups")
        row = cur.fetchone()
        next_num = (row["MAX_ID"] or 0) + 301
        fol_code = f"FOL-{next_num}"

        cur.execute("""
            INSERT INTO Discipline_Followups
            (FOLLOWUP_CODE, INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, ACTION_TYPE, ASSIGNED_TO, SCHEDULED_DATE, STATUS, OUTCOME_NOTES, PARENT_ACKNOWLEDGED)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Scheduled', %s, FALSE)
        """, (fol_code, inc_code, roll, name, action_type, assigned_to, sched_date, outcome_notes))

        # Update Incident status to Follow-up Scheduled
        cur.execute("UPDATE Discipline_Incidents SET STATUS = 'Follow-up Scheduled' WHERE INCIDENT_CODE = %s", (inc_code,))
        con.commit()
        print(f"\n[SUCCESS] Follow-up action scheduled successfully as {fol_code} for incident {inc_code}!")
    except Error as e:
        print("Database Error:", e)
    finally:
        cur.close()
        con.close()
    pause_and_clear()


# --------------------------------- CLI MAIN MENU ---------------------------------

def health_discipline_menu():
    create_health_discipline_tables()
    seed_health_discipline_data()
    while True:
        clear_screen()
        print("\n" + "=" * 80)
        print("          STUDENT HEALTH & DISCIPLINE MANAGEMENT SYSTEM".center(80))
        print("          (Medical-Room Visits, Health Profiles & Conduct Records)".center(80))
        print("=" * 80)
        print("1. View Student Health Profiles (Restricted)".center(80))
        print("2. Add / Update Student Health Profile".center(80))
        print("3. View Medical-Room / Clinic Visits Log".center(80))
        print("4. Record New Medical-Room Visit".center(80))
        print("5. View Student Behaviour & Discipline Incidents".center(80))
        print("6. Report New Discipline Incident".center(80))
        print("7. View Disciplinary Interventions & Follow-ups".center(80))
        print("8. Schedule Follow-up Action / Counseling Session".center(80))
        print("0. Return to Main Menu".center(80))
        print("=" * 80)

        choice = input("\nEnter choice : : ").strip()
        if choice == "1":
            view_health_profiles()
        elif choice == "2":
            add_or_update_health_profile()
        elif choice == "3":
            view_medical_visits()
        elif choice == "4":
            log_medical_visit()
        elif choice == "5":
            view_discipline_incidents()
        elif choice == "6":
            log_discipline_incident()
        elif choice == "7":
            view_followup_actions()
        elif choice == "8":
            schedule_followup_action()
        elif choice == "0":
            break
        else:
            print("Invalid Choice, Try Again!")
            pause_and_clear()


if __name__ == "__main__":
    health_discipline_menu()
