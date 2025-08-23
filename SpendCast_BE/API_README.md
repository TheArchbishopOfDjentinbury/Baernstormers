# SpendCast Backend API

Comprehensive Financial Data Management System with GraphDB SPARQL integration.

## Overview

SpendCast API provides CRUD operations for managing financial data including customers, accounts, and transactions. The system integrates with GraphDB using SPARQL queries to retrieve and analyze financial data.

## Database Statistics

- **Customers**: 1
- **Accounts**: 5,591
- **Transactions**: 360

## API Endpoints

### Base URLs

- **Development**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health & Status

- `GET /` - Root endpoint with API overview
- `GET /health` - Health check endpoint
- `GET /api/v1/database/check` - Database connection status

### Customer Management (`/api/v1/customers`)

#### Customer Endpoints

- `GET /api/v1/customers/` - List all customers
  - Query params: `limit` (default: 10, max: 100)
- `GET /api/v1/customers/{customer_name}` - Get customer details with accounts
- `GET /api/v1/customers/{customer_name}/transactions` - Get customer transactions
  - Query params: `limit`, `offset`
- `GET /api/v1/customers/{customer_name}/spending-analysis` - Spending by category
  - Query params: `year` (default: 2025)
- `GET /api/v1/customers/{customer_name}/monthly-spending` - Monthly spending breakdown
  - Query params: `year` (default: 2025)

#### Example Response

```json
{
  "customer": {
    "id": "Customer_76178901",
    "name": "Jeanine Marie Blumenthal",
    "email": "jeanine.blumenthal@example.com",
    "phone": "+41 44 123 45 67"
  },
  "accounts": [
    {
      "account_id": "Account1",
      "account_type": "CheckingAccount",
      "balance": 20000.0,
      "currency": "Swiss_franc",
      "iban": "CH9300762011623852957"
    }
  ],
  "total_balance": 55121.3,
  "account_count": 2
}
```

### Account Management (`/api/v1/accounts`)

#### Account Endpoints

- `GET /api/v1/accounts/` - List all accounts
  - Query params: `account_type`, `limit`
- `GET /api/v1/accounts/{account_id}` - Get account details with recent transactions
- `GET /api/v1/accounts/{account_id}/transactions` - Get account transactions
  - Query params: `transaction_type`, `start_date`, `end_date`, `limit`, `offset`
- `GET /api/v1/accounts/{account_id}/balance-history` - Get balance history
  - Query params: `period` (day/week/month)
- `GET /api/v1/accounts/types` - Get available account types

#### Example Response

```json
{
  "account": {
    "account_id": "Account1",
    "account_type": "CheckingAccount",
    "balance": 20000.0,
    "currency": "Swiss_franc",
    "iban": "CH9300762011623852957",
    "holder_name": "Jeanine Marie Blumenthal"
  },
  "recent_transactions": [
    {
      "transaction_id": "Mittagessen_Sommer_2025_2025_07_02",
      "amount": 13.0,
      "date": "2025-07-02",
      "status": "settled",
      "merchant": "Restaurant"
    }
  ],
  "transaction_count": 10,
  "monthly_spending": 329.15,
  "monthly_income": 0.0
}
```

### Transaction Management (`/api/v1/transactions`)

#### Transaction Endpoints

- `GET /api/v1/transactions/` - List all transactions
  - Query params: `status`, `transaction_type`, `start_date`, `end_date`, `limit`, `offset`
- `GET /api/v1/transactions/{transaction_id}` - Get transaction details
- `GET /api/v1/transactions/{transaction_id}/receipt` - Get transaction receipt
- `GET /api/v1/transactions/analytics/overview` - Spending analytics overview
  - Query params: `start_date`, `end_date`, `customer_name`
- `GET /api/v1/transactions/analytics/monthly-trends` - Monthly spending trends
  - Query params: `year`, `customer_name`

#### Example Response

```json
{
  "transaction_id": "Mittagessen_Sommer_2025_2025_07_02",
  "amount": 13.0,
  "currency": "Swiss_franc",
  "date": "2025-07-02",
  "status": "settled",
  "transaction_type": "expense",
  "payer_name": "Jeanine Marie Blumenthal",
  "merchant": "Restaurant",
  "has_receipt": false
}
```

### Analytics Endpoints

#### Spending Overview

