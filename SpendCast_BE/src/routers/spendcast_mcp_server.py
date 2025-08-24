import asyncio
import json
import logging
import os

from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from datetime import datetime


import httpx
from dotenv import load_dotenv
from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Configuration ---
class GraphDBConfig(BaseModel):
    """Configuration for the GraphDB connection."""

    url: str = Field(..., description="The URL of the GraphDB SPARQL endpoint.")
    username: str = Field(..., description="The username for GraphDB authentication.")
    password: str = Field(..., description="The password for GraphDB authentication.")


# --- Open Food Facts Models ---
class ProductNutrition(BaseModel):
    """Nutritional information for a product."""

    energy: Optional[float] = None
    fat: Optional[float] = None
    saturated_fat: Optional[float] = None
    carbohydrates: Optional[float] = None
    sugars: Optional[float] = None
    proteins: Optional[float] = None
    salt: Optional[float] = None
    fiber: Optional[float] = None


class OpenFoodFactsProduct(BaseModel):
    """Product information from Open Food Facts."""

    id: str
    barcode: str
    name: str
    brands: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    nutri_score: Optional[str] = None
    nova_group: Optional[int] = None
    eco_score: Optional[str] = None
    image_url: Optional[str] = None
    nutrition_facts: Optional[ProductNutrition] = None
    labels: Optional[str] = None
    categories: Optional[str] = None
    countries: Optional[str] = None


def get_config() -> GraphDBConfig:
    """Loads configuration from environment variables."""
    graphdb_url = os.getenv(
        "GRAPHDB_URL", "http://localhost:7200/repositories/spendcast"
    )
    graphdb_user = os.getenv("GRAPHDB_USER", "")
    graphdb_password = os.getenv("GRAPHDB_PASSWORD", "")

    if not graphdb_url:
        logging.error("GRAPHDB_URL environment variable not set.")
        raise ValueError("GRAPHDB_URL environment variable not set.")

    return GraphDBConfig(
        url=graphdb_url, username=graphdb_user, password=graphdb_password
    )


mcp = FastMCP(
    name="spendcast-mcp",
    instructions="MCP server for executing SPARQL queries against a financial data triple store and accessing Open Food Facts nutritional data",
)


# --- Tool Definition ---
async def _execute_sparql_impl(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Internal implementation of SPARQL query execution.

    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    log_file_path = "/tmp/debug.txt"
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] --- EXECUTING SPARQL QUERY ---\n{query}\n\n"
            f.write(log_entry)
    except IOError as e:
        logging.error(f"Failed to write to log file {log_file_path}: {e}")

    config = get_config()
    logging.info(f"Executing SPARQL query on {config.url}")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json",
    }
    data = {"query": query}
    auth = httpx.BasicAuth(config.username, config.password)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.url, headers=headers, data=data, auth=auth, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"An error occurred while connecting to GraphDB: {e}"
        logging.error(error_msg)
        return {"error": error_msg}
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response from GraphDB.")
        return {"error": "Invalid JSON response from GraphDB."}


# --- Open Food Facts Utilities ---
async def _fetch_openfoodfacts_product(barcode: str) -> Optional[OpenFoodFactsProduct]:
    """
    Fetch product information from Open Food Facts API by barcode.

    :param barcode: Product barcode
    :return: Product information or None if not found
    """
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != 1 or "product" not in data:
                return None

            product_data = data["product"]

            # Extract nutritional information
            nutrition = None
            if "nutriments" in product_data:
                nutriments = product_data["nutriments"]
                nutrition = ProductNutrition(
                    energy=nutriments.get("energy-kcal_100g"),
                    fat=nutriments.get("fat_100g"),
                    saturated_fat=nutriments.get("saturated-fat_100g"),
                    carbohydrates=nutriments.get("carbohydrates_100g"),
                    sugars=nutriments.get("sugars_100g"),
                    proteins=nutriments.get("proteins_100g"),
                    salt=nutriments.get("salt_100g"),
                    fiber=nutriments.get("fiber_100g"),
                )

            # Create product object
            product = OpenFoodFactsProduct(
                id=barcode,
                barcode=barcode,
                name=product_data.get("product_name", ""),
                brands=product_data.get("brands", ""),
                ingredients=product_data.get("ingredients_text", ""),
                allergens=product_data.get("allergens", ""),
                nutri_score=product_data.get("nutriscore_grade", "").upper(),
                nova_group=product_data.get("nova_group"),
                eco_score=product_data.get("ecoscore_grade", "").upper(),
                image_url=product_data.get("image_url", ""),
                nutrition_facts=nutrition,
                labels=product_data.get("labels", ""),
                categories=product_data.get("categories", ""),
                countries=product_data.get("countries", ""),
            )

            return product

    except httpx.HTTPStatusError as e:
        logging.error(
            f"HTTP error fetching product {barcode}: {e.response.status_code}"
        )
        return None
    except httpx.RequestError as e:
        logging.error(f"Request error fetching product {barcode}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching product {barcode}: {e}")
        return None


