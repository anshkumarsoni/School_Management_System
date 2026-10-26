# ================================================================================
#       AIVEN CLOUD MYSQL REPLICATION & AUTO-BACKUP SYNC ENGINE
#       (Real-Time Cloud Synchronization, Schema Mirroring & Data Replication)
# ================================================================================

import os
import sys
import time
import datetime
import mysql.connector as ms
from dotenv import load_dotenv
from tabulate import tabulate

from utils import (
    clear_screen,
    get_connection,
    pause_and_clear,
    center_text
)

# Load environment configuration
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

# Track last sync in-memory / state
LAST_SYNC_META = {
    "last_sync_time": None,
    "last_synced_tables": 0,
    "last_synced_rows": 0,
    "last_status": "Not Synced Yet"
}


def get_aiven_connection():
    """Establishes an SSL-encrypted connection to the Aiven Cloud MySQL database."""
    host = os.getenv("AIVEN_DB_HOST")
    port = int(os.getenv("AIVEN_DB_PORT", 23236))
    user = os.getenv("AIVEN_DB_USER")
    password = os.getenv("AIVEN_DB_PASSWORD")
    database = os.getenv("AIVEN_DB_NAME", "defaultdb")

    if not host or not password:
        return None

    try:
        con = ms.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl_disabled=False
        )
        return con
    except ms.Error as e:
        print("Aiven Connection Error:", e)
        return None


def test_aiven_connection():
    """Tests Aiven Cloud connection and returns health status, latency, and server info."""
    start_time = time.time()
    con = get_aiven_connection()
    if not con:
        return {
            "connected": False,
            "latency_ms": 0,
            "server_version": "N/A",
            "host": os.getenv("AIVEN_DB_HOST", "Not Configured"),
            "port": os.getenv("AIVEN_DB_PORT", 23236),
            "database": os.getenv("AIVEN_DB_NAME", "defaultdb"),
            "error": "Failed to connect to Aiven Cloud MySQL. Check .env configuration."
        }

    try:
        latency = round((time.time() - start_time) * 1000, 1)
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT VERSION() AS ver, DATABASE() AS db_name")
        res = cur.fetchone()
        cur.execute("SHOW TABLES")
        tables_cnt = len(cur.fetchall())
        cur.close()
        con.close()

        return {
            "connected": True,
            "latency_ms": latency,
            "server_version": res["ver"] if res else "Unknown",
            "host": os.getenv("AIVEN_DB_HOST"),
            "port": os.getenv("AIVEN_DB_PORT", 23236),
            "database": res["db_name"] if res else "defaultdb",
            "table_count": tables_cnt,
            "error": None
        }
    except ms.Error as e:
        return {
            "connected": False,
            "latency_ms": 0,
            "server_version": "N/A",
            "host": os.getenv("AIVEN_DB_HOST"),
            "port": os.getenv("AIVEN_DB_PORT", 23236),
            "database": os.getenv("AIVEN_DB_NAME", "defaultdb"),
            "error": str(e)
        }


def sync_local_to_aiven():
    """Replicates full schema and all table records from Local MySQL to Aiven Cloud MySQL."""
    local_con = get_connection()
    if not local_con:
        return False, "Failed to connect to Local MySQL database."

    cloud_con = get_aiven_connection()
    if not cloud_con:
        local_con.close()
        return False, "Failed to connect to Aiven Cloud MySQL server. Check internet and .env credentials."

    local_cur = local_con.cursor(dictionary=True)
    cloud_cur = cloud_con.cursor(dictionary=True)

    try:
        # Disable foreign key checks on Aiven Cloud during schema setup
        cloud_cur.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Discover all base tables in local database
        local_cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [list(r.values())[0] for r in local_cur.fetchall()]

        synced_tables = 0
        total_rows_copied = 0
        table_summary = []

        for table in tables:
            # 1. Fetch CREATE TABLE DDL from Local
            local_cur.execute(f"SHOW CREATE TABLE `{table}`")
            create_res = local_cur.fetchone()
            create_stmt = list(create_res.values())[1]

            # 2. Re-create table on Aiven Cloud
            cloud_cur.execute(f"DROP TABLE IF EXISTS `{table}`")
            cloud_cur.execute(create_stmt)

            # 3. Read data from Local
            local_cur.execute(f"SELECT * FROM `{table}`")
            rows = local_cur.fetchall()

            if rows:
                columns = list(rows[0].keys())
                placeholders = ", ".join(["%s"] * len(columns))
                cols_joined = ", ".join([f"`{c}`" for c in columns])
                insert_stmt = f"INSERT INTO `{table}` ({cols_joined}) VALUES ({placeholders})"

                data_tuples = [tuple(r[c] for c in columns) for r in rows]
                cloud_cur.executemany(insert_stmt, data_tuples)
                total_rows_copied += len(data_tuples)
                table_summary.append({"table": table, "rows": len(data_tuples), "status": "Synced"})
            else:
                table_summary.append({"table": table, "rows": 0, "status": "Schema Created"})

            synced_tables += 1

        # Re-enable foreign key checks and commit
        cloud_cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        cloud_con.commit()

        sync_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        LAST_SYNC_META["last_sync_time"] = sync_timestamp
        LAST_SYNC_META["last_synced_tables"] = synced_tables
        LAST_SYNC_META["last_synced_rows"] = total_rows_copied
        LAST_SYNC_META["last_status"] = "Success"

        msg = f"Synced {synced_tables} tables and {total_rows_copied} records to Aiven Cloud at {sync_timestamp}."
        return True, {
            "message": msg,
            "synced_tables": synced_tables,
            "total_rows": total_rows_copied,
            "timestamp": sync_timestamp,
            "table_summary": table_summary
        }

    except ms.Error as e:
        LAST_SYNC_META["last_status"] = f"Failed: {e}"
        return False, f"Replication Error: {e}"
    finally:
        local_cur.close()
        local_con.close()
        cloud_cur.close()
        cloud_con.close()


