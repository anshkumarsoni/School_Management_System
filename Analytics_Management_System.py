# --------------------------------- IMPORT COMMANDS ---------------------------------
import matplotlib.pyplot as plt
from utils import get_connection, clear_screen, pause_and_clear

# --------------------------------- ANALYTICS FUNCTION ------------------------------
def plot_school_demographics():
    con = None
    cur = None
    try:
        con = get_connection()
        if not con:
            print("Database connection failed.")
            return
        cur = con.cursor()

        # 1. Total Student & Teacher Counts
        cur.execute("SELECT COUNT(*) FROM Students_Details")
        total_students = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Teachers_Details")
        total_teachers = cur.fetchone()[0]

        if total_students == 0:
            print("No student records available to generate demographics.")
            pause_and_clear()
            return

        # 2. Query Enrollment by Class
        cur.execute("""
            SELECT CLASS, COUNT(*) 
            FROM Students_Details 
            GROUP BY CLASS 
            ORDER BY CLASS
        """)
        class_data = cur.fetchall()
        classes = [r[0] for r in class_data]
        student_counts = [r[1] for r in class_data]

        # 3. Query Gender Distribution
        cur.execute("""
            SELECT GENDER, COUNT(*) 
            FROM Students_Details 
            GROUP BY GENDER
        """)
        gender_data = cur.fetchall()
        genders = [r[0] for r in gender_data]
        gender_counts = [r[1] for r in gender_data]

        # 4. Setup 2-in-1 Dashboard Window
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(
            f"School Demographics & Executive Overview\n(Total Students: {total_students}  |  Total Faculty: {total_teachers}  |  Active Classes: {len(classes)})",
            fontsize=14, fontweight="bold"
        )

        # Subplot 1: Class Enrollment
        bars = ax1.bar(classes, student_counts, color="#3498db", edgecolor="black", width=0.55)
        for bar in bars:
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + (max(student_counts) * 0.02),
                f"{int(height)}",
                ha="center", va="bottom",
                fontweight="bold", fontsize=9
            )
        ax1.set_title("Student Enrollment by Class", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Class / Grade", fontweight="bold")
        ax1.set_ylabel("Number of Students", fontweight="bold")
        ax1.grid(axis="y", linestyle=":", alpha=0.6)
        ax1.set_ylim(0, max(student_counts) * 1.18 if student_counts else 10)

        # Subplot 2: Gender Distribution
        gender_colors_map = {"Male": "#2980b9", "Female": "#e84393", "Other": "#9b59b6"}
        pie_colors = [gender_colors_map.get(g, "#95a5a6") for g in genders]

        wedges, texts, autotexts = ax2.pie(
            gender_counts,
            labels=[f"{g} ({c})" for g, c in zip(genders, gender_counts)],
            colors=pie_colors,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
        )
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(10)

        ax2.set_title("Gender Ratio Breakdown", fontsize=11, fontweight="bold")

        plt.tight_layout()
        print("\nOpening Executive Demographics Dashboard... (Close the chart window to return)")
        plt.show()

    except Exception as e:
        print("Demographics Chart Error:", e)
        pause_and_clear()
    finally:
        if con:
            cur.close()
            con.close()