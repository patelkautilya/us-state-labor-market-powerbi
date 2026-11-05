# Findings and metric notes

The panel contains 51 jurisdictions (50 states plus DC) × 24 calendar months in 2024–2025. It is a snapshot of BLS LAUS seasonally adjusted series retrieved on 2026-11-05 UTC.

## Definitions

- **Unemployment rate:** BLS LAUS series measure `03`, percent of civilian labor force; use BLS values directly.
- **Unemployed persons:** BLS LAUS series measure `04`, estimated people unemployed in a state at a month; not a flow of people losing jobs.
- **State median:** Median of available state/DC rates for a selected month, which describes the middle jurisdiction. It is not the U.S. national rate.
- **Year-end change:** December 2025 rate minus December 2024 rate for the same state, in percentage points.
- **Available jurisdiction:** Both rate and unemployed-person estimate have numeric BLS values for the selected month.

## Checked results

The Power BI KPI card for **3.80%** takes the median of all 1,173 available state-month rates across the full 2024–2025 panel. It is a different scope from the 51-jurisdiction **December 2025 median of 4.2%** below. Selecting Alabama in the report's state slicer yields a 2.90% median, 23 available months, and 3.10% maximum, matching the curated CSV.

1. December 2025 state/DC median rate: **4.2%** across 51 available jurisdictions.
2. December 2025 extremes: **Hawaii 2.2%**, **District of Columbia 6.7%**.
3. Largest December-to-December changes in this snapshot: **Colorado −0.5 percentage points**; **Delaware +1.3 percentage points**.
4. **October 2025 is missing in every state/DC series.** The BLS API marks unavailable data with footnote `X` and cites the 2025 lapse in appropriations. The CSV keeps these rows with blank numeric fields and `data_available=False`.

## Interpretation

State rates are estimates and may be revised. A high rate, a low rate, or a change between two months does not identify its cause. The December comparison avoids the October gap, while monthly charts should visibly break at that gap. For a national rate, use BLS's separate national series; do not average these 51 rates. State rankings do not account for statistical uncertainty.

