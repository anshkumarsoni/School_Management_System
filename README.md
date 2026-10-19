# 🎓 School Management System (CLI)

A modular, terminal-based **School Management System** built with **Python 3** and **MySQL**. It provides administrative tools to manage students, teachers, library inventory, daily attendance, fee transactions, and academic examinations with automated report card generation.

---

## 🚀 Key Modules & Features

### 1. 👨‍🎓 Student Management
* **Add Student**: Register new students with roll number, class, age, gender, address, phone, and email validation.
* **View Details**: Tabulated view of all registered student records.
* **Search Student**: Query by Roll Number or partial Name matching.
* **Update Details**: Modify specific fields or update all details at once.
* **Delete Record**: Remove student records with confirmation prompts.

### 2. 👩‍🏫 Teacher Management
* **Add Teacher**: Record Teacher ID, subject specialization, age, contact details, and qualifications.
* **View Teachers**: Grid view of all faculty members.
* **Search Teacher**: Search by Teacher ID or Name.
* **Update Details**: Edit teacher subjects, contacts, and personal information.
* **Delete Teacher**: Remove faculty records safely.

### 3. 📚 Library Management
* **Book Inventory**: Register books with Book ID, Title, Author, Genre, and Total Copies.
* **View All Books**: Track both total and currently available copies.
* **Search Books**: Search by Book ID, Title, or Author.
* **Update Inventory**: Modify book details or adjust total/available stock.
* **Delete Record**: Remove decommissioned books.

### 4. 📅 Attendance Management
* **Single Student Attendance**: Mark daily status (`Present`, `Absent`, `Leave`) with date auto-fill.
* **Class Batch Mode**: Rapidly mark attendance for an entire classroom in one pass.
* **Attendance % Calculator**: Calculates student working day attendance percentage.
* **Defaulter Warning**: Automatically flags warnings for students falling below **75% attendance**.
* **Rectify Records**: Correct mistakenly marked attendance entries.

### 5. 💳 Fee & Finance Management
* **Fee Collection & Receipts**: Record student payments (Cash, UPI, Card, Net Banking) and generate formatted receipt cards.
* **Student Statement**: Track total annual fee, total paid so far, and remaining balance due.
* **Fee Defaulters**: Instantly filter and list all students with pending fee dues.
* **Class Fee Structure**: Configure custom annual fee standards per grade/class.
* **Transaction Log**: Complete historical record of all school fee transactions.

### 6. 📊 Examination & Marks Management
* **Marks Entry**: Record subject-wise marks across exams (Unit Tests, Mid-Term, Final Exams) with upper-bound score validation.
* **Academic Report Cards**: Generate formatted student report cards with subject percentages, overall GPA, letter grades (`A+` to `F`), and pass/fail status.
* **Class Merit List**: Rank students in a class sorted by overall performance and percentage (Rank 1, 2, 3...).
* **Update / Rectify**: Update subject marks in case of re-evaluation.

---

## 🛠️ Tech Stack & Requirements

* **Language**: Python 3.8+
* **Database**: MySQL Server 8.0+
* **Python Libraries**:
  * `mysql-connector-python` — MySQL database driver
  * `tabulate` — ASCII table formatting
  * `pyfiglet` — Terminal banners
  * `python-dotenv` — Environment configuration

---

## 📂 Project Architecture

```text
School Management System/
│
├── Main.py                          # Application entry point and master menu
├── Student_Manegement_System.py     # Student CRUD operations and student menu
├── Teacher_Management_System.py     # Teacher CRUD operations and faculty menu
├── Library_Management_System.py     # Book inventory operations and library menu
├── Attendance_Management_System.py  # Daily attendance tracking and defaulter logic
├── Fee_Management_System.py         # Financial ledger, receipts, and fee structures
├── Exam_Management_System.py        # Examination records, report cards, and merit lists
├── utils.py                         # Shared utilities, DB connection, and regex validators
├── .env                             # Database connection credentials (local configuration)
└── README.md                        # Documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone or Download
Ensure all project files are saved together in your project folder:
```bash
cd "C:\Users\lenovo\Desktop\python\School Management System"
```

### 2. Install Required Python Packages
Run the following command in your terminal:
```bash
pip install mysql-connector-python tabulate pyfiglet python-dotenv
```

### 3. Configure Database Credentials
Create a `.env` file in the project folder with your MySQL login credentials:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=Student
```
*(If no password is set, leave `DB_PASSWORD=` blank).*

### 4. Run the Application
Start the main management portal:
```bash
python Main.py
```

The database (`Student`) and all corresponding tables will be created automatically on your first run.

---

## 🗄️ Database Tables Schema

* `Students_Details`: `(ID, ROLL_NUMBER, NAME, CLASS, AGE, ADDRESS, PHONE, EMAIL, GENDER)`
* `Teachers_Details`: `(ID, TEACHER_ID, NAME, SUBJECT, AGE, ADDRESS, PHONE, EMAIL, GENDER)`
* `Books_Details`: `(ID, BOOK_ID, TITLE, AUTHOR, GENRE, TOTAL_COPIES, AVAILABLE_COPIES)`
* `Attendance_Details`: `(ID, ROLL_NUMBER, ATTENDANCE_DATE, STATUS, REMARKS)`
* `Fee_Structure`: `(CLASS, ANNUAL_FEE)`
* `Fee_Transactions`: `(RECEIPT_NO, ROLL_NUMBER, AMOUNT_PAID, PAYMENT_DATE, PAYMENT_MODE, REMARKS)`
* `Marks_Details`: `(ID, ROLL_NUMBER, EXAM_TYPE, SUBJECT, MARKS_OBTAINED, MAX_MARKS)`

---

## 📄 License
This project is open-source and intended for academic and administrative demonstration.
