#!/usr/bin/env python3
"""
Transport monthly spend (Python + rdflib)

Reads:
  - Turtle : data-extraction/data/graph.ttl
  - SPARQL : data-extraction/queries/transport_receipts.sparql

Writes:
  - JSON (requested shape, single category "transport"):
      data-extraction/output/transport_spend.json
      [
        {"category":"transport","month":"July","monthISO":"2024-07","amount":"CHF 123.45"},
        ...
      ]

  - CSV (optional per-receipt details):
      data-extraction/output/transport_receipts.csv
"""

from __future__ import annotations
import csv, json
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse
from rdflib import Graph

ROOT        = Path(__file__).resolve().parents[1]
TTL_PATH    = ROOT / "data" / "graph.ttl"
SPARQL_PATH = ROOT / "queries" / "transport-receipts.sparql"
OUT_JSON    = ROOT / "output" / "transport_spend.json"
OUT_CSV     = ROOT / "output" / "transport_receipts.csv"

SAVE_DETAILS = True  # set False if you don't want the CSV

def parse_amount(val) -> float:
    """Accept '3.50', '3,50', etc."""
    s = str(val).strip().replace("\u00A0", "").replace(" ", "").replace(",", ".")
    return float(s)

def month_info(date_val) -> tuple[str, str]:
    """Return (YYYY-MM, MonthName) from rdflib literal or string."""
    try:
        dt = date_val.toPython() if hasattr(date_val, "toPython") else dtparse.parse(str(date_val))
    except Exception:
        dt = dtparse.parse(str(date_val))
    iso = f"{dt.year:04d}-{dt.month:02d}"
    month_name = datetime(dt.year, dt.month, 1).strftime("%B")
    return iso, month_name

def main():
    if not TTL_PATH.exists():
        raise FileNotFoundError(f"TTL not found: {TTL_PATH}")
    if not SPARQL_PATH.exists():
        raise FileNotFoundError(f"SPARQL not found: {SPARQL_PATH}")

    query_text = SPARQL_PATH.read_text(encoding="utf-8").strip()
    if not query_text[:10].upper().startswith(("PREFIX","SELECT","CONSTRUCT","ASK","DESCRIBE")):
        raise ValueError(f"SPARQL must start with a SPARQL keyword. Preview: {query_text[:80]}")

    g = Graph()
    g.parse(str(TTL_PATH), format="turtle")
    rows = g.query(query_text)

    # Aggregate monthly totals
    monthly_totals = {}  # (iso, monthName) -> float

    # Optional detailed export
    details = []

    for r in rows:
        b = r.asdict()
        date_val   = b.get("date")
        total_val  = b.get("receiptTotal")
        receipt    = b.get("receipt")
        merchant   = b.get("merchantLabel")
        mcc        = b.get("merchantCategory")
        desc       = b.get("receiptDescription")

        if date_val is None or total_val is None:
            continue

        try:
            amt = parse_amount(total_val)
        except Exception:
            continue

        iso, mname = month_info(date_val)
        monthly_totals[(iso, mname)] = monthly_totals.get((iso, mname), 0.0) + amt

        if SAVE_DETAILS:
            details.append({
                "date": str(date_val),
                "receipt": str(receipt or ""),
                "merchant": str(merchant or ""),
                "merchant_category": str(mcc or ""),
                "description": str(desc or ""),
                "receipt_total_chf": f"{amt:.2f}",
            })

    # Write monthly JSON in your requested format
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    for (iso, mname) in sorted(monthly_totals.keys()):
        amount = monthly_totals[(iso, mname)]
        out_rows.append({
            "category": "transport",
            "month": mname,
            "monthISO": iso,
            "amount": f"CHF {amount:.2f}",
        })
    OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(out_rows)} months).")

if __name__ == "__main__":
    main()
