"""Build a reproducible 2024–2025 state labor-market panel from BLS LAUS."""

from __future__ import annotations

import csv
import io
import json
import statistics
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_URL = "https://www2.census.gov/geo/docs/reference/state.txt"
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
YEARS = (2024, 2025)
MEASURES = {"rate": "03", "unemployed": "04"}


def read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "KayPatelPortfolio/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def get_states() -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(read_url(STATE_URL).decode("utf-8")), delimiter="|")
    states = [
        {"fips": row["STATE"], "abbr": row["STUSAB"], "state": row["STATE_NAME"]}
        for row in reader
        if int(row["STATE"]) <= 56
    ]
    if len(states) != 51 or len({x["fips"] for x in states}) != 51:
        raise ValueError(f"Expected 50 states and DC; got {len(states)}")
    return states


def series_id(fips: str, measure: str) -> str:
    return f"LASST{fips}00000000000{measure}"


def fetch_series(ids: list[str]) -> dict[str, list[dict]]:
    result = {}
    for start in range(0, len(ids), 20):
        batch = ids[start : start + 20]
        body = json.dumps(
            {"seriesid": batch, "startyear": str(min(YEARS)), "endyear": str(max(YEARS))}
        ).encode("utf-8")
        request = urllib.request.Request(
            BLS_URL,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "KayPatelPortfolio/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
        if payload.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS batch failed: {payload.get('message')}")
        for item in payload["Results"]["series"]:
            result[item["seriesID"]] = item["data"]
    missing_ids = set(ids) - set(result)
    if missing_ids:
        raise ValueError(f"BLS did not return {sorted(missing_ids)}")
    return result


def main() -> None:
    states = get_states()
    ids = [series_id(state["fips"], measure) for state in states for measure in MEASURES.values()]
    raw = fetch_series(ids)
    indexed: dict[tuple[str, int, int, str], dict] = {}
    for state in states:
        for measure, code in MEASURES.items():
            for point in raw[series_id(state["fips"], code)]:
                period = point["period"]
                if not period.startswith("M") or period == "M13":
                    continue
                month = int(period[1:])
                indexed[(state["fips"], int(point["year"]), month, measure)] = point

    rows = []
    missing = Counter()
    for state in states:
        for year in YEARS:
            for month in range(1, 13):
                points = {
                    measure: indexed.get((state["fips"], year, month, measure))
                    for measure in MEASURES
                }
                values = {}
                for measure, point in points.items():
                    value = point["value"] if point else "-"
                    values[measure] = None if value == "-" else float(value) if measure == "rate" else int(value)
                    if values[measure] is None:
                        missing[f"{year}-{month:02d}:{measure}"] += 1
                if (values["rate"] is None) != (values["unemployed"] is None):
                    raise ValueError(f"Measure availability differs for {state['state']} {year}-{month:02d}")
                rows.append(
                    {
                        "month_start": date(year, month, 1).isoformat(),
                        "year": year,
                        "month": month,
                        "state": state["state"],
                        "state_abbr": state["abbr"],
                        "state_fips": state["fips"],
                        "unemployment_rate_pct": values["rate"],
                        "unemployed_persons": values["unemployed"],
                        "data_available": values["rate"] is not None,
                    }
                )

    if len(rows) != 51 * 24 or len({(r["state_fips"], r["month_start"]) for r in rows}) != len(rows):
        raise ValueError("State-month panel is not complete and unique")
    available = [r for r in rows if r["data_available"]]
    if any(not 0 <= r["unemployment_rate_pct"] <= 100 or r["unemployed_persons"] < 0 for r in available):
        raise ValueError("Out-of-range BLS values")

    path = ROOT / "bls_state_laus_2024_2025.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    dec_2025 = [r for r in rows if r["month_start"] == "2025-12-01"]
    rates_2024 = {r["state_abbr"]: r["unemployment_rate_pct"] for r in rows if r["month_start"] == "2024-12-01"}
    changes = sorted(
        ((r["state"], round(r["unemployment_rate_pct"] - rates_2024[r["state_abbr"]], 1)) for r in dec_2025),
        key=lambda x: x[1],
    )
    summary = {
        "source": "BLS Local Area Unemployment Statistics (seasonally adjusted state series)",
        "state_mapping": STATE_URL,
        "bls_api": BLS_URL,
        "snapshot_utc": datetime.now(timezone.utc).isoformat(),
        "states_plus_dc": len(states),
        "expected_state_month_rows": len(rows),
        "available_state_month_rows": len(available),
        "missing_by_month_measure": dict(sorted(missing.items())),
        "december_2025_median_state_rate_pct": statistics.median(r["unemployment_rate_pct"] for r in dec_2025),
        "december_2025_lowest": min((r["unemployment_rate_pct"], r["state"]) for r in dec_2025),
        "december_2025_highest": max((r["unemployment_rate_pct"], r["state"]) for r in dec_2025),
        "december_2024_to_2025_largest_decrease_pp": changes[0],
        "december_2024_to_2025_largest_increase_pp": changes[-1],
    }
    (ROOT / "validation_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