def get_sync_overview():
    """Returns combined status of local vs Aiven Cloud tables for the Web dashboard."""
    local_con = get_connection()
    cloud_con = get_aiven_connection()

    overview = {
        "cloud_health": test_aiven_connection(),
        "tables": [],
        "total_local_rows": 0,
        "total_cloud_rows": 0,
        "last_sync": LAST_SYNC_META
    }

    if not local_con:
        return overview

    local_cur = local_con.cursor(dictionary=True)
    cloud_cur = cloud_con.cursor(dictionary=True) if cloud_con else None

    try:
        local_cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        local_tables = [list(r.values())[0] for r in local_cur.fetchall()]

        for tbl in local_tables:
            # Count local rows
            local_cur.execute(f"SELECT COUNT(*) AS cnt FROM `{tbl}`")
            loc_cnt = local_cur.fetchone()["cnt"]
            overview["total_local_rows"] += loc_cnt

            # Count cloud rows
            cloud_cnt = 0
            if cloud_cur:
                try:
                    cloud_cur.execute(f"SELECT COUNT(*) AS cnt FROM `{tbl}`")
                    cloud_cnt = cloud_cur.fetchone()["cnt"]
                    overview["total_cloud_rows"] += cloud_cnt
                except Exception:
                    cloud_cnt = "--"

            overview["tables"].append({
                "table_name": tbl,
                "local_rows": loc_cnt,
                "cloud_rows": cloud_cnt,
                "in_sync": (loc_cnt == cloud_cnt) if isinstance(cloud_cnt, int) else False
            })

    except Exception as e:
        print("Overview error:", e)
    finally:
        local_cur.close()
        local_con.close()
        if cloud_cur:
            cloud_cur.close()
            cloud_con.close()

    return overview


# --------------------------------- CLI TERMINAL INTERACTION -----------------------

def cloud_sync_menu():
    """Terminal CLI user interface for Aiven Cloud Sync."""
    while True:
        clear_screen()
        center_text("=" * 80)
        center_text("AIVEN CLOUD MYSQL DATABASE SYNCHRONIZATION & REPLICATION")
        center_text("=" * 80)

        health = test_aiven_connection()
        status_text = "CONNECTED (Online)" if health["connected"] else f"DISCONNECTED ({health.get('error')})"
        print(f"\nAiven Cloud Status: {status_text}")
        print(f"Cloud Host        : {health.get('host')}:{health.get('port')}")
        print(f"Cloud Database    : {health.get('database')}")
        print(f"Latency           : {health.get('latency_ms')} ms")
        if LAST_SYNC_META["last_sync_time"]:
            print(f"Last Sync Time    : {LAST_SYNC_META['last_sync_time']} ({LAST_SYNC_META['last_synced_tables']} tables, {LAST_SYNC_META['last_synced_rows']} rows)")
        print("-" * 80)

        print("\n1. Test Aiven Cloud Connection Health")
        print("2. Sync / Replicate All Tables & Data to Aiven Cloud Now")
        print("3. View Local vs Aiven Cloud Tables Comparison")
        print("0. Return to Main Menu\n")

        choice = input("Enter your choice (0-3): ").strip()

        if choice == "1":
            clear_screen()
            print("\nTesting connection to Aiven Cloud MySQL...\n")
            h = test_aiven_connection()
            if h["connected"]:
                print(f"[SUCCESS] Connected to Aiven Cloud MySQL!")
                print(f" - Host: {h['host']}:{h['port']}")
                print(f" - Server Version: {h['server_version']}")
                print(f" - Database: {h['database']}")
                print(f" - Roundtrip Latency: {h['latency_ms']} ms")
                print(f" - Tables Present: {h.get('table_count', 0)}")
            else:
                print(f"[FAILED] Could not connect: {h.get('error')}")
            pause_and_clear()

        elif choice == "2":
            clear_screen()
            print("\nStarting full replication from Local MySQL -> Aiven Cloud MySQL...")
            print("Please wait while tables and data are synchronized...\n")
            ok, res = sync_local_to_aiven()
            if ok:
                print(f"[SUCCESS] {res['message']}")
                print(tabulate([[t["table"], t["rows"], t["status"]] for t in res["table_summary"]], headers=["Table Name", "Records Copied", "Status"], tablefmt="fancy_grid"))
            else:
                print(f"[FAILED] {res}")
            pause_and_clear()

        elif choice == "3":
            clear_screen()
            print("\nFetching Local vs Cloud Table Comparison...\n")
            ov = get_sync_overview()
            table_data = []
            for t in ov["tables"]:
                sync_badge = "YES" if t["in_sync"] else "MISMATCH"
                table_data.append([t["table_name"], t["local_rows"], t["cloud_rows"], sync_badge])
            print(tabulate(table_data, headers=["Table Name", "Local Rows", "Cloud Rows", "In Sync?"], tablefmt="fancy_grid"))
            print(f"\nTotal Local Records: {ov['total_local_rows']}  |  Total Cloud Records: {ov['total_cloud_rows']}")
            pause_and_clear()

        elif choice == "0":
            break
        else:
            print("\nInvalid choice.")
            pause_and_clear()
