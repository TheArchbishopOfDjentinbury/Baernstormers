"""Transaction management and analytics API router using GraphDB SPARQL queries."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
import httpx
from datetime import datetime, date

from src.config import settings
from src.models import (
    TransactionBasic,
    TransactionDetailsAPI as TransactionDetails,
    ReceiptItemAPI as ReceiptItem,
    ReceiptDetailsAPI as ReceiptDetails,
    SpendingAnalyticsAPI as SpendingAnalytics,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

logger = logging.getLogger(__name__)


async def execute_sparql_query(query: str) -> Dict[str, Any]:
    """Execute SPARQL query against GraphDB."""
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        }
        data = {"query": query}
        auth = httpx.BasicAuth(settings.graphdb_user, settings.graphdb_password)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.graphdb_url,
                headers=headers,
                data=data,
                auth=auth,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(
            f"GraphDB HTTP error: {e.response.status_code} - {e.response.text}"
        )
        raise HTTPException(
            status_code=500, detail=f"GraphDB error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"GraphDB connection error: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to GraphDB")
    except Exception as e:
        logger.error(f"Unexpected error in SPARQL query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[TransactionBasic])
async def list_transactions(
    transaction_type: Optional[str] = Query(
        None, description="Filter by transaction type"
    ),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get list of transactions with optional filters."""
    filters = []

    if transaction_type:
        filters.append(f'FILTER(?transaction_type = "{transaction_type}")')

    if start_date and end_date:
        filters.append(
            f'FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)'
        )
    elif start_date:
        filters.append(f'FILTER(?date >= "{start_date}"^^xsd:date)')
    elif end_date:
        filters.append(f'FILTER(?date <= "{end_date}"^^xsd:date)')

    filter_clause = " ".join(filters)

    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?transaction ?amount ?date ?transaction_type WHERE {{
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        
        OPTIONAL {{ ?transaction exs:transactionType ?transaction_type }}
        
        {filter_clause}
    }}
    ORDER BY DESC(?date)
    LIMIT {limit}
    OFFSET {offset}
    """

    result = await execute_sparql_query(query)
    transactions = []

    for binding in result.get("results", {}).get("bindings", []):
        transaction = TransactionBasic(
            transaction_id=binding["transaction"]["value"].split("/")[-1],
            amount=float(binding["amount"]["value"]),
            date=binding["date"]["value"],
            status="settled",
            transaction_type=binding.get("transaction_type", {}).get("value"),
        )
        transactions.append(transaction)

    return transactions


@router.get("/{transaction_id}", response_model=TransactionDetails)
async def get_transaction_details(transaction_id: str):
    """Get detailed information about a specific transaction."""
    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?transaction ?amount ?currency ?date ?value_date ?transaction_type 
           ?payer_name ?payee_name ?merchant_name ?receipt WHERE {{
        VALUES ?transaction {{ ex:{transaction_id} <https://static.rwpz.net/spendcast/tx/{transaction_id}> }}
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?amount_uri exs:hasCurrency ?currency .
        ?transaction exs:hasTransactionDate ?date .
        
        OPTIONAL {{ ?transaction exs:valueDate ?value_date }}
        OPTIONAL {{ ?transaction exs:transactionType ?transaction_type }}
        OPTIONAL {{ ?transaction exs:hasReceipt ?receipt }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payerRole .
            ?payerRole a exs:Payer .
            ?payerRole exs:isPlayedBy ?payer .
            ?payer exs:hasName ?payer_name .
        }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payeeRole .
            ?payeeRole a exs:Payee .
            ?payeeRole exs:isPlayedBy ?payee .
            ?payee exs:hasName ?payee_name .
        }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payeeRole .
            ?payeeRole a exs:Payee .
            ?payeeRole exs:isPlayedBy ?merchant .
            ?merchant rdfs:label ?merchant_name .
        }}
    }}
    """

    result = await execute_sparql_query(query)
    bindings = result.get("results", {}).get("bindings", [])

    if not bindings:
        raise HTTPException(status_code=404, detail="Transaction not found")

    data = bindings[0]

    transaction_details = TransactionDetails(
        transaction_id=data["transaction"]["value"].split("/")[-1],
        amount=float(data["amount"]["value"]),
        currency=data["currency"]["value"].split("/")[-1],
        date=data["date"]["value"],
        value_date=data.get("value_date", {}).get("value"),
        status="settled",
        transaction_type=data.get("transaction_type", {}).get("value"),
        payer_name=data.get("payer_name", {}).get("value"),
        payee_name=data.get("payee_name", {}).get("value"),
        merchant=data.get("merchant_name", {}).get("value"),
        receipt_id=data.get("receipt", {}).get("value", "").split("/")[-1]
        if data.get("receipt")
        else None,
        has_receipt=bool(data.get("receipt")),
    )

    return transaction_details


