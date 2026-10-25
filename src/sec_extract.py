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

        # Keep periods ending near the company's fiscal year-end date
        df = df[df["end"].apply(lambda d: days_from_year_end(d, month, day) <= tolerance_days)]

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


def extract_company(data, fye_mmdd):
    """Extract every variable in TAGS for one company, in long format (one row per year and variable)."""
    pieces = []
    for variable, tags in TAGS.items():
        table = get_annual_values(data, tags, fye_mmdd)
        if table is not None and not table.empty:
            pieces.append(table.assign(variable=variable))

    if not pieces:
        return None
    return pd.concat(pieces, ignore_index=True)
