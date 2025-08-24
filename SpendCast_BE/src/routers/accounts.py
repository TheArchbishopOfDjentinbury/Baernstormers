"""Account management API router using GraphDB SPARQL queries."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
import httpx

from src.config import settings
from src.models import (
    AccountBasic,
    AccountDetailsAPI as AccountDetails,
    AccountTransaction,
    AccountSummaryAPI as AccountSummary,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

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


@router.get("/types", response_model=List[str])
async def get_account_types():
    """Get list of available account types."""
    query = """
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    
    SELECT DISTINCT ?account_type WHERE {
        ?account a ?account_type .
        VALUES ?account_type { 
            exs:CheckingAccount 
            exs:SavingsAccount 
            exs:CreditCard 
            exs:Retirement3A 
            exs:Other 
        }
    }
    ORDER BY ?account_type
    """

    result = await execute_sparql_query(query)
    account_types = []

    for binding in result.get("results", {}).get("bindings", []):
        # Extract account type from schema URI
        account_type_uri = binding["account_type"]["value"]
        account_type = account_type_uri.split("#")[-1]
        account_types.append(account_type)

    return account_types


@router.get("/", response_model=List[AccountBasic])
async def list_accounts(
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get list of all accounts."""
    type_filter = ""
    if account_type:
        type_filter = f"FILTER(?account_type = exs:{account_type})"

    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?account ?account_type ?balance ?currency ?account_number ?display_name WHERE {{
        ?account a ?account_type .
        OPTIONAL {{ ?account exs:hasInitialBalance ?balance }}
        ?account exs:hasCurrency ?currency .
        ?account exs:accountNumber ?account_number .
        OPTIONAL {{ ?account rdfs:label ?display_name }}
        FILTER(?account_type != exs:Account)
        {type_filter}
    }}
    ORDER BY ?account_type ?account
    LIMIT {limit}
    """

    result = await execute_sparql_query(query)
    accounts = []

    for binding in result.get("results", {}).get("bindings", []):
        # Use account number as the professional account_id
        account_number = binding["account_number"]["value"]

        # Extract account type from schema URI
        account_type_uri = binding["account_type"]["value"]
        account_type = account_type_uri.split("#")[-1]

        # Extract currency from URI
        currency_uri = binding["currency"]["value"]
        currency = currency_uri.split("/")[-1]

        # Get display name (optional)
        display_name = binding.get("display_name", {}).get("value")

        # Get balance (optional - may not exist for credit cards)
        balance = 0.0
        if "balance" in binding and binding["balance"].get("value"):
            balance = float(binding["balance"]["value"])

        account = AccountBasic(
            account_id=account_number,  # Professional: use account number as ID
            account_number=account_number,
            account_type=account_type,
            balance=balance,
            currency=currency,
            display_name=display_name,
        )
        accounts.append(account)

    return accounts


@router.get("/{account_id}", response_model=AccountSummary)
async def get_account_details(account_id: str):
    """Get detailed information about a specific account.

    Args:
        account_id: Account number (e.g., '1234567890')
    """
    # Get account details using account number
    account_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?account ?account_type ?balance ?currency ?iban ?account_number 
           ?account_purpose ?overdraft_limit ?holder_name ?provider_name ?display_name WHERE {{
        ?account a ?account_type .
        ?account exs:accountNumber "{account_id}" .
        
        OPTIONAL {{ ?account exs:hasInitialBalance ?balance }}
        ?account exs:hasCurrency ?currency .
        ?account exs:accountNumber ?account_number .
        
        OPTIONAL {{ ?account rdfs:label ?display_name }}
        OPTIONAL {{ ?account exs:hasInternationalBankAccountIdentifier ?iban }}
        OPTIONAL {{ ?account exs:hasAccountPurpose ?account_purpose }}
        OPTIONAL {{ ?account exs:hasOverdraftLimit ?overdraft_limit }}
        
        OPTIONAL {{
            ?account exs:hasAccountHolder ?holderRole .
            ?holderRole exs:isPlayedBy ?holder .
            ?holder exs:hasName ?holder_name .
        }}
        
        OPTIONAL {{
            ?account exs:hasAccountProvider ?providerRole .
            ?providerRole exs:isPlayedBy ?provider .
            OPTIONAL {{ ?provider rdfs:label ?provider_name }}
            OPTIONAL {{ ?provider exs:hasName ?provider_name }}
        }}
        
        FILTER(?account_type != exs:Account)
    }}
    """

    account_result = await execute_sparql_query(account_query)
    account_bindings = account_result.get("results", {}).get("bindings", [])

    if not account_bindings:
        raise HTTPException(status_code=404, detail="Account not found")

    account_data = account_bindings[0]

    # Get recent transactions for this account
    transactions_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?transaction ?amount ?date ?status ?transaction_type ?merchant_name WHERE {{
        ?account exs:accountNumber "{account_id}" .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        
        OPTIONAL {{ ?transaction exs:status ?status }}
        OPTIONAL {{ ?transaction exs:transactionType ?transaction_type }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payeeRole .
            ?payeeRole a exs:Payee .
            ?payeeRole exs:isPlayedBy ?merchant .
            ?merchant rdfs:label ?merchant_name .
        }}
    }}
    ORDER BY DESC(?date)
    LIMIT 10
    """

    transactions_result = await execute_sparql_query(transactions_query)
    transactions = []

    for binding in transactions_result.get("results", {}).get("bindings", []):
        # Extract transaction ID from URI
        transaction_uri = binding["transaction"]["value"]
        transaction_id = transaction_uri.split("/")[-1]

        transaction = AccountTransaction(
            transaction_id=transaction_id,
            amount=float(binding["amount"]["value"]),
            date=binding["date"]["value"],
            status=binding.get("status", {}).get("value", "unknown"),
            transaction_type=binding.get("transaction_type", {}).get("value"),
            merchant=binding.get("merchant_name", {}).get("value"),
        )
        transactions.append(transaction)

    # Calculate monthly spending and income
    monthly_stats_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    SELECT ?transaction_type (SUM(?amount) AS ?total) WHERE {{
        ?account exs:accountNumber "{account_id}" .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        ?transaction exs:transactionType ?transaction_type .
        
        FILTER(?date >= "2025-06-01"^^xsd:date && ?date <= "2025-07-31"^^xsd:date)
    }}
    GROUP BY ?transaction_type
    """

    monthly_result = await execute_sparql_query(monthly_stats_query)
    monthly_spending = 0.0
    monthly_income = 0.0

    for binding in monthly_result.get("results", {}).get("bindings", []):
        amount = float(binding["total"]["value"])
        trans_type = binding["transaction_type"]["value"]

        if trans_type == "expense":
            monthly_spending += amount
        elif trans_type == "income":
            monthly_income += amount

    # Build account details with professional account identification
    account_number = account_data["account_number"]["value"]

    account_type_uri = account_data["account_type"]["value"]
    account_type = account_type_uri.split("#")[-1]

    currency_uri = account_data["currency"]["value"]
    currency = currency_uri.split("/")[-1]

    # Extract internal ID for reference
    account_uri = account_data["account"]["value"]
    internal_id = account_uri.split("/")[-1]

    # Get balance (optional - may not exist for credit cards)
    balance = 0.0
    if account_data.get("balance") and account_data["balance"].get("value"):
        balance = float(account_data["balance"]["value"])

    account_details = AccountDetails(
        account_id=account_number,  # Professional: use account number as ID
        account_number=account_number,
        account_type=account_type,
        balance=balance,
        currency=currency,
        display_name=account_data.get("display_name", {}).get("value"),
        iban=account_data.get("iban", {}).get("value"),
        account_purpose=account_data.get("account_purpose", {}).get("value"),
        overdraft_limit=float(account_data["overdraft_limit"]["value"])
        if account_data.get("overdraft_limit")
        else None,
        holder_name=account_data.get("holder_name", {}).get("value"),
        provider_name=account_data.get("provider_name", {}).get("value"),
        internal_id=internal_id,
    )

    return AccountSummary(
        account=account_details,
        recent_transactions=transactions,
        transaction_count=len(transactions),
        monthly_spending=monthly_spending,
        monthly_income=monthly_income,
    )


