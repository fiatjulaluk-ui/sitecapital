"""
SiteCapital — Construction Treasury Intelligence Platform
Enterprise-grade CFO dashboard — UX-focused, psychologically framed.
"""

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
[data-testid="stSidebar"] .stRadio label {{
    color: #FFFFFF !important;
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
/* Metric cards — equal height via min-height covering label+value+delta */
div[data-testid="metric-container"],
[data-testid="stMetric"] {{
    background-color: {CARD_BG} !important;
    border-radius: 8px;
    padding: 14px 18px !important;
    border-left: 4px solid #8DC63F !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    min-height: 108px !important;
    box-sizing: border-box !important;
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
    border-color: {CHART_SPINE} !important;
}}
[data-testid="stExpander"] summary span {{
    color: {TEXT_MAIN} !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(v):   return f"${v:,.0f}"
def fmt_m(v): return f"${v/1e6:,.1f}M"
def to_csv_bytes(df): return df.to_csv(index=False).encode()

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

@st.cache_data
def load_all(p=None, e=None, l=None, f=None, a=None, fac=None, wcf=None, ba=None, sc=None):
    projects   = load_csv("projects.csv",             p)
    expenses   = load_csv("site_expenses.csv",        e)
    ledger     = load_csv("sap_ledger.csv",           l)
    forecasts  = load_csv("cash_forecasts.csv",       f)
    audit      = load_csv("audit_log.csv",            a)
    facilities = load_csv("bank_facilities.csv",      fac)
    weekly_cf  = load_csv("weekly_cashflow.csv",      wcf)
    bank_accts = load_csv("bank_accounts.csv",        ba)
    statutory  = load_csv("statutory_compliance.csv", sc)

    expenses["booking_date"]   = pd.to_datetime(expenses["booking_date"])
    ledger["posting_date"]     = pd.to_datetime(ledger["posting_date"])
    forecasts["forecast_date"] = pd.to_datetime(forecasts["forecast_date"])
    audit["event_date"]        = pd.to_datetime(audit["event_date"])
    weekly_cf["week_start"]    = pd.to_datetime(weekly_cf["week_start"])
    bank_accts["date"]         = pd.to_datetime(bank_accts["date"])
    statutory["due_date"]      = pd.to_datetime(statutory["due_date"])

    return projects, expenses, ledger, forecasts, audit, facilities, weekly_cf, bank_accts, statutory


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
        "Executive Pulse", "Portfolio Health", "Reconciliation",
        "Cash & Covenant", "Vendor Risk", "Audit Register",
        "Statutory Compliance", "SAP Transformation"
    ], index=1)

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

try:
    projects, expenses, ledger, forecasts, audit, facilities, weekly_cf, bank_accts, statutory = load_all(
        p_up, e_up, l_up, f_up, a_up, fac_up, wcf_up, ba_up, sc_up
    )
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

with st.sidebar:
    st.divider()
    pnames   = ["All Projects"] + projects["project_name"].tolist()
    selected = st.selectbox("Filter Project", pnames)

    all_dates = pd.concat([expenses["booking_date"], ledger["posting_date"]])
    mn, mx = all_dates.min().date(), all_dates.max().date()
    dr     = st.date_input("Date Range", value=(mn, mx), min_value=mn, max_value=mx)
    d_from = pd.Timestamp(dr[0] if isinstance(dr, (list,tuple)) and len(dr)==2 else mn)
    d_to   = pd.Timestamp(dr[1] if isinstance(dr, (list,tuple)) and len(dr)==2 else mx)
    st.caption("As at 18 April 2026 · Confidential · All figures ex-GST")

# ── Filter helpers ────────────────────────────────────────────────────────────

proj_ids = (projects["project_id"].tolist() if selected == "All Projects"
            else projects.loc[projects["project_name"]==selected,"project_id"].tolist())

def fe(df): return df[df["project_id"].isin(proj_ids) & df["booking_date"].between(d_from, d_to)]
def fl(df): return df[df["project_id"].isin(proj_ids) & df["posting_date"].between(d_from, d_to)]
def ff(df): return df[df["project_id"].isin(proj_ids) & df["forecast_date"].between(d_from, d_to)]
def fa(df): return df[df["project_id"].isin(proj_ids)]


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
        exp_t = exp_f["amount"].sum()
        led_t = fl(ledger)["amount"].sum()
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
            s.append(f"Average weekly net cash: {fmt_m(avg_net)} (outflow). Covenant floor reached in ~**{weeks:.0f} weeks** at current rate.")
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


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — EXECUTIVE PULSE
# ══════════════════════════════════════════════════════════════════════════════

if page == "Executive Pulse":
    page_header("Executive Pulse", "Board & CFO view — consolidated group position · 18 April 2026 · All figures ex-GST")
    exec_summary(build_exec_summary("pulse"))

    total_budget = projects["project_budget"].sum()
    total_spent  = expenses["amount"].sum()
    headroom     = (facilities["limit_aud"] - facilities["drawn_aud"]).sum()
    open_audits  = int((fa(audit)["status"] == "Open").sum())
    actual_cf    = weekly_cf[weekly_cf["type"] == "Actual"]
    cash         = actual_cf["closing_balance"].iloc[-1] if not actual_cf.empty else 0
    spent_pct    = total_spent / total_budget * 100
    proj_risk    = int(len(
        expenses.groupby("project_id")["amount"].sum().reset_index(name="s")
        .merge(projects[["project_id","project_budget"]], on="project_id")
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

elif page == "Reconciliation":
    page_header("Reconciliation", "SAP S/4HANA ledger vs site expenses — variances > $5,000 highlighted")
    exec_summary(build_exec_summary("recon"))

    exp_f = fe(expenses)
    led_f = fl(ledger)
    ea = exp_f.groupby("project_id")["amount"].sum().reset_index(name="exp_total")
    la = led_f.groupby("project_id")["amount"].sum().reset_index(name="led_total")
    rc = ea.merge(la, on="project_id", how="outer").fillna(0)
    rc = rc.merge(projects[["project_id","project_name","project_budget"]], on="project_id")
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

    with st.expander("📋 GL Materiality Threshold Reference — AASB 1031 / IFRS", expanded=False):
        ref_df = pd.DataFrame([
            {"GL Account": gl, "Description": desc, "Materiality Threshold": f"{pct}% of GL balance",
             "Rationale": "High value / audit risk — tighter threshold" if pct <= 1.0
                          else ("Standard construction cost account" if pct <= 2.0
                                else "Low-risk, low-value account")}
            for gl, (desc, pct) in GL_MATERIALITY.items()
        ])
        st.dataframe(ref_df, use_container_width=True, hide_index=True)

    # Compare actual GL variance against threshold
    led_f_gl  = fl(ledger)
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
        col_config = {
            "Booking Date":  st.column_config.TextColumn("Booking Date",  width="small"),
            "Project ID":    st.column_config.TextColumn("Project ID",    width="small"),
            "Expense Type":  st.column_config.TextColumn("Expense Type",  width="small"),
            "Amount":        st.column_config.NumberColumn("Amount",      width="small", format="$%,.0f"),
            "Status":        st.column_config.TextColumn("Status",        width="small"),
            "Source System": st.column_config.TextColumn("Source System", width="small"),
        }
        st.dataframe(disp, column_config=col_config, use_container_width=True)
        st.download_button("Export Exception Lines", to_csv_bytes(flagged), "recon_exceptions.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — CASH & COVENANT
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Cash & Covenant":
    page_header("Cash & Covenant", "Liquidity headroom · Covenant compliance · 16-week runway simulation")
    exec_summary(build_exec_summary("covenant"))

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
    st.caption("Today's opening, receipts, payments, and closing balance across all group accounts · Ex-GST · AUD")

    today_str = "2026-04-18"
    today_accts = bank_accts[bank_accts["date"].dt.strftime("%Y-%m-%d") == today_str].copy()

    if not today_accts.empty:
        total_closing = today_accts["closing_balance"].sum()
        total_receipts = today_accts["receipts"].sum()
        total_payments = today_accts["payments"].sum()
        net_today = total_receipts - total_payments

        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("Total Cash (All Accounts)", fmt_m(total_closing))
        tc2.metric("Total Receipts Today",      fmt_m(total_receipts))
        tc3.metric("Total Payments Today",      fmt_m(total_payments))
        tc4.metric("Net Movement Today",        fmt_m(net_today),
                   delta_color="normal" if net_today >= 0 else "inverse")

        st.markdown("")
        disp = today_accts[["account_name","bank","bsb","account_type",
                             "opening_balance","receipts","payments","closing_balance"]].copy()
        disp["movement"] = disp["closing_balance"] - disp["opening_balance"]
        disp.columns = ["Account Name","Bank","BSB","Type",
                        "Opening Balance","Receipts","Payments","Closing Balance","Net Movement"]
        st.dataframe(
            disp,
            column_config={
                "Account Name":    st.column_config.TextColumn("Account Name",    width="medium"),
                "Bank":            st.column_config.TextColumn("Bank",            width="small"),
                "BSB":             st.column_config.TextColumn("BSB",             width="small"),
                "Type":            st.column_config.TextColumn("Type",            width="small"),
                "Opening Balance": st.column_config.NumberColumn("Opening Balance", format="$%,.0f"),
                "Receipts":        st.column_config.NumberColumn("Receipts",        format="$%,.0f"),
                "Payments":        st.column_config.NumberColumn("Payments",        format="$%,.0f"),
                "Closing Balance": st.column_config.NumberColumn("Closing Balance", format="$%,.0f"),
                "Net Movement":    st.column_config.NumberColumn("Net Movement",    format="$%,.0f"),
            },
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### 10-Day Rolling Balance by Account")
        fig, ax = plt.subplots(figsize=(10, 3.8))
        for _, grp in bank_accts.groupby("account_name"):
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
            path.append(path[-1] + avg_net * random.uniform(0.7, 1.3))
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


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — VENDOR RISK
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Vendor Risk":
    page_header("Vendor Risk", "Spend concentration · Flagged transactions · Payment status")
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
    status_styled = (
        status_df.set_index("vendor").style
        .format({c: "${:,.0f}" for c in amt_cols})
        .set_properties(subset=amt_cols, **{"text-align": "right"})
    )
    st.dataframe(status_styled, use_container_width=True)

    flagged = exp_f[exp_f["comment"].notna() & (exp_f["comment"] != "")].copy()
    if not flagged.empty:
        st.divider()
        st.markdown("#### ⚠ Flagged Vendor Exceptions — AP Review Required")
        risk = (flagged.groupby("vendor")
                .agg(flags=("comment","count"), value=("amount","sum"))
                .sort_values("flags", ascending=False).reset_index())
        risk.columns = ["Vendor", "Flag Count", "Flagged Value"]
        st.dataframe(
            risk,
            column_config={
                "Flag Count":   st.column_config.NumberColumn("Flag Count",   width="small"),
                "Flagged Value":st.column_config.NumberColumn("Flagged Value",width="small", format="$%,.0f"),
            },
            use_container_width=True,
        )
        st.download_button("Export Flagged Vendors", to_csv_bytes(flagged), "vendor_exceptions.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 6 — AUDIT REGISTER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Audit Register":
    page_header("Audit Register", "Open items prioritised by urgency · Filter by module and status")
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

elif page == "SAP Transformation":
    page_header("SAP Dual-Run Validation", "Automated legacy ↔ S/4HANA comparison · Migration readiness scoring")

    st.info("**How to use:** Run `python generate_csv.py` to generate `data/sap_legacy_extract.csv` as a simulated legacy extract, then upload it below — or supply your own real export.")

    legacy_file = st.file_uploader("Upload Legacy SAP Extract (.csv)", type="csv", key="legacy")
    if legacy_file is None:
        legacy_path = DATA_DIR / "sap_legacy_extract.csv"
        if legacy_path.exists():
            legacy_df = pd.read_csv(legacy_path)
            st.caption("Using auto-generated `data/sap_legacy_extract.csv`")
        else:
            st.warning("No legacy extract found. Run `python generate_csv.py` first."); st.stop()
    else:
        legacy_df = pd.read_csv(legacy_file)

    current_df = load_csv("sap_ledger.csv")
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
        exc_styled = (
            exc_display.set_index("Ledger ID").style
            .format({c: "${:,.0f}" for c in _amt_exc})
            .set_properties(subset=_amt_exc, **{"text-align": "right"})
        )
        st.dataframe(
            exc_styled,
            column_config={
                "Project ID":      st.column_config.TextColumn("Project ID",      width="small"),
                "GL Account":      st.column_config.TextColumn("GL Account",      width="small"),
                "Legacy GL":       st.column_config.TextColumn("Legacy GL",       width="small"),
                "Migration Status":st.column_config.TextColumn("Migration Status",width="small"),
            },
            use_container_width=True,
        )
        st.download_button("Export Exception Report", to_csv_bytes(exceptions), "migration_exceptions.csv", "text/csv")
    else:
        st.success("No exceptions — all records matched.")
