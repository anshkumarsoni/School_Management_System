import os
import mysql.connector as ms
from mysql.connector import Error
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

load_dotenv()

app = Flask(__name__)
app.secret_key = "school_secret_key_12345"

# ----------------- DATABASE CONNECTION -----------------
def get_db():
    try:
        return ms.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "Student")
        )
    except Error as e:
        print("Database Connection Error:", e)
        return None

# ----------------- 1. DASHBOARD ROUTE -----------------
@app.route("/")
def dashboard():
    con = get_db()
    if not con:
        return "Database Connection Failed! Please check your .env file.", 500
    
    cur = con.cursor(dictionary=True)

    # 1. Total counts for KPI cards
    cur.execute("SELECT COUNT(*) AS total FROM Students_Details")
    total_students = cur.fetchone()["total"] or 0

    cur.execute("SELECT COUNT(*) AS total FROM Teachers_Details")
    total_teachers = cur.fetchone()["total"] or 0

    cur.execute("SELECT IFNULL(SUM(TOTAL_COPIES), 0) AS total FROM Books_Details")
    total_books = int(cur.fetchone()["total"] or 0)

    cur.execute("SELECT IFNULL(SUM(AMOUNT_PAID), 0) AS total FROM Fee_Transactions")
    total_fees_collected = float(cur.fetchone()["total"] or 0)

    # 2. Enrollment by Class (for Chart.js Bar Chart)
    cur.execute("SELECT CLASS, COUNT(*) AS count FROM Students_Details WHERE CLASS IS NOT NULL AND CLASS != '' GROUP BY CLASS ORDER BY CLASS")
    class_data = cur.fetchall()
    class_labels = [row["CLASS"] for row in class_data]
    class_counts = [int(row["count"]) for row in class_data]

    # 3. Gender Ratio (for Chart.js Donut Chart)
    cur.execute("SELECT GENDER, COUNT(*) AS count FROM Students_Details WHERE GENDER IS NOT NULL GROUP BY GENDER")
    gender_data = cur.fetchall()
    gender_labels = [row["GENDER"] for row in gender_data]
    gender_counts = [int(row["count"]) for row in gender_data]

    # 4. Recent Student Registrations
    cur.execute("SELECT ID, ROLL_NUMBER, NAME, CLASS, PHONE, GENDER FROM Students_Details ORDER BY ID DESC LIMIT 5")
    recent_students = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        title="Admin Dashboard",
        total_students=total_students,
        total_teachers=total_teachers,
        total_books=total_books,
        total_fees=total_fees_collected,
        class_labels=class_labels,
        class_counts=class_counts,
        gender_labels=gender_labels,
        gender_counts=gender_counts,
        recent_students=recent_students
    )

# ----------------- 2. STUDENTS MANAGEMENT ROUTES -----------------
@app.route("/students")
def students_view():
    search = request.args.get("search", "").strip()
    selected_class = request.args.get("class", "").strip()

    con = get_db()
    if not con:
        flash("Database Connection Failed!", "danger")
        return redirect(url_for("dashboard"))

    cur = con.cursor(dictionary=True)
    
    # Fetch distinct classes for filter dropdown
    cur.execute("SELECT DISTINCT CLASS FROM Students_Details WHERE CLASS IS NOT NULL AND CLASS != '' ORDER BY CLASS")
    available_classes = [row["CLASS"] for row in cur.fetchall()]

    query = "SELECT * FROM Students_Details WHERE 1=1"
    params = []

    if search:
        query += " AND (NAME LIKE %s OR ROLL_NUMBER LIKE %s OR PHONE LIKE %s)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])
    
    if selected_class:
        query += " AND CLASS = %s"
        params.append(selected_class)

    query += " ORDER BY ID DESC"
    cur.execute(query, tuple(params))
    students = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        "students.html",
        active_page="students",
        title="Student Management",
        students=students,
        available_classes=available_classes,
        search=search,
        selected_class=selected_class
    )

