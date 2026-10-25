# Manual Review of Size-Qualified Companies

Each company that passed the size gate was reviewed against `docs/investment_mandate.md`: U.S. B2B business services; excluded types are staffing/PEO, financial services, and real estate; companies under an announced acquisition are excluded. Research was AI-assisted and checked against the sources listed; business descriptions marked (10-K) should be confirmed against Item 1 of the latest 10-K.

| Ticker | Company | What the business does | Announced deal? | Decision | Reason | Source |
|---|---|---|---|---|---|---|
| WLDN | Willdan Group | Energy-efficiency, engineering, and consulting services, mainly for utilities and government agencies (10-K) | No (Willdan is a buyer: Compass Municipal Advisors) | Include | B2B/B2G professional services | Company release on Compass acquisition |
| QNST | QuinStreet | Performance marketing: generates customer leads for clients in financial and home services (10-K) | No (QuinStreet is a buyer: HomeBuddy, ~$190M) | Include | Clients are businesses paying for leads. Data flag: acquisition spending not captured | Pulse 2.0; QuinStreet 8-K (FY2026) |
| LQDT | Liquidity Services | B2B online marketplaces for surplus assets (GovDeals, retail, heavy equipment) for ~15,000 corporate and government sellers | No | Include (flagged) | Outsourced asset-disposal service for businesses and governments; flag: marketplace model with purchase-and-resale inventory risk | Stock Titan company overview |
| ONT | Onterris (formerly Montrose Environmental) | Environmental services: measurement and analysis, remediation, restoration for industrial, government, and utility clients | No | Include; fails leverage limit | B2B services, but 4.9x net leverage exceeds the 3.0x hard filter; law-firm investigation notices noted | roic.ai company profile |
| TISI | Team Inc | Industrial inspection and maintenance services (10-K) | No; Stellex Capital (PE) agreed to buy ~35% stake from Corre Partners (Aug 2026) | Include; fails leverage limit | B2B services, but 5.8x net leverage exceeds the 3.0x hard filter; negative equity; a 35% PE holder would be central to any deal | Latham & Watkins announcement |
| ADV | Advantage Solutions | Outsourced sales and marketing services (merchandising, sampling) for consumer-goods brands and retailers (10-K) | None found | Include; fails leverage limit | B2B services, but ~18.9x net leverage exceeds the 3.0x hard filter | Search found only 2020 SPAC listing |
| MG | Mistras Group | Asset integrity testing and inspection services for industrial customers | Yes: merger agreement with an H.I.G. Capital affiliate, $20.35/share | Exclude | Under announced acquisition; retained as answer key and deal benchmark | 10-K FY2025; 8-K filed 2026-09-18 |
| RMR | RMR Group | Alternative asset manager focused on real estate (~$37B AUM) | n/a | Exclude | Financial services and real estate: excluded business types under the mandate | RMR fiscal Q1 2026 results release |

## Result

- **Eligible for recommendation (pass leverage limit):** WLDN, QNST, LQDT
- **Scored and tracked, not eligible (fail 3.0x leverage limit):** ONT, TISI, ADV
- **Excluded:** MG, RMR

## Limitations

- Finding no announced deal in news searches is not proof that none exists.
- "(10-K)" descriptions are from general knowledge and should be confirmed against Item 1 of each company's latest 10-K.
