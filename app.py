import os
import math
import datetime
import mysql.connector as ms
from mysql.connector import Error
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session

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

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "edupulse_academic_secret_998877")

# Global Template Context Injector for Session User
@app.context_processor
def inject_user_context():
    return {
        "current_user": session.get("username"),
        "current_role": session.get("role")
    }

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
            con.commit()
        except Error as e:
            print("Schema Init Notice:", e)
        finally:
            cur.close()
            con.close()

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
                log_history(username, "Initial Super Admin account registered")
                session["username"] = username
                session["role"] = "super_admin"
                flash(f"Welcome, {username}! Initial Super Admin account created.", "success")
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

        if selected_role and selected_role != user_role:
            flash(f"Access Denied: Account belongs to '{user_role.replace('_', ' ').title()}', not '{selected_role.replace('_', ' ').title()}'.", "danger")
            return render_template("login.html", first_run=False)

        if check_password(password, stored_hash):
            session["username"] = user_row["USERNAME"]
            session["role"] = user_role
            log_history(user_row["USERNAME"], "Logged in")
            flash(f"Welcome back, {user_row['USERNAME']}!", "success")
            
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

    # 8. Upcoming Academic Events & Milestones
    today = datetime.date.today()
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
    role = request.form.get("role", "").strip().lower()

    if not username or not password:
        flash("Username and password are required.", "warning")
        return redirect(url_for("users_view"))

    if role not in ("admin", "viewer"):
        flash("Invalid role assignment. Only 'admin' or 'viewer' accounts can be created.", "danger")
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
        cur.execute("INSERT INTO users (USERNAME, PASSWORD, ROLE) VALUES (%s, %s, %s)", (username, hashed, role))
        con.commit()

        curr_user = session.get("username")
        log_history(curr_user, f"Registered user {username} as {role}")
        flash(f"User '{username}' registered successfully with role '{role.title()}'!", "success")
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
    con = get_connection()
    books = []
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Books_Details ORDER BY ID DESC")
        books = cur.fetchall()
        cur.close()
        con.close()
    return render_template("library.html", active_page="library", title="Library Catalog", books=books)


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


@app.route("/library/add", methods=["POST"], endpoint="add_book")
@role_required(["super_admin", "admin"])
def add_book_route():
    book_id = request.form.get("book_id", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    genre = request.form.get("genre", "").strip()
    copies_raw = request.form.get("copies", "1").strip()

    if not book_id or not title:
        flash("Validation Error: Book ID and Title are required.", "warning")
        return redirect(url_for("library_view"))

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
                flash(f"Validation Error: Book ID '{book_id}' already exists.", "danger")
            else:
                cur.execute("""
                    INSERT INTO Books_Details (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (book_id, title, author, genre, copies, copies))
                con.commit()
                log_history(session.get("username", "Admin"), f"Added book ID {book_id}")
                flash(f"Book '{title}' added to library catalog successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()

    return redirect(url_for("library_view"))


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
    app.run(debug=True, port=5000)
