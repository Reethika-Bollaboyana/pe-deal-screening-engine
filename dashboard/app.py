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

# ---------- Scoring (uses src/scoring.py, the same model as Phase 7) ----------
import sys

import altair as alt

sys.path.append("src")
import scoring  # noqa: E402

LABELS = {
    "revenue_cagr_3y": "Revenue growth (3-yr CAGR)",
    "ebitda_margin": "EBITDA margin",
    "fcf_conversion_3y": "FCF conversion (3-yr)",
    "capex_intensity": "CapEx intensity (lower is better)",
    "net_leverage": "Net leverage (lower is better)",
    "ev_to_ebitda": "EV/EBITDA (cheaper is better)",
}

with st.sidebar:
    st.header("Scoring weights")
    st.caption("Base case = the weights in docs/scoring_methodology.md. Move a slider to test a different view.")
    weights = {metric: st.slider(LABELS[metric], 0, 50, base_weight, step=5)
               for metric, (_, _, base_weight) in scoring.SCORING.items()}

st.subheader("Scoring and ranking")
if sum(weights.values()) == 0:
    st.warning("Set at least one weight above zero.")
    st.stop()

all_metrics = pd.read_csv("data/processed/metrics.csv")
with_cash_conv = scoring.add_three_year_cash_conversion(all_metrics)
latest = valuation[valuation["ticker"].isin(REVIEWED)][["cik", "ticker", "fiscal_year", "ev_to_ebitda"]]
candidates = latest.merge(with_cash_conv.drop(columns="ticker"), on=["cik", "fiscal_year"])

# Same scales as the base model; only the weights change
config = {m: (zero, full, weights[m]) for m, (zero, full, _) in scoring.SCORING.items()}
ranked = scoring.score_companies(candidates, scoring=config)

top = ranked[ranked["eligible"]].iloc[0]
st.markdown(f"**Top eligible company with these weights: {top['ticker']}** (score {top['total_score']:.1f} out of 100)")

chart_data = pd.DataFrame({
    "Ticker": ranked["ticker"],
    "Score": ranked["total_score"].round(1),
    "Status": ranked["eligible"].map({True: "Eligible", False: "Fails leverage limit"}),
})
chart = (
    alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Weighted score (0-100)"),
        y=alt.Y("Ticker:N", sort="-x", title=None, scale=alt.Scale(paddingInner=0.35)),
        color=alt.Color("Status:N",
                        scale=alt.Scale(domain=["Eligible", "Fails leverage limit"],
                                        range=["#2a78d6", "#b5b3ad"]),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=["Ticker", "Score", "Status"],
    )
        .properties(height=48 * len(chart_data))
)
st.altair_chart(chart, use_container_width=True)

breakdown = ranked[["ticker", "eligible", "total_score"] + [f"score_{m}" for m in scoring.SCORING]].copy()
breakdown.columns = ["Ticker", "Eligible", "Total score"] + [LABELS[m] for m in scoring.SCORING]
st.dataframe(breakdown.round(1), hide_index=True)
st.caption("Each metric is scored 0-100 on a fixed scale tied to the mandate, then weighted. "
           "Companies above 3.0x net leverage are scored but cannot be recommended.")