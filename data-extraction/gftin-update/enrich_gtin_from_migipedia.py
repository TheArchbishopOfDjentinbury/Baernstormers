#!/usr/bin/env python3
# -*- coding: utf-8 -*-

####DELETE DONT USE!#####

import argparse, json, re, sys, time
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from SPARQLWrapper import SPARQLWrapper, JSON, POST, BASIC

# ===================== GTIN helpers =====================
GTIN_RE = re.compile(r'\b(\d{8}|\d{12}|\d{13}|\d{14})\b')

def gs1_ok(code: str) -> bool:
    if not code or not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return False
    ds = [int(c) for c in code]
    chk = ds[-1]; body = ds[:-1]
    s = 0
    for i, d in enumerate(reversed(body)):  # weights 3,1,3,1,...
        s += d * (3 if i % 2 == 0 else 1)
    return (10 - (s % 10)) % 10 == chk

def to_gtin14(code: str) -> str:
    return code.zfill(14)

# ===================== React stream parsing (Priority) =====================
# Find: ..."children":"GTIN"... then the next ..."children":"<digits, ...>"...
RE_CHILDREN_GTIN = re.compile(r'"children"\s*:\s*"GTIN"', re.I)
RE_NEXT_CHILDREN = re.compile(r'"children"\s*:\s*"([^"]+)"', re.S)

def extract_from_react_with_rule(html: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Priority:
      1) In the React stream cell next to 'GTIN', return the FIRST 13-digit code
         starting with '76' that passes GS1.  -> method 'react-76-first'
      2) Otherwise, return the LAST valid GTIN found in that cell (prefer 13-digit,
         else any valid) -> method 'react-last'
      Returns (gtin14, method) or (None, None) if not found.
    """
    best_fallback_last_raw = None
    for m in RE_CHILDREN_GTIN.finditer(html):
        v = RE_NEXT_CHILDREN.search(html, m.end())
        if not v:
            continue
        cell = v.group(1)  # e.g. "7613312316528, 7613269190431, 76168765"
        codes = re.findall(r'\d{8,14}', cell)

        # Step 1: first 13-digit starting with 76 (Swiss), GS1-valid
        for c in codes:
            if len(c) == 13 and c.startswith("76") and gs1_ok(c):
                return to_gtin14(c), "react-76-first"

        # Step 2: last valid code in cell, prefer 13-digit if present
        valid_13 = [c for c in codes if len(c) == 13 and gs1_ok(c)]
        if valid_13:
            best_fallback_last_raw = valid_13[-1]
        else:
            valid_any = [c for c in codes if gs1_ok(c)]
            if valid_any:
                best_fallback_last_raw = valid_any[-1]

    if best_fallback_last_raw:
        return to_gtin14(best_fallback_last_raw), "react-last"
    return None, None

# ===================== Other extractors =====================
# Any JSON in <script> with keys like gtin/gtin13/ean/barcode
GTIN_KEY_RE = re.compile(r'"(?:gtin|gtin8|gtin12|gtin13|gtin14|ean|barcode)"\s*:\s*"?(\d{8,14})"?', re.I)

def _walk_jsonld(node):
    out = []
    if isinstance(node, dict):
        for k in ("gtin","gtin8","gtin12","gtin13","gtin14","ean","barcode"):
            v = node.get(k)
            if isinstance(v, str) and v.isdigit():
                out.append(v)
        for v in node.values():
            out += _walk_jsonld(v)
    elif isinstance(node, list):
        for v in node:
            out += _walk_jsonld(v)
    return out

def _extract_jsonld(soup: BeautifulSoup) -> List[str]:
    out = []
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        txt = (tag.string or tag.text or "").strip()
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        data = data if isinstance(data, list) else [data]
        for node in data:
            out += _walk_jsonld(node)
    return out

def _extract_any_script_json(soup: BeautifulSoup) -> List[str]:
    out = []
    for tag in soup.find_all("script"):
        raw = (tag.string or tag.text or "")
        if not raw:
            continue
        for m in GTIN_KEY_RE.finditer(raw):
            out.append(m.group(1))
    return out

def _extract_label_text(soup: BeautifulSoup) -> List[str]:
    text = soup.get_text(" ", strip=True)
    m = re.search(r'GTIN[^0-9]{0,40}(\d{8,14})', text, re.I)
    return [m.group(1)] if m else []

# ===================== Unified extractor =====================
def extract_gtin_from_html(html: str) -> Tuple[Optional[str], str]:
    """
    Returns (gtin14, method).
    Priority: React stream rule -> JSON-LD -> script JSON -> visible label -> regex.
    """
    # Priority: React rule
    gt, method = extract_from_react_with_rule(html)
    if gt:
        return gt, method

    soup = BeautifulSoup(html, "html.parser")

    # JSON-LD
    jsonld = [c for c in _extract_jsonld(soup) if gs1_ok(c)]
    if jsonld:
        # prefer longer codes, then lexical
        raw = sorted(jsonld, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "jsonld"

    # any <script> JSON blobs
    anyjs = [c for c in _extract_any_script_json(soup) if gs1_ok(c)]
    if anyjs:
        raw = sorted(anyjs, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "script"

    # visible label
    label = [c for c in _extract_label_text(soup) if gs1_ok(c)]
    if label:
        return to_gtin14(label[-1]), "label"

    # brute regex
    text_all = soup.get_text(" ", strip=True) + " " + (html or "")
    brute = [c for c in GTIN_RE.findall(text_all) if gs1_ok(c)]
    if brute:
        raw = sorted(brute, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "regex"

    return None, "none"

def fetch(url: str, session: requests.Session, timeout: int = 25) -> str:
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def try_extract(url: str, session: requests.Session) -> Tuple[Optional[str], str]:
    # 1) Original page
    try:
        html = fetch(url, session)
        gt, method = extract_gtin_from_html(html)
        if gt:
            return gt, method
    except Exception:
        pass
    # 2) Locale fallback: /de|fr|it/ -> /en/
    if re.search(r"/(de|fr|it)/", url):
        url_en = re.sub(r"/(de|fr|it)/", "/en/", url, count=1)
        try:
            html = fetch(url_en, session)
            gt, method = extract_gtin_from_html(html)
            if gt:
                return gt, f"{method}+en"
        except Exception:
            pass
    return None, "none"

# ===================== SPARQL & I/O =====================
# SELECT_TPL = """
# PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX sc: <https://static.rwpz.net/spendcast/schema#>