async def _search_openfoodfacts_products(
    query: str, page: int = 1, page_size: int = 10
) -> List[OpenFoodFactsProduct]:
    """
    Search for products in Open Food Facts by name or brand.

    :param query: Search query
    :param page: Page number (1-based)
    :param page_size: Number of results per page
    :return: List of products
    """
    encoded_query = quote_plus(query)
    url = "https://world.openfoodfacts.org/cgi/search.pl"

    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": min(page_size, 50),  # API limit
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            data = response.json()

            products = []
            if "products" in data:
                for product_data in data["products"]:
                    # Extract nutritional information
                    nutrition = None
                    if "nutriments" in product_data:
                        nutriments = product_data["nutriments"]
                        nutrition = ProductNutrition(
                            energy=nutriments.get("energy-kcal_100g"),
                            fat=nutriments.get("fat_100g"),
                            saturated_fat=nutriments.get("saturated-fat_100g"),
                            carbohydrates=nutriments.get("carbohydrates_100g"),
                            sugars=nutriments.get("sugars_100g"),
                            proteins=nutriments.get("proteins_100g"),
                            salt=nutriments.get("salt_100g"),
                            fiber=nutriments.get("fiber_100g"),
                        )

                    # Create product object
                    product = OpenFoodFactsProduct(
                        id=product_data.get("code", ""),
                        barcode=product_data.get("code", ""),
                        name=product_data.get("product_name", ""),
                        brands=product_data.get("brands", ""),
                        ingredients=product_data.get("ingredients_text", ""),
                        allergens=product_data.get("allergens", ""),
                        nutri_score=product_data.get("nutriscore_grade", "").upper(),
                        nova_group=product_data.get("nova_group"),
                        eco_score=product_data.get("ecoscore_grade", "").upper(),
                        image_url=product_data.get("image_url", ""),
                        nutrition_facts=nutrition,
                        labels=product_data.get("labels", ""),
                        categories=product_data.get("categories", ""),
                        countries=product_data.get("countries", ""),
                    )
                    products.append(product)

            return products

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error searching products: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        logging.error(f"Request error searching products: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error searching products: {e}")
        return []


@mcp.tool()
def get_schema_help() -> Dict[str, Any]:
    """
    Get schema documentation and query examples for the financial data store.

    This tool provides immediate access to schema information and working examples
    to help you write SPARQL queries. No need to access separate resources.

    :return: Dictionary containing schema content and examples
    """
    return {
        "schema_summary": get_schema_summary.fn(),
        "example_queries": get_example_queries.fn(),
        "ontology": get_ontology_content.fn(),
        "description": "Complete schema information and examples for writing SPARQL queries",
        "quick_tips": [
            "Use exs: prefix for schema properties (e.g., exs:hasAccount)",
            "Use ex: prefix for data instances (e.g., ex:Swiss_franc)",
            "Transactions use accounts, not cards directly",
            "Check the schema_summary for entity relationships",
            "See example_queries for working SPARQL patterns",
        ],
        "note": "All content is included directly - no need to access separate resources",
        "ontology_source": "Local files with online fallback at https://static.rwpz.net/spendcast/schema#",
    }


@mcp.tool()
def get_schema_content(resource_name: str = "schema_summary") -> Dict[str, Any]:
    """
    Get the actual content of schema resources instead of just the URIs.

    This tool reads and returns the content of schema resources, making it easier
    to access schema information without having to use MCP resource reading.

    :param resource_name: Which resource to read. Options: "schema_summary", "example_queries", "ontology"
    :return: Dictionary containing the resource content and metadata
    """
    resource_map = {
        "schema_summary": ("internal://schema_summary.md", get_schema_summary.fn),
        "example_queries": ("internal://example_queries.md", get_example_queries.fn),
        "ontology": (
            "https://static.rwpz.net/spendcast/schema#",
            get_ontology_content.fn,
        ),
    }

    if resource_name not in resource_map:
        return {
            "error": f"Unknown resource: {resource_name}",
            "available_resources": list(resource_map.keys()),
            "suggestion": "Use one of the available resource names",
        }

    uri, resource_func = resource_map[resource_name]

    try:
        content = resource_func()
        return {
            "resource_name": resource_name,
            "uri": uri,
            "content": content,
            "content_length": len(content),
            "note": "This is the actual content, not just a URI reference",
        }
    except Exception as e:
        return {
            "error": f"Failed to read resource {resource_name}: {str(e)}",
            "resource_name": resource_name,
            "uri": uri,
        }