@router.get("/{transaction_id}/receipt", response_model=ReceiptDetails)
async def get_transaction_receipt(transaction_id: str):
    """Get receipt details for a transaction."""
    # First check if transaction has a receipt
    receipt_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?receipt WHERE {{
        VALUES ?transaction {{ ex:{transaction_id} <https://static.rwpz.net/spendcast/tx/{transaction_id}> }}
        ?transaction exs:hasReceipt ?receipt .
    }}
    """

    receipt_result = await execute_sparql_query(receipt_query)
    receipt_bindings = receipt_result.get("results", {}).get("bindings", [])

    if not receipt_bindings:
        raise HTTPException(
            status_code=404, detail="No receipt found for this transaction"
        )

    receipt_uri = receipt_bindings[0]["receipt"]["value"]
    receipt_id = receipt_uri.split("/")[-1]

    # Get receipt details
    receipt_details_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?receipt ?total_amount ?receipt_date ?receipt_time ?payment_method 
           ?merchant ?vat_number WHERE {{
        VALUES ?receipt {{ <{receipt_uri}> }}
        
        OPTIONAL {{ ?receipt exs:hasTotalAmount ?total_amount_uri . ?total_amount_uri exs:hasAmount ?total_amount }}
        OPTIONAL {{ ?receipt exs:receiptDate ?receipt_date }}
        OPTIONAL {{ ?receipt exs:receiptTime ?receipt_time }}
        OPTIONAL {{ ?receipt exs:paymentMethod ?payment_method }}
        OPTIONAL {{ ?receipt exs:vatNumber ?vat_number }}
        
        OPTIONAL {{
            ?receipt exs:hasParticipant ?merchantRole .
            ?merchantRole exs:isPlayedBy ?merchant .
            ?merchant rdfs:label ?merchant .
        }}
    }}
    """

    details_result = await execute_sparql_query(receipt_details_query)
    details_bindings = details_result.get("results", {}).get("bindings", [])

    if not details_bindings:
        raise HTTPException(status_code=404, detail="Receipt details not found")

    receipt_data = details_bindings[0]

    # Get receipt line items
    items_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?item_description ?quantity ?unit_price ?line_subtotal 
           ?product_name ?category_label WHERE {{
        VALUES ?receipt {{ <{receipt_uri}> }}
        
        ?receipt exs:hasLineItem ?line_item .
        
        OPTIONAL {{ ?line_item exs:itemDescription ?item_description }}
        OPTIONAL {{ ?line_item exs:quantity ?quantity }}
        OPTIONAL {{ ?line_item exs:unitPrice ?unit_price }}
        OPTIONAL {{ ?line_item exs:lineSubtotal ?line_subtotal }}
        
        OPTIONAL {{
            ?line_item exs:hasProduct ?product .
            ?product exs:name ?product_name .
            OPTIONAL {{
                ?product exs:category ?category .
                ?category rdfs:label ?category_label .
            }}
        }}
    }}
    ORDER BY ?item_description
    """

    items_result = await execute_sparql_query(items_query)
    receipt_items = []

    for binding in items_result.get("results", {}).get("bindings", []):
        item = ReceiptItem(
            item_description=binding.get("item_description", {}).get(
                "value", "Unknown item"
            ),
            quantity=int(binding.get("quantity", {}).get("value", 1)),
            unit_price=float(binding.get("unit_price", {}).get("value", 0.0)),
            line_subtotal=float(binding.get("line_subtotal", {}).get("value", 0.0)),
            product_name=binding.get("product_name", {}).get("value"),
            category=binding.get("category_label", {}).get("value"),
        )
        receipt_items.append(item)

    receipt_details = ReceiptDetails(
        receipt_id=receipt_id,
        total_amount=float(receipt_data.get("total_amount", {}).get("value", 0.0)),
        receipt_date=receipt_data.get("receipt_date", {}).get("value", ""),
        receipt_time=receipt_data.get("receipt_time", {}).get("value"),
        payment_method=receipt_data.get("payment_method", {}).get("value"),
        merchant=receipt_data.get("merchant", {}).get("value"),
        vat_number=receipt_data.get("vat_number", {}).get("value"),
        items=receipt_items,
    )

    return receipt_details


@router.get("/analytics/overview")
async def get_spending_overview(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
):
    """Get overall spending analytics."""
    # Build filters
    filters = []
    customer_filter = ""

    if start_date and end_date:
        filters.append(
            f'FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)'
        )
    elif start_date:
        filters.append(f'FILTER(?date >= "{start_date}"^^xsd:date)')
    elif end_date:
        filters.append(f'FILTER(?date <= "{end_date}"^^xsd:date)')

    if customer_name:
        customer_filter = f"""
        ?account exs:hasAccountHolder ?holderRole .
        ?holderRole exs:isPlayedBy ?customer .
        ?customer exs:hasName "{customer_name}" .
        """

    filter_clause = " ".join(filters)

    # Get spending by transaction type
    overview_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?transaction_type (SUM(?amount) AS ?total) (COUNT(?transaction) AS ?count) WHERE {{
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        {customer_filter}
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        ?transaction exs:transactionType ?transaction_type .
        
        {filter_clause}
    }}
    GROUP BY ?transaction_type
    """

    overview_result = await execute_sparql_query(overview_query)

    total_spending = 0.0
    total_income = 0.0
    transaction_count = 0

    for binding in overview_result.get("results", {}).get("bindings", []):
        amount = float(binding["total"]["value"])
        count = int(binding["count"]["value"])
        trans_type = binding["transaction_type"]["value"]

        transaction_count += count

        if trans_type == "expense":
            total_spending += amount
        elif trans_type == "income":
            total_income += amount

    # Get top categories
    categories_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?category_label (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {{
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        {customer_filter}
        
        ?transaction exs:hasReceipt ?receipt .
        ?receipt exs:hasLineItem ?line_item .
        ?line_item exs:hasProduct ?product .
        ?product exs:category ?category .
        ?category rdfs:label ?category_label .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        
        {filter_clause}
    }}
    GROUP BY ?category_label
    ORDER BY DESC(?total_spent)
    LIMIT 10
    """

    categories_result = await execute_sparql_query(categories_query)
    top_categories = []

    for binding in categories_result.get("results", {}).get("bindings", []):
        category = {
            "category": binding["category_label"]["value"],
            "total_spent": float(binding["total_spent"]["value"]),
            "transaction_count": int(binding["transaction_count"]["value"]),
        }
        top_categories.append(category)

    # Get top merchants
    merchants_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?merchant_name (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {{
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        {customer_filter}
        
        ?transaction exs:hasParticipant ?payeeRole .
        ?payeeRole a exs:Payee .
        ?payeeRole exs:isPlayedBy ?merchant .
        ?merchant rdfs:label ?merchant_name .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        ?transaction exs:transactionType "expense" .
        
        {filter_clause}
    }}
    GROUP BY ?merchant_name
    ORDER BY DESC(?total_spent)
    LIMIT 10
    """

    merchants_result = await execute_sparql_query(merchants_query)
    top_merchants = []

    for binding in merchants_result.get("results", {}).get("bindings", []):
        merchant = {
            "merchant": binding["merchant_name"]["value"],
            "total_spent": float(binding["total_spent"]["value"]),
            "transaction_count": int(binding["transaction_count"]["value"]),
        }
        top_merchants.append(merchant)

    analytics = SpendingAnalytics(
        total_spending=total_spending,
        total_income=total_income,
        net_amount=total_income - total_spending,
        transaction_count=transaction_count,
        average_transaction=total_spending / max(transaction_count, 1),
        top_categories=top_categories,
        top_merchants=top_merchants,
    )

    return analytics


@router.get("/analytics/monthly-trends")
async def get_monthly_trends(
    year: int = Query(2025, ge=2020, le=2030),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
):
    """Get monthly spending trends."""
    customer_filter = ""
    if customer_name:
        customer_filter = f"""
        ?account exs:hasAccountHolder ?holderRole .
        ?holderRole exs:isPlayedBy ?customer .
        ?customer exs:hasName "{customer_name}" .
        """

    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?month ?transaction_type (SUM(?amount) AS ?total) (COUNT(?transaction) AS ?count) WHERE {{
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        {customer_filter}
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        ?transaction exs:transactionType ?transaction_type .
        
        FILTER(?date >= "{year}-01-01"^^xsd:date && ?date <= "{year}-12-31"^^xsd:date)
        BIND(CONCAT(STR(YEAR(?date)), "-", IF(MONTH(?date) < 10, "0", ""), STR(MONTH(?date))) AS ?month)
    }}
    GROUP BY ?month ?transaction_type
    ORDER BY ?month ?transaction_type
    """

    result = await execute_sparql_query(query)

    # Organize data by month
    monthly_data = {}

    for binding in result.get("results", {}).get("bindings", []):
        # Safely get required values, skip if not present
        if "month" not in binding or "transaction_type" not in binding:
            continue

        month = binding["month"]["value"]
        trans_type = binding["transaction_type"]["value"]
        amount = float(binding["total"]["value"])
        count = int(binding["count"]["value"])

        if month not in monthly_data:
            monthly_data[month] = {
                "month": month,
                "spending": 0.0,
                "income": 0.0,
                "transaction_count": 0,
                "net": 0.0,
            }

        monthly_data[month]["transaction_count"] += count

        if trans_type == "expense":
            monthly_data[month]["spending"] += amount
        elif trans_type == "income":
            monthly_data[month]["income"] += amount

        monthly_data[month]["net"] = (
            monthly_data[month]["income"] - monthly_data[month]["spending"]
        )

    # Convert to list and sort
    trends = list(monthly_data.values())
    trends.sort(key=lambda x: x["month"])

    return {
        "year": year,
        "customer_name": customer_name,
        "monthly_trends": trends,
        "total_months": len(trends),
    }