@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    transaction_type: Optional[str] = Query(
        None, description="Filter by transaction type"
    ),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get transactions for a specific account with filters.

    Args:
        account_id: Account number (e.g., '1234567890')
    """
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
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    SELECT ?transaction ?amount ?date ?status ?transaction_type ?merchant_name WHERE {{
        ?account exs:accountNumber "{account_id}" .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        
        OPTIONAL {{ ?transaction exs:status ?status }}
        OPTIONAL {{ ?transaction exs:transactionType ?transaction_type }}
        
        OPTIONAL {{
            ?transaction exs:hasParticipant ?payeeRole .
            ?payeeRole a exs:Payee .
            ?payeeRole exs:isPlayedBy ?merchant .
            ?merchant rdfs:label ?merchant_name .
        }}
        
        {filter_clause}
    }}
    ORDER BY DESC(?date)
    LIMIT {limit}
    OFFSET {offset}
    """

    result = await execute_sparql_query(query)
    transactions = []

    for binding in result.get("results", {}).get("bindings", []):
        # Extract transaction ID from URI
        transaction_uri = binding["transaction"]["value"]
        transaction_id = transaction_uri.split("/")[-1]

        transaction = {
            "transaction_id": transaction_id,
            "amount": float(binding["amount"]["value"]),
            "date": binding["date"]["value"],
            "status": binding.get("status", {}).get("value", "unknown"),
            "transaction_type": binding.get("transaction_type", {}).get("value"),
            "merchant": binding.get("merchant_name", {}).get("value"),
        }
        transactions.append(transaction)

    return {
        "account_id": account_id,
        "transactions": transactions,
        "count": len(transactions),
        "offset": offset,
        "limit": limit,
        "filters": {
            "transaction_type": transaction_type,
            "start_date": start_date,
            "end_date": end_date,
        },
    }


