"""Calculate Ridgeline's screening metrics from extracted annual data.

Formulas follow docs/data_dictionary.md and are validated against the
Mistras Group answer key (excel/mistras_answer_key.xlsx).
"""

import numpy as np
import pandas as pd

TAX_RATE = 0.25               # NOPAT tax assumption (mandate, section 7)
INCLUDE_FINANCE_LEASES = 1    # 1 = count finance leases as debt (mandate, section 7)

RAW_VARIABLES = ["revenue", "operating_income", "interest_expense", "diluted_shares",
                 "d_and_a", "cfo", "capex", "acquisitions_paid", "cash",
                 "short_term_debt", "long_term_debt", "long_term_debt_total",
                 "finance_lease_current", "finance_lease_noncurrent",
                 "stockholders_equity", "accounts_receivable", "goodwill"]


def to_wide(financials):
    """Long format -> one row per company and fiscal year, one column per variable."""
    wide = financials.pivot_table(index=["cik", "ticker", "fiscal_year"], columns="variable",
                                  values="value_000s", aggfunc="first").reset_index()
    wide.columns.name = None
    for col in RAW_VARIABLES:          # make sure every variable has a column
        if col not in wide.columns:
            wide[col] = np.nan
    return wide


def safe_divide(numerator, denominator):
    """Divide, leaving a blank (NM) where the denominator is zero or negative."""
    return numerator / denominator.where(denominator > 0)


def add_lagged(df, columns, years):
    """Add each column's value from `years` fiscal years earlier, matched by company and year."""
    lagged = df[["cik", "fiscal_year"] + columns].copy()
    lagged["fiscal_year"] = lagged["fiscal_year"] + years
    lagged = lagged.rename(columns={c: f"{c}_lag{years}" for c in columns})
    return df.merge(lagged, on=["cik", "fiscal_year"], how="left")


def compute_metrics(wide, tax_rate=TAX_RATE, include_finance_leases=INCLUDE_FINANCE_LEASES):
    """Calculate every screening metric in docs/data_dictionary.md."""
    m = wide.copy()

    # --- Debt ---
    # Preferred: current + non-current debt. Fallback: total borrowings (LongTermDebt tag),
    # used only when neither split figure is reported. A missing line counts as zero,
    # but companies with no debt tags at all are flagged for manual checking.
    split_missing = m["short_term_debt"].isna() & m["long_term_debt"].isna()
    borrowings = m["short_term_debt"].fillna(0) + m["long_term_debt"].fillna(0)
    borrowings = borrowings.where(~split_missing, m["long_term_debt_total"].fillna(0))
    m["debt_tags_missing"] = split_missing & m["long_term_debt_total"].isna()

    finance_leases = m["finance_lease_current"].fillna(0) + m["finance_lease_noncurrent"].fillna(0)
    m["total_debt"] = borrowings + include_finance_leases * finance_leases
    # No balance sheet at all for that year -> debt is unknown, not zero
    m.loc[m["stockholders_equity"].isna(), "total_debt"] = np.nan

    # --- Building blocks ---
    m["ebitda"] = m["operating_income"] + m["d_and_a"]
    m["fcf"] = m["cfo"] - m["capex"]
    m["net_debt"] = m["total_debt"] - m["cash"]
    m["nopat"] = m["operating_income"] * (1 - tax_rate)
    m["invested_capital"] = m["total_debt"] + m["stockholders_equity"] - m["cash"]

    # --- Single-year metrics ---
    m["ebitda_margin"] = safe_divide(m["ebitda"], m["revenue"])
    m["fcf_conversion"] = safe_divide(m["fcf"], m["ebitda"])
    m["capex_intensity"] = safe_divide(m["capex"], m["revenue"])
    m["net_leverage"] = safe_divide(m["net_debt"], m["ebitda"])
    m["dso"] = safe_divide(m["accounts_receivable"], m["revenue"]) * 365

    # --- Growth ---
    m = add_lagged(m, ["revenue"], 1)
    m = add_lagged(m, ["revenue"], 3)
    m["revenue_growth_yoy"] = safe_divide(m["revenue"], m["revenue_lag1"]) - 1
    m["revenue_cagr_3y"] = safe_divide(m["revenue"], m["revenue_lag3"]) ** (1 / 3) - 1

    # --- ROIC on average invested capital (with and without goodwill) ---
    m = add_lagged(m, ["invested_capital", "goodwill"], 1)
    avg_ic = (m["invested_capital"] + m["invested_capital_lag1"]) / 2
    avg_ic_ex_gw = ((m["invested_capital"] - m["goodwill"])
                    + (m["invested_capital_lag1"] - m["goodwill_lag1"])) / 2
    m["roic"] = safe_divide(m["nopat"], avg_ic)
    m["roic_ex_goodwill"] = safe_divide(m["nopat"], avg_ic_ex_gw)

    # --- Diagnostic flags ---
    m = add_lagged(m, ["ebitda_margin"], 1)
    m = add_lagged(m, ["ebitda_margin"], 2)
    margins_3y = m[["ebitda_margin", "ebitda_margin_lag1", "ebitda_margin_lag2"]]
    m["ebitda_margin_range_3y"] = margins_3y.max(axis=1, skipna=False) - margins_3y.min(axis=1, skipna=False)

    m["acquisitions_paid_filled"] = m["acquisitions_paid"].fillna(0)   # no line = no acquisitions
    m = add_lagged(m, ["acquisitions_paid_filled"], 1)
    m = add_lagged(m, ["acquisitions_paid_filled"], 2)
    acq_3y = (m["acquisitions_paid_filled"] + m["acquisitions_paid_filled_lag1"].fillna(0)
              + m["acquisitions_paid_filled_lag2"].fillna(0))
    m["acq_spend_to_revenue"] = safe_divide(acq_3y, m["revenue"])

    return m

def compute_valuation(latest, prices, shares=None):
    """Market cap, enterprise value, and EV/EBITDA ($000s).

    latest: one row per company (latest fiscal year metrics)
    prices: columns ticker, close_price
    shares: columns cik, shares_out_000s (cover page); if missing, average diluted shares are used
    """
    v = latest.merge(prices, on="ticker", how="left")
    if shares is not None:
        v = v.merge(shares, on="cik", how="left")
    else:
        v["shares_out_000s"] = np.nan

    v["shares_used_000s"] = v["shares_out_000s"].fillna(v["diluted_shares"])
    v["shares_basis"] = np.where(v["shares_out_000s"].notna(), "cover page", "avg diluted (fallback)")
    v["market_cap"] = v["close_price"] * v["shares_used_000s"]      # $ x thousands of shares = $000s
    v["enterprise_value"] = v["market_cap"] + v["net_debt"]
    v["ev_to_ebitda"] = safe_divide(v["enterprise_value"], v["ebitda"])
    return v

def apply_adjustments(financials, adjustments):
    """Override or add values from a documented manual-adjustments file (long format).

    Each adjustment replaces any extracted value for the same company, fiscal year,
    and variable. Adjusted rows are tagged "MANUAL", with the source kept in `accn`.
    """
    keys = ["cik", "fiscal_year", "variable"]
    flagged = financials.merge(adjustments[keys], on=keys, how="left", indicator=True)
    kept = financials[(flagged["_merge"] == "left_only").to_numpy()]
    manual = adjustments.assign(tag="MANUAL", accn=adjustments["source"])
    manual = manual[[c for c in financials.columns if c in manual.columns]]
    return pd.concat([kept, manual], ignore_index=True)