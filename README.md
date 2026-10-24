# 🎓 EduPulse - School Management System (Web & CLI)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Security](https://img.shields.io/badge/Auth-Bcrypt%20%7C%20RBAC-green.svg)](https://pypi.org/project/bcrypt/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384.svg?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

A modern, professional **School Management System** built with **Python, Flask, and MySQL**, featuring an intuitive **Navy-Blue Light Theme Web Interface** and a modular **Terminal CLI**. The application preserves all existing database tables, validation rules, and business logic while introducing **Role-Based Access Control (Super Admin, Admin, Viewer)**, **Bcrypt Password Encryption**, **Field-Level Editing**, **Server-Side Pagination & Filtering**, and **Audit History Logging**.

---

## 📋 Table of Contents
- [✨ Key Features](#-key-features)
  - [1. Role-Based Access Control (RBAC)](#1-role-based-access-control-rbac)
  - [2. Modern Web Dashboard & Data Visualizations](#2-modern-web-dashboard--data-visualizations)
  - [3. Comprehensive Student & Faculty Management](#3-comprehensive-student--faculty-management)
  - [4. Security, Authentication & Audit History](#4-security-authentication--audit-history)
- [📂 Project Architecture](#-project-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [⚙️ Installation & Setup (Windows)](#️-installation--setup-windows)
- [🗄️ Database Schema](#️-database-schema)
- [🌐 Web Route Documentation](#-web-route-documentation)
- [💡 Technical Highlights & UI Architecture](#-technical-highlights--ui-architecture)
- [📜 License](#-license)

---

## ✨ Key Features

### 1. Role-Based Access Control (RBAC)
The system strictly enforces permissions on both the client interface and server controllers, mapping executive and academic roles to security levels:
* **Principal (Super Admin)**: Full institutional and administrative authority. Can manage students, faculty, and parent profiles, provision and delete user accounts for Teachers and Parents/Students, inspect complete activity audit trails, and oversee school-wide configurations.
* **Teacher (Admin)**: Operational faculty authority. Can record and update student details, parents information, attendance records, exam marks, and teacher listings. Restricted from user provisioning.
* **Parents & Students (Viewer)**: Read-only institutional portal access. Can view student directory, announcements, academic calendar, library catalog, and attendance statistics. All Add, Edit, and Delete action buttons are hidden from the UI and blocked on the server (`@role_required`).

### 2. Modern Web Dashboard & Data Visualizations
* **Light Navy-Blue Theme**: Crisp slate background (`#f8fafc`), deep navy primary tones (`#1e3a8a` / `#0f172a`), card elevation, and responsive spacing suitable for institutional demonstrations.
* **Live KPI Cards**: Real-time counts for Enrolled Students, Faculty Members, Total Users (for Super Admin), and Total Fee Collections.
* **Chart.js Visualizations**:
  * **Enrollment by Class (Bar Chart)**: Vertical bars showing student counts per grade standard.
  * **Demographics (Doughnut Chart)**: Gender distribution ratio (Male / Female / Other).
  * Safe data serialization with 0 linter errors.
* **Recent Activity Feed**: Real-time chronological audit trail loaded directly from the MySQL `history` table.

### 3. Comprehensive Student & Faculty Management
* **Student Details (`/students`)**:
  * Paginated table with roll number badges, avatar initials, and class indicators.
  * Multi-parameter search by student name, roll number, or phone.
  * Filters for class standard and age range (`min_age` to `max_age`).
  * Field-level edit modal prefilled with current student details.
  * Delete confirmation modal with record cleanup.
  * Validation: Numeric-only unique roll numbers, realistic ages (1–120), 10-digit phone numbers.
* **Faculty Directory (`/teachers`)**:
  * Paginated table with faculty ID, subject specializations, and contact info.
  * Search by teacher ID, name, or phone; filter by subject.
  * Add Faculty and Edit Faculty modals prefilled dynamically.
  * Validation: Unique teacher IDs, teacher age (18–120), 10-digit phone numbers.

### 4. Security, Authentication & Audit History
* **First-Run Automatic Setup**: If no user accounts exist, the system automatically redirects to an initial setup view to initialize the primary **Super Admin** account.
* **Bcrypt Password Encryption**: Industry-standard cryptographic salting and hashing. Raw passwords are never stored or logged.
* **Password Policy Enforcement**: Validates that passwords are at least 8 characters long, contain at least 1 uppercase letter, and at least 1 digit.
* **Audit Trail**: Every significant action (logins, logouts, additions, edits, deletions, password updates) is timestamped and recorded in the MySQL `history` table.

---

## 📂 Project Architecture

```text
Student_Management_system/
│
├── app.py                              # Flask Web Server, Controllers & RBAC Routes
├── auth.py                             # Authentication, Bcrypt Hashing, RBAC Decorators
├── utils.py                            # Database connection helper & input validators
├── .env                                # Environment variables (DB credentials, Secret key)
├── requirements.txt                    # Project Python dependencies
├── README.md                           # Master Documentation
│
├── static/                             # Web Portal Static Assets
│   └── css/
│       └── style.css                   # Custom Navy-Blue Light Theme Stylesheet
│
├── templates/                          # Jinja2 HTML5 Templates
│   ├── base.html                       # Base layout (responsive sidebar, topbar, modals)
│   ├── login.html                      # Standalone authentication card & first-run setup
│   ├── dashboard.html                  # Executive dashboard, KPIs, Chart.js & history feed
│   ├── students.html                   # Student directory with search, filters, edit modal
│   ├── teachers.html                   # Faculty directory with search, filter, edit modal
│   ├── users.html                      # Super Admin user management & audit trail
│   ├── change_password.html            # User password update interface
│   ├── library.html                    # Library catalog and book inventory
│   ├── attendance.html                 # Daily classroom attendance logs
│   ├── fees.html                       # Fee transaction ledger & receipt logging
│   └── exams.html                      # Examination records & mark evaluations
│
├── Main.py                             # Standalone CLI Main Menu
├── Student_Manegement_System.py        # CLI Student CRUD
├── Teacher_Management_System.py        # CLI Teacher Operations
├── Library_Management_System.py        # CLI Library Operations
├── Attendance_Management_System.py     # CLI Attendance Module
├── FeeFinance_Management_System.py     # CLI Financial Statements & Receipts
├── ExamMarks_Management_System.py      # CLI Report Cards & Merit Ranking
├── Export_Management_System.py         # CLI CSV & Excel Exporter
└── Import_Management_System.py         # CLI Bulk CSV Importer
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.9+, [Flask 3.0+](https://flask.palletsprojects.com/) |
| **Authentication & Security** | [bcrypt](https://pypi.org/project/bcrypt/), Flask Session, RBAC |
| **Database** | [MySQL 8.0+](https://www.mysql.com/), `mysql-connector-python` |
| **Frontend Styling** | Custom Navy-Blue Light Theme CSS3 (CSS Variables, Flexbox, Grid) |
| **Typography & Icons** | Plus Jakarta Sans (Google Fonts), FontAwesome 6.5.1 CDN |
| **Data Visualizations** | [Chart.js 4.4.1 CDN](https://www.chartjs.org/) |
| **Environment Config** | `python-dotenv` |

---

## ⚙️ Installation & Setup (Windows)

### 1. Prerequisites
* **Python 3.9 or higher** installed ([Download Python](https://www.python.org/downloads/)).
* **MySQL Server** installed and running on `localhost:3306`.

### 2. Open Project Folder
Open PowerShell or your preferred terminal in the project directory:
```powershell
cd "C:\Users\lenovo\Desktop\New folder\Student_Management_system"
```

### 3. Install Dependencies
Install all required libraries using `pip`:
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Ensure your `.env` file in the project root is properly configured with your MySQL password:
```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=Student
FLASK_SECRET_KEY=edupulse_academic_secret_998877
```

### 5. Verify / Initialize Database
Make sure the `Student` database exists in MySQL:
```sql
CREATE DATABASE IF NOT EXISTS Student;
```

### 6. Run the Application
Start the Flask web server:
```powershell
python app.py
```
Open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

* **First Visit**: If the database has no users, the login page will present the **Initial Super Admin Setup** form. Choose your username and password (at least 8 chars, 1 uppercase, 1 digit) to initialize the system.

---

## 🗄️ Database Schema

The application connects to the following existing tables in MySQL:

```sql
-- 1. Users Table (Role-Based Access)
CREATE TABLE IF NOT EXISTS users (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    USERNAME VARCHAR(50) UNIQUE NOT NULL,
    PASSWORD VARBINARY(255) NOT NULL,
    ROLE ENUM('super_admin', 'admin', 'viewer') NOT NULL
);

-- 2. Audit Trail Table
CREATE TABLE IF NOT EXISTS history (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    USERNAME VARCHAR(50) NOT NULL,
    ACTIONS VARCHAR(255) NOT NULL,
    LOG_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Students Table
CREATE TABLE IF NOT EXISTS Students_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ROLL_NUMBER VARCHAR(20) UNIQUE NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    CLASS VARCHAR(20),
    AGE INT,
    ADDRESS VARCHAR(255),
    PHONE VARCHAR(15),
    EMAIL VARCHAR(100),
    GENDER ENUM('Male', 'Female', 'Other')
);

-- 4. Teachers Table
CREATE TABLE IF NOT EXISTS Teachers_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    TEACHER_ID VARCHAR(20) UNIQUE NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    SUBJECT VARCHAR(100),
    AGE INT,
    ADDRESS VARCHAR(255),
    PHONE VARCHAR(15),
    EMAIL VARCHAR(100),
    GENDER ENUM('Male', 'Female', 'Other')
);

-- 5. Library Books Table
CREATE TABLE IF NOT EXISTS Books_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    BOOK_ID VARCHAR(20) UNIQUE NOT NULL,
    TITLE VARCHAR(150) NOT NULL,
    AUTHOR VARCHAR(100),
    GENRE VARCHAR(50),
    TOTAL_COPIES INT DEFAULT 1,
    AVAILABLE_COPIES INT DEFAULT 1
);

-- 6. Fee Transactions Table
CREATE TABLE IF NOT EXISTS Fee_Transactions (
    RECEIPT_NO INT AUTO_INCREMENT PRIMARY KEY,
    ROLL_NUMBER VARCHAR(20) NOT NULL,
    AMOUNT_PAID DECIMAL(10, 2) NOT NULL,
    PAYMENT_DATE DATE NOT NULL,
    PAYMENT_MODE VARCHAR(30) DEFAULT 'Cash',
    REMARKS VARCHAR(255)
);

-- 7. Attendance Records
CREATE TABLE IF NOT EXISTS Attendance_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ROLL_NUMBER VARCHAR(20) NOT NULL,
    ATTENDANCE_DATE DATE NOT NULL,
    STATUS ENUM('Present', 'Absent', 'Leave') DEFAULT 'Present',
    REMARKS VARCHAR(255)
);

-- 8. Exam Marks Table
CREATE TABLE IF NOT EXISTS Marks_Details (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    ROLL_NUMBER VARCHAR(20) NOT NULL,
    EXAM_TYPE VARCHAR(50) NOT NULL,
    SUBJECT VARCHAR(50) NOT NULL,
    MARKS_OBTAINED DECIMAL(5, 2) NOT NULL,
    MAX_MARKS DECIMAL(5, 2) NOT NULL
);
```

---

## 🌐 Web Route Documentation

| Route | HTTP Method | Permitted Roles | Description |
|---|---|---|---|
| `/login` | `GET`, `POST` | Public | User authentication & first-run Super Admin setup. |
| `/logout` | `GET` | Authenticated | Signs out user and logs activity. |
| `/change-password` | `GET`, `POST` | Authenticated | Updates the current user's password with strength verification. |
| `/` or `/dashboard` | `GET` | Authenticated | Live KPI cards, Chart.js analytics, and recent activity logs. |
| `/students` | `GET` | Authenticated | Paginated student table with search, class filter, and age filter. |
| `/students/add` | `POST` | `super_admin`, `admin` | Registers a new student record with uniqueness verification. |
| `/students/edit/<id>` | `POST` | `super_admin`, `admin` | Updates an existing student's details via modal form. |
| `/students/delete/<id>` | `POST` | `super_admin`, `admin` | Deletes a student record with confirmation. |
| `/teachers` | `GET` | Authenticated | Paginated faculty table with search and subject filter. |
| `/teachers/add` | `POST` | `super_admin`, `admin` | Registers a faculty member with subject specialization. |
| `/teachers/edit/<id>` | `POST` | `super_admin`, `admin` | Updates an existing teacher's details via modal form. |
| `/teachers/delete/<id>` | `POST` | `super_admin`, `admin` | Deletes a teacher record with confirmation. |
| `/users` | `GET` | `super_admin` | Displays provisioned accounts and complete system audit trail. |
| `/users/add` | `POST` | `super_admin` | Provisions a new Administrator or Viewer account. |
| `/users/delete/<id>` | `POST` | `super_admin` | Deletes a user account (prevents self-deletion). |
| `/library` | `GET` | Authenticated | Displays book catalog inventory. |
| `/library/add` | `POST` | `super_admin`, `admin` | Adds new title and available copies to catalog. |
| `/fees` | `GET` | Authenticated | Ledger of fee transactions and total revenue counter. |
| `/fees/add` | `POST` | `super_admin`, `admin` | Records a student payment receipt. |
| `/attendance` | `GET` | Authenticated | Classroom roll-call and attendance status records. |
| `/exams` | `GET` | Authenticated | Academic evaluation marks and maximum score table. |

---

## 💡 Technical Highlights & UI Architecture

1. **Backend Integrity Guaranteed**:
   * Existing CLI programs (`Main.py`, `Student_Manegement_System.py`, etc.) and database tables remain 100% intact.
   * Parameterized SQL queries are used throughout to prevent SQL injection vulnerabilities.
2. **True Role-Based Security**:
   * Viewer users see a clean read-only directory with mutating buttons omitted.
   * Direct POST requests to mutating endpoints by unauthorized roles are intercepted by `@role_required` and redirected with an Access Denied alert.
3. **No Linter Warnings**:
   * Chart.js data is decoupled from template tags via `<script type="application/json">` blocks, eliminating inline syntax warnings in modern code editors.
4. **Fluid Responsiveness**:
   * Sidebar collapses into a compact desktop mode or transforms into an off-canvas mobile drawer with smooth backdrop overlays.

---

## 📜 License
This project is open-source and available under the **MIT License**.
