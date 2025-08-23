#!/usr/bin/env python3
"""
Coffee item monthly spend (Python + rdflib)

Reads:
  - TTL:     data-extraction/data/graph.ttl
  - SPARQL:  data-extraction/queries/coffee_items.sparql

Writes:
  - JSON monthly summary (category = "coffee"):
      data-extraction/output/coffee_spend.json
      [
        {"category":"coffee","month":"July","monthISO":"2024-07","amount":"CHF 30.00"},
        ...
      ]

  - CSV details of matched items:
      data-extraction/output/coffee_items.csv
"""

from __future__ import annotations
import csv, json
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse
from rdflib import Graph

ROOT        = Path(__file__).resolve().parents[1]
TTL_PATH    = ROOT / "data" / "graph.ttl"
SPARQL_PATH = ROOT / "queries" / "coffee-items.sparql"
OUT_JSON    = ROOT / "output" / "coffee_spend.json"
OUT_CSV     = ROOT / "output" / "coffee_items.csv"

def parse_amount(val) -> float:
    s = str(val).strip().replace("\u00A0", "").replace(" ", "").replace(",", ".")
    return float(s)

def month_info(date_val) -> tuple[str, str]:
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

    monthly = {}  # (iso, monthName) -> sum CHF
    details = []

    for r in rows:
        b = r.asdict()
        date_val = b.get("date")
        line_subtotal = b.get("lineSubtotal")
        qty = b.get("quantity")
        if date_val is None or line_subtotal is None:
            continue

        try:
            amt = parse_amount(line_subtotal)
        except Exception:
            continue

        # If your subtotal is per-item and not per-line, uncomment next two lines:
        # q = float(qty) if qty is not None else 1.0
        # amt = amt * q

        iso, mname = month_info(date_val)
        monthly[(iso, mname)] = monthly.get((iso, mname), 0.0) + amt

        details.append({
            "date": str(date_val),
            "receipt": str(b.get("receipt") or ""),
            "product_name": str(b.get("productName") or ""),
            "description": str(b.get("description") or ""),
            "category_label": str(b.get("categoryLabel") or ""),
            "quantity": str(qty or ""),
            "line_subtotal_chf": f"{amt:.2f}",
        })

    # Write monthly JSON in your format
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    for (iso, mname) in sorted(monthly.keys()):
        amount = monthly[(iso, mname)]
        out_rows.append({
            "category": "coffee",
            "month": mname,
            "monthISO": iso,
            "amount": f"CHF {amount:.2f}"
        })
    OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(out_rows)} months).")

    # Write details CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date","receipt","product_name","description","category_label","quantity","line_subtotal_chf"
        ])
        w.writeheader()
        w.writerows(details)
    print(f"Wrote {OUT_CSV} ({len(details)} items).")

if __name__ == "__main__":
    main()
