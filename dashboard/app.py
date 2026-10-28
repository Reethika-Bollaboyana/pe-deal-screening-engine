"""Ridgeline Capital deal screening dashboard (Phase 9).

Run from the project folder with:  streamlit run dashboard/app.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ridgeline Deal Screen", layout="wide")

st.title("Ridgeline Capital: B2B Services Deal Screen")
st.caption("Fictional $2B private equity fund screening U.S.-listed business services companies. "
           "Data: SEC EDGAR filings; share prices as of 2026-10-23. Portfolio project, not investment advice.")

valuation = pd.read_csv("data/processed/valuation.csv")

st.subheader("Size-qualified companies")
st.dataframe(valuation[["ticker", "company_name", "fiscal_year", "revenue", "ebitda", "ev_to_ebitda"]])
