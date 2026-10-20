# 🎓 School Management System (CLI)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-MySQL-orange.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

A modular, terminal-based **School Management System** built with **Python 3** and **MySQL**. It features complete administrative tools to manage students, faculty, library inventory, daily classroom attendance, student fee ledgers, academic examinations with automated report cards, full CSV/Excel export, and **high-speed bulk CSV data importing**.

---

## 📋 Table of Contents
- [Key Modules & Features](#-key-modules--features)
- [Project Architecture](#-project-architecture)
- [Prerequisites & Dependencies](#-prerequisites--dependencies)
- [Installation & Quickstart](#-installation--quickstart)
- [How to Bulk Import Data](#-how-to-bulk-import-data)
- [Database Schema](#-database-schema)
- [License](#-license)

---

## 🚀 Key Modules & Features

### 1. 👨‍🎓 Student Management (`Student_Manegement_System.py`)
* **Add Student**: Register students with roll number, class, age, gender, contact details, and input validation.
* **View Directory**: Display all student records in a clean tabular grid.
* **Search Records**: Lookup by Roll Number or partial Name search.
* **Update Details**: Update single attributes or complete student profiles.
* **Delete Record**: Remove student records with confirmation prompts.

### 2. 👩‍🏫 Teacher Management (`Teacher_Management_System.py`)
* **Add Teacher**: Record Teacher ID, subject specialization, contact info, and age validation.
* **Faculty Directory**: Formatted table of all active teachers.
* **Search Teacher**: Lookup by Teacher ID or Name.
* **Update Details**: Modify teacher subject allocations and personal details.
* **Delete Teacher**: Safely remove faculty records.

### 3. 📚 Library Management (`Library_Management_System.py`)
* **Book Cataloging**: Register books with Book ID, Title, Author, Genre, and Total Copies.
* **Stock Tracking**: Monitors both Total Copies and Available Copies in real-time.
* **Search Catalog**: Search inventory by Book ID, Title, or Author.
* **Update Inventory**: Modify book details or adjust copy counts.
* **Delete Book**: Remove damaged or decommissioned book entries.

### 4. 📅 Attendance Management (`Attendance_Management_System.py`)
* **Single Student Attendance**: Mark daily status (`Present`, `Absent`, `Leave`) with auto-date filling.
* **Class Batch Mode**: Quickly roll through an entire classroom in one pass (`P/A/L`).
* **Attendance % Calculator**: Calculates student working day percentage.
* **Defaulter Warning**: Automatically flags warnings for students falling below **75% attendance**.
* **Rectify Records**: Correct mistakenly marked attendance records.

### 5. 💳 Fee & Finance Management (`Fee_Management_System.py`)
* **Collect Fee & Print Receipt**: Record payments (Cash, UPI, Card, Net Banking) and generate formatted receipt cards.
* **Student Statement**: Track total annual fee, total paid so far, and remaining balance due.
* **Fee Defaulters List**: Instantly lists all students who have pending fee balances.
* **Class Fee Structure**: Configure custom annual fee standards per grade/class.
* **Transaction Log**: Complete historical record of all school fee transactions.

### 6. 📊 Examination & Marks Management (`Exam_Management_System.py`)
* **Marks Entry**: Record subject-wise marks across exams (Unit Tests, Mid-Term, Final Exams) with score validation.
* **Academic Report Cards**: Generate formatted student report cards with subject percentages, overall GPA, letter grades (`A+` to `F`), and pass/fail status.
* **Class Merit List**: Rank students in a class sorted by overall performance and percentage (Rank 1, 2, 3...).
* **Update / Rectify**: Update subject marks in case of re-evaluation.

### 7. 📄 Data Export to CSV / Excel (`Export_Management_System.py`)
* Export Student Rosters, Teacher Rosters, Library Stock, Fee Defaulters, Daily Attendance, and Exam Rankings directly into Microsoft Excel `.csv` files inside an `exports/` folder.

### 8. 📥 Bulk Data Import (`Import_Management_System.py`)
* **Import Students**: Read thousands of student rows from an Excel `.csv` file into MySQL in seconds.
* **Import Teachers**: Bulk upload faculty rosters from spreadsheets.
* **Import Books**: Import library inventory and book lists.
* **Generate Blank Templates**: Automatically creates pre-formatted `.csv` templates in `import_templates/` so staff know exactly how to structure the columns in Excel.

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
├── Export_Management_System.py      # Automated report generation and CSV/Excel exports
├── Import_Management_System.py      # High-speed bulk CSV data importer & template generator
├── utils.py                         # Shared utilities, DB connection, and regex validators
├── exports/                         # Output folder for generated CSV files
├── import_templates/                # Pre-formatted sample templates for Excel
├── .env                             # Database connection credentials (local configuration)
├── .gitignore                       # Git ignore rules for passwords and cache
├── requirements.txt                 # Python dependencies list
└── README.md                        # Documentation
```

---

## 📥 How to Bulk Import Data

1. Run the application (`python Main.py`) and choose option **`8. Import Bulk Data from CSV / Excel`**.
2. Select option **`4. Generate Blank CSV Templates`**.
3. Open the newly generated files in `import_templates/` using **Microsoft Excel**:
   * `template_students.csv`
   * `template_teachers.csv`
   * `template_books.csv`
4. Paste your school's data into the columns and save the file.
5. In the program menu, select the corresponding import option (e.g. `1. Import Students from CSV`) and enter the path. All records will be saved into MySQL instantly!

---

## ⚙️ Installation & Quickstart

```bash
# 1. Navigate to project folder
cd "C:\Users\lenovo\Desktop\python\School Management System"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your MySQL password in .env
# DB_PASSWORD=your_password

# 4. Run application
python Main.py
```

---

## 📄 License
This project is licensed under the **MIT License** — feel free to modify and use it for learning or personal projects!
