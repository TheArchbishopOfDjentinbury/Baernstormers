#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, re, sys, time
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from SPARQLWrapper import SPARQLWrapper, JSON, POST, BASIC

# ===== GTIN helpers =====
GTIN_RE = re.compile(r'\b(\d{8}|\d{12}|\d{13}|\d{14})\b')

def gs1_ok(code: str) -> bool:
    if not code or not code.isdigit() or len(code) not in (8,12,13,14):
        return False
    ds = [int(c) for c in code]; chk = ds[-1]; body = ds[:-1]
    s = 0
    for i, d in enumerate(reversed(body)):
        s += d * (3 if i % 2 == 0 else 1)
    return (10 - (s % 10)) % 10 == chk

def to_gtin14(code: str) -> str:
    return code.zfill(14)

# ===== React stream parsing (priority) =====
RE_CHILDREN_GTIN = re.compile(r'"children"\s*:\s*"GTIN"', re.I)
RE_NEXT_CHILDREN = re.compile(r'"children"\s*:\s*"([^"]+)"', re.S)

def extract_from_react_with_rule(html: str) -> Tuple[Optional[str], Optional[str]]:
    # 1) first 13-digit starting with 76; 2) else last valid in the cell
    fallback_last = None
    for m in RE_CHILDREN_GTIN.finditer(html):
        v = RE_NEXT_CHILDREN.search(html, m.end())
        if not v: continue
        cell = v.group(1)
        codes = re.findall(r'\d{8,14}', cell)
        for c in codes:
            if len(c) == 13 and c.startswith("76") and gs1_ok(c):
                return to_gtin14(c), "react-76-first"
        v13 = [c for c in codes if len(c)==13 and gs1_ok(c)]
        fallback_last = v13[-1] if v13 else ( [c for c in codes if gs1_ok(c)][-1] if [c for c in codes if gs1_ok(c)] else None )
    if fallback_last:
        return to_gtin14(fallback_last), "react-last"
    return None, None

# ===== Other extractors =====
GTIN_KEY_RE = re.compile(r'"(?:gtin|gtin8|gtin12|gtin13|gtin14|ean|barcode)"\s*:\s*"?(\d{8,14})"?', re.I)

def _walk_jsonld(node):
    out=[]
    if isinstance(node, dict):
        for k in ("gtin","gtin8","gtin12","gtin13","gtin14","ean","barcode"):
            v=node.get(k)
            if isinstance(v,str) and v.isdigit(): out.append(v)
        for v in node.values(): out += _walk_jsonld(v)
    elif isinstance(node, list):
        for v in node: out += _walk_jsonld(v)
    return out

def _extract_jsonld(soup):
    out=[]
    for tag in soup.find_all("script", {"type":"application/ld+json"}):
        txt=(tag.string or tag.text or "").strip()
        if not txt: continue
        try:
            data=json.loads(txt)
        except Exception:
            continue
        data=data if isinstance(data,list) else [data]
        for n in data: out += _walk_jsonld(n)
    return out

def _extract_any_script_json(soup):
    out=[]
    for tag in soup.find_all("script"):
        raw=(tag.string or tag.text or "")
        if not raw: continue
        for m in GTIN_KEY_RE.finditer(raw): out.append(m.group(1))
    return out

def _extract_label_text(soup):
    text=soup.get_text(" ", strip=True)
    m=re.search(r'GTIN[^0-9]{0,40}(\d{8,14})', text, re.I)
    return [m.group(1)] if m else []