# SELECT DISTINCT ?product ?productName ?migrosId ?productUrl ?migipediaUrl ?categoryLabel ?description ?urlSel
# WHERE {{
#   ?product rdf:type sc:Product .
#   ?product sc:name ?productName .
#   ?product sc:migrosId ?migrosId .
#   ?product sc:productUrls ?productUrl .
#   OPTIONAL {{ ?product sc:migipediaUrl ?migipediaUrl }}
#   ?product sc:category ?category .
#   ?category rdfs:label ?categoryLabel .
#   OPTIONAL {{ ?product sc:description ?description }}

#   BIND(COALESCE(?migipediaUrl, ?productUrl) AS ?urlSel)
#   FILTER(CONTAINS(STR(?urlSel), "migipedia.migros.ch"))
# }}
# ORDER BY ?productName
# LIMIT {limit}
# """

SELECT_TPL = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX sc: <https://static.rwpz.net/spendcast/schema#>

SELECT DISTINCT ?prodById ?migrosId ?urlSel
WHERE {{
  ?prodById <https://static.rwpz.net/spendcast/schema#> ?migrosId .
  OPTIONAL {{ ?prodById <http://schema.org/migipediaUrl> ?migipediaUrl }}
  OPTIONAL {{ ?prodById <http://schema.org/productUrls> ?productUrl }}
  BIND(COALESCE(?migipediaUrl, ?productUrl) AS ?urlSel)
  FILTER(BOUND(?urlSel) && CONTAINS(STR(?urlSel), "migipedia.migros.ch"))
}}
ORDER BY ?migrosId
LIMIT {limit}
"""

def run_select(endpoint, query, user=None, password=None, verbose=False):
    sp = SPARQLWrapper(endpoint)
    sp.setReturnFormat(JSON)
    if user and password:
        sp.setHTTPAuth(BASIC); sp.setCredentials(user, password)
    sp.setQuery(query)
    if verbose:
        print("\n--- SELECT ---\n", query, "\n--------------\n", file=sys.stderr)
    return sp.query().convert()

def build_insert_triples(rows, predicate_iri, graph_iri=None):
    if not rows: return None
    triples = []
    for r in rows:
        prod = r.get("product"); gt = r.get("gtin14")
        if not (prod and gt): continue
        triples.append(f"<{prod}> <{predicate_iri}> \"{gt}\"^^<http://www.w3.org/2001/XMLSchema#string> .")
    body = "\n".join(triples)
    if graph_iri:
        return f"INSERT DATA {{ GRAPH <{graph_iri}> {{\n{body}\n}} }}"
    return f"INSERT DATA {{\n{body}\n}}"

def run_update(update_endpoint, update_query, user=None, password=None, verbose=False):
    sp = SPARQLWrapper(update_endpoint)
    sp.setMethod(POST)
    if user and password:
        sp.setHTTPAuth(BASIC); sp.setCredentials(user, password)
    sp.setQuery(update_query)
    if verbose:
        print("\n--- UPDATE ---\n", update_query, "\n--------------\n", file=sys.stderr)
    return sp.query()

def resolve_predicate(pred: str) -> str:
    if pred.startswith("http://") or pred.startswith("https://"):
        return pred
    if pred.startswith("sc:") or pred.startswith("schema:"):
        return "http://schema.org/" + pred.split(":", 1)[1]
    return pred

# ===================== Main =====================
def main():
    ap = argparse.ArgumentParser(description="Extract GTINs from Migipedia (prefer first 13-digit starting with 76) and update GraphDB.")
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--update-endpoint", required=True)
    ap.add_argument("--user"); ap.add_argument("--password")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--outfile", default="gtins.txt")
    ap.add_argument("--predicate", default="sc:gtin14")  # will resolve to http://schema.org/gtin14
    ap.add_argument("--graph", help="optional named graph IRI")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--test-url", help="Only test one URL and print the result.")
    args = ap.parse_args()

    predicate_iri = resolve_predicate(args.predicate)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "KG-GTIN-Enricher/76rule/1.0",
        "Accept-Language": "de-CH,de;q=0.9,en;q=0.8,fr;q=0.7,it;q=0.6",
    })

    # Debug single URL
    if args.test_url:
        gt, method = try_extract(args.test_url, session)
        print(f"{args.test_url} -> {gt or 'NONE'} [{method}]")
        return

    # 1) SELECT rows
    query = SELECT_TPL.format(limit=int(args.limit))
    data = run_select(args.endpoint, query, args.user, args.password, args.verbose)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        print("No rows matched your SPARQL.", file=sys.stderr)
        return

    rows = []
    for b in bindings:
        def v(k): return b.get(k, {}).get("value")
        rows.append({
            "product": v("product"),
            "migrosId": v("migrosId"),
            "urlSel": v("urlSel"),
        })

    # 2) Fetch & extract
    appended, inserts = 0, []
    for r in rows:
        url = r["urlSel"]
        if not url:
            continue
        gt, method = try_extract(url, session)
        if args.verbose:
            print(f"{r.get('migrosId','-')} {url} -> {gt or 'NONE'} [{method}]")
        if gt:
            with open(args.outfile, "a", encoding="utf-8") as f:
                f.write(f"{r.get('migrosId','')}\t{url}\t{gt}\n")
            appended += 1
            inserts.append({"product": r["product"], "gtin14": gt})
        time.sleep(args.delay)

    print(f"Wrote {appended} lines to {args.outfile}")

    # 3) INSERT into KG
    iq = build_insert_triples(inserts, predicate_iri, args.graph)
    if iq:
        try:
            run_update(args.update_endpoint, iq, args.user, args.password, args.verbose)
            print(f"Inserted {len(inserts)} GTIN triples.")
        except Exception as e:
            print(f"[UPDATE ERROR] {e}", file=sys.stderr)
    else:
        print("No triples to insert.")

if __name__ == "__main__":
    main()
