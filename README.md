# 🎓 School Management System (CLI)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-MySQL-orange.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

A modular, terminal-based **School Management System** built with **Python 3** and **MySQL**. It features complete administrative tools to manage students, faculty, library inventory, daily classroom attendance, student fee ledgers, academic examinations with automated report cards, and one-click data exports to Microsoft Excel (CSV).

---

## 📋 Table of Contents
- [Key Modules & Features](#-key-modules--features)
- [Project Architecture](#-project-architecture)
- [Prerequisites & Dependencies](#-prerequisites--dependencies)
- [Installation & Quickstart](#-installation--quickstart)
- [Database Schema](#-database-schema)
- [Troubleshooting](#-troubleshooting)
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
* **Add Teacher**: Record Teacher ID, subject specialization, contact info, and age validation (18–120).
* **Faculty Directory**: Formatted table of all active teachers.
* **Search Teacher**: Lookup by Teacher ID or Name.
* **Update Details**: Modify teacher subject allocations and personal details.
* **Delete Teacher**: Safely remove faculty records.

### 3. 📚 Library Management (`Library_Management_System.py`)
* **Book Cataloging**: Register books with Book ID, Title, Author, Genre, and Total Copies.
* **Stock Tracking**: Monitors both Total Copies and Available Copies in real-time.
* **Search Catalog**: Search inventory by Book ID, Title, or Author.
* **Update Inventory**: Modify book details or replenish copy counts.
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
* **Export Students**: Export full student roster or filter by specific class to `.csv`.
* **Export Faculty**: Export teacher roster and contact info.
* **Export Library Inventory**: Save book stock reports to `.csv`.
* **Export Fee Defaulters**: Generate list of unpaid dues directly openable in Microsoft Excel.
* **Export Attendance**: Export daily school attendance sheets.
* **Export Merit List**: Save class exam rankings and percentages to `.csv`.
* **Full School Backup**: One-click export of all school tables into the `exports/` folder with timestamps.

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
├── utils.py                         # Shared utilities, DB connection, and regex validators
├── exports/                         # Output folder for generated CSV files
├── .env                             # Database connection credentials (local configuration)
├── .gitignore                       # Git ignore rules for passwords and cache
├── requirements.txt                 # Python dependencies list
└── README.md                        # Documentation