"""
Generates realistic construction-industry CSV files themed for a Tier 1 Australian
construction company (Lendlease / Multiplex scale) — Melbourne HQ, national projects.

Outputs: projects.csv, site_expenses.csv, sap_ledger.csv, cash_forecasts.csv, audit_log.csv
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

COMPANY = "Lendlease Construction (Pty) Ltd"

# ── Projects ──────────────────────────────────────────────────────────────────
# Typical Tier 1 portfolio: CBD towers, hospitals, mixed-use, transport, data centres
PROJECTS = [
    (1, "Collins Arch — Stage 2 Fit-Out",   COMPANY, "2026-01-05", "2026-12-18",  185_000_000, "CC-MEL-01", "Commercial",     "VIC", "Melbourne CBD"),
    (2, "Victorian Heart Hospital Ext.",     COMPANY, "2026-02-03", "2027-06-30",  310_000_000, "CC-MEL-02", "Healthcare",     "VIC", "Clayton"),
    (3, "Southbank Precinct Tower C",        COMPANY, "2026-03-10", "2027-09-30",  420_000_000, "CC-MEL-03", "Mixed-Use",      "VIC", "Southbank"),
    (4, "Melbourne Metro — Station Works",   COMPANY, "2026-01-12", "2026-11-28",  560_000_000, "CC-MEL-04", "Infrastructure", "VIC", "Melbourne CBD"),
    (5, "Sydney Tech Hub — Pyrmont",         COMPANY, "2026-04-07", "2027-04-30",   98_000_000, "CC-SYD-05", "Commercial",     "NSW", "Pyrmont"),
    (6, "Perth Data Centre — Stage 1",       COMPANY, "2026-02-16", "2026-12-20",  145_000_000, "CC-PER-06", "Industrial",     "WA",  "East Perth"),
]

# ── Vendor panel (approved subcontractors & suppliers) ────────────────────────
VENDORS = {
    "Subcontractor": [
        "John Holland Group",
        "Watpac Civil & Mining",
        "Probuild Constructions",
        "Kane Constructions",
        "Hickory Group",
        "Hacer Group",
        "Buxton Construction",
        "Kapitol Group",
        "Built Environs",
        "Cockram Constructions",
    ],
    "Materials": [
        "Boral Construction Materials",
        "Holcim Australia Pty Ltd",
        "BlueScope Distribution",
        "Adbri Masonry",
        "Hanson Construction Materials",
        "CSR Building Products",
        "James Hardie Building Products",
        "Rebar Direct Pty Ltd",
        "Sika Australia",
        "Saint-Gobain Placo",
    ],
    "Plant Hire": [
        "Coates Hire Operations",
        "Kennards Hire",
        "Tutt Bryant Equipment",
        "Sherrin Rentals",
        "Adaptalift Hyster",
        "All Cranes Hire & Sales",
    ],
    "Professional Services": [
        "AECOM Australia Pty Ltd",
        "GHD Advisory",
        "WSP Australia",
        "Jacobs Engineering Group",
        "Stantec Consulting",
        "Arcadis Australia Pacific",
        "Arup Pty Ltd",
        "Turner & Townsend",
    ],
    "Permits & Compliance": [
        "Vic Department of Transport",
        "City of Melbourne Council",
        "DELWP Victoria",
        "EPA Victoria",
        "WorkSafe Victoria",
        "NSW Planning Department",
    ],
    "Travel & Accommodation": [
        "Crown Towers Melbourne",
        "Marriott Hotels Australia",
        "FCm Travel Solutions",
        "Corporate Travel Management (CTM)",
        "Mantra on Little Bourke",
    ],
}

EXPENSE_TYPES  = list(VENDORS.keys())
EXPENSE_WEIGHT = [0.40, 0.27, 0.12, 0.10, 0.06, 0.05]

SAP_COST_CODES = {
    "Subcontractor":          "SAP-5001",
    "Materials":              "SAP-5002",
    "Plant Hire":             "SAP-5003",
    "Professional Services":  "SAP-5004",
    "Permits & Compliance":   "SAP-5005",
    "Travel & Accommodation": "SAP-5006",
}

GL_ACCOUNTS = {
    "Subcontractor":          ("GL-6100", "Direct Labour & Subcontract Costs"),
    "Materials":              ("GL-6200", "Raw Materials & Consumables"),
    "Plant Hire":             ("GL-6300", "Equipment & Plant Hire"),
    "Professional Services":  ("GL-6400", "Professional & Consulting Fees"),
    "Permits & Compliance":   ("GL-6500", "Regulatory Fees & Permit Costs"),
    "Travel & Accommodation": ("GL-6600", "Travel & Accommodation"),
}

# Tier 1 invoice ranges — larger floor/ceiling than generic
AMOUNT_RANGE = {
    "Subcontractor":          (120_000,  1_800_000),
    "Materials":              (25_000,    480_000),
    "Plant Hire":             (8_500,     145_000),
    "Professional Services":  (12_000,    220_000),
    "Permits & Compliance":   (2_500,      55_000),
    "Travel & Accommodation": (800,          6_500),
}

# ── Audit templates (Tier 1 / Treasury-relevant issues) ──────────────────────
AUDIT_TEMPLATES = [
    ("Reconciliation Gap",       "Open",          "Site expense amount does not reconcile with SAP S/4HANA ledger posting. Treasury review required."),
    ("Policy Exception",         "Under Review",  "Invoice submitted outside approved vendor panel. Procurement compliance review in progress."),
    ("Missing Supporting Docs",  "Open",          "Tax invoice or delivery docket not attached in Concur. Document deadline: 5 business days."),
    ("Duplicate Payment Risk",   "Under Review",  "Duplicate invoice detected across two SAP cost centres. AP automation hold applied."),
    ("Tax Compliance",           "Resolved",      "GST coding error on cross-state delivery corrected. BAS adjustment lodged with ATO."),
    ("Budget Overrun Warning",   "Open",          "Committed spend exceeds 90% of approved project budget. CFO and Project Director sign-off required."),
    ("Unapproved Variation",     "Under Review",  "Scope variation raised on site without approved Variation Order (VO). Contract admin notified."),
    ("Late Payment Penalty",     "Resolved",      "Subcontractor late payment fee applied under the Security of Payment Act 2002 (VIC). Settled in full."),
    ("Bank Guarantee Expiry",    "Open",          "Performance bank guarantee expiring within 30 days. Treasury to arrange renewal with ANZ."),
    ("Retention Release",        "Under Review",  "Practical completion milestone reached. Subcontractor retention release pending QS sign-off."),
    ("Intercompany Recharge",    "Open",          "Shared services recharge from Lendlease Corporate not matched to project WBS. Finance to clarify allocation."),
]

MODULES = ["AP", "Banking & Treasury", "SAP S/4HANA", "Concur Expense", "Project Accounting", "Procurement", "Payroll"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def random_date(start: str, end: str) -> str:
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)
    span = max((e - s).days, 1)
    return (s + timedelta(days=random.randint(0, span))).date().isoformat()


def s_curve_amount(budget: int, expense_type: str, week: int, total_weeks: int) -> float:
    lo, hi = AMOUNT_RANGE[expense_type]
    progress = week / max(total_weeks, 1)
    if progress < 0.10:
        mult = random.uniform(0.35, 0.55)   # mobilisation — low spend
    elif progress < 0.25:
        mult = random.uniform(0.70, 0.95)   # ramp-up
    elif progress < 0.75:
        mult = random.uniform(0.90, 1.25)   # peak construction
    elif progress < 0.90:
        mult = random.uniform(0.55, 0.80)   # fit-out / wind-down
    else:
        mult = random.uniform(0.20, 0.45)   # defects & close-out
    raw = random.uniform(lo, hi) * mult
    return round(max(lo * 0.4, min(raw, hi * 1.35)), 2)


def write_csv(filename: str, headers: list, rows: list):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  Written {len(rows):>4} rows  →  {path}")


# ── Generators ────────────────────────────────────────────────────────────────

def gen_projects():
    headers = [
        "project_id", "project_name", "client", "start_date", "end_date",
        "project_budget", "sap_cost_center", "sector", "state", "location",
    ]
    write_csv("projects.csv", headers, PROJECTS)


def gen_expenses_and_ledger():
    expense_rows = []
    ledger_rows  = []
    exp_id = 1
    led_id = 1

    for proj in PROJECTS:
        pid, name, client, start, end, budget, cc, sector, state, location = proj
        start_dt   = datetime.fromisoformat(start)
        end_dt     = datetime.fromisoformat(end)
        total_weeks = max((end_dt - start_dt).days // 7, 1)
        n_expenses  = random.randint(28, 42)   # Tier 1: more transactions

        for i in range(n_expenses):
            week     = random.randint(0, total_weeks)
            exp_type = random.choices(EXPENSE_TYPES, weights=EXPENSE_WEIGHT)[0]
            vendor   = random.choice(VENDORS[exp_type])
            amount   = s_curve_amount(budget, exp_type, week, total_weeks)
            cost_code = SAP_COST_CODES[exp_type]
            booking   = random_date(start, end)
            status    = random.choices(
                ["Approved", "Pending", "Paid", "On Hold"],
                weights=[0.40, 0.22, 0.32, 0.06]
            )[0]
            comment = ""
            if random.random() < 0.15:
                comment = random.choice([
                    "Possible cost allocation mismatch — verify WBS element",
                    "Vendor invoice pending project manager approval",
                    "High variance to approved payment schedule",
                    "Mismatch between SAP cost code and VO reference",
                    "Awaiting delivery confirmation from site supervisor",
                    "Retention clause applies — partial payment released",
                    "Intercompany recharge — allocation pending CFO review",
                ])
            source = random.choices(
                ["Concur Export", "Site System", "Manual Entry"],
                weights=[0.78, 0.16, 0.06]
            )[0]
            expense_rows.append((
                exp_id, pid, booking, exp_type, amount,
                cost_code, vendor, status, comment, source,
            ))

            # SAP ledger posting — 22% chance of reconciliation gap
            posting_dt = datetime.fromisoformat(booking) + timedelta(days=random.randint(1, 6))
            posting    = posting_dt.date().isoformat()
            gl, gl_desc = GL_ACCOUNTS[exp_type]
            if random.random() < 0.22:
                led_amount = round(amount * random.uniform(0.87, 1.18), 2)
                led_desc   = f"[VARIANCE] {gl_desc} — {name}"
            else:
                led_amount = amount
                led_desc   = f"{gl_desc} — {name}"
            ledger_rows.append((
                led_id, pid, posting, gl, led_amount, "INV", led_desc, vendor,
            ))

            exp_id += 1
            led_id += 1

    # ── Targeted demo anomalies (treasury-relevant) ────────────────────────
    # 1. Large subcontract discrepancy — Collins Arch
    expense_rows.append((exp_id,   1, "2026-04-14", "Subcontractor",    895_000.00,  "SAP-5001", "Hickory Group",               "Pending",   "Mismatch to SAP budget code — VO-0044 not yet approved",         "Concur Export"))
    ledger_rows.append( (led_id,   1, "2026-04-16", "GL-6100",          832_500.00,  "INV",      "[VARIANCE] Direct Labour & Subcontract — Collins Arch", "Hickory Group"))

    # 2. Materials invoice on hold — Heart Hospital
    expense_rows.append((exp_id+1, 2, "2026-06-09", "Materials",        312_000.00,  "SAP-5002", "Holcim Australia Pty Ltd",    "On Hold",   "Delivery docket mismatch — site rejected 40 palettes",           "Site System"))
    ledger_rows.append( (led_id+1, 2, "2026-06-12", "GL-6200",          312_000.00,  "INV",      "Raw Materials — Victorian Heart Hospital", "Holcim Australia Pty Ltd"))

    # 3. Cash crunch period — Southbank Tower C
    expense_rows.append((exp_id+2, 3, "2026-09-01", "Subcontractor",  1_250_000.00,  "SAP-5001", "John Holland Group",          "Approved",  "Accelerated milestone payment — Practical Completion Stage 3",   "Concur Export"))
    ledger_rows.append( (led_id+2, 3, "2026-09-03", "GL-6100",        1_250_000.00,  "INV",      "Direct Labour — Southbank Precinct Tower C", "John Holland Group"))

    # 4. Budget overrun — Metro Station Works
    expense_rows.append((exp_id+3, 4, "2026-08-20", "Professional Services", 540_000.00, "SAP-5004", "AECOM Australia Pty Ltd", "Approved",  "Additional scope for geotechnical re-assessment — approved by PMO", "Manual Entry"))
    ledger_rows.append( (led_id+3, 4, "2026-08-22", "GL-6400",          498_000.00,  "INV",      "[VARIANCE] Professional Fees — Melbourne Metro", "AECOM Australia Pty Ltd"))

    exp_headers = [
        "expense_id", "project_id", "booking_date", "expense_type", "amount",
        "sap_cost_code", "vendor", "status", "comment", "source_system",
    ]
    led_headers = [
        "ledger_id", "project_id", "posting_date", "gl_account", "amount",
        "doc_type", "description", "vendor",
    ]
    write_csv("site_expenses.csv", exp_headers, expense_rows)
    write_csv("sap_ledger.csv",    led_headers, ledger_rows)


def gen_forecasts():
    rows = []
    fid  = 1
    for proj in PROJECTS:
        pid, name, client, start, end, budget, cc, sector, state, location = proj
        start_dt    = datetime.fromisoformat(start)
        end_dt      = datetime.fromisoformat(end)
        total_months = max(round((end_dt - start_dt).days / 30), 1)

        progress = 0.04
        for m in range(min(total_months, 12)):
            fdate = (start_dt + timedelta(days=m * 30)).date().isoformat()
            phase = m / max(total_months - 1, 1)

            # S-curve cash flow profile
            if phase < 0.15:
                out_pct = random.uniform(0.03, 0.06)
                in_pct  = random.uniform(0.01, 0.04)
            elif phase < 0.70:
                out_pct = random.uniform(0.09, 0.15)
                in_pct  = random.uniform(0.07, 0.13)
            else:
                out_pct = random.uniform(0.03, 0.07)
                in_pct  = random.uniform(0.05, 0.10)

            expected_out = round(budget * out_pct, 2)
            expected_in  = round(budget * in_pct,  2)
            schedule     = "Accelerated" if expected_out > expected_in * 1.12 else "Stable"
            site_pct     = round(min(progress * 100, 100.0), 1)
            progress    += random.uniform(0.06, 0.13)

            rows.append((fid, pid, fdate, expected_in, expected_out, schedule, site_pct))
            fid += 1

    # Anomaly: Southbank Tower C — cash crunch Q3 (large subcontractor milestone)
    rows.append((fid,   3, "2026-09-01", 2_800_000.00, 9_500_000.00, "Accelerated", 58.0))
    # Anomaly: Metro — drawdown delay
    rows.append((fid+1, 4, "2026-07-01", 1_500_000.00, 8_200_000.00, "Accelerated", 44.0))

    headers = [
        "forecast_id", "project_id", "forecast_date",
        "expected_cash_in", "expected_cash_out", "payment_schedule", "site_progress_pct",
    ]
    write_csv("cash_forecasts.csv", headers, rows)


def gen_audit():
    rows = []
    aid  = 1
    for proj in PROJECTS:
        pid, name, *_ = proj
        start, end = proj[3], proj[4]
        n    = random.randint(3, 5)
        used = random.sample(AUDIT_TEMPLATES, min(n, len(AUDIT_TEMPLATES)))
        for issue_type, status, notes in used:
            rows.append((
                aid,
                random_date(start, end),
                pid,
                random.choice(MODULES),
                issue_type,
                status,
                notes,
            ))
            aid += 1

    # Targeted audit entries
    rows.append((aid,   "2026-07-10", 3, "SAP S/4HANA",      "Missing Supporting Docs", "Open",          "Three subcontractor invoices not uploaded to Concur. Defect liability period commenced."))
    rows.append((aid+1, "2026-08-21", 4, "Project Accounting","Budget Overrun Warning",  "Open",          "Committed spend at 94% of $560M approved budget. CFO and Board notification required."))
    rows.append((aid+2, "2026-05-15", 6, "AP",                "Duplicate Payment Risk",  "Under Review",  "Duplicate invoice SAP-INV-0078 for Coates Hire flagged by AP automation. On hold pending review."))
    rows.append((aid+3, "2026-06-03", 2, "Banking & Treasury","Bank Guarantee Expiry",   "Open",          "ANZ performance bond BG-2024-1132 expiring 2026-07-15. Treasury renewal in progress."))
    rows.append((aid+4, "2026-09-12", 1, "Procurement",       "Unapproved Variation",    "Under Review",  "VO-0044 Hickory Group — $895K variation not yet approved via formal change control process."))

    headers = [
        "audit_id", "event_date", "project_id", "module",
        "issue_type", "status", "notes",
    ]
    write_csv("audit_log.csv", headers, rows)


def gen_bank_facilities():
    """
    Simulates the corporate banking facilities a Tier 1 construction company
    holds: revolving credit, bank guarantee lines, overdraft, and bonding facilities.
    Covenant tests mirror real ANZ / NAB / Westpac project finance terms.
    """
    rows = [
        # id, facility_name, bank, type, limit_aud, drawn_aud, covenant_min_cash_aud, covenant_max_gearing_pct, maturity_date, review_date
        (1, "Revolving Credit Facility",       "ANZ",      "RCF",            250_000_000, 187_500_000, 25_000_000, 55.0, "2027-06-30", "2026-09-30"),
        (2, "Bank Guarantee Line — Projects",  "NAB",      "BG Line",        180_000_000, 142_000_000, 15_000_000, 60.0, "2027-03-31", "2026-06-30"),
        (3, "Working Capital Overdraft",       "Westpac",  "Overdraft",       30_000_000,  18_200_000,  8_000_000, 50.0, "2026-12-31", "2026-06-30"),
        (4, "Performance Bond Facility",       "CBA",      "Bonding",        120_000_000,  89_400_000, 10_000_000, 65.0, "2027-09-30", "2026-09-30"),
        (5, "Project Finance — Metro Works",   "ANZ",      "Project Finance", 95_000_000,  72_300_000, 20_000_000, 70.0, "2026-11-30", "2026-07-31"),
    ]
    headers = [
        "facility_id", "facility_name", "bank", "facility_type",
        "limit_aud", "drawn_aud", "covenant_min_cash_aud",
        "covenant_max_gearing_pct", "maturity_date", "next_review_date",
    ]
    write_csv("bank_facilities.csv", headers, rows)


def gen_weekly_cashflow():
    """
    Generates a rolling 8-week cash position used by the Executive Pulse view.
    Simulates actual vs forecast with a realistic burn curve.
    """
    rows = []
    base_cash = 48_500_000
    today = datetime(2026, 4, 18)
    for w in range(-4, 9):   # 4 weeks history + 8 weeks forward
        week_start = (today + timedelta(weeks=w)).date().isoformat()
        is_forecast = w >= 0
        inflow  = round(random.uniform(8_500_000, 22_000_000), 0)
        outflow = round(random.uniform(14_000_000, 31_000_000), 0)
        net     = inflow - outflow
        base_cash = max(base_cash + net, 5_000_000)
        rows.append((week_start, round(inflow, 0), round(outflow, 0), round(net, 0), round(base_cash, 0), "Forecast" if is_forecast else "Actual"))

    headers = ["week_start", "cash_in", "cash_out", "net_movement", "closing_balance", "type"]
    write_csv("weekly_cashflow.csv", headers, rows)


def gen_bank_accounts():
    """
    Daily cash positions across the group's operating bank accounts.
    Covers the last 10 business days — mirrors what Treasury monitors each morning.
    """
    from datetime import date

    ACCOUNTS = [
        # id, name, bank, bsb, type, opening_base
        (1, "Group Operating Account",     "ANZ",     "013-003", "Operating",    28_500_000),
        (2, "Project Drawdown Account",    "NAB",     "082-057", "Project",      12_800_000),
        (3, "Subcontractor Payment Trust", "Westpac", "033-041", "Trust",         6_200_000),
        (4, "Payroll & Statutory Account", "CBA",     "062-000", "Payroll",       3_900_000),
    ]

    rows = []
    today = date(2026, 4, 18)

    for acct_id, name, bank, bsb, acct_type, opening_base in ACCOUNTS:
        balance = opening_base
        for d in range(9, -1, -1):   # 10 days back to today
            day = today - timedelta(days=d)
            if day.weekday() >= 5:
                continue  # skip weekends

            # Simulate daily inflows/outflows per account type
            if acct_type == "Operating":
                receipts = round(random.uniform(2_500_000, 9_500_000), 0)
                payments = round(random.uniform(4_000_000, 13_000_000), 0)
            elif acct_type == "Project":
                receipts = round(random.uniform(1_000_000, 5_000_000), 0)
                payments = round(random.uniform(2_000_000, 7_500_000), 0)
            elif acct_type == "Trust":
                receipts = round(random.uniform(500_000, 3_000_000), 0)
                payments = round(random.uniform(800_000, 4_000_000), 0)
            else:  # Payroll
                receipts = round(random.uniform(200_000, 800_000), 0)
                payments = round(random.uniform(300_000, 2_500_000), 0)  # payroll runs

            closing = max(balance + receipts - payments, 500_000)
            rows.append((
                acct_id, name, bank, bsb, acct_type,
                day.isoformat(),
                round(balance, 0),
                round(receipts, 0),
                round(payments, 0),
                round(closing, 0),
            ))
            balance = closing

    headers = [
        "account_id", "account_name", "bank", "bsb", "account_type",
        "date", "opening_balance", "receipts", "payments", "closing_balance",
    ]
    write_csv("bank_accounts.csv", headers, rows)


def gen_sap_legacy_extract():
    """
    Generates a 'legacy SAP' ledger extract used for the Transformation Validation page.
    ~15% of rows have deliberate discrepancies vs the current sap_ledger.csv to simulate
    what a dual-run ERP migration check would surface.
    """
    import csv as _csv

    source = OUTPUT_DIR / "sap_ledger.csv"
    if not source.exists():
        print("  Skipping legacy extract — run gen_expenses_and_ledger() first.")
        return

    with open(source, encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        rows = list(reader)

    legacy_rows = []
    for row in rows:
        new_row = dict(row)
        r = random.random()
        if r < 0.08:
            # Amount rounding difference (common in legacy system migrations)
            new_row["amount"] = str(round(float(row["amount"]) * random.uniform(0.995, 1.005), 0))
            new_row["_migration_flag"] = "ROUNDING_DIFF"
        elif r < 0.13:
            # GL account mapped differently in old chart of accounts
            new_row["gl_account"] = new_row["gl_account"].replace("GL-6", "GL-5")
            new_row["_migration_flag"] = "GL_REMAP"
        elif r < 0.15:
            # Missing row (simulate records not migrated)
            new_row["_migration_flag"] = "MISSING_IN_NEW"
        else:
            new_row["_migration_flag"] = "OK"
        legacy_rows.append(new_row)

    path = OUTPUT_DIR / "sap_legacy_extract.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=list(legacy_rows[0].keys()))
        writer.writeheader()
        writer.writerows(legacy_rows)
    print(f"  Written {len(legacy_rows):>4} rows  →  {path}")


def gen_statutory_compliance():
    """
    Generates statutory obligation schedule: BAS/IAS (ATO), payroll tax by state,
    and superannuation SG payments. Amounts derived from project budget/wages proxy.
    As at 19 April 2026.
    """
    from datetime import date as _date

    TODAY = _date(2026, 4, 19)
    rows  = []
    ob_id = 1

    def _status(due_str, force_overdue=False):
        due = _date.fromisoformat(due_str)
        if force_overdue:
            return "Overdue", ""
        if due < TODAY:
            lodged = (_date.fromisoformat(due_str) - timedelta(days=random.randint(1, 5))).isoformat()
            return "Lodged", lodged
        if (due - TODAY).days <= 14:
            return "Pending", ""
        return "Scheduled", ""

    # ── BAS quarterly (GST + PAYG Withholding + PAYG Instalment) ─────────────
    BAS_QUARTERS = [
        ("Q1 FY2026 (Jul–Sep 2025)", "2025-07-01", "2025-09-30", "2025-10-28"),
        ("Q2 FY2026 (Oct–Dec 2025)", "2025-10-01", "2025-12-31", "2026-02-28"),
        ("Q3 FY2026 (Jan–Mar 2026)", "2026-01-01", "2026-03-31", "2026-04-28"),
        ("Q4 FY2026 (Apr–Jun 2026)", "2026-04-01", "2026-06-30", "2026-07-28"),
    ]
    for label, ps, pe, due in BAS_QUARTERS:
        status, lodged = _status(due)
        gst    = round(random.uniform(1_800_000, 3_200_000), 0)
        payg_w = round(random.uniform(850_000,   1_400_000), 0)
        rows.append((ob_id, "BAS", label, ps, pe, due, lodged,
                     gst + payg_w, status, "National",
                     f"GST: ${gst:,.0f} · PAYG Withholding: ${payg_w:,.0f} · Lodged via ATO Business Portal",
                     "ATO"))
        ob_id += 1

    # ── IAS monthly (large PAYG withholding — lodged monthly) ────────────────
    IAS_MONTHS = [
        ("January 2026",  "2026-01-01", "2026-01-31", "2026-02-21"),
        ("February 2026", "2026-02-01", "2026-02-28", "2026-03-21"),
        ("March 2026",    "2026-03-01", "2026-03-31", "2026-04-21"),  # due in 2 days
        ("April 2026",    "2026-04-01", "2026-04-30", "2026-05-21"),
        ("May 2026",      "2026-05-01", "2026-05-31", "2026-06-21"),
    ]
    for i, (label, ps, pe, due) in enumerate(IAS_MONTHS):
        # Deliberately flag Feb as overdue for demo interest
        force_ov = (label == "February 2026")
        status, lodged = _status(due, force_overdue=force_ov)
        amount = round(random.uniform(280_000, 520_000), 0)
        note   = "PAYG Withholding instalment — monthly lodger (annual withholding > $1M)"
        if force_ov:
            note += " · ⚠ Lodgement overdue — ATO late lodgement penalty may apply"
        rows.append((ob_id, "IAS", label, ps, pe, due, lodged,
                     amount, status, "National", note, "ATO"))
        ob_id += 1

    # ── Payroll tax by state (VIC, NSW, WA) ──────────────────────────────────
    STATE_BUDGETS = {
        "VIC": 185e6 + 310e6 + 420e6 + 560e6,   # 4 VIC projects — $1,475M
        "NSW": 98e6,
        "WA":  145e6,
    }
    WAGES_PCT = 0.22  # construction wages ~22% of project budget
    national_annual_wages = sum(STATE_BUDGETS.values()) * WAGES_PCT   # ~$377M

    def calc_vic_monthly_pt(monthly_vic_wages):
        """
        VIC payroll tax from 1 Jul 2025:
        - Deduction $1M annual, phases out at 50% between $3M–$5M annual wages; nil above $5M
        - Base rate 4.85%
        - Combined surcharge (mental health + COVID debt):
            1% if national payroll > $10M, 2% if > $100M
            applied to VIC wages above monthly surcharge threshold ($833,333)
        """
        annual_vic = monthly_vic_wages * 12
        if annual_vic <= 3_000_000:
            annual_deduction = 1_000_000
        elif annual_vic <= 5_000_000:
            annual_deduction = 1_000_000 - 0.50 * (annual_vic - 3_000_000)
        else:
            annual_deduction = 0
        monthly_deduction = annual_deduction / 12
        base_tax = max(0, monthly_vic_wages - monthly_deduction) * 0.0485

        if national_annual_wages > 100_000_000:
            surcharge_rate = 0.02
        elif national_annual_wages > 10_000_000:
            surcharge_rate = 0.01
        else:
            surcharge_rate = 0.0
        surcharge = max(0, monthly_vic_wages - 10_000_000 / 12) * surcharge_rate
        return round(base_tax + surcharge, 0), annual_deduction, surcharge_rate

    STATE_PT_OTHER = {
        "NSW": (1_200_000, 5.45, "Revenue NSW"),
        "WA":  (1_000_000, 5.50, "Revenue WA"),
    }

    PT_MONTHS = [
        ("March 2026", "2026-03-01", "2026-03-31", "2026-04-07"),
        ("April 2026", "2026-04-01", "2026-04-30", "2026-05-07"),
    ]
    for month_label, ps, pe, due in PT_MONTHS:
        # VIC — phase-out + surcharge
        vic_mw = round(STATE_BUDGETS["VIC"] * WAGES_PCT / 12, 0)
        liability, ann_ded, s_rate = calc_vic_monthly_pt(vic_mw)
        status, lodged = _status(due)
        ded_note = "nil (wages > $5M annual threshold)" if ann_ded == 0 else f"${ann_ded/12:,.0f}/month"
        surcharge_label = f"{s_rate*100:.0f}% combined surcharge (national payroll >${'100M' if s_rate == 0.02 else '10M'})"
        rows.append((ob_id, "Payroll Tax", month_label, ps, pe, due, lodged,
                     liability, status, "VIC",
                     f"Wages base (est.): ${vic_mw:,.0f} · Deduction: {ded_note} · "
                     f"Base rate: 4.85% · {surcharge_label} · Derived from payroll register extract",
                     "SRO Victoria"))
        ob_id += 1

        # NSW and WA — standard calculation
        for state, (annual_threshold, rate, authority) in STATE_PT_OTHER.items():
            monthly_wages     = round(STATE_BUDGETS[state] * WAGES_PCT / 12, 0)
            monthly_threshold = annual_threshold / 12
            liability         = round(max(0, (monthly_wages - monthly_threshold) * rate / 100), 0)
            status, lodged    = _status(due)
            rows.append((ob_id, "Payroll Tax", month_label, ps, pe, due, lodged,
                         liability, status, state,
                         f"Wages base (est.): ${monthly_wages:,.0f} · Monthly threshold: ${monthly_threshold:,.0f} "
                         f"· Rate: {rate}% · Derived from payroll register extract",
                         authority))
            ob_id += 1

    # ── Superannuation SG (12.0% from 1 Jul 2025) ────────────────────────────
    total_annual_wages  = sum(STATE_BUDGETS.values()) * WAGES_PCT
    quarterly_wages     = total_annual_wages / 4
    SG_RATE             = 0.120   # 12.0% SG rate FY2025-26

    SUPER_QUARTERS = [
        ("Q3 FY2026 (Jan–Mar)", "2026-01-01", "2026-03-31", "2026-04-28"),
        ("Q4 FY2026 (Apr–Jun)", "2026-04-01", "2026-06-30", "2026-07-28"),
    ]
    for label, ps, pe, due in SUPER_QUARTERS:
        amount = round(quarterly_wages * SG_RATE * random.uniform(0.93, 1.07), 0)
        status, lodged = _status(due)
        rows.append((ob_id, "Superannuation SG", label, ps, pe, due, lodged,
                     amount, status, "National",
                     f"SG rate: 12.0% (FY25-26) · Paid via SuperStream · "
                     f"Funds: REST / AustralianSuper / Hostplus · Derived from payroll register extract",
                     "ATO / SuperStream"))
        ob_id += 1

    headers = [
        "obligation_id", "obligation_type", "period_label",
        "period_start", "period_end", "due_date", "lodged_date",
        "amount_aud", "status", "state", "notes", "authority",
    ]
    write_csv("statutory_compliance.csv", headers, rows)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating finance data for: {COMPANY}\n")
    gen_projects()
    gen_expenses_and_ledger()
    gen_forecasts()
    gen_audit()
    gen_bank_facilities()
    gen_weekly_cashflow()
    gen_bank_accounts()
    gen_sap_legacy_extract()
    gen_statutory_compliance()
    print(f"\nDone. Files saved to: {OUTPUT_DIR.resolve()}")
    print("Run `streamlit run app.py` to launch the dashboard.")