@app.route("/students/add", methods=["POST"])
def add_student():
    roll_number = request.form.get("roll_number", "").strip()
    name = request.form.get("name", "").strip()
    class_name = request.form.get("class_name", "").strip()
    age_raw = request.form.get("age", "").strip()
    gender = request.form.get("gender", "Male").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    if not roll_number or not name:
        flash("Roll Number and Student Name are required!", "warning")
        return redirect(request.referrer or url_for("students_view"))

    age = int(age_raw) if age_raw.isdigit() else None

    con = get_db()
    if not con:
        flash("Database Connection Failed!", "danger")
        return redirect(request.referrer or url_for("students_view"))

    cur = con.cursor()
    try:
        cur.execute("SELECT 1 FROM Students_Details WHERE ROLL_NUMBER = %s", (roll_number,))
        if cur.fetchone():
            flash(f"Error: Roll Number '{roll_number}' already exists!", "danger")
            return redirect(request.referrer or url_for("students_view"))

        cur.execute("""
            INSERT INTO Students_Details (ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (roll_number, name, class_name, age, address, phone, email, gender))
        con.commit()
        flash(f"Student '{name}' (# {roll_number}) added successfully!", "success")
    except Error as e:
        flash(f"Database Error: {e}", "danger")
    finally:
        cur.close()
        con.close()

    return redirect(request.referrer or url_for("students_view"))

@app.route("/students/delete/<int:id>", methods=["POST"])
def delete_student(id):
    con = get_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM Students_Details WHERE ID = %s", (id,))
            con.commit()
            flash("Student record deleted successfully.", "info")
        except Error as e:
            flash(f"Error deleting record: {e}", "danger")
        finally:
            cur.close()
            con.close()
    return redirect(request.referrer or url_for("students_view"))

# ----------------- 3. TEACHERS MANAGEMENT ROUTE -----------------
@app.route("/teachers")
def teachers_view():
    con = get_db()
    teachers = []
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Teachers_Details ORDER BY ID DESC")
        teachers = cur.fetchall()
        cur.close()
        con.close()
    return render_template("teachers.html", active_page="teachers", title="Faculty Management", teachers=teachers)

@app.route("/teachers/add", methods=["POST"])
def add_teacher():
    teacher_id = request.form.get("teacher_id", "").strip()
    name = request.form.get("name", "").strip()
    subject = request.form.get("subject", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    gender = request.form.get("gender", "Male").strip()
    address = request.form.get("address", "").strip()
    age_raw = request.form.get("age", "").strip()
    age = int(age_raw) if age_raw.isdigit() else None

    if not teacher_id or not name:
        flash("Teacher ID and Name are required!", "warning")
        return redirect(url_for("teachers_view"))

    con = get_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO Teachers_Details (TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (teacher_id, name, subject, age, address, phone, email, gender))
            con.commit()
            flash(f"Teacher '{name}' registered successfully!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()
    return redirect(url_for("teachers_view"))

# ----------------- 4. LIBRARY MANAGEMENT ROUTE -----------------
@app.route("/library")
def library_view():
    con = get_db()
    books = []
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM Books_Details ORDER BY ID DESC")
        books = cur.fetchall()
        cur.close()
        con.close()
    return render_template("library.html", active_page="library", title="Library Catalog", books=books)

@app.route("/library/add", methods=["POST"])
def add_book():
    book_id = request.form.get("book_id", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    genre = request.form.get("genre", "").strip()
    copies = int(request.form.get("copies", 1))

    if not book_id or not title:
        flash("Book ID and Title are required!", "warning")
        return redirect(url_for("library_view"))

    con = get_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO Books_Details (BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (book_id, title, author, genre, copies, copies))
            con.commit()
            flash(f"Book '{title}' added to catalog!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()
    return redirect(url_for("library_view"))

# ----------------- 5. ATTENDANCE MANAGEMENT ROUTE -----------------
@app.route("/attendance")
def attendance_view():
    con = get_db()
    records = []
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT a.*, s.NAME, s.CLASS 
            FROM Attendance_Details a
            LEFT JOIN Students_Details s ON a.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY a.ATTENDANCE_DATE DESC, a.ID DESC
            LIMIT 50
        """)
        records = cur.fetchall()
        cur.close()
        con.close()
    return render_template("attendance.html", active_page="attendance", title="Attendance Records", records=records)

# ----------------- 6. FEES & FINANCE MANAGEMENT ROUTE -----------------
@app.route("/fees")
def fees_view():
    con = get_db()
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

@app.route("/fees/add", methods=["POST"])
def add_fee():
    receipt_no = request.form.get("receipt_no", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    amount = float(request.form.get("amount", 0))
    mode = request.form.get("mode", "Cash").strip()
    remarks = request.form.get("remarks", "").strip()

    if not receipt_no or not roll_number or amount <= 0:
        flash("Valid Receipt No, Roll Number, and Amount are required!", "warning")
        return redirect(url_for("fees_view"))

    con = get_db()
    if con:
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO Fee_Transactions (RECEIPT_NO, ROLL_NUMBER, AMOUNT_PAID, PAYMENT_DATE, PAYMENT_MODE, REMARKS)
                VALUES (%s, %s, %s, CURDATE(), %s, %s)
            """, (receipt_no, roll_number, amount, mode, remarks))
            con.commit()
            flash(f"Payment of ₹{amount:,.2f} recorded under Receipt #{receipt_no}!", "success")
        except Error as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cur.close()
            con.close()
    return redirect(url_for("fees_view"))

# ----------------- 7. EXAMINATIONS ROUTE -----------------
@app.route("/exams")
def exams_view():
    con = get_db()
    marks = []
    if con:
        cur = con.cursor(dictionary=True)
        cur.execute("""
            SELECT m.*, s.NAME, s.CLASS 
            FROM Marks_Details m
            LEFT JOIN Students_Details s ON m.ROLL_NUMBER = s.ROLL_NUMBER
            ORDER BY m.ID DESC
            LIMIT 50
        """)
        marks = cur.fetchall()
        cur.close()
        con.close()
    return render_template("exams.html", active_page="exams", title="Examination Marks", marks=marks)

if __name__ == "__main__":
    app.run(debug=True, port=5000)