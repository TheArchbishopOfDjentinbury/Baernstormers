#!/usr/bin/env python3
"""
Swiss-made monthly aggregator (Python + rdflib)

Inputs
- Turtle graph: data-extraction/data/graph.ttl
- SPARQL file : data-extraction/queries/swiss-made.sparql
- Swiss brands: data-extraction/data/unique_brands.csv   (single column 'brand' or unlabeled)

Output
- JSON: data-extraction/output/swiss_made_spend.json
  [
    {"category":"Swiss-made","month":"July","monthISO":"2024-07","amount":"CHF 30.00"},
    {"category":"not Swiss-made","month":"July","monthISO":"2024-07","amount":"CHF 12.45"}
  ]
"""

from __future__ import annotations
import csv, json, unicodedata
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse
from rdflib import Graph

# --- Paths (change if needed)
ROOT = Path(__file__).resolve().parents[1]
TTL_PATH    = ROOT / "data" / "graph.ttl"
SPARQL_PATH = ROOT / "queries" / "swiss-made.sparql"
BRANDS_CSV  = ROOT / "data" / "unique_brands.csv"   # assumed to contain *Swiss* brands
OUT_PATH    = ROOT / "output" / "swiss_made_spend.json"

# --- Helpers ------------------------------------------------------------------

def strip_accents_lower(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()

def parse_amount(value) -> float:
    """Accept '3.50', '3,50', 3.5, etc."""
    if value is None:
        raise ValueError("amount is None")
    s = str(value).strip().replace("\u00A0", "").replace(" ", "").replace(",", ".")
    return float(s)

def month_info(date_val) -> tuple[str, str]:
    """Return (YYYY-MM, MonthName). Robust to rdflib literals and strings."""
    try:
        if hasattr(date_val, "toPython"):
            dt = date_val.toPython()
        else:
            dt = dtparse.parse(str(date_val))
    except Exception:
        dt = dtparse.parse(str(date_val))
    y, m = dt.year, dt.month
    iso = f"{y:04d}-{m:02d}"
    month_name = datetime(y, m, 1).strftime("%B")  # English month names (e.g., "July")
    return iso, month_name

# Swiss signal keywords (accent-insensitive, case-insensitive)
SWISS_KEYWORDS = [
    "ip-suisse", "spécialité suisse", "schweizer", "schweiz", "hausbäckerei"
]

def is_swiss_made(text_norm: str, swiss_brands_norm: set[str]) -> bool:
    # brand hit?
    for b in swiss_brands_norm:
        if b and b in text_norm:
            return True
    # keyword hit?
    for kw in (strip_accents_lower(k) for k in SWISS_KEYWORDS):
        if kw in text_norm:
            return True
    return False

def load_swiss_brands(csv_path: Path) -> set[str]:
    """
    Loads a single-column CSV (header either 'brand' or none) into a set of normalized strings.
    """
    brands = set()
    with csv_path.open("r", encoding="utf-8") as f:
        sniffer = csv.Sniffer()
        sample = f.read(4096)
        f.seek(0)
        has_header = False
        try:
            has_header = sniffer.has_header(sample)
        except Exception:
            pass
        reader = csv.reader(f)
        first = True
        for row in reader:
            if not row:
                continue
            cell = row[0].strip()
            if first and has_header and cell.lower() in {"brand", "brands"}:
                first = False
                continue
            first = False
            if not cell:
                continue
            brands.add(strip_accents_lower(cell))
    return brands

# --- Main ---------------------------------------------------------------------

def main():
    if not TTL_PATH.exists():
        raise FileNotFoundError(f"TTL not found: {TTL_PATH}")
    if not SPARQL_PATH.exists():
        raise FileNotFoundError(f"SPARQL not found: {SPARQL_PATH}")
    if not BRANDS_CSV.exists():
        raise FileNotFoundError(f"Brands CSV not found: {BRANDS_CSV}")

    swiss_brands = load_swiss_brands(BRANDS_CSV)

    # Load SPARQL
    query_text = SPARQL_PATH.read_text(encoding="utf-8").strip()
    if not query_text[:10].upper().startswith(("PREFIX","SELECT","CONSTRUCT","ASK","DESCRIBE")):
        raise ValueError(f"SPARQL must start with a SPARQL keyword. Preview: {query_text[:80]}")

    # Load graph & query
    g = Graph()
    g.parse(str(TTL_PATH), format="turtle")
    rows = g.query(query_text)

    # Aggregate totals by (monthISO, MonthName, Swiss-made|not Swiss-made)
    totals = {}  # (iso, monthName, category) -> float

    for b in rows:
        bd = b.asdict()
        date_val      = bd.get("date")
        product_name  = bd.get("productName")
        description   = bd.get("description")
        line_subtotal = bd.get("lineSubtotal")

        if date_val is None or line_subtotal is None:
            continue

        try:
            amt = parse_amount(line_subtotal)
        except Exception:
            continue

        iso, month_name = month_info(date_val)

        # Build searchable text: productName + description (both normalized)
        text_norm = strip_accents_lower(
            f"{product_name or ''} || {description or ''}"
        )

        swiss = is_swiss_made(text_norm, swiss_brands)
        category = "Swiss-made" if swiss else "not Swiss-made"

        key = (iso, month_name, category)
        totals[key] = totals.get(key, 0.0) + amt

    # Emit requested shape
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_rows = []
    for (iso, month_name, category) in sorted(totals.keys()):
        amount = totals[(iso, month_name, category)]
        out_rows.append({
            "category": category,
            "month": month_name,
            "monthISO": iso,
            "amount": f"CHF {amount:.2f}"
        })

    OUT_PATH.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(out_rows)} rows).")

if __name__ == "__main__":
    main()
