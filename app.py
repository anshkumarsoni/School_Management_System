import os
import math
import datetime
import mysql.connector as ms
from mysql.connector import Error
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

from utils import (
    get_connection,
    valid_email,
    valid_phonenumber
)
from auth import (
    hash_password,
    check_password,
    validate_password_strength,
    log_history,
    login_required,
    role_required
)

# Load environment variables from .env relative to this project file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "edupulse_academic_secret_998877"

# Role Display Names and Flexible Persona Mapping
ROLE_DISPLAY = {
    "super_admin": "Principal",
    "admin": "Teacher",
    "viewer": "Parent & Student"
}

ROLE_ALIASES = {
    # Canonical MySQL ENUM values
    "super_admin": "super_admin",
    "admin": "admin",
    "viewer": "viewer",
    # Principal aliases (user requested: super_admin as Principle / Principal)
    "principal": "super_admin",
    "principle": "super_admin",
    "superadmin": "super_admin",
    "super admin": "super_admin",
    "super administrator": "super_admin",
    "headmaster": "super_admin",
    # Teacher aliases (user requested: admin as Teachers)
    "teacher": "admin",
    "teachers": "admin",
    "faculty": "admin",
    "staff": "admin",
    "administrator": "admin",
    # Parent & Student / Viewer aliases (user requested: Parents and Students as Viewer)
    "parent": "viewer",
    "parents": "viewer",
    "student": "viewer",
    "students": "viewer",
    "parents and students": "viewer",
    "parents & students": "viewer",
    "parent and student": "viewer",
    "parent & student": "viewer",
    "read-only": "viewer",
    "readonly": "viewer"
}

def get_role_display(role_code: str) -> str:
    """Returns human-friendly display title for technical database role codes."""
    if not role_code:
        return "Parent & Student"
    return ROLE_DISPLAY.get(role_code.lower().strip(), role_code.replace("_", " ").title())

# Global Template Context Injector for Session User & Role Labels
@app.context_processor
def inject_user_context():
    role = session.get("role")
    return {
        "current_user": session.get("username"),
        "current_role": role,
        "current_role_name": get_role_display(role),
        "ROLE_DISPLAY": ROLE_DISPLAY
    }

# Jinja2 Template Filter for formatting role badges
@app.template_filter("role_name")
def role_name_filter(role_code):
    return get_role_display(role_code)

# Ensure Database Schema includes DOB column and dashboard widgets tables
def init_db_schema():
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            for table in ["Students_Details", "Teachers_Details"]:
                cur.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = 'DOB'
                """, (table,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN DOB DATE NULL")
                    con.commit()

            # Ensure Announcements table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    TITLE VARCHAR(200) NOT NULL,
                    CATEGORY VARCHAR(50) DEFAULT 'General',
                    DESCRIPTION TEXT,
                    POST_DATE DATE DEFAULT (CURRENT_DATE),
                    PRIORITY VARCHAR(20) DEFAULT 'Normal'
                )
            """)

            # Ensure Academic Events table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS academic_events (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    TITLE VARCHAR(200) NOT NULL,
                    EVENT_DATE DATE NOT NULL,
                    CATEGORY VARCHAR(50) DEFAULT 'Academic',
                    LOCATION VARCHAR(100) DEFAULT 'Main Campus'
                )
            """)

            # Ensure Teacher Attendance table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Teacher_Attendance (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    TEACHER_ID VARCHAR(20) NOT NULL,
                    ATTENDANCE_DATE DATE NOT NULL,
                    STATUS ENUM('Present', 'Absent', 'On Leave') NOT NULL,
                    REMARKS VARCHAR(100),
                    UNIQUE KEY unique_teacher_date (TEACHER_ID, ATTENDANCE_DATE)
                )
            """)

            # Ensure Parents Details table exists
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

            # Ensure Book_Issues table exists (Issue/Return, Due Dates, Overdue & Fines)
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

            # Ensure Book_Reservations table exists
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

            # Ensure Books_Details has extended attributes (shelf location, ISBN, publisher)
            for col_def in [
                ("SHELF_LOCATION", "VARCHAR(50) DEFAULT NULL"),
                ("ISBN", "VARCHAR(30) DEFAULT NULL"),
                ("PUBLISHER", "VARCHAR(100) DEFAULT NULL")
            ]:
                col_name, col_type = col_def
                cur.execute("""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Books_Details' AND COLUMN_NAME = %s
                """, (col_name,))
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE Books_Details ADD COLUMN {col_name} {col_type}")
                    con.commit()
        except Error as e:
            print("Schema Init Notice:", e)
        finally:
            cur.close()
            con.close()

    try:
        from Coursework_Management_System import create_coursework_tables
        create_coursework_tables()
    except Exception as _cw_err:
        print("Coursework schema init notice:", _cw_err)
    try:
        from Health_Discipline_Management_System import create_health_discipline_tables, seed_health_discipline_data
        create_health_discipline_tables()
        seed_health_discipline_data()
    except Exception as _hd_err:
        print("Health & Discipline schema init notice:", _hd_err)
    try:
        from Calendar_PTM_Management_System import create_calendar_ptm_tables, seed_calendar_ptm_data
        create_calendar_ptm_tables()
        seed_calendar_ptm_data()
    except Exception as _cptm_err:
        print("Calendar & PTM schema init notice:", _cptm_err)
    try:
        from Analytics_Management_System import init_analytics_tables
        init_analytics_tables()
    except Exception as _ams_err:
        print("Performance Analytics schema init notice:", _ams_err)



init_db_schema()

def calculate_birthday_events(records):
    """Calculates birthdays for today and upcoming in next 30 days."""
    today = datetime.date.today()
    todays_birthdays = []
    upcoming_birthdays = []

    for r in records:
        dob = r.get("DOB")
        if not dob:
            continue
        if isinstance(dob, str):
            try:
                dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                continue

        try:
            this_year_bday = dob.replace(year=today.year)
        except ValueError:
            this_year_bday = dob.replace(year=today.year, day=28)

        if this_year_bday < today:
            try:
                next_bday = dob.replace(year=today.year + 1)
            except ValueError:
                next_bday = dob.replace(year=today.year + 1, day=28)
        else:
            next_bday = this_year_bday

        days_until = (next_bday - today).days
        turning_age = next_bday.year - dob.year

        item = dict(r)
        item["days_until"] = days_until
        item["turning_age"] = turning_age
        item["bday_formatted"] = dob.strftime("%b %d, %Y")
        item["bday_short"] = dob.strftime("%b %d")
        item["next_bday_formatted"] = next_bday.strftime("%b %d")
        item["is_today"] = (days_until == 0)

        if days_until == 0:
            todays_birthdays.append(item)
        elif 0 < days_until <= 30:
            upcoming_birthdays.append(item)

    upcoming_birthdays.sort(key=lambda x: x["days_until"])
    return todays_birthdays, upcoming_birthdays

# -------------------------------------------------------------------------
# 1. AUTHENTICATION & SESSION MANAGEMENT
# -------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, go straight to dashboard
    if "username" in session and "role" in session:
        return redirect(url_for("dashboard"))

    con = get_connection()
    if not con:
        return "Database Connection Failed! Please verify MySQL is running and your .env configuration.", 500

    cur = con.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cur.fetchone()["total"]

    # First-run scenario: No users exist yet
    first_run = (total_users == 0)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if first_run:
            # Register initial Super Admin account
            if not username or not password:
                flash("Username and Password cannot be empty.", "warning")
                cur.close()
                con.close()
                return render_template("login.html", first_run=True)

            is_valid, err_msg = validate_password_strength(password)
            if not is_valid:
                flash(err_msg, "danger")
                cur.close()
                con.close()
                return render_template("login.html", first_run=True)

            hashed = hash_password(password)
            try:
                cur.execute(
                    "INSERT INTO users (USERNAME, PASSWORD, ROLE) VALUES (%s, %s, %s)",
                    (username, hashed, "super_admin")
                )
                con.commit()
                log_history(username, "Initial Principal account registered")
                session["username"] = username
                session["role"] = "super_admin"
                flash(f"Welcome, {username}! Initial Principal (Super Admin) account created.", "success")
                cur.close()
                con.close()
                return redirect(url_for("dashboard"))
            except Error as e:
                flash(f"Registration Error: {e}", "danger")
                cur.close()
                con.close()
                return render_template("login.html", first_run=True)

        # Standard Login Flow
        selected_role = request.form.get("role", "").strip()

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            cur.close()
            con.close()
            return render_template("login.html", first_run=False)

        cur.execute("SELECT USERNAME, PASSWORD, ROLE FROM users WHERE USERNAME = %s", (username,))
        user_row = cur.fetchone()
        cur.close()
        con.close()

        if not user_row:
            flash("Invalid username or password.", "danger")
            return render_template("login.html", first_run=False)

        stored_hash = user_row["PASSWORD"]
        user_role = user_row["ROLE"]

        # Support role aliases (e.g. principal -> super_admin, teacher -> admin, student/parent -> viewer)
        if selected_role:
            canonical_selected = ROLE_ALIASES.get(selected_role.lower(), selected_role)
            if canonical_selected != user_role:
                expected_label = get_role_display(user_role)
                selected_label = get_role_display(canonical_selected)
                flash(f"Access Denied: Account belongs to '{expected_label}', not '{selected_label}'.", "danger")
                return render_template("login.html", first_run=False)

        if check_password(password, stored_hash):
            session["username"] = user_row["USERNAME"]
            session["role"] = user_role
            role_label = get_role_display(user_role)
            log_history(user_row["USERNAME"], f"Logged in as {role_label}")
            flash(f"Welcome back, {user_row['USERNAME']} ({role_label})!", "success")
            
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html", first_run=False)

    cur.close()
    con.close()
    return render_template("login.html", first_run=first_run)


@app.route("/logout")
def logout():
    username = session.get("username")
    if username:
        log_history(username, "Logged out")
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password_route():
    if request.method == "POST":
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not old_password or not new_password or not confirm_password:
            flash("All password fields are required.", "warning")
            return redirect(url_for("change_password_route"))

        if new_password != confirm_password:
            flash("New password and confirmation password do not match.", "danger")
            return redirect(url_for("change_password_route"))

        is_valid, err_msg = validate_password_strength(new_password)
        if not is_valid:
            flash(err_msg, "danger")
            return redirect(url_for("change_password_route"))

        username = session.get("username")
        con = get_connection()
        if not con:
            flash("Database Connection Failed.", "danger")
            return redirect(url_for("change_password_route"))

        cur = con.cursor(dictionary=True)
        cur.execute("SELECT PASSWORD FROM users WHERE USERNAME = %s", (username,))
        row = cur.fetchone()

        if not row or not check_password(old_password, row["PASSWORD"]):
            flash("Current password is incorrect.", "danger")
            cur.close()
            con.close()
            return redirect(url_for("change_password_route"))

        new_hashed = hash_password(new_password)
        try:
            cur.execute("UPDATE users SET PASSWORD = %s WHERE USERNAME = %s", (new_hashed, username))
            con.commit()
            log_history(username, "Changed password")
            flash("Your password has been updated successfully!", "success")
            cur.close()
            con.close()
            return redirect(url_for("dashboard"))
        except Error as e:
            flash(f"Error updating password: {e}", "danger")
            cur.close()
            con.close()
            return redirect(url_for("change_password_route"))

    return render_template("change_password.html", active_page="change_password", title="Change Password")


# -------------------------------------------------------------------------
# 2. DASHBOARD
# -------------------------------------------------------------------------

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return render_template("dashboard.html", active_page="dashboard", title="Dashboard")

    cur = con.cursor(dictionary=True)

    # 1. Total counts from real database records
    cur.execute("SELECT COUNT(*) AS total FROM Students_Details")
    total_students = cur.fetchone()["total"] or 0

    cur.execute("SELECT COUNT(*) AS total FROM Teachers_Details")
    total_teachers = cur.fetchone()["total"] or 0

    total_users = 0
    if session.get("role") == "super_admin":
        cur.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cur.fetchone()["total"] or 0

    cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) AS total FROM Fee_Transactions")
    total_fees = float(cur.fetchone()["total"] or 0)

    cur.execute("SELECT IFNULL(SUM(TOTAL_COPIES), 0) AS total FROM Books_Details")
    total_books = int(cur.fetchone()["total"] or 0)

    # 2. Real recent activity from history table
    cur.execute("SELECT USERNAME, ACTIONS, LOG_TIME FROM history ORDER BY ID DESC LIMIT 8")
    recent_activity = cur.fetchall()

    # 3. Recent Students
    cur.execute("SELECT ID, ROLL_NUMBER, NAME, CLASS, PHONE, GENDER FROM Students_Details ORDER BY ID DESC LIMIT 5")
    recent_students = cur.fetchall()

    # 4. Chart 1: Enrollment by Class
    cur.execute("SELECT CLASS, COUNT(*) AS count FROM Students_Details WHERE CLASS IS NOT NULL AND CLASS != '' GROUP BY CLASS ORDER BY CLASS")
    class_rows = cur.fetchall()
    class_labels = [r["CLASS"] for r in class_rows]
    class_counts = [int(r["count"]) for r in class_rows]

    # 5. Chart 2: Gender Demographics
    cur.execute("SELECT GENDER, COUNT(*) AS count FROM Students_Details WHERE GENDER IS NOT NULL GROUP BY GENDER")
    gender_rows = cur.fetchall()
    gender_labels = [r["GENDER"] for r in gender_rows]
    gender_counts = [int(r["count"]) for r in gender_rows]

    # 6. Today's Birthdays (Students + Faculty)
    cur.execute("SELECT NAME, CLASS, 'Student' as role FROM Students_Details WHERE DOB IS NOT NULL AND MONTH(DOB) = MONTH(CURDATE()) AND DAY(DOB) = DAY(CURDATE())")
    todays_student_bdays = cur.fetchall()
    cur.execute("SELECT NAME, SUBJECT as CLASS, 'Faculty' as role FROM Teachers_Details WHERE DOB IS NOT NULL AND MONTH(DOB) = MONTH(CURDATE()) AND DAY(DOB) = DAY(CURDATE())")
    todays_teacher_bdays = cur.fetchall()
    all_todays_bdays = todays_student_bdays + todays_teacher_bdays

    # 7. Announcements / Notice Board
    cur.execute("SELECT ID, TITLE, CATEGORY, DESCRIPTION, POST_DATE, PRIORITY FROM announcements ORDER BY ID DESC LIMIT 4")
    raw_announcements = cur.fetchall()
    announcements = []
    for a in raw_announcements:
        p_date = a.get("POST_DATE")
        a["formatted_date"] = p_date.strftime("%b %d, %Y") if p_date else "Recent"
        announcements.append(a)

    # 8. Upcoming Academic Events & Milestones (Synchronized with School_Events)
    today = datetime.date.today()
    try:
        cur.execute("SELECT ID, TITLE, EVENT_DATE, CATEGORY, LOCATION FROM School_Events WHERE EVENT_DATE >= %s AND STATUS != 'Cancelled' ORDER BY EVENT_DATE ASC LIMIT 4", (today,))
        raw_events = cur.fetchall()
        if not raw_events:
            cur.execute("SELECT ID, TITLE, EVENT_DATE, CATEGORY, LOCATION FROM School_Events ORDER BY EVENT_DATE ASC LIMIT 4")
            raw_events = cur.fetchall()
    except Exception:
        cur.execute("SELECT ID, TITLE, EVENT_DATE, CATEGORY, LOCATION FROM academic_events ORDER BY EVENT_DATE ASC LIMIT 4")
        raw_events = cur.fetchall()
    academic_events = []
    for ev in raw_events:
        ed = ev.get("EVENT_DATE")
        if ed:
            ev["month_abbr"] = ed.strftime("%b").upper()
            ev["day_num"] = ed.strftime("%d")
            ev["formatted_date"] = ed.strftime("%a, %b %d, %Y")
            delta = (ed - today).days
            if delta == 0:
                ev["countdown"] = "Today"
                ev["is_urgent"] = True
            elif delta == 1:
                ev["countdown"] = "Tomorrow"
                ev["is_urgent"] = True
            elif delta > 1:
                ev["countdown"] = f"In {delta} days"
                ev["is_urgent"] = (delta <= 7)
            else:
                ev["countdown"] = f"{abs(delta)}d ago"
                ev["is_urgent"] = False
        else:
            ev["month_abbr"] = "TBD"
            ev["day_num"] = "--"
            ev["countdown"] = "Upcoming"
            ev["is_urgent"] = False
        academic_events.append(ev)

    cur.close()
    con.close()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        title="Dashboard Overview",
        total_students=total_students,
        total_teachers=total_teachers,
        total_users=total_users,
        total_fees=total_fees,
        total_books=total_books,
        recent_activity=recent_activity,
        recent_students=recent_students,
        all_todays_bdays=all_todays_bdays,
        announcements=announcements,
        academic_events=academic_events,
        class_labels=class_labels,
        class_counts=class_counts,
        gender_labels=gender_labels,
        gender_counts=gender_counts
    )


# -------------------------------------------------------------------------
# 3. STUDENT MANAGEMENT MODULE
# -------------------------------------------------------------------------

