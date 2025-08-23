"""Customer management API router using GraphDB SPARQL queries."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import httpx

from src.config import settings

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])

logger = logging.getLogger(__name__)


class CustomerBasic(BaseModel):
    """Basic customer information model."""

    name: str = Field(..., description="Full name of the customer")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")


class CustomerDetails(BaseModel):
    """Detailed customer information model."""

    id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    birth_date: Optional[str] = Field(None, description="Birth date")
    citizenship: Optional[str] = Field(None, description="Citizenship")


class CustomerAccount(BaseModel):
    """Customer account summary model."""

    account_id: str = Field(..., description="Account ID")
    account_type: str = Field(..., description="Type of account")
    balance: float = Field(..., description="Account balance")
    currency: str = Field(..., description="Account currency")
    iban: Optional[str] = Field(None, description="IBAN number")


class CustomerSummary(BaseModel):
    """Complete customer summary model."""

    customer: CustomerDetails
    accounts: List[CustomerAccount]
    total_balance: float
    account_count: int


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


@router.get("/", response_model=List[CustomerBasic])
async def list_customers(limit: int = Query(10, ge=1, le=100)):
    """Get list of all customers."""
    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?name ?email ?phone WHERE {{
        ?person a exs:Person .
        ?person exs:hasName ?name .
        OPTIONAL {{ ?person exs:hasEmailAddress ?email }}
        OPTIONAL {{ ?person exs:hasTelephoneNumber ?phone }}
    }}
    ORDER BY ?name
    LIMIT {limit}
    """

    result = await execute_sparql_query(query)
    customers = []

    for binding in result.get("results", {}).get("bindings", []):
        customer = CustomerBasic(
            name=binding["name"]["value"],
            email=binding.get("email", {}).get("value"),
            phone=binding.get("phone", {}).get("value"),
        )
        customers.append(customer)

    return customers


@router.get("/{customer_name}", response_model=CustomerSummary)
async def get_customer_details(customer_name: str):
    """Get detailed information about a specific customer."""
    # First get customer basic info
    customer_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?person ?name ?email ?phone ?birth_date ?citizenship WHERE {{
        ?person a exs:Person .
        ?person exs:hasName "{customer_name}" .
        ?person exs:hasName ?name .
        OPTIONAL {{ ?person exs:hasEmailAddress ?email }}
        OPTIONAL {{ ?person exs:hasTelephoneNumber ?phone }}
        OPTIONAL {{ ?person exs:birthDate ?birth_date }}
        OPTIONAL {{ ?person exs:citizenship ?citizenship }}
    }}
    """

    customer_result = await execute_sparql_query(customer_query)
    customer_bindings = customer_result.get("results", {}).get("bindings", [])

    if not customer_bindings:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer_data = customer_bindings[0]

    # Get customer accounts
    accounts_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?account ?account_type ?balance ?currency ?iban WHERE {{
        ?person exs:hasName "{customer_name}" .
        ?person exs:hasAccount ?account .
        ?account a ?account_type .
        OPTIONAL {{ ?account exs:hasInitialBalance ?balance }}
        OPTIONAL {{ ?account exs:hasCurrency ?currency }}
        OPTIONAL {{ ?account exs:hasInternationalBankAccountIdentifier ?iban }}
        FILTER(?account_type != exs:Account)
    }}
    ORDER BY ?account_type
    """

    accounts_result = await execute_sparql_query(accounts_query)
    accounts = []
    total_balance = 0.0

    for binding in accounts_result.get("results", {}).get("bindings", []):
        balance = float(binding.get("balance", {}).get("value", 0))
        total_balance += balance

        account = CustomerAccount(
            account_id=binding["account"]["value"].split("/")[-1],
            account_type=binding["account_type"]["value"].split("#")[-1],
            balance=balance,
            currency=binding.get("currency", {}).get("value", "CHF").split("/")[-1],
            iban=binding.get("iban", {}).get("value"),
        )
        accounts.append(account)

    # Build customer details
    customer = CustomerDetails(
        id=customer_data["person"]["value"].split("/")[-1],
        name=customer_data["name"]["value"],
        email=customer_data.get("email", {}).get("value"),
        phone=customer_data.get("phone", {}).get("value"),
        birth_date=customer_data.get("birth_date", {}).get("value"),
        citizenship=customer_data.get("citizenship", {}).get("value"),
    )

    return CustomerSummary(
        customer=customer,
        accounts=accounts,
        total_balance=total_balance,
        account_count=len(accounts),
    )


