# SiteCapital Construction Treasury Intelligence Platform

An enterprise-grade treasury dashboard built in Python and Streamlit, simulating the finance operations of a Tier 1 Australian construction company (Lendlease / Multiplex scale). Designed to demonstrate the full scope of a Construction Treasury Accountant role — from daily reconciliation to CFO-level liquidity risk reporting.

---

## What It Does

This platform bridges the gap between raw construction project data and executive decision-making. It covers the four core responsibilities of a Tier 1 treasury function:

| Responsibility | Module |
|---|---|
| Capital preservation & liquidity management | Cash & Covenant · Executive Pulse |
| Month-end reconciliation (SAP vs site) | Reconciliation |
| Vendor & AP risk management | Vendor Risk |
| Statutory compliance & audit governance | Statutory Compliance · Audit Register |
| ERP migration & system transformation | SAP Transformation Validation |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard & UI | Python 3.11 · Streamlit |
| Data processing | Pandas · NumPy |
| Visualisation | Matplotlib (institutional palette — no rainbow charts) |
| Data generation | Pure Python · CSV · SQLite |
| Deployment | Streamlit Community Cloud (free) |

No external APIs. No paid services. Runs fully offline.

---

## Project Structure

```
finance_portfolio_project/
├── app.py                  # Main dashboard — 8 pages
├── generate_csv.py         # Realistic synthetic data generator
├── requirements.txt        # Python dependencies
└── data/                   # Auto-generated CSV files (git-ignored)
    ├── projects.csv
    ├── site_expenses.csv
    ├── sap_ledger.csv
    ├── cash_forecasts.csv
    ├── audit_log.csv
    ├── bank_facilities.csv
    ├── weekly_cashflow.csv
    ├── statutory_compliance.csv
    └── sap_legacy_extract.csv
```

---

## How to Run

**Step 1 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Generate the data**
```bash
python generate_csv.py
```

This creates 8 realistic CSV files in `data/` — modelled on a Lendlease-scale portfolio of 6 active projects across Melbourne (CBD, Southbank, Clayton), Sydney (Pyrmont), and Perth.

**Step 3 — Launch the dashboard**
```bash
streamlit run app.py
```

Opens at `http://localhost:8501` in your browser.

---

## Dashboard Pages

### Executive Pulse
The CFO's morning brief. Zero tables. Five headline KPIs, a natural-language Executive Summary generated from live data, an 8-week rolling cash burn chart (actual vs forecast), and a facility utilisation strip across all five banking relationships.

> *"Cash position is stable at $48.5M, with $155M of undrawn facility headroom across ANZ, NAB, Westpac, and CBA. No immediate liquidity action is required."*

### Portfolio Health
Project-by-project budget utilisation with S-curve burn profiling. Exception cards highlight projects above 85% utilisation with traffic-light colour coding. No project is buried in a table — each surfaces as a card with its own status badge.

### Reconciliation
SAP S/4HANA ledger vs site expenses. Variances above $5,000 are flagged as material gaps. Flagged exception lines (WBS mismatches, unapproved variations, coding errors) are surfaced separately for month-end clear-down.

### Cash & Covenant
The risk management core of the platform. Per-facility covenant tests (minimum cash, gearing ratio) against five banking facilities (ANZ RCF, NAB BG Line, Westpac Overdraft, CBA Bonding, ANZ Project Finance). A 200-path Monte Carlo simulation projects the 16-week liquidity runway against the covenant floor.

### Vendor Risk
Spend concentration analysis across the approved subcontractor and supplier panel. Flags AP exceptions (duplicate payment risk, unapproved variations, WBS coding mismatches) before the payment run.

### Audit Register
Open items prioritised by urgency — Bank Guarantee expiry, budget overrun warnings, missing supporting documents. Filtered by module and status. Exportable for governance sign-off.

### Statutory Compliance
ATO lodgement calendar covering BAS (quarterly), IAS (monthly PAYG withholding), payroll tax by state (VIC, NSW, WA), and Superannuation SG payment schedule. Traffic-light status per obligation type — Lodged / Pending / Overdue / Scheduled. Amounts derived from payroll register extract and project budget proxy. Exportable obligations register.

### SAP Transformation Validation
Dual-run comparison between a legacy SAP extract and the current S/4HANA ledger. Categorises every record (Clean Match / GL Remap / Rounding Diff / Missing) and produces a migration match rate score. A 95% threshold is required for go-live sign-off.

---

## Data Design

The synthetic data is engineered to reflect real Tier 1 construction finance:

- **S-curve burn profiles** — expenses follow mobilisation → ramp-up → peak construction → fit-out → close-out phases, not random uniform distributions
- **Real vendor panel** — John Holland, Hickory Group, Kane Constructions, Boral, Holcim, AECOM, Coates Hire, Turner & Townsend
- **Realistic invoice ranges** — subcontract invoices $120K–$1.8M; professional services $12K–$220K
- **Targeted anomalies** — deliberate reconciliation gaps, unapproved variations, cash crunch periods, and covenant stress scenarios for demo purposes
- **Banking facilities** — modelled on real ANZ/NAB/Westpac project finance terms including gearing covenants and minimum cash clauses

---

## Replacing Synthetic Data with Real Data

Every page supports CSV upload via the sidebar. To connect your own data:

1. Export from your source system (SAP, Concur, Oracle, etc.) to CSV
2. Match the column headers to the templates in `data/`
3. Upload via **Data Sources** in the sidebar — the dashboard reloads instantly

No code changes required.

---

## Design Principles

This dashboard was built around one question: *what does a CFO actually need to see in 30 seconds?*

- **Institutional palette only** — navy `#1B3A6B`, charcoal `#2C3E50`, white. Colour signals meaning (green = compliant, amber = monitor, red = act now). No decorative colour.
- **No rainbow charts** — every chart uses 1–2 tones. Visual noise is cognitive load.
- **Natural language summaries** — each page opens with an interpretive sentence, not a label. Data without interpretation is just noise.
- **Exception-first layout** — the most critical item on each page is always the first thing the eye lands on. Good news is understated; risk is prominent.
- **Flow of insight** — navigation follows a CFO's decision tree: group position → project detail → reconciliation → covenant risk → vendor risk → governance → system health.

---

## Author

Built as a portfolio demonstration of treasury, finance operations, and data engineering skills for a Tier 1 construction finance context.
