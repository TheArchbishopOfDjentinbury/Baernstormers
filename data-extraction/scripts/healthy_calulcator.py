#!/usr/bin/env python3
"""
Healthy / Unhealthy monthly aggregator over a local TTL + SPARQL

Reads:
  - Turtle graph: data-extraction/data/graph.ttl
  - SPARQL file : data-extraction/queries/food-data.sparql

Writes:
  - JSON        : data-extraction/output/healthy_spend.json
"""

from __future__ import annotations
import json, os, sys, argparse
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparse
from rdflib import Graph

# ------------------ Defaults (your paths) ------------------

DEFAULT_TTL = Path(__file__).resolve().parents[1] / "data" / "graph.ttl"
DEFAULT_SPARQL = Path(__file__).resolve().parents[1] / "queries" / "food-data.sparql"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "output" / "healthy_spend.json"

# ------------------ Helpers ------------------


def parse_amount(value: str | float | int) -> float:
    """
    Accepts '3.50', '3,50', 3.5, etc. Returns float or raises ValueError.
    """
    if value is None:
        raise ValueError("amount is None")
    if isinstance(value, (int, float)):
        v = float(value)
    else:
        s = str(value).strip().replace("\u00a0", "").replace(" ", "")
        s = s.replace(",", ".")
        v = float(s)
    if not (v == v and v != float("inf") and v != float("-inf")):
        raise ValueError(f"invalid numeric: {value}")
    return v


def month_info(date_value: object) -> tuple[str, str]:
    """
    Return (isoYM, monthName) from various date literal shapes.
    - Tries rdflib literal .toPython()
    - Falls back to dateutil parser
    """
    # rdflib Literal often has .toPython()
    try:
        if hasattr(date_value, "toPython"):
            dt = date_value.toPython()
            # might be date or datetime
            if hasattr(dt, "year") and hasattr(dt, "month"):
                y, m = dt.year, dt.month
            else:
                raise ValueError
        else:
            raise ValueError
    except Exception:
        dt = dtparse.parse(str(date_value))
        y, m = dt.year, dt.month

    iso = f"{y:04d}-{m:02d}"
    # Month name in English; change to 'de_CH' if you prefer German
    month_name = datetime(y, m, 1).strftime("%B")  # "July"
    return iso, month_name


def classify_food_healthiness(category_label: str, product_name: str) -> str:
    category = (category_label or "").lower()
    product = (product_name or "").lower()

    healthy_patterns = [
        "bananen",
        "äpfel",
        "birnen",
        "orangen",
        "zitronen",
        "ananas",
        "beeren",
        "trauben",
        "gemüse",
        "salate",
        "abgepackte salate",
        "tomaten",
        "gurken",
        "karotten",
        "spinat",
        "kräuter",
        "zwiebeln",
        "kartoffeln",
        "peperoni",
        "auberginen",
        "zucchini",
        "brokkoli",
        "blumenkohl",
        "kohl",
        "rüebli",
        "lauch",
        "sellerie",
        "radieschen",
        "rucola",
        "fisch",
        "meeresfrüchte",
        "bohnen & hülsenfrüchte",
        "linsen",
        "kichererbsen",
        "nüsse",
        "kerne",
        "mandeln",
        "walnüsse",
        "haselnüsse",
        "alternativen zu milch & rahm",
        "alternativen zu joghurts & desserts",
        "alternativen zu hackfleisch",
        "alternativen zu burgern",
        "vollkorn",
        "dinkel",
        "hafer",
        "quinoa",
        "naturreis",
        "wildreis",
        "wasser",
        "mineralwasser",
        "tee",
        "kräutertee",
        "olivenöl",
        "rapsöl",
        "leinöl",
        "essig",
        "senf",
    ]

    unhealthy_patterns = [
        "schokolade",
        "bonbons",
        "süssigkeiten",
        "kekse",
        "gebäck",
        "kuchen",
        "torten",
        "glacé",
        "glace",
        "eis",
        "dessert",
        "pudding",
        "am stiel",
        "pralinés",
        "chips",
        "crackers",
        "snacks",
        "salzgebäck",
        "nüssli",
        "popcorn",
        "softdrinks",
        "cola",
        "limonade",
        "energydrinks",
        "süssgetränke",
        "fruchtsäfte",
        "nektar",
        "sirup",
        "eistee",
        "wurst",
        "salami",
        "speck",
        "geschnitten",
        "aufschnitt",
        "würstchen",
        "leberwurst",
        "mortadella",
        "schinken",
        "pizza",
        "fertiggerichte",
        "convenience",
        "burger",
        "pommes",
        "instant",
        "mikrowelle",
        "tiefkühlpizza",
        "bier",
        "wein",
        "spirituosen",
        "alkohol",
        "champagner",
        "prosecco",
        "weissbrot",
        "toast",
        "brötchen",
        "gipfeli",
        "croissant",
    ]

    healthy_keywords = [
        "bio",
        "organic",
        "vollkorn",
        "natur",
        "frisch",
        "ungesüsst",
        "zuckerfrei",
        "light",
        "fettarm",
        "vitamin",
        "unbehandelt",
    ]
    unhealthy_keywords = [
        "zucker",
        "süss",
        "schoko",
        "caramel",
        "vanille",
        "sahne",
        "rahm",
        "frittiert",
        "paniert",
        "gebacken",
        "crispy",
        "gesalzen",
    ]

    if any(p in category for p in healthy_patterns):
        return "healthy"
    if any(k in product for k in healthy_keywords):
        return "healthy"
    if any(p in category for p in unhealthy_patterns):
        return "unhealthy"
    if any(k in product for k in unhealthy_keywords):
        return "unhealthy"
    return "healthy"  # conservative default


