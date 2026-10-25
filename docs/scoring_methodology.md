# Scoring Methodology

Implemented in `src/scoring.py`; run in `notebooks/07_scoring.ipynb`.

## Candidates

Six companies passed the size gate and the manual review (`docs/manual_review.md`): WLDN, QNST, LQDT, ONT, TISI, ADV. All six are scored. Only companies below the **3.0x net leverage hard filter** can be recommended (ONT, TISI, and ADV are scored and tracked but not eligible).

## Scoring scales

Each metric is scored on a fixed scale tied to the mandate, not relative to peers: 0 points at one value, 100 at another, linear in between, capped at both ends. Missing values score 0 (a company cannot benefit from missing data).

| Metric | 0 points | 100 points | Weight |
|---|---|---|---|
| Revenue CAGR (3-yr) | 0% | 10% | 20 |
| EBITDA margin | 5% | 20% | 20 |
| FCF conversion (3-yr total FCF / total EBITDA) | 0% | 90% | 20 |
| CapEx intensity | 6% | 0% | 10 |
| Net leverage | 4.0x | 0.0x | 10 |
| EV/EBITDA (share prices as of 2026-10-23) | 18x | 8x | 20 |

Roughly 75% of the weight is on business quality and 25% on price: cash generation and margins determine how much acquisition debt a company can carry and repay.

## Results (base case)

| Rank | Company | Score | Eligible |
|---|---|---|---|
| 1 | QuinStreet (QNST) | 66.4 | Yes |
| 2 | Willdan (WLDN) | 64.7 | Yes |
| 3 | Liquidity Services (LQDT) | 63.3 | Yes |
| 4 | Onterris (ONT) | 59.6 | No (leverage) |
| 5 | Team Inc (TISI) | 32.9 | No (leverage) |
| 6 | Advantage Solutions (ADV) | 29.7 | No (leverage) |

## Sensitivity to weights

| Scenario | Ranking (eligible) | Gap #1 vs #2 |
|---|---|---|
| Base case | QNST > WLDN > LQDT | 1.7 |
| Equal weights | QNST > WLDN > LQDT | 3.0 |
| Quality focus | WLDN > LQDT > QNST | 0.4 |
| Value focus | QNST > WLDN > LQDT | 7.6 |
| Growth discounted | QNST > WLDN > LQDT | 1.7 |

**Conclusion:** QuinStreet leads in four of five scenarios, driven by its lower valuation; Willdan leads when quality is emphasized and never ranks below second. The model narrows the field to two finalists but does not decide between them. The weights were not adjusted after seeing results.

## Known limitations

- Revenue CAGR does not separate organic from acquired growth. QuinStreet's growth is partly acquired (acquisition spending ≈ 8.5% of revenue over 3 years); this is shown as a flag, not scored.
- Growth and 3-year cash conversion score 100 for most candidates, so they discriminate little.
- CapEx excludes capitalized software (e.g., QuinStreet's $10.9M internal software development in FY2026), which understates capital intensity for some companies.
- Valuation uses one day's share prices and the latest fiscal year's EBITDA.
