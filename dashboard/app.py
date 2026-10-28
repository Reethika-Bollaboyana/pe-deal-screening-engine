"""Ridgeline Capital deal screening dashboard (Phase 9).

Run from the project folder with:  streamlit run dashboard/app.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ridgeline Deal Screen", layout="wide")

st.title("Ridgeline Capital: B2B Services Deal Screen")
st.caption("Fictional $2B private equity fund screening U.S.-listed business services companies. "
           "Data: SEC EDGAR filings; share prices as of 2026-10-23. Portfolio project, not investment advice.")

# ---------- Data ----------
review = pd.read_csv("data/processed/universe_review.csv")
gate = pd.read_csv("data/processed/size_gate_results.csv")
valuation = pd.read_csv("data/processed/valuation.csv")

# Companies kept after the manual review (see docs/manual_review.md)
REVIEWED = ["WLDN", "QNST", "LQDT", "ONT", "TISI", "ADV"]
LEVERAGE_LIMIT = 3.0


def status(row):
    """Where each size-qualified company ended up in the screen."""
    if row["ticker"] not in REVIEWED:
        return "Excluded (manual review)"
    if row["net_leverage"] >= LEVERAGE_LIMIT:
        return "Fails leverage limit"
    return "Eligible"


valuation["status"] = valuation.apply(status, axis=1)
eligible = valuation[valuation["status"] == "Eligible"]

# ---------- Funnel ----------
st.subheader("The screening funnel")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("SIC universe", len(review))
c2.metric("U.S. filers with data", int(review["in_universe"].sum()))
c3.metric("Pass size gate", int((gate["size_gate"] == "PASS").sum()))
c4.metric("Pass manual review", len(REVIEWED))
c5.metric("Eligible (leverage < 3.0x)", len(eligible))

# ---------- Comparison table ----------
st.subheader("Size-qualified companies")
table = pd.DataFrame({
    "Ticker": valuation["ticker"],
    "Company": valuation["company_name"],
    "Status": valuation["status"],
    "Revenue ($M)": (valuation["revenue"] / 1000).round(0),
    "EBITDA ($M)": (valuation["ebitda"] / 1000).round(1),
    "EBITDA margin (%)": (valuation["ebitda_margin"] * 100).round(1),
    "Revenue CAGR 3-yr (%)": (valuation["revenue_cagr_3y"] * 100).round(1),
    "Net leverage (x)": valuation["net_leverage"].round(2),
    "EV/EBITDA (x)": valuation["ev_to_ebitda"].round(1),
})
st.dataframe(table.sort_values(["Status", "Ticker"]), hide_index=True)
st.caption("EBITDA = reported operating income + D&A (not company-adjusted). Net leverage includes finance leases. "
           "Valuation uses closing prices on 2026-10-23 and cover-page share counts.")