@mcp.tool()
async def execute_sparql(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Execute SPARQL queries against a financial data triple store containing comprehensive banking, transaction, and retail data. The store includes:\n\n

    **IMPORTANT: Before writing queries, use these tools for schema help:**
    - `get_schema_help()` - Complete schema information and examples (recommended)
    - `get_schema_content('schema_summary')` - Read entity relationships and schema patterns
    - `get_schema_content('example_queries')` - Read working SPARQL examples

    **Core Financial Entities:**\n
    - **Accounts**: Checking, savings, credit cards, retirement accounts (3A pillar)\n
    - **Parties**: People (customers) and organizations (banks, merchants) with detailed contact information\n
    - **Payment Cards**: Credit/debit cards linked to accounts for transactions\n
    - **Financial Transactions**: Complete transaction records with amounts, dates, status, and types\n\n
    **Retail & Receipt Data:**\n
    - **Receipts**: Detailed purchase receipts with line items, dates, and payment methods\n
    - **Products**: Migros product catalog with EAN codes, names, and category links\n
    - **Product Categories**: Hierarchical classification (beverages, bread, cleaning, etc.)\n
    - **Merchants**: Business entities with names and addresses\n\n
    **Key Data Properties:**\n
    - Transaction amounts in CHF with currency information\n
    - Complete transaction dates and status tracking\n
    - Account balances and payment card details\n
    - Product information and receipt line items\n
    - Customer account and card relationships\n\n
    **Query Capabilities:**\n
    - Find transactions by customer, date, amount, or merchant\n
    - Analyze spending patterns through accounts and payment cards\n
    - Track account balances and payment card usage\n
    - Search products and receipt details\n
    - Analyze customer financial relationships\n\n
    **Important Data Structure Insights:**\n
    - **Customers** are `exs:Person` entities with direct `exs:hasAccount` relationships\n
    - **Payment Cards** are linked to accounts via `exs:linkedAccount`\n
    - **Transactions** use accounts (not cards directly) through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`\n
    - **Product Categories** now work correctly with proper `exs:category` relationships and hierarchical structure\n
    - **Party Roles** (Payer, Payee, AccountHolder, CardHolder) mediate relationships between entities\n\n
    **Common Query Patterns:**\n
    - Use `exs:` prefix for schema properties (e.g., `exs:hasMonetaryAmount`)\n
    - Use `ex:` prefix for data instances (e.g., `ex:Swiss_franc`)\n
    - Find customer transactions through accounts: `?person exs:hasAccount ?account`\n
    - Find card transactions through linked accounts: `?card exs:linkedAccount ?account`\n
    - Join transactions with receipts using `exs:hasReceipt`

    **💡 Pro Tip:** Use `get_schema_help()` to get complete schema information and examples before writing queries!\n\n

    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    return await _execute_sparql_impl(ctx, query)


# --- Resource Tools ---
# Resources will be added after the functions are defined


@mcp.resource(
    "internal://schema_summary.md",
    name="schema_summary",
    description="Human-readable summary of key triple store entities and relationships",
    mime_type="text/markdown",
)
def get_schema_summary() -> str:
    """Generate a human-readable schema summary."""
    return """
**Key Insights**: 
- **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
- **Role-based relationships**: `?account exs:hasAccountHolder ?role` → `?role exs:isPlayedBy ?person`
- **Card-account linking**: `?card exs:linkedAccount ?account` (cards use accounts for transactions)
- **Transaction participation**: Through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`
"""


@mcp.resource(
    "internal://example_queries.md",
    name="example_queries",
    description="Common SPARQL query patterns and examples for the financial data store",
    mime_type="text/markdown",
)
def get_example_queries() -> str:
    """Generate example SPARQL queries."""
    return """# Example SPARQL Queries for Financial Data Store

## Important Note on Customer-Transaction Relationships

**Customers (Persons) have both direct and role-based relationships:**

1. **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
2. **Role-based relationships**: 
   - `?account exs:hasAccountHolder ?holderRole` → `?holderRole exs:isPlayedBy ?person`
   - `?card exs:hasCardHolder ?cardHolderRole` → `?cardHolderRole exs:isPlayedBy ?person`

**Transactions have participants through Party Roles:**
- `?transaction exs:hasParticipant ?payerRole` → `?payerRole exs:isPlayedBy ?payer`
- `?transaction exs:hasParticipant ?payeeRole` → `?payeeRole exs:isPlayedBy ?payee`

**Key Party Role Types:**
- `exs:Payer` - The party paying money
- `exs:Payee` - The party receiving money  
- `exs:AccountHolder` - The party owning an account
- `exs:CardHolder` - The party holding a payment card
- `exs:AccountProvider` - The bank providing an account
- `exs:CardIssuer` - The bank issuing a payment card

**Important**: Payment cards are linked to accounts via `exs:linkedAccount`, and transactions use the linked account (not the card directly).

## Customer Analysis

### 1. Find All Transactions for a Specific Customer 
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
  # Find the customer
  ?customer exs:hasName "CUSTOMER NAME" .
  
  # Option 1: Through bank accounts (customer is payer)
  {
    ?customer exs:hasAccount ?account .
    ?account a ?payer_type .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?account .
  }
  UNION
  # Option 2: Through payment cards (customer is payer)
  {
    ?customer exs:hasPaymentCard ?card .
    ?card exs:linkedAccount ?account_linked_to_card . # <-- Find the linked account
    ?account_linked_to_card a ?payer_type .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?account_linked_to_card . # <-- Use the ACCOUNT as the Payer
  }

  # Get transaction details
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
  
  # Get merchant information (merchant is payee)
  ?transaction exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee ;
    exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant .
}
ORDER BY DESC(?date)
```

### 1a. Find Transactions Through Bank Accounts Only 
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?account_type WHERE {
  ?customer exs:hasName "CUSTOMER NAME" .
  ?account exs:hasAccountHolder ?holderRole .
  ?holderRole exs:isPlayedBy ?customer .
  ?account a ?account_type .
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer ;
    exs:isPlayedBy ?account .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
}
ORDER BY DESC(?date)
```