# ------------------ Main ------------------


def run(ttl_path: Path, sparql_path: Path, out_path: Path) -> None:
    if not ttl_path.exists():
        raise FileNotFoundError(f"TTL not found: {ttl_path}")
    if not sparql_path.exists():
        raise FileNotFoundError(f"SPARQL not found: {sparql_path}")

    # Load query text
    query_text = sparql_path.read_text(encoding="utf-8").strip()
    if (
        not query_text[:10]
        .upper()
        .startswith(("PREFIX", "SELECT", "CONSTRUCT", "ASK", "DESCRIBE"))
    ):
        raise ValueError(
            f"SPARQL file must start with a SPARQL keyword. Preview: {query_text[:80]}"
        )

    # Load graph
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    # Run query
    rows = g.query(query_text)

    # Aggregate totals: (YYYY-MM, MonthName, healthy|unhealthy) -> CHF float
    totals: dict[tuple[str, str, str], float] = {}

    for binding in rows:
        # Your SELECT order: ?receipt ?date ?lineItem ?product ?productName ?category ?categoryLabel ?lineSubtotal ?quantity
        # We'll pick the ones we need by name (rdflib lets access by var name)
        b = binding.asdict()
        date_val = b.get("date")
        product_name = (
            str(b.get("productName", "")) if b.get("productName") is not None else ""
        )
        category_label = (
            str(b.get("categoryLabel", ""))
            if b.get("categoryLabel") is not None
            else ""
        )
        line_subtotal = b.get("lineSubtotal")

        if date_val is None or line_subtotal is None:
            continue

        # amount
        try:
            amount = parse_amount(str(line_subtotal))
        except Exception:
            continue

        # month
        try:
            isoYM, monthName = month_info(date_val)
        except Exception:
            continue

        # health
        health = classify_food_healthiness(category_label, product_name)

        key = (isoYM, monthName, health)
        totals[key] = totals.get(key, 0.0) + amount

    # Emit requested shape
    out_rows = []
    for isoYM, monthName, health in sorted(totals.keys()):
        chf_str = f"CHF {totals[(isoYM, monthName, health)]:.2f}"
        out_rows.append(
            {
                "category": health,
                "month": monthName,
                "monthISO": isoYM,
                "amount": chf_str,
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {out_path} ({len(out_rows)} rows).")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Healthy/Unhealthy monthly aggregator (Python + rdflib)"
    )
    ap.add_argument("--ttl", default=str(DEFAULT_TTL), help="Path to Turtle file")
    ap.add_argument("--sparql", default=str(DEFAULT_SPARQL), help="Path to SPARQL file")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Path to output JSON")
    args = ap.parse_args(argv)

    run(Path(args.ttl), Path(args.sparql), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
