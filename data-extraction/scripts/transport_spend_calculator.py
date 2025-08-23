#!/usr/bin/env python3
"""
Travel & Transport monthly spend (Python + GraphDB SPARQL)

Reads:
  - GraphDB: http://localhost:7200/repositories/spendcast
  - SPARQL:  data-extraction/queries/travel_transport.sparql

Writes:
  - JSON monthly summary (category = "travel and transport"):
      data-extraction/output/travel_transport_spend.json
      [
        {"category":"travel and transport","month":"July","monthISO":"2024-07","amount":"CHF 42.75"},
        ...
      ]

  - CSV details of matched items:
      data-extraction/output/travel_transport_items.csv


"""

from __future__ import annotations
import csv, json, requests
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse

ROOT        = Path(__file__).resolve().parents[1]
SPARQL_PATH = ROOT / "queries" / "transport-receipts.sparql"
OUT_JSON    = ROOT / "output" / "transport_spend.json"
OUT_CSV     = ROOT / "output" / "travel_transport_items.csv"

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

def categorize_transaction(label: str) -> str:
    """Categorize transaction based on label content."""
    label_lower = label.lower()
    
    # Fuel and gas
    if any(term in label_lower for term in ['benzin', 'gas', 'fuel', 'petrol', 'tankstelle']):
        return "fuel"
    
    # Public transport and tickets
    elif any(term in label_lower for term in ['öv', 'abo', 'sbb', 'train', 'bus', 'ticket', 'zugticket']):
        return "public transport"
    
    # Air travel
    elif any(term in label_lower for term in ['flight', 'airline', 'airport', 'flug', 'kopenhagen', 'copenhagen']):
        return "flights"
    
    # Accommodation
    elif any(term in label_lower for term in ['hotel', 'airbnb', 'apartment', 'accommodation', 'vesterboro']):
        return "accommodation"
    
    # Water transport
    elif any(term in label_lower for term in ['ferry', 'cruise', 'boat', 'sardinien']):
        return "ferry/cruise"
    
    # Car related (parking, tolls, etc.)
    elif any(term in label_lower for term in ['parking', 'toll', 'vignette', 'rental']):
        return "car expenses"
    
    # Taxi/ride sharing
    elif any(term in label_lower for term in ['taxi', 'uber', 'lyft', 'bolt']):
        return "taxi/rideshare"
    
    # General travel
    elif any(term in label_lower for term in ['travel', 'reise', 'vacation', 'holiday']):
        return "travel expenses"
    
    else:
        return "transport"

def convert_to_chf(amount: float, currency: str, date_str: str) -> float:
    """Convert amount to CHF. For simplicity, using approximate rates."""
    if 'Swiss_franc' in currency:
        return amount
    elif 'Euro' in currency:
        # Approximate EUR to CHF rate (you might want to use historical rates)
        return amount * 0.95  # Rough average rate
    elif 'Dollar' in currency:
        # Approximate USD to CHF rate
        return amount * 0.90
    else:
        return amount  # Default to CHF

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

        # Convert to CHF
        amt_chf = convert_to_chf(amt, currency, date_val)
        
        # Determine original currency symbol
        if 'Swiss_franc' in currency:
            curr_symbol = 'CHF'
        elif 'Euro' in currency:
            curr_symbol = 'EUR'
        elif 'Dollar' in currency:
            curr_symbol = 'USD'
        else:
            curr_symbol = 'CHF'  # Default

        iso, mname = month_info(date_val)
        monthly[(iso, mname)] = monthly.get((iso, mname), 0.0) + amt_chf

        # Categorize the transaction
     # Categorize the transaction
        category = categorize_transaction(label)

        # Add main category to details for CSV
        if category == "fuel":
            main_category = "fuel and gas"
        elif category == "public transport":
            main_category = "public transport"
        else:
            main_category = "travel and transport other"
        details.append({
            "date": date_val,
            "transaction_id": transaction.split('/')[-1] if '/' in transaction else transaction,
            "label": label,
            "main_category": main_category,
            "subcategory": category,
            "amount_original": f"{curr_symbol} {amt:.2f}",
            "amount_chf": f"CHF {amt_chf:.2f}",
            "currency": curr_symbol,
        })

    # Organize by category and month
    category_monthly = {}  # category -> (iso, monthName) -> sum CHF
    
    for detail in details:
        subcat = detail['subcategory']
        date_val = detail['date']
        amt_chf = float(detail['amount_chf'].replace('CHF ', ''))
        
        iso, mname = month_info(date_val)
        
        # Map subcategories to main categories
        if subcat == "fuel":
            main_category = "fuel and gas"
        elif subcat == "public transport":
            main_category = "public transport"
        else:
            main_category = "travel and transport other"
        
        if main_category not in category_monthly:
            category_monthly[main_category] = {}
        
        key = (iso, mname)
        category_monthly[main_category][key] = category_monthly[main_category].get(key, 0.0) + amt_chf

    # Write monthly JSON in requested format (split by categories)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    
    for category in sorted(category_monthly.keys()):
        for (iso, mname) in sorted(category_monthly[category].keys()):
            amount = category_monthly[category][(iso, mname)]
            out_rows.append({
                "category": category,
                "month": mname,
                "monthISO": iso,
                "amount": f"CHF {amount:.2f}"
            })

    OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(out_rows)} category-months).")

    # Write details CSV


    # Print summary by main category and subcategory
    print("\n📊 Summary by category:")
    category_totals = {}
    for detail in details:
        subcat = detail['subcategory']
        amount = float(detail['amount_chf'].replace('CHF ', ''))
        
        # Map to main categories
        if subcat == "fuel":
            main_category = "fuel and gas"
        elif subcat == "public transport":
            main_category = "public transport"
        else:
            main_category = "travel and transport other"
        
        category_totals[main_category] = category_totals.get(main_category, 0.0) + amount
    
    for category in sorted(category_totals.keys()):
        total = category_totals[category]
        print(f"  {category:25} CHF {total:8.2f}")
    
    grand_total = sum(category_totals.values())
    print(f"  {'='*25} {'='*12}")
    print(f"  {'TOTAL':25} CHF {grand_total:8.2f}")
    
    print("\n📋 Detailed breakdown by subcategory:")
    subcategory_totals = {}
    for detail in details:
        subcat = detail['subcategory']
        amount = float(detail['amount_chf'].replace('CHF ', ''))
        subcategory_totals[subcat] = subcategory_totals.get(subcat, 0.0) + amount
    
    for subcat in sorted(subcategory_totals.keys()):
        total = subcategory_totals[subcat]
        print(f"  {subcat:20} CHF {total:8.2f}")

if __name__ == "__main__":
    main()