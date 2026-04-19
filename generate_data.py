import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "finance_bridge.db"

PROJECTS = [
    (1, "Metro Link Upgrade", "City Infrastructure Pty Ltd", "2026-01-03", "2026-12-31", 52000000, "CC-101"),
    (2, "Harbour Roadworks", "National Build Group", "2026-02-01", "2026-11-30", 43000000, "CC-102"),
    (3, "Eastside Apartment", "Urban Developments", "2026-03-15", "2026-10-20", 28000000, "CC-103"),
]

EXPENSE_TYPES = ["Subcontractor", "Materials", "Plant Hire", "Travel", "Permits"]
SAP_COST_CODES = ["SAP-5001", "SAP-5002", "SAP-5003", "SAP-5004", "SAP-5005"]
GL_ACCOUNTS = ["GL-1000", "GL-2100", "GL-3300", "GL-4500", "GL-5000"]
AUDIT_ISSUES = ["Reconciliation Gap", "Policy Exception", "Missing Supporting Docs", "Duplicate Payment", "Tax Compliance" ]
MODULES = ["AP", "Banking", "Treasury", "SAP Interface", "Expense Management"]


def create_tables(cursor):
    cursor.executescript(
        """
        DROP TABLE IF EXISTS projects;
        DROP TABLE IF EXISTS site_expenses;
        DROP TABLE IF EXISTS sap_ledger;
        DROP TABLE IF EXISTS cash_forecasts;
        DROP TABLE IF EXISTS audit_log;

        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY,
            project_name TEXT,
            client TEXT,
            start_date TEXT,
            end_date TEXT,
            project_budget INTEGER,
            sap_cost_center TEXT
        );

        CREATE TABLE site_expenses (
            expense_id INTEGER PRIMARY KEY,
            project_id INTEGER,
            booking_date TEXT,
            expense_type TEXT,
            amount REAL,
            sap_cost_code TEXT,
            vendor TEXT,
            status TEXT,
            comment TEXT
        );

        CREATE TABLE sap_ledger (
            ledger_id INTEGER PRIMARY KEY,
            project_id INTEGER,
            posting_date TEXT,
            gl_account TEXT,
            amount REAL,
            doc_type TEXT,
            description TEXT
        );

        CREATE TABLE cash_forecasts (
            forecast_id INTEGER PRIMARY KEY,
            project_id INTEGER,
            forecast_date TEXT,
            expected_cash_in REAL,
            expected_cash_out REAL,
            payment_schedule TEXT,
            site_progress_pct REAL
        );

        CREATE TABLE audit_log (
            audit_id INTEGER PRIMARY KEY,
            event_date TEXT,
            project_id INTEGER,
            module TEXT,
            issue_type TEXT,
            status TEXT,
            notes TEXT
        );
        """
    )


def random_date(start_date, end_date):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    span = (end - start).days
    return (start + timedelta(days=random.randint(0, max(span, 0)))).date().isoformat()


def generate_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_tables(cursor)

    cursor.executemany(
        "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)",
        PROJECTS,
    )

    expense_rows = []
    ledger_rows = []
    forecast_rows = []
    audit_rows = []

    for project in PROJECTS:
        project_id, project_name, client, start_date, end_date, budget, cost_center = project
        days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
        for i in range(12):
            booking = random_date(start_date, end_date)
            amount = round(random.uniform(25000, 275000), 2)
            cost_code = random.choice(SAP_COST_CODES)
            status = random.choice(["Pending", "Approved", "Paid"])
            vendor = random.choice(["Harris Civil", "BridgeCo", "SuperBuild", "Aussie Concrete"])
            comment = "" if random.random() > 0.30 else "Possible cost allocation mismatch"
            expense_rows.append((None, project_id, booking, random.choice(EXPENSE_TYPES), amount, cost_code, vendor, status, comment))

            posting = random_date(start_date, end_date)
            gl_account = random.choice(GL_ACCOUNTS)
            ledger_amount = amount if random.random() > 0.22 else amount * random.uniform(0.85, 1.18)
            description = f"Posted from {vendor} for {project_name}"
            ledger_rows.append((None, project_id, posting, gl_account, round(ledger_amount, 2), "INV", description))

        progress = 0.2
        for weeks in range(6):
            forecast_date = (datetime.fromisoformat(start_date) + timedelta(days=weeks * 28)).date().isoformat()
            expected_in = round(budget * random.uniform(0.05, 0.12), 2)
            expected_out = round(budget * random.uniform(0.08, 0.16), 2)
            payment_schedule = "Accelerated" if expected_out > expected_in else "Stable"
            site_progress_pct = min(100.0, round(progress * 100, 1))
            progress += random.uniform(0.09, 0.16)
            forecast_rows.append((None, project_id, forecast_date, expected_in, expected_out, payment_schedule, site_progress_pct))

        audit_rows.append((None, random_date(start_date, end_date), project_id, random.choice(MODULES), "Reconciliation Gap", "Open", "Expense and ledger values need matching."))
        audit_rows.append((None, random_date(start_date, end_date), project_id, random.choice(MODULES), "Policy Exception", "Under Review", "Concur entry missing approval trace."))

    # Add targeted anomalies for demo
    expense_rows.append((None, 1, "2026-04-12", "Subcontractor", 342000.00, "SAP-5002", "Harris Civil", "Pending", "Mismatch to SAP budget code"))
    ledger_rows.append((None, 1, "2026-04-14", "GL-4500", 318500.00, "INV", "Expected amount differs from site expense"))
    expense_rows.append((None, 2, "2026-06-07", "Materials", 186000.00, "SAP-5001", "Aussie Concrete", "Approved", "High variance to payment schedule"))
    ledger_rows.append((None, 2, "2026-06-10", "GL-3300", 186000.00, "INV", "Matched ledger posting"))
    forecast_rows.append((None, 3, "2026-07-01", 1500000.00, 2300000.00, "Accelerated", 72.0))
    audit_rows.append((None, "2026-07-08", 3, "SAP Interface", "Missing Supporting Docs", "Open", "Site invoice not uploaded to Concur."))

    cursor.executemany(
        "INSERT INTO site_expenses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        expense_rows,
    )
    cursor.executemany(
        "INSERT INTO sap_ledger VALUES (?, ?, ?, ?, ?, ?, ?)",
        ledger_rows,
    )
    cursor.executemany(
        "INSERT INTO cash_forecasts VALUES (?, ?, ?, ?, ?, ?, ?)",
        forecast_rows,
    )
    cursor.executemany(
        "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?)",
        audit_rows,
    )

    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with synthetic finance and reconciliation data.")


if __name__ == "__main__":
    generate_data()