### 1b. Find Transactions Through Payment Cards Only 
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?card_type WHERE {
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  ?card exs:hasCardHolder ?cardHolderRole .
  ?cardHolderRole exs:isPlayedBy ?customer .
  ?card a ?card_type .
  ?card exs:linkedAccount ?linked_account . # 1. Find the card's linked account
  
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer ;
    exs:isPlayedBy ?linked_account . # 2. Find transactions where the LINKED ACCOUNT is the payer
    
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
}
ORDER BY DESC(?date)
```

### 2. Customer Account Summary
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?account ?type ?balance ?currency WHERE {
  ?account a ?account_type ;
    exs:hasAccountHolder ?holder_role .
  ?holder_role exs:isPlayedBy ?customer .
  ?customer exs:hasName "CUSTOMER NAME" .
  ?account exs:hasInitialBalance ?balance ;
    exs:hasCurrency ?currency .
  VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
}
```

## Spending Analysis

### 3. Monthly Spending by Category 
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?month ?category ?category_label (SUM(?amount) AS ?total_spent) WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasTransactionDate ?date ;
    exs:hasReceipt ?receipt .
  ?receipt exs:hasLineItem ?line_item .
  ?line_item exs:hasProduct ?product .
  ?product exs:hasCategory ?category .
  ?category rdfs:label ?category_label .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  BIND(STRDT(CONCAT(YEAR(?date), "-", STR(MONTH(?date)), "-01"), xsd:date) AS ?month)
  FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-12-31"^^xsd:date)
}
GROUP BY ?month ?category ?category_label
ORDER BY ?month DESC(?total_spent)
```

**Note**: This example is now working! The product categories have been fixed and return real spending data by category and month.

### 4. Top Spending Merchants 
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?merchant (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee ;
    exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  FILTER(?transaction exs:transactionType "expense")
}
GROUP BY ?merchant
ORDER BY DESC(?total_spent)
LIMIT 20
```

### 5. Payment Card Usage Patterns

```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?card ?card_type ?total_spent ?transaction_count WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasCard ?card .
  ?card exs:cardType ?card_type ;
    exs:cardNumber ?card_number .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  FILTER(?transaction exs:transactionType "expense")
}
GROUP BY ?card ?card_type ?card_number
ORDER BY DESC(?total_spent)
```

