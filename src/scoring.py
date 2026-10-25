"""Ridgeline scoring model: converts screening metrics into a weighted score out of 100.

Each metric is scored on a fixed scale tied to the mandate (not relative to peers):
0 points at `zero_point`, 100 points at `full_point`, linear in between, capped at both ends.
Missing values score 0 (conservative). Methodology: docs/scoring_methodology.md
"""

import metrics as mx

# metric: (value scoring 0, value scoring 100, weight)
SCORING = {
    "revenue_cagr_3y":   (0.00, 0.10, 20),
    "ebitda_margin":     (0.05, 0.20, 20),
    "fcf_conversion_3y": (0.00, 0.90, 20),
    "capex_intensity":   (0.06, 0.00, 10),   # lower is better
    "net_leverage":      (4.0,  0.0,  10),   # lower is better
    "ev_to_ebitda":      (18.0, 8.0,  20),   # lower (cheaper) is better
}

LEVERAGE_LIMIT = 3.0   # hard filter: above this, a company cannot be recommended


def add_three_year_cash_conversion(results):
    """3-year FCF conversion: total FCF over 3 years / total EBITDA over 3 years."""
    r = mx.add_lagged(results, ["fcf", "ebitda"], 1)
    r = mx.add_lagged(r, ["fcf", "ebitda"], 2)
    fcf_3y = r["fcf"] + r["fcf_lag1"] + r["fcf_lag2"]
    ebitda_3y = r["ebitda"] + r["ebitda_lag1"] + r["ebitda_lag2"]
    r["fcf_conversion_3y"] = mx.safe_divide(fcf_3y, ebitda_3y)
    return r


def linear_score(values, zero_point, full_point):
    """Map values onto 0-100: zero_point -> 0, full_point -> 100, capped; missing -> 0."""
    scaled = (values - zero_point) / (full_point - zero_point)
    return (scaled.clip(0, 1) * 100).fillna(0)


def score_companies(df, scoring=SCORING, leverage_limit=LEVERAGE_LIMIT):
    """Add a score for each metric, a weighted total score, and the hard-filter result."""
    s = df.copy()
    total_weight = sum(weight for _, _, weight in scoring.values())
    s["total_score"] = 0.0
    for metric, (zero_point, full_point, weight) in scoring.items():
        s[f"score_{metric}"] = linear_score(s[metric], zero_point, full_point)
        s["total_score"] += s[f"score_{metric}"] * weight / total_weight
    s["eligible"] = s["net_leverage"] < leverage_limit
    return s.sort_values("total_score", ascending=False)
