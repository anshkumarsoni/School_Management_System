import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("AIVEN_DB_HOST"),
        port=int(os.getenv("AIVEN_DB_PORT", "23236")),
        user=os.getenv("AIVEN_DB_USER"),
        password=os.getenv("AIVEN_DB_PASSWORD"),
        database=os.getenv("AIVEN_DB_NAME"),
        ssl_ca=os.path.join(os.path.dirname(__file__), "ca.pem"),
        ssl_verify_cert=True
    )

    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Fee_Transactions (
        RECEIPT_NO INT AUTO_INCREMENT PRIMARY KEY,
        ROLL_NUMBER VARCHAR(20) NOT NULL,
        AMOUNT_PAID DECIMAL(10, 2) NOT NULL,
        PAYMENT_DATE DATE NOT NULL,
        PAYMENT_MODE ENUM(
            'Cash', 'UPI', 'Card', 'Cheque', 'Net Banking'
        ) NOT NULL,
        REMARKS VARCHAR(100)
    )
    """)

    conn.commit()
    print("Fee_Transactions table created successfully!")

    cursor.execute("SHOW TABLES")

    print("\nAIVEN DATABASE TABLES:")
    for table in cursor.fetchall():
        print(table[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Database Error:", e)