```json
{
  "total_spending": 25000.0,
  "total_income": 50000.0,
  "net_amount": 25000.0,
  "transaction_count": 150,
  "average_transaction": 166.67,
  "top_categories": [
    {
      "category": "Salate",
      "total_spent": 4495.7,
      "transaction_count": 37
    }
  ],
  "top_merchants": [
    {
      "merchant": "Migros",
      "total_spent": 15000.0,
      "transaction_count": 120
    }
  ]
}
```

## GraphDB Integration

### SPARQL Endpoints

The API uses GraphDB with the following SPARQL endpoint:

- **URL**: `http://localhost:7200/repositories/spendcast`

### Key Entities and Relationships

#### Core Financial Entities

- **Person**: Individual customers with accounts and payment cards
- **Account**: Banking accounts (checking, savings, credit cards, retirement 3A)
- **FinancialTransaction**: Money transfers with amounts, dates, and status
- **PaymentCard**: Credit/debit cards linked to accounts

#### Retail & Receipt Data

- **Receipt**: Purchase documents with line items and totals
- **Product**: Goods and services with names, descriptions, and category links
- **ProductCategory**: Hierarchical product classification
- **Merchant**: Business entities with names and addresses

#### Key Properties

- `exs:hasName` - Entity names
- `exs:hasAccount` - Person to account relationship
- `exs:hasMonetaryAmount` - Transaction amounts
- `exs:hasTransactionDate` - Transaction dates
- `exs:hasParticipant` - Transaction participants (through roles)
- `exs:category` - Product categories

### Example SPARQL Queries

#### Get Customer Transactions

```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?merchant WHERE {
  ?person exs:hasName "Jeanine Marie Blumenthal" .
  ?person exs:hasAccount ?account .

  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer .
  ?payerRole exs:isPlayedBy ?account .

  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
}
ORDER BY DESC(?date)
```

#### Get Spending by Category

```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?category_label (SUM(?amount) AS ?total_spent) WHERE {
  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasReceipt ?receipt .
  ?receipt exs:hasLineItem ?line_item .
  ?line_item exs:hasProduct ?product .
  ?product exs:category ?category .
  ?category rdfs:label ?category_label .

  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
}
GROUP BY ?category_label
ORDER BY DESC(?total_spent)
```

## Data Models

### Enumerations

- **TransactionStatus**: settled, pending, rejected, cancelled
- **TransactionType**: expense, income, transfer
- **AccountType**: CheckingAccount, SavingsAccount, CreditCard, Retirement3A, Other
- **Currency**: Swiss_franc, Euro, United_States_dollar

### Key Models

- `CustomerDetails`: Complete customer information
- `AccountDetails`: Account information with balances
- `TransactionDetails`: Transaction details with participants
- `ReceiptDetails`: Receipt with line items
- `SpendingAnalytics`: Analytics and trends

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "message": "Customer not found",
  "errors": [
    {
      "field": "customer_name",
      "message": "Customer with name 'John Doe' does not exist",
      "code": "NOT_FOUND"
    }
  ],
  "timestamp": "2025-01-21T10:30:00Z"
}
```

## Development Setup

### Requirements

- Python 3.10+
- FastAPI
- httpx (for GraphDB communication)
- Pydantic (for data validation)
- Access to GraphDB instance

### Environment Variables

```bash
GRAPHDB_URL=http://localhost:7200/repositories/spendcast
GRAPHDB_USER=your-username
GRAPHDB_PASSWORD=your-password
```

### Running the API

```bash
cd SpendCast_BE
pip install -r requirements.txt
python main.py
```

### Testing Endpoints

Once running, visit:

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Database Status: http://localhost:8000/api/v1/database/check

## MCP Integration

The system integrates with Model Context Protocol (MCP) server for advanced SPARQL query capabilities. See the spendcast-mcp project for details on MCP server functionality.

## Production Deployment

For production deployment:

1. Set proper environment variables
2. Configure authentication and authorization
3. Set up monitoring and logging
4. Use production WSGI server (Gunicorn/Uvicorn)
5. Configure reverse proxy (Nginx)

## Security Considerations

- GraphDB credentials should be secured
- Implement proper authentication for API endpoints
- Use HTTPS in production
- Validate all input data
- Implement rate limiting
- Log all database access

## Support

For issues and questions:

- Check the API documentation at `/docs`
- Review the troubleshooting section
- Test connectivity with `/health` endpoint
