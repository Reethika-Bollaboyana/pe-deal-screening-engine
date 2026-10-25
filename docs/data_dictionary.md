# Data Dictionary

This document defines every variable used in the Ridgeline Capital deal screening engine: what it means, where it comes from, and how calculated metrics are built. It is the single reference for both the Excel answer key (`excel/mistras_answer_key.xlsx`) and the Python code.

> Ridgeline Capital is a fictional fund created for this portfolio project. All company data comes from public SEC filings.

## Conventions

| Convention | Rule |
|---|---|
| Units | Dollar amounts stored in USD as provided by SEC XBRL data; the Excel answer key uses USD thousands, as shown in the 10-K |
| Percentages | Stored as decimals (0.15 = 15%) |
| Multiples | Stored as plain numbers (9.5 = 9.5x) |
| Period | Annual figures from Form 10-K (fiscal year) |
| History | 5 fiscal years collected where available |
| Missing data | Left blank, never filled with zero. A reported zero (line present, value shown as "—") is entered as 0 |
| Negative denominators | Ratios with zero or negative EBITDA are marked NM (not meaningful) |
| Sign convention | Cash outflows (CapEx, acquisitions) stored as positive numbers; formulas subtract them |
| Traceability | Every financial figure keeps the accession number of its source filing |
| D&A fallback | If no combined D&A tag is reported: Depreciation + Amortization of intangible assets only. Other amortization (capitalized software, finance leases, financing costs) is excluded because it may already be inside depreciation or relates to financing; this can only understate EBITDA. If no intangible amortization tag exists, depreciation alone is used |
| Tag fallbacks | Cash: total including restricted cash, if unrestricted cash is not reported (slightly overstates usable cash). Equity: total equity including noncontrolling interests, if parent equity is not reported (slightly overstates). Debt: total borrowings (LongTermDebt tag, including current portion, excluding leases), if current and non-current debt are not reported separately. Companies with no debt tags at all are flagged for manual checking |

## Table grain

| Table | One row equals |
|---|---|
| Company information | One company |
| Financial data | One company, one fiscal year |
| Market data | One company, one price date |

## 1. Raw financial data (source: SEC EDGAR, Form 10-K)

XBRL tags shown are the typical ones; companies vary, so tags are confirmed against actual data.

### Identifier fields

| Variable | Meaning | Units |
|---|---|---|
| `cik` | SEC Central Index Key; permanent company ID | Number (stored as text with leading zeros) |
| `fiscal_year` | Fiscal year covered | Year |
| `period_end_date` | Last day of the fiscal year | Date |
| `form_type` | Filing type (10-K) | Text |
| `accession_number` | Unique ID of the source filing | Text |
| `filed_date` | Date the filing was submitted | Date |

### Income statement

| Variable | Meaning | Typical XBRL tag |
|---|---|---|
| `revenue` | Total revenue | `Revenues` or `RevenueFromContractWithCustomerExcludingAssessedTax` |
| `operating_income` | Operating income (loss) | `OperatingIncomeLoss` |
| `interest_expense` | Interest expense (used in LBO phase) | `InterestExpense` |
| `diluted_shares` | Weighted-average diluted shares | `WeightedAverageNumberOfDilutedSharesOutstanding` |

### Cash flow statement

| Variable | Meaning | Typical XBRL tag |
|---|---|---|
| `d_and_a` | Depreciation and amortization | `DepreciationDepletionAndAmortization` or `DepreciationAndAmortization` |
| `cfo` | Net cash provided by operating activities | `NetCashProvidedByUsedInOperatingActivities` |
| `capex` | Purchases of property, plant and equipment | `PaymentsToAcquirePropertyPlantAndEquipment` |
| `acquisitions_paid` | Cash paid for acquisitions, net of cash acquired | `PaymentsToAcquireBusinessesNetOfCashAcquired` |

### Balance sheet

| Variable | Meaning | Typical XBRL tag |
|---|---|---|
| `cash` | Cash and cash equivalents | `CashAndCashEquivalentsAtCarryingValue` |
| `short_term_debt` | Short-term borrowings and current portion of long-term debt | `ShortTermBorrowings`, `LongTermDebtCurrent` |
| `long_term_debt` | Long-term debt, non-current | `LongTermDebtNoncurrent` |
| `finance_lease_current` | Finance lease obligations, current | `FinanceLeaseLiabilityCurrent` |
| `finance_lease_noncurrent` | Finance lease obligations, non-current | `FinanceLeaseLiabilityNoncurrent` |
| `stockholders_equity` | Total stockholders' equity attributable to the parent (excludes noncontrolling interest) | `StockholdersEquity` |
| `accounts_receivable` | Accounts receivable, net | `AccountsReceivableNetCurrent` |
| `goodwill` | Goodwill | `Goodwill` |

**Exclusions:** Operating lease liabilities are not collected and are never treated as debt. Purchases of intangible assets and equipment acquired through finance leases are not included in `capex`; they are noted as a limitation of free cash flow.

## 2. Market and valuation data

| Variable | Meaning | Source | Changes |
|---|---|---|---|
| `share_price` | Closing share price (or deal offer price, where stated) | Market data provider, or 8-K for announced deals | Daily |
| `price_date` | Date of the price | Same | Daily |
| `price_source` | Where the price came from | Recorded by us | Rarely |