@app.route("/students")
@login_required
def students_view():
    search = request.args.get("search", "").strip()
    selected_class = request.args.get("class", "").strip()
    min_age_raw = request.args.get("min_age", "").strip()
    max_age_raw = request.args.get("max_age", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(url_for("dashboard"))

    cur = con.cursor(dictionary=True)

    # Fetch available classes for dropdown filter
    cur.execute("SELECT DISTINCT CLASS FROM Students_Details WHERE CLASS IS NOT NULL AND CLASS != '' ORDER BY CLASS")
    available_classes = [r["CLASS"] for r in cur.fetchall()]

    # Dynamic Filter Query Construction
    base_query = "FROM Students_Details WHERE 1=1"
    params = []

    if search:
        base_query += " AND (NAME LIKE %s OR ROLL_NUMBER LIKE %s OR PHONE LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if selected_class:
        base_query += " AND CLASS = %s"
        params.append(selected_class)

    if min_age_raw.isdigit():
        base_query += " AND AGE >= %s"
        params.append(int(min_age_raw))

    if max_age_raw.isdigit():
        base_query += " AND AGE <= %s"
        params.append(int(max_age_raw))

    # Count total matching rows for pagination
    cur.execute(f"SELECT COUNT(*) AS total {base_query}", tuple(params))
    total_records = cur.fetchone()["total"] or 0
    total_pages = max(1, math.ceil(total_records / per_page))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    # Fetch paginated slice
    cur.execute(f"SELECT * {base_query} ORDER BY ID DESC LIMIT %s OFFSET %s", tuple(params + [per_page, offset]))
    students = cur.fetchall()

    today = datetime.date.today()
    for s in students:
        dob_val = s.get("DOB")
        if dob_val:
            if isinstance(dob_val, (datetime.date, datetime.datetime)):
                s["DOB_RAW"] = dob_val.strftime("%Y-%m-%d")
                s["DOB_FORMATTED"] = dob_val.strftime("%b %d, %Y")
                s["IS_TODAY_BDAY"] = (dob_val.month == today.month and dob_val.day == today.day)
            else:
                s["DOB_RAW"] = str(dob_val)
                s["DOB_FORMATTED"] = str(dob_val)
                s["IS_TODAY_BDAY"] = False
        else:
            s["DOB_RAW"] = ""
            s["DOB_FORMATTED"] = ""
            s["IS_TODAY_BDAY"] = False

    # Fetch all students with DOB for the Birthday Section
    cur.execute("SELECT ID, ROLL_NUMBER, NAME, CLASS, GENDER, DOB FROM Students_Details WHERE DOB IS NOT NULL")
    all_bday_students = cur.fetchall()
    bday_today, bday_upcoming = calculate_birthday_events(all_bday_students)

    # Visual Pie Chart 1: Student Gender Demographics (Male / Female / Other)
    cur.execute("""
        SELECT 
            COALESCE(NULLIF(TRIM(GENDER), ''), 'Other') as gender_label,
            COUNT(*) as count
        FROM Students_Details
        GROUP BY gender_label
        ORDER BY FIELD(gender_label, 'Male', 'Female', 'Other')
    """)
    gender_rows = cur.fetchall()
    student_gender_labels = [r["gender_label"] for r in gender_rows]
    student_gender_counts = [int(r["count"]) for r in gender_rows]

    # Visual Pie Chart 2: Student Attendance Overview (Present / Absent / Leave)
    cur.execute("""
        SELECT STATUS as status_label, COUNT(*) as count
        FROM attendance_details
        GROUP BY STATUS
        ORDER BY FIELD(STATUS, 'Present', 'Absent', 'Leave')
    """)
    att_rows = cur.fetchall()
    student_att_labels = [r["status_label"] for r in att_rows]
    student_att_counts = [int(r["count"]) for r in att_rows]

    cur.close()
    con.close()

    return render_template(
        "students.html",
        active_page="students",
        title="Student Management",
        students=students,
        available_classes=available_classes,
        bday_today=bday_today,
        bday_upcoming=bday_upcoming,
        student_gender_labels=student_gender_labels,
        student_gender_counts=student_gender_counts,
        student_att_labels=student_att_labels,
        student_att_counts=student_att_counts,
        search=search,
        selected_class=selected_class,
        min_age=min_age_raw,
        max_age=max_age_raw,
        page=page,
        total_pages=total_pages,
        total_records=total_records
    )


@app.route("/students/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_student_route():
    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    class_name = request.form.get("class_name", "").strip()
    age_raw = request.form.get("age", "").strip()
    gender = request.form.get("gender", "Male").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    dob_raw = request.form.get("dob", "").strip()

    # Preserve Existing Validation Rules:
    if not roll_number.isdigit():
        flash("Validation Error: Roll number must contain digits only.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    if not name:
        flash("Validation Error: Student name cannot be empty.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    dob = None
    if dob_raw:
        try:
            parsed_dob = datetime.datetime.strptime(dob_raw, "%Y-%m-%d").date()
            if parsed_dob > datetime.date.today():
                flash("Validation Error: Date of Birth cannot be in the future.", "danger")
                return redirect(request.referrer or url_for("students_view"))
            dob = dob_raw
        except ValueError:
            flash("Validation Error: Invalid Date of Birth format.", "danger")
            return redirect(request.referrer or url_for("students_view"))

    age = None
    if age_raw:
        try:
            age = int(age_raw)
            if age <= 0 or age > 120:
                flash("Validation Error: Please enter a realistic age (1 - 120).", "danger")
                return redirect(request.referrer or url_for("students_view"))
        except ValueError:
            flash("Validation Error: Age must be a number.", "danger")
            return redirect(request.referrer or url_for("students_view"))
    elif dob:
        today = datetime.date.today()
        age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))

    if phone and not valid_phonenumber(phone):
        flash("Validation Error: Invalid Indian phone number (10 digits starting with 6, 7, 8, or 9).", "danger")
        return redirect(request.referrer or url_for("students_view"))

    if email and not valid_email(email):
        flash("Validation Error: Invalid email address format.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    if gender not in ("Male", "Female", "Other"):
        flash("Validation Error: Invalid gender option.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    cur = con.cursor(dictionary=True)
    try:
        # Check uniqueness of Roll Number
        cur.execute("SELECT 1 FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
        if cur.fetchone():
            flash(f"Validation Error: Roll Number '{roll_number}' already exists in database.", "danger")
            return redirect(request.referrer or url_for("students_view"))

        cur.execute("""
            INSERT INTO Students_Details (ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER, DOB)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (roll_number, name, class_name, age, address, phone, email, gender, dob))
        con.commit()

        username = session.get("username", "Admin")
        log_history(username, f"Added student Roll {roll_number}")
        flash(f"Student '{name}' (Roll #{roll_number}) registered successfully!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(request.referrer or url_for("students_view"))


@app.route("/students/edit/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def edit_student_route(id):
    name = request.form.get("name", "").strip()
    class_name = request.form.get("class_name", "").strip()
    age_raw = request.form.get("age", "").strip()
    gender = request.form.get("gender", "Male").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    dob_raw = request.form.get("dob", "").strip()

    if not name:
        flash("Validation Error: Student name cannot be empty.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    dob = None
    if dob_raw:
        try:
            parsed_dob = datetime.datetime.strptime(dob_raw, "%Y-%m-%d").date()
            if parsed_dob > datetime.date.today():
                flash("Validation Error: Date of Birth cannot be in the future.", "danger")
                return redirect(request.referrer or url_for("students_view"))
            dob = dob_raw
        except ValueError:
            flash("Validation Error: Invalid Date of Birth format.", "danger")
            return redirect(request.referrer or url_for("students_view"))

    age = None
    if age_raw:
        try:
            age = int(age_raw)
            if age <= 0 or age > 120:
                flash("Validation Error: Please enter a realistic age.", "danger")
                return redirect(request.referrer or url_for("students_view"))
        except ValueError:
            flash("Validation Error: Age must be a number.", "danger")
            return redirect(request.referrer or url_for("students_view"))
    elif dob:
        today = datetime.date.today()
        age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))

    if phone and not valid_phonenumber(phone):
        flash("Validation Error: Invalid Indian phone number.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    if email and not valid_email(email):
        flash("Validation Error: Invalid email format.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(request.referrer or url_for("students_view"))

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT ROLL_NUMBER FROM Students_Details WHERE ID = %s", (id,))
        row = cur.fetchone()
        if not row:
            flash("Student record not found.", "warning")
            return redirect(request.referrer or url_for("students_view"))

        roll_number = row["ROLL_NUMBER"]

        cur.execute("""
            UPDATE Students_Details
            SET NAME = %s, CLASS = %s, AGE = %s, ADDRESS = %s, PHONE = %s, EMAIL = %s, GENDER = %s, DOB = %s
            WHERE ID = %s
        """, (name, class_name, age, address, phone, email, gender, dob, id))
        con.commit()

        username = session.get("username", "Admin")
        log_history(username, f"Updated ALL details for Roll {roll_number}")
        flash(f"Student details for Roll #{roll_number} updated successfully!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(request.referrer or url_for("students_view"))


@app.route("/students/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_student_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT ROLL_NUMBER FROM Students_Details WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                roll_number = row["ROLL_NUMBER"]
                cur.execute("DELETE FROM Students_Details WHERE ID = %s", (id,))
                con.commit()
                username = session.get("username", "Admin")
                log_history(username, f"Delete student Roll {roll_number}")
                flash(f"Student record (Roll #{roll_number}) deleted successfully.", "info")
            else:
                flash("Student record not found.", "warning")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(request.referrer or url_for("students_view"))


# -------------------------------------------------------------------------
# 3B. PARENT & GUARDIAN DETAILS MODULE
# -------------------------------------------------------------------------

@app.route("/parents")
@login_required
def parents_view():
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10

    con = get_connection()
    parents = []
    students = []
    total_records = 0
    total_pages = 1

    if con:
        cur = con.cursor(dictionary=True)

        query = """
            SELECT 
                p.ID, p.ROLL_NUMBER,
                COALESCE(s.NAME, 'Unknown Student') AS STUDENT_NAME,
                COALESCE(s.CLASS, 'N/A') AS STUDENT_CLASS,
                COALESCE(s.PHONE, 'N/A') AS STUDENT_PHONE,
                p.FATHER_NAME, p.FATHER_OCCUPATION, p.FATHER_PHONE,
                p.MOTHER_NAME, p.MOTHER_OCCUPATION, p.MOTHER_PHONE,
                p.GUARDIAN_NAME, p.RELATION,
                p.PRIMARY_CONTACT, p.EMAIL,
                p.RESIDENTIAL_ADDRESS, p.EMERGENCY_CONTACT, p.ANNUAL_INCOME
            FROM Parents_Details p
            LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER
        """
        count_query = "SELECT COUNT(*) as cnt FROM Parents_Details p LEFT JOIN Students_Details s ON p.ROLL_NUMBER = s.ROLL_NUMBER"
        params = []

        if search:
            query += " WHERE (p.ROLL_NUMBER LIKE %s OR s.NAME LIKE %s OR p.FATHER_NAME LIKE %s OR p.MOTHER_NAME LIKE %s OR p.PRIMARY_CONTACT LIKE %s)"
            count_query += " WHERE (p.ROLL_NUMBER LIKE %s OR s.NAME LIKE %s OR p.FATHER_NAME LIKE %s OR p.MOTHER_NAME LIKE %s OR p.PRIMARY_CONTACT LIKE %s)"
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

        cur.execute(count_query, params)
        total_records = cur.fetchone()["cnt"] or 0
        total_pages = max(1, (total_records + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query += " ORDER BY p.ROLL_NUMBER ASC LIMIT %s OFFSET %s"
        query_params = list(params) + [per_page, offset]
        cur.execute(query, query_params)
        parents = cur.fetchall()

        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
        students = cur.fetchall()

        cur.close()
        con.close()

    return render_template(
        "parents.html",
        active_page="parents",
        title="Parent & Guardian Directory",
        parents=parents,
        students=students,
        search=search,
        page=page,
        total_pages=total_pages,
        total_records=total_records
    )


@app.route("/parents/add", methods=["POST"], endpoint="add_parent_route")
@login_required
@role_required(["super_admin", "admin"])
def add_parent_route():
    roll_number = request.form.get("roll_number", "").strip()
    father_name = request.form.get("father_name", "").strip()
    father_occ = request.form.get("father_occupation", "").strip()
    father_phone = request.form.get("father_phone", "").strip()
    mother_name = request.form.get("mother_name", "").strip()
    mother_occ = request.form.get("mother_occupation", "").strip()
    mother_phone = request.form.get("mother_phone", "").strip()
    guardian_name = request.form.get("guardian_name", "").strip()
    relation = request.form.get("relation", "Parent").strip()
    primary_contact = request.form.get("primary_contact", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    emergency_contact = request.form.get("emergency_contact", "").strip()
    income_raw = request.form.get("annual_income", "0").strip()

    if not roll_number:
        flash("Validation Error: Student Roll Number is required.", "warning")
        return redirect(url_for("parents_view"))

    if not primary_contact:
        primary_contact = father_phone or mother_phone

    if not primary_contact:
        flash("Validation Error: A valid Primary Contact Phone number is required.", "danger")
        return redirect(url_for("parents_view"))

    try:
        annual_income = float(income_raw) if income_raw else 0.00
    except ValueError:
        annual_income = 0.00

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            student = cur.fetchone()
            if not student:
                flash(f"Validation Error: Student with Roll Number '{roll_number}' was not found.", "danger")
                return redirect(url_for("parents_view"))

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
                roll_number, father_name, father_occ, father_phone,
                mother_name, mother_occ, mother_phone,
                guardian_name, relation, primary_contact,
                email, address, emergency_contact, annual_income,
                father_name, father_occ, father_phone,
                mother_name, mother_occ, mother_phone,
                guardian_name, relation, primary_contact,
                email, address, emergency_contact, annual_income
            ))
            con.commit()
            log_history(session.get("username", "Admin"), f"Linked parent details for student Roll #{roll_number} ({student['NAME']})")
            flash(f"Parent/Guardian details successfully linked to {student['NAME']} (Roll #{roll_number})!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("parents_view"))


@app.route("/parents/edit/<int:id>", methods=["POST"], endpoint="edit_parent_route")
@login_required
@role_required(["super_admin", "admin"])
def edit_parent_route(id):
    father_name = request.form.get("father_name", "").strip()
    father_occ = request.form.get("father_occupation", "").strip()
    father_phone = request.form.get("father_phone", "").strip()
    mother_name = request.form.get("mother_name", "").strip()
    mother_occ = request.form.get("mother_occupation", "").strip()
    mother_phone = request.form.get("mother_phone", "").strip()
    guardian_name = request.form.get("guardian_name", "").strip()
    relation = request.form.get("relation", "Parent").strip()
    primary_contact = request.form.get("primary_contact", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    emergency_contact = request.form.get("emergency_contact", "").strip()
    income_raw = request.form.get("annual_income", "0").strip()

    try:
        annual_income = float(income_raw) if income_raw else 0.00
    except ValueError:
        annual_income = 0.00

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                UPDATE Parents_Details SET
                    FATHER_NAME = %s, FATHER_OCCUPATION = %s, FATHER_PHONE = %s,
                    MOTHER_NAME = %s, MOTHER_OCCUPATION = %s, MOTHER_PHONE = %s,
                    GUARDIAN_NAME = %s, RELATION = %s, PRIMARY_CONTACT = %s,
                    EMAIL = %s, RESIDENTIAL_ADDRESS = %s, EMERGENCY_CONTACT = %s, ANNUAL_INCOME = %s
                WHERE ID = %s
            """, (
                father_name, father_occ, father_phone,
                mother_name, mother_occ, mother_phone,
                guardian_name, relation, primary_contact,
                email, address, emergency_contact, annual_income,
                id
            ))
            con.commit()
            log_history(session.get("username", "Admin"), f"Updated parent details ID #{id}")
            flash("Parent details updated successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("parents_view"))


@app.route("/parents/delete/<int:id>", methods=["POST"], endpoint="delete_parent_route")
@login_required
@role_required(["super_admin", "admin"])
def delete_parent_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT ROLL_NUMBER FROM Parents_Details WHERE ID = %s", (id,))
            row = cur.fetchone()
            roll = row["ROLL_NUMBER"] if row else id

            cur.execute("DELETE FROM Parents_Details WHERE ID = %s", (id,))
            con.commit()
            log_history(session.get("username", "Admin"), f"Deleted parent details record for Roll #{roll}")
            flash(f"Parent record for Roll #{roll} was removed successfully.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("parents_view"))


# -------------------------------------------------------------------------
# 4. TEACHER MANAGEMENT MODULE
# -------------------------------------------------------------------------

@app.route("/teachers")
@login_required
def teachers_view():
    search = request.args.get("search", "").strip()
    selected_subject = request.args.get("subject", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 10

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(url_for("dashboard"))

    cur = con.cursor(dictionary=True)

    cur.execute("SELECT DISTINCT SUBJECT FROM Teachers_Details WHERE SUBJECT IS NOT NULL AND SUBJECT != '' ORDER BY SUBJECT")
    available_subjects = [r["SUBJECT"] for r in cur.fetchall()]

    base_query = "FROM Teachers_Details WHERE 1=1"
    params = []

    if search:
        base_query += " AND (NAME LIKE %s OR TEACHER_ID LIKE %s OR PHONE LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if selected_subject:
        base_query += " AND SUBJECT = %s"
        params.append(selected_subject)

    cur.execute(f"SELECT COUNT(*) AS total {base_query}", tuple(params))
    total_records = cur.fetchone()["total"] or 0
    total_pages = max(1, math.ceil(total_records / per_page))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page

    cur.execute(f"SELECT * {base_query} ORDER BY ID DESC LIMIT %s OFFSET %s", tuple(params + [per_page, offset]))
    teachers = cur.fetchall()

    today = datetime.date.today()
    for t in teachers:
        dob_val = t.get("DOB")
        if dob_val:
            if isinstance(dob_val, (datetime.date, datetime.datetime)):
                t["DOB_RAW"] = dob_val.strftime("%Y-%m-%d")
                t["DOB_FORMATTED"] = dob_val.strftime("%b %d, %Y")
                t["IS_TODAY_BDAY"] = (dob_val.month == today.month and dob_val.day == today.day)
            else:
                t["DOB_RAW"] = str(dob_val)
                t["DOB_FORMATTED"] = str(dob_val)
                t["IS_TODAY_BDAY"] = False
        else:
            t["DOB_RAW"] = ""
            t["DOB_FORMATTED"] = ""
            t["IS_TODAY_BDAY"] = False

    # Fetch all teachers with DOB for the Birthday Section
    cur.execute("SELECT ID, TEACHER_ID, NAME, SUBJECT, GENDER, DOB FROM Teachers_Details WHERE DOB IS NOT NULL")
    all_bday_teachers = cur.fetchall()
    bday_today, bday_upcoming = calculate_birthday_events(all_bday_teachers)

    # Visual Pie Chart 1: Faculty Gender Demographics (Male / Female / Other)
    cur.execute("""
        SELECT 
            COALESCE(NULLIF(TRIM(GENDER), ''), 'Other') as gender_label,
            COUNT(*) as count
        FROM Teachers_Details
        GROUP BY gender_label
        ORDER BY FIELD(gender_label, 'Male', 'Female', 'Other')
    """)
    t_gender_rows = cur.fetchall()
    teacher_gender_labels = [r["gender_label"] for r in t_gender_rows]
    teacher_gender_counts = [int(r["count"]) for r in t_gender_rows]

    # Visual Pie Chart 2: Faculty Attendance Overview (Present / Absent / On Leave)
    cur.execute("""
        SELECT STATUS as status_label, COUNT(*) as count
        FROM Teacher_Attendance
        GROUP BY STATUS
        ORDER BY FIELD(STATUS, 'Present', 'Absent', 'On Leave')
    """)
    t_att_rows = cur.fetchall()
    teacher_att_labels = [r["status_label"] for r in t_att_rows]
    teacher_att_counts = [int(r["count"]) for r in t_att_rows]

    cur.close()
    con.close()

    return render_template(
        "teachers.html",
        active_page="teachers",
        title="Faculty Management",
        teachers=teachers,
        available_subjects=available_subjects,
        bday_today=bday_today,
        bday_upcoming=bday_upcoming,
        teacher_gender_labels=teacher_gender_labels,
        teacher_gender_counts=teacher_gender_counts,
        teacher_att_labels=teacher_att_labels,
        teacher_att_counts=teacher_att_counts,
        search=search,
        selected_subject=selected_subject,
        page=page,
        total_pages=total_pages,
        total_records=total_records
    )


@app.route("/teachers/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_teacher_route():
    teacher_id = request.form.get("teacher_id", "").strip()
    name = request.form.get("name", "").strip()
    subject = request.form.get("subject", "").strip()
    age_raw = request.form.get("age", "").strip()
    gender = request.form.get("gender", "Male").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    dob_raw = request.form.get("dob", "").strip()

    if not teacher_id:
        flash("Validation Error: Teacher ID cannot be empty.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    if not name or not subject:
        flash("Validation Error: Teacher name and Subject are required.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    dob = None
    if dob_raw:
        try:
            parsed_dob = datetime.datetime.strptime(dob_raw, "%Y-%m-%d").date()
            if parsed_dob > datetime.date.today():
                flash("Validation Error: Date of Birth cannot be in the future.", "danger")
                return redirect(request.referrer or url_for("teachers_view"))
            dob = dob_raw
        except ValueError:
            flash("Validation Error: Invalid Date of Birth format.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))

    try:
        if age_raw:
            age = int(age_raw)
        elif dob:
            today = datetime.date.today()
            age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))
        else:
            flash("Validation Error: Age or Date of Birth is required.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))

        if age < 18 or age > 120:
            flash("Validation Error: Teacher age must be between 18 and 120.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))
    except ValueError:
        flash("Validation Error: Age must be a number.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    if phone and not valid_phonenumber(phone):
        flash("Validation Error: Invalid Indian phone number format.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    if email and not valid_email(email):
        flash("Validation Error: Invalid email format.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT 1 FROM Teachers_Details WHERE TEACHER_ID = %s", (teacher_id,))
        if cur.fetchone():
            flash(f"Validation Error: Teacher ID '{teacher_id}' already exists in database.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))

        cur.execute("""
            INSERT INTO Teachers_Details (TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER, DOB)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (teacher_id, name, subject, age, address, phone, email, gender, dob))
        con.commit()

        username = session.get("username", "Admin")
        log_history(username, f"Added teacher ID {teacher_id}")
        flash(f"Faculty member '{name}' registered successfully!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(request.referrer or url_for("teachers_view"))


@app.route("/teachers/edit/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def edit_teacher_route(id):
    name = request.form.get("name", "").strip()
    subject = request.form.get("subject", "").strip()
    age_raw = request.form.get("age", "").strip()
    gender = request.form.get("gender", "Male").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    dob_raw = request.form.get("dob", "").strip()

    if not name or not subject:
        flash("Validation Error: Name and Subject cannot be empty.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    dob = None
    if dob_raw:
        try:
            parsed_dob = datetime.datetime.strptime(dob_raw, "%Y-%m-%d").date()
            if parsed_dob > datetime.date.today():
                flash("Validation Error: Date of Birth cannot be in the future.", "danger")
                return redirect(request.referrer or url_for("teachers_view"))
            dob = dob_raw
        except ValueError:
            flash("Validation Error: Invalid Date of Birth format.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))

    try:
        if age_raw:
            age = int(age_raw)
        elif dob:
            today = datetime.date.today()
            age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))
        else:
            flash("Validation Error: Age or Date of Birth is required.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))

        if age < 18 or age > 120:
            flash("Validation Error: Teacher age must be between 18 and 120.", "danger")
            return redirect(request.referrer or url_for("teachers_view"))
    except ValueError:
        flash("Validation Error: Age must be a number.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    if phone and not valid_phonenumber(phone):
        flash("Validation Error: Invalid Indian phone number.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    if email and not valid_email(email):
        flash("Validation Error: Invalid email format.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(request.referrer or url_for("teachers_view"))

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT TEACHER_ID FROM Teachers_Details WHERE ID = %s", (id,))
        row = cur.fetchone()
        if not row:
            flash("Teacher record not found.", "warning")
            return redirect(request.referrer or url_for("teachers_view"))

        teacher_id = row["TEACHER_ID"]

        cur.execute("""
            UPDATE Teachers_Details
            SET NAME = %s, SUBJECT = %s, AGE = %s, ADDRESS = %s, PHONE = %s, EMAIL = %s, GENDER = %s, DOB = %s
            WHERE ID = %s
        """, (name, subject, age, address, phone, email, gender, dob, id))
        con.commit()

        username = session.get("username", "Admin")
        log_history(username, f"Updated teacher ID {teacher_id}")
        flash(f"Teacher details for ID #{teacher_id} updated successfully!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(request.referrer or url_for("teachers_view"))


@app.route("/teachers/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_teacher_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT TEACHER_ID FROM Teachers_Details WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                teacher_id = row["TEACHER_ID"]
                cur.execute("DELETE FROM Teachers_Details WHERE ID = %s", (id,))
                con.commit()
                username = session.get("username", "Admin")
                log_history(username, f"Delete teacher ID {teacher_id}")
                flash(f"Teacher record (ID #{teacher_id}) deleted successfully.", "info")
            else:
                flash("Teacher record not found.", "warning")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(request.referrer or url_for("teachers_view"))


# -------------------------------------------------------------------------
# 5. USER & ACTIVITY MANAGEMENT MODULE (SUPER ADMIN ONLY)
# -------------------------------------------------------------------------

@app.route("/users")
@role_required(["super_admin"])
def users_view():
    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(url_for("dashboard"))

    cur = con.cursor(dictionary=True)

    # 1. Fetch all users (Excluding password hashes for security)
    cur.execute("SELECT ID, USERNAME, ROLE FROM users ORDER BY ID ASC")
    users_list = cur.fetchall()

    # 2. Fetch activity audit history
    cur.execute("SELECT ID, USERNAME, ACTIONS, LOG_TIME FROM history ORDER BY ID DESC LIMIT 50")
    history_logs = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        "users.html",
        active_page="users",
        title="User & Security Management",
        users=users_list,
        history_logs=history_logs
    )


@app.route("/users/add", methods=["POST"])
@role_required(["super_admin"])
def add_user_route():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role_input = request.form.get("role", "").strip().lower()

    if not username or not password:
        flash("Username and password are required.", "warning")
        return redirect(url_for("users_view"))

    canonical_role = ROLE_ALIASES.get(role_input, role_input)
    if canonical_role not in ("super_admin", "admin", "viewer"):
        flash("Invalid role assignment. Allowed roles: Principal, Teacher, Parent & Student.", "danger")
        return redirect(url_for("users_view"))

    is_valid, err_msg = validate_password_strength(password)
    if not is_valid:
        flash(err_msg, "danger")
        return redirect(url_for("users_view"))

    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(url_for("users_view"))

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT 1 FROM users WHERE USERNAME = %s", (username,))
        if cur.fetchone():
            flash(f"Username '{username}' already exists.", "danger")
            return redirect(url_for("users_view"))

        hashed = hash_password(password)
        cur.execute("INSERT INTO users (USERNAME, PASSWORD, ROLE) VALUES (%s, %s, %s)", (username, hashed, canonical_role))
        con.commit()

        curr_user = session.get("username")
        display_role = get_role_display(canonical_role)
        log_history(curr_user, f"Registered user {username} as {display_role}")
        flash(f"User '{username}' registered successfully as '{display_role}'!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(url_for("users_view"))


@app.route("/users/delete/<int:id>", methods=["POST"])
@role_required(["super_admin"])
def delete_user_route(id):
    con = get_connection()
    if not con:
        flash("Database Connection Failed.", "danger")
        return redirect(url_for("users_view"))

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT USERNAME FROM users WHERE ID = %s", (id,))
        row = cur.fetchone()
        if not row:
            flash("User not found.", "warning")
            return redirect(url_for("users_view"))

        target_username = row["USERNAME"]

        # Prevent deleting own account
        if target_username == session.get("username"):
            flash("Operation Cancelled: You cannot delete your own logged-in account!", "danger")
            return redirect(url_for("users_view"))

        cur.execute("DELETE FROM users WHERE ID = %s", (id,))
        con.commit()

        curr_user = session.get("username")
        log_history(curr_user, f"Deleted user {target_username}")
        flash(f"User account '{target_username}' has been deleted.", "info")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(url_for("users_view"))


# -------------------------------------------------------------------------
# 6. INTEGRATED MODULES (LIBRARY, ATTENDANCE, FEES, EXAMS)
# -------------------------------------------------------------------------

@app.route("/library")
@login_required
def library_view():
    tab = request.args.get("tab", "catalogue").strip().lower()
    search = request.args.get("search", "").strip()
    selected_genre = request.args.get("genre", "").strip()
    selected_status = request.args.get("status", "").strip()

    con = get_connection()
    books = []
    issues = []
    overdue_issues = []
    reservations = []
    students = []
    teachers = []
    genres = set()
    stats = {
        "total_titles": 0,
        "total_copies": 0,
        "available_copies": 0,
        "issued_copies": 0,
        "overdue_count": 0,
        "total_fines_unpaid": 0.0,
        "total_fines_collected": 0.0,
        "active_reservations": 0
    }

    if con:
        cur = con.cursor(dictionary=True)
        today = datetime.date.today()

        # 1. Fetch Books Catalogue
        cur.execute("SELECT * FROM Books_Details ORDER BY ID ASC")
        all_books = cur.fetchall()
        for b in all_books:
            if b.get("GENRE"):
                genres.add(b["GENRE"])
            b["issued_copies"] = max(0, b["TOTAL_COPIES"] - b["AVAILABLE_COPIES"])
            b["stock_status"] = "in_stock" if b["AVAILABLE_COPIES"] > 2 else ("low_stock" if b["AVAILABLE_COPIES"] > 0 else "out_of_stock")

        # Filter books if search or genre specified
        for b in all_books:
            match_search = True
            if search and tab == "catalogue":
                s_lower = search.lower()
                match_search = (s_lower in b["BOOK_ID"].lower() or 
                                s_lower in b["TITLE"].lower() or 
                                s_lower in (b["AUTHOR"] or "").lower() or
                                s_lower in (b.get("SHELF_LOCATION") or "").lower())
            match_genre = True
            if selected_genre:
                match_genre = (b.get("GENRE") == selected_genre)
            if match_search and match_genre:
                books.append(b)

        # 2. Fetch All Issues
        cur.execute("""
            SELECT i.*, b.TITLE AS BOOK_TITLE, b.AUTHOR AS BOOK_AUTHOR, b.GENRE AS BOOK_GENRE, b.SHELF_LOCATION
            FROM Book_Issues i
            LEFT JOIN Books_Details b ON i.BOOK_ID = b.BOOK_ID
            ORDER BY i.ID DESC
        """)
        all_issues = cur.fetchall()

        for iss in all_issues:
            due = iss["DUE_DATE"]
            return_dt = iss.get("RETURN_DATE")
            
            iss["issue_date_fmt"] = iss["ISSUE_DATE"].strftime("%b %d, %Y")
            iss["due_date_fmt"] = due.strftime("%b %d, %Y")
            iss["return_date_fmt"] = return_dt.strftime("%b %d, %Y") if return_dt else None

            if iss["STATUS"] == "Issued":
                if today > due:
                    iss["is_overdue"] = True
                    iss["days_overdue"] = (today - due).days
                    iss["days_left"] = 0
                    iss["display_status"] = "Overdue"
                    computed_fine = iss["days_overdue"] * 5.00
                    if float(iss.get("FINE_AMOUNT") or 0.0) < computed_fine and iss.get("FINE_STATUS") != "Paid":
                        iss["FINE_AMOUNT"] = computed_fine
                        if iss["FINE_STATUS"] == "None":
                            iss["FINE_STATUS"] = "Unpaid"
                else:
                    iss["is_overdue"] = False
                    iss["days_overdue"] = 0
                    iss["days_left"] = (due - today).days
                    iss["display_status"] = "Active"
            else:
                iss["is_overdue"] = False
                iss["days_overdue"] = 0
                iss["days_left"] = 0
                iss["display_status"] = "Returned"

            match_issue_search = True
            if search and tab in ("issues", "fines"):
                s_lower = search.lower()
                match_issue_search = (s_lower in iss["ISSUE_ID"].lower() or
                                      s_lower in iss["BOOK_ID"].lower() or
                                      s_lower in (iss.get("BOOK_TITLE") or "").lower() or
                                      s_lower in iss["BORROWER_NAME"].lower() or
                                      s_lower in iss["BORROWER_ID"].lower())
            match_status = True
            if selected_status:
                if selected_status == "overdue":
                    match_status = iss.get("is_overdue", False)
                elif selected_status == "active":
                    match_status = (iss["STATUS"] == "Issued" and not iss.get("is_overdue"))
                elif selected_status == "returned":
                    match_status = (iss["STATUS"] == "Returned")

            if match_issue_search and match_status:
                issues.append(iss)

            if iss.get("is_overdue") or (float(iss.get("FINE_AMOUNT") or 0.0) > 0 and iss.get("FINE_STATUS") == "Unpaid"):
                overdue_issues.append(iss)

        # 3. Fetch Book Reservations
        cur.execute("""
            SELECT r.*, b.TITLE AS BOOK_TITLE, b.AUTHOR AS BOOK_AUTHOR, b.AVAILABLE_COPIES
            FROM Book_Reservations r
            LEFT JOIN Books_Details b ON r.BOOK_ID = b.BOOK_ID
            ORDER BY r.ID DESC
        """)
        all_reservations = cur.fetchall()
        for res_item in all_reservations:
            res_item["reserve_date_fmt"] = res_item["RESERVE_DATE"].strftime("%b %d, %Y")
            res_item["expiry_date_fmt"] = res_item["EXPIRY_DATE"].strftime("%b %d, %Y") if res_item.get("EXPIRY_DATE") else None
            match_res = True
            if search and tab == "reservations":
                s_lower = search.lower()
                match_res = (s_lower in res_item["RESERVATION_ID"].lower() or
                             s_lower in res_item["BOOK_ID"].lower() or
                             s_lower in (res_item.get("BOOK_TITLE") or "").lower() or
                             s_lower in res_item["BORROWER_NAME"].lower() or
                             s_lower in res_item["BORROWER_ID"].lower())
            if match_res:
                reservations.append(res_item)

        # 4. Fetch Students & Faculty for autocompletion dropdowns
        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
        students = cur.fetchall()

        cur.execute("SELECT TEACHER_ID, NAME, SUBJECT FROM Teachers_Details ORDER BY TEACHER_ID ASC")
        teachers = cur.fetchall()

        # Compute Summary Stats
        stats["total_titles"] = len(all_books)
        stats["total_copies"] = sum(b["TOTAL_COPIES"] for b in all_books)
        stats["available_copies"] = sum(b["AVAILABLE_COPIES"] for b in all_books)
        stats["issued_copies"] = sum(1 for i in all_issues if i["STATUS"] == "Issued")
        stats["overdue_count"] = sum(1 for i in all_issues if i["STATUS"] == "Issued" and i.get("is_overdue"))
        stats["total_fines_unpaid"] = sum(float(i.get("FINE_AMOUNT") or 0.0) for i in all_issues if i.get("FINE_STATUS") == "Unpaid")
        stats["total_fines_collected"] = sum(float(i.get("FINE_AMOUNT") or 0.0) for i in all_issues if i.get("FINE_STATUS") == "Paid")
        stats["active_reservations"] = sum(1 for r in all_reservations if r["STATUS"] in ("Pending", "Ready for Pickup"))

        cur.close()
        con.close()

    return render_template(
        "library.html",
        active_page="library",
        title="Library & Resource Management",
        tab=tab,
        search=search,
        selected_genre=selected_genre,
        selected_status=selected_status,
        books=books,
        issues=issues,
        overdue_issues=overdue_issues,
        reservations=reservations,
        students=students,
        teachers=teachers,
        genres=sorted(list(genres)),
        stats=stats
    )


@app.route("/attendance")
@login_required
def attendance_view():
    con = get_connection()
    records = []
    students = []
    stats = {"total": 0, "present": 0, "absent": 0, "leave": 0, "rate": 0}
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT a.*, s.NAME, s.CLASS 
            FROM Attendance_Details a
            LEFT JOIN Students_Details s ON a.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY a.ATTENDANCE_DATE DESC, a.ID DESC
            LIMIT 100
        """)
        records = cur.fetchall()

        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
        students = cur.fetchall()

        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN STATUS = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN STATUS = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN STATUS = 'Leave' THEN 1 ELSE 0 END) as `leave`
            FROM Attendance_Details
        """)
        row = cur.fetchone()
        if row and row["total"]:
            stats["total"] = int(row["total"] or 0)
            stats["present"] = int(row["present"] or 0)
            stats["absent"] = int(row["absent"] or 0)
            stats["leave"] = int(row["leave"] or 0)
            stats["rate"] = round((stats["present"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0

        cur.close()
        con.close()
    return render_template(
        "attendance.html",
        active_page="attendance",
        title="Attendance Records",
        records=records,
        students=students,
        stats=stats
    )


@app.route("/attendance/add", methods=["POST"], endpoint="add_attendance")
@login_required
@role_required(["super_admin", "admin"])
def add_attendance_route():
    roll_number = request.form.get("roll_number", "").strip()
    att_date = request.form.get("attendance_date", "").strip()
    status = request.form.get("status", "Present").strip()
    remarks = request.form.get("remarks", "").strip()

    if not roll_number:
        flash("Validation Error: Student Roll Number is required.", "warning")
        return redirect(url_for("attendance_view"))

    if not att_date:
        att_date = datetime.date.today().strftime("%Y-%m-%d")

    # Normalize status
    if status.lower() in ("p", "present"):
        status = "Present"
    elif status.lower() in ("a", "absent"):
        status = "Absent"
    elif status.lower() in ("l", "leave"):
        status = "Leave"
    else:
        status = "Present"

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            student = cur.fetchone()
            if not student:
                flash(f"Validation Error: Student Roll Number '{roll_number}' was not found.", "danger")
                return redirect(url_for("attendance_view"))

            cur.execute("""
                INSERT INTO Attendance_Details (ROLL_NUMBER, ATTENDANCE_DATE, STATUS, REMARKS)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE STATUS = %s, REMARKS = %s
            """, (roll_number, att_date, status, remarks, status, remarks))
            con.commit()
            log_history(session.get("username", "Admin"), f"Marked attendance for Roll #{roll_number} as '{status}' on {att_date}")
            flash(f"Attendance recorded successfully for {student['NAME']} (Roll #{roll_number}) as '{status}' on {att_date}!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("attendance_view"))


@app.route("/fees")
@login_required
def fees_view():
    con = get_connection()
    transactions = []
    total_rev = 0.0
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT f.*, s.NAME, s.CLASS 
            FROM Fee_Transactions f
            LEFT JOIN Students_Details s ON f.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY f.PAYMENT_DATE DESC
            LIMIT 50
        """)
        transactions = cur.fetchall()

        cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) AS total FROM Fee_Transactions")
        total_rev = float(cur.fetchone()["total"] or 0)

        cur.close()
        con.close()
    return render_template("fees.html", active_page="fees", title="Fees & Finance", transactions=transactions, total_rev=total_rev)


@app.route("/exams")
@login_required
def exams_view():
    con = get_connection()
    marks = []
    students = []
    stats = {"total": 0, "avg_pct": 0, "highest": 0, "pass_count": 0}
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT m.*, s.NAME, s.CLASS 
            FROM Marks_Details m
            LEFT JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY m.ID DESC
            LIMIT 100
        """)
        raw_marks = cur.fetchall()
        for m in raw_marks:
            mo = float(m["MARKS_OBTAINED"])
            mm = float(m["MAX_MARKS"]) if m["MAX_MARKS"] else 100.0
            pct = round((mo / mm) * 100, 1) if mm > 0 else 0
            m["percentage"] = pct
            if pct >= 80:
                m["grade"] = "A+"
                m["grade_class"] = "status-active"
            elif pct >= 60:
                m["grade"] = "B"
                m["grade_class"] = "badge-blue"
            elif pct >= 40:
                m["grade"] = "C"
                m["grade_class"] = "badge-amber"
            else:
                m["grade"] = "F"
                m["grade_class"] = "badge-rose"
            marks.append(m)

        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
        students = cur.fetchall()

        if marks:
            total_evals = len(marks)
            avg_p = round(sum(m["percentage"] for m in marks) / total_evals, 1)
            highest_score = max(m["percentage"] for m in marks)
            passes = sum(1 for m in marks if m["percentage"] >= 40)
            stats["total"] = total_evals
            stats["avg_pct"] = avg_p
            stats["highest"] = highest_score
            stats["pass_count"] = passes

        cur.close()
        con.close()
    return render_template(
        "exams.html",
        active_page="exams",
        title="Examination Marks",
        marks=marks,
        students=students,
        stats=stats
    )


@app.route("/exams/add", methods=["POST"], endpoint="add_exam_mark")
@login_required
@role_required(["super_admin", "admin"])
def add_exam_mark_route():
    roll_number = request.form.get("roll_number", "").strip()
    exam_type = request.form.get("exam_type", "").strip()
    subject = request.form.get("subject", "").strip()
    marks_raw = request.form.get("marks_obtained", "").strip()
    max_marks_raw = request.form.get("max_marks", "100").strip()

    if not roll_number or not exam_type or not subject or not marks_raw:
        flash("Validation Error: Roll Number, Exam Type, Subject, and Marks Obtained are all required.", "warning")
        return redirect(url_for("exams_view"))

    try:
        marks_obtained = float(marks_raw)
        max_marks = float(max_marks_raw) if max_marks_raw else 100.0
        if marks_obtained < 0 or max_marks <= 0:
            flash("Validation Error: Marks must be positive numbers.", "danger")
            return redirect(url_for("exams_view"))
        if marks_obtained > max_marks:
            flash(f"Validation Error: Marks obtained ({marks_obtained}) cannot exceed maximum marks ({max_marks}).", "danger")
            return redirect(url_for("exams_view"))
    except ValueError:
        flash("Validation Error: Marks must be valid numerical values.", "danger")
        return redirect(url_for("exams_view"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            student = cur.fetchone()
            if not student:
                flash(f"Validation Error: Student Roll Number '{roll_number}' was not found.", "danger")
                return redirect(url_for("exams_view"))

            cur.execute("""
                INSERT INTO Marks_Details (ROLL_NUMBER, EXAM_TYPE, SUBJECT, MARKS_OBTAINED, MAX_MARKS)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE MARKS_OBTAINED = %s, MAX_MARKS = %s
            """, (roll_number, exam_type, subject, marks_obtained, max_marks, marks_obtained, max_marks))
            con.commit()
            log_history(session.get("username", "Admin"), f"Entered exam marks for Roll #{roll_number}: {subject} ({marks_obtained}/{max_marks}) in {exam_type}")
            pct = round((marks_obtained / max_marks) * 100, 1)
            flash(f"Exam marks saved successfully for {student['NAME']} (Roll #{roll_number}) in {subject}: {marks_obtained}/{max_marks} ({pct}%)!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("exams_view"))


# -------------------------------------------------------------------------
# LIBRARY MANAGEMENT ROUTES (CATALOGUE, ISSUE/RETURN, DUE DATES, FINES, RESERVATIONS)
# -------------------------------------------------------------------------

@app.route("/library/add", methods=["POST"], endpoint="add_book")
@role_required(["super_admin", "admin"])
def add_book_route():
    book_id = request.form.get("book_id", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    genre = request.form.get("genre", "").strip()
    shelf = request.form.get("shelf_location", "").strip() or None
    isbn = request.form.get("isbn", "").strip() or None
    publisher = request.form.get("publisher", "").strip() or None
    copies_raw = request.form.get("copies", "1").strip()

    if not book_id or not title:
        flash("Validation Error: Book ID and Title are required.", "warning")
        return redirect(url_for("library_view", tab="catalogue"))

    try:
        copies = max(1, int(copies_raw))
    except ValueError:
        copies = 1

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT 1 FROM Books_Details WHERE BOOK_ID = %s", (book_id,))
            if cur.fetchone():
                flash(f"Validation Error: Book ID '{book_id}' already exists in catalogue.", "danger")
            else:
                cur.execute("""
                    INSERT INTO Books_Details 
                    (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES, SHELF_LOCATION, ISBN, PUBLISHER)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (book_id, title, author, genre, copies, copies, shelf, isbn, publisher))
                con.commit()
                log_history(session.get("username", "Admin"), f"Added book ID {book_id} ({title})")
                flash(f"Book '{title}' added to library catalog successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="catalogue"))


@app.route("/library/edit/<book_id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def edit_book_route(book_id):
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    genre = request.form.get("genre", "").strip()
    shelf = request.form.get("shelf_location", "").strip() or None
    isbn = request.form.get("isbn", "").strip() or None
    publisher = request.form.get("publisher", "").strip() or None
    total_copies_raw = request.form.get("total_copies", "").strip()

    if not title:
        flash("Title cannot be empty.", "warning")
        return redirect(url_for("library_view", tab="catalogue"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID = %s", (book_id,))
            book = cur.fetchone()
            if not book:
                flash("Book not found.", "danger")
                return redirect(url_for("library_view", tab="catalogue"))

            if total_copies_raw:
                try:
                    new_total = max(1, int(total_copies_raw))
                    issued_count = max(0, book["TOTAL_COPIES"] - book["AVAILABLE_COPIES"])
                    if new_total < issued_count:
                        flash(f"Cannot reduce total copies below {issued_count} (currently issued copies).", "danger")
                        return redirect(url_for("library_view", tab="catalogue"))
                    new_available = new_total - issued_count
                except ValueError:
                    new_total = book["TOTAL_COPIES"]
                    new_available = book["AVAILABLE_COPIES"]
            else:
                new_total = book["TOTAL_COPIES"]
                new_available = book["AVAILABLE_COPIES"]

            cur.execute("""
                UPDATE Books_Details 
                SET TITLE = %s, AUTHOR = %s, GENRE = %s, TOTAL_COPIES = %s, AVAILABLE_COPIES = %s,
                    SHELF_LOCATION = %s, ISBN = %s, PUBLISHER = %s
                WHERE BOOK_ID = %s
            """, (title, author, genre, new_total, new_available, shelf, isbn, publisher, book_id))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Updated book {book_id} ({title})")
            flash(f"Book '{title}' updated successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="catalogue"))


@app.route("/library/delete/<book_id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_book_route(book_id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT COUNT(*) AS c FROM Book_Issues WHERE BOOK_ID = %s AND STATUS = 'Issued'", (book_id,))
            if cur.fetchone()["c"] > 0:
                flash("Cannot delete book: Copies of this book are currently issued to students or faculty!", "danger")
                return redirect(url_for("library_view", tab="catalogue"))

            cur.execute("DELETE FROM Books_Details WHERE BOOK_ID = %s", (book_id,))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Deleted book {book_id} from catalogue")
            flash(f"Book {book_id} deleted successfully from catalogue.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="catalogue"))


@app.route("/library/issue", methods=["POST"])
@role_required(["super_admin", "admin"])
def issue_book_route():
    book_id = request.form.get("book_id", "").strip()
    borrower_type = request.form.get("borrower_type", "Student").strip()
    borrower_id = request.form.get("borrower_id", "").strip()
    borrower_name = request.form.get("borrower_name", "").strip()
    due_days_str = request.form.get("due_days", "14").strip()
    remarks = request.form.get("remarks", "").strip() or None

    try:
        due_days = max(1, int(due_days_str))
    except ValueError:
        due_days = 14

    if not book_id or not borrower_id or not borrower_name:
        flash("Validation Error: Book, Borrower ID, and Name are required.", "warning")
        return redirect(url_for("library_view", tab="issues"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID = %s", (book_id,))
            book = cur.fetchone()
            if not book:
                flash(f"Error: Book ID '{book_id}' does not exist.", "danger")
                return redirect(url_for("library_view", tab="issues"))

            if book["AVAILABLE_COPIES"] <= 0:
                flash(f"Stock Error: No copies of '{book['TITLE']}' are available. Please place a reservation instead.", "danger")
                return redirect(url_for("library_view", tab="reservations"))

            today = datetime.date.today()
            due_date = today + datetime.timedelta(days=due_days)

            # Generate issue ID
            cur.execute("SELECT MAX(ID) AS max_id FROM Book_Issues")
            next_num = (cur.fetchone()["max_id"] or 0) + 1
            issue_id = f"ISS-{today.year}-{next_num:04d}"

            cur.execute("""
                INSERT INTO Book_Issues 
                (ISSUE_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, ISSUE_DATE, DUE_DATE, STATUS, REMARKS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Issued', %s)
            """, (issue_id, book_id, borrower_type, borrower_id, borrower_name, today, due_date, remarks))

            cur.execute("UPDATE Books_Details SET AVAILABLE_COPIES = AVAILABLE_COPIES - 1 WHERE BOOK_ID = %s", (book_id,))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Issued book {book_id} ({book['TITLE']}) to {borrower_type} {borrower_name} ({borrower_id})")
            flash(f"Book '{book['TITLE']}' issued successfully to {borrower_name}! Due date: {due_date.strftime('%b %d, %Y')}.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="issues"))


@app.route("/library/return/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def return_book_route(id):
    fine_collected = request.form.get("fine_collected") == "yes"

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT i.*, b.TITLE 
                FROM Book_Issues i
                LEFT JOIN Books_Details b ON i.BOOK_ID = b.BOOK_ID
                WHERE i.ID = %s
            """, (id,))
            iss = cur.fetchone()
            if not iss:
                flash("Issue record not found.", "warning")
                return redirect(url_for("library_view", tab="issues"))

            if iss["STATUS"] == "Returned":
                flash("Book has already been returned.", "info")
                return redirect(url_for("library_view", tab="issues"))

            today = datetime.date.today()
            due = iss["DUE_DATE"]
            days_overdue = (today - due).days if today > due else 0
            fine_amount = days_overdue * 5.00 # Rs 5 per day

            if days_overdue > 0:
                fine_status = "Paid" if fine_collected else "Unpaid"
            else:
                fine_amount = 0.00
                fine_status = "None"

            cur.execute("""
                UPDATE Book_Issues 
                SET RETURN_DATE = %s,
                    STATUS = 'Returned',
                    FINE_AMOUNT = %s,
                    FINE_STATUS = %s
                WHERE ID = %s
            """, (today, fine_amount, fine_status, id))

            # Increment available copies (bounded by total copies)
            cur.execute("""
                UPDATE Books_Details 
                SET AVAILABLE_COPIES = LEAST(TOTAL_COPIES, AVAILABLE_COPIES + 1)
                WHERE BOOK_ID = %s
            """, (iss["BOOK_ID"],))

            # Check if any pending reservation exists
            cur.execute("""
                SELECT * FROM Book_Reservations 
                WHERE BOOK_ID = %s AND STATUS = 'Pending' 
                ORDER BY ID ASC LIMIT 1
            """, (iss["BOOK_ID"],))
            pending_res = cur.fetchone()
            res_notice = ""
            if pending_res:
                cur.execute("UPDATE Book_Reservations SET STATUS = 'Ready for Pickup' WHERE ID = %s", (pending_res["ID"],))
                res_notice = f" • Notification: Reservation #{pending_res['RESERVATION_ID']} for {pending_res['BORROWER_NAME']} is now Ready for Pickup!"
            
            con.commit()
            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Returned book {iss['BOOK_ID']} (Issue {iss['ISSUE_ID']}), fine: Rs. {fine_amount} ({fine_status})")
            
            fine_msg = f" Overdue fine: ₹{fine_amount:.2f} ({fine_status})." if fine_amount > 0 else " Returned on time (No fine)."
            flash(f"Book '{iss['TITLE']}' returned successfully!{fine_msg}{res_notice}", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="issues"))


@app.route("/library/fines/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def resolve_fine_route(id):
    action = request.form.get("action", "pay").strip().lower() # 'pay' or 'waive'

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Book_Issues WHERE ID = %s", (id,))
            iss = cur.fetchone()
            if not iss:
                flash("Record not found.", "warning")
                return redirect(url_for("library_view", tab="fines"))

            new_status = "Paid" if action == "pay" else "Waived"
            cur.execute("UPDATE Book_Issues SET FINE_STATUS = %s WHERE ID = %s", (new_status, id))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"{new_status} fine of Rs. {iss['FINE_AMOUNT']} for Issue {iss['ISSUE_ID']} ({iss['BORROWER_NAME']})")
            flash(f"Fine for Issue {iss['ISSUE_ID']} ({iss['BORROWER_NAME']}) marked as {new_status.upper()} successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="fines"))


@app.route("/library/reserve", methods=["POST"])
@role_required(["super_admin", "admin"])
def reserve_book_route():
    book_id = request.form.get("book_id", "").strip()
    borrower_type = request.form.get("borrower_type", "Student").strip()
    borrower_id = request.form.get("borrower_id", "").strip()
    borrower_name = request.form.get("borrower_name", "").strip()
    notes = request.form.get("notes", "").strip() or None

    if not book_id or not borrower_id or not borrower_name:
        flash("Validation Error: Book ID, Borrower ID, and Name are required.", "warning")
        return redirect(url_for("library_view", tab="reservations"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Books_Details WHERE BOOK_ID = %s", (book_id,))
            book = cur.fetchone()
            if not book:
                flash(f"Error: Book ID '{book_id}' does not exist.", "danger")
                return redirect(url_for("library_view", tab="reservations"))

            today = datetime.date.today()
            expiry = today + datetime.timedelta(days=7)

            cur.execute("SELECT MAX(ID) AS max_id FROM Book_Reservations")
            next_num = (cur.fetchone()["max_id"] or 0) + 1
            res_id = f"RES-{today.year}-{next_num:04d}"

            status = "Ready for Pickup" if book["AVAILABLE_COPIES"] > 0 else "Pending"

            cur.execute("""
                INSERT INTO Book_Reservations 
                (RESERVATION_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, RESERVE_DATE, EXPIRY_DATE, STATUS, NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (res_id, book_id, borrower_type, borrower_id, borrower_name, today, expiry, status, notes))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Created reservation {res_id} for book {book_id} ({borrower_name})")
            flash(f"Reservation placed for '{book['TITLE']}' ({borrower_name})! Status: {status}.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="reservations"))


@app.route("/library/reserve/fulfill/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def fulfill_reservation_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT r.*, b.TITLE, b.AVAILABLE_COPIES 
                FROM Book_Reservations r
                LEFT JOIN Books_Details b ON r.BOOK_ID = b.BOOK_ID
                WHERE r.ID = %s AND r.STATUS IN ('Pending', 'Ready for Pickup')
            """, (id,))
            res_item = cur.fetchone()
            if not res_item:
                flash("Active reservation not found.", "warning")
                return redirect(url_for("library_view", tab="reservations"))

            if res_item["AVAILABLE_COPIES"] <= 0:
                flash(f"Cannot fulfill: No available stock for '{res_item['TITLE']}' right now.", "danger")
                return redirect(url_for("library_view", tab="reservations"))

            today = datetime.date.today()
            due_date = today + datetime.timedelta(days=14)

            cur.execute("SELECT MAX(ID) AS max_id FROM Book_Issues")
            next_num = (cur.fetchone()["max_id"] or 0) + 1
            issue_id = f"ISS-{today.year}-{next_num:04d}"

            cur.execute("""
                INSERT INTO Book_Issues 
                (ISSUE_ID, BOOK_ID, BORROWER_TYPE, BORROWER_ID, BORROWER_NAME, ISSUE_DATE, DUE_DATE, STATUS, REMARKS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Issued', %s)
            """, (issue_id, res_item["BOOK_ID"], res_item["BORROWER_TYPE"], res_item["BORROWER_ID"], res_item["BORROWER_NAME"], today, due_date, f"Fulfilled from {res_item['RESERVATION_ID']}"))

            cur.execute("UPDATE Book_Reservations SET STATUS = 'Fulfilled' WHERE ID = %s", (id,))
            cur.execute("UPDATE Books_Details SET AVAILABLE_COPIES = AVAILABLE_COPIES - 1 WHERE BOOK_ID = %s", (res_item["BOOK_ID"],))
            con.commit()

            curr_user = session.get("username", "Admin")
            log_history(curr_user, f"Fulfilled reservation {res_item['RESERVATION_ID']} -> Issue {issue_id}")
            flash(f"Reservation fulfilled! Book '{res_item['TITLE']}' issued to {res_item['BORROWER_NAME']} (Issue ID: {issue_id}, Due: {due_date.strftime('%b %d, %Y')}).", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="issues"))


@app.route("/library/reserve/cancel/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def cancel_reservation_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("UPDATE Book_Reservations SET STATUS = 'Cancelled' WHERE ID = %s AND STATUS IN ('Pending', 'Ready for Pickup')", (id,))
            con.commit()
            flash("Reservation has been cancelled.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view", tab="reservations"))


@app.route("/fees/add", methods=["POST"], endpoint="add_fee")
@role_required(["super_admin", "admin"])
def add_fee_route():
    roll_number = request.form.get("roll_number", "").strip()
    amount_raw = request.form.get("amount", "0").strip()
    mode = request.form.get("mode", "Cash").strip()
    remarks = request.form.get("remarks", "").strip()

    if not roll_number:
        flash("Validation Error: Student Roll Number is required.", "warning")
        return redirect(url_for("fees_view"))

    try:
        amount = float(amount_raw)
        if amount <= 0:
            flash("Validation Error: Fee amount must be greater than zero.", "danger")
            return redirect(url_for("fees_view"))
    except ValueError:
        flash("Validation Error: Fee amount must be a valid number.", "danger")
        return redirect(url_for("fees_view"))

    import datetime
    today = datetime.date.today().strftime('%Y-%m-%d')

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            # Check student exists
            cur.execute("SELECT 1 FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            if not cur.fetchone():
                flash(f"Validation Warning: Student Roll Number '{roll_number}' not found in registry.", "warning")

            cur.execute("""
                INSERT INTO Fee_Transactions (ROLL_NUMBER, AMOUNT_PAID, PAYMENT_DATE, PAYMENT_MODE, REMARKS)
                VALUES (%s, %s, %s, %s, %s)
            """, (roll_number, amount, today, mode, remarks))
            con.commit()
            log_history(session.get("username", "Admin"), f"Recorded fee ₹{amount} for Roll {roll_number}")
            flash(f"Fee transaction of ₹{amount:,.2f} recorded for Roll #{roll_number}!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("fees_view"))


# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# 6B. COURSEWORK, ASSIGNMENTS, STUDY MATERIALS, COURSES & ONLINE QUIZZES
# -------------------------------------------------------------------------

@app.route("/coursework")
@login_required
def coursework_view():
    tab = request.args.get("tab", "assignments").strip().lower()
    search = request.args.get("search", "").strip()
    selected_subject = request.args.get("subject", "").strip()
    selected_class = request.args.get("class", "").strip()
    selected_status = request.args.get("status", "").strip()
    take_quiz_code = request.args.get("take_quiz", "").strip()

    con = get_connection()
    all_assignments = []
    assignments = []
    all_materials = []
    materials = []
    all_submissions = []
    submissions = []
    courses = []
    quizzes = []
    quiz_questions_map = {}
    quiz_attempts = []
    students = []
    teachers = []
    subjects = set()
    classes = ["Grade 9", "Grade 10", "Grade 11", "Grade 12"]

    stats = {
        "total_assignments": 0,
        "active_assignments": 0,
        "total_materials": 0,
        "total_submissions": 0,
        "pending_reviews": 0,
        "total_courses": 0,
        "total_quizzes": 0,
        "total_attempts": 0,
    }

    if con:
        cur = con.cursor(dictionary=True)
        today = datetime.date.today()

        try:
            # 1. Fetch Assignments
            cur.execute("""
                SELECT a.*,
                       (SELECT COUNT(*) FROM Assignment_Submissions s WHERE s.ASSIGNMENT_CODE = a.ASSIGNMENT_CODE) AS SUBMISSION_COUNT
                FROM Assignments a
                ORDER BY a.ID DESC
            """)
            all_assignments = cur.fetchall()
            for a in all_assignments:
                if a.get("SUBJECT"):
                    subjects.add(a["SUBJECT"])
                due = a.get("DUE_DATE")
                if due:
                    a["is_overdue"] = (today > due)
                    a["days_left"] = (due - today).days
                    a["due_date_fmt"] = due.strftime("%b %d, %Y")
                else:
                    a["is_overdue"] = False
                    a["days_left"] = 0
                    a["due_date_fmt"] = "-"
                a["assigned_date_fmt"] = a["ASSIGNED_DATE"].strftime("%b %d, %Y") if a.get("ASSIGNED_DATE") else "-"

            # Filter assignments
            for a in all_assignments:
                match_search = True
                if search and tab == "assignments":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in a["ASSIGNMENT_CODE"].lower() or
                        s_lower in a["TITLE"].lower() or
                        s_lower in a["SUBJECT"].lower() or
                        s_lower in (a.get("TEACHER_NAME") or "").lower()
                    )
                match_subj = True
                if selected_subject and tab == "assignments":
                    match_subj = (a.get("SUBJECT") == selected_subject)
                match_cls = True
                if selected_class and tab == "assignments":
                    match_cls = (a.get("CLASS") == selected_class)
                match_st = True
                if selected_status and tab == "assignments":
                    match_st = (a.get("STATUS") == selected_status)

                if match_search and match_subj and match_cls and match_st:
                    assignments.append(a)

            # 2. Fetch Study Materials
            cur.execute("SELECT * FROM Study_Materials ORDER BY ID DESC")
            all_materials = cur.fetchall()
            for m in all_materials:
                if m.get("SUBJECT"):
                    subjects.add(m["SUBJECT"])
                m["upload_date_fmt"] = m["UPLOAD_DATE"].strftime("%b %d, %Y") if m.get("UPLOAD_DATE") else "-"

            # Filter materials
            for m in all_materials:
                match_search = True
                if search and tab == "materials":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in m["MATERIAL_CODE"].lower() or
                        s_lower in m["TITLE"].lower() or
                        s_lower in m["SUBJECT"].lower() or
                        s_lower in (m.get("TOPIC") or "").lower() or
                        s_lower in (m.get("UPLOADED_BY") or "").lower()
                    )
                match_subj = True
                if selected_subject and tab == "materials":
                    match_subj = (m.get("SUBJECT") == selected_subject)
                match_cls = True
                if selected_class and tab == "materials":
                    match_cls = (m.get("CLASS") == selected_class)

                if match_search and match_subj and match_cls:
                    materials.append(m)

            # 3. Fetch Submissions
            cur.execute("""
                SELECT s.*,
                       a.TITLE AS ASSIGNMENT_TITLE,
                       a.SUBJECT AS ASSIGNMENT_SUBJECT,
                       a.MAX_MARKS,
                       a.DUE_DATE AS ASSIGNMENT_DUE_DATE
                FROM Assignment_Submissions s
                LEFT JOIN Assignments a ON s.ASSIGNMENT_CODE = a.ASSIGNMENT_CODE
                ORDER BY s.ID DESC
            """)
            all_submissions = cur.fetchall()
            for s in all_submissions:
                s["submitted_date_fmt"] = s["SUBMITTED_DATE"].strftime("%b %d, %Y") if s.get("SUBMITTED_DATE") else "-"
                s["reviewed_date_fmt"] = s["REVIEWED_DATE"].strftime("%b %d, %Y") if s.get("REVIEWED_DATE") else "-"

            # Filter submissions
            for s in all_submissions:
                match_search = True
                if search and tab == "submissions":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in s["SUBMISSION_CODE"].lower() or
                        s_lower in s["ASSIGNMENT_CODE"].lower() or
                        s_lower in s["STUDENT_ROLL"].lower() or
                        s_lower in s["STUDENT_NAME"].lower() or
                        s_lower in (s.get("ASSIGNMENT_TITLE") or "").lower()
                    )
                match_st = True
                if selected_status and tab == "submissions":
                    match_st = (s.get("STATUS") == selected_status)

                if match_search and match_st:
                    submissions.append(s)

            # 4. Fetch Learning Courses
            cur.execute("SELECT * FROM Learning_Courses ORDER BY ID ASC")
            courses = cur.fetchall()
            for c in courses:
                if c.get("SUBJECT"):
                    subjects.add(c["SUBJECT"])

            # 5. Fetch Online Quizzes
            cur.execute("""
                SELECT q.*,
                       (SELECT COUNT(*) FROM Quiz_Questions qq WHERE qq.QUIZ_CODE = q.QUIZ_CODE) AS QUESTIONS_COUNT,
                       (SELECT COUNT(*) FROM Quiz_Attempts qa WHERE qa.QUIZ_CODE = q.QUIZ_CODE) AS ATTEMPTS_COUNT
                FROM Online_Quizzes q
                ORDER BY q.ID ASC
            """)
            quizzes = cur.fetchall()
            for q in quizzes:
                if q.get("SUBJECT"):
                    subjects.add(q["SUBJECT"])

            # 6. Fetch Quiz Questions (map by QUIZ_CODE)
            cur.execute("SELECT * FROM Quiz_Questions ORDER BY QUIZ_CODE ASC, QUESTION_NUMBER ASC")
            all_questions = cur.fetchall()
            for qn in all_questions:
                quiz_questions_map.setdefault(qn["QUIZ_CODE"], []).append(qn)

            # 7. Fetch Quiz Attempts
            cur.execute("""
                SELECT qa.*,
                       q.TITLE AS QUIZ_TITLE,
                       q.SUBJECT AS QUIZ_SUBJECT,
                       q.PASS_PERCENTAGE
                FROM Quiz_Attempts qa
                LEFT JOIN Online_Quizzes q ON qa.QUIZ_CODE = q.QUIZ_CODE
                ORDER BY qa.ID DESC
            """)
            quiz_attempts = cur.fetchall()
            for qa in quiz_attempts:
                qa["attempt_date_fmt"] = qa["ATTEMPT_DATE"].strftime("%b %d, %Y") if qa.get("ATTEMPT_DATE") else "-"

            # 8. Fetch Helpers (Students & Teachers)
            cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
            students = cur.fetchall()
            cur.execute("SELECT TEACHER_ID, NAME, SUBJECT FROM Teachers_Details ORDER BY NAME ASC")
            teachers = cur.fetchall()

            # Stats calculation
            stats["total_assignments"] = len(all_assignments)
            stats["active_assignments"] = sum(1 for a in all_assignments if a.get("STATUS") == "Active")
            stats["total_materials"] = len(all_materials)
            stats["total_submissions"] = len(all_submissions)
            stats["pending_reviews"] = sum(1 for s in all_submissions if s.get("STATUS") != "Graded")
            stats["total_courses"] = len(courses)
            stats["total_quizzes"] = len(quizzes)
            stats["total_attempts"] = len(quiz_attempts)

        except Error as e:
            flash(f"Database Query Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return render_template(
        "coursework.html",
        title="Coursework & LMS",
        active_page="coursework",
        tab=tab,
        stats=stats,
        assignments=assignments,
        all_assignments=all_assignments,
        materials=materials,
        submissions=submissions,
        courses=courses,
        quizzes=quizzes,
        quiz_questions_map=quiz_questions_map,
        quiz_attempts=quiz_attempts,
        students=students,
        teachers=teachers,
        subjects=sorted(list(subjects)),
        classes=classes,
        search=search,
        selected_subject=selected_subject,
        selected_class=selected_class,
        selected_status=selected_status,
        take_quiz_code=take_quiz_code
    )


@app.route("/coursework/assignments/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_assignment_route():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    class_name = request.form.get("class_name", "").strip()
    teacher_name = request.form.get("teacher_name", "").strip()
    description = request.form.get("description", "").strip()
    attachment_url = request.form.get("attachment_url", "").strip()
    due_date = request.form.get("due_date", "").strip()
    max_marks_raw = request.form.get("max_marks", "100").strip()

    if not title or not subject or not class_name or not due_date or not description:
        flash("Validation Error: Title, Subject, Class, Due Date, and Description are required.", "warning")
        return redirect(url_for("coursework_view", tab="assignments"))

    try:
        max_marks = int(max_marks_raw)
        if max_marks <= 0:
            max_marks = 100
    except ValueError:
        max_marks = 100

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Assignments")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 101
            code = f"ASN-{next_num}"

            cur.execute("""
                INSERT INTO Assignments (ASSIGNMENT_CODE, TITLE, SUBJECT, CLASS, TEACHER_NAME, DESCRIPTION, ATTACHMENT_URL, ASSIGNED_DATE, DUE_DATE, MAX_MARKS, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), %s, %s, 'Active')
            """, (code, title, subject, class_name, teacher_name or "Faculty", description, attachment_url or None, due_date, max_marks))
            con.commit()
            log_history(session.get("username", "Teacher"), f"Created assignment {code}: {title}")
            flash(f"Assignment '{title}' ({code}) published successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="assignments"))


@app.route("/coursework/assignments/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_assignment_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT ASSIGNMENT_CODE, TITLE FROM Assignments WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                code = row["ASSIGNMENT_CODE"]
                cur.execute("DELETE FROM Assignment_Submissions WHERE ASSIGNMENT_CODE = %s", (code,))
                cur.execute("DELETE FROM Assignments WHERE ID = %s", (id,))
                con.commit()
                log_history(session.get("username", "Teacher"), f"Deleted assignment {code}")
                flash(f"Assignment {code} and its submissions have been removed.", "info")
            else:
                flash("Assignment not found.", "warning")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="assignments"))


@app.route("/coursework/assignments/toggle-status/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def toggle_assignment_status_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT STATUS, ASSIGNMENT_CODE FROM Assignments WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                new_status = "Closed" if row["STATUS"] == "Active" else "Active"
                cur.execute("UPDATE Assignments SET STATUS = %s WHERE ID = %s", (new_status, id))
                con.commit()
                flash(f"Assignment {row['ASSIGNMENT_CODE']} status updated to '{new_status}'.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="assignments"))


@app.route("/coursework/materials/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_material_route():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    class_name = request.form.get("class_name", "").strip()
    topic = request.form.get("topic", "").strip()
    resource_type = request.form.get("resource_type", "Lecture Notes").strip()
    resource_url = request.form.get("resource_url", "").strip()
    content_text = request.form.get("content_text", "").strip()
    uploaded_by = request.form.get("uploaded_by", "").strip() or session.get("username", "Faculty")

    if not title or not subject or not class_name or not topic:
        flash("Validation Error: Title, Subject, Class, and Topic are required.", "warning")
        return redirect(url_for("coursework_view", tab="materials"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Study_Materials")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 201
            code = f"MAT-{next_num}"

            cur.execute("""
                INSERT INTO Study_Materials (MATERIAL_CODE, TITLE, SUBJECT, CLASS, TOPIC, RESOURCE_TYPE, RESOURCE_URL, CONTENT_TEXT, UPLOADED_BY, UPLOAD_DATE)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
            """, (code, title, subject, class_name, topic, resource_type, resource_url or None, content_text or None, uploaded_by))
            con.commit()
            log_history(session.get("username", "Teacher"), f"Uploaded study material {code}: {title}")
            flash(f"Study Material '{title}' ({code}) uploaded successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="materials"))


@app.route("/coursework/materials/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_material_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("DELETE FROM Study_Materials WHERE ID = %s", (id,))
            con.commit()
            flash("Study material item has been deleted.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="materials"))


@app.route("/coursework/submissions/submit", methods=["POST"])
@login_required
def submit_coursework_route():
    assignment_code = request.form.get("assignment_code", "").strip()
    student_roll = request.form.get("student_roll", "").strip()
    student_name = request.form.get("student_name", "").strip()
    student_class = request.form.get("student_class", "").strip()
    submission_text = request.form.get("submission_text", "").strip()
    file_url = request.form.get("file_url", "").strip()

    if not assignment_code or not student_roll or not student_name or not submission_text:
        flash("Validation Error: Assignment, Roll Number, Student Name, and Solution Content are required.", "warning")
        return redirect(url_for("coursework_view", tab="submissions"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        today = datetime.date.today()
        try:
            # Check assignment due date
            cur.execute("SELECT DUE_DATE, TITLE FROM Assignments WHERE ASSIGNMENT_CODE = %s", (assignment_code,))
            asn = cur.fetchone()
            if not asn:
                flash(f"Assignment code '{assignment_code}' not found.", "warning")
                return redirect(url_for("coursework_view", tab="submissions"))

            status = "Late Submission" if (today > asn["DUE_DATE"]) else "Submitted"

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Assignment_Submissions")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 301
            code = f"SUB-{next_num}"

            cur.execute("""
                INSERT INTO Assignment_Submissions (SUBMISSION_CODE, ASSIGNMENT_CODE, STUDENT_ROLL, STUDENT_NAME, STUDENT_CLASS, SUBMISSION_TEXT, FILE_URL, SUBMITTED_DATE, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (code, assignment_code, student_roll, student_name, student_class or "Grade 10", submission_text, file_url or None, today, status))
            con.commit()
            log_history(student_name, f"Submitted assignment work {code} for {assignment_code}")
            if status == "Late Submission":
                flash(f"Assignment submitted ({code}) — Note: Recorded as Late Submission past due date.", "warning")
            else:
                flash(f"Your assignment work ({code}) for '{asn['TITLE']}' has been submitted on time! Excellent work.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="submissions"))


@app.route("/coursework/submissions/grade/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def grade_submission_route(id):
    marks_raw = request.form.get("marks_obtained", "0").strip()
    grade = request.form.get("grade", "").strip()
    feedback = request.form.get("teacher_feedback", "").strip()
    reviewed_by = request.form.get("reviewed_by", "").strip() or session.get("username", "Teacher")

    try:
        marks = float(marks_raw)
    except ValueError:
        flash("Validation Error: Marks obtained must be a valid number.", "warning")
        return redirect(url_for("coursework_view", tab="submissions"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT SUBMISSION_CODE, STUDENT_NAME FROM Assignment_Submissions WHERE ID = %s", (id,))
            sub = cur.fetchone()
            if not sub:
                flash("Submission not found.", "warning")
                return redirect(url_for("coursework_view", tab="submissions"))

            cur.execute("""
                UPDATE Assignment_Submissions
                SET MARKS_OBTAINED = %s,
                    GRADE = %s,
                    TEACHER_FEEDBACK = %s,
                    REVIEWED_BY = %s,
                    REVIEWED_DATE = CURDATE(),
                    STATUS = 'Graded'
                WHERE ID = %s
            """, (marks, grade, feedback, reviewed_by, id))
            con.commit()
            log_history(session.get("username", "Teacher"), f"Graded submission {sub['SUBMISSION_CODE']} for {sub['STUDENT_NAME']} ({marks} pts, {grade})")
            flash(f"Submission {sub['SUBMISSION_CODE']} for {sub['STUDENT_NAME']} graded: {marks} pts (Grade: {grade})!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="submissions"))


@app.route("/coursework/courses/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_course_route():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    instructor = request.form.get("instructor", "").strip() or session.get("username", "Faculty")
    level = request.form.get("level", "Intermediate").strip()
    try:
        total_lessons = int(request.form.get("total_lessons", 10) or 10)
    except ValueError:
        total_lessons = 10
    try:
        duration_weeks = int(request.form.get("duration_weeks", 12) or 12)
    except ValueError:
        duration_weeks = 12
    description = request.form.get("description", "").strip()
    syllabus = request.form.get("syllabus", "").strip()

    if not title or not subject or not description:
        flash("Validation Error: Course Title, Subject, and Description are required.", "warning")
        return redirect(url_for("coursework_view", tab="courses"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Learning_Courses")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 401
            code = f"CRS-{next_num}"

            cur.execute("""
                INSERT INTO Learning_Courses (COURSE_CODE, TITLE, SUBJECT, INSTRUCTOR, LEVEL, TOTAL_LESSONS, DURATION_WEEKS, DESCRIPTION, SYLLABUS, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (code, title, subject, instructor, level, total_lessons, duration_weeks, description, syllabus))
            con.commit()
            log_history(session.get("username", "Teacher"), f"Created course {code}: {title}")
            flash(f"Learning Course '{title}' ({code}) launched successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="courses"))


@app.route("/coursework/quizzes/submit", methods=["POST"])
@login_required
def submit_quiz_route():
    quiz_code = request.form.get("quiz_code", "").strip()
    student_roll = request.form.get("student_roll", "").strip()
    student_name = request.form.get("student_name", "").strip()

    if not quiz_code or not student_roll or not student_name:
        flash("Validation Error: Quiz Code, Roll Number, and Student Name are required to take the quiz.", "warning")
        return redirect(url_for("coursework_view", tab="quizzes"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM Online_Quizzes WHERE QUIZ_CODE = %s", (quiz_code,))
            quiz = cur.fetchone()
            if not quiz:
                flash(f"Quiz '{quiz_code}' not found.", "warning")
                return redirect(url_for("coursework_view", tab="quizzes"))

            cur.execute("SELECT * FROM Quiz_Questions WHERE QUIZ_CODE = %s ORDER BY QUESTION_NUMBER ASC", (quiz_code,))
            questions = cur.fetchall()

            total_questions = len(questions)
            score = 0
            for q in questions:
                q_num = q["QUESTION_NUMBER"]
                user_ans = request.form.get(f"q_{q_num}", "").strip().upper()
                if user_ans and user_ans == q["CORRECT_OPTION"].upper():
                    score += 1

            percentage = round((score / total_questions) * 100, 1) if total_questions > 0 else 0
            pass_mark = quiz.get("PASS_PERCENTAGE") or 60
            passed = bool(percentage >= pass_mark)

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Quiz_Attempts")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 601
            att_code = f"ATT-{next_num}"

            cur.execute("""
                INSERT INTO Quiz_Attempts (ATTEMPT_CODE, QUIZ_CODE, STUDENT_ROLL, STUDENT_NAME, SCORE, TOTAL_QUESTIONS, PERCENTAGE, PASSED, ATTEMPT_DATE)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
            """, (att_code, quiz_code, student_roll, student_name, score, total_questions, percentage, passed))
            con.commit()

            log_history(student_name, f"Completed quiz {quiz_code} with score {score}/{total_questions} ({percentage}%)")
            if passed:
                flash(f"🎉 Congratulations {student_name}! You PASSED '{quiz['TITLE']}' scoring {score}/{total_questions} ({percentage}%). Passing mark: {pass_mark}%.", "success")
            else:
                flash(f"Quiz completed! You scored {score}/{total_questions} ({percentage}%). Passing mark is {pass_mark}%. Review the course materials and try again!", "warning")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("coursework_view", tab="quizzes"))




# -------------------------------------------------------------------------
# 6C. STUDENT HEALTH & DISCIPLINE MANAGEMENT (RESTRICTED ACCESS)
# -------------------------------------------------------------------------

@app.route("/health-discipline")
@login_required
def health_discipline_view():
    tab = request.args.get("tab", "health").strip().lower()
    search = request.args.get("search", "").strip()
    selected_class = request.args.get("class", "").strip()
    selected_blood = request.args.get("blood", "").strip()
    selected_severity = request.args.get("severity", "").strip()
    selected_status = request.args.get("status", "").strip()
    selected_category = request.args.get("category", "").strip()

    con = get_connection()
    health_profiles = []
    all_profiles = []
    medical_visits = []
    all_visits = []
    discipline_incidents = []
    all_incidents = []
    followups = []
    all_followups = []
    students = []
    teachers = []

    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    classes = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    severities = ["Minor", "Moderate", "Major", "Critical"]
    categories = [
        "Disruptive Behaviour",
        "Academic Dishonesty",
        "Bullying / Harassment",
        "Vandalism / Property Damage",
        "Late Attendance / Truancy",
        "Uniform / Dress Code Violation",
        "Physical Altercation",
        "Substance Abuse",
        "Other"
    ]
    action_types = [
        "Verbal Counseling",
        "Written Warning",
        "Parent-Teacher Meeting",
        "Student Counselor Session",
        "After-School Detention",
        "Campus Community Service",
        "Suspension (Short-term)",
        "Behavioral Contract"
    ]

    stats = {
        "total_profiles": 0,
        "students_with_allergies": 0,
        "total_visits": 0,
        "visits_this_week": 0,
        "active_incidents": 0,
        "critical_incidents": 0,
        "scheduled_followups": 0,
        "completed_followups": 0
    }

    if con:
        cur = con.cursor(dictionary=True)
        today = datetime.date.today()
        seven_days_ago = today - datetime.timedelta(days=7)

        try:
            # 1. Fetch Health Profiles
            cur.execute("SELECT * FROM Student_Health_Profiles ORDER BY ROLL_NUMBER ASC")
            all_profiles = cur.fetchall()
            for p in all_profiles:
                p["last_updated_fmt"] = p["LAST_UPDATED"].strftime("%b %d, %Y") if p.get("LAST_UPDATED") else "-"

            # Filter Profiles
            for p in all_profiles:
                match_search = True
                if search and tab == "health":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in p["ROLL_NUMBER"].lower() or
                        s_lower in p["STUDENT_NAME"].lower() or
                        s_lower in (p.get("ALLERGIES") or "").lower() or
                        s_lower in (p.get("CHRONIC_CONDITIONS") or "").lower() or
                        s_lower in (p.get("EMERGENCY_DOCTOR_NAME") or "").lower()
                    )
                match_class = True
                if selected_class and tab == "health":
                    match_class = (p.get("CLASS") == selected_class)
                match_blood = True
                if selected_blood and tab == "health":
                    match_blood = (p.get("BLOOD_GROUP") == selected_blood)

                if match_search and match_class and match_blood:
                    health_profiles.append(p)

            # 2. Fetch Medical Visits
            cur.execute("SELECT * FROM Medical_Room_Visits ORDER BY ID DESC")
            all_visits = cur.fetchall()
            for v in all_visits:
                v_date = v.get("VISIT_DATE")
                v["visit_date_fmt"] = v_date.strftime("%b %d, %Y") if v_date else "-"
                time_val = v.get("VISIT_TIME")
                v["visit_time_fmt"] = str(time_val)[:5] if time_val else "-"

            # Filter Visits
            for v in all_visits:
                match_search = True
                if search and tab == "medical_visits":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in v["VISIT_CODE"].lower() or
                        s_lower in v["ROLL_NUMBER"].lower() or
                        s_lower in v["STUDENT_NAME"].lower() or
                        s_lower in v["SYMPTOMS"].lower() or
                        s_lower in (v.get("ATTENDING_STAFF") or "").lower() or
                        s_lower in (v.get("OUTCOME") or "").lower()
                    )
                match_class = True
                if selected_class and tab == "medical_visits":
                    match_class = (v.get("CLASS") == selected_class)

                if match_search and match_class:
                    medical_visits.append(v)

            # 3. Fetch Discipline Incidents
            cur.execute("SELECT * FROM Discipline_Incidents ORDER BY ID DESC")
            all_incidents = cur.fetchall()
            for inc in all_incidents:
                i_date = inc.get("INCIDENT_DATE")
                inc["incident_date_fmt"] = i_date.strftime("%b %d, %Y") if i_date else "-"

            # Filter Incidents
            for inc in all_incidents:
                match_search = True
                if search and tab == "discipline":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in inc["INCIDENT_CODE"].lower() or
                        s_lower in inc["ROLL_NUMBER"].lower() or
                        s_lower in inc["STUDENT_NAME"].lower() or
                        s_lower in inc["DESCRIPTION"].lower() or
                        s_lower in (inc.get("REPORTED_BY") or "").lower() or
                        s_lower in (inc.get("LOCATION") or "").lower()
                    )
                match_class = True
                if selected_class and tab == "discipline":
                    match_class = (inc.get("CLASS") == selected_class)
                match_sev = True
                if selected_severity and tab == "discipline":
                    match_sev = (inc.get("SEVERITY") == selected_severity)
                match_cat = True
                if selected_category and tab == "discipline":
                    match_cat = (inc.get("CATEGORY") == selected_category)
                match_st = True
                if selected_status and tab == "discipline":
                    match_st = (inc.get("STATUS") == selected_status)

                if match_search and match_class and match_sev and match_cat and match_st:
                    discipline_incidents.append(inc)

            # 4. Fetch Follow-up Interventions
            cur.execute("""
                SELECT f.*, i.CATEGORY AS INCIDENT_CATEGORY, i.SEVERITY AS INCIDENT_SEVERITY, i.DESCRIPTION AS INCIDENT_DESCRIPTION
                FROM Discipline_Followups f
                LEFT JOIN Discipline_Incidents i ON f.INCIDENT_CODE = i.INCIDENT_CODE
                ORDER BY f.ID DESC
            """)
            all_followups = cur.fetchall()
            for fol in all_followups:
                s_date = fol.get("SCHEDULED_DATE")
                c_date = fol.get("COMPLETION_DATE")
                fol["scheduled_date_fmt"] = s_date.strftime("%b %d, %Y") if s_date else "-"
                fol["completion_date_fmt"] = c_date.strftime("%b %d, %Y") if c_date else "-"

            # Filter Followups
            for fol in all_followups:
                match_search = True
                if search and tab == "followups":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in fol["FOLLOWUP_CODE"].lower() or
                        s_lower in fol["INCIDENT_CODE"].lower() or
                        s_lower in fol["ROLL_NUMBER"].lower() or
                        s_lower in fol["STUDENT_NAME"].lower() or
                        s_lower in (fol.get("ASSIGNED_TO") or "").lower() or
                        s_lower in (fol.get("ACTION_TYPE") or "").lower()
                    )
                match_st = True
                if selected_status and tab == "followups":
                    match_st = (fol.get("STATUS") == selected_status)

                if match_search and match_st:
                    followups.append(fol)

            # 5. Fetch Helpers
            cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
            students = cur.fetchall()
            cur.execute("SELECT TEACHER_ID, NAME, SUBJECT FROM Teachers_Details ORDER BY NAME ASC")
            teachers = cur.fetchall()

            # Stats
            stats["total_profiles"] = len(all_profiles)
            stats["students_with_allergies"] = sum(1 for p in all_profiles if p.get("ALLERGIES") and p["ALLERGIES"].lower() != "none")
            stats["total_visits"] = len(all_visits)
            stats["visits_this_week"] = sum(1 for v in all_visits if v.get("VISIT_DATE") and v["VISIT_DATE"] >= seven_days_ago)
            stats["active_incidents"] = sum(1 for inc in all_incidents if inc.get("STATUS") in ("Reported", "Under Investigation", "Action Pending", "Follow-up Scheduled"))
            stats["critical_incidents"] = sum(1 for inc in all_incidents if inc.get("SEVERITY") in ("Major", "Critical"))
            stats["scheduled_followups"] = sum(1 for fol in all_followups if fol.get("STATUS") in ("Scheduled", "In Progress"))
            stats["completed_followups"] = sum(1 for fol in all_followups if fol.get("STATUS") == "Completed")

        except Error as e:
            flash(f"Database Query Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return render_template(
        "health_discipline.html",
        title="Health & Discipline Records",
        active_page="health_discipline",
        tab=tab,
        stats=stats,
        health_profiles=health_profiles,
        all_profiles=all_profiles,
        medical_visits=medical_visits,
        discipline_incidents=discipline_incidents,
        all_incidents=all_incidents,
        followups=followups,
        students=students,
        teachers=teachers,
        blood_groups=blood_groups,
        classes=classes,
        severities=severities,
        categories=categories,
        action_types=action_types,
        search=search,
        selected_class=selected_class,
        selected_blood=selected_blood,
        selected_severity=selected_severity,
        selected_status=selected_status,
        selected_category=selected_category
    )


@app.route("/health-discipline/health-profile/save", methods=["POST"])
@role_required(["super_admin", "admin"])
def save_health_profile_route():
    roll_number = request.form.get("roll_number", "").strip()
    blood_group = request.form.get("blood_group", "Unknown").strip()
    allergies = request.form.get("allergies", "None").strip()
    chronic_conditions = request.form.get("chronic_conditions", "None").strip()
    medications = request.form.get("medications", "None").strip()
    doctor_name = request.form.get("emergency_doctor_name", "").strip()
    doctor_phone = request.form.get("emergency_doctor_phone", "").strip()
    insurance_policy = request.form.get("insurance_policy_no", "").strip()
    special_care = request.form.get("special_care_instructions", "").strip()
    vaccination_status = request.form.get("vaccination_status", "Up to Date").strip()

    if not roll_number:
        flash("Validation Error: Student Roll Number is required.", "warning")
        return redirect(url_for("health_discipline_view", tab="health"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            # Check student exists
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            st = cur.fetchone()
            if not st:
                flash(f"Student with Roll #{roll_number} not found in school registry.", "warning")
                return redirect(url_for("health_discipline_view", tab="health"))

            name = st["NAME"]
            cls = st["CLASS"]

            cur.execute("""
                INSERT INTO Student_Health_Profiles
                (ROLL_NUMBER, STUDENT_NAME, CLASS, BLOOD_GROUP, ALLERGIES, CHRONIC_CONDITIONS, MEDICATIONS,
                 EMERGENCY_DOCTOR_NAME, EMERGENCY_DOCTOR_PHONE, INSURANCE_POLICY_NO, SPECIAL_CARE_INSTRUCTIONS, VACCINATION_STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    STUDENT_NAME = VALUES(STUDENT_NAME),
                    CLASS = VALUES(CLASS),
                    BLOOD_GROUP = VALUES(BLOOD_GROUP),
                    ALLERGIES = VALUES(ALLERGIES),
                    CHRONIC_CONDITIONS = VALUES(CHRONIC_CONDITIONS),
                    MEDICATIONS = VALUES(MEDICATIONS),
                    EMERGENCY_DOCTOR_NAME = VALUES(EMERGENCY_DOCTOR_NAME),
                    EMERGENCY_DOCTOR_PHONE = VALUES(EMERGENCY_DOCTOR_PHONE),
                    INSURANCE_POLICY_NO = VALUES(INSURANCE_POLICY_NO),
                    SPECIAL_CARE_INSTRUCTIONS = VALUES(SPECIAL_CARE_INSTRUCTIONS),
                    VACCINATION_STATUS = VALUES(VACCINATION_STATUS)
            """, (roll_number, name, cls, blood_group, allergies, chronic_conditions, medications, doctor_name, doctor_phone, insurance_policy, special_care, vaccination_status))
            con.commit()
            log_history(session.get("username", "Staff"), f"Saved health profile for {name} ({roll_number})")
            flash(f"Health profile for '{name}' (Roll #{roll_number}) saved successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="health"))


@app.route("/health-discipline/medical-visit/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_medical_visit_route():
    roll_number = request.form.get("roll_number", "").strip()
    symptoms = request.form.get("symptoms", "").strip()
    diagnosis = request.form.get("diagnosis_observation", "").strip()
    treatment = request.form.get("treatment_given", "").strip()
    attending = request.form.get("attending_staff", "").strip() or session.get("username", "Nurse Anita Roy")
    parent_notified = request.form.get("parent_notified", "No").strip()
    outcome = request.form.get("outcome", "Returned to Class").strip()
    confidential_notes = request.form.get("confidential_notes", "").strip()

    if not roll_number or not symptoms or not treatment:
        flash("Validation Error: Student Roll Number, Symptoms, and Treatment Given are required.", "warning")
        return redirect(url_for("health_discipline_view", tab="medical_visits"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            st = cur.fetchone()
            if not st:
                flash(f"Student with Roll #{roll_number} not found.", "warning")
                return redirect(url_for("health_discipline_view", tab="medical_visits"))

            name = st["NAME"]
            cls = st["CLASS"]

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Medical_Room_Visits")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 101
            visit_code = f"MED-{next_num}"

            now_time = datetime.datetime.now().strftime("%H:%M:%S")

            cur.execute("""
                INSERT INTO Medical_Room_Visits
                (VISIT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, VISIT_DATE, VISIT_TIME, SYMPTOMS,
                 DIAGNOSIS_OBSERVATION, TREATMENT_GIVEN, ATTENDING_STAFF, PARENT_NOTIFIED, OUTCOME, CONFIDENTIAL_NOTES)
                VALUES (%s, %s, %s, %s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s)
            """, (visit_code, roll_number, name, cls, now_time, symptoms, diagnosis, treatment, attending, parent_notified, outcome, confidential_notes))
            con.commit()
            log_history(session.get("username", "Staff"), f"Logged medical room visit {visit_code} for {name}")
            flash(f"Medical-room visit recorded ({visit_code}) for '{name}'!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="medical_visits"))


@app.route("/health-discipline/medical-visit/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_medical_visit_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("DELETE FROM Medical_Room_Visits WHERE ID = %s", (id,))
            con.commit()
            flash("Medical visit record deleted successfully.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="medical_visits"))


@app.route("/health-discipline/incident/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_discipline_incident_route():
    roll_number = request.form.get("roll_number", "").strip()
    incident_date = request.form.get("incident_date", "").strip()
    category = request.form.get("category", "Disruptive Behaviour").strip()
    severity = request.form.get("severity", "Minor").strip()
    location = request.form.get("location", "Classroom").strip()
    reported_by = request.form.get("reported_by", "").strip() or session.get("username", "Faculty")
    description = request.form.get("description", "").strip()
    witnesses = request.form.get("witnesses", "").strip()

    if not roll_number or not description:
        flash("Validation Error: Student Roll Number and Incident Description are required.", "warning")
        return redirect(url_for("health_discipline_view", tab="discipline"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
            st = cur.fetchone()
            if not st:
                flash(f"Student with Roll #{roll_number} not found.", "warning")
                return redirect(url_for("health_discipline_view", tab="discipline"))

            name = st["NAME"]
            cls = st["CLASS"]

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Discipline_Incidents")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 201
            inc_code = f"DIS-{next_num}"

            date_val = incident_date if incident_date else datetime.date.today().strftime("%Y-%m-%d")

            cur.execute("""
                INSERT INTO Discipline_Incidents
                (INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, CLASS, INCIDENT_DATE, CATEGORY, SEVERITY, LOCATION, REPORTED_BY, DESCRIPTION, WITNESSES, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Reported')
            """, (inc_code, roll_number, name, cls, date_val, category, severity, location, reported_by, description, witnesses))
            con.commit()
            log_history(session.get("username", "Staff"), f"Logged behaviour incident {inc_code} for {name} ({severity})")
            flash(f"Disciplinary incident recorded ({inc_code}) for '{name}' with severity '{severity}'.", "warning" if severity in ("Major", "Critical") else "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="discipline"))


@app.route("/health-discipline/incident/update-status/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def update_incident_status_route(id):
    new_status = request.form.get("status", "Under Investigation").strip()

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("UPDATE Discipline_Incidents SET STATUS = %s WHERE ID = %s", (new_status, id))
            con.commit()
            flash(f"Incident status updated to '{new_status}'.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="discipline"))


@app.route("/health-discipline/incident/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_discipline_incident_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT INCIDENT_CODE FROM Discipline_Incidents WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                inc_code = row["INCIDENT_CODE"]
                cur.execute("DELETE FROM Discipline_Followups WHERE INCIDENT_CODE = %s", (inc_code,))
                cur.execute("DELETE FROM Discipline_Incidents WHERE ID = %s", (id,))
                con.commit()
                flash(f"Discipline incident {inc_code} and associated follow-up actions deleted.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="discipline"))


@app.route("/health-discipline/followup/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_discipline_followup_route():
    incident_code = request.form.get("incident_code", "").strip()
    action_type = request.form.get("action_type", "Verbal Counseling").strip()
    assigned_to = request.form.get("assigned_to", "").strip() or session.get("username", "School Counselor")
    scheduled_date = request.form.get("scheduled_date", "").strip()
    outcome_notes = request.form.get("outcome_notes", "").strip()

    if not incident_code or not scheduled_date:
        flash("Validation Error: Linked Incident Code and Scheduled Date are required.", "warning")
        return redirect(url_for("health_discipline_view", tab="followups"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT ROLL_NUMBER, STUDENT_NAME FROM Discipline_Incidents WHERE INCIDENT_CODE = %s", (incident_code,))
            inc = cur.fetchone()
            if not inc:
                flash(f"Incident {incident_code} not found in incident registry.", "warning")
                return redirect(url_for("health_discipline_view", tab="followups"))

            roll = inc["ROLL_NUMBER"]
            name = inc["STUDENT_NAME"]

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Discipline_Followups")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 301
            fol_code = f"FOL-{next_num}"

            cur.execute("""
                INSERT INTO Discipline_Followups
                (FOLLOWUP_CODE, INCIDENT_CODE, ROLL_NUMBER, STUDENT_NAME, ACTION_TYPE, ASSIGNED_TO, SCHEDULED_DATE, STATUS, OUTCOME_NOTES, PARENT_ACKNOWLEDGED)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Scheduled', %s, FALSE)
            """, (fol_code, incident_code, roll, name, action_type, assigned_to, scheduled_date, outcome_notes))

            # Update linked incident status to Follow-up Scheduled
            cur.execute("UPDATE Discipline_Incidents SET STATUS = 'Follow-up Scheduled' WHERE INCIDENT_CODE = %s", (incident_code,))
            con.commit()

            log_history(session.get("username", "Staff"), f"Scheduled follow-up {fol_code} ({action_type}) for incident {incident_code}")
            flash(f"Follow-up intervention ({fol_code}) scheduled for '{name}' with {assigned_to}.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="followups"))


@app.route("/health-discipline/followup/complete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def complete_discipline_followup_route(id):
    status = request.form.get("status", "Completed").strip()
    outcome_notes = request.form.get("outcome_notes", "").strip()
    parent_acknowledged = bool(request.form.get("parent_acknowledged"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT FOLLOWUP_CODE, INCIDENT_CODE FROM Discipline_Followups WHERE ID = %s", (id,))
            fol = cur.fetchone()
            if not fol:
                flash("Follow-up action not found.", "warning")
                return redirect(url_for("health_discipline_view", tab="followups"))

            if status == "Completed":
                cur.execute("""
                    UPDATE Discipline_Followups
                    SET STATUS = %s,
                        COMPLETION_DATE = CURDATE(),
                        OUTCOME_NOTES = %s,
                        PARENT_ACKNOWLEDGED = %s
                    WHERE ID = %s
                """, (status, outcome_notes, parent_acknowledged, id))
                # Also resolve the linked incident
                cur.execute("UPDATE Discipline_Incidents SET STATUS = 'Resolved' WHERE INCIDENT_CODE = %s", (fol["INCIDENT_CODE"],))
            else:
                cur.execute("""
                    UPDATE Discipline_Followups
                    SET STATUS = %s,
                        OUTCOME_NOTES = %s,
                        PARENT_ACKNOWLEDGED = %s
                    WHERE ID = %s
                """, (status, outcome_notes, parent_acknowledged, id))

            con.commit()
            log_history(session.get("username", "Staff"), f"Updated follow-up {fol['FOLLOWUP_CODE']} to {status}")
            flash(f"Follow-up action {fol['FOLLOWUP_CODE']} updated to '{status}'!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("health_discipline_view", tab="followups"))




# -------------------------------------------------------------------------
# 6D. SCHOOL CALENDAR & PARENT-TEACHER MEETINGS (PTM)
# -------------------------------------------------------------------------

@app.route("/calendar-ptm")
@login_required
def calendar_ptm_view():
    tab = request.args.get("tab", "events").strip().lower()
    search = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_type = request.args.get("type", "").strip()
    selected_teacher = request.args.get("teacher", "").strip()
    selected_status = request.args.get("status", "").strip()

    con = get_connection()
    events = []
    all_events = []
    holidays = []
    all_holidays = []
    slots = []
    all_slots = []
    bookings = []
    all_bookings = []
    reminders = []
    all_reminders = []
    students = []
    parents_map = {}
    teachers = []

    event_categories = ['Academic', 'Examination', 'Sports', 'Cultural', 'Meeting', 'Exhibition', 'Workshop', 'Holiday']
    holiday_types = ['National Holiday', 'Gazetted Holiday', 'Term Break', 'Emergency Closure', 'Restricted Holiday']
    meeting_modes = ['In-Person (Campus)', 'Virtual (Google Meet / Zoom)', 'Phone Call']

    stats = {
        "total_events": 0,
        "upcoming_events": 0,
        "total_holidays": 0,
        "upcoming_holidays": 0,
        "total_slots": 0,
        "available_slots": 0,
        "confirmed_bookings": 0,
        "active_reminders": 0
    }

    if con:
        cur = con.cursor(dictionary=True)
        today = datetime.date.today()

        try:
            # 1. Fetch School Events
            cur.execute("SELECT * FROM School_Events ORDER BY EVENT_DATE ASC, START_TIME ASC")
            all_events = cur.fetchall()
            for e in all_events:
                e_date = e.get("EVENT_DATE")
                e["is_upcoming"] = (e_date >= today) if e_date else False
                e["days_left"] = (e_date - today).days if e_date else 0
                e["event_date_fmt"] = e_date.strftime("%b %d, %Y") if e_date else "-"
                s_time = e.get("START_TIME")
                e["start_time_fmt"] = str(s_time)[:5] if s_time else ""
                end_time = e.get("END_TIME")
                e["end_time_fmt"] = str(end_time)[:5] if end_time else ""

            # Filter Events
            for e in all_events:
                match_search = True
                if search and tab == "events":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in e["EVENT_CODE"].lower() or
                        s_lower in e["TITLE"].lower() or
                        s_lower in (e.get("LOCATION") or "").lower() or
                        s_lower in (e.get("ORGANIZER") or "").lower()
                    )
                match_cat = True
                if selected_category and tab == "events":
                    match_cat = (e.get("CATEGORY") == selected_category)
                match_st = True
                if selected_status and tab == "events":
                    match_st = (e.get("STATUS") == selected_status)

                if match_search and match_cat and match_st:
                    events.append(e)

            # 2. Fetch School Holidays
            cur.execute("SELECT *, DATEDIFF(END_DATE, START_DATE) + 1 AS DURATION_DAYS FROM School_Holidays ORDER BY START_DATE ASC")
            all_holidays = cur.fetchall()
            for h in all_holidays:
                s_date = h.get("START_DATE")
                e_date = h.get("END_DATE")
                h["start_date_fmt"] = s_date.strftime("%b %d, %Y") if s_date else "-"
                h["end_date_fmt"] = e_date.strftime("%b %d, %Y") if e_date else "-"
                h["is_active_now"] = (s_date <= today <= e_date) if (s_date and e_date) else False
                h["days_left"] = (s_date - today).days if s_date else 0

            # Filter Holidays
            for h in all_holidays:
                match_search = True
                if search and tab == "holidays":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in h["HOLIDAY_NAME"].lower() or
                        s_lower in (h.get("DESCRIPTION") or "").lower()
                    )
                match_type = True
                if selected_type and tab == "holidays":
                    match_type = (h.get("HOLIDAY_TYPE") == selected_type)

                if match_search and match_type:
                    holidays.append(h)

            # 3. Fetch PTM Meeting Slots
            cur.execute("""
                SELECT s.*,
                       (SELECT COUNT(*) FROM PTM_Bookings b WHERE b.SLOT_CODE = s.SLOT_CODE AND b.STATUS = 'Confirmed') AS BOOKED_COUNT
                FROM PTM_Meeting_Slots s
                ORDER BY s.MEETING_DATE ASC, s.START_TIME ASC
            """)
            all_slots = cur.fetchall()
            for s in all_slots:
                m_date = s.get("MEETING_DATE")
                s["meeting_date_fmt"] = m_date.strftime("%b %d, %Y") if m_date else "-"
                st_time = s.get("START_TIME")
                en_time = s.get("END_TIME")
                s["start_time_fmt"] = str(st_time)[:5] if st_time else ""
                s["end_time_fmt"] = str(en_time)[:5] if en_time else ""
                s["time_range"] = f"{s['start_time_fmt']} - {s['end_time_fmt']}"

            # Filter Slots
            for s in all_slots:
                match_search = True
                if search and tab == "slots":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in s["SLOT_CODE"].lower() or
                        s_lower in s["TEACHER_NAME"].lower() or
                        s_lower in s["SUBJECT"].lower() or
                        s_lower in (s.get("ROOM_OR_LINK") or "").lower()
                    )
                match_teach = True
                if selected_teacher and tab == "slots":
                    match_teach = (s.get("TEACHER_ID") == selected_teacher or s.get("TEACHER_NAME") == selected_teacher)
                match_st = True
                if selected_status and tab == "slots":
                    match_st = (s.get("STATUS") == selected_status)

                if match_search and match_teach and match_st:
                    slots.append(s)

            # 4. Fetch PTM Bookings
            cur.execute("""
                SELECT b.*,
                       s.TEACHER_ID, s.TEACHER_NAME, s.SUBJECT, s.MEETING_DATE, s.START_TIME, s.END_TIME, s.MEETING_MODE, s.ROOM_OR_LINK
                FROM PTM_Bookings b
                JOIN PTM_Meeting_Slots s ON b.SLOT_CODE = s.SLOT_CODE
                ORDER BY s.MEETING_DATE ASC, s.START_TIME ASC
            """)
            all_bookings = cur.fetchall()
            for b in all_bookings:
                m_date = b.get("MEETING_DATE")
                b["meeting_date_fmt"] = m_date.strftime("%b %d, %Y") if m_date else "-"
                st_time = b.get("START_TIME")
                en_time = b.get("END_TIME")
                b["time_range"] = f"{str(st_time)[:5]} - {str(en_time)[:5]}"
                b["booked_at_fmt"] = b["BOOKED_AT"].strftime("%b %d, %Y") if b.get("BOOKED_AT") else "-"

            # Filter Bookings
            for b in all_bookings:
                match_search = True
                if search and tab == "bookings":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in b["BOOKING_CODE"].lower() or
                        s_lower in b["SLOT_CODE"].lower() or
                        s_lower in b["STUDENT_ROLL"].lower() or
                        s_lower in b["STUDENT_NAME"].lower() or
                        s_lower in b["PARENT_NAME"].lower() or
                        s_lower in b["TEACHER_NAME"].lower() or
                        s_lower in b["DISCUSSION_TOPIC"].lower()
                    )
                match_st = True
                if selected_status and tab == "bookings":
                    match_st = (b.get("STATUS") == selected_status)

                if match_search and match_st:
                    bookings.append(b)

            # 5. Fetch Calendar Reminders
            cur.execute("SELECT * FROM Calendar_Reminders ORDER BY REMINDER_DATE ASC, ID DESC")
            all_reminders = cur.fetchall()
            for r in all_reminders:
                r_date = r.get("REMINDER_DATE")
                r["reminder_date_fmt"] = r_date.strftime("%b %d, %Y") if r_date else "-"

            for r in all_reminders:
                match_search = True
                if search and tab == "reminders":
                    s_lower = search.lower()
                    match_search = (
                        s_lower in r["REMINDER_CODE"].lower() or
                        s_lower in r["TITLE"].lower() or
                        s_lower in r["MESSAGE"].lower() or
                        s_lower in (r.get("RECIPIENT_NAME") or "").lower()
                    )
                match_st = True
                if selected_status and tab == "reminders":
                    match_st = (r.get("STATUS") == selected_status)

                if match_search and match_st:
                    reminders.append(r)

            # 6. Fetch Helpers (Students, Parents, Teachers)
            cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
            students = cur.fetchall()

            cur.execute("SELECT ROLL_NUMBER, FATHER_NAME, PRIMARY_CONTACT, EMAIL FROM Parents_Details")
            for p in cur.fetchall():
                parents_map[p["ROLL_NUMBER"]] = p

            cur.execute("SELECT TEACHER_ID, NAME, SUBJECT FROM Teachers_Details ORDER BY NAME ASC")
            teachers = cur.fetchall()

            # Stats calculation
            stats["total_events"] = len(all_events)
            stats["upcoming_events"] = sum(1 for e in all_events if e.get("EVENT_DATE") and e["EVENT_DATE"] >= today)
            stats["total_holidays"] = len(all_holidays)
            stats["upcoming_holidays"] = sum(1 for h in all_holidays if h.get("END_DATE") and h["END_DATE"] >= today)
            stats["total_slots"] = len(all_slots)
            stats["available_slots"] = sum(1 for s in all_slots if s.get("STATUS") == "Available")
            stats["confirmed_bookings"] = sum(1 for b in all_bookings if b.get("STATUS") == "Confirmed")
            stats["active_reminders"] = sum(1 for r in all_reminders if r.get("STATUS") == "Active")

        except Error as e:
            flash(f"Database Query Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return render_template(
        "calendar_ptm.html",
        title="School Calendar & Parent-Teacher Meetings",
        active_page="calendar_ptm",
        tab=tab,
        stats=stats,
        events=events,
        all_events=all_events,
        holidays=holidays,
        all_holidays=all_holidays,
        slots=slots,
        all_slots=all_slots,
        bookings=bookings,
        all_bookings=all_bookings,
        reminders=reminders,
        all_reminders=all_reminders,
        students=students,
        parents_map=parents_map,
        teachers=teachers,
        event_categories=event_categories,
        holiday_types=holiday_types,
        meeting_modes=meeting_modes,
        search=search,
        selected_category=selected_category,
        selected_type=selected_type,
        selected_teacher=selected_teacher,
        selected_status=selected_status
    )


@app.route("/calendar-ptm/events/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_calendar_event_route():
    title = request.form.get("title", "").strip()
    event_date = request.form.get("event_date", "").strip()
    start_time = request.form.get("start_time", "09:00").strip()
    end_time = request.form.get("end_time", "12:00").strip()
    category = request.form.get("category", "Academic").strip()
    location = request.form.get("location", "Main Campus").strip()
    target_audience = request.form.get("target_audience", "All Students").strip()
    organizer = request.form.get("organizer", "").strip() or session.get("username", "Faculty")
    description = request.form.get("description", "").strip()

    if not title or not event_date:
        flash("Validation Error: Event Title and Date are required.", "warning")
        return redirect(url_for("calendar_ptm_view", tab="events"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM School_Events")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 101
            code = f"EVT-{next_num}"

            cur.execute("""
                INSERT INTO School_Events (EVENT_CODE, TITLE, EVENT_DATE, START_TIME, END_TIME, CATEGORY, LOCATION, TARGET_AUDIENCE, ORGANIZER, DESCRIPTION, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')
            """, (code, title, event_date, start_time, end_time, category, location, target_audience, organizer, description))
            con.commit()
            log_history(session.get("username", "Admin"), f"Scheduled school event {code}: {title}")
            flash(f"School event '{title}' ({code}) scheduled on calendar!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="events"))


@app.route("/calendar-ptm/events/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_calendar_event_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT TITLE, EVENT_CODE FROM School_Events WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM School_Events WHERE ID = %s", (id,))
                con.commit()
                flash(f"Event {row['EVENT_CODE']} ({row['TITLE']}) deleted.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="events"))


@app.route("/calendar-ptm/holidays/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_calendar_holiday_route():
    holiday_name = request.form.get("holiday_name", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip() or start_date
    holiday_type = request.form.get("holiday_type", "Gazetted Holiday").strip()
    description = request.form.get("description", "").strip()

    if not holiday_name or not start_date:
        flash("Validation Error: Holiday Name and Start Date are required.", "warning")
        return redirect(url_for("calendar_ptm_view", tab="holidays"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                INSERT INTO School_Holidays (HOLIDAY_NAME, START_DATE, END_DATE, HOLIDAY_TYPE, DESCRIPTION, IS_ACADEMIC_OFF)
                VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (holiday_name, start_date, end_date, holiday_type, description))
            con.commit()
            log_history(session.get("username", "Admin"), f"Added school holiday: {holiday_name}")
            flash(f"Holiday '{holiday_name}' added to school academic calendar!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="holidays"))


@app.route("/calendar-ptm/holidays/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_calendar_holiday_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT HOLIDAY_NAME FROM School_Holidays WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                cur.execute("DELETE FROM School_Holidays WHERE ID = %s", (id,))
                con.commit()
                flash(f"Holiday '{row['HOLIDAY_NAME']}' removed from calendar.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="holidays"))


@app.route("/calendar-ptm/slots/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_ptm_slot_route():
    teacher_id = request.form.get("teacher_id", "").strip()
    meeting_date = request.form.get("meeting_date", "").strip()
    start_time = request.form.get("start_time", "10:00").strip()
    end_time = request.form.get("end_time", "10:20").strip()
    meeting_mode = request.form.get("meeting_mode", "In-Person (Campus)").strip()
    room_or_link = request.form.get("room_or_link", "Staff Room Block A").strip()
    notes = request.form.get("notes", "").strip()

    if not teacher_id or not meeting_date:
        flash("Validation Error: Teacher and Meeting Date are required.", "warning")
        return redirect(url_for("calendar_ptm_view", tab="slots"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT NAME, SUBJECT FROM Teachers_Details WHERE TEACHER_ID = %s", (teacher_id,))
            teacher = cur.fetchone()
            if not teacher:
                flash(f"Teacher with ID '{teacher_id}' not found.", "warning")
                return redirect(url_for("calendar_ptm_view", tab="slots"))

            teacher_name = teacher["NAME"]
            subject = teacher["SUBJECT"]

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM PTM_Meeting_Slots")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 201
            slot_code = f"SLT-{next_num}"

            cur.execute("""
                INSERT INTO PTM_Meeting_Slots (SLOT_CODE, TEACHER_ID, TEACHER_NAME, SUBJECT, MEETING_DATE, START_TIME, END_TIME, MEETING_MODE, ROOM_OR_LINK, STATUS, NOTES)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available', %s)
            """, (slot_code, teacher_id, teacher_name, subject, meeting_date, start_time, end_time, meeting_mode, room_or_link, notes))
            con.commit()
            log_history(session.get("username", "Teacher"), f"Created PTM slot {slot_code} for {teacher_name}")
            flash(f"Meeting slot {slot_code} created for {teacher_name} ({subject}) on {meeting_date}!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="slots"))


@app.route("/calendar-ptm/slots/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_ptm_slot_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT SLOT_CODE FROM PTM_Meeting_Slots WHERE ID = %s", (id,))
            row = cur.fetchone()
            if row:
                slot_code = row["SLOT_CODE"]
                cur.execute("DELETE FROM PTM_Bookings WHERE SLOT_CODE = %s", (slot_code,))
                cur.execute("DELETE FROM PTM_Meeting_Slots WHERE ID = %s", (id,))
                con.commit()
                flash(f"Meeting slot {slot_code} deleted.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="slots"))


@app.route("/calendar-ptm/bookings/book", methods=["POST"])
@login_required
def book_ptm_slot_route():
    slot_code = request.form.get("slot_code", "").strip().upper()
    student_roll = request.form.get("student_roll", "").strip()
    parent_name = request.form.get("parent_name", "").strip()
    parent_phone = request.form.get("parent_phone", "").strip()
    parent_email = request.form.get("parent_email", "").strip()
    discussion_topic = request.form.get("discussion_topic", "").strip()

    if not slot_code or not student_roll or not parent_name or not parent_phone:
        flash("Validation Error: Slot Code, Student Roll Number, Parent Name, and Phone are required.", "warning")
        return redirect(url_for("calendar_ptm_view", tab="slots"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            # Check slot is available
            cur.execute("SELECT * FROM PTM_Meeting_Slots WHERE SLOT_CODE = %s", (slot_code,))
            slot = cur.fetchone()
            if not slot or slot["STATUS"] != "Available":
                flash(f"Meeting Slot '{slot_code}' is no longer available for booking.", "warning")
                return redirect(url_for("calendar_ptm_view", tab="slots"))

            # Check student
            cur.execute("SELECT NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (student_roll,))
            st = cur.fetchone()
            if not st:
                flash(f"Student with Roll Number '{student_roll}' not found in registry.", "warning")
                return redirect(url_for("calendar_ptm_view", tab="slots"))

            student_name = st["NAME"]
            student_class = st["CLASS"]

            cur.execute("SELECT MAX(ID) AS MAX_ID FROM PTM_Bookings")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 301
            booking_code = f"BKG-{next_num}"

            topic_text = discussion_topic or "General review of academic progress, coursework, and attendance."

            cur.execute("""
                INSERT INTO PTM_Bookings (BOOKING_CODE, SLOT_CODE, STUDENT_ROLL, STUDENT_NAME, STUDENT_CLASS, PARENT_NAME, PARENT_PHONE, PARENT_EMAIL, DISCUSSION_TOPIC, STATUS, REMINDER_SENT)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', FALSE)
            """, (booking_code, slot_code, student_roll, student_name, student_class, parent_name, parent_phone, parent_email or None, topic_text))

            # Mark slot booked
            cur.execute("UPDATE PTM_Meeting_Slots SET STATUS = 'Booked' WHERE SLOT_CODE = %s", (slot_code,))

            # Generate automated reminder
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Calendar_Reminders")
            row = cur.fetchone()
            next_rem_num = (row["MAX_ID"] or 0) + 401
            rem_code = f"REM-{next_rem_num}"

            cur.execute("""
                INSERT INTO Calendar_Reminders (REMINDER_CODE, TITLE, REMINDER_DATE, TARGET_TYPE, TARGET_ID, RECIPIENT_NAME, MESSAGE, STATUS, DELIVERY_CHANNEL)
                VALUES (%s, %s, %s, 'Specific Student / Parent', %s, %s, %s, 'Active', 'In-App Notification')
            """, (rem_code, f"PTM Consultation: {slot['TEACHER_NAME']} ({slot['SUBJECT']})", slot["MEETING_DATE"], student_roll, parent_name, f"Confirmed PTM conference with {slot['TEACHER_NAME']} ({slot['SUBJECT']}) on {slot['MEETING_DATE']} ({slot['START_TIME']} - {slot['END_TIME']}) in {slot['ROOM_OR_LINK']}."))

            con.commit()
            log_history(parent_name, f"Booked PTM slot {slot_code} ({booking_code}) with {slot['TEACHER_NAME']}")
            flash(f"PTM Appointment Confirmed ({booking_code})! Scheduled with {slot['TEACHER_NAME']} on {slot['MEETING_DATE']}.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="bookings"))


@app.route("/calendar-ptm/bookings/cancel/<int:id>", methods=["POST"])
@login_required
def cancel_ptm_booking_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT BOOKING_CODE, SLOT_CODE, PARENT_NAME FROM PTM_Bookings WHERE ID = %s", (id,))
            bkg = cur.fetchone()
            if bkg:
                slot_code = bkg["SLOT_CODE"]
                cur.execute("UPDATE PTM_Bookings SET STATUS = 'Cancelled' WHERE ID = %s", (id,))
                cur.execute("UPDATE PTM_Meeting_Slots SET STATUS = 'Available' WHERE SLOT_CODE = %s", (slot_code,))
                con.commit()
                log_history(session.get("username", "User"), f"Cancelled PTM booking {bkg['BOOKING_CODE']}")
                flash(f"Meeting booking {bkg['BOOKING_CODE']} cancelled. The slot has been reopened for other parents.", "info")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="bookings"))


@app.route("/calendar-ptm/bookings/notes/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def save_ptm_notes_route(id):
    notes = request.form.get("teacher_feedback_notes", "").strip()
    status = request.form.get("status", "Completed").strip()

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                UPDATE PTM_Bookings
                SET TEACHER_FEEDBACK_NOTES = %s,
                    STATUS = %s
                WHERE ID = %s
            """, (notes, status, id))
            con.commit()
            flash("Meeting consultation feedback and completion status saved.", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="bookings"))


@app.route("/calendar-ptm/reminders/send/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def send_ptm_reminder_route(id):
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("""
                UPDATE PTM_Bookings
                SET REMINDER_SENT = TRUE,
                    REMINDER_SENT_AT = NOW()
                WHERE ID = %s
            """, (id,))
            con.commit()
            flash("Meeting reminder notification marked as dispatched to parent!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="bookings"))


@app.route("/calendar-ptm/reminders/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_calendar_reminder_route():
    title = request.form.get("title", "").strip()
    reminder_date = request.form.get("reminder_date", "").strip()
    target_type = request.form.get("target_type", "All School").strip()
    recipient_name = request.form.get("recipient_name", "School Community").strip()
    message = request.form.get("message", "").strip()
    delivery_channel = request.form.get("delivery_channel", "In-App Notification").strip()

    if not title or not reminder_date or not message:
        flash("Validation Error: Reminder Title, Date, and Notice Body are required.", "warning")
        return redirect(url_for("calendar_ptm_view", tab="reminders"))

    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT MAX(ID) AS MAX_ID FROM Calendar_Reminders")
            row = cur.fetchone()
            next_num = (row["MAX_ID"] or 0) + 401
            code = f"REM-{next_num}"

            cur.execute("""
                INSERT INTO Calendar_Reminders (REMINDER_CODE, TITLE, REMINDER_DATE, TARGET_TYPE, TARGET_ID, RECIPIENT_NAME, MESSAGE, STATUS, DELIVERY_CHANNEL)
                VALUES (%s, %s, %s, %s, 'ALL', %s, %s, 'Active', %s)
            """, (code, title, reminder_date, target_type, recipient_name, message, delivery_channel))
            con.commit()
            log_history(session.get("username", "Admin"), f"Broadcast reminder notice {code}: {title}")
            flash(f"Calendar reminder notice '{title}' ({code}) published!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("calendar_ptm_view", tab="reminders"))


# =========================================================================
# 8. STUDENT PERFORMANCE ANALYTICS & INTERVENTION MANAGEMENT ROUTES
# =========================================================================

@app.route("/performance-analytics")
@login_required
def performance_analytics_view():
    tab = request.args.get("tab", "trends").lower()
    class_filter = request.args.get("class_filter", "All")
    term_filter = request.args.get("term_filter", "All")

    from Analytics_Management_System import (
        get_performance_kpis,
        get_multi_term_trends,
        get_subject_struggle_diagnostics,
        get_class_comparative_benchmarks,
        get_at_risk_students_registry,
        get_academic_interventions_list
    )

    kpis = get_performance_kpis()
    trends = get_multi_term_trends(class_filter)
    subject_diagnostics = get_subject_struggle_diagnostics(term_filter, class_filter)
    class_benchmarks = get_class_comparative_benchmarks(term_filter)
    at_risk_students = get_at_risk_students_registry()
    interventions = get_academic_interventions_list()

    # Fetch auxiliary dropdown lists
    students = []
    teachers = []
    con = get_connection()
    if con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details ORDER BY ROLL_NUMBER ASC")
            students = cur.fetchall()
            cur.execute("SELECT TEACHER_ID, NAME, SUBJECT FROM Teachers_Details ORDER BY NAME ASC")
            teachers = cur.fetchall()
        except Error as e:
            print("Aux data fetch error:", e)
        finally:
            cur.close()
            con.close()

    classes_list = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    terms_list = ["Term 1 Exam", "Mid-Term Examination", "Term 2 Exam", "Final Examination"]

    return render_template(
        "performance_analytics.html",
        active_page="performance_analytics",
        tab=tab,
        class_filter=class_filter,
        term_filter=term_filter,
        kpis=kpis,
        trends=trends,
        subject_diagnostics=subject_diagnostics,
        class_benchmarks=class_benchmarks,
        at_risk_students=at_risk_students,
        interventions=interventions,
        students=students,
        teachers=teachers,
        classes_list=classes_list,
        terms_list=terms_list
    )


@app.route("/performance-analytics/intervention/add", methods=["POST"])
@role_required(["super_admin", "admin"])
def add_intervention_route():
    roll_number = request.form.get("roll_number", "").strip()
    assigned_mentor = request.form.get("assigned_mentor", "").strip()
    remedial_strategy = request.form.get("remedial_strategy", "").strip()
    action_plan = request.form.get("action_plan", "").strip()
    risk_level = request.form.get("risk_level", "Moderate").strip().capitalize()
    parent_notified = request.form.get("parent_notified", "Yes").strip().capitalize()

    if not roll_number or not assigned_mentor or not remedial_strategy:
        flash("Student Roll Number, Assigned Mentor, and Remedial Strategy are required.", "warning")
        return redirect(url_for("performance_analytics_view", tab="support"))

    from Analytics_Management_System import create_academic_intervention
    success, msg = create_academic_intervention(
        roll_number, assigned_mentor, remedial_strategy, action_plan, risk_level, parent_notified
    )
    if success:
        log_history(session.get("username", "Admin"), f"Created Academic Support Plan for Roll {roll_number} with Mentor {assigned_mentor}")
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("performance_analytics_view", tab="support"))


@app.route("/performance-analytics/intervention/update-status/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def update_intervention_status_route(id):
    new_status = request.form.get("status", "").strip()
    notes = request.form.get("notes", "").strip()

    if not new_status:
        flash("Status is required.", "warning")
        return redirect(url_for("performance_analytics_view", tab="support"))

    from Analytics_Management_System import update_intervention_status
    success, msg = update_intervention_status(id, new_status, notes)
    if success:
        log_history(session.get("username", "Admin"), f"Updated Academic Support Plan #{id} status to '{new_status}'")
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("performance_analytics_view", tab="support"))


@app.route("/performance-analytics/intervention/delete/<int:id>", methods=["POST"])
@role_required(["super_admin", "admin"])
def delete_intervention_route(id):
    from Analytics_Management_System import delete_intervention
    success, msg = delete_intervention(id)
    if success:
        log_history(session.get("username", "Admin"), f"Deleted Academic Support Plan #{id}")
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("performance_analytics_view", tab="support"))


@app.route("/performance-analytics/api/student-report/<roll>", methods=["GET"])
@login_required
def student_report_api(roll):
    con = get_connection()
    if not con:
        return jsonify({"error": "Database connection failed"}), 500
    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT ROLL_NUMBER, NAME, CLASS FROM Students_Details WHERE ROLL_NUMBER = %s", (roll,))
        stud = cur.fetchone()
        if not stud:
            return jsonify({"error": "Student not found"}), 404

        cur.execute("""
            SELECT EXAM_TYPE, SUBJECT, MARKS_OBTAINED, MAX_MARKS
            FROM Marks_Details
            WHERE ROLL_NUMBER = %s
            ORDER BY FIELD(EXAM_TYPE, 'Term 1 Exam', 'Mid-Term Examination', 'Term 2 Exam', 'Final Examination'), SUBJECT ASC
        """, (roll,))
        marks = cur.fetchall()

        for m in marks:
            m["MARKS_OBTAINED"] = float(m["MARKS_OBTAINED"])
            m["MAX_MARKS"] = float(m["MAX_MARKS"])
            pct = round((m["MARKS_OBTAINED"] / m["MAX_MARKS"]) * 100, 1) if m["MAX_MARKS"] else 0.0
            m["percentage"] = pct

        total_marks = sum(m["percentage"] for m in marks)
        avg_score = round(total_marks / len(marks), 1) if marks else 0.0
        failing_count = sum(1 for m in marks if m["percentage"] < 40.0)

        return jsonify({
            "roll": stud["ROLL_NUMBER"],
            "name": stud["NAME"],
            "class": stud["CLASS"],
            "overall_avg": avg_score,
            "failing_count": failing_count,
            "evaluations": marks
        })
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        con.close()


# =========================================================================
# 9. AIVEN CLOUD MYSQL DATABASE SYNCHRONIZATION ROUTES
# =========================================================================

@app.route("/cloud-sync")
@role_required(["super_admin"])
def cloud_sync_view():
    from Cloud_Backup_Sync_System import get_sync_overview
    overview = get_sync_overview()
    return render_template(
        "cloud_sync.html",
        active_page="cloud_sync",
        title="Aiven Cloud Database Sync",
        overview=overview
    )


@app.route("/cloud-sync/sync", methods=["POST"])
@role_required(["super_admin"])
def trigger_cloud_sync_route():
    from Cloud_Backup_Sync_System import sync_local_to_aiven
    success, result = sync_local_to_aiven()
    if success:
        flash(f"Aiven Cloud Sync Completed! {result['synced_tables']} tables and {result['total_rows']} records mirrored to Aiven Cloud successfully.", "success")
        log_history(session.get("username", "Principal"), f"Triggered Aiven Cloud Sync: {result['synced_tables']} tables, {result['total_rows']} rows copied")
    else:
        flash(f"Aiven Cloud Sync Failed: {result}", "danger")
    return redirect(url_for("cloud_sync_view"))


# 7. BACKWARD COMPATIBILITY / TEMPLATE URL ALIASES
# -------------------------------------------------------------------------
app.add_url_rule("/students/add", endpoint="add_student", view_func=add_student_route, methods=["POST"])
app.add_url_rule("/students/edit/<int:id>", endpoint="edit_student", view_func=edit_student_route, methods=["POST"])
app.add_url_rule("/students/delete/<int:id>", endpoint="delete_student", view_func=delete_student_route, methods=["POST"])
app.add_url_rule("/teachers/add", endpoint="add_teacher", view_func=add_teacher_route, methods=["POST"])
app.add_url_rule("/teachers/edit/<int:id>", endpoint="edit_teacher", view_func=edit_teacher_route, methods=["POST"])
app.add_url_rule("/teachers/delete/<int:id>", endpoint="delete_teacher", view_func=delete_teacher_route, methods=["POST"])
app.add_url_rule("/users/add", endpoint="add_user", view_func=add_user_route, methods=["POST"])
app.add_url_rule("/users/delete/<int:id>", endpoint="delete_user", view_func=delete_user_route, methods=["POST"])
app.add_url_rule("/change-password", endpoint="change_password", view_func=change_password_route, methods=["GET", "POST"])


if __name__ == "__main__":
    app.run(debug=True, host= "0.0.0.0", port=5000)