def extract_gtin_from_html(html: str) -> Tuple[Optional[str], str]:
    gt, method = extract_from_react_with_rule(html)
    if gt: return gt, method
    soup = BeautifulSoup(html, "html.parser")
    jsonld=[c for c in _extract_jsonld(soup) if gs1_ok(c)]
    if jsonld:
        raw = sorted(jsonld, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "jsonld"
    anyjs=[c for c in _extract_any_script_json(soup) if gs1_ok(c)]
    if anyjs:
        raw = sorted(anyjs, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "script"
    label=[c for c in _extract_label_text(soup) if gs1_ok(c)]
    if label: return to_gtin14(label[-1]), "label"
    text_all = soup.get_text(" ", strip=True) + " " + (html or "")
    brute=[c for c in GTIN_RE.findall(text_all) if gs1_ok(c)]
    if brute:
        raw = sorted(brute, key=lambda x: (len(x), x), reverse=True)[0]
        return to_gtin14(raw), "regex"
    return None, "none"

def fetch(url: str, session: requests.Session, timeout: int = 25) -> str:
    r = session.get(url, timeout=timeout); r.raise_for_status(); return r.text

def try_extract(url: str, session: requests.Session) -> Tuple[Optional[str], str]:
    try:
        html = fetch(url, session)
        gt, method = extract_gtin_from_html(html)
        if gt: return gt, method
    except Exception: pass
    if re.search(r"/(de|fr|it)/", url):
        url_en = re.sub(r"/(de|fr|it)/", "/en/", url, count=1)
        try:
            html = fetch(url_en, session)
            gt, method = extract_gtin_from_html(html)
            if gt: return gt, f"{method}+en"
        except Exception: pass
    return None, "none"

# ===== FIXED SPARQL QUERY =====
# The key fix: Select products that have migipediaUrl AND ensure we get the product URI
SELECT_TPL = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX sc: <https://static.rwpz.net/spendcast/schema#>

SELECT DISTINCT ?prodById ?migrosId ?urlSel
WHERE {{
  ?prodById rdf:type sc:Product .
  ?prodById sc:migrosId ?migrosId .
  OPTIONAL {{ ?prodById sc:migipediaUrl ?migipediaUrl }}
  OPTIONAL {{ ?prodById sc:productUrls ?productUrl }}
  BIND(COALESCE(?migipediaUrl, ?productUrl) AS ?urlSel)
  FILTER(BOUND(?urlSel))
  # Filter for migipedia URLs if you want only those, or remove this filter for all URLs
  FILTER(CONTAINS(STR(?urlSel), "migipedia.migros.ch"))
}}
ORDER BY ?migrosId
{limit_clause}
"""

def run_select(endpoint, query, user=None, password=None, verbose=False):
    sp = SPARQLWrapper(endpoint); sp.setReturnFormat(JSON)
    if user and password: sp.setHTTPAuth(BASIC); sp.setCredentials(user, password)
    sp.setQuery(query)
    if verbose: print("\n--- SELECT ---\n", query, "\n--------------\n", file=sys.stderr)
    return sp.query().convert()

# ===== FIXED INSERT FUNCTION =====
def build_insert_triples(rows, predicate_iri, graph_iri=None):
    """Build INSERT query that adds GTIN to the actual product nodes"""
    if not rows: return None
    triples = []
    for r in rows:
        s = r.get("subject"); gt = r.get("gtin14")
        if not (s and gt): continue
        # This will add the GTIN property to the actual product URI
        triples.append(f"<{s}> <{predicate_iri}> \"{gt}\"^^<http://www.w3.org/2001/XMLSchema#string> .")
    
    if not triples: return None
    
    body = "\n".join(triples)
    if graph_iri:
        return f"INSERT DATA {{ GRAPH <{graph_iri}> {{\n{body}\n}} }}"
    else:
        return f"INSERT DATA {{\n{body}\n}}"

def run_update(update_endpoint, update_query, user=None, password=None, verbose=False):
    sp = SPARQLWrapper(update_endpoint); sp.setMethod(POST)
    if user and password: sp.setHTTPAuth(BASIC); sp.setCredentials(user, password)
    sp.setQuery(update_query)
    if verbose: print("\n--- UPDATE ---\n", update_query, "\n--------------\n", file=sys.stderr)
    return sp.query()

def resolve_predicate(pred: str) -> str:
    """Resolve predicate shortcuts to full URIs"""
    if pred.startswith("http://") or pred.startswith("https://"): 
        return pred
    if pred.startswith("sc:"):
        # Use Spendcast schema namespace
        return "https://static.rwpz.net/spendcast/schema#" + pred.split(":",1)[1]
    if pred.startswith("schema:"):
        return "http://schema.org/" + pred.split(":",1)[1]
    # Default to schema.org for backwards compatibility
    return f"http://schema.org/{pred}"

def main():
    ap = argparse.ArgumentParser(description="Attach gtin14 to products that have sc:migrosId.")
    ap.add_argument("--endpoint", required=True, help="SPARQL SELECT endpoint")
    ap.add_argument("--update-endpoint", required=True, help="SPARQL UPDATE endpoint")
    ap.add_argument("--user", help="SPARQL username")
    ap.add_argument("--password", help="SPARQL password")
    ap.add_argument("--limit", type=int, default=0, help="Limit products to process (0 = all products)")
    ap.add_argument("--outfile", default="gtins.txt", help="Output file for GTIN data")
    ap.add_argument("--predicate", default="schema:gtin14", help="Predicate to use (e.g., sc:gtin14, schema:gtin14)")
    ap.add_argument("--graph", help="Named graph URI (optional)")
    ap.add_argument("--delay", type=float, default=1.0, help="Delay between HTTP requests")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    ap.add_argument("--test-url", help="Just test one URL and print result.")
    ap.add_argument("--dry-run", action="store_true", help="Don't execute UPDATE, just show what would be done")
    args = ap.parse_args()

    pred_iri = resolve_predicate(args.predicate)
    if args.verbose:
        print(f"Using predicate: {pred_iri}", file=sys.stderr)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "KG-GTIN-Enricher/product-fix/1.0",
        "Accept-Language": "de-CH,de;q=0.9,en;q=0.8,fr;q=0.7,it;q=0.6",
    })

    if args.test_url:
        gt, method = try_extract(args.test_url, session)
        print(f"{args.test_url} -> {gt or 'NONE'} [{method}]")
        return

    # 1) Select products with their URIs and URLs
    limit_clause = f"LIMIT {int(args.limit)}" if args.limit > 0 else ""
    query = SELECT_TPL.format(limit_clause=limit_clause)
    if args.verbose:
        print(f"Executing query with limit={args.limit}", file=sys.stderr)
    
    data = run_select(args.endpoint, query, args.user, args.password, args.verbose)
    bindings = data.get("results", {}).get("bindings", [])
    
    if not bindings:
        print("No products matched. Check your endpoint and query.", file=sys.stderr)
        return

    print(f"Found {len(bindings)} products to process", file=sys.stderr)

    # 2) Extract product data
    items = []
    for b in bindings:
        def v(k): return b.get(k, {}).get("value")
        item = {
            "subject": v("prodById"),  # This is the product URI 
            "migrosId": v("migrosId"),
            "url": v("urlSel")
        }
        if item["subject"] and item["url"]:  # Only process if we have both
            items.append(item)

    print(f"Processing {len(items)} valid items", file=sys.stderr)

    # 3) Fetch GTINs and prepare inserts
    appended = 0
    inserts = []
    
    for i, item in enumerate(items):
        url = item["url"]
        subj = item["subject"]
        migros_id = item.get("migrosId", "unknown")
        
        if args.verbose:
            print(f"[{i+1}/{len(items)}] Processing {migros_id}: {url}", file=sys.stderr)
        
        gt, method = try_extract(url, session)
        
        if args.verbose:
            status = f"{gt or 'NONE'} [{method}]"
            print(f"  -> {status} -> will update {subj}", file=sys.stderr)
        else:
            print(f"{migros_id}: {gt or 'NONE'} [{method}]")
        
        if gt:
            # Write to output file
            with open(args.outfile, "a", encoding="utf-8") as f:
                f.write(f"{migros_id}\t{url}\t{gt}\t{subj}\n")
            appended += 1
            
            # Prepare for INSERT - this will add GTIN to the product URI
            inserts.append({"subject": subj, "gtin14": gt})
        
        if args.delay > 0:
            time.sleep(args.delay)

    print(f"\nWrote {appended} GTIN entries to {args.outfile}")

    # 4) Execute INSERT to add GTINs to product nodes
    if inserts:
        iq = build_insert_triples(inserts, pred_iri, args.graph)
        if iq:
            if args.dry_run:
                print("\n=== DRY RUN - Would execute this UPDATE: ===")
                print(iq)
                print("=== END DRY RUN ===")
            else:
                try:
                    run_update(args.update_endpoint, iq, args.user, args.password, args.verbose)
                    print(f"✅ Successfully inserted {len(inserts)} GTIN triples to product nodes.")
                except Exception as e:
                    print(f"❌ UPDATE ERROR: {e}", file=sys.stderr)
                    print(f"Query that failed:\n{iq}", file=sys.stderr)
        else:
            print("No valid triples to insert.")
    else:
        print("No GTINs extracted, nothing to insert.")

if __name__ == "__main__":
    main()