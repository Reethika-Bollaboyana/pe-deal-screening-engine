"""Extract annual financial data from SEC Company Facts (XBRL) files.

Used by the Ridgeline Capital deal screening engine. Validated against the
Mistras Group answer key (excel/mistras_answer_key.xlsx).
"""

import pandas as pd

# Each variable from docs/data_dictionary.md, with XBRL tags to try (in priority order)
TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "operating_income": ["OperatingIncomeLoss"],
    "interest_expense": ["InterestExpenseNonoperating", "InterestExpense", "InterestExpenseDebt"],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "d_and_a": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
                "DepreciationAmortizationAndAccretionNet"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "acquisitions_paid": ["PaymentsToAcquireBusinessesNetOfCashAcquired"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "short_term_debt": ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings"],
    "long_term_debt": ["LongTermDebtNoncurrent"],
    "finance_lease_current": ["FinanceLeaseLiabilityCurrent"],
    "finance_lease_noncurrent": ["FinanceLeaseLiabilityNoncurrent"],
    "stockholders_equity": ["StockholdersEquity"],
    "accounts_receivable": ["AccountsReceivableNetCurrent",
                            "AccountsReceivableExcludingAccruedInterestAfterAllowanceForCreditLossCurrent",
                            "ReceivablesNetCurrent"],
    "goodwill": ["Goodwill"],
}


def days_from_year_end(end_date, month, day):
    """Days between an end date and the nearest fiscal year-end (handles 52/53-week years)."""
    candidates = [pd.Timestamp(year=end_date.year + shift, month=month, day=day)
                  for shift in (-1, 0, 1)]
    return min(abs((end_date - c).days) for c in candidates)

def infer_fiscal_year_end(data):
    """Infer fiscal year-end (MMDD) from the latest full-year period reported in a 10-K."""
    latest = None
    for info in data.get("facts", {}).get("us-gaap", {}).values():
        for entries in info["units"].values():
            for e in entries:
                if e.get("form") == "10-K" and "start" in e:
                    start, end = pd.Timestamp(e["start"]), pd.Timestamp(e["end"])
                    if 350 <= (end - start).days <= 380 and (latest is None or end > latest):
                        latest = end
    return None if latest is None else latest.strftime("%m%d")

def get_annual_values(data, candidate_tags, fye_mmdd, tolerance_days=10):
    """One value per fiscal year (in thousands), combining candidate tags in priority order."""
    facts = data.get("facts", {}).get("us-gaap", {})
    month, day = int(fye_mmdd[:2]), int(fye_mmdd[2:])
    tables = []

    for priority, tag in enumerate(candidate_tags):
        if tag not in facts:
            continue
        units = facts[tag]["units"]
        unit_name = list(units.keys())[0]      # "USD" for money, "shares" for share counts
        df = pd.DataFrame(units[unit_name])

        df["end"] = pd.to_datetime(df["end"])
        df["filed"] = pd.to_datetime(df["filed"])
        df = df[df["form"] == "10-K"]

        # Income and cash flow items cover a period: keep full years only
        if "start" in df.columns:
            df["start"] = pd.to_datetime(df["start"])
            df = df[(df["end"] - df["start"]).dt.days.between(350, 380)]

                # Skip tags with no annual 10-K data left (avoids an empty-table quirk in pandas)
        if df.empty:
            continue

        # Keep periods ending near the company's fiscal year-end date
        near_end = df["end"].apply(lambda d: days_from_year_end(d, month, day) <= tolerance_days)
        df = df[near_end.astype(bool)]

        df["tag"] = tag
        df["priority"] = priority
        tables.append(df)

    if not tables:
        return None

    combined = pd.concat(tables)
    combined = combined.sort_values(["priority", "filed"], ascending=[True, False])
    combined = combined.drop_duplicates(subset="end", keep="first")

    combined["value_000s"] = combined["val"] / 1000
    # A year ending in early January (52/53-week calendars) belongs to the prior fiscal year
    combined["fiscal_year"] = (combined["end"] - pd.Timedelta(days=15)).dt.year
    return combined.sort_values("end")[["fiscal_year", "end", "value_000s", "tag", "accn"]]

def fallback_d_and_a(data, fye_mmdd):
    """D&A from components, for companies with no combined D&A tag.

    Rule (conservative): Depreciation + AmortizationOfIntangibleAssets.
    Other amortization (capitalized software, finance leases, financing costs)
    is excluded: it may already be inside Depreciation, or is not operating D&A.
    If there is no intangible amortization tag, Depreciation alone is used.
    """
    dep = get_annual_values(data, ["Depreciation"], fye_mmdd)
    if dep is None or dep.empty:
        return None

    result = dep[["fiscal_year", "end", "value_000s", "accn"]].copy()
    amort = get_annual_values(data, ["AmortizationOfIntangibleAssets"], fye_mmdd)
    if amort is not None and not amort.empty:
        amort = amort[["fiscal_year", "value_000s"]].rename(columns={"value_000s": "amort"})
        result = result.merge(amort, on="fiscal_year", how="left")
    else:
        result["amort"] = 0.0

    result["value_000s"] = result["value_000s"] + result["amort"].fillna(0)
    result["tag"] = "Depreciation + AmortizationOfIntangibleAssets"
    return result[["fiscal_year", "end", "value_000s", "tag", "accn"]]

def extract_company(data, fye_mmdd):
    """Extract every variable in TAGS for one company, in long format (one row per year and variable)."""
    pieces = []
    for variable, tags in TAGS.items():
        table = get_annual_values(data, tags, fye_mmdd)
        if table is not None and not table.empty:
            pieces.append(table.assign(variable=variable))

    # D&A fallback: fill only the fiscal years with no combined D&A tag
    fallback = fallback_d_and_a(data, fye_mmdd)
    if fallback is not None:
        reported = [p for p in pieces if p["variable"].iloc[0] == "d_and_a"]
        years_reported = set(reported[0]["fiscal_year"]) if reported else set()
        extra = fallback[~fallback["fiscal_year"].isin(years_reported)]
        if not extra.empty:
            pieces.append(extra.assign(variable="d_and_a"))

    if not pieces:
        return None
    return pd.concat(pieces, ignore_index=True)