## 3. Assumptions

| Parameter | Value | Notes |
|---|---|---|
| `tax_rate` | 25% | Approximates U.S. federal plus state tax; applied uniformly for NOPAT |
| `include_finance_leases` | 1 (yes) | Finance leases are contractual borrowing for equipment and are counted as debt by lenders |
| EBITDA definition | Reported operating income + D&A | Company-defined "Adjusted EBITDA" is not used |

## 4. Calculated metrics

### Intermediate calculations

| Variable | Formula |
|---|---|
| `ebitda` | `operating_income` + `d_and_a` |
| `fcf` | `cfo` − `capex` |
| `total_debt` | `short_term_debt` + `long_term_debt` + `include_finance_leases` × (`finance_lease_current` + `finance_lease_noncurrent`) |
| `net_debt` | `total_debt` − `cash` |
| `nopat` | `operating_income` × (1 − `tax_rate`) |
| `invested_capital` | `total_debt` + `stockholders_equity` − `cash` |
| `market_cap` | `share_price` × `diluted_shares` |
| `enterprise_value` | `market_cap` + `net_debt` |

### Screening metrics

| Variable | Formula | Mandate rule |
|---|---|---|
| `revenue_cagr_3y` | (`revenue` this year ÷ `revenue` 3 years earlier)^(1/3) − 1 | ≥ 5% |
| `ebitda_margin` | `ebitda` ÷ `revenue` | ≥ 12% |
| `fcf_conversion` | `fcf` ÷ `ebitda` | ≥ 70% |
| `capex_intensity` | `capex` ÷ `revenue` | < 3% |
| `net_leverage` | `net_debt` ÷ `ebitda` | < 3.0x |
| `roic` | `nopat` ÷ average(`invested_capital` this year, prior year) | Set after reviewing data |
| `roic_ex_goodwill` | `nopat` ÷ average(`invested_capital` − `goodwill`, this year and prior year) | Context only |
| `ev_to_ebitda` | `enterprise_value` ÷ `ebitda` | ≤ ~10x preferred; > ~13x too expensive |
| `ebitda_margin_range_3y` | Highest − lowest `ebitda_margin` over 3 years | Flag if > 5 percentage points |
| `dso` | `accounts_receivable` ÷ `revenue` × 365 | Flag if high or rising |
| `acq_spend_to_revenue` | 3-year sum of `acquisitions_paid` ÷ current `revenue` | Flag if significant |
| `passes_size_gate` | `revenue` $250M–$1B and `ebitda` $40–100M | Must be TRUE |

## 5. Company descriptive information

| Variable | Meaning | Source |
|---|---|---|
| `cik` | Links to financial data | EDGAR |
| `ticker` | Stock symbol | EDGAR profile |
| `company_name` | Legal name | EDGAR profile |
| `sic_code` / `sic_description` | SEC industry classification (imperfect; reviewed manually) | EDGAR profile |
| `exchange` | Listing exchange | EDGAR profile |
| `hq_state` | Headquarters state | EDGAR profile |
| `fiscal_year_end` | Fiscal year-end month and day | EDGAR profile |
| `in_universe` | Included in screening list | Our decision |
| `exclusion_reason` | Why a company was removed | Our decision |

Qualitative fields for finalists only (from 10-K text, verified): `recurring_revenue_notes`, `customer_concentration_notes`, `end_market_notes`, `labor_notes`, `qualitative_source`.

## Appendix: Validation values (Mistras Group answer key)

Manually calculated from Mistras Group's FY2025 10-K (filed 2026-03-11, Acc. 0001628280-26-016765) and FY2024 10-K (FY2022 revenue). Python results must match these. USD thousands unless stated; finance leases included.

| Metric | FY2025 | FY2024 | FY2023 |
|---|---|---|---|
| EBITDA | 71,580 | 72,836 | 32,195 |
| EBITDA margin | 9.9% | 10.0% | 4.6% |
| Revenue growth (YoY) | -0.8% | 3.4% | n/a |
| Revenue CAGR (FY2022–25) | 1.7% | | |
| Free cash flow | 8,307 | 32,227 | 5,894 |
| FCF conversion | 11.6% | 44.2% | 18.3% |
| CapEx intensity | 3.4% | 2.5% | 3.0% |
| Total debt | 202,357 | 190,126 | n/a |
| Net debt | 174,349 | 171,809 | n/a |
| Net leverage | 2.44x | 2.36x | n/a |
| DSO (days) | 78.0 | 63.7 | n/a |
| NOPAT | 30,429 | 29,870 | (1,428) |
| Invested capital | 409,453 | 370,377 | n/a |
| ROIC | 7.8% | n/a | n/a |
| ROIC ex-goodwill | 14.7% | n/a | n/a |
| EBITDA margin range (3-yr) | 5.4 pp (flag) | | |
| EV / EBITDA at $20.35 deal price (our estimate) | 11.55x | | |
| EV / EBITDA at announced ~$866M EV | 12.10x | | |

Result against the Ridgeline mandate: 3 of 8 criteria passed (size gates and leverage). Mistras is excluded from the screen because it is under an announced acquisition (8-K filed 2026-09-18).
