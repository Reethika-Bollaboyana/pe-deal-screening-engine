-- Ridgeline Capital size gate (docs/investment_mandate.md, section 3)
-- A company passes if, in its latest fiscal year with revenue data:
--   * the fiscal year is 2025 or later (recent annual report), and
--   * EBITDA is between $40M and $100M (values stored in $000s).

WITH latest AS (
    -- Each company's most recent fiscal year that has revenue
    SELECT cik, MAX(fiscal_year) AS fiscal_year
    FROM financials
    WHERE revenue IS NOT NULL
    GROUP BY cik
)
SELECT c.ticker,
       c.company_name,
       f.fiscal_year,
       ROUND(f.revenue / 1000, 1) AS revenue_m,
       ROUND(f.ebitda / 1000, 1)  AS ebitda_m
FROM latest AS l
JOIN financials AS f ON f.cik = l.cik AND f.fiscal_year = l.fiscal_year
JOIN companies  AS c ON c.cik = l.cik
WHERE c.in_universe = 1
  AND f.fiscal_year >= 2025
  AND f.ebitda BETWEEN 40000 AND 100000
ORDER BY f.ebitda DESC;
