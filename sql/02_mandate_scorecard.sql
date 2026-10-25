-- Ridgeline Capital mandate scorecard (docs/investment_mandate.md, section 4)
-- Applies each core criterion to the companies that pass the size gate.
-- Results: PASS / FAIL / N/A (N/A = metric not available or not meaningful).
-- Net leverage < 3.0x is treated as a hard filter; the others are preferences.

WITH latest AS (
    SELECT cik, MAX(fiscal_year) AS fiscal_year
    FROM financials
    WHERE revenue IS NOT NULL
    GROUP BY cik
),
shortlist AS (
    -- Size-qualified companies with the metrics needed for each criterion
    SELECT c.ticker,
           f.revenue_cagr_3y,
           f.ebitda_margin,
           f.fcf_conversion,
           f.capex_intensity,
           f.net_leverage,
           (m.close_price * m.shares_used_000s + f.net_debt) / f.ebitda AS ev_to_ebitda
    FROM latest AS l
    JOIN financials AS f ON f.cik = l.cik AND f.fiscal_year = l.fiscal_year
    JOIN companies  AS c ON c.cik = l.cik
    LEFT JOIN market_data AS m ON m.cik = l.cik
    WHERE c.in_universe = 1
      AND f.fiscal_year >= 2025
      AND f.ebitda BETWEEN 40000 AND 100000
),
scored AS (
    SELECT ticker,
           CASE WHEN revenue_cagr_3y IS NULL THEN 'N/A' WHEN revenue_cagr_3y >= 0.05 THEN 'PASS' ELSE 'FAIL' END AS growth,
           CASE WHEN ebitda_margin   IS NULL THEN 'N/A' WHEN ebitda_margin   >= 0.12 THEN 'PASS' ELSE 'FAIL' END AS margin,
           CASE WHEN fcf_conversion  IS NULL THEN 'N/A' WHEN fcf_conversion  >= 0.70 THEN 'PASS' ELSE 'FAIL' END AS cash_conversion,
           CASE WHEN capex_intensity IS NULL THEN 'N/A' WHEN capex_intensity <  0.03 THEN 'PASS' ELSE 'FAIL' END AS capex,
           CASE WHEN net_leverage    IS NULL THEN 'N/A' WHEN net_leverage    <  3.0  THEN 'PASS' ELSE 'FAIL' END AS leverage,
           CASE WHEN ev_to_ebitda    IS NULL THEN 'N/A' WHEN ev_to_ebitda    <= 10.0 THEN 'PASS' ELSE 'FAIL' END AS valuation
    FROM shortlist
)
SELECT *,
       (growth = 'PASS') + (margin = 'PASS') + (cash_conversion = 'PASS')
     + (capex = 'PASS') + (leverage = 'PASS') + (valuation = 'PASS') AS criteria_passed
FROM scored
ORDER BY criteria_passed DESC, ticker;