@router.get("/{customer_name}/transactions")
async def get_customer_transactions(
    customer_name: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get recent transactions for a customer."""
    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?transaction ?amount ?date ?status ?merchant_name WHERE {{
        ?person exs:hasName "{customer_name}" .
        ?person exs:hasAccount ?account .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        OPTIONAL {{ ?transaction exs:status ?status }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payeeRole .
            ?payeeRole a exs:Payee .
            ?payeeRole exs:isPlayedBy ?merchant .
            ?merchant rdfs:label ?merchant_name .
        }}
    }}
    ORDER BY DESC(?date)
    LIMIT {limit}
    OFFSET {offset}
    """

    result = await execute_sparql_query(query)
    transactions = []

    for binding in result.get("results", {}).get("bindings", []):
        transaction = {
            "transaction_id": binding["transaction"]["value"].split("/")[-1],
            "amount": float(binding["amount"]["value"]),
            "date": binding["date"]["value"],
            "status": binding.get("status", {}).get("value", "unknown"),
            "merchant": binding.get("merchant_name", {}).get("value", "unknown"),
        }
        transactions.append(transaction)

    return {
        "customer_name": customer_name,
        "transactions": transactions,
        "count": len(transactions),
        "offset": offset,
        "limit": limit,
    }


@router.get("/{customer_name}/spending-analysis")
async def get_customer_spending_analysis(
    customer_name: str, year: int = Query(2025, ge=2020, le=2030)
):
    """Get spending analysis by category for a customer."""
    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?category_label (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {{
        ?person exs:hasName "{customer_name}" .
        ?person exs:hasAccount ?account .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasReceipt ?receipt .
        ?receipt exs:hasLineItem ?line_item .
        ?line_item exs:hasProduct ?product .
        ?product exs:category ?category .
        ?category rdfs:label ?category_label .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        
        ?transaction exs:hasTransactionDate ?date .
        FILTER(?date >= "{year}-01-01"^^xsd:date && ?date <= "{year}-12-31"^^xsd:date)
    }}
    GROUP BY ?category_label
    ORDER BY DESC(?total_spent)
    LIMIT 20
    """

    result = await execute_sparql_query(query)
    categories = []
    total_amount = 0.0

    for binding in result.get("results", {}).get("bindings", []):
        amount = float(binding["total_spent"]["value"])
        total_amount += amount

        category = {
            "category": binding["category_label"]["value"],
            "total_spent": amount,
            "transaction_count": int(binding["transaction_count"]["value"]),
        }
        categories.append(category)

    return {
        "customer_name": customer_name,
        "year": year,
        "categories": categories,
        "total_spending": total_amount,
        "category_count": len(categories),
    }


@router.get("/{customer_name}/monthly-spending")
async def get_customer_monthly_spending(
    customer_name: str, year: int = Query(2025, ge=2020, le=2030)
):
    """Get monthly spending breakdown for a customer."""
    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?month (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {{
        ?person exs:hasName "{customer_name}" .
        ?person exs:hasAccount ?account .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        
        FILTER(?date >= "{year}-01-01"^^xsd:date && ?date <= "{year}-12-31"^^xsd:date)
        BIND(CONCAT(STR(YEAR(?date)), "-", IF(MONTH(?date) < 10, "0", ""), STR(MONTH(?date))) AS ?month)
    }}
    GROUP BY ?month
    ORDER BY ?month
    """

    result = await execute_sparql_query(query)
    monthly_data = []
    total_year_spending = 0.0

    for binding in result.get("results", {}).get("bindings", []):
        amount = float(binding["total_spent"]["value"])
        total_year_spending += amount

        # Safely get month value, skip if not present
        if "month" not in binding:
            continue

        month_data = {
            "month": binding["month"]["value"],
            "total_spent": amount,
            "transaction_count": int(binding["transaction_count"]["value"]),
        }
        monthly_data.append(month_data)

    return {
        "customer_name": customer_name,
        "year": year,
        "monthly_spending": monthly_data,
        "total_year_spending": total_year_spending,
        "average_monthly_spending": total_year_spending / max(len(monthly_data), 1),
    }
