"""
SiteCapital — Construction Treasury Intelligence Platform
Enterprise-grade CFO dashboard — UX-focused, psychologically framed.
"""

import datetime
import random
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pandas as pd
import streamlit as st

DATA_DIR = Path("data")
random.seed(99)

# Auto-generate data if missing (Streamlit Cloud cold start)
if not (DATA_DIR / "projects.csv").exists():
    DATA_DIR.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "generate_csv.py"], check=True)

# ── Design tokens ─────────────────────────────────────────────────────────────
BLUE      = "#1A5C3A"   # forest green — primary
BLUE_MID  = "#8DC63F"   # lime accent
CHARCOAL  = "#222222"   # near-black
GREY      = "#555555"
GREY_LIGHT= "#D8D8D8"   # light grey for chart grid lines
WHITE     = "#FFFFFF"
BG        = "#F5F5F5"
GREEN     = "#1A5C3A"
AMBER     = "#CA6F1E"
RED       = "#C0392B"

st.set_page_config(
    page_title="SiteCapital | Treasury Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Theme toggle (must be before sidebar renders) ─────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

DARK = st.session_state.dark_mode

# Dynamic theme values
PAGE_BG    = "#121212" if DARK else "#F5F5F5"
CARD_BG    = "#1E1E1E" if DARK else "#FFFFFF"
TEXT_MAIN  = "#EEEEEE" if DARK else "#222222"
TEXT_SUB   = "#AAAAAA" if DARK else "#555555"
CHART_GRID = "#333333" if DARK else "#D8D8D8"
CHART_SPINE= "#444444" if DARK else "#D8D8D8"

st.markdown(f"""
<style>
/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: #1A5C3A !important;
}}
[data-testid="stSidebar"] * {{
    color: #FFFFFF !important;
}}
/* Input fields inside sidebar */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="input"] *,
[data-testid="stSidebar"] [data-testid="stDateInput"] input,
[data-testid="stSidebar"] [role="listbox"] * {{
    color: #222222 !important;
}}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio div,
[data-testid="stSidebar"] .stRadio span,
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] p,
[data-testid="stSidebar"] [data-baseweb="radio"] label,
[data-testid="stSidebar"] [data-baseweb="radio"] div,
[data-testid="stSidebar"] [data-baseweb="radio"] span {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
    color: #FFFFFF !important;
}}
/* File uploader: label white, dropzone interior dark (white card bg) */
[data-testid="stSidebar"] [data-testid="stFileUploader"] label {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{
    color: #222222 !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.2) !important;
}}
[data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] ~ div {{
    color: #8DC63F !important;
    font-weight: 700;
}}
/* Page background */
.stApp {{
    background-color: {PAGE_BG} !important;
}}
/* Main content text */
.stApp p, .stApp li, .stApp span, .stApp label,
[data-testid="stMarkdownContainer"] p {{
    color: {TEXT_MAIN} !important;
}}
/* Headings */
h1, h2, h3, h4 {{
    color: #1A5C3A !important;
}}
/* Metric cards — fixed height equalises all cards regardless of delta */
div[data-testid="metric-container"],
[data-testid="stMetric"] {{
    background-color: {CARD_BG} !important;
    border-radius: 8px;
    padding: 14px 18px !important;
    border-left: 4px solid #8DC63F !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    height: 116px !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}}
div[data-testid="metric-container"] label,
div[data-testid="metric-container"] div,
[data-testid="stMetric"] label,
[data-testid="stMetric"] div {{
    color: {TEXT_MAIN} !important;
}}
/* Dataframes */
[data-testid="stDataFrame"] {{
    background-color: {CARD_BG} !important;
}}
/* Info/warning boxes */
[data-testid="stAlert"] {{
    background-color: {CARD_BG} !important;
    color: {TEXT_MAIN} !important;
}}
/* Expanders */
[data-testid="stExpander"] {{
    background-color: {CARD_BG} !important;
}}
[data-testid="stExpander"] summary span {{
    color: {TEXT_MAIN} !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(v):      return f"${v:,.0f}"
def fmt_m(v):    return f"${v/1e6:,.1f}M"
def fmt_pct(v):  return f"{v:.2f}%" if isinstance(v, (int, float)) and not pd.isna(v) else ""
def to_csv_bytes(df): return df.to_csv(index=False).encode()

def fmt_pct_col(df, cols):
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(fmt_pct)
    return df

def _dollar(v):
    if not isinstance(v, (int, float)) or pd.isna(v):
        return "" if pd.isna(v) else str(v)
    return f"(${abs(v):,.0f})" if v < 0 else f"${v:,.0f}"

def _neg_red(v):
    return "color: #C0392B; font-weight:600" if isinstance(v, (int, float)) and v < 0 else ""

def style_dollars(df, cols):
    return (
        df.style
        .format({c: _dollar for c in cols})
        .map(_neg_red, subset=cols)
    )

def load_csv(name, uploaded=None):
    if uploaded is not None:
        return pd.read_csv(uploaded)
    path = DATA_DIR / name
    if path.exists():
        return pd.read_csv(path)
    raise FileNotFoundError(f"Missing {path}. Run `python generate_csv.py` first.")

def page_header(title, subtitle=""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()

def exec_summary(text):
    text = text.replace("$", r"\$")
    st.info(f"**Executive Summary**\n\n{text}")

def status_icon(pct, lo=70, hi=85):
    if pct < lo:   return "🟢"
    if pct < hi:   return "🟡"
    return "🔴"

def style_ax(ax, title="", ylabel="", xlabel="", yticker=None):
    ax.set_facecolor(CARD_BG)
    ax.figure.patch.set_facecolor(PAGE_BG)
    for s in ["top","right"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(CHART_SPINE)
    ax.spines["bottom"].set_color(CHART_SPINE)
    ax.tick_params(labelsize=8, length=3, colors=TEXT_MAIN)
    ax.xaxis.label.set_color(TEXT_MAIN)
    ax.yaxis.label.set_color(TEXT_MAIN)
    ax.grid(axis="y", color=CHART_GRID, linewidth=0.7, linestyle="--")
    ax.set_axisbelow(True)
    if title:  ax.set_title(title, fontsize=9.5, fontweight="600", pad=10, loc="left", color=TEXT_MAIN)
    if ylabel: ax.set_ylabel(ylabel, fontsize=8, color=TEXT_MAIN)
    if xlabel: ax.set_xlabel(xlabel, fontsize=8, color=TEXT_MAIN)
    if yticker: ax.yaxis.set_major_formatter(yticker)

def millions_fmt():
    return mticker.FuncFormatter(lambda v, _: f"${v:.0f}M")


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=0)
def load_all(p=None, e=None, l=None, f=None, a=None, fac=None, wcf=None, ba=None, sc=None, acc=None, ar=None, coa=None):
    projects   = load_csv("projects.csv",             p)
    expenses   = load_csv("site_expenses.csv",        e)
    ledger     = load_csv("sap_ledger.csv",           l)
    forecasts  = load_csv("cash_forecasts.csv",       f)
    audit      = load_csv("audit_log.csv",            a)
    facilities = load_csv("bank_facilities.csv",      fac)
    weekly_cf  = load_csv("weekly_cashflow.csv",      wcf)
    bank_accts = load_csv("bank_accounts.csv",        ba)
    statutory  = load_csv("statutory_compliance.csv", sc)
    try:
        coa_df = load_csv("chart_of_accounts.csv", coa)
    except FileNotFoundError:
        coa_df = pd.DataFrame(columns=["gl_account","account_name","account_type","account_group",
                                        "normal_balance","tax_code","bas_field","cost_center_required",
                                        "active","standard_ref","notes"])

    try:
        accruals = load_csv("accruals.csv", acc)
    except FileNotFoundError:
        accruals = pd.DataFrame(columns=["accrual_id","project_id","sap_cost_center","accrual_date",
                                          "period","expense_type","gl_account","amount","tax_code",
                                          "gst_amount","description","vendor","status","reversal_date"])
    try:
        ar_inv = load_csv("ar_invoices.csv", ar)
    except FileNotFoundError:
        ar_inv = pd.DataFrame(columns=["ar_id","project_id","sap_cost_center","gl_account",
                                        "claim_number","claim_type","claim_date","description",
                                        "claim_amount","retention_withheld","net_claim","gst_amount",
                                        "total_incl_gst","due_date","paid_date","paid_amount",
                                        "outstanding","status"])

    expenses["booking_date"]   = pd.to_datetime(expenses["booking_date"])
    ledger["posting_date"]     = pd.to_datetime(ledger["posting_date"])
    forecasts["forecast_date"] = pd.to_datetime(forecasts["forecast_date"])
    audit["event_date"]        = pd.to_datetime(audit["event_date"])
    weekly_cf["week_start"]    = pd.to_datetime(weekly_cf["week_start"])
    if "project_id" in weekly_cf.columns:
        weekly_cf["project_id"] = pd.to_numeric(weekly_cf["project_id"], errors="coerce").fillna(0).astype(int)
    else:
        weekly_cf["project_id"] = 0
    bank_accts["date"]         = pd.to_datetime(bank_accts["date"])
    if "project_id" in bank_accts.columns:
        bank_accts["project_id"] = pd.to_numeric(bank_accts["project_id"], errors="coerce").fillna(0).astype(int)
    else:
        bank_accts["project_id"] = 0
    statutory["due_date"]      = pd.to_datetime(statutory["due_date"])
    if not accruals.empty:
        accruals["accrual_date"] = pd.to_datetime(accruals["accrual_date"])
        accruals["amount"]       = pd.to_numeric(accruals["amount"], errors="coerce").fillna(0)
        accruals["gst_amount"]   = pd.to_numeric(accruals["gst_amount"], errors="coerce").fillna(0)
    if not ar_inv.empty:
        ar_inv["claim_date"] = pd.to_datetime(ar_inv["claim_date"])
        ar_inv["due_date"]   = pd.to_datetime(ar_inv["due_date"])
        for _c in ("claim_amount","retention_withheld","net_claim","gst_amount",
                   "total_incl_gst","paid_amount","outstanding"):
            ar_inv[_c] = pd.to_numeric(ar_inv[_c], errors="coerce").fillna(0)

    for col in ("contract_value", "eac", "dso_days", "retention_rate"):
        if col in projects.columns:
            projects[col] = pd.to_numeric(projects[col], errors="coerce")

    return projects, expenses, ledger, forecasts, audit, facilities, weekly_cf, bank_accts, statutory, accruals, ar_inv, coa_df


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### SiteCapital")
    st.caption("Construction Treasury Intelligence · Melbourne HQ")
    st.divider()

    dark_toggle = st.toggle("Dark Mode", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.divider()

    page = st.radio("Navigation", [
        "Daily Cash Position",
        "Cash Flow & Covenant",
        "Payments & Vendor Risk",
        "Reconciliation Control",
        "Statutory Compliance",
        "Audit & Controls",
        "Portfolio Health",
        "SAP Integration",
        "Board Summary",
        "Revenue & POC",
        "AR & Collections",
        "Retention Register",
        "WIP Report",
        "Chart of Accounts",
        "Data Management",
    ], index=0)

    st.divider()
    with st.expander("Upload Data Sources"):
        p_up   = st.file_uploader("projects.csv",                     type="csv", key="p")
        e_up   = st.file_uploader("site_expenses.csv (Concur export)", type="csv", key="e")
        l_up   = st.file_uploader("sap_ledger.csv",                   type="csv", key="l")
        f_up   = st.file_uploader("cash_forecasts.csv",               type="csv", key="f")
        a_up   = st.file_uploader("audit_log.csv",                    type="csv", key="a")
        fac_up = st.file_uploader("bank_facilities.csv",              type="csv", key="fac")
        wcf_up = st.file_uploader("weekly_cashflow.csv",              type="csv", key="wcf")
        ba_up  = st.file_uploader("bank_accounts.csv",                type="csv", key="ba")
        sc_up  = st.file_uploader("statutory_compliance.csv",         type="csv", key="sc")
        acc_up = st.file_uploader("accruals.csv",                     type="csv", key="acc")
        ar_up  = st.file_uploader("ar_invoices.csv",                  type="csv", key="ar")
        coa_up = st.file_uploader("chart_of_accounts.csv",            type="csv", key="coa")

try:
    projects, expenses, ledger, forecasts, audit, facilities, weekly_cf, bank_accts, statutory, accruals, ar_inv, coa_df = load_all(
        p_up, e_up, l_up, f_up, a_up, fac_up, wcf_up, ba_up, sc_up, acc_up, ar_up, coa_up
    )
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.divider()
    pnames   = ["All Projects"] + projects["project_name"].tolist()
    selected = st.selectbox("Filter Project", pnames)

    all_dates   = pd.concat([expenses["booking_date"], ledger["posting_date"]])
    mn, mx      = all_dates.min().date(), all_dates.max().date()
    _today      = datetime.date.today()
    _default_to = min(mx, _today)

    def _parse_date(s, fallback):
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(s.strip(), fmt).date()
            except ValueError:
                pass
        return fallback

    _from_str = st.text_input("From (DD/MM/YYYY)", value=mn.strftime("%d/%m/%Y"), key="d_from")
    _to_str   = st.text_input("To (DD/MM/YYYY)",   value=_default_to.strftime("%d/%m/%Y"), key="d_to")
    d_from    = pd.Timestamp(_parse_date(_from_str, mn))
    d_to      = pd.Timestamp(_parse_date(_to_str, _default_to))
    if d_to < d_from:
        st.warning("'To' date is before 'From'.")
    st.caption("Treasury Operations · Confidential · Spend figures ex-GST · GST captured via ATO tax codes")

# ── Data templates (realistic system-export formats) ─────────────────────────

TEMPLATES = {
    "projects.csv": {
        "system": "SAP PS / Procore — Project Register Export",
        "path":   "SAP: PS → Project Builder → Export | Procore: Reports → Project List → CSV",
        "df": pd.DataFrame([
            {"project_id": 1, "project_name": "Collins Arch — Stage 2 Fit-Out",
             "client": "Lendlease Construction (Pty) Ltd", "start_date": "2026-01-05",
             "end_date": "2026-12-18", "project_budget": 185000000,
             "sap_cost_center": "CC-MEL-01", "sector": "Commercial",
             "state": "VIC", "location": "Melbourne CBD"},
            {"project_id": 2, "project_name": "Victorian Heart Hospital Ext.",
             "client": "Lendlease Construction (Pty) Ltd", "start_date": "2026-02-03",
             "end_date": "2027-06-30", "project_budget": 310000000,
             "sap_cost_center": "CC-MEL-02", "sector": "Healthcare",
             "state": "VIC", "location": "Clayton"},
        ]),
    },
    "site_expenses.csv": {
        "system": "AP Invoices — Trade Accounts & Concur Expense Export",
        "path":   "Subcontractors/Materials/Plant: Trade Account → AP module | Travel/Prof. Services: Concur → Reporting → Standard Reports → Expense Export → Download CSV",
        "df": pd.DataFrame([
            {"expense_id": "EXP-00001", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "booking_date": "2026-01-15", "expense_type": "Subcontractor", "amount": 125000.00,
             "sap_cost_code": "SAP-5001", "gl_account": "GL-6100",
             "vendor": "Kane Constructions", "status": "Approved", "comment": "",
             "source_system": "Trade Account", "tax_code": "G11", "gst_amount": 12500.00,
             "po_reference": "PO-2026-1042", "po_value": 131250.00, "contract_ref": "CTR-CC-MEL-01-01", "po_status": "Matched"},
            {"expense_id": "EXP-00002", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "booking_date": "2026-01-18", "expense_type": "Travel & Accommodation", "amount": 2340.00,
             "sap_cost_code": "SAP-5006", "gl_account": "GL-6600",
             "vendor": "Mantra on Little Bourke", "status": "Approved", "comment": "",
             "source_system": "Concur Export", "tax_code": "G11", "gst_amount": 234.00,
             "po_reference": "PO-2026-1043", "po_value": 2500.00, "contract_ref": "", "po_status": "Matched"},
            {"expense_id": "EXP-00003", "project_id": 2, "sap_cost_center": "CC-MEL-02",
             "booking_date": "2026-01-20", "expense_type": "Materials", "amount": 87500.00,
             "sap_cost_code": "SAP-5002", "gl_account": "GL-6200",
             "vendor": "Boral Construction Materials", "status": "Pending",
             "comment": "Awaiting delivery confirmation", "source_system": "Trade Account",
             "tax_code": "G11", "gst_amount": 8750.00,
             "po_reference": "PO-2026-1044", "po_value": 90000.00, "contract_ref": "", "po_status": "Matched"},
            {"expense_id": "EXP-00004", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "booking_date": "2026-01-22", "expense_type": "Permits & Compliance", "amount": 8500.00,
             "sap_cost_code": "SAP-5005", "gl_account": "GL-6500",
             "vendor": "WorkSafe Victoria", "status": "Approved",
             "comment": "Government fee — GST-free", "source_system": "Manual Entry",
             "tax_code": "G12", "gst_amount": 0.00,
             "po_reference": "", "po_value": 0.00, "contract_ref": "", "po_status": "No PO"},
        ]),
    },
    "sap_ledger.csv": {
        "system": "SAP S/4HANA — FBL3N GL Line Item Report",
        "path":   "SAP: FBL3N → GL Account → Execute → List → Export Spreadsheet (include Cost Center, Tax Code & Tax Amount columns)",
        "df": pd.DataFrame([
            {"ledger_id": "1000000001", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "posting_date": "2026-01-15", "gl_account": "GL-6100", "amount": 125000.00, "doc_type": "RE",
             "description": "Subcontractor invoice — Kane Constructions Jan",
             "vendor": "Kane Constructions", "tax_code": "G11", "gst_amount": 12500.00},
            {"ledger_id": "1000000002", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "posting_date": "2026-01-18", "gl_account": "GL-6600", "amount": 2340.00, "doc_type": "KR",
             "description": "T&A — Mantra on Little Bourke",
             "vendor": "Mantra on Little Bourke", "tax_code": "G11", "gst_amount": 234.00},
            {"ledger_id": "1000000003", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "posting_date": "2026-01-20", "gl_account": "GL-6500", "amount": 8500.00, "doc_type": "KR",
             "description": "WorkSafe permit fee — Collins Arch",
             "vendor": "WorkSafe Victoria", "tax_code": "G12", "gst_amount": 0.00},
            {"ledger_id": "1000000004", "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "posting_date": "2026-02-01", "gl_account": "GL-4100", "amount": 18500000.00, "doc_type": "RV",
             "description": "Progress Claim #3 — Collins Arch Stage 2",
             "vendor": "Lendlease Construction (Pty) Ltd", "tax_code": "G1", "gst_amount": 1850000.00},
        ]),
    },
    "cash_forecasts.csv": {
        "system": "Treasury Management System / Excel Cash Forecast",
        "path":   "TMS: Reports → Cash Forecast → Export CSV | or export from approved Excel template",
        "df": pd.DataFrame([
            {"forecast_id": 1, "project_id": 1, "forecast_date": "2026-04-21",
             "expected_cash_in": 4200000.00, "expected_cash_out": 6800000.00,
             "payment_schedule": "Standard", "site_progress_pct": 42.0},
            {"forecast_id": 2, "project_id": 2, "forecast_date": "2026-04-28",
             "expected_cash_in": 7100000.00, "expected_cash_out": 9300000.00,
             "payment_schedule": "Accelerated", "site_progress_pct": 31.5},
        ]),
    },
    "audit_log.csv": {
        "system": "Audit Management System / Internal Controls Register",
        "path":   "Risk & Audit system → Issue Register → Export to CSV",
        "df": pd.DataFrame([
            {"audit_id": "AUD-001", "event_date": "2026-03-15", "project_id": 1,
             "module": "Accounts Payable", "issue_type": "Duplicate Invoice",
             "status": "Open",
             "notes": "Duplicate invoice detected for EXP-00045 — vendor Kane Constructions. Escalated to AP Manager."},
            {"audit_id": "AUD-002", "event_date": "2026-03-20", "project_id": 2,
             "module": "Bank Guarantee", "issue_type": "Bank Guarantee Expiry",
             "status": "Under Review",
             "notes": "BG-2024-089 expires 30 Jun 2026 — renewal in progress with ANZ."},
        ]),
    },
    "bank_facilities.csv": {
        "system": "ANZ Transactive / Westpac Online — Facility Summary Export",
        "path":   "Bank portal: Treasury → Facilities → Summary → Export CSV",
        "df": pd.DataFrame([
            {"facility_id": 1, "facility_name": "Revolving Credit Facility — ANZ",
             "bank": "ANZ", "facility_type": "Revolving Credit",
             "limit_aud": 250000000, "drawn_aud": 187500000,
             "covenant_min_cash_aud": 25000000, "covenant_max_gearing_pct": 55.0,
             "maturity_date": "2027-06-30", "next_review_date": "2026-09-30"},
            {"facility_id": 2, "facility_name": "Working Capital Facility — CBA",
             "bank": "CBA", "facility_type": "Working Capital",
             "limit_aud": 100000000, "drawn_aud": 62000000,
             "covenant_min_cash_aud": 25000000, "covenant_max_gearing_pct": 55.0,
             "maturity_date": "2026-12-31", "next_review_date": "2026-06-30"},
        ]),
    },
    "weekly_cashflow.csv": {
        "system": "Treasury Cashflow Report — Actual from Bank / Forecast from TMS",
        "path":   "Bank feeds (actual) + TMS forecast export → consolidated weekly summary",
        "df": pd.DataFrame([
            {"week_start": "2026-03-23", "cash_in": 18200000, "cash_out": 21400000,
             "net_movement": -3200000, "closing_balance": 31800000, "type": "Actual"},
            {"week_start": "2026-03-30", "cash_in": 22600000, "cash_out": 19800000,
             "net_movement": 2800000, "closing_balance": 34600000, "type": "Actual"},
            {"week_start": "2026-04-18", "cash_in": 15000000, "cash_out": 19000000,
             "net_movement": -4000000, "closing_balance": 29400000, "type": "Forecast"},
        ]),
    },
    "bank_accounts.csv": {
        "system": "ANZ Transactive / NAB Connect — Account Statement Export",
        "path":   "Bank portal: Accounts → Statement → Date range → Export CSV",
        "df": pd.DataFrame([
            {"account_id": "ANZ-001", "account_name": "ANZ Operating Account — VIC Projects",
             "bank": "ANZ", "bsb": "013-006", "account_type": "Operating",
             "date": "2026-04-18", "opening_balance": 12450000,
             "receipts": 3200000, "payments": 4100000, "closing_balance": 11550000},
            {"account_id": "CBA-001", "account_name": "CBA Payroll Trust Account",
             "bank": "CBA", "bsb": "062-000", "account_type": "Trust",
             "date": "2026-04-18", "opening_balance": 8900000,
             "receipts": 0, "payments": 2300000, "closing_balance": 6600000},
        ]),
    },
    "statutory_compliance.csv": {
        "system": "ATO Business Portal / Payroll System — Obligation Schedule",
        "path":   "ATO Business Portal: Activity Statements → Export | Payroll: Reports → Tax Obligations",
        "df": pd.DataFrame([
            {"obligation_id": "BAS-2026-Q1", "obligation_type": "BAS",
             "period_label": "Q3 FY2026 (Jan–Mar)", "period_start": "2026-01-01",
             "period_end": "2026-03-31", "due_date": "2026-04-28",
             "lodged_date": "", "amount_aud": 1250000, "status": "Pending",
             "state": "National", "notes": "GST collected $1.8M less GST paid $0.55M",
             "authority": "ATO"},
            {"obligation_id": "PT-VIC-MAR26", "obligation_type": "Payroll Tax",
             "period_label": "March 2026", "period_start": "2026-03-01",
             "period_end": "2026-03-31", "due_date": "2026-04-07",
             "lodged_date": "2026-04-05", "amount_aud": 187450, "status": "Lodged",
             "state": "VIC", "notes": "Rate 4.85% on VIC wages above monthly threshold $83,333",
             "authority": "State Revenue Office VIC"},
        ]),
    },
    "accruals.csv": {
        "system": "SAP S/4HANA — Manual Journal / Month-End Accruals Register",
        "path":   "SAP: FB50 → Recurring Entries → Accruals Journal | or Finance team accruals register export",
        "df": pd.DataFrame([
            {"accrual_id": 1, "project_id": 1, "sap_cost_center": "CC-MEL-01",
             "accrual_date": "2026-03-31", "period": "Mar-26",
             "expense_type": "Subcontractor", "gl_account": "GL-6100",
             "amount": 3500000.00, "tax_code": "G11", "gst_amount": 350000.00,
             "description": "Month-end accrual — subcontractor work completed, invoice pending",
             "vendor": "Hickory Group", "status": "Posted", "reversal_date": "2026-04-14"},
            {"accrual_id": 2, "project_id": 2, "sap_cost_center": "CC-MEL-02",
             "accrual_date": "2026-03-31", "period": "Mar-26",
             "expense_type": "Materials", "gl_account": "GL-6200",
             "amount": 5200000.00, "tax_code": "G11", "gst_amount": 520000.00,
             "description": "Month-end accrual — materials delivered, tax invoice in transit",
             "vendor": "Holcim Australia Pty Ltd", "status": "Posted", "reversal_date": "2026-04-10"},
        ]),
    },
    "ar_invoices.csv": {
        "system": "SAP S/4HANA FBL5N / Procore — AR Progress Claims",
        "path":   "SAP: FBL5N → Customer → Execute → Export | Procore: Billing → Export Progress Claims CSV",
        "df": pd.DataFrame([
            {"ar_id": 1, "project_id": 1, "sap_cost_center": "CC-MEL-01", "gl_account": "GL-4100",
             "claim_number": "PC-001", "claim_type": "Progress Claim",
             "claim_date": "2026-02-28", "description": "Progress Claim #1 — Collins Arch Stage 2 (February)",
             "claim_amount": 18525000.00, "retention_withheld": 926250.00, "net_claim": 17598750.00,
             "gst_amount": 1759875.00, "total_incl_gst": 19358625.00, "due_date": "2026-04-14",
             "paid_date": "2026-04-10", "paid_amount": 19358625.00, "outstanding": 0.00, "status": "Paid"},
            {"ar_id": 2, "project_id": 1, "sap_cost_center": "CC-MEL-01", "gl_account": "GL-4100",
             "claim_number": "PC-002", "claim_type": "Progress Claim",
             "claim_date": "2026-04-15", "description": "Progress Claim #2 — Collins Arch Stage 2 (April)",
             "claim_amount": 19500000.00, "retention_withheld": 975000.00, "net_claim": 18525000.00,
             "gst_amount": 1852500.00, "total_incl_gst": 20377500.00, "due_date": "2026-05-30",
             "paid_date": "", "paid_amount": 0.00, "outstanding": 20377500.00, "status": "Issued"},
        ]),
    },
}


# ── Filter helpers ────────────────────────────────────────────────────────────

proj_ids = (projects["project_id"].tolist() if selected == "All Projects"
            else projects.loc[projects["project_name"]==selected,"project_id"].tolist())

def fe(df): return df[df["project_id"].isin(proj_ids) & df["booking_date"].between(d_from, d_to)]
def fl(df): return df[df["project_id"].isin(proj_ids) & df["posting_date"].between(d_from, d_to)]
def ff(df): return df[df["project_id"].isin(proj_ids) & df["forecast_date"].between(d_from, d_to)]
def fa(df): return df[df["project_id"].isin(proj_ids)]
def fb(df): return df[(df["project_id"] == 0) | (df["project_id"].isin(proj_ids))]


# ── Natural language summary engine ──────────────────────────────────────────

def build_exec_summary(context="pulse"):
    actual_cf   = weekly_cf[weekly_cf["type"] == "Actual"]
    cash        = actual_cf["closing_balance"].iloc[-1] if not actual_cf.empty else 0
    headroom    = (facilities["limit_aud"] - facilities["drawn_aud"]).sum()
    open_audits = int((fa(audit)["status"] == "Open").sum())
    exp_f       = fe(expenses)
    spent_proj  = exp_f.groupby("project_id")["amount"].sum().reset_index(name="s")
    risk_df     = spent_proj.merge(projects[["project_id","project_name","project_budget"]], on="project_id")
    risk_df["pct"] = risk_df["s"] / risk_df["project_budget"] * 100
    at_risk     = risk_df[risk_df["pct"] > 85].sort_values("pct", ascending=False)
    breach_fac  = facilities[facilities["drawn_aud"] / facilities["limit_aud"] > 0.85]
    avg_net     = actual_cf["net_movement"].mean() if not actual_cf.empty else 0

    s = []
    if context == "pulse":
        s.append(f"Cash position is {'**stable**' if cash >= 40e6 else '**under monitoring**'} at {fmt_m(cash)}, "
                 f"with {fmt_m(headroom)} undrawn across all banking facilities.")
        if not at_risk.empty:
            top = at_risk.iloc[0]
            s.append(f"**{len(at_risk)} project(s) above 85% budget utilisation** — "
                     f"{top['project_name']} is highest at {top['pct']:.0f}%. CFO sign-off recommended.")
        else:
            s.append("All projects are tracking within approved budget parameters.")
        cov = f" {len(breach_fac)} facility(ies) above 85% utilisation — treasury review required." if not breach_fac.empty else ""
        s.append(f"**{open_audits} open audit item(s)** require action across the portfolio.{cov}")

    elif context == "recon":
        _COST_GL = ["GL-6100","GL-6200","GL-6300","GL-6400","GL-6500","GL-6600"]
        exp_t = exp_f["amount"].sum()
        led_t = fl(ledger)[fl(ledger)["gl_account"].isin(_COST_GL)]["amount"].sum()
        var   = abs(exp_t - led_t)
        vp    = var / max(exp_t, 1) * 100
        s.append(f"Site expenses total {fmt_m(exp_t)} against SAP ledger postings of {fmt_m(led_t)} — "
                 f"gross variance {fmt_m(var)} ({vp:.1f}%). "
                 f"{'Within acceptable tolerance.' if vp < 2 else 'Exceeds 2% materiality threshold — reconciliation sign-off required.'}")
        fl_n = len(exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")])
        if fl_n > 0:
            s.append(f"**{fl_n} flagged line(s)** — WBS mismatches and coding errors to clear before month-end.")

    elif context == "covenant":
        min_cov = facilities["covenant_min_cash_aud"].max()
        gap     = cash - min_cov
        if not breach_fac.empty:
            s.append(f"**Covenant attention required.** {len(breach_fac)} facility(ies) above 85% utilisation.")
        else:
            s.append(f"All facilities within covenant compliance. {fmt_m(gap)} above the minimum cash covenant floor of {fmt_m(min_cov)}.")
        if avg_net < 0:
            weeks = max(gap / abs(avg_net), 0)
            # Only flag imminent breach: headroom covers fewer than 4 weeks of avg burn
            if gap < abs(avg_net) * 4:
                s.append(f"Average weekly net cash: {fmt_m(avg_net)} (outflow). Covenant floor reached in ~**{weeks:.0f} weeks** at current rate.")
            else:
                s.append(f"Weekly net cash: {fmt_m(avg_net)}/week (outflow). Covenant floor projected in ~{weeks:.0f} weeks — no near-term breach risk.")
        else:
            s.append(f"Weekly cash flow is **net positive** at {fmt_m(avg_net)}/week — no near-term breach risk.")

    elif context == "vendor":
        top_v = exp_f.groupby("vendor")["amount"].sum().sort_values(ascending=False)
        conc  = top_v.head(3).sum() / max(top_v.sum(), 1) * 100
        fv    = exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")]["vendor"].nunique()
        s.append(f"Vendor spend across **{exp_f['vendor'].nunique()} suppliers** totals {fmt_m(exp_f['amount'].sum())}. "
                 f"Top-3 vendors account for **{conc:.0f}%** of spend — "
                 f"{'within acceptable limits.' if conc < 60 else 'review against procurement policy.'}")
        if fv > 0:
            s.append(f"**{fv} vendor(s) carry flagged transactions** — AP review recommended before next payment run.")

    elif context == "audit":
        on = int((fa(audit)["status"] == "Open").sum())
        rv = int((fa(audit)["status"] == "Under Review").sum())
        bg = int((fa(audit)["issue_type"] == "Bank Guarantee Expiry").sum())
        s.append(f"**{on} open** and **{rv} under-review** items across the portfolio.")
        if bg > 0:
            s.append(f"**{bg} bank guarantee renewal(s) outstanding** — failure to renew constitutes contract breach. Escalate to Treasury immediately.")

    return "  \n".join(s)


# ── Smart alerts engine ───────────────────────────────────────────────────────

def generate_alerts(exp, fcast, fac, wcf):
    alerts = []
    actual = wcf[wcf["type"] == "Actual"]
    if not actual.empty:
        closing = actual.iloc[-1]["closing_balance"]
        min_cov = fac["covenant_min_cash_aud"].max()
        if closing < min_cov:
            alerts.append(("CRITICAL", f"Cash {fmt_m(closing)} is BELOW covenant threshold {fmt_m(min_cov)}"))
        elif closing < min_cov * 1.25:
            alerts.append(("WARNING", f"Cash buffer narrowing — only {fmt_m(closing - min_cov)} above covenant floor"))

    fc = fcast.copy()
    if "expected_cash_in" in fc.columns and "expected_cash_out" in fc.columns:
        fc["net"] = fc["expected_cash_in"] - fc["expected_cash_out"]
        neg = fc[fc["net"] < 0]
        if not neg.empty:
            alerts.append(("WARNING", f"{len(neg)} forecast period(s) show negative net cash flow"))

    overdue = exp[
        (exp["status"] == "Pending") &
        (exp["booking_date"] < pd.Timestamp.today() - pd.Timedelta(days=7))
    ]
    if not overdue.empty:
        alerts.append(("WARNING", f"{len(overdue)} supplier payment(s) pending >7 days — AP review required"))

    return alerts

def show_alerts(alerts):
    if not alerts:
        st.markdown("<div style='padding:8px 14px;border-radius:6px;background:#EAF3DE;border:0.5px solid #97C459;font-size:13px;color:#27500A;margin-bottom:12px;'>Treasury position stable — no active alerts.</div>", unsafe_allow_html=True)
        return
    crits = [m for l,m in alerts if l=="CRITICAL"]
    warns = [m for l,m in alerts if l=="WARNING"]
    if crits:
        st.markdown(f"<div style='padding:8px 14px;border-radius:6px;background:#FCEBEB;border:0.5px solid #F09595;font-size:13px;color:#A32D2D;margin-bottom:6px;'>&#9679; {'  ·  '.join(crits)}</div>", unsafe_allow_html=True)
    if warns:
        st.markdown(f"<div style='padding:8px 14px;border-radius:6px;background:#FAEEDA;border:0.5px solid #EF9F27;font-size:13px;color:#854F0B;margin-bottom:6px;'>&#9651; {'  ·  '.join(warns)}</div>", unsafe_allow_html=True)


# ── Scenario simulation engine ────────────────────────────────────────────────

def simulate_spend_scenarios(fcast, wcf, fac, scenarios=(0.0, 0.05, 0.10, 0.20)):
    actual = wcf[wcf["type"] == "Actual"]
    if actual.empty or "expected_cash_in" not in fcast.columns:
        return None
    start_cash = actual.iloc[-1]["closing_balance"]
    covenant   = fac["covenant_min_cash_aud"].max()

    # Aggregate to portfolio-level monthly net (sum across all projects per date),
    # then cap to next 12 periods so cumulative outflows don't compound unrealistically.
    agg = (fcast.copy()
           .sort_values("forecast_date")
           .groupby("forecast_date", as_index=False)
           .agg(expected_cash_in=("expected_cash_in", "sum"),
                expected_cash_out=("expected_cash_out", "sum"))
           .head(12))

    results = []
    for scn in scenarios:
        df = agg.copy()
        df["adj_out"] = df["expected_cash_out"] * (1 + scn)
        df["net"]     = df["expected_cash_in"] - df["adj_out"]
        cash, balances = start_cash, []
        for _, row in df.iterrows():
            cash = max(cash + row["net"], covenant)
            balances.append(cash)
        df["balance"] = balances
        breach = next((i + 1 for i, v in enumerate(balances) if v <= covenant), None)
        results.append({
            "scenario":    f"+{int(scn * 100)}%",
            "final_cash":  balances[-1],
            "breach":      breach is not None,
            "breach_week": breach or "Safe",
            "runway":      breach or len(balances),
            "df":          df,
        })
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — EXECUTIVE PULSE
# ══════════════════════════════════════════════════════════════════════════════

if page == "Daily Cash Position":
    _ba_f        = fb(bank_accts)
    _today_label = _ba_f["date"].max().strftime("%d %B %Y") if not _ba_f.empty else bank_accts["date"].max().strftime("%d %B %Y")
    page_header("Daily Cash Position", f"Live treasury snapshot · Bank balances · Liquidity monitoring · {_today_label}")

    show_alerts(generate_alerts(fe(expenses), ff(forecasts), facilities, weekly_cf))
    if selected != "All Projects":
        st.info(f"Showing: project drawdown accounts + group accounts for **{selected}**")
    st.divider()

    latest_date = _ba_f["date"].max() if not _ba_f.empty else bank_accts["date"].max()
    today_str   = latest_date.strftime("%Y-%m-%d")
    today_accts = _ba_f[_ba_f["date"] == latest_date].copy()
    actual_cf   = weekly_cf[weekly_cf["type"] == "Actual"]

    if not today_accts.empty:
        t_open  = today_accts["opening_balance"].sum()
        t_in    = today_accts["receipts"].sum()
        t_out   = today_accts["payments"].sum()
        t_close = today_accts["closing_balance"].sum()
    elif not actual_cf.empty:
        latest = actual_cf.iloc[-1]
        t_in    = latest["cash_in"]
        t_out   = latest["cash_out"]
        t_close = latest["closing_balance"]
        t_open  = t_close - latest["net_movement"]
    else:
        t_open = t_in = t_out = t_close = 0

    headroom = (facilities["limit_aud"] - facilities["drawn_aud"]).sum()
    min_cov  = facilities["covenant_min_cash_aud"].max()
    net_day  = t_in - t_out

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Opening Balance",   fmt_m(t_open),  delta="Today's start")
    c2.metric("Cash In",           fmt_m(t_in),    delta="Receipts today")
    c3.metric("Cash Out",          fmt_m(t_out),   delta=round(t_out / 1e6, 1),  delta_color="inverse" if t_out > 0 else "off")
    c4.metric("Closing Balance",   fmt_m(t_close), delta=round(net_day / 1e6, 1),
              delta_color="normal")
    c5.metric("Facility Headroom", fmt_m(headroom), delta="vs covenant min")

    st.divider()
    st.markdown(f"#### Bank Account Positions — {_today_label}")
    if not today_accts.empty:
        _ba_cols = ["account_name","bank","account_type"]
        if "sap_cost_center" in today_accts.columns:
            _ba_cols.append("sap_cost_center")
        _ba_cols += ["opening_balance","receipts","payments","closing_balance"]
        disp_b = today_accts[_ba_cols].copy()
        _col_names = ["Account","Bank","Type"]
        if "sap_cost_center" in today_accts.columns:
            _col_names.append("Cost Centre")
        _col_names += ["Opening","Cash In","Cash Out","Closing"]
        disp_b.columns = _col_names
        for _c in ["Opening","Cash In","Cash Out","Closing"]:
            if _c in disp_b.columns:
                disp_b[_c] = disp_b[_c].apply(lambda v: fmt_m(v) if isinstance(v,(int,float)) else v)
        st.dataframe(disp_b.set_index("Account"), use_container_width=True)
    else:
        st.info("No daily account data for today.")

    st.divider()
    st.markdown("#### 7-Week Cash Balance Trend")
    # Use raw weekly_cf directly — never filtered by sidebar date range.
    _wcf_sorted = weekly_cf.sort_values("week_start").reset_index(drop=True)
    _trend_act  = _wcf_sorted[_wcf_sorted["type"] == "Actual"].tail(4).reset_index(drop=True)
    _trend_fcst = _wcf_sorted[_wcf_sorted["type"] == "Forecast"].head(3).reset_index(drop=True)
    if not _trend_act.empty:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        ax.fill_between(_trend_act["week_start"], _trend_act["closing_balance"] / 1e6,
                        alpha=0.12, color=BLUE)
        ax.plot(_trend_act["week_start"], _trend_act["closing_balance"] / 1e6,
                color=BLUE, lw=2.2, marker="o", ms=5, label="Actual")
        if not _trend_fcst.empty:
            # Bridge: last actual → first forecast for visual continuity
            _bridge = pd.concat([_trend_act.tail(1), _trend_fcst]).reset_index(drop=True)
            ax.plot(_bridge["week_start"], _bridge["closing_balance"] / 1e6,
                    color=BLUE, lw=1.8, marker="o", ms=4, linestyle="--", alpha=0.85, label="Forecast")
        ax.axhline(min_cov / 1e6, color=RED, lw=1.3, linestyle="--",
                   label=f"Covenant Floor {fmt_m(min_cov)}")
        style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
        ax.legend(fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        plt.xticks(rotation=20, ha="right", fontsize=7.5)
        plt.tight_layout(pad=1.2)
        st.pyplot(fig, use_container_width=True)
        plt.close()


elif page == "Board Summary":
    page_header("Board Summary", "CFO view — consolidated group position · 18 April 2026 · All figures ex-GST")
    exec_summary(build_exec_summary("pulse"))

    _proj_f      = projects[projects["project_id"].isin(proj_ids)]
    _exp_f       = fe(expenses)
    total_budget = _proj_f["project_budget"].sum()
    total_spent  = _exp_f["amount"].sum()
    headroom     = (facilities["limit_aud"] - facilities["drawn_aud"]).sum()
    open_audits  = int((fa(audit)["status"] == "Open").sum())
    actual_cf    = weekly_cf[weekly_cf["type"] == "Actual"]
    cash         = actual_cf["closing_balance"].iloc[-1] if not actual_cf.empty else 0
    spent_pct    = total_spent / max(total_budget, 1) * 100
    proj_risk    = int(len(
        _exp_f.groupby("project_id")["amount"].sum().reset_index(name="s")
        .merge(_proj_f[["project_id","project_budget"]], on="project_id")
        .query("s / project_budget > 0.85")
    ))

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Portfolio Budget",   fmt_m(total_budget))
    c2.metric("Committed Spend",    fmt_m(total_spent),   delta=f"{spent_pct:.1f}% utilised")
    c3.metric("Cash Balance",       fmt_m(cash),           delta="Confirmed 11 Apr")
    c4.metric("Facility Headroom",  fmt_m(headroom),       delta="5 facilities")
    c5.metric("Open Audit Items",   str(open_audits),      delta="Require action",  delta_color="inverse")
    c6.metric("Projects at Risk",   str(proj_risk),        delta=">85% utilised",   delta_color="inverse")

    st.divider()

    # 8-week cash burn chart
    st.markdown("#### 8-Week Rolling Cash Burn")
    st.caption("Actual (solid) · Forecast (translucent) · Covenant floor (red dashed)")

    actual_w   = weekly_cf[weekly_cf["type"] == "Actual"].copy()
    forecast_w = weekly_cf[weekly_cf["type"] == "Forecast"].copy()
    n_act = len(actual_w)
    x_a   = list(range(n_act))
    x_f   = list(range(n_act - 1, n_act - 1 + len(forecast_w)))

    fig, ax1 = plt.subplots(figsize=(11, 4))
    ax1.bar([i-0.2 for i in x_a], actual_w["cash_in"]   /1e6, 0.38, color=BLUE,  alpha=0.9,  label="Cash In (Actual)")
    ax1.bar([i+0.2 for i in x_a], actual_w["cash_out"]  /1e6, 0.38, color=AMBER, alpha=0.9,  label="Cash Out (Actual)")
    ax1.bar([i-0.2 for i in x_f], forecast_w["cash_in"] /1e6, 0.38, color=BLUE,  alpha=0.3,  label="Cash In (Fcst)")
    ax1.bar([i+0.2 for i in x_f], forecast_w["cash_out"]/1e6, 0.38, color=AMBER, alpha=0.3,  label="Cash Out (Fcst)")
    all_x  = x_a + x_f
    labels = pd.concat([actual_w["week_start"], forecast_w["week_start"]]).dt.strftime("%d %b")
    ax1.set_xticks(all_x)
    ax1.set_xticklabels(labels, rotation=30, ha="right", fontsize=7.5)
    style_ax(ax1, ylabel="AUD (M)", yticker=millions_fmt())
    ax1.legend(fontsize=7.5, ncol=4, loc="upper left")
    ax2 = ax1.twinx()
    bal = list(actual_w["closing_balance"]) + list(forecast_w["closing_balance"])
    ax2.plot(all_x[:n_act], [v/1e6 for v in actual_w["closing_balance"]], color=CHARCOAL, lw=2, marker="o", ms=4)
    ax2.plot(all_x[n_act-1:], [v/1e6 for v in [actual_w["closing_balance"].iloc[-1]] + list(forecast_w["closing_balance"])],
             color=CHARCOAL, lw=1.5, marker="o", ms=3, linestyle="--", label="Closing Balance")
    min_cov = facilities["covenant_min_cash_aud"].max()/1e6
    ax2.axhline(min_cov, color=RED, lw=1.3, linestyle=":", label=f"Covenant Floor {fmt_m(min_cov*1e6)}")
    ax2.set_ylabel("Balance (AUD M)", fontsize=8, color=GREY)
    ax2.tick_params(colors=GREY, labelsize=8)
    ax2.spines["top"].set_visible(False)
    ax2.legend(fontsize=7.5, loc="upper right")
    ax1.axvline(n_act-0.5, color=GREY_LIGHT, lw=1.5, linestyle="--")
    ax1.text(n_act-0.3, ax1.get_ylim()[1]*0.9, "Today →", fontsize=7, color=GREY)
    plt.tight_layout(pad=1.2)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    st.divider()
    st.markdown("#### Banking Facility Utilisation")
    for _, row in facilities.iterrows():
        pct   = row["drawn_aud"] / row["limit_aud"]
        icon  = "🟢" if pct < 0.65 else ("🟡" if pct < 0.85 else "🔴")
        label = "Compliant" if pct < 0.65 else ("Monitor" if pct < 0.85 else "⚠ Breach Risk")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"{icon} **{row['facility_name']}** — {row['bank']} · Matures {row['maturity_date']}")
            st.progress(float(pct), text=f"{pct*100:.1f}% drawn · Headroom {fmt(row['limit_aud']-row['drawn_aud'])}")
        with col2:
            st.markdown(f"`{label}`")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — PORTFOLIO HEALTH
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Portfolio Health":
    page_header("Portfolio Health", "Budget utilisation, spend tracking, and exception flags · All figures ex-GST")

    exp_f = fe(expenses)
    spent = exp_f.groupby("project_id")["amount"].sum().reset_index(name="spent")
    df    = projects[projects["project_id"].isin(proj_ids)].merge(spent, on="project_id", how="left")
    df["spent"]     = df["spent"].fillna(0)
    df["remaining"] = df["project_budget"] - df["spent"]
    df["pct"]       = df["spent"] / df["project_budget"] * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Projects",   str(len(df)))
    c2.metric("Total Portfolio",   fmt_m(df["project_budget"].sum()))
    c3.metric("Total Committed",   fmt_m(df["spent"].sum()))
    c4.metric("Total Remaining",   fmt_m(df["remaining"].sum()))
    c5.metric("Over 85% Utilised", str(int((df["pct"] > 85).sum())), delta_color="inverse",
              delta="⚠ Action required" if (df["pct"] > 85).sum() > 0 else "✓ All clear")

    st.divider()
    for _, row in df.sort_values("pct", ascending=False).iterrows():
        pct  = row["pct"]
        icon = status_icon(pct)
        with st.expander(f"{icon} {row['project_name']} — {row.get('sector','')} · {row.get('location','')}"):
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Budget",    fmt_m(row["project_budget"]))
            cc2.metric("Committed", fmt_m(row["spent"]))
            cc3.metric("Remaining", fmt_m(row["remaining"]))
            cc4.metric("Utilised",  f"{pct:.1f}%")
            st.progress(min(pct/100, 1.0), text=f"SAP Cost Centre: {row['sap_cost_center']} · {row['start_date']} → {row['end_date']}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Budget vs Committed")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        x = range(len(df))
        ax.bar([i-0.2 for i in x], df["project_budget"]/1e6, 0.38, color=BLUE,     label="Budget",    alpha=0.9)
        ax.bar([i+0.2 for i in x], df["spent"]         /1e6, 0.38, color=BLUE_MID, label="Committed", alpha=0.9)
        names = [n.split("—")[0].strip()[:18] for n in df["project_name"]]
        ax.set_xticks(list(x)); ax.set_xticklabels(names, rotation=20, ha="right", fontsize=7.5)
        style_ax(ax, yticker=millions_fmt()); ax.legend(fontsize=8)
        plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        st.markdown("#### Utilisation % by Project")
        fig, ax = plt.subplots(figsize=(6, 3.5))
        colors = [RED if p > 85 else (AMBER if p > 70 else BLUE) for p in df["pct"]]
        ax.barh(df["project_name"].str.split("—").str[0].str.strip().str[:22][::-1],
                df["pct"][::-1], color=colors[::-1], height=0.55)
        ax.axvline(85, color=RED,   lw=1.2, linestyle="--", alpha=0.7)
        ax.axvline(70, color=AMBER, lw=1.0, linestyle=":",  alpha=0.7)
        ax.set_xlabel("% Budget Utilised", fontsize=8, color=GREY)
        style_ax(ax); plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    st.download_button("Export Portfolio Summary", to_csv_bytes(df), "portfolio_summary.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — RECONCILIATION
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Reconciliation Control":
    page_header("Reconciliation Control", "SAP S/4HANA ledger vs site expenses — variances > $5,000 highlighted")
    exec_summary(build_exec_summary("recon"))

    exp_f = fe(expenses)
    led_f = fl(ledger)
    led_f = led_f[led_f["gl_account"].isin(["GL-6100","GL-6200","GL-6300","GL-6400","GL-6500","GL-6600"])]
    ea = exp_f.groupby("project_id")["amount"].sum().reset_index(name="exp_total")
    la = led_f.groupby("project_id")["amount"].sum().reset_index(name="led_total")
    rc = ea.merge(la, on="project_id", how="outer").fillna(0)
    rc = rc.merge(
        projects[projects["project_id"].isin(proj_ids)][["project_id","project_name","project_budget"]],
        on="project_id"
    )
    rc["variance"] = (rc["exp_total"] - rc["led_total"]).round(2)
    rc["var_pct"]  = (rc["variance"].abs() / rc["exp_total"].replace(0,1) * 100).round(1)
    rc["budget_pct"] = (rc["variance"].abs() / rc["project_budget"] * 100).round(2)
    rc["status"]   = rc["budget_pct"].apply(
        lambda p: "✅ Matched" if p < 0.5 else ("⚠ Minor Gap" if p < 2.0 else "🔴 Material Gap")
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Site Expenses",    fmt_m(exp_f["amount"].sum()))
    c2.metric("SAP Ledger",       fmt_m(led_f["amount"].sum()))
    c3.metric("Gross Variance",   fmt_m(rc["variance"].abs().sum()))
    c4.metric("Material Gaps",    str(int((rc["status"] == "🔴 Material Gap").sum())), delta_color="inverse")
    c5.metric("Flagged Lines",    str(len(exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")])), delta_color="inverse")

    st.divider()
    st.markdown("#### Reconciliation by Project")
    st.caption(
        "⚠ Status thresholds are based on variance as a % of approved project budget — "
        "Tier 1 construction industry standard: "
        "✅ Matched < 0.5% · ⚠ Minor Gap 0.5%–2.0% · 🔴 Material Gap > 2.0%. "
        "A fixed dollar threshold is not used as materiality scales with project size."
    )
    for _, row in rc.iterrows():
        with st.expander(f"{row['status']}  {row['project_name']}  —  Variance: {fmt(row['variance'])} ({row['budget_pct']}% of budget)"):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Site Expenses",       fmt(row["exp_total"]))
            c2.metric("SAP Ledger",          fmt(row["led_total"]))
            c3.metric("Variance $",          fmt(row["variance"]))
            c4.metric("Variance % of Spend", f"{row['var_pct']}%")
            c5.metric("Variance % of Budget",f"{row['budget_pct']}%")

    st.divider()

    # ── GL Accounting Materiality (AASB 1031 / IFRS) ─────────────────────────
    st.markdown("#### GL Accounting Materiality")
    st.caption(
        "Accounting materiality is assessed at GL account level, not project level — per AASB 1031 / IFRS practice. "
        "Threshold = maximum tolerable misstatement as % of GL account balance. "
        "Subcontract and professional fees carry tighter thresholds due to higher audit risk."
    )

    # Reference thresholds by GL account
    GL_MATERIALITY = {
        "GL-6100": ("Direct Labour & Subcontract",  1.0),
        "GL-6200": ("Raw Materials & Consumables",  1.5),
        "GL-6300": ("Equipment & Plant Hire",       2.0),
        "GL-6400": ("Professional & Consulting",    1.0),
        "GL-6500": ("Regulatory & Permit Costs",    2.0),
        "GL-6600": ("Travel & Accommodation",       5.0),
    }

    # Enrich descriptions from CoA where available
    if not coa_df.empty:
        coa_lookup = coa_df.set_index("gl_account")["account_name"].to_dict()
        GL_MATERIALITY = {gl: (coa_lookup.get(gl, desc), pct) for gl, (desc, pct) in GL_MATERIALITY.items()}

    with st.expander("📋 GL Materiality Threshold Reference — AASB 1031 / IFRS", expanded=False):
        ref_df = pd.DataFrame([
            {"GL Account": gl, "Description": desc, "Materiality Threshold": f"{pct}% of GL balance",
             "Tax Code": coa_df.set_index("gl_account").get("tax_code", {}).get(gl, "—") if not coa_df.empty else "—",
             "BAS Field": coa_df.set_index("gl_account").get("bas_field", {}).get(gl, "—") if not coa_df.empty else "—",
             "Rationale": "High value / audit risk — tighter threshold" if pct <= 1.0
                          else ("Standard construction cost account" if pct <= 2.0
                                else "Low-risk, low-value account")}
            for gl, (desc, pct) in GL_MATERIALITY.items()
        ])
        st.dataframe(ref_df, use_container_width=True, hide_index=True)

    # Compare actual GL variance against threshold
    led_f_gl  = fl(ledger)
    led_f_gl = led_f_gl[led_f_gl["gl_account"].isin(["GL-6100","GL-6200","GL-6300","GL-6400","GL-6500","GL-6600"])]
    exp_f_gl  = fe(expenses)

    # Map expense SAP cost codes → GL accounts for comparison
    SAP_TO_GL = {
        "SAP-5001": "GL-6100", "SAP-5002": "GL-6200",
        "SAP-5003": "GL-6300", "SAP-5004": "GL-6400",
        "SAP-5005": "GL-6500", "SAP-5006": "GL-6600",
    }
    exp_f_gl = exp_f_gl.copy()
    exp_f_gl["gl_account"] = exp_f_gl["sap_cost_code"].map(SAP_TO_GL)

    exp_by_gl = exp_f_gl.groupby("gl_account")["amount"].sum().reset_index(name="exp_total")
    led_by_gl = led_f_gl.groupby("gl_account")["amount"].sum().reset_index(name="led_total")
    gl_rc     = exp_by_gl.merge(led_by_gl, on="gl_account", how="outer").fillna(0)
    gl_rc["variance"]     = (gl_rc["exp_total"] - gl_rc["led_total"]).abs().round(2)
    gl_rc["var_pct_of_gl"]= (gl_rc["variance"] / gl_rc["exp_total"].replace(0, 1) * 100).round(2)
    gl_rc["threshold"]    = gl_rc["gl_account"].map(lambda g: GL_MATERIALITY.get(g, ("Unknown", 2.0))[1])
    gl_rc["description"]  = gl_rc["gl_account"].map(lambda g: GL_MATERIALITY.get(g, ("Unknown", 2.0))[0])
    gl_rc["exceeds"]      = gl_rc["var_pct_of_gl"] > gl_rc["threshold"]
    gl_rc["mat_status"]   = gl_rc.apply(
        lambda r: "🔴 Exceeds Materiality" if r["exceeds"]
                  else ("🟡 Approaching" if r["var_pct_of_gl"] > r["threshold"] * 0.75
                  else "✅ Within Threshold"), axis=1
    )

    for _, row in gl_rc.sort_values("exceeds", ascending=False).iterrows():
        with st.expander(f"{row['mat_status']}  {row['gl_account']} — {row['description']}"):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Site Expenses",       fmt(row["exp_total"]))
            c2.metric("SAP Ledger",          fmt(row["led_total"]))
            c3.metric("Variance $",          fmt(row["variance"]))
            c4.metric("Variance % of GL",    f"{row['var_pct_of_gl']}%")
            c5.metric("Materiality Threshold", f"{row['threshold']}%",
                      delta="⚠ Exceeded" if row["exceeds"] else "✅ Clear",
                      delta_color="inverse" if row["exceeds"] else "normal")
            st.progress(
                min(row["var_pct_of_gl"] / row["threshold"], 1.0) if row["threshold"] > 0 else 0.0,
                text=f"{row['var_pct_of_gl']}% of {row['threshold']}% threshold used"
            )

    # ── GST Bridge ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### GST Bridge — BAS Derivation from SAP Tax Codes")
    st.caption(
        "ATO tax codes on each GL posting link directly to BAS fields — "
        "G1 (output tax → 1A), G11 (input credits → 1B), G12 (GST-free purchases)."
    )

    if "tax_code" in ledger.columns and "gst_amount" in ledger.columns:
        led_tax = fl(ledger).copy()
        output_tax    = led_tax[led_tax["tax_code"] == "G1"]["gst_amount"].sum()
        input_credits = led_tax[led_tax["tax_code"] == "G11"]["gst_amount"].sum()
        gst_free_val  = led_tax[led_tax["tax_code"] == "G12"]["amount"].sum()
        net_bas       = output_tax - input_credits

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("1A — GST Collected",   fmt_m(output_tax),    delta="Output tax on supplies")
        c2.metric("1B — Input Credits",   fmt_m(input_credits), delta="GST on purchases")
        c3.metric("Net BAS (1A − 1B)",    fmt_m(abs(net_bas)),
                  delta="Refund due ↓" if net_bas < 0 else "Payable to ATO ↑",
                  delta_color="normal" if net_bas < 0 else "inverse")
        c4.metric("GST-Free Purchases",   fmt_m(gst_free_val),  delta="G12 — no GST impact")

        if net_bas < 0:
            st.success(
                f"Input credits exceed output tax by **{fmt_m(abs(net_bas))}** — "
                f"ATO refund expected. Typical for construction: high subcontractor/materials "
                f"input credits during build phase outpace progress claim output tax."
            )
        else:
            st.warning(f"Net GST payable: **{fmt_m(net_bas)}** — cash outflow due on next BAS lodgement date.")

        TAX_DESC = {
            "G1":  "Output tax — GST on supplies (BAS 1A)",
            "G11": "Input credits — non-capital purchases (BAS 1B)",
            "G12": "GST-free purchases — government/exempt charges",
        }
        tax_grp = (
            led_tax.groupby("tax_code")
            .agg(Transactions=("ledger_id","count"),
                 Ex_GST_Amount=("amount","sum"),
                 GST_Amount=("gst_amount","sum"))
            .reset_index()
        )
        tax_grp.columns   = ["Tax Code","Transactions","Ex-GST Amount","GST Amount"]
        tax_grp["Description"] = tax_grp["Tax Code"].map(TAX_DESC)
        tax_grp["BAS Field"]   = tax_grp["Tax Code"].map({"G1":"1A","G11":"1B","G12":"N/A"})
        st.dataframe(
            style_dollars(tax_grp.set_index("Tax Code"), ["Ex-GST Amount","GST Amount"]),
            use_container_width=True,
        )
    else:
        st.info("Tax code data unavailable — re-run `generate_csv.py` to add GST fields.")

    st.divider()
    flagged = exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")].copy()
    if not flagged.empty:
        st.markdown("#### ⚠ Exception Lines — Require Review Before Month-End Close")
        st.caption("Exception lines sourced from Concur AP export and site system — reviewed pre-payment run against SAP S/4HANA ledger.")
        flagged["booking_date"] = flagged["booking_date"].dt.strftime("%d %b %Y")
        src_col = "source_system" if "source_system" in flagged.columns else None
        cols = ["booking_date","project_id","expense_type","amount","vendor","status","comment"]
        if src_col:
            cols.insert(cols.index("comment"), src_col)
        disp = flagged[cols].copy().reset_index(drop=True)
        disp["project_id"] = disp["project_id"].astype(str)
        col_names = ["Booking Date","Project ID","Expense Type","Amount","Vendor","Status","Comment"]
        if src_col:
            col_names.insert(col_names.index("Comment"), "Source System")
        disp.columns = col_names
        disp.index = range(1, len(disp) + 1)
        st.dataframe(style_dollars(disp, ["Amount"]), use_container_width=True)
        st.download_button("Export Exception Lines", to_csv_bytes(flagged), "recon_exceptions.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — CASH & COVENANT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Cash Flow & Covenant":
    page_header("Cash Flow & Covenant", "Liquidity headroom · Covenant compliance · Scenario stress-testing")
    show_alerts(generate_alerts(fe(expenses), ff(forecasts), facilities, weekly_cf))
    exec_summary(build_exec_summary("covenant"))
    if selected != "All Projects":
        st.info(f"Bank accounts filtered to **{selected}** drawdown + group accounts. Covenant facilities and weekly cash flow are group-level.")

    actual_cf = weekly_cf[weekly_cf["type"] == "Actual"]
    cash      = actual_cf["closing_balance"].iloc[-1] if not actual_cf.empty else 0
    avg_net   = actual_cf["net_movement"].mean() if not actual_cf.empty else 0
    min_cov   = facilities["covenant_min_cash_aud"].max()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Facility Limit",   fmt_m(facilities["limit_aud"].sum()))
    c2.metric("Total Drawn",      fmt_m(facilities["drawn_aud"].sum()))
    c3.metric("Headroom",         fmt_m((facilities["limit_aud"]-facilities["drawn_aud"]).sum()))
    c4.metric("Cash Balance",     fmt_m(cash))
    c5.metric("Above Cov. Floor", fmt_m(cash - min_cov), delta=f"Floor: {fmt_m(min_cov)}")
    c6.metric("Weekly Net Cash",  fmt_m(avg_net), delta="Avg last 4 wks",
              delta_color="normal" if avg_net >= 0 else "inverse")

    st.divider()
    st.markdown("#### Covenant Test — Per Facility")
    for _, row in facilities.iterrows():
        util    = row["drawn_aud"] / row["limit_aud"]
        hdroom  = row["limit_aud"] - row["drawn_aud"]
        cash_ok = cash >= row["covenant_min_cash_aud"]
        icon    = "🟢" if util < 0.70 and cash_ok else ("🟡" if util < 0.85 else "🔴")
        status  = "Compliant" if util < 0.70 and cash_ok else ("Monitor" if util < 0.85 else "⚠ Breach Risk")
        with st.expander(f"{icon} {row['facility_name']} — {row['bank']}  |  {status}"):
            cc1, cc2, cc3, cc4, cc5 = st.columns(5)
            cc1.metric("Limit",    fmt(row["limit_aud"]))
            cc2.metric("Drawn",    fmt(row["drawn_aud"]), delta=f"{util*100:.1f}%", delta_color="inverse")
            cc3.metric("Headroom", fmt(hdroom))
            cc4.metric("Min Cash Covenant", fmt(row["covenant_min_cash_aud"]),
                       delta="✅ Met" if cash_ok else "❌ At Risk",
                       delta_color="normal" if cash_ok else "inverse")
            cc5.metric("Maturity", row["maturity_date"])
            st.progress(float(util), text=f"{util*100:.1f}% utilised · Review: {row['next_review_date']}")

    st.divider()
    st.markdown("#### Daily Bank Account Positions")
    st.caption("Today's opening, receipts, payments, and closing balance across all group accounts · GST-inclusive · AUD")

    _ba_cov     = fb(bank_accts)
    today_str   = "2026-04-18"
    today_accts = _ba_cov[_ba_cov["date"].dt.strftime("%Y-%m-%d") == today_str].copy()

    if not today_accts.empty:
        total_closing = today_accts["closing_balance"].sum()
        total_receipts = today_accts["receipts"].sum()
        total_payments = today_accts["payments"].sum()
        net_today = total_receipts - total_payments

        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Total Cash (Filtered Accounts)", fmt_m(total_closing))
        tc2.metric("Total Receipts Today",           fmt_m(total_receipts))
        tc3.metric("Total Payments Today",           fmt_m(total_payments))
        tc4.metric("Net Movement Today",             fmt_m(net_today),
                   delta_color="normal" if net_today >= 0 else "inverse")

        st.markdown("")
        _disp_cols = ["account_name","bank","bsb","account_type"]
        if "sap_cost_center" in today_accts.columns:
            _disp_cols.append("sap_cost_center")
        _disp_cols += ["opening_balance","receipts","payments","closing_balance"]
        disp = today_accts[_disp_cols].copy()
        disp["movement"] = disp["closing_balance"] - disp["opening_balance"]
        _hdr = ["Account Name","Bank","BSB","Type"]
        if "sap_cost_center" in today_accts.columns:
            _hdr.append("Cost Centre")
        _hdr += ["Opening Balance","Receipts","Payments","Closing Balance","Net Movement"]
        disp.columns = _hdr
        _amt_ba = ["Opening Balance","Receipts","Payments","Closing Balance","Net Movement"]
        st.dataframe(
            style_dollars(disp.set_index("Account Name"), _amt_ba),
            use_container_width=True,
        )

        st.markdown("#### 10-Day Rolling Balance by Account")
        fig, ax = plt.subplots(figsize=(10, 3.8))
        for _, grp in _ba_cov.groupby("account_name"):
            grp = grp.sort_values("date")
            ax.plot(grp["date"], grp["closing_balance"] / 1e6,
                    marker="o", ms=3.5, lw=1.8, label=grp["account_name"].iloc[0].split(" ")[0] + " " + grp["account_name"].iloc[0].split(" ")[1])
        style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
        ax.legend(fontsize=7.5, ncol=2, loc="upper left")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        plt.xticks(rotation=20, ha="right", fontsize=7.5)
        plt.tight_layout(pad=1.2)
        st.pyplot(fig, use_container_width=True)
        plt.close()

    st.divider()
    st.markdown("#### 16-Week Liquidity Runway Simulation")
    st.caption("200-path simulation based on current burn rate. Green = safe headroom · Red = breach zone.")

    sims = 200
    weeks = 16
    matrix = []
    for _ in range(sims):
        path = [cash]
        for _ in range(weeks):
            next_val = max(path[-1] + avg_net * random.uniform(0.7, 1.3), min_cov)
            path.append(next_val)
        matrix.append(path)

    sim_df = pd.DataFrame(matrix).T
    p5  = sim_df.quantile(0.05, axis=1)
    p95 = sim_df.quantile(0.95, axis=1)
    med = sim_df.quantile(0.50, axis=1)

    fig, ax = plt.subplots(figsize=(10, 4))
    x = range(weeks + 1)
    ax.fill_between(x, p5/1e6, p95/1e6, alpha=0.12, color=BLUE, label="5th–95th percentile")
    ax.plot(x, med/1e6, color=BLUE, lw=2.2, label="Median trajectory")
    ax.axhline(min_cov/1e6, color=RED, lw=1.4, linestyle="--", label=f"Covenant floor {fmt_m(min_cov)}")
    ax.fill_between(x, p5/1e6, min_cov/1e6,
                    where=[p5.iloc[i] < min_cov for i in range(weeks+1)],
                    alpha=0.18, color=RED, label="Breach probability zone")
    style_ax(ax, ylabel="AUD (M)", xlabel="Weeks Forward", yticker=millions_fmt())
    ax.legend(fontsize=8)
    plt.tight_layout(pad=1.2)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # ── Scenario stress-testing ───────────────────────────────────────────────
    st.divider()
    st.markdown("#### Scenario Stress-Testing — Cost Escalation Impact")
    st.caption("Adjusts forecast outflows by selected %, recalculates cash runway and covenant breach risk.")

    scn_pcts = st.multiselect(
        "Stress scenarios (spend increase %)",
        options=[0, 5, 10, 15, 20, 30],
        default=[0, 10, 20],
        key="scn_select",
    )
    if scn_pcts:
        scn_results = simulate_spend_scenarios(
            forecasts, weekly_cf, facilities,
            scenarios=[p / 100 for p in sorted(scn_pcts)]
        )
        if scn_results:
            summary_rows = [{
                "Scenario":        r["scenario"],
                "Final Cash":      r["final_cash"],
                "Runway (periods)": r["runway"],
                "Covenant Breach": "⚠ Yes" if r["breach"] else "✅ Safe",
                "Breach Period":   r["breach_week"],
            } for r in scn_results]
            scn_summary = pd.DataFrame(summary_rows)
            st.dataframe(style_dollars(scn_summary.set_index("Scenario"), ["Final Cash"]), use_container_width=True)

            chart_scn = pd.DataFrame()
            for r in scn_results:
                tmp = r["df"][["forecast_date","balance"]].rename(columns={"balance": r["scenario"]}).set_index("forecast_date")
                chart_scn = tmp if chart_scn.empty else chart_scn.join(tmp, how="outer")
            st.line_chart(chart_scn)

            risky = [r for r in scn_results if r["breach"]]
            if risky:
                worst = sorted(risky, key=lambda r: r["runway"])[0]
                st.error(f"🚨 Highest-risk scenario {worst['scenario']} breaches covenant in period {worst['breach_week']}.")
            else:
                st.success("All tested scenarios remain within covenant limits.")
        else:
            st.info("Insufficient forecast data for simulation.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — VENDOR RISK
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Payments & Vendor Risk":
    page_header("Payments & Vendor Risk", "Spend concentration · Flagged transactions · Payment status")
    exec_summary(build_exec_summary("vendor"))

    exp_f = fe(expenses).merge(projects[["project_id","project_name"]], on="project_id")
    top10 = exp_f.groupby("vendor")["amount"].sum().sort_values(ascending=False).head(10)
    conc3 = top10.head(3).sum() / max(exp_f["amount"].sum(), 1) * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Vendors",      str(exp_f["vendor"].nunique()))
    c2.metric("Total Vendor Spend",  fmt_m(exp_f["amount"].sum()))
    c3.metric("Top-3 Concentration", f"{conc3:.0f}%", delta="Of total spend",
              delta_color="inverse" if conc3 > 55 else "normal")
    c4.metric("Avg Invoice",         fmt(exp_f["amount"].mean()))
    c5.metric("Flagged Vendors",     str(exp_f[exp_f["comment"].notna() & (exp_f["comment"]!="")]["vendor"].nunique()),
              delta_color="inverse")

    st.divider()
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("#### Top 10 Vendors by Committed Spend")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.barh(top10.index[::-1], top10.values[::-1]/1e6, color=BLUE, height=0.55)
        style_ax(ax, yticker=millions_fmt())
        plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        st.markdown("#### Expense Type Breakdown")
        by_type = exp_f.groupby("expense_type")["amount"].sum().sort_values(ascending=False)
        type_colors = [BLUE, BLUE_MID, GREY, "#8e9eb5", "#b8c4d6", "#d0d8e8"]
        fig, ax = plt.subplots(figsize=(5, 4.5))
        wedges, texts, auto = ax.pie(by_type.values, labels=None, autopct="%1.0f%%",
                                     colors=type_colors[:len(by_type)], startangle=140,
                                     pctdistance=0.75, wedgeprops={"linewidth":1.5,"edgecolor":WHITE})
        for t in auto: t.set_fontsize(8); t.set_color(WHITE)
        ax.legend(by_type.index, loc="lower center", fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
        plt.tight_layout(pad=0.5); st.pyplot(fig, use_container_width=True); plt.close()

    st.divider()
    st.markdown("#### Payment Status by Top Vendors")
    status_df = (
        exp_f[exp_f["vendor"].isin(top10.index)]
        .groupby(["vendor","status"])["amount"].sum().unstack(fill_value=0).reset_index()
    )
    amt_cols = [c for c in status_df.columns if c != "vendor"]
    st.dataframe(style_dollars(status_df.set_index("vendor"), amt_cols), use_container_width=True)

    flagged = exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")].copy()
    if not flagged.empty:
        st.divider()
        st.markdown("#### ⚠ Flagged Vendor Exceptions — AP Review Required")
        risk = (flagged.groupby("vendor")
                .agg(flags=("comment","count"), value=("amount","sum"))
                .sort_values("flags", ascending=False).reset_index())
        risk.columns = ["Vendor", "Flag Count", "Flagged Value"]
        st.dataframe(style_dollars(risk.set_index("Vendor"), ["Flagged Value"]), use_container_width=True)
        st.download_button("Export Flagged Vendors", to_csv_bytes(flagged), "vendor_exceptions.csv", "text/csv")

    # ── AP / Invoice GST Breakdown ─────────────────────────────────────────────
    if "tax_code" in exp_f.columns and "gst_amount" in exp_f.columns:
        st.divider()
        st.markdown("#### AP Invoice GST Position (Input Tax Credits — BAS 1B)")

        exp_f["gst_amount"] = pd.to_numeric(exp_f["gst_amount"], errors="coerce").fillna(0)
        exp_taxable  = exp_f[exp_f["tax_code"] == "G11"]
        exp_free     = exp_f[exp_f["tax_code"] == "G12"]
        total_ex_gst = exp_f["amount"].sum()
        total_gst    = exp_f["gst_amount"].sum()
        total_inc_gst = total_ex_gst + total_gst
        gst_free_amt  = exp_free["amount"].sum()

        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("Total Ex-GST Payable",    fmt_m(total_ex_gst),   delta="AP invoices ex-GST", delta_color="off")
        gc2.metric("GST Input Credits (1B)",  fmt_m(total_gst),      delta="Claimable from ATO", delta_color="normal")
        gc3.metric("Total GST-Incl. Payable", fmt_m(total_inc_gst),  delta="Actual cash to vendors", delta_color="off")
        gc4.metric("GST-Free Invoices (G12)", fmt_m(gst_free_amt),   delta="Government charges etc.", delta_color="off")

        st.caption(
            "**G11** — Standard-rated AP invoices (subcontractors, materials, plant hire, professional services) — "
            "GST input credits recoverable on your BAS.  "
            "**G12** — GST-free purchases (government permits, compliance fees) — no GST component.  "
            "Source: Trade Account & Concur Expense data."
        )

        # Breakdown by tax code and source system
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**By ATO Tax Code**")
            by_tax = (exp_f.groupby("tax_code")
                      .agg(invoices=("expense_id","count"), ex_gst=("amount","sum"), gst=("gst_amount","sum"))
                      .reset_index())
            by_tax.columns = ["Tax Code", "Invoice Count", "Ex-GST Amount", "GST Amount"]
            st.dataframe(style_dollars(by_tax.set_index("Tax Code"), ["Ex-GST Amount", "GST Amount"]),
                         use_container_width=True)
        with col_b:
            st.markdown("**By Source System**")
            by_src = (exp_f.groupby("source_system")
                      .agg(invoices=("expense_id","count"), ex_gst=("amount","sum"), gst=("gst_amount","sum"))
                      .sort_values("ex_gst", ascending=False).reset_index())
            by_src.columns = ["Source System", "Invoice Count", "Ex-GST Amount", "GST Amount"]
            st.dataframe(style_dollars(by_src.set_index("Source System"), ["Ex-GST Amount", "GST Amount"]),
                         use_container_width=True)

    # ── AP Procurement Compliance — 3-Way Match Control ────────────────────────
    if "po_status" in exp_f.columns:
        st.divider()
        st.markdown("#### AP Procurement Compliance — PO / Contract 3-Way Match")

        exp_f["po_value"] = pd.to_numeric(exp_f["po_value"], errors="coerce").fillna(0)
        total_inv   = len(exp_f)
        matched_n   = int((exp_f["po_status"] == "Matched").sum())
        over_po_n   = int((exp_f["po_status"] == "Over PO").sum())
        no_po_n     = int((exp_f["po_status"] == "No PO").sum())
        compliance_rate = matched_n / max(total_inv, 1) * 100

        # Over-PO monetary exposure
        over_po_df = exp_f[exp_f["po_status"] == "Over PO"].copy()
        over_po_df["variance_amt"] = over_po_df["amount"] - over_po_df["po_value"]
        over_po_df["variance_pct"] = (over_po_df["variance_amt"] / over_po_df["po_value"].replace(0, 1) * 100).round(2)
        over_po_exposure = over_po_df["variance_amt"].sum()

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Compliance Rate",      f"{compliance_rate:.0f}%",
                   delta=f"{matched_n} of {total_inv} invoices matched",
                   delta_color="normal" if compliance_rate >= 85 else "inverse")
        pc2.metric("Over-PO Exceptions",   str(over_po_n),
                   delta=f"${over_po_exposure:,.0f} excess exposure",
                   delta_color="inverse" if over_po_n > 0 else "normal")
        pc3.metric("Missing PO (Breach)",  str(no_po_n),
                   delta="Procurement policy breach" if no_po_n > 0 else "None",
                   delta_color="inverse" if no_po_n > 0 else "normal")
        pc4.metric("With Contract Ref",
                   str(exp_f[exp_f["contract_ref"].notna() & (exp_f["contract_ref"] != "")].shape[0]),
                   delta="Formal contract in place", delta_color="off")

        # Tolerance reference
        tol_info = pd.DataFrame([
            {"Expense Type": k, "Tolerance": f"±{int(v*100)}%",
             "Basis": "Fixed fees" if v == 0 else ("Formal contract" if v <= 0.02 else "Policy-based" if v >= 0.10 else "Delivery variance")}
            for k, v in [
                ("Subcontractor", 0.02), ("Materials", 0.05), ("Plant Hire", 0.05),
                ("Professional Services", 0.03), ("Permits & Compliance", 0.00), ("Travel & Accommodation", 0.10),
            ]
        ])
        with st.expander("View PO Tolerance Thresholds by Category"):
            st.dataframe(tol_info.set_index("Expense Type"), use_container_width=True)

        if not over_po_df.empty:
            st.markdown("**Over-PO Exceptions — Requires Variation Order or Re-Approval**")
            st.caption(
                "All amounts **ex-GST** — PO value is approved ex-GST (SAP commitment). "
                "Invoice Amt is ex-GST from AP invoice. "
                "GST-Incl Total = actual cash payable to vendor (Invoice Amt + GST). "
                "Variance is calculated ex-GST vs ex-GST."
            )
            over_po_df["gst_amount"] = pd.to_numeric(over_po_df.get("gst_amount", 0), errors="coerce").fillna(0)
            over_po_df["gst_incl_total"] = over_po_df["amount"] + over_po_df["gst_amount"]
            disp_over = over_po_df[["vendor","expense_type","amount","gst_amount","gst_incl_total",
                                     "po_value","variance_amt","variance_pct",
                                     "po_reference","contract_ref","comment"]].copy()
            disp_over.columns = ["Vendor","Type","Invoice (ex-GST)","GST Amount","GST-Incl Total",
                                  "PO Value (ex-GST)","Variance $","Variance %",
                                  "PO Reference","Contract Ref","Comment"]
            disp_over.index = range(1, len(disp_over) + 1)
            disp_over = fmt_pct_col(disp_over, ["Variance %"])
            st.dataframe(style_dollars(disp_over, ["Invoice (ex-GST)","GST Amount","GST-Incl Total","PO Value (ex-GST)","Variance $"]),
                         use_container_width=True)

        no_po_df = exp_f[exp_f["po_status"] == "No PO"].copy()
        if not no_po_df.empty:
            st.markdown("**Missing PO — Procurement Policy Breach**")
            st.caption("Invoice Amt is ex-GST. GST-Incl Total = actual cash payable to vendor.")
            no_po_df["gst_amount"]    = pd.to_numeric(no_po_df.get("gst_amount", 0), errors="coerce").fillna(0)
            no_po_df["gst_incl_total"] = no_po_df["amount"] + no_po_df["gst_amount"]
            disp_nopo = no_po_df[["vendor","expense_type","amount","gst_amount","gst_incl_total",
                                   "booking_date","source_system","comment"]].copy()
            disp_nopo.columns = ["Vendor","Type","Invoice (ex-GST)","GST Amount","GST-Incl Total",
                                  "Booking Date","Source","Comment"]
            disp_nopo.index = range(1, len(disp_nopo) + 1)
            st.dataframe(style_dollars(disp_nopo, ["Invoice (ex-GST)","GST Amount","GST-Incl Total"]), use_container_width=True)
            st.caption(
                "⚠ Invoices processed without a valid PO reference violate the Procurement Policy. "
                "Escalate to Procurement Manager for retrospective PO or rejection."
            )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — AUDIT REGISTER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Audit & Controls":
    page_header("Audit & Controls", "Open items prioritised by urgency · Filter by module and status")
    exec_summary(build_exec_summary("audit"))

    aud_f = fa(audit).merge(projects[["project_id","project_name"]], on="project_id")
    open_n = int((aud_f["status"]=="Open").sum())
    rev_n  = int((aud_f["status"]=="Under Review").sum())
    res_n  = int((aud_f["status"]=="Resolved").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Open",         str(open_n), delta="Immediate action", delta_color="inverse")
    c2.metric("🟡 Under Review", str(rev_n),  delta="In progress",      delta_color="off")
    c3.metric("🟢 Resolved",     str(res_n),  delta="Closed",           delta_color="normal")
    c4.metric("Total Items",     str(len(aud_f)))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Filter by Status**")
        status_opts = aud_f["status"].unique().tolist()
        status_icons = {"Open": "🔴", "Under Review": "🟡", "Resolved": "🟢"}
        st_cols = st.columns(3)
        status_f = [s for i, s in enumerate(status_opts)
                    if st_cols[i % 3].checkbox(f"{status_icons.get(s, '')} {s}", value=True, key=f"st_{s}")]
    with col2:
        st.markdown("**Filter by Module**")
        module_opts = sorted(aud_f["module"].unique().tolist())
        mod_cols = st.columns(4)
        module_f = [m for i, m in enumerate(module_opts)
                    if mod_cols[i % 4].checkbox(m, value=True, key=f"mod_{m}")]

    urgency = {"Open": 0, "Under Review": 1, "Resolved": 2}
    filtered = (aud_f[aud_f["status"].isin(status_f) & aud_f["module"].isin(module_f)]
                .assign(_s=lambda d: d["status"].map(urgency))
                .sort_values("_s").drop(columns="_s"))

    for _, row in filtered.iterrows():
        icon = "🔴" if row["status"]=="Open" else ("🟡" if row["status"]=="Under Review" else "🟢")
        with st.expander(f"{icon} [{row['status']}] {row['issue_type']} — {row['project_name']}  ·  {row['event_date'].strftime('%d %b %Y')}"):
            st.caption(f"Module: {row['module']}")
            st.markdown(row["notes"])

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Issues by Type")
        counts = aud_f["issue_type"].value_counts()
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        bar_colors = [RED if any(k in i for k in ["Overrun","Breach","Guarantee"]) else
                      (AMBER if any(k in i for k in ["Missing","Duplicate","Exception"]) else BLUE)
                      for i in counts.index[::-1]]
        ax.barh(counts.index[::-1], counts.values[::-1], color=bar_colors, height=0.55)
        style_ax(ax); plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        st.markdown("#### Status Distribution")
        sc = aud_f["status"].value_counts()
        s_colors = [RED if s=="Open" else (AMBER if s=="Under Review" else GREEN) for s in sc.index]
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        wedges, texts, auto = ax.pie(sc.values, labels=None, autopct="%1.0f%%", colors=s_colors,
                                     startangle=90, wedgeprops={"linewidth":1.5,"edgecolor":WHITE}, pctdistance=0.72)
        for t in auto: t.set_fontsize(8.5); t.set_color(WHITE); t.set_fontweight("600")
        ax.legend(sc.index, loc="lower center", fontsize=8, bbox_to_anchor=(0.5,-0.08), ncol=3, frameon=False)
        plt.tight_layout(pad=0.5); st.pyplot(fig, use_container_width=True); plt.close()

    export = filtered.copy()
    export["event_date"] = export["event_date"].dt.strftime("%d %b %Y")
    st.download_button("Export Audit Register", to_csv_bytes(export), "audit_register.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 7 — STATUTORY COMPLIANCE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Statutory Compliance":
    page_header("Statutory Compliance", "BAS · IAS · Payroll Tax · Superannuation SG · ATO lodgement calendar")

    STATUS_ICON = {"Lodged": "🟢", "Pending": "🟡", "Overdue": "🔴", "Scheduled": "⚪"}
    STATUS_ORDER = {"Overdue": 0, "Pending": 1, "Scheduled": 2, "Lodged": 3}

    overdue_n  = int((statutory["status"] == "Overdue").sum())
    pending_n  = int((statutory["status"] == "Pending").sum())
    lodged_n   = int((statutory["status"] == "Lodged").sum())
    sched_n    = int((statutory["status"] == "Scheduled").sum())
    total_liab = statutory[statutory["status"].isin(["Pending","Overdue"])]["amount_aud"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔴 Overdue",        str(overdue_n),  delta="Immediate action", delta_color="inverse")
    c2.metric("🟡 Pending",        str(pending_n),  delta="Due within 14 days", delta_color="off")
    c3.metric("🟢 Lodged",         str(lodged_n),   delta="Compliant",        delta_color="normal")
    c4.metric("⚪ Scheduled",      str(sched_n),    delta="Future obligations", delta_color="off")
    c5.metric("Imminent Liability", fmt_m(total_liab), delta="Overdue + Pending", delta_color="inverse")

    st.info(
        "**Note:** Obligation amounts are calculated from the payroll register extract and project budget proxy "
        "(wages base ≈ 22% of committed project expenditure). BAS/IAS figures represent GST and PAYG Withholding "
        "components. All figures are estimates pending final payroll close."
    )
    st.divider()

    # ── BAS cash impact from GST Bridge ──────────────────────────────────────
    if "tax_code" in ledger.columns and "gst_amount" in ledger.columns:
        output_tax_all    = ledger[ledger["tax_code"] == "G1"]["gst_amount"].sum()
        input_credits_all = ledger[ledger["tax_code"] == "G11"]["gst_amount"].sum()
        net_bas_all       = output_tax_all - input_credits_all
        bas_row = statutory[statutory["obligation_type"] == "BAS"].sort_values("due_date")
        next_bas_due = bas_row[bas_row["status"].isin(["Pending","Overdue"])]["due_date"].min()

        st.markdown("#### BAS Cash Flow Impact — Derived from GL Tax Codes")
        st.caption("1A and 1B figures cross-referenced from SAP ledger postings (see Reconciliation Control → GST Bridge for full workpaper).")
        cb1, cb2, cb3 = st.columns(3)
        cb1.metric("GST Collected (1A)",  fmt_m(output_tax_all),    delta="From G1 GL postings")
        cb2.metric("Input Credits (1B)",  fmt_m(input_credits_all), delta="From G11 GL postings")
        cb3.metric("Net BAS Position",    fmt_m(abs(net_bas_all)),
                   delta=f"{'Refund' if net_bas_all < 0 else 'Payable'} · Due {next_bas_due.strftime('%d %b %Y') if pd.notna(next_bas_due) else 'N/A'}",
                   delta_color="normal" if net_bas_all < 0 else "inverse")
        if net_bas_all < 0:
            st.success("Net refund position — ATO expected to credit on lodgement. Positive treasury cash event.")
        else:
            st.warning(f"Net payable — {fmt_m(net_bas_all)} cash outflow due on BAS lodgement date.")
        st.divider()

    # ── Traffic-light summary by obligation type ──────────────────────────────
    st.markdown("#### Compliance Status by Obligation Type")
    for ob_type in ["BAS", "IAS", "Payroll Tax", "Superannuation SG"]:
        subset = statutory[statutory["obligation_type"] == ob_type]
        ov = int((subset["status"] == "Overdue").sum())
        pe = int((subset["status"] == "Pending").sum())
        lo = int((subset["status"] == "Lodged").sum())
        overall_icon = "🔴" if ov > 0 else ("🟡" if pe > 0 else "🟢")
        overall_label = "Action Required" if ov > 0 else ("Due Soon" if pe > 0 else "Compliant")
        with st.expander(f"{overall_icon} **{ob_type}** — {overall_label}  ·  {len(subset)} obligations  ·  Total: {fmt_m(subset['amount_aud'].sum())}"):
            for _, row in subset.sort_values("status", key=lambda s: s.map(STATUS_ORDER)).iterrows():
                icon  = STATUS_ICON.get(row["status"], "⚪")
                state = f" · {row['state']}" if row["state"] != "National" else ""
                due   = row["due_date"].strftime("%d %b %Y")
                lodged_str = f" · Lodged {row['lodged_date']}" if pd.notna(row.get("lodged_date")) and row["lodged_date"] != "" else ""
                cc1, cc2, cc3, cc4 = st.columns([2, 1, 1, 2])
                cc1.markdown(f"{icon} **{row['period_label']}**{state}")
                cc2.markdown(f"Due: `{due}`{lodged_str}")
                cc3.markdown(fmt_m(row["amount_aud"]))
                cc4.caption(row["notes"][:120] + ("…" if len(str(row["notes"])) > 120 else ""))
                if row["status"] == "Overdue":
                    st.warning(f"⚠ **{row['period_label']} — {ob_type} overdue.** Contact {row['authority']} immediately. Late lodgement penalties may apply.")

    st.divider()

    # ── Payroll tax by state breakdown ────────────────────────────────────────
    st.markdown("#### Payroll Tax — State Obligations")
    st.caption("Active jurisdictions: VIC · NSW · WA — matching current project locations.")

    with st.expander("📋 Australian Payroll Tax Rates & Thresholds — All Jurisdictions Reference", expanded=False):
        pt_ref = pd.DataFrame([
            {"State": "VIC ✦", "Rate": "4.85% (1.2125% regional)",
             "Annual Threshold": "$1,000,000", "Monthly Threshold": "$83,333",
             "Notes": "Deduction phases out 50% between $3M–$5M wages; nil >$5M. "
                      "Combined surcharge: 1% national >$10M, 2% national >$100M (mental health + COVID debt)."},
            {"State": "NSW ✦", "Rate": "5.45%",
             "Annual Threshold": "$1,200,000", "Monthly Threshold": "$100,000",
             "Notes": "Deduction = threshold. Active jurisdiction."},
            {"State": "WA ✦",  "Rate": "5.50%",
             "Annual Threshold": "$1,000,000", "Monthly Threshold": "$83,333",
             "Notes": "Deduction = threshold. Active jurisdiction."},
            {"State": "QLD",   "Rate": "4.75% (≤$6.5M) / 4.95% (>$6.5M)",
             "Annual Threshold": "$1,300,000", "Monthly Threshold": "$108,333",
             "Notes": "1% regional discount to Jun 2030. Mental health levy: +0.25% >$10M, +0.75% >$100M."},
            {"State": "SA",    "Rate": "0%–4.95% ($1.5M–$1.7M) / 4.95% (>$1.7M)",
             "Annual Threshold": "$1,500,000", "Monthly Threshold": "$125,000",
             "Notes": "Max annual deduction $600,000 (not equal to threshold)."},
            {"State": "ACT",   "Rate": "6.85%",
             "Annual Threshold": "$2,000,000", "Monthly Threshold": "$166,667",
             "Notes": "Surcharge from Jul 2024: +0.25% national >$50M; +0.50% national >$100M on ACT wages above threshold."},
            {"State": "TAS",   "Rate": "4% ($1.25M–$2M) / 6.1% (>$2M)",
             "Annual Threshold": "$1,250,000", "Monthly Threshold": "$104,167",
             "Notes": "Deduction = threshold."},
            {"State": "NT",    "Rate": "5.50%",
             "Annual Threshold": "$2,500,000", "Monthly Threshold": "$208,333",
             "Notes": "Deduction = threshold. Highest threshold nationally."},
        ])
        st.caption("✦ Active jurisdiction for this portfolio.")
        st.dataframe(pt_ref, use_container_width=True, hide_index=True,
                     column_config={
                         "State":             st.column_config.TextColumn(width="small"),
                         "Rate":              st.column_config.TextColumn(width="medium"),
                         "Annual Threshold":  st.column_config.TextColumn(width="small"),
                         "Monthly Threshold": st.column_config.TextColumn(width="small"),
                         "Notes":             st.column_config.TextColumn(width="large"),
                     })

    pt = statutory[statutory["obligation_type"] == "Payroll Tax"].copy()
    if not pt.empty:
        pt_summary = pt.groupby("state").agg(
            total_liability=("amount_aud", "sum"),
            obligations=("obligation_id", "count"),
            overdue=("status", lambda x: (x == "Overdue").sum()),
            pending=("status", lambda x: (x == "Pending").sum()),
        ).reset_index()
        for _, row in pt_summary.iterrows():
            icon = "🔴" if row["overdue"] > 0 else ("🟡" if row["pending"] > 0 else "🟢")
            st.markdown(f"{icon} **{row['state']}** — Total: {fmt_m(row['total_liability'])} · {row['obligations']} obligations")

    st.divider()

    # ── Super SG schedule ─────────────────────────────────────────────────────
    st.markdown("#### Superannuation SG — Payment Schedule")
    st.caption("SG rate: 12.0% (FY2025–26, from 1 Jul 2025) · Paid via SuperStream · Funds: REST / AustralianSuper / Hostplus")

    super_df = statutory[statutory["obligation_type"] == "Superannuation SG"].copy()
    for _, row in super_df.iterrows():
        icon = STATUS_ICON.get(row["status"], "⚪")
        due  = row["due_date"].strftime("%d %b %Y")
        st.markdown(f"{icon} **{row['period_label']}** — Due: `{due}` · Amount: {fmt_m(row['amount_aud'])} · Status: **{row['status']}**")

    st.divider()
    export_sc = statutory.copy()
    export_sc["due_date"] = export_sc["due_date"].dt.strftime("%d %b %Y")
    st.download_button("Export Statutory Obligations Register", to_csv_bytes(export_sc), "statutory_compliance.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 8 — SAP TRANSFORMATION
# ══════════════════════════════════════════════════════════════════════════════

elif page == "SAP Integration":
    page_header("SAP Dual-Run Validation", "Automated legacy ↔ S/4HANA comparison · Migration readiness scoring")

    st.info("**How to use:** Run `python generate_csv.py` to generate `data/sap_legacy_extract.csv` as a simulated legacy extract, then upload it below — or supply your own real export.")

    legacy_file = st.file_uploader("Upload Legacy SAP Extract (.csv)", type="csv", key="legacy")
    if legacy_file is None:
        legacy_path = DATA_DIR / "sap_legacy_extract.csv"
        if legacy_path.exists():
            legacy_df = pd.read_csv(legacy_path)
            st.caption("Using auto-generated `data/sap_legacy_extract.csv`")
        else:
            st.warning("No legacy extract found. Run `python generate_csv.py` first.")
            legacy_df = None
    else:
        legacy_df = pd.read_csv(legacy_file)

    current_df = load_csv("sap_ledger.csv")
    if legacy_df is None:
        st.stop()
    current_df["ledger_id"] = current_df["ledger_id"].astype(str)
    legacy_df["ledger_id"]  = legacy_df["ledger_id"].astype(str)
    current_df["amount"]    = pd.to_numeric(current_df["amount"], errors="coerce")
    legacy_df["amount"]     = pd.to_numeric(legacy_df["amount"],  errors="coerce")

    merged = current_df[["ledger_id","project_id","gl_account","amount","vendor"]].merge(
        legacy_df[["ledger_id","gl_account","amount","_migration_flag"]].rename(
            columns={"gl_account":"legacy_gl","amount":"legacy_amount"}),
        on="ledger_id", how="outer", indicator=True)
    merged["variance"] = (merged["amount"] - merged["legacy_amount"]).round(2)

    fc  = "_migration_flag"
    ok_n    = int((merged[fc]=="OK").sum())          if fc in merged.columns else 0
    round_n = int((merged[fc]=="ROUNDING_DIFF").sum()) if fc in merged.columns else 0
    gl_n    = int((merged[fc]=="GL_REMAP").sum())    if fc in merged.columns else 0
    miss_n  = int((merged[fc]=="MISSING_IN_NEW").sum()) if fc in merged.columns else 0
    new_only = int((merged["_merge"]=="left_only").sum())
    total    = max(len(merged), 1)
    mr       = ok_n / total * 100

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Records",    str(total))
    c2.metric("✅ Clean Matches", str(ok_n))
    c3.metric("⚠ GL Remaps",     str(gl_n),    delta_color="inverse")
    c4.metric("🔢 Rounding",      str(round_n), delta_color="inverse")
    c5.metric("❌ Missing",       str(miss_n + new_only), delta_color="inverse")
    c6.metric("Match Rate",       f"{mr:.1f}%",
              delta="✅ Go-live ready" if mr >= 95 else ("⚠ Resolve issues" if mr >= 85 else "❌ Not ready"),
              delta_color="normal" if mr >= 95 else "inverse")

    if mr >= 95:   st.success(f"Migration match rate {mr:.1f}% — system is ready for go-live review.")
    elif mr >= 85: st.warning(f"Migration match rate {mr:.1f}% — issues must be resolved before go-live.")
    else:          st.error(f"Migration match rate {mr:.1f}% — critical gaps detected. Do not proceed.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Issue Category Breakdown")
        issue_d = {"Clean Match": ok_n, "GL Remap": gl_n, "Rounding": round_n, "Missing": miss_n+new_only}
        fig, ax = plt.subplots(figsize=(6, 3.5))
        bars = ax.bar(issue_d.keys(), issue_d.values(), color=[GREEN, AMBER, BLUE_MID, RED], width=0.55)
        ax.bar_label(bars, padding=3, fontsize=9, color=CHARCOAL)
        style_ax(ax, ylabel="Record Count")
        plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        st.markdown("#### Match Rate")
        st.metric("Migration Match Rate", f"{mr:.1f}%",
                  delta="Target: 95% for go-live sign-off",
                  delta_color="normal" if mr >= 95 else "inverse")
        st.progress(mr / 100)
        color_label = "🟢 Ready" if mr >= 95 else ("🟡 Issues to resolve" if mr >= 85 else "🔴 Critical gaps")
        st.markdown(f"**Status:** {color_label}")

    st.divider()
    exceptions = merged[merged.get(fc, pd.Series("OK", index=merged.index)) != "OK"].copy() if fc in merged.columns else pd.DataFrame()
    if not exceptions.empty:
        st.markdown("#### Exception Detail — Resolve Before Go-Live")
        exc_display = exceptions[["ledger_id","project_id","gl_account","legacy_gl","amount",
                                   "legacy_amount","variance","_migration_flag","vendor"]].copy().reset_index(drop=True)
        exc_display["project_id"] = exc_display["project_id"].astype(str)
        exc_display.columns = ["Ledger ID","Project ID","GL Account","Legacy GL",
                                "S/4HANA Amount","Legacy Amount","Variance","Migration Status","Vendor"]
        _amt_exc = ["S/4HANA Amount", "Legacy Amount", "Variance"]
        st.dataframe(
            style_dollars(exc_display.set_index("Ledger ID"), _amt_exc),
            use_container_width=True,
        )
        st.download_button("Export Exception Report", to_csv_bytes(exceptions), "migration_exceptions.csv", "text/csv")
    else:
        st.success("No exceptions — all records matched.")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 11 — REVENUE & POC
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Revenue & POC":
    page_header("Revenue & POC", "Percentage of Completion · Earned Revenue · EAC vs Budget · All figures ex-GST · AUD")

    if "contract_value" not in projects.columns or "eac" not in projects.columns:
        st.warning("Projects data is missing contract_value / EAC columns. Run `python generate_csv.py` then restart the app.")
        st.stop()

    proj_f = projects[projects["project_id"].isin(proj_ids)].copy()
    exp_f  = fe(expenses)

    # AASB 15 §98: cost-to-cost uses costs incurred for work performed (accrual basis).
    # Approved + Paid + Pending all represent work performed — invoice received or certified.
    # On Hold excluded: disputed invoices where performance is not yet confirmed.
    ap_eligible = exp_f[exp_f["status"].isin(["Approved", "Paid", "Pending"])]
    ap_by_proj = ap_eligible.groupby("project_id")["amount"].sum().reset_index(name="ap_costs")

    # Accruals: Posted only, and exclude any that have already reversed (reversal_date ≤ today).
    _today_ts = pd.Timestamp.today().normalize()
    acc_active = accruals[accruals["status"].eq("Posted") & accruals["project_id"].isin(proj_ids)].copy()
    if "reversal_date" in acc_active.columns:
        acc_active["_rev_dt"] = pd.to_datetime(acc_active["reversal_date"], errors="coerce")
        acc_active = acc_active[acc_active["_rev_dt"].isna() | (acc_active["_rev_dt"] > _today_ts)]
    acc_posted = acc_active.groupby("project_id")["amount"].sum().reset_index(name="accrual_costs")

    # Merge into project table
    poc_df = proj_f.merge(ap_by_proj, on="project_id", how="left")
    poc_df = poc_df.merge(acc_posted, on="project_id", how="left")
    poc_df[["ap_costs", "accrual_costs"]] = poc_df[["ap_costs", "accrual_costs"]].fillna(0)

    poc_df["actual_costs"]   = poc_df["ap_costs"] + poc_df["accrual_costs"]
    poc_df["poc"]            = poc_df["actual_costs"] / poc_df["eac"].replace(0, 1)
    poc_df["poc"]            = poc_df["poc"].clip(0, 1)
    poc_df["revenue_earned"] = poc_df["poc"] * poc_df["contract_value"]
    poc_df["eac_vs_budget"]  = poc_df["eac"] - poc_df["project_budget"]
    poc_df["margin"]         = poc_df["contract_value"] - poc_df["eac"]
    poc_df["margin_pct"]     = poc_df["margin"] / poc_df["contract_value"].replace(0, 1) * 100

    # Summary metrics
    tot_contract  = poc_df["contract_value"].sum()
    tot_eac       = poc_df["eac"].sum()
    tot_earned    = poc_df["revenue_earned"].sum()
    tot_costs     = poc_df["actual_costs"].sum()
    tot_margin    = poc_df["margin"].sum()
    avg_poc       = poc_df["poc"].mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Contract Value",  fmt_m(tot_contract),  delta=f"{len(poc_df)} projects")
    c2.metric("Total EAC",             fmt_m(tot_eac),       delta=f"{fmt_m(tot_eac - poc_df['project_budget'].sum())} vs budget")
    c3.metric("Revenue Earned (POC)",  fmt_m(tot_earned),    delta=f"Avg POC {avg_poc:.1f}%")
    c4.metric("Actual Costs Incurred", fmt_m(tot_costs),     delta="AP + Accruals ex-GST")
    c5.metric("Gross Margin (Contract − EAC)", fmt_m(tot_margin),
              delta=f"{tot_margin / max(tot_contract, 1) * 100:.1f}% of contract",
              delta_color="normal" if tot_margin >= 0 else "inverse")

    st.divider()
    st.markdown("#### POC by Project")
    st.caption(
        "POC = Actual Costs (AP invoices + Posted accruals) ÷ EAC · "
        "Revenue Earned = POC × Contract Value · "
        "EAC starts at project_budget and is updated with approved variations. · "
        "AASB 15 §98: AP costs limited to Approved/Paid status (uninstalled materials excluded). "
        "Reversed accruals (reversal_date ≤ today) excluded from cost base."
    )

    for _, row in poc_df.sort_values("poc", ascending=False).iterrows():
        poc_pct  = row["poc"] * 100
        icon     = "🟢" if poc_pct < 70 else ("🟡" if poc_pct < 90 else "🔴")
        eac_flag = " ⚠ EAC > Budget" if row["eac_vs_budget"] > 0 else ""
        with st.expander(f"{icon} {row['project_name']}  —  POC: {poc_pct:.1f}%  ·  Earned: {fmt_m(row['revenue_earned'])}{eac_flag}"):
            cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
            cc1.metric("Contract Value",    fmt_m(row["contract_value"]))
            cc2.metric("EAC",              fmt_m(row["eac"]),
                       delta=f"{fmt_m(row['eac_vs_budget'])} vs budget",
                       delta_color="inverse" if row["eac_vs_budget"] > 0 else "normal")
            cc3.metric("Actual Costs",     fmt_m(row["actual_costs"]),
                       delta=f"AP {fmt_m(row['ap_costs'])} + Acc {fmt_m(row['accrual_costs'])}")
            cc4.metric("POC",              f"{poc_pct:.1f}%")
            cc5.metric("Revenue Earned",   fmt_m(row["revenue_earned"]))
            cc6.metric("Gross Margin",     fmt_m(row["margin"]),
                       delta=f"{row['margin_pct']:.1f}%",
                       delta_color="normal" if row["margin"] >= 0 else "inverse")
            st.progress(min(row["poc"], 1.0), text=f"{poc_pct:.1f}% complete · Client type: {row.get('client_type', 'N/A')}")

    st.divider()
    st.markdown("#### Portfolio Revenue Curve — Earned vs Contract Value")

    fig, ax = plt.subplots(figsize=(10, 4))
    names_short = poc_df["project_name"].str.split("—").str[0].str.strip().str[:22]
    x = range(len(poc_df))
    ax.bar(x, poc_df["contract_value"] / 1e6, color=GREY_LIGHT, width=0.6, label="Contract Value")
    ax.bar(x, poc_df["revenue_earned"] / 1e6, color=BLUE, width=0.6, alpha=0.85, label="Revenue Earned (POC)")
    ax.set_xticks(list(x)); ax.set_xticklabels(names_short, rotation=20, ha="right", fontsize=7.5)
    style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
    ax.legend(fontsize=8)
    plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    st.divider()
    st.markdown("#### Monthly Revenue Recognition Curve — AASB 15 Over-Time Recognition")
    st.caption(
        "Incremental revenue recognised per period = (POC_this − POC_last) × Contract Value. "
        "Each bar represents new revenue earned in that month only — not cumulative. "
        "X-axis capped at each project's end date."
    )
    _fcst_f = forecasts[forecasts["project_id"].isin(proj_ids)].copy()
    if not _fcst_f.empty and "site_progress_pct" in _fcst_f.columns:
        _fcst_f = _fcst_f.merge(
            poc_df[["project_id","contract_value","end_date"]], on="project_id", how="left"
        )
        if "end_date" in _fcst_f.columns:
            _fcst_f["end_date"] = pd.to_datetime(_fcst_f["end_date"], errors="coerce")
            _fcst_f = _fcst_f[_fcst_f["forecast_date"] <= _fcst_f["end_date"]]

        fig, ax = plt.subplots(figsize=(11, 4))
        _colors = [BLUE, AMBER, GREEN, RED, CHARCOAL, GREY]
        for i, (pid, grp) in enumerate(_fcst_f.groupby("project_id")):
            grp = grp.sort_values("forecast_date").reset_index(drop=True)
            cv  = grp["contract_value"].iloc[0]
            # Incremental revenue = delta POC × contract value, capped at contract value
            poc_pct = (grp["site_progress_pct"] / 100).clip(0, 1)
            prev    = poc_pct.shift(1, fill_value=0)
            grp["rev_incremental"] = ((poc_pct - prev) * cv).clip(lower=0)
            _pname = poc_df.loc[poc_df["project_id"] == pid, "project_name"].iloc[0].split("—")[0].strip()[:22]
            ax.bar(grp["forecast_date"], grp["rev_incremental"] / 1e6,
                   width=20, color=_colors[i % len(_colors)], alpha=0.75, label=_pname)
        style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
        ax.legend(fontsize=7.5, ncol=2, loc="upper right")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        plt.xticks(rotation=20, ha="right", fontsize=7.5)
        plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()
    else:
        st.info("No forecast data available to build revenue curve.")

    st.download_button("Export POC Summary", to_csv_bytes(poc_df[[
        "project_name","contract_value","eac","project_budget","eac_vs_budget",
        "ap_costs","accrual_costs","actual_costs","poc","revenue_earned","margin","margin_pct"
    ]]), "revenue_poc.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 12 — AR & COLLECTIONS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "AR & Collections":
    page_header("AR & Collections", "Progress claims · DSO analysis · Outstanding balances · Retention tracking · AUD")

    if ar_inv.empty:
        st.warning("No AR data loaded. Run `python generate_csv.py` then restart the app to populate this page.")
        st.stop()

    # Safely select only available project columns
    _proj_cols = ["project_id", "project_name"]
    for _c in ("client_type", "dso_days", "retention_rate"):
        if _c in projects.columns:
            _proj_cols.append(_c)
    ar_f = ar_inv[ar_inv["project_id"].isin(proj_ids)].merge(projects[_proj_cols], on="project_id", how="left")
    if "client_type"    not in ar_f.columns: ar_f["client_type"]    = "N/A"
    if "dso_days"       not in ar_f.columns: ar_f["dso_days"]       = 0
    if "retention_rate" not in ar_f.columns: ar_f["retention_rate"] = 0.05

    if ar_f.empty:
        st.info("No AR claims for the selected project. Progress claims exist for Collins Arch and Victorian Heart Hospital only.")
        st.stop()

    total_claimed    = ar_f["claim_amount"].sum()
    total_retention  = ar_f["retention_withheld"].sum()
    total_paid       = ar_f["paid_amount"].sum()
    total_outstanding = ar_f["outstanding"].sum()
    overdue_n        = int((ar_f["status"] == "Overdue").sum())
    issued_n         = int((ar_f["status"] == "Issued").sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Claimed (ex-GST)",    fmt_m(total_claimed))
    c2.metric("Retention Withheld",        fmt_m(total_retention), delta="5% per contract")
    c3.metric("Collected",                 fmt_m(total_paid),      delta_color="normal")
    c4.metric("Outstanding (incl. GST)",   fmt_m(total_outstanding),
              delta=f"{issued_n} Issued · {overdue_n} Overdue",
              delta_color="inverse" if overdue_n > 0 else "off")
    c5.metric("Collection Rate",           f"{total_paid / max(total_claimed, 1) * 100:.0f}%",
              delta="Paid / Claimed",      delta_color="normal")

    st.divider()
    st.markdown("#### Progress Claims — All Projects")
    st.caption(
        "Claim Amount is ex-GST. Retention Withheld = Claim Amount × retention_rate. "
        "Net Claim = Claim Amount less retention. GST is 10% of Net Claim. "
        "Due Date = Claim Date + DSO days per client type (Government 30 days, Private 45 days)."
    )

    STATUS_COLOR = {"Paid": "🟢", "Issued": "🟡", "Overdue": "🔴", "Disputed": "🔴"}
    for pid, grp in ar_f.groupby("project_id"):
        proj_row  = grp.iloc[0]
        total_out = grp["outstanding"].sum()
        icon      = "🟢" if total_out == 0 else ("🔴" if (grp["status"] == "Overdue").any() else "🟡")
        with st.expander(f"{icon} {proj_row['project_name']}  —  Outstanding: {fmt_m(total_out)}  ·  Client: {proj_row.get('client_type', 'N/A')}  ·  DSO: {int(proj_row.get('dso_days', 0))} days"):
            for _, claim in grp.iterrows():
                s_icon = STATUS_COLOR.get(claim["status"], "⚪")
                cd_str = claim["claim_date"].strftime("%d %b %Y")
                dd_str = claim["due_date"].strftime("%d %b %Y")
                pd_str = str(claim["paid_date"]) if pd.notna(claim["paid_date"]) and str(claim["paid_date"]) not in ("", "NaT") else "—"
                with st.container():
                    cl1, cl2, cl3, cl4, cl5, cl6 = st.columns([2, 1, 1, 1, 1, 1])
                    cl1.markdown(f"{s_icon} **{claim['claim_number']}** — {claim['status']}")
                    cl2.markdown(f"Claim: {cd_str}")
                    cl3.markdown(f"Due: {dd_str}")
                    cl4.markdown(fmt_m(claim["claim_amount"]))
                    cl5.markdown(f"Ret: {fmt_m(claim['retention_withheld'])}")
                    cl6.markdown(f"O/S: {fmt_m(claim['outstanding'])}")
                if claim["status"] == "Overdue":
                    days_overdue = (pd.Timestamp.today() - claim["due_date"]).days
                    st.warning(f"⚠ {claim['claim_number']} overdue by {days_overdue} days — escalate to client.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Claims by Status")
        sc = ar_f.groupby("status")["total_incl_gst"].sum()
        s_colors = [GREEN if s == "Paid" else (AMBER if s == "Issued" else RED) for s in sc.index]
        fig, ax = plt.subplots(figsize=(5, 3.5))
        wedges, texts, auto = ax.pie(sc.values, labels=None, autopct="%1.0f%%", colors=s_colors,
                                     startangle=90, wedgeprops={"linewidth":1.5,"edgecolor":WHITE},
                                     pctdistance=0.72)
        for t in auto: t.set_fontsize(9); t.set_color(WHITE); t.set_fontweight("600")
        ax.legend([f"{s} — {fmt_m(v)}" for s, v in zip(sc.index, sc.values)],
                  loc="lower center", fontsize=7.5, bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)
        plt.tight_layout(pad=0.5); st.pyplot(fig, use_container_width=True); plt.close()

    with col2:
        st.markdown("#### DSO Summary by Client Type")
        dso_grp = ar_f.groupby("client_type").agg(
            claims=("ar_id", "count"),
            total_claimed=("claim_amount", "sum"),
            outstanding=("outstanding", "sum"),
            dso_days=("dso_days", "first"),
        ).reset_index()
        dso_grp.columns = ["Client Type", "Claims", "Total Claimed", "Outstanding", "DSO (days)"]
        st.dataframe(style_dollars(dso_grp.set_index("Client Type"), ["Total Claimed", "Outstanding"]),
                     use_container_width=True)
        st.caption("DSO per contract terms: Government = 30 days · Private = 45 days.")

    st.divider()
    st.markdown("#### AR Aging Analysis — Outstanding Balances")
    st.caption("Days overdue calculated from due_date. Only Issued/Overdue claims included.")

    _ar_today = pd.Timestamp.today().normalize()
    _ar_outstanding = ar_f[ar_f["outstanding"] > 0].copy()
    if not _ar_outstanding.empty:
        _ar_outstanding["days_overdue"] = (_ar_today - _ar_outstanding["due_date"]).dt.days.clip(lower=0)

        def _aging_bucket(d):
            if d <= 0:   return "Current (not yet due)"
            if d <= 30:  return "1–30 days"
            if d <= 60:  return "31–60 days"
            if d <= 90:  return "61–90 days"
            return "90+ days"

        _ar_outstanding["aging_bucket"] = _ar_outstanding["days_overdue"].apply(_aging_bucket)
        _bucket_order = ["Current (not yet due)", "1–30 days", "31–60 days", "61–90 days", "90+ days"]
        _bucket_colors = [GREEN, BLUE, AMBER, AMBER, RED]

        aging_grp = (
            _ar_outstanding.groupby("aging_bucket")
            .agg(claims=("ar_id", "count"), outstanding=("outstanding", "sum"))
            .reindex(_bucket_order).fillna(0).reset_index()
        )
        aging_grp.columns = ["Bucket", "Claims", "Outstanding (AUD)"]

        col_ag1, col_ag2 = st.columns([1, 1])
        with col_ag1:
            st.dataframe(
                style_dollars(aging_grp.set_index("Bucket"), ["Outstanding (AUD)"]),
                use_container_width=True,
            )
        with col_ag2:
            fig, ax = plt.subplots(figsize=(5, 3.5))
            _vals   = aging_grp["Outstanding (AUD)"].values
            _labels = aging_grp["Bucket"].values
            _bars   = ax.barh(_labels, _vals / 1e6, color=_bucket_colors, alpha=0.88)
            ax.bar_label(_bars, labels=[fmt_m(v) for v in _vals], padding=4, fontsize=7.5)
            style_ax(ax, xlabel="AUD (M)")
            ax.invert_yaxis()
            ax.xaxis.set_major_formatter(millions_fmt())
            plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

        _overdue_90 = aging_grp.loc[aging_grp["Bucket"] == "90+ days", "Outstanding (AUD)"].sum()
        if _overdue_90 > 0:
            st.error(f"⚠ {fmt_m(_overdue_90)} outstanding >90 days — escalate to legal/commercial team.")
    else:
        st.success("No outstanding AR balances — all claims collected.")

    st.download_button("Export AR Register", to_csv_bytes(ar_f[[
        "project_name","claim_number","claim_type","claim_date","claim_amount",
        "retention_withheld","net_claim","gst_amount","total_incl_gst",
        "due_date","paid_date","outstanding","status","client_type","dso_days"
    ]]), "ar_register.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 13 — RETENTION REGISTER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Retention Register":
    page_header("Retention Register", "Retention withheld · Practical completion · Release schedule · AUD")

    if ar_inv.empty:
        st.warning("No AR data loaded. Run `python generate_csv.py` then restart the app to populate this page.")
        st.stop()

    _ret_cols = ["project_id", "project_name", "end_date"]
    for _c in ("retention_rate", "practical_completion_date", "contract_value", "client_type"):
        if _c in projects.columns:
            _ret_cols.append(_c)
    ret_f = ar_inv[ar_inv["project_id"].isin(proj_ids)].merge(projects[_ret_cols], on="project_id", how="left")
    for _c in ("retention_rate",):
        if _c not in ret_f.columns: ret_f[_c] = 0.05
    for _c in ("practical_completion_date", "client_type"):
        if _c not in ret_f.columns: ret_f[_c] = ""
    for _c in ("contract_value",):
        if _c not in ret_f.columns: ret_f[_c] = 0.0

    if ret_f.empty:
        st.info("No retention data for the selected date range.")
        st.stop()

    _grp_keys = ["project_id","project_name","retention_rate",
                 "practical_completion_date","contract_value","end_date","client_type"]
    ret_by_proj = ret_f.groupby(_grp_keys, dropna=False).agg(
        total_claimed   = ("claim_amount", "sum"),
        total_retention = ("retention_withheld", "sum"),
    ).reset_index()
    ret_by_proj["max_retention"] = ret_by_proj["contract_value"] * ret_by_proj["retention_rate"]

    # Release retention if PC date is set AND in the past (treasury cash inflow event)
    _ret_today = pd.Timestamp.today().normalize()
    def _calc_released(row):
        pc = str(row.get("practical_completion_date", ""))
        if pc in ("", "nan", "NaT", "None"):
            return 0.0
        try:
            pc_dt = pd.Timestamp(pc)
            return row["total_retention"] if pc_dt <= _ret_today else 0.0
        except Exception:
            return 0.0

    ret_by_proj["released"] = ret_by_proj.apply(_calc_released, axis=1)
    ret_by_proj["held"]     = ret_by_proj["total_retention"] - ret_by_proj["released"]

    def _pc_achieved(row):
        pc = str(row.get("practical_completion_date", ""))
        return pc not in ("", "nan", "NaT", "None")

    total_held     = ret_by_proj["held"].sum()
    total_released = ret_by_proj["released"].sum()
    pc_achieved    = int(ret_by_proj.apply(_pc_achieved, axis=1).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Retention Withheld",  fmt_m(total_held),     delta=f"{len(ret_by_proj)} projects")
    c2.metric("Retention Released",        fmt_m(total_released), delta_color="normal")
    c3.metric("Retention Still Held",      fmt_m(total_held - total_released),
              delta="Held pending PC",     delta_color="inverse" if total_held > 0 else "normal")
    c4.metric("Practical Completion",      f"{pc_achieved} of {len(ret_by_proj)}",
              delta="PC achieved",         delta_color="normal" if pc_achieved > 0 else "off")

    st.divider()
    st.markdown("#### Retention by Project")
    st.caption(
        "Retention Rate = 5% of each progress claim (configurable per project). "
        "Maximum Retention Cap = Contract Value × Retention Rate. "
        "Retention is released on Practical Completion (PC) sign-off. "
        "Defects Liability Period (DLP) typically 12 months from PC."
    )

    for _, row in ret_by_proj.iterrows():
        pc       = str(row.get("practical_completion_date", ""))
        pc_done  = pc not in ("", "nan", "NaT", "None")
        icon     = "🟢" if pc_done else ("🟡" if row["held"] > 0 else "⚪")
        pc_label = f"PC: {pc}" if pc_done else "PC: Pending"
        with st.expander(f"{icon} {row['project_name']}  —  Held: {fmt_m(row['held'])}  ·  Rate: {row['retention_rate']*100:.0f}%  ·  {pc_label}"):
            rc1, rc2, rc3, rc4, rc5 = st.columns(5)
            rc1.metric("Total Claimed",       fmt_m(row["total_claimed"]))
            rc2.metric("Retention Withheld",  fmt_m(row["total_retention"]))
            rc3.metric("Max Retention Cap",   fmt_m(row["max_retention"]),
                       delta=f"{row['retention_rate']*100:.0f}% × contract value")
            rc4.metric("Released",            fmt_m(row["released"]),
                       delta="On PC sign-off" if pc_done else "Pending PC",
                       delta_color="normal" if pc_done else "off")
            rc5.metric("Currently Held",      fmt_m(row["held"]),
                       delta="DLP applies after PC" if pc_done else "Until PC",
                       delta_color="off")
            if pc_done:
                st.success(f"Practical Completion achieved {pc} — retention release initiated. DLP 12 months to {pc[:4]}.")
            else:
                st.info(f"Practical Completion pending (scheduled completion: {row['end_date']}) — retention held until PC sign-off.")

    st.divider()
    st.markdown("#### Retention Liability Summary — Treasury Impact")
    st.caption(
        "Retention held by the client is a current asset (amounts owed to Lendlease). "
        "Release timing is a treasury event — affects cash inflow forecasting."
    )
    ret_chart = ret_by_proj[["project_name","total_retention","released","held"]].copy()
    ret_chart["project_name"] = ret_chart["project_name"].str.split("—").str[0].str.strip().str[:22]
    fig, ax = plt.subplots(figsize=(10, 3.5))
    x = range(len(ret_chart))
    ax.bar(x, ret_chart["total_retention"] / 1e6, color=GREY_LIGHT, width=0.6, label="Total Withheld")
    ax.bar(x, ret_chart["held"] / 1e6, color=AMBER, width=0.6, alpha=0.85, label="Still Held")
    ax.bar(x, ret_chart["released"] / 1e6, color=GREEN, width=0.6, alpha=0.85, label="Released")
    ax.set_xticks(list(x)); ax.set_xticklabels(ret_chart["project_name"], rotation=20, ha="right", fontsize=7.5)
    style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
    ax.legend(fontsize=8)
    plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    st.download_button("Export Retention Register", to_csv_bytes(ret_by_proj[[
        "project_name","contract_value","retention_rate","max_retention",
        "total_claimed","total_retention","released","held","practical_completion_date","end_date"
    ]]), "retention_register.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 14 — WIP REPORT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "WIP Report":
    page_header("WIP Report", "Work in Progress — Revenue Earned vs Billings to Date · Underbilled asset / Overbilled liability · AUD")

    if "contract_value" not in projects.columns or "eac" not in projects.columns:
        st.warning("Projects data is missing contract_value / EAC columns. Run `python generate_csv.py` then restart the app.")
        st.stop()

    proj_f    = projects[projects["project_id"].isin(proj_ids)].copy()
    exp_f     = fe(expenses)

    # Accrual basis: Approved + Paid + Pending all represent work performed.
    # On Hold excluded — disputed, performance not confirmed.
    _wip_ap_elig = exp_f[exp_f["status"].isin(["Approved", "Paid", "Pending"])]
    ap_by_proj  = _wip_ap_elig.groupby("project_id")["amount"].sum().reset_index(name="ap_costs")
    _wip_today  = pd.Timestamp.today().normalize()
    _wip_acc    = accruals[accruals["status"].eq("Posted") & accruals["project_id"].isin(proj_ids)].copy()
    if "reversal_date" in _wip_acc.columns:
        _wip_acc["_rev_dt"] = pd.to_datetime(_wip_acc["reversal_date"], errors="coerce")
        _wip_acc = _wip_acc[_wip_acc["_rev_dt"].isna() | (_wip_acc["_rev_dt"] > _wip_today)]
    acc_posted  = _wip_acc.groupby("project_id")["amount"].sum().reset_index(name="accrual_costs")
    # Billings = gross claim_amount (AASB 15: revenue is gross value of work performed).
    # Retention is a payment timing difference — not a reduction in earned value.
    billings_df = (
        ar_inv[ar_inv["project_id"].isin(proj_ids)]
        .groupby("project_id")["claim_amount"].sum().reset_index(name="billings_to_date")
    )

    wip_df = proj_f.merge(ap_by_proj, on="project_id", how="left")
    wip_df = wip_df.merge(acc_posted, on="project_id", how="left")
    wip_df = wip_df.merge(billings_df, on="project_id", how="left")
    wip_df[["ap_costs","accrual_costs","billings_to_date"]] = wip_df[["ap_costs","accrual_costs","billings_to_date"]].fillna(0)

    wip_df["actual_costs"]   = wip_df["ap_costs"] + wip_df["accrual_costs"]
    wip_df["poc"]            = (wip_df["actual_costs"] / wip_df["eac"].replace(0, 1)).clip(0, 1)
    wip_df["revenue_earned"] = wip_df["poc"] * wip_df["contract_value"]
    wip_df["wip"]            = wip_df["revenue_earned"] - wip_df["billings_to_date"]
    wip_df["wip_type"]       = wip_df["wip"].apply(lambda v: "Underbilled" if v >= 0 else "Overbilled")

    total_earned    = wip_df["revenue_earned"].sum()
    total_billings  = wip_df["billings_to_date"].sum()
    total_wip       = wip_df["wip"].sum()
    underbilled_n   = int((wip_df["wip"] >= 0).sum())
    overbilled_n    = int((wip_df["wip"] < 0).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue Earned (POC)",   fmt_m(total_earned),   delta="Earned via % completion")
    c2.metric("Billings to Date",       fmt_m(total_billings), delta="Gross claims raised")
    c3.metric("Net WIP",                fmt_m(total_wip),
              delta="Underbilled asset" if total_wip >= 0 else "Overbilled liability",
              delta_color="normal" if total_wip >= 0 else "inverse")
    c4.metric("Underbilled Projects",   str(underbilled_n),    delta="Asset (earn > bill)",   delta_color="normal")
    c5.metric("Overbilled Projects",    str(overbilled_n),     delta="Liability (bill > earn)", delta_color="inverse" if overbilled_n > 0 else "normal")

    st.info(
        "**WIP = Revenue Earned (POC × Contract Value) − Billings to Date (gross progress claims)**  \n"
        "Billings use gross claim_amount — retention is a payment timing difference, not a revenue reduction (AASB 15).  \n"
        "**Underbilled (positive WIP)** → revenue recognised exceeds invoices raised — Contract Asset on balance sheet.  \n"
        "**Overbilled (negative WIP)** → invoices raised exceed revenue earned — Contract Liability on balance sheet.  \n"
        "Retention withheld is tracked separately as a non-current receivable (GL-1210) until Practical Completion.  \n"
        "Early-stage overbilling is normal in Tier 1 construction — mobilisation payments and front-loaded schedules create contract liabilities that reverse as POC catches up to billings."
    )

    st.divider()
    st.markdown("#### WIP by Project")

    for _, row in wip_df.dropna(subset=["wip","revenue_earned","billings_to_date","poc"]).sort_values("wip", ascending=False).iterrows():
        poc_pct   = row["poc"] * 100
        wip_val   = row["wip"]
        icon      = "🟢" if wip_val >= 0 else "🔴"
        wip_label = "Underbilled Asset" if wip_val >= 0 else "Overbilled Liability"
        with st.expander(f"{icon} {row['project_name']}  —  WIP: {fmt_m(wip_val)}  ·  {wip_label}  ·  POC: {poc_pct:.1f}%"):
            wc1, wc2, wc3, wc4, wc5, wc6 = st.columns(6)
            wc1.metric("Contract Value",   fmt_m(row["contract_value"]))
            wc2.metric("EAC",              fmt_m(row["eac"]))
            wc3.metric("Actual Costs",     fmt_m(row["actual_costs"]),
                       delta=f"POC {poc_pct:.1f}%")
            wc4.metric("Revenue Earned",   fmt_m(row["revenue_earned"]))
            wc5.metric("Billings to Date", fmt_m(row["billings_to_date"]))
            wc6.metric("WIP",              fmt_m(wip_val),
                       delta=wip_label,
                       delta_color="off")
            st.progress(min(row["poc"], 1.0), text=f"POC: {poc_pct:.1f}%")

    st.divider()
    st.markdown("#### WIP Waterfall — Revenue Earned vs Billings to Date")
    st.caption(
        "Grey = matched base (min of earned/billed) · "
        "Green gap bar = Underbilled asset (revenue > billings) · "
        "Red gap bar = Overbilled liability (billings > revenue)"
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    names_short = wip_df["project_name"].str.split("—").str[0].str.strip().str[:22]
    x = list(range(len(wip_df)))
    bar_w = 0.55
    for i, row in enumerate(wip_df.itertuples()):
        rev   = row.revenue_earned / 1e6
        bill  = row.billings_to_date / 1e6
        base  = min(rev, bill)
        gap   = abs(rev - bill)
        gap_c = GREEN if row.wip >= 0 else RED
        ax.bar(i, base, width=bar_w, color=GREY_LIGHT)
        ax.bar(i, gap,  width=bar_w, bottom=base, color=gap_c, alpha=0.85)
        # Narrow blue marker line showing billings level
        ax.plot([i - bar_w * 0.38, i + bar_w * 0.38], [bill, bill],
                color=BLUE, lw=2.2, solid_capstyle="butt", zorder=4)
        lbl = f"+{fmt_m(row.wip)}" if row.wip >= 0 else fmt_m(row.wip)
        ax.text(i, base + gap + 0.5, lbl, ha="center", va="bottom", fontsize=7, color=gap_c, fontweight="600")
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_els = [
        Patch(color=GREY_LIGHT, label="Matched base"),
        Patch(color=GREEN,      alpha=0.85, label="Underbilled asset"),
        Patch(color=RED,        alpha=0.85, label="Overbilled liability"),
        Line2D([0],[0], color=BLUE, lw=2.2, label="Billings to date"),
    ]
    ax.set_xticks(x); ax.set_xticklabels(names_short, rotation=20, ha="right", fontsize=7.5)
    style_ax(ax, ylabel="AUD (M)", yticker=millions_fmt())
    ax.legend(handles=legend_els, fontsize=7.5, ncol=4, loc="upper right")
    plt.tight_layout(pad=1.2); st.pyplot(fig, use_container_width=True); plt.close()

    # ── Physical POC Override — QS Monthly Survey ────────────────────────────
    st.divider()
    st.markdown("#### Physical POC Override — QS Monthly Survey")
    st.caption(
        "Tier 1 standard: QS walks the site ~20th of each month and certifies a physical % complete. "
        "Enter that figure below. The dashboard calculates the **Required Cost Accrual** — the "
        "'Subbie Lag' journal Finance must post to GL-2300 before period close so the ledger "
        "reflects physical reality, not just matched AP invoices."
    )

    _n  = len(wip_df)
    _nc = min(_n, 3)
    _input_cols = st.columns(_nc)
    _poc_overrides = {}
    for _i, (_, _row) in enumerate(wip_df.iterrows()):
        _default = round(float(_row["poc"]) * 100, 2)
        _entered = _input_cols[_i % _nc].number_input(
            _row["project_name"].split("—")[0].strip()[:24],
            min_value=0.0, max_value=100.0,
            value=_default, step=0.1, format="%.2f",
            key=f"phys_poc_{int(_row['project_id'])}",
            help=f"Cost-to-cost POC: {_default:.2f}% — enter QS-surveyed physical % to override",
        )
        _poc_overrides[int(_row["project_id"])] = _entered / 100.0

    _adj_rows = []
    for _, _row in wip_df.iterrows():
        _phys     = _poc_overrides.get(int(_row["project_id"]), float(_row["poc"]))
        _rev_p    = _phys * _row["contract_value"]
        _req_accr = max((_phys * _row["eac"]) - _row["actual_costs"], 0)
        _wip_p    = _rev_p - _row["billings_to_date"]
        _adj_rows.append({
            "Project":            _row["project_name"].split("—")[0].strip(),
            "Ledger POC":         f"{_row['poc']*100:.2f}%",
            "Physical POC":       f"{_phys*100:.2f}%",
            "Ledger Costs":       fmt_m(_row["actual_costs"]),
            "Revenue (Physical)": fmt_m(_rev_p),
            "Required Accrual":   fmt_m(_req_accr),
            "WIP (Physical)":     fmt_m(_wip_p),
        })

    st.dataframe(pd.DataFrame(_adj_rows).set_index("Project"), use_container_width=True)

    _total_accrual = sum(
        max((_poc_overrides.get(int(r["project_id"]), float(r["poc"])) * r["eac"]) - r["actual_costs"], 0)
        for _, r in wip_df.iterrows()
    )
    if _total_accrual > 100_000:
        st.warning(
            f"**Required month-end accrual: {fmt_m(_total_accrual)}** — work physically performed "
            f"but not yet invoiced by subcontractors (Subbie Lag). "
            f"Post to GL-2300 Accrued Expenses / GL-6100 Subcontract Costs before period close."
        )
    else:
        st.success("Ledger costs consistent with physical progress — no material accrual required.")

    st.download_button("Export WIP Report", to_csv_bytes(wip_df[[
        "project_name","contract_value","eac","ap_costs","accrual_costs","actual_costs",
        "poc","revenue_earned","billings_to_date","wip","wip_type"
    ]]), "wip_report.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 15 — CHART OF ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Chart of Accounts":
    page_header("Chart of Accounts", "SAP S/4HANA CoA — GL account register · Tax codes · BAS mapping · AASB/IFRS reference")

    if coa_df.empty:
        st.warning("Chart of Accounts not loaded. Run `python generate_csv.py` then restart the app.")
        st.stop()

    # ── Summary metrics ───────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total GL Accounts",    str(len(coa_df)))
    c2.metric("Balance Sheet",        str((coa_df["account_group"] == "Balance Sheet").sum()))
    c3.metric("Income Statement",     str((coa_df["account_group"] == "Income Statement").sum()))
    c4.metric("GST-Applicable (G11)", str((coa_df["tax_code"] == "G11").sum()),  delta="Input credits")
    c5.metric("GST-Free (G12)",       str((coa_df["tax_code"] == "G12").sum()),  delta="Government charges")

    st.info(
        "The Chart of Accounts is the master reference for all GL postings across SAP, accruals, "
        "AR invoices, and the SAP ledger. Every transaction in this dashboard maps to an account below. "
        "**Cost Center Required = Yes** means the posting must carry a project cost center (CC-MEL-01 etc.) "
        "for project accounting to work. Missing cost center = unallocated overhead."
    )

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        type_filter = st.multiselect("Account Type", options=sorted(coa_df["account_type"].unique()),
                                     default=sorted(coa_df["account_type"].unique()), key="coa_type")
    with col_f2:
        group_filter = st.multiselect("Statement", options=sorted(coa_df["account_group"].unique()),
                                      default=sorted(coa_df["account_group"].unique()), key="coa_grp")
    with col_f3:
        _tax_opts = sorted(coa_df["tax_code"].dropna().unique().tolist())
        tax_filter = st.multiselect("Tax Code", options=_tax_opts, default=_tax_opts, key="coa_tax")

    coa_filt = coa_df[
        coa_df["account_type"].isin(type_filter) &
        coa_df["account_group"].isin(group_filter) &
        coa_df["tax_code"].isin(tax_filter)
    ].copy()

    # ── Account type colour coding ────────────────────────────────────────────
    TYPE_ICON = {
        "Asset":     "🔵",
        "Liability": "🔴",
        "Equity":    "🟣",
        "Revenue":   "🟢",
        "Expense":   "🟡",
    }

    st.markdown("#### GL Account Register")
    st.caption("Colour: 🔵 Asset · 🔴 Liability · 🟣 Equity · 🟢 Revenue · 🟡 Expense")

    for grp_name, grp_df in coa_filt.groupby("account_group", sort=False):
        st.markdown(f"**{grp_name}**")
        for atype, atype_df in grp_df.groupby("account_type", sort=False):
            icon = TYPE_ICON.get(atype, "⚪")
            with st.expander(f"{icon} {atype}  —  {len(atype_df)} accounts", expanded=(atype in ("Revenue","Expense"))):
                disp = atype_df[["gl_account","account_name","normal_balance",
                                  "tax_code","bas_field","cost_center_required",
                                  "standard_ref","notes"]].copy()
                disp.columns = ["GL Account","Account Name","Normal Balance",
                                 "Tax Code","BAS Field","CC Required",
                                 "Standard","Notes"]
                st.dataframe(disp.set_index("GL Account"), use_container_width=True)

    st.divider()

    # ── Tax code → BAS field cross-reference ──────────────────────────────────
    st.markdown("#### Tax Code → BAS Field Mapping")
    st.caption("How each ATO tax code flows into your Business Activity Statement")

    bas_map = pd.DataFrame([
        {"Tax Code": "G1",  "Description": "GST on supplies (output tax)",         "BAS Field": "1A — GST Collected",   "Normal Balance": "Credit (liability)",  "Applies To": "Revenue GL accounts (progress claims, variations)"},
        {"Tax Code": "G11", "Description": "Non-capital purchases with GST (input)","BAS Field": "1B — Input Tax Credits","Normal Balance": "Debit (recoverable)", "Applies To": "Subcontractors, materials, plant, professional fees, T&E"},
        {"Tax Code": "G12", "Description": "GST-free purchases",                    "BAS Field": "N/A — not reported",   "Normal Balance": "N/A",                 "Applies To": "Government permits, regulatory fees, insurance, interest"},
        {"Tax Code": "N/A", "Description": "Outside GST scope / not applicable",    "BAS Field": "N/A",                  "Normal Balance": "N/A",                 "Applies To": "Payroll, tax, equity, intercompany, balance sheet non-trading"},
    ])
    st.dataframe(bas_map.set_index("Tax Code"), use_container_width=True)

    st.divider()

    # ── Posting validation — detect GL codes in transactions not in CoA ───────
    st.markdown("#### Posting Validation — GL Codes Used vs Chart of Accounts")
    st.caption("Any GL code appearing in transactions but NOT in the CoA indicates a miscoding or chart of accounts gap.")

    coa_codes   = set(coa_df["gl_account"].tolist())
    ledger_gls  = set(ledger["gl_account"].unique())
    accrual_gls = set(accruals["gl_account"].unique()) if "gl_account" in accruals.columns else set()
    ar_gls      = set(ar_inv["gl_account"].unique())   if "gl_account" in ar_inv.columns  else set()
    exp_gls     = set(expenses["gl_account"].unique()) if "gl_account" in expenses.columns else set()

    all_used    = ledger_gls | accrual_gls | ar_gls | exp_gls
    unmatched   = sorted(all_used - coa_codes)
    matched_n   = len(all_used - set(unmatched))

    vc1, vc2, vc3 = st.columns(3)
    vc1.metric("GL Codes in Transactions", str(len(all_used)))
    vc2.metric("Matched to CoA",           str(matched_n),       delta_color="normal")
    vc3.metric("Unmatched (not in CoA)",   str(len(unmatched)),
               delta="Investigate" if unmatched else "Clean",
               delta_color="inverse" if unmatched else "normal")

    if unmatched:
        st.error(f"**{len(unmatched)} GL code(s) in transactions do not exist in the Chart of Accounts:** {', '.join(unmatched)}")
        st.caption("Action: Add these accounts to chart_of_accounts.csv, or correct the GL code on the transaction.")
    else:
        st.success("All GL codes in transactions are validated against the Chart of Accounts.")

    st.divider()
    st.download_button("Export Chart of Accounts", to_csv_bytes(coa_df), "chart_of_accounts.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 10 — DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Data Management":
    st.markdown("## Data Management")
    st.success("Page loaded — scroll up if you don't see content below.")
    st.caption("Upload live data · Download templates · Column format reference")
    st.divider()

    st.markdown(
        "Download a template, populate it from your source system, "
        "then upload via **Upload Data Sources** in the sidebar. "
        "Column names must not be renamed."
    )

    # ── Step 1: Download templates ─────────────────────────────────────────────
    st.markdown("### Step 1 — Download Templates")

    FILE_META = {
        "projects.csv":             ("SAP PS / Procore",                   "Project register — includes contract_value, EAC, client_type, DSO, retention_rate"),
        "site_expenses.csv":        ("Trade Accounts / SAP Concur",        "AP invoices — subcontractors via trade account, T&E via Concur"),
        "sap_ledger.csv":           ("SAP S/4HANA FBL3N",                  "GL line items — must include tax_code and gst_amount columns"),
        "cash_forecasts.csv":       ("TMS / Treasury Excel",               "Monthly cash in/out forecast per project"),
        "audit_log.csv":            ("Audit Management / Risk Register",   "Open items, issues, and compliance events"),
        "bank_facilities.csv":      ("ANZ / NAB / Westpac Banking",        "Facility limits, drawn amounts, covenants"),
        "weekly_cashflow.csv":      ("TMS / Treasury Excel",               "Rolling 8-week actual vs forecast cash position"),
        "bank_accounts.csv":        ("Bank feeds / BAI2 / SWIFT MT940",    "Daily account balances across all operating accounts"),
        "statutory_compliance.csv": ("ATO / SRO — internal register",      "BAS, IAS, payroll tax, super SG obligations"),
        "accruals.csv":             ("SAP S/4HANA — FB50 / Month-End Register", "Month-end accruals — work completed, invoice not yet received"),
        "ar_invoices.csv":          ("SAP FBL5N / Procore Billing",        "AR progress claims, retention withheld, payment status"),
        "chart_of_accounts.csv":    ("SAP S/4HANA — FS00",                 "Master GL account register — CoA foundation for all postings"),
    }

    for fname, tmpl in TEMPLATES.items():
        meta = FILE_META.get(fname, (tmpl.get("system",""), ""))
        with st.expander(f"{fname}   —   {meta[1]}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.caption(f"Source: {meta[0]}")
                st.caption(f"Export path: {tmpl.get('path','')}")
                df_tmpl = tmpl["df"]
                col_rows = []
                for col in df_tmpl.columns:
                    sample = str(df_tmpl[col].iloc[0]) if len(df_tmpl) > 0 else ""
                    col_rows.append({"Column": col, "Sample Value": sample, "Type": str(df_tmpl[col].dtype)})
                st.dataframe(pd.DataFrame(col_rows).set_index("Column"), use_container_width=True, height=200)
            with c2:
                st.download_button(
                    f"Download {fname}",
                    df_tmpl.to_csv(index=False).encode(),
                    file_name=fname,
                    mime="text/csv",
                    key=f"dm_{fname}",
                    use_container_width=True,
                )

    # ── Step 2: Upload ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Step 2 — Upload Your Data")
    st.markdown("Use the **Upload Data Sources** expander in the **left sidebar** to upload files. The dashboard updates immediately.")

    upload_ref = {
        "projects.csv":             "SAP PS / Procore",
        "site_expenses.csv":        "Trade Account + SAP Concur",
        "sap_ledger.csv":           "SAP FBL3N (include Tax Code column)",
        "cash_forecasts.csv":       "TMS / Treasury Excel",
        "bank_facilities.csv":      "Bank portal / Finance team",
        "weekly_cashflow.csv":      "TMS / Treasury Excel",
        "bank_accounts.csv":        "Bank feeds / BAI2",
        "audit_log.csv":            "Audit / Risk register",
        "statutory_compliance.csv": "ATO portal / SRO",
        "accruals.csv":             "SAP S/4HANA — FB50 / Month-End Accruals Register",
        "ar_invoices.csv":          "SAP FBL5N / Procore Billing — Progress Claims",
        "chart_of_accounts.csv":    "SAP S/4HANA — FS00 / Chart of Accounts Export",
    }

    ref_df = pd.DataFrame([{"File": k, "Source System": v} for k, v in upload_ref.items()])
    st.dataframe(ref_df.set_index("File"), use_container_width=True)
    st.caption("Uploaded files are session-only. To persist, replace files in the /data folder.")
