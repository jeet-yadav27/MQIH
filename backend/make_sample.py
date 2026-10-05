"""Write a deterministic FTIR sample extract."""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sample_data" / "ftir_sample.csv"

COMPLAINTS = [
    "Engine hesitates on a cold start",
    "Transmission slips between second and third",
    "Air conditioner loses cooling at idle",
    "Steering pulls to the left under braking",
    "Battery warning after an overnight park",
    "Abnormal noise from the front suspension",
    "Fuel smell in the cabin after refuelling",
    "Infotainment screen restarts while driving",
]
CODES = ["P0301", "P0420", "P0171", "P0507", "C0035", "B1001", "U0100", "P0128"]
COUNTRIES = ["India"] * 5 + ["Thailand"] * 3 + ["Indonesia"] * 2 + ["UAE"] * 2 + ["South Africa"] * 2 + ["Mexico", "Australia"]
MODELS = ["PM-118"] * 3 + ["PM-210"] * 4 + ["PM-340"] * 2 + ["PM-455"] * 2 + ["PM-510"]
SEGMENTS = ["Passenger", "Passenger", "SUV", "LCV", "MUV"]
DEALERS = [
    "Northwind Motors",
    "Harbor Auto",
    "Crescent Commercial",
    "Summit Fleet",
    "Amberline Service",
    "Redrock Motors",
]
SPECS = {
    "India": "INDIA",
    "Thailand": "ASEAN",
    "Indonesia": "ASEAN",
    "UAE": "GCC",
    "South Africa": "AFRICA",
    "Mexico": "LATAM",
    "Australia": "OCEANIA",
}


def main() -> None:
    random.seed(11)
    start = datetime(2024, 1, 15)
    rows = []
    for index in range(1, 97):
        country = random.choice(COUNTRIES)
        days = random.randint(8, 1400)
        if random.random() < 0.12:
            days_cell = ""
        else:
            days_cell = str(days)
        registered = start + timedelta(days=random.randint(0, 640))
        incident = registered + timedelta(days=days)
        report = incident + timedelta(days=random.randint(2, 35))
        solved = random.random() < 0.58
        rank_roll = random.random()
        rank = "A" if rank_roll < 0.16 else "B" if rank_roll < 0.48 else "C"
        km = days * random.randint(22, 78)
        rows.append(
            {
                "ftir_no": f"FTIR-2024-{index:04d}",
                "ftir_report_date": report.strftime("%Y-%m-%d"),
                "status": "Closed" if solved else random.choice(["Open", "In progress", "Monitoring"]),
                "product_model_code": random.choice(MODELS),
                "outbreak_country": country,
                "customer_complaint": random.choice(COMPLAINTS),
                "sbpr_no": f"SBPR-{18000 + index}" if random.random() < 0.42 else "",
                "reply_date": (report + timedelta(days=random.randint(3, 21))).strftime("%Y-%m-%d"),
                "fc_ok": "Yes" if random.random() < 0.8 else "No",
                "sales_model_code": random.choice(["SM-A", "SM-B", "SM-C"]),
                "segmentation": random.choice(SEGMENTS),
                "date_registered": registered.strftime("%Y-%m-%d"),
                "date_of_incident": incident.strftime("%Y-%m-%d"),
                "using_time_km": f"{km} km",
                "reported_company": random.choice(DEALERS),
                "reported_country": country if random.random() < 0.75 else random.choice(["India", "UAE", "Thailand"]),
                "rank": rank,
                "quality": random.choice(["Complete", "Complete", "Partial", "Insufficient"]),
                "repair_status": "Completed" if solved else random.choice(["Pending", "In workshop", "Parts awaited"]),
                "problem_solved": "Yes" if solved else "No",
                "trouble_code_complaint": random.choice(CODES),
                "days_used": days_cell,
                "spec_on_destination": SPECS[country],
                "sales_dealer": random.choice(DEALERS),
                "service_dealer": random.choice(DEALERS),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
