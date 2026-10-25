# SQL Screening Queries

Queries run against `data/ridgeline_screen.db` (built by `notebooks/06_sql_database.ipynb`).

| Table | One row is | Key |
|---|---|---|
| `companies` | one company | `cik` |
| `financials` | one company, one fiscal year (raw data and metrics, $000s) | `cik`, `fiscal_year` |
| `size_gate` | one company's size gate result | `cik` |
| `market_data` | one company's share price on one date | `cik`, `price_date` |

| Query | Purpose | Validation |
|---|---|---|
| `01_size_gate.sql` | Ridgeline's size gate: latest fiscal year ≥ 2025 and EBITDA $40–100M | Returns the same 8 companies as the pandas size gate |
| `02_mandate_scorecard.sql` | PASS / FAIL / N/A on each core mandate criterion, with a count of criteria passed | Matches hand calculations; Mistras agrees with the Excel Scorecard |

Thresholds follow `docs/investment_mandate.md`. Net leverage < 3.0x is treated as a hard filter; other criteria are preferences.