### 6. Currency Conversion Analysis
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?base_currency ?counter_currency ?exchange_rate ?date WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasCurrencyConversion ?conversion .
  ?conversion exs:hasBaseAmount ?base_amount ;
    exs:hasCounterAmount ?counter_amount ;
    exs:exchangeRate ?exchange_rate ;
    exs:conversionDate ?date .
  ?base_amount exs:hasCurrency ?base_currency .
  ?counter_amount exs:hasCurrency ?counter_currency .
}
ORDER BY DESC(?date)
```
## Tips for Writing Queries

"""


@mcp.resource(
    "https://static.rwpz.net/spendcast/schema#",
    name="triple_store_schema",
    description="Complete ontology and schema for the financial data triple store",
    mime_type="text/turtle",
)
def get_ontology_content() -> str:
    """Read the ontology.ttl file content with online fallback."""
    try:
        # Try data/ontology.ttl first (for development)
        ontology_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "ontology.ttl"
        )
        if not os.path.exists(ontology_path):
            # Fall back to deploy/ontology.ttl (for production)
            ontology_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "deploy", "ontology.ttl"
            )

        with open(ontology_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to online ontology
        try:
            # Create a simple async function to fetch the online ontology
            async def fetch_online_ontology():
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://static.rwpz.net/spendcast/schema#", timeout=10.0
                    )
                    response.raise_for_status()
                    return response.text

            # Run the async function in a new event loop if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, we can't use run_until_complete
                    return "# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#"
                else:
                    return loop.run_until_complete(fetch_online_ontology())
            except RuntimeError:
                # No event loop available, return the URL
                return "# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#"

        except Exception as fetch_error:
            return f"# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#\n# Error fetching online version: {str(fetch_error)}"
    except Exception as e:
        return f"# Error reading ontology file: {str(e)}\n# Online ontology available at: https://static.rwpz.net/spendcast/schema#"


# --- Query Validation ---
def validate_sparql_query(query: str) -> tuple[bool, str]:
    """
    Basic SPARQL query validation.

    :param query: The SPARQL query string to validate
    :return: Tuple of (is_valid, error_message)
    """
    # Check for required prefixes
    required_prefixes = ["exs:", "ex:"]
    missing_prefixes = []

    for prefix in required_prefixes:
        if prefix not in query:
            missing_prefixes.append(prefix)

    if missing_prefixes:
        return False, f"Missing required prefixes: {', '.join(missing_prefixes)}"

    # Check for basic SPARQL syntax
    if not query.strip().upper().startswith(("SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
        return False, "Query must start with SELECT, ASK, CONSTRUCT, or DESCRIBE"

    # Check for balanced braces
    if query.count("{") != query.count("}"):
        return False, "Unbalanced braces in SPARQL query"

    # Check for basic WHERE clause
    if "{" not in query or "}" not in query:
        return False, "Missing WHERE clause with braces"

    return True, "Query is valid"


# --- Enhanced SPARQL Tool with Validation ---
@mcp.tool()
async def execute_sparql_validated(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Execute SPARQL queries with validation against a financial data triple store.

    This tool provides the same functionality as execute_sparql but includes
    basic query validation to catch common syntax errors before sending to GraphDB.

    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    # Validate the query first
    is_valid, error_message = validate_sparql_query(query)
    if not is_valid:
        return {
            "error": f"SPARQL validation failed: {error_message}",
            "query": query,
            "validation_tips": [
                "Ensure your query starts with SELECT, ASK, CONSTRUCT, or DESCRIBE",
                "Include both exs: and ex: prefixes",
                "Check that all braces { } are properly balanced",
                "Verify your WHERE clause syntax",
            ],
        }

    # If validation passes, execute the query
    return await _execute_sparql_impl(ctx, query)


# --- Open Food Facts Tools ---
@mcp.tool()
async def search_food_products(
    ctx: Context, query: str, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """
    Search for food products in the Open Food Facts database by name, brand, or keywords.

    This tool allows you to find products by searching for specific terms. You can search by:
    - Product name (e.g., "nutella", "coca cola")
    - Brand name (e.g., "ferrero", "nestle")
    - Category (e.g., "chocolate", "cereals")
    - General keywords

    :param ctx: The tool context (unused in this implementation).
    :param query: Search query - product name, brand, or keywords
    :param page: Page number for pagination (default: 1)
    :param page_size: Number of results per page (max: 50, default: 10)
    :return: Dictionary containing search results and metadata
    """
    if not query or len(query.strip()) < 2:
        return {
            "error": "Search query must be at least 2 characters long",
            "products": [],
            "total_found": 0,
        }

    try:
        products = await _search_openfoodfacts_products(query.strip(), page, page_size)

        # Convert products to dictionaries for JSON serialization
        products_data = []
        for product in products:
            product_dict = product.dict()
            # Convert nutrition facts to dict if present
            if product_dict["nutrition_facts"]:
                product_dict["nutrition_facts"] = product_dict["nutrition_facts"]
            products_data.append(product_dict)

        return {
            "products": products_data,
            "total_found": len(products_data),
            "page": page,
            "page_size": page_size,
            "query": query,
            "message": f"Found {len(products_data)} products matching '{query}'",
        }

    except Exception as e:
        logging.error(f"Error searching food products: {e}")
        return {
            "error": f"Failed to search products: {str(e)}",
            "products": [],
            "total_found": 0,
        }


@mcp.tool()
async def get_food_product_by_barcode(ctx: Context, barcode: str) -> Dict[str, Any]:
    """
    Get detailed information about a food product by its barcode (EAN, UPC, etc.).

    This tool fetches comprehensive product information from Open Food Facts including:
    - Basic product details (name, brand, ingredients)
    - Nutritional information per 100g
    - Quality scores (Nutri-Score, Nova Group, Eco-Score)
    - Allergen information
    - Product images
    - Categories and labels

    :param ctx: The tool context (unused in this implementation).
    :param barcode: Product barcode (EAN, UPC, etc.) - usually 8-13 digits
    :return: Dictionary containing detailed product information
    """
    if not barcode or not barcode.strip():
        return {"error": "Barcode is required", "product": None}

    # Clean the barcode
    clean_barcode = barcode.strip()

    try:
        product = await _fetch_openfoodfacts_product(clean_barcode)

        if not product:
            return {
                "error": f"Product with barcode {clean_barcode} not found in Open Food Facts database",
                "product": None,
                "barcode": clean_barcode,
            }

        # Convert to dictionary for JSON serialization
        product_dict = product.dict()

        return {
            "product": product_dict,
            "barcode": clean_barcode,
            "message": f"Successfully retrieved product: {product.name}",
        }

    except Exception as e:
        logging.error(f"Error fetching product by barcode {clean_barcode}: {e}")
        return {
            "error": f"Failed to fetch product: {str(e)}",
            "product": None,
            "barcode": clean_barcode,
        }


@mcp.tool()
async def analyze_nutrition_spending(
    ctx: Context,
    customer_name: str,
    start_date: str,
    end_date: str,
    nutrition_focus: str = "general",
) -> Dict[str, Any]:
    """
    Analyze customer spending from a nutritional perspective by combining transaction data with Open Food Facts.

    This tool provides insights into spending patterns based on nutritional quality:
    - Spending on products by Nutri-Score (A-E rating)
    - Analysis by Nova Group (1-4, processing level)
    - Eco-Score analysis for environmental impact
    - Categorization by nutritional categories

    :param ctx: The tool context (unused in this implementation).
    :param customer_name: Customer name to analyze (e.g., "Jeanine Marie Blumenthal")
    :param start_date: Start date for analysis (YYYY-MM-DD format)
    :param end_date: End date for analysis (YYYY-MM-DD format)
    :param nutrition_focus: Focus of analysis - "nutriscore", "nova", "eco", or "general"
    :return: Dictionary containing nutritional spending analysis
    """
    if not all([customer_name, start_date, end_date]):
        return {
            "error": "customer_name, start_date, and end_date are required",
            "analysis": None,
        }

    try:
        # First, get customer transactions with products that have EAN codes
        sparql_query = f"""
        PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
        PREFIX ex: <https://static.rwpz.net/spendcast/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?transaction ?amount ?date ?productName ?ean WHERE {{
            ?person exs:hasName "{customer_name}" .
            ?person exs:hasAccount ?account .
            
            ?transaction a exs:FinancialTransaction ;
                        exs:hasParticipant ?payerRole ;
                        exs:hasMonetaryAmount ?amount_uri ;
                        exs:hasTransactionDate ?date ;
                        exs:hasReceipt ?receipt .
            
            ?payerRole a exs:Payer ;
                      exs:isPlayedBy ?account .
            
            ?amount_uri exs:hasAmount ?amount .
            
            ?receipt exs:hasLineItem ?lineItem .
            ?lineItem exs:hasProduct ?product ;
                     exs:quantity ?quantity .
            
            ?product exs:name ?productName .
            OPTIONAL {{ ?product exs:hasEAN ?ean . }}
            
            FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)
        }}
        ORDER BY ?date
        """

        # Execute SPARQL query
        sparql_result = await _execute_sparql_impl(ctx, sparql_query)

        if "error" in sparql_result:
            return {
                "error": f"Failed to fetch transaction data: {sparql_result['error']}",
                "analysis": None,
            }

        if not sparql_result.get("results", {}).get("bindings"):
            return {
                "message": "No transactions found for the specified period",
                "analysis": {
                    "total_transactions": 0,
                    "nutritional_breakdown": {},
                    "recommendations": [],
                },
            }

        # Process transactions and enrich with Open Food Facts data
        transactions = sparql_result["results"]["bindings"]
        nutrition_analysis = {
            "nutri_score_spending": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "E": 0,
                "unknown": 0,
            },
            "nova_group_spending": {"1": 0, "2": 0, "3": 0, "4": 0, "unknown": 0},
            "eco_score_spending": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "E": 0,
                "unknown": 0,
            },
            "total_amount": 0,
            "analyzed_products": 0,
            "products_with_nutrition_data": 0,
            "products_with_ean": 0,
        }

        # Process each transaction
        for transaction in transactions:
            amount = float(transaction["amount"]["value"])
            product_name = transaction["productName"]["value"]

            nutrition_analysis["total_amount"] += amount
            nutrition_analysis["analyzed_products"] += 1

            # Check if EAN code is available
            if "ean" in transaction and transaction["ean"]["value"]:
                ean = transaction["ean"]["value"]
                nutrition_analysis["products_with_ean"] += 1

                # Fetch nutrition data from Open Food Facts
                off_product = await _fetch_openfoodfacts_product(ean)

                if off_product:
                    nutrition_analysis["products_with_nutrition_data"] += 1

                    # Categorize by Nutri-Score
                    nutri_score = off_product.nutri_score or "unknown"
                    if nutri_score.lower() in ["a", "b", "c", "d", "e"]:
                        nutrition_analysis["nutri_score_spending"][
                            nutri_score.upper()
                        ] += amount
                    else:
                        nutrition_analysis["nutri_score_spending"]["unknown"] += amount

                    # Categorize by Nova Group
                    nova_group = (
                        str(off_product.nova_group)
                        if off_product.nova_group
                        else "unknown"
                    )
                    if nova_group in ["1", "2", "3", "4"]:
                        nutrition_analysis["nova_group_spending"][nova_group] += amount
                    else:
                        nutrition_analysis["nova_group_spending"]["unknown"] += amount

                    # Categorize by Eco-Score
                    eco_score = off_product.eco_score or "unknown"
                    if eco_score.lower() in ["a", "b", "c", "d", "e"]:
                        nutrition_analysis["eco_score_spending"][eco_score.upper()] += (
                            amount
                        )
                    else:
                        nutrition_analysis["eco_score_spending"]["unknown"] += amount
                else:
                    # No nutrition data available for this EAN
                    nutrition_analysis["nutri_score_spending"]["unknown"] += amount
                    nutrition_analysis["nova_group_spending"]["unknown"] += amount
                    nutrition_analysis["eco_score_spending"]["unknown"] += amount
            else:
                # No EAN code available
                nutrition_analysis["nutri_score_spending"]["unknown"] += amount
                nutrition_analysis["nova_group_spending"]["unknown"] += amount
                nutrition_analysis["eco_score_spending"]["unknown"] += amount

        # Generate recommendations based on the analysis
        recommendations = []

        if nutrition_analysis["total_amount"] > 0:
            # Nutri-Score recommendations
            unhealthy_spending = (
                nutrition_analysis["nutri_score_spending"]["D"]
                + nutrition_analysis["nutri_score_spending"]["E"]
            )
            if unhealthy_spending > nutrition_analysis["total_amount"] * 0.3:
                recommendations.append(
                    {
                        "type": "nutri_score",
                        "message": f"You spend {unhealthy_spending:.2f} CHF ({unhealthy_spending / nutrition_analysis['total_amount'] * 100:.1f}%) on products with poor Nutri-Scores (D/E). Consider choosing more A/B rated products.",
                    }
                )

            # Nova Group recommendations
            ultra_processed_spending = nutrition_analysis["nova_group_spending"]["4"]
            if ultra_processed_spending > nutrition_analysis["total_amount"] * 0.4:
                recommendations.append(
                    {
                        "type": "nova_group",
                        "message": f"You spend {ultra_processed_spending:.2f} CHF ({ultra_processed_spending / nutrition_analysis['total_amount'] * 100:.1f}%) on ultra-processed foods (Nova Group 4). Try to include more minimally processed alternatives.",
                    }
                )

        return {
            "analysis": nutrition_analysis,
            "customer_name": customer_name,
            "period": f"{start_date} to {end_date}",
            "recommendations": recommendations,
            "summary": {
                "total_spent": f"{nutrition_analysis['total_amount']:.2f} CHF",
                "products_analyzed": nutrition_analysis["analyzed_products"],
                "products_with_ean": nutrition_analysis["products_with_ean"],
                "nutrition_data_coverage": f"{nutrition_analysis['products_with_nutrition_data']}/{nutrition_analysis['products_with_ean']} products with EAN codes",
            },
        }

    except Exception as e:
        logging.error(f"Error analyzing nutrition spending: {e}")
        return {
            "error": f"Failed to analyze nutrition spending: {str(e)}",
            "analysis": None,
        }


@mcp.tool()
async def get_healthy_alternatives(
    ctx: Context, barcode: str, criteria: str = "nutri_score"
) -> Dict[str, Any]:
    """
    Find healthier alternatives to a given product using Open Food Facts data.

    This tool suggests products that are:
    - In the same category as the original product
    - Have better nutritional scores
    - Are available in the same market (when possible)

    :param ctx: The tool context (unused in this implementation).
    :param barcode: Barcode of the product to find alternatives for
    :param criteria: Criteria for "healthier" - "nutri_score", "nova_group", "eco_score", or "all"
    :return: Dictionary containing healthier alternatives
    """
    if not barcode or not barcode.strip():
        return {"error": "Barcode is required", "alternatives": []}

    try:
        # First, get the original product
        original_product = await _fetch_openfoodfacts_product(barcode.strip())

        if not original_product:
            return {
                "error": f"Original product with barcode {barcode} not found",
                "alternatives": [],
            }

        # Extract main category for searching alternatives
        categories = original_product.categories or ""
        main_category = categories.split(",")[0].strip() if categories else ""

        if not main_category:
            return {
                "error": "Cannot find alternatives - original product has no category information",
                "original_product": original_product.dict(),
                "alternatives": [],
            }

        # Search for products in the same category
        alternative_products = await _search_openfoodfacts_products(
            main_category, page=1, page_size=20
        )

        # Filter and rank alternatives based on criteria
        better_alternatives = []

        for alt_product in alternative_products:
            if alt_product.barcode == original_product.barcode:
                continue  # Skip the original product

            is_better = False
            score_comparison = {}

            # Compare based on criteria
            if criteria in ["nutri_score", "all"]:
                orig_nutri = original_product.nutri_score or "Z"
                alt_nutri = alt_product.nutri_score or "Z"
                if alt_nutri < orig_nutri:  # A < B < C < D < E
                    is_better = True
                    score_comparison["nutri_score"] = f"{orig_nutri} → {alt_nutri}"

            if criteria in ["nova_group", "all"]:
                orig_nova = original_product.nova_group or 5
                alt_nova = alt_product.nova_group or 5
                if alt_nova < orig_nova:  # Lower Nova group is better
                    is_better = True
                    score_comparison["nova_group"] = f"{orig_nova} → {alt_nova}"

            if criteria in ["eco_score", "all"]:
                orig_eco = original_product.eco_score or "Z"
                alt_eco = alt_product.eco_score or "Z"
                if alt_eco < orig_eco:  # A < B < C < D < E
                    is_better = True
                    score_comparison["eco_score"] = f"{orig_eco} → {alt_eco}"

            if is_better:
                alt_dict = alt_product.dict()
                alt_dict["improvement_reason"] = score_comparison
                better_alternatives.append(alt_dict)

        # Sort alternatives by number of improvements
        better_alternatives.sort(
            key=lambda x: len(x["improvement_reason"]), reverse=True
        )

        # Limit to top 5 alternatives
        better_alternatives = better_alternatives[:5]

        return {
            "original_product": original_product.dict(),
            "alternatives": better_alternatives,
            "criteria_used": criteria,
            "total_alternatives_found": len(better_alternatives),
            "message": f"Found {len(better_alternatives)} healthier alternatives to {original_product.name}",
        }

    except Exception as e:
        logging.error(f"Error finding healthy alternatives: {e}")
        return {"error": f"Failed to find alternatives: {str(e)}", "alternatives": []}


# --- Resource Registration ---
# Resources are now registered using decorators above


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    get_config()  # Validate config on startup
    mcp.run()
