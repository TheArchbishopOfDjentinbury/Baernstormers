// Healthy / Unhealthy monthly aggregator over a local TTL + SPARQL
// Uses: n3 (RDFJS store) + @comunica/query-sparql-rdfjs (query engine)

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Parser as N3Parser, Store as N3Store } from 'n3';
import { QueryEngine } from '@comunica/query-sparql-rdfjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- Paths (as you specified)
const TTL_PATH    = path.resolve(__dirname, '..', 'data', 'graph.ttl');            // data-extraction/data/graph.ttl
const SPARQL_PATH = path.resolve(__dirname, '..', 'queries', 'food-data.sparql');  // data-extraction/queries/food-data.sparql
const OUT_PATH    = path.resolve(__dirname, '..', 'output', 'healthy_spend.json');

// --- Helpers ---------------------------------------------------------------

// A little safer number parser (accepts "3,50" or "3.50")
function parseAmount(str) {
  if (str == null) return NaN;
  const s = String(str).replace(/\s+/g, '').replace(',', '.');
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : NaN;
}

// Try: full value; if invalid and looks like xsd:dateTime, try first 10 chars (YYYY-MM-DD)
function toMonthInfo(dateStr) {
  const direct = new Date(dateStr);
  let d = Number.isNaN(direct.getTime()) && typeof dateStr === 'string' && dateStr.length >= 10
    ? new Date(dateStr.slice(0, 10)) : direct;

  if (Number.isNaN(d.getTime())) throw new Error(`Bad date value: ${dateStr}`);

  const isoYM = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
  const monthName = d.toLocaleString('en-US', { month: 'long', timeZone: 'UTC' }); // "July"
  return { isoYM, monthName };
}

// Your categorization logic
function classifyFoodHealthiness(categoryLabel, productName) {
  const category = (categoryLabel || '').toLowerCase();
  const product  = (productName   || '').toLowerCase();

  const healthyPatterns = [
    'bananen','äpfel','birnen','orangen','zitronen','ananas','beeren','trauben',
    'gemüse','salate','abgepackte salate','tomaten','gurken','karotten','spinat',
    'kräuter','zwiebeln','kartoffeln','peperoni','auberginen','zucchini','brokkoli',
    'blumenkohl','kohl','rüebli','lauch','sellerie','radieschen','rucola',
    'fisch','meeresfrüchte','bohnen & hülsenfrüchte','linsen','kichererbsen',
    'nüsse','kerne','mandeln','walnüsse','haselnüsse',
    'alternativen zu milch & rahm','alternativen zu joghurts & desserts',
    'alternativen zu hackfleisch','alternativen zu burgern',
    'vollkorn','dinkel','hafer','quinoa','naturreis','wildreis',
    'wasser','mineralwasser','tee','kräutertee',
    'olivenöl','rapsöl','leinöl','essig','senf'
  ];

  const unhealthyPatterns = [
    'schokolade','bonbons','süssigkeiten','kekse','gebäck','kuchen','torten',
    'glacé','glace','eis','dessert','pudding','am stiel','pralinés',
    'chips','crackers','snacks','salzgebäck','nüssli','popcorn',
    'softdrinks','cola','limonade','energydrinks','süssgetränke',
    'fruchtsäfte','nektar','sirup','eistee',
    'wurst','salami','speck','geschnitten','aufschnitt','würstchen',
    'leberwurst','mortadella','schinken',
    'pizza','fertiggerichte','convenience','burger','pommes',
    'instant','mikrowelle','tiefkühlpizza',
    'bier','wein','spirituosen','alkohol','champagner','prosecco',
    'weissbrot','toast','brötchen','gipfeli','croissant'
  ];

  const healthyKeywords   = ['bio','organic','vollkorn','natur','frisch','ungesüsst','zuckerfrei','light','fettarm','vitamin','unbehandelt'];
  const unhealthyKeywords = ['zucker','süss','schoko','caramel','vanille','sahne','rahm','frittiert','paniert','gebacken','crispy','gesalzen'];

  if (healthyPatterns.some(p => category.includes(p))) return 'healthy';
  if (healthyKeywords.some(k => product.includes(k)))  return 'healthy';
  if (unhealthyPatterns.some(p => category.includes(p))) return 'unhealthy';
  if (unhealthyKeywords.some(k => product.includes(k)))  return 'unhealthy';
  return 'healthy'; // default
}

// Format CHF with 2 decimals, keep as "CHF X.YY" string
function chf(amountNumber) {
  return `CHF ${amountNumber.toFixed(2)}`;
}

// --- Main -----------------------------------------------------------------
async function main() {
  // Load & parse TTL into an RDFJS store (N3)
  const ttlText = await fs.readFile(TTL_PATH, 'utf8')
    .catch(err => { throw new Error(`Could not read TTL at ${TTL_PATH}: ${err.message}`); });

  const parser = new N3Parser({ format: 'text/turtle', baseIRI: 'file://' + TTL_PATH });
  const quads  = parser.parse(ttlText);
  const store  = new N3Store(quads);

  // Load SPARQL
  const queryText = (await fs.readFile(SPARQL_PATH, 'utf8'))
    .catch(err => { throw new Error(`Could not read SPARQL at ${SPARQL_PATH}: ${err.message}`); });
  if (!/^(PREFIX|SELECT|CONSTRUCT|ASK|DESCRIBE)/i.test(queryText.trim())) {
    throw new Error(`SPARQL must start with a SPARQL keyword. Preview: ${queryText.slice(0, 80)}`);
    }

  // Run query with the RDFJS engine (takes the store directly)
  const qe = new QueryEngine();
  const bindingsStream = await qe.queryBindings(queryText, { sources: [ store ] });

  // Aggregate totals: key = `${isoYM}|${monthName}|${healthy|unhealthy}` -> sum CHF
  const totals = new Map();

  for await (const b of bindingsStream) {
    const date          = b.get('date')?.value;
    const productName   = b.get('productName')?.value;
    const categoryLabel = b.get('categoryLabel')?.value;
    const subtotalStr   = b.get('lineSubtotal')?.value;

    if (!date || subtotalStr == null) continue;
    const amount = parseAmount(subtotalStr);
    if (!Number.isFinite(amount)) continue;

    const { isoYM, monthName } = toMonthInfo(date);
    const health = classifyFoodHealthiness(categoryLabel, productName);

    const key = `${isoYM}|${monthName}|${health}`;
    totals.set(key, (totals.get(key) || 0) + amount);
  }

  // Emit requested shape
  const rows = [...totals.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([key, amount]) => {
      const [iso, month, category] = key.split('|');
      return { category, month, monthISO: iso, amount: chf(amount) };
    });

  await fs.mkdir(path.dirname(OUT_PATH), { recursive: true });
  await fs.writeFile(OUT_PATH, JSON.stringify(rows, null, 2), 'utf8');

  console.log(`Wrote ${OUT_PATH} (${rows.length} rows).`);
}

main().catch(err => {
  console.error('❌ Failed:', err.message);
  process.exit(1);
});