@router.get("/{account_id}/balance-history")
async def get_account_balance_history(
    account_id: str,
    period: str = Query("month", description="Period: day, week, month"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get balance history for an account (simulated based on transactions).

    Args:
        account_id: Account number (e.g., '1234567890')
        period: Aggregation period (day, week, month)
        start_date: Start date for history (default: based on period)
        end_date: End date for history (default: today)
    """

    # Calculate date range based on period if not provided
    from datetime import datetime, timedelta

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if not start_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if period == "day":
            start_dt = end_dt - timedelta(days=30)  # Last 30 days
        elif period == "week":
            start_dt = end_dt - timedelta(weeks=12)  # Last 12 weeks
        else:  # month
            start_dt = end_dt - timedelta(days=365)  # Last year
        start_date = start_dt.strftime("%Y-%m-%d")

    query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    SELECT ?date ?amount ?transaction_type WHERE {{
        ?account exs:accountNumber "{account_id}" .
        
        ?transaction a exs:FinancialTransaction .
        ?transaction exs:hasParticipant ?payerRole .
        ?payerRole a exs:Payer .
        ?payerRole exs:isPlayedBy ?account .
        
        ?transaction exs:hasMonetaryAmount ?amount_uri .
        ?amount_uri exs:hasAmount ?amount .
        ?transaction exs:hasTransactionDate ?date .
        ?transaction exs:transactionType ?transaction_type .
        
        FILTER(?date >= "{start_date}"^^xsd:date && ?date <= "{end_date}"^^xsd:date)
    }}
    ORDER BY ?date
    """

    result = await execute_sparql_query(query)

    # Get initial balance
    balance_query = f"""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?balance WHERE {{
        ?account exs:accountNumber "{account_id}" .
        OPTIONAL {{ ?account exs:hasInitialBalance ?balance }}
    }}
    """

    balance_result = await execute_sparql_query(balance_query)
    initial_balance = 0.0

    if balance_result.get("results", {}).get("bindings"):
        bindings = balance_result["results"]["bindings"]
        if (
            bindings
            and bindings[0].get("balance")
            and bindings[0]["balance"].get("value")
        ):
            initial_balance = float(bindings[0]["balance"]["value"])

    # Calculate running balance with period aggregation
    from collections import defaultdict
    from datetime import datetime, timedelta

    # Group transactions by period
    period_groups = defaultdict(list)
    current_balance = initial_balance

    for binding in result.get("results", {}).get("bindings", []):
        amount = float(binding["amount"]["value"])
        trans_type = binding["transaction_type"]["value"]
        date_str = binding["date"]["value"]
        date_obj = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")

        # Adjust balance based on transaction type
        if trans_type == "expense":
            current_balance -= amount
        elif trans_type == "income":
            current_balance += amount

        # Group by period
        if period == "day":
            period_key = date_obj.strftime("%Y-%m-%d")
        elif period == "week":
            # Get Monday of the week
            monday = date_obj - timedelta(days=date_obj.weekday())
            period_key = monday.strftime("%Y-%m-%d")
        else:  # month
            period_key = date_obj.strftime("%Y-%m")

        period_groups[period_key].append(
            {
                "date": date_str,
                "amount": amount,
                "transaction_type": trans_type,
                "running_balance": round(current_balance, 2),
            }
        )

    # Create aggregated balance history
    balance_history = []
    for period_key in sorted(period_groups.keys()):
        transactions = period_groups[period_key]

        # Use the last balance of the period
        period_balance = (
            transactions[-1]["running_balance"] if transactions else initial_balance
        )

        # Calculate period totals
        period_income = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "income"
        )
        period_expenses = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "expense"
        )

        balance_history.append(
            {
                "period": period_key,
                "balance": period_balance,
                "income": round(period_income, 2),
                "expenses": round(period_expenses, 2),
                "net_change": round(period_income - period_expenses, 2),
                "transaction_count": len(transactions),
            }
        )

    return {
        "account_id": account_id,
        "initial_balance": initial_balance,
        "current_balance": round(current_balance, 2),
        "balance_history": balance_history,
        "period": period,
        "date_range": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "total_periods": len(balance_history),
            "total_transactions": sum(
                len(transactions) for transactions in period_groups.values()
            ),
        },
    }
