#!/usr/bin/env python3
"""
Media & Internet Subscriptions monthly spend (Python + GraphDB SPARQL)

Reads:
  - GraphDB: http://localhost:7200/repositories/spendcast
  - SPARQL:  data-extraction/queries/media_subscriptions.sparql

Writes:
  - JSON monthly summary (category = "media and internet subscriptions"):
      data-extraction/output/media_subscriptions_spend.json
      [
        {"category":"media and internet subscriptions","month":"July","monthISO":"2024-07","amount":"CHF 40.80"},
        ...
      ]

  - CSV details of matched items:
      data-extraction/output/media_subscriptions_items.csv
"""

from __future__ import annotations
import csv, json, requests
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse

ROOT        = Path(__file__).resolve().parents[1]
SPARQL_PATH = ROOT / "queries" / "media-subscriptions.sparql"
OUT_JSON    = ROOT / "output" / "media_subscriptions_spend.json"
OUT_CSV     = ROOT / "output" / "media_subscriptions_items.csv"

# GraphDB configuration
GRAPHDB_URL = "http://localhost:7200/repositories/spendcast"
GRAPHDB_USER = "admin"
GRAPHDB_PASS = ""  # Set your password here if needed

def parse_amount(val) -> float:
    """Parse amount from various string formats."""
    s = str(val).strip().replace("\u00A0", "").replace(" ", "").replace(",", ".")
    return float(s)

def month_info(date_val) -> tuple[str, str]:
    """Extract ISO month and readable month name from date."""
    try:
        if hasattr(date_val, "toPython"):
            dt = date_val.toPython()
        else:
            dt = dtparse.parse(str(date_val))
    except Exception:
        dt = dtparse.parse(str(date_val))
    
    iso = f"{dt.year:04d}-{dt.month:02d}"
    month_name = datetime(dt.year, dt.month, 1).strftime("%B")
    return iso, month_name

def execute_sparql_query(query_text: str) -> dict:
    """Execute SPARQL query against GraphDB."""
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query'
    }
    
    session = requests.Session()
    if GRAPHDB_USER and GRAPHDB_PASS:
        session.auth = (GRAPHDB_USER, GRAPHDB_PASS)
    
    response = session.post(GRAPHDB_URL, data=query_text, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    """Main processing function."""
    if not SPARQL_PATH.exists():
        raise FileNotFoundError(f"SPARQL not found: {SPARQL_PATH}")

    # Read and validate SPARQL query
    query_text = SPARQL_PATH.read_text(encoding="utf-8").strip()
    if not query_text[:10].upper().startswith(("PREFIX","SELECT","CONSTRUCT","ASK","DESCRIBE")):
        raise ValueError(f"SPARQL must start with a SPARQL keyword. Preview: {query_text[:80]}")

    # Execute SPARQL query against GraphDB
    print(f"Executing SPARQL query from {SPARQL_PATH}")
    result = execute_sparql_query(query_text)
    
    monthly = {}  # (iso, monthName) -> sum CHF
    details = []

    # Process query results
    for binding in result.get('results', {}).get('bindings', []):
        transaction = binding.get('transaction', {}).get('value', '')
        label = binding.get('label', {}).get('value', '')
        date_val = binding.get('date', {}).get('value', '')
        amount_val = binding.get('amount', {}).get('value', '')
        currency = binding.get('currency', {}).get('value', '')
        
        if not date_val or not amount_val:
            continue

        try:
            amt = parse_amount(amount_val)
        except Exception:
            continue

        # Determine currency symbol
        if 'Swiss_franc' in currency:
            curr_symbol = 'CHF'
        elif 'Euro' in currency:
            curr_symbol = 'EUR'
        elif 'Dollar' in currency:
            curr_symbol = 'USD'
        else:
            curr_symbol = 'CHF'  # Default

        iso, mname = month_info(date_val)
        key = (iso, mname, curr_symbol)
        monthly[key] = monthly.get(key, 0.0) + amt

        # Determine category based on transaction label
        category = "utilities"
        if any(term in label.lower() for term in ['netflix', 'spotify', 'prime', 'streaming', 'disney', 'hulu']):
            category = "streaming subscriptions"
        elif any(term in label.lower() for term in ['mobile', 'internet', 'phone', 'telecom', 'salt', 'sunrise', 'swisscom']):
            category = "telecommunications"
        elif any(term in label.lower() for term in ['öv', 'abo', 'transport']):
            category = "transport subscriptions"

        details.append({
            "date": date_val,
            "transaction_id": transaction.split('/')[-1] if '/' in transaction else transaction,
            "label": label,
            "category": category,
            "amount_chf": f"{amt:.2f}",
            "currency": curr_symbol,
        })

    # Write monthly JSON in requested format
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    
    # Group by month across all currencies (convert to CHF if needed)
    monthly_chf = {}
    for (iso, mname, curr) in monthly.keys():
        amount = monthly[(iso, mname, curr)]
        # For simplicity, assume all amounts are already in CHF
        # In a real scenario, you'd convert currencies here
        key = (iso, mname)
        monthly_chf[key] = monthly_chf.get(key, 0.0) + amount

    for (iso, mname) in sorted(monthly_chf.keys()):
        amount = monthly_chf[(iso, mname)]
        out_rows.append({
            "category": "media and internet subscriptions",
            "month": mname,
            "monthISO": iso,
            "amount": f"CHF {amount:.2f}"
        })

    OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(out_rows)} months).")

    # Write details CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date", "transaction_id", "label", "category", "amount_chf", "currency"
        ])
        w.writeheader()
        w.writerows(details)
    print(f"Wrote {OUT_CSV} ({len(details)} items).")

if __name__ == "__main__":
    main()