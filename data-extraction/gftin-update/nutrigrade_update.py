#!/usr/bin/env python3
"""
Script to identify all products with GTIN numbers from Spendcast database,
look up their Nutri-Score, NOVA Group, Eco-Score, and country of origin
using Open Food Facts API, then update the knowledge graph.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SPENDCAST_SPARQL_ENDPOINT = "http://graphdb-spendcast-vjkt3jacgq-ey.a.run.app/repositories/spendcast/"
SPENDCAST_UPDATE_ENDPOINT = "http://graphdb-spendcast-vjkt3jacgq-ey.a.run.app/repositories/spendcast/statements"
OPENFOODFACTS_API_BASE = "http://localhost:8000/api/v1/openfoodfacts"
OUTPUT_FILE = f"kg_update_results2.txt"
BATCH_SIZE = 10

# SPARQL query to get all products with GTIN numbers
FETCH_PRODUCTS_QUERY = """
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?product ?migrosId ?productName ?description ?gtin
WHERE {
  ?product exs:migrosId ?migrosId .
  ?product exs:name ?productName .
  OPTIONAL { ?product exs:description ?description . }
  BIND(STRAFTER(STR(?product), "http://static.rwpz.net/spendcast/gtin/") AS ?gtin)
  FILTER(BOUND(?migrosId) && BOUND(?productName) && BOUND(?gtin) && ?gtin != "")
}
ORDER BY ?migrosId
"""

# SPARQL INSERT template for updating products with Open Food Facts data
UPDATE_PRODUCT_TEMPLATE = """
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {{
  <{product_uri}> exs:nutriScore "{nutri_score}" ;
                  exs:novaGroup {nova_group} ;
                  exs:ecoScore "{eco_score}" ;
                  exs:countryOfOrigin "{country_of_origin}" ;
                  exs:openFoodFactsData "{off_data_json}"^^xsd:string ;
                  exs:lastUpdatedFromOFF "{timestamp}"^^xsd:dateTime .
}}
"""

class ProductUpdateInfo:
    """Class to store product and update information."""
    def __init__(self, product_uri: str, migros_id: str, name: str, gtin: str, description: str = ""):
        self.product_uri = product_uri
        self.migros_id = migros_id
        self.name = name
        self.gtin = gtin
        self.description = description
        
        # Open Food Facts data
        self.nutri_score = None
        self.nova_group = None
        self.eco_score = None
        self.country_of_origin = None
        self.off_data = None
        
        # Status tracking
        self.found_in_off = False
        self.updated_in_kg = False
        self.error_message = None


class KnowledgeGraphUpdater:
    """Main class for updating knowledge graph with Open Food Facts data."""
    
    def __init__(self):
        self.session = None
        self.products: List[ProductUpdateInfo] = []
        self.processed_count = 0
        self.found_count = 0
        self.updated_count = 0
        self.error_count = 0
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'Content-Type': 'application/sparql-query'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_all_products_from_spendcast(self) -> List[ProductUpdateInfo]:
        """Fetch all products with GTIN numbers from Spendcast database."""
        logger.info("Fetching all products with GTIN from Spendcast database...")
        
        try:
            async with self.session.post(
                SPENDCAST_SPARQL_ENDPOINT,
                data=FETCH_PRODUCTS_QUERY,
                headers={'Accept': 'application/sparql-results+json'}
            ) as response:
                if response.status != 200:
                    raise Exception(f"SPARQL query failed with status {response.status}")
                
                result = await response.json()
                bindings = result.get('results', {}).get('bindings', [])
                
                products = []
                for binding in bindings:
                    product = ProductUpdateInfo(
                        product_uri=binding['product']['value'],
                        migros_id=binding['migrosId']['value'],
                        name=binding['productName']['value'],
                        gtin=binding['gtin']['value'],
                        description=binding.get('description', {}).get('value', '')
                    )
                    products.append(product)
                
                logger.info(f"Fetched {len(products)} products with GTIN numbers from Spendcast")
                return products
                
        except Exception as e:
            logger.error(f"Error fetching products from Spendcast: {e}")
            raise
    
    async def lookup_product_in_openfoodfacts(self, product: ProductUpdateInfo) -> None:
        """Look up a single product in Open Food Facts API."""
        try:
            url = f"{OPENFOODFACTS_API_BASE}/product/{product.gtin}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success") and data.get("product"):
                        product_data = data["product"]
                        product.found_in_off = True
                        
                        # Extract key information
                        product.nutri_score = product_data.get("nutri_score") or product_data.get("nutri_score_grade")
                        product.nova_group = product_data.get("nova_group")
                        product.eco_score = product_data.get("eco_score") or product_data.get("eco_score_grade")
                        
                        # Extract country of origin (try multiple fields)
                        origins = product_data.get("origins") or product_data.get("manufacturing_places") or product_data.get("countries")
                        if isinstance(origins, list) and origins:
                            product.country_of_origin = origins[0]
                        elif isinstance(origins, str):
                            product.country_of_origin = origins.split(',')[0].strip() if origins else None
                        
                        # Store relevant OFF data as JSON string (limit to essential fields)
                        essential_data = {
                            'nutri_score': product.nutri_score,
                            'nova_group': product.nova_group,
                            'eco_score': product.eco_score,
                            'country_of_origin': product.country_of_origin,
                            'brand': product_data.get('brand'),
                            'categories': product_data.get('categories', [])[:5],  # Limit categories
                            'last_modified': product_data.get('last_modified_t')
                        }
                        product.off_data = json.dumps(essential_data, ensure_ascii=False)
                        
                        self.found_count += 1
                        logger.info(f"✓ Found {product.name} - Nutri-Score: {product.nutri_score}, NOVA: {product.nova_group}")
                    else:
                        product.error_message = data.get("message", "Product not found")
                        logger.debug(f"✗ Product not found: {product.name} (GTIN: {product.gtin})")
                else:
                    product.error_message = f"HTTP {response.status}"
                    logger.warning(f"✗ HTTP error {response.status} for {product.name}")
                    
        except Exception as e:
            product.error_message = str(e)
            logger.error(f"✗ Error looking up {product.name} (GTIN: {product.gtin}): {e}")
            self.error_count += 1
        
        self.processed_count += 1
    
    async def update_product_in_kg(self, product: ProductUpdateInfo) -> None:
        """Update a product in the knowledge graph with Open Food Facts data."""
        if not product.found_in_off:
            return
        
        try:
            # Prepare values for SPARQL (handle None values)
            nutri_score = product.nutri_score or "unknown"
            nova_group = product.nova_group if product.nova_group is not None else 0
            eco_score = product.eco_score or "unknown"
            country_of_origin = product.country_of_origin or "unknown"
            timestamp = datetime.now().isoformat()
            
            # Escape quotes in JSON data
            off_data_escaped = product.off_data.replace('"', '\\"') if product.off_data else "{}"
            
            # Build SPARQL UPDATE query
            update_query = UPDATE_PRODUCT_TEMPLATE.format(
                product_uri=product.product_uri,
                nutri_score=nutri_score,
                nova_group=nova_group,
                eco_score=eco_score,
                country_of_origin=country_of_origin,
                off_data_json=off_data_escaped,
                timestamp=timestamp
            )
            
            # Execute update
            async with self.session.post(
                SPENDCAST_UPDATE_ENDPOINT,
                data=update_query,
                headers={'Content-Type': 'application/sparql-update'}
            ) as response:
                if response.status in [200, 204]:
                    product.updated_in_kg = True
                    self.updated_count += 1
                    logger.info(f"✓ Updated KG for {product.name}")
                else:
                    error_text = await response.text()
                    product.error_message = f"KG update failed: HTTP {response.status} - {error_text}"
                    logger.error(f"✗ Failed to update KG for {product.name}: {response.status}")
                    
        except Exception as e:
            product.error_message = f"KG update error: {str(e)}"
            logger.error(f"✗ Error updating KG for {product.name}: {e}")
            self.error_count += 1
    
    async def process_products_in_batches(self, products: List[ProductUpdateInfo]) -> None:
        """Process products in batches."""
        logger.info(f"Processing {len(products)} products in batches of {BATCH_SIZE}")
        
        for i in range(0, len(products), BATCH_SIZE):
            batch = products[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(products) + BATCH_SIZE - 1) // BATCH_SIZE
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")
            
            # Step 1: Look up in Open Food Facts
            lookup_tasks = [self.lookup_product_in_openfoodfacts(product) for product in batch]
            await asyncio.gather(*lookup_tasks, return_exceptions=True)
            
            # Step 2: Update knowledge graph for found products
            update_tasks = [self.update_product_in_kg(product) for product in batch if product.found_in_off]
            if update_tasks:
                await asyncio.gather(*update_tasks, return_exceptions=True)
            
            # Brief pause between batches
            if i + BATCH_SIZE < len(products):
                await asyncio.sleep(2)
            
            # Progress update
            if batch_num % 10 == 0:
                logger.info(f"Progress: {batch_num}/{total_batches} batches completed")
    
    def write_results_to_file(self, products: List[ProductUpdateInfo]) -> None:
        """Write the results to a text file."""
        logger.info(f"Writing results to {OUTPUT_FILE}")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 100 + "\n")
            f.write("KNOWLEDGE GRAPH UPDATE RESULTS\n")
            f.write("=" * 100 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total products processed: {len(products)}\n")
            f.write(f"Products found in Open Food Facts: {self.found_count}\n")
            f.write(f"Products successfully updated in KG: {self.updated_count}\n")
            f.write(f"Products not found in OFF: {len(products) - self.found_count}\n")
            f.write(f"Errors encountered: {self.error_count}\n")
            f.write(f"Success rate (found): {(self.found_count/len(products)*100):.1f}%\n")
            f.write(f"Update rate (updated/found): {(self.updated_count/max(1,self.found_count)*100):.1f}%\n")
            f.write("=" * 100 + "\n\n")
            
            # Write successfully updated products
            f.write("PRODUCTS SUCCESSFULLY UPDATED IN KNOWLEDGE GRAPH:\n")
            f.write("-" * 70 + "\n")
            updated_products = [p for p in products if p.updated_in_kg]
            
            for product in updated_products:
                f.write(f"Migros ID: {product.migros_id}\n")
                f.write(f"Product Name: {product.name}\n")
                f.write(f"GTIN: {product.gtin}\n")
                f.write(f"Product URI: {product.product_uri}\n")
                f.write(f"Nutri-Score: {product.nutri_score or 'N/A'}\n")
                f.write(f"NOVA Group: {product.nova_group or 'N/A'}\n")
                f.write(f"Eco-Score: {product.eco_score or 'N/A'}\n")
                f.write(f"Country of Origin: {product.country_of_origin or 'N/A'}\n")
                f.write("-" * 70 + "\n")
            
            # Write products found but not updated (errors)
            f.write("\nPRODUCTS FOUND IN OFF BUT FAILED TO UPDATE IN KG:\n")
            f.write("-" * 70 + "\n")
            failed_updates = [p for p in products if p.found_in_off and not p.updated_in_kg]
            
            for product in failed_updates:
                f.write(f"Migros ID: {product.migros_id}\n")
                f.write(f"Product Name: {product.name}\n")
                f.write(f"GTIN: {product.gtin}\n")
                f.write(f"Error: {product.error_message}\n")
                f.write("-" * 50 + "\n")
            
            # Write products not found in OFF
            f.write("\nPRODUCTS NOT FOUND IN OPEN FOOD FACTS:\n")
            f.write("-" * 70 + "\n")
            not_found_products = [p for p in products if not p.found_in_off]
            
            # Only show first 50 to avoid huge files
            display_count = min(50, len(not_found_products))
            for product in not_found_products[:display_count]:
                f.write(f"Migros ID: {product.migros_id}\n")
                f.write(f"Product Name: {product.name}\n")
                f.write(f"GTIN: {product.gtin}\n")
                f.write("-" * 30 + "\n")
            
            if len(not_found_products) > 50:
                f.write(f"... and {len(not_found_products) - 50} more products not found\n")
            
            # Write summary statistics
            f.write(f"\nSUMMARY STATISTICS:\n")
            f.write("-" * 30 + "\n")
            
            # Nutri-Score distribution
            nutri_scores = {}
            for product in updated_products:
                score = product.nutri_score or "Unknown"
                nutri_scores[score] = nutri_scores.get(score, 0) + 1
            
            f.write("Nutri-Score Distribution (Updated Products):\n")
            for score, count in sorted(nutri_scores.items()):
                f.write(f"  {score}: {count} products\n")
            
            # NOVA Group distribution
            nova_groups = {}
            for product in updated_products:
                group = str(product.nova_group) if product.nova_group is not None else "Unknown"
                nova_groups[group] = nova_groups.get(group, 0) + 1
            
            f.write("\nNOVA Group Distribution (Updated Products):\n")
            for group, count in sorted(nova_groups.items()):
                f.write(f"  Group {group}: {count} products\n")
            
            # Country distribution
            countries = {}
            for product in updated_products:
                country = product.country_of_origin or "Unknown"
                countries[country] = countries.get(country, 0) + 1
            
            f.write("\nCountry of Origin Distribution (Updated Products):\n")
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {country}: {count} products\n")
        
        logger.info(f"Results written to {OUTPUT_FILE}")
    
    async def run(self) -> None:
        """Main execution method."""
        logger.info("Starting Knowledge Graph update process...")
        
        try:
            # Step 1: Fetch all products from Spendcast
            products = await self.fetch_all_products_from_spendcast()
            self.products = products
            
            if not products:
                logger.warning("No products found. Exiting.")
                return
            
            logger.info(f"Found {len(products)} products to process")
            
            # Step 2: Process products (lookup + update)
            await self.process_products_in_batches(products)
            
            # Step 3: Write results to file
            self.write_results_to_file(products)
            
            # Step 4: Print final summary
            logger.info("=" * 80)
            logger.info("PROCESS COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Total products processed: {len(products)}")
            logger.info(f"Products found in Open Food Facts: {self.found_count}")
            logger.info(f"Products updated in Knowledge Graph: {self.updated_count}")
            logger.info(f"Open Food Facts lookup success rate: {(self.found_count/len(products)*100):.1f}%")
            logger.info(f"Knowledge Graph update success rate: {(self.updated_count/max(1,self.found_count)*100):.1f}%")
            logger.info(f"Overall success rate: {(self.updated_count/len(products)*100):.1f}%")
            logger.info(f"Results saved to: {OUTPUT_FILE}")
            
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise


async def main():
    """Main entry point."""
    try:
        async with KnowledgeGraphUpdater() as updater:
            await updater.run()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)