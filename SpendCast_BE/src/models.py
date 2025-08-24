"""Pydantic models for SpendCast API data validation and serialization."""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""

    SETTLED = "settled"
    PENDING = "pending"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class AccountType(str, Enum):
    """Account type enumeration."""

    CHECKING = "CheckingAccount"
    SAVINGS = "SavingsAccount"
    CREDIT_CARD = "CreditCard"
    RETIREMENT_3A = "Retirement3A"
    OTHER = "Other"


class Currency(str, Enum):
    """Currency enumeration."""

    CHF = "Swiss_franc"
    EUR = "Euro"
    USD = "United_States_dollar"


# Base Models
class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class PaginationParams(BaseModel):
    """Pagination parameters model."""

    limit: int = Field(50, ge=1, le=500, description="Number of items to return")
    offset: int = Field(0, ge=0, description="Number of items to skip")


class DateRangeFilter(BaseModel):
    """Date range filter model."""

    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        if v and values.get("start_date") and v < values.get("start_date"):
            raise ValueError("end_date must be after start_date")
        return v


# Customer Models
class CustomerBase(BaseModel):
    """Base customer model."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Customer full name"
    )
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")

    @validator("email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class CustomerCreate(CustomerBase):
    """Customer creation model."""

    birth_date: Optional[date] = Field(None, description="Birth date")
    citizenship: Optional[str] = Field(None, description="Citizenship")


class CustomerUpdate(BaseModel):
    """Customer update model."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Customer full name"
    )
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    birth_date: Optional[date] = Field(None, description="Birth date")
    citizenship: Optional[str] = Field(None, description="Citizenship")


class CustomerDetails(CustomerBase):
    """Detailed customer information model."""

    id: str = Field(..., description="Customer ID")
    birth_date: Optional[date] = Field(None, description="Birth date")
    citizenship: Optional[str] = Field(None, description="Citizenship")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# Customer API Models (for GraphDB integration)
class CustomerBasic(BaseModel):
    """Basic customer information model for API responses."""

    name: str = Field(..., description="Full name of the customer")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")


class CustomerDetailsAPI(BaseModel):
    """Detailed customer information model for API responses."""

    id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    birth_date: Optional[str] = Field(None, description="Birth date")
    citizenship: Optional[str] = Field(None, description="Citizenship")


class CustomerAccount(BaseModel):
    """Customer account summary model for API responses."""

    account_id: str = Field(..., description="Account ID")
    account_type: str = Field(..., description="Type of account")
    balance: float = Field(..., description="Account balance")
    currency: str = Field(..., description="Account currency")
    iban: Optional[str] = Field(None, description="IBAN number")


class CustomerSummary(BaseModel):
    """Complete customer summary model for API responses."""

    customer: CustomerDetailsAPI
    accounts: List[CustomerAccount]
    total_balance: float
    account_count: int


# Account Models
class AccountBase(BaseModel):
    """Base account model."""

    account_type: AccountType = Field(..., description="Type of account")
    balance: float = Field(..., ge=0, description="Account balance")
    currency: Currency = Field(Currency.CHF, description="Account currency")


class AccountCreate(AccountBase):
    """Account creation model."""

    holder_id: str = Field(..., description="Account holder customer ID")
    iban: Optional[str] = Field(None, description="IBAN number")
    account_number: Optional[str] = Field(None, description="Account number")
    account_purpose: Optional[str] = Field(None, description="Purpose of account")
    overdraft_limit: Optional[float] = Field(None, ge=0, description="Overdraft limit")


class AccountUpdate(BaseModel):
    """Account update model."""

    balance: Optional[float] = Field(None, ge=0, description="Account balance")
    account_purpose: Optional[str] = Field(None, description="Purpose of account")
    overdraft_limit: Optional[float] = Field(None, ge=0, description="Overdraft limit")


class AccountDetails(AccountBase):
    """Detailed account information model."""

    id: str = Field(..., description="Account ID")
    iban: Optional[str] = Field(None, description="IBAN number")
    account_number: Optional[str] = Field(None, description="Account number")
    account_purpose: Optional[str] = Field(None, description="Purpose of account")
    overdraft_limit: Optional[float] = Field(None, description="Overdraft limit")
    holder_name: Optional[str] = Field(None, description="Account holder name")
    provider_name: Optional[str] = Field(None, description="Account provider name")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class AccountSummary(BaseModel):
    """Account summary with basic statistics."""

    account: AccountDetails
    transaction_count: int = Field(..., description="Total transaction count")
    monthly_spending: float = Field(..., description="Monthly spending amount")
    monthly_income: float = Field(..., description="Monthly income amount")
    last_transaction_date: Optional[date] = Field(
        None, description="Date of last transaction"
    )


# Account API Models (for GraphDB integration)
class AccountBasic(BaseModel):
    """Basic account information model for API responses."""

    account_id: str = Field(..., description="Account number (primary identifier)")
    account_number: str = Field(..., description="Account number")
    account_type: str = Field(..., description="Type of account")
    balance: float = Field(..., description="Current balance")
    currency: str = Field(..., description="Account currency")
    display_name: Optional[str] = Field(None, description="Account display name")


class AccountDetailsAPI(BaseModel):
    """Detailed account information model for API responses."""

    account_id: str = Field(..., description="Account number (primary identifier)")
    account_number: str = Field(..., description="Account number")
    account_type: str = Field(..., description="Type of account")
    balance: float = Field(..., description="Current balance")
    currency: str = Field(..., description="Account currency")
    display_name: Optional[str] = Field(None, description="Account display name")
    iban: Optional[str] = Field(None, description="IBAN number")
    account_purpose: Optional[str] = Field(None, description="Purpose of account")
    overdraft_limit: Optional[float] = Field(None, description="Overdraft limit")
    holder_name: Optional[str] = Field(None, description="Account holder name")
    provider_name: Optional[str] = Field(None, description="Account provider name")
    internal_id: Optional[str] = Field(None, description="Internal system ID")


class AccountTransaction(BaseModel):
    """Account transaction model for API responses."""

    transaction_id: str = Field(..., description="Transaction ID")
    amount: float = Field(..., description="Transaction amount")
    date: str = Field(..., description="Transaction date")
    status: str = Field(..., description="Transaction status")
    transaction_type: Optional[str] = Field(None, description="Transaction type")
    merchant: Optional[str] = Field(None, description="Merchant name")


class AccountSummaryAPI(BaseModel):
    """Account summary with transactions for API responses."""

    account: AccountDetailsAPI
    recent_transactions: List[AccountTransaction]
    transaction_count: int
    monthly_spending: float
    monthly_income: float


# Transaction Models
class TransactionBase(BaseModel):
    """Base transaction model."""

    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: Currency = Field(Currency.CHF, description="Transaction currency")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    description: Optional[str] = Field(None, description="Transaction description")


class TransactionCreate(TransactionBase):
    """Transaction creation model."""

    payer_id: str = Field(..., description="Payer account/customer ID")
    payee_id: Optional[str] = Field(None, description="Payee account/customer ID")
    transaction_date: date = Field(
        default_factory=date.today, description="Transaction date"
    )
    value_date: Optional[date] = Field(None, description="Value date")


class TransactionUpdate(BaseModel):
    """Transaction update model."""

    status: Optional[TransactionStatus] = Field(None, description="Transaction status")
    description: Optional[str] = Field(None, description="Transaction description")
    value_date: Optional[date] = Field(None, description="Value date")


class TransactionDetails(TransactionBase):
    """Detailed transaction information model."""

    id: str = Field(..., description="Transaction ID")
    status: TransactionStatus = Field(..., description="Transaction status")
    transaction_date: date = Field(..., description="Transaction date")
    value_date: Optional[date] = Field(None, description="Value date")
    payer_name: Optional[str] = Field(None, description="Payer name")
    payee_name: Optional[str] = Field(None, description="Payee name")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    receipt_id: Optional[str] = Field(None, description="Receipt ID")
    has_receipt: bool = Field(False, description="Has receipt attached")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# Receipt Models
class ReceiptItemBase(BaseModel):
    """Base receipt item model."""

    item_description: str = Field(..., description="Item description")
    quantity: int = Field(..., gt=0, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")
    line_subtotal: float = Field(..., ge=0, description="Line subtotal")


class ReceiptItemCreate(ReceiptItemBase):
    """Receipt item creation model."""

    product_id: Optional[str] = Field(None, description="Product ID")


class ReceiptItemDetails(ReceiptItemBase):
    """Receipt item details model."""

    id: str = Field(..., description="Receipt item ID")
    product_name: Optional[str] = Field(None, description="Product name")
    category: Optional[str] = Field(None, description="Product category")


class ReceiptBase(BaseModel):
    """Base receipt model."""

    total_amount: float = Field(..., ge=0, description="Total receipt amount")
    receipt_date: date = Field(..., description="Receipt date")
    receipt_time: Optional[str] = Field(None, description="Receipt time")
    payment_method: Optional[str] = Field(None, description="Payment method")


class ReceiptCreate(ReceiptBase):
    """Receipt creation model."""

    transaction_id: str = Field(..., description="Associated transaction ID")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    vat_number: Optional[str] = Field(None, description="VAT number")
    items: List[ReceiptItemCreate] = Field(
        default_factory=list, description="Receipt items"
    )


class ReceiptDetails(ReceiptBase):
    """Receipt details model."""

    id: str = Field(..., description="Receipt ID")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    vat_number: Optional[str] = Field(None, description="VAT number")
    authorization_code: Optional[str] = Field(None, description="Authorization code")
    entry_mode: Optional[str] = Field(None, description="Entry mode")
    items: List[ReceiptItemDetails] = Field(
        default_factory=list, description="Receipt items"
    )


# Analytics Models
class CategorySpending(BaseModel):
    """Category spending model."""

    category: str = Field(..., description="Category name")
    total_spent: float = Field(..., description="Total amount spent")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: Optional[float] = Field(
        None, description="Percentage of total spending"
    )


class MerchantSpending(BaseModel):
    """Merchant spending model."""

    merchant: str = Field(..., description="Merchant name")
    total_spent: float = Field(..., description="Total amount spent")
    transaction_count: int = Field(..., description="Number of transactions")
    average_transaction: float = Field(..., description="Average transaction amount")


class MonthlyTrend(BaseModel):
    """Monthly spending trend model."""

    month: str = Field(..., description="Month (YYYY-MM-DD)")
    spending: float = Field(..., description="Total spending")
    income: float = Field(..., description="Total income")
    net: float = Field(..., description="Net amount (income - spending)")
    transaction_count: int = Field(..., description="Number of transactions")


class SpendingAnalytics(BaseModel):
    """Comprehensive spending analytics model."""

    total_spending: float = Field(..., description="Total spending amount")
    total_income: float = Field(..., description="Total income amount")
    net_amount: float = Field(..., description="Net amount (income - spending)")
    transaction_count: int = Field(..., description="Total transaction count")
    average_transaction: float = Field(..., description="Average transaction amount")
    top_categories: List[CategorySpending] = Field(
        default_factory=list, description="Top spending categories"
    )
    top_merchants: List[MerchantSpending] = Field(
        default_factory=list, description="Top merchants"
    )
    monthly_trends: Optional[List[MonthlyTrend]] = Field(
        None, description="Monthly spending trends"
    )


# Response Models
class CustomerResponse(BaseResponse):
    """Customer response model."""

    data: Union[CustomerDetails, List[CustomerDetails]] = Field(
        ..., description="Customer data"
    )


class AccountResponse(BaseResponse):
    """Account response model."""

    data: Union[AccountDetails, AccountSummary, List[AccountDetails]] = Field(
        ..., description="Account data"
    )


class TransactionResponse(BaseResponse):
    """Transaction response model."""

    data: Union[TransactionDetails, List[TransactionDetails]] = Field(
        ..., description="Transaction data"
    )


class ReceiptResponse(BaseResponse):
    """Receipt response model."""

    data: ReceiptDetails = Field(..., description="Receipt data")


class AnalyticsResponse(BaseResponse):
    """Analytics response model."""

    data: SpendingAnalytics = Field(..., description="Analytics data")


class PaginatedResponse(BaseResponse):
    """Paginated response model."""

    data: List[Union[CustomerDetails, AccountDetails, TransactionDetails]] = Field(
        ..., description="Response data"
    )
    pagination: Dict[str, Any] = Field(..., description="Pagination information")

    @classmethod
    def create(
        cls,
        data: List[Any],
        total_count: int,
        limit: int,
        offset: int,
        message: Optional[str] = None,
    ):
        """Create a paginated response."""
        has_next = offset + limit < total_count
        has_previous = offset > 0

        pagination = {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": has_next,
            "has_previous": has_previous,
            "page_count": (total_count + limit - 1) // limit if limit > 0 else 0,
            "current_page": (offset // limit) + 1 if limit > 0 else 1,
        }

        return cls(
            data=data,
            pagination=pagination,
            message=message or f"Retrieved {len(data)} items",
        )


# Error Models
class ErrorDetail(BaseModel):
    """Error detail model."""

    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Request success status")
    message: str = Field(..., description="Error message")
    errors: List[ErrorDetail] = Field(
        default_factory=list, description="Detailed errors"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


# GraphDB Query Models
class SparqlQuery(BaseModel):
    """SPARQL query model."""

    query: str = Field(..., description="SPARQL query string")
    prefixes: Optional[Dict[str, str]] = Field(None, description="SPARQL prefixes")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Query result limit")

    @validator("query")
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SparqlResult(BaseModel):
    """SPARQL query result model."""

    head: Dict[str, Any] = Field(..., description="Query head with variables")
    results: Dict[str, Any] = Field(..., description="Query results")
    execution_time: Optional[float] = Field(
        None, description="Query execution time in seconds"
    )


# Database Models
class DatabaseStatus(BaseModel):
    """Database connection status model."""

    status: str = Field(..., description="Connection status")
    database_type: str = Field(..., description="Type of database")
    error: Optional[str] = Field(None, description="Error message if connection failed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional connection details")


class DatabaseCheckResponse(BaseModel):
    """Complete database check response model."""

    overall_status: str = Field(..., description="Overall health status")
    databases: List[DatabaseStatus] = Field(..., description="List of database statuses")
    timestamp: str = Field(..., description="Check timestamp")


# OpenFoodFacts Models
class ProductSearchRequest(BaseModel):
    """Product search request model."""

    query: str = Field(..., min_length=2, description="Search query (product name, brand, category)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=50, description="Number of results per page")


class ProductAnalysisResponse(BaseModel):
    """Product analysis response model."""

    success: bool = Field(True, description="Request success status")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Nutritional analysis")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthyAlternativesRequest(BaseModel):
    """Healthy alternatives request model."""

    barcode: str = Field(..., description="Product barcode to find alternatives for")
    criteria: str = Field("nutri_score", description="Criteria for healthier alternatives")


class OpenFoodFactsBaseResponse(BaseModel):
    """Base response model for OpenFoodFacts API."""

    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")


class ProductResponse(OpenFoodFactsBaseResponse):
    """Single product response model."""

    product: Optional[Any] = Field(None, description="Product data")  # OpenFoodFactsProduct type


class SearchResponse(OpenFoodFactsBaseResponse):
    """Product search response model."""

    data: Any = Field(..., description="Search results")  # ProductSearchResult type


class AlternativesResponse(OpenFoodFactsBaseResponse):
    """Healthy alternatives response model."""

    data: Any = Field(..., description="Alternative products")  # HealthyAlternativesResult type


# OpenFoodFacts CRUD Models
class ProductNutrition(BaseModel):
    """Nutritional information for a product."""

    energy: Optional[float] = Field(None, description="Energy in kcal per 100g")
    fat: Optional[float] = Field(None, description="Fat content per 100g")
    saturated_fat: Optional[float] = Field(None, description="Saturated fat per 100g")
    carbohydrates: Optional[float] = Field(None, description="Carbohydrates per 100g")
    sugars: Optional[float] = Field(None, description="Sugars per 100g")
    proteins: Optional[float] = Field(None, description="Proteins per 100g")
    salt: Optional[float] = Field(None, description="Salt per 100g")
    fiber: Optional[float] = Field(None, description="Fiber per 100g")


class OpenFoodFactsProduct(BaseModel):
    """Product information from Open Food Facts."""

    id: str = Field(..., description="Product ID")
    barcode: str = Field(..., description="Product barcode")
    name: str = Field(..., description="Product name")
    brands: Optional[str] = Field(None, description="Product brands")
    ingredients: Optional[str] = Field(None, description="Ingredients list")
    allergens: Optional[str] = Field(None, description="Allergen information")
    nutri_score: Optional[str] = Field(None, description="Nutri-Score grade (A-E)")
    nova_group: Optional[int] = Field(None, description="NOVA group (1-4)")
    eco_score: Optional[str] = Field(None, description="Eco-Score grade (A-E)")
    image_url: Optional[str] = Field(None, description="Product image URL")
    nutrition_facts: Optional[ProductNutrition] = Field(None, description="Nutritional information")
    labels: Optional[str] = Field(None, description="Product labels")
    categories: Optional[str] = Field(None, description="Product categories")
    countries: Optional[str] = Field(None, description="Available countries")


class ProductSearchResult(BaseModel):
    """Search result for products."""

    products: List[OpenFoodFactsProduct] = Field(..., description="List of products")
    total_found: int = Field(..., description="Total number of products found")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of products per page")
    query: str = Field(..., description="Search query used")


class NutritionAnalysis(BaseModel):
    """Nutrition analysis result."""

    nutri_score_spending: Dict[str, float] = Field(..., description="Spending by Nutri-Score")
    nova_group_spending: Dict[str, float] = Field(..., description="Spending by NOVA group")
    eco_score_spending: Dict[str, float] = Field(..., description="Spending by Eco-Score")
    total_amount: float = Field(..., description="Total amount analyzed")
    analyzed_products: int = Field(..., description="Number of products analyzed")
    products_with_nutrition_data: int = Field(..., description="Products with nutrition data")
    recommendations: List[Dict[str, str]] = Field(..., description="Health recommendations")


class HealthyAlternativesResult(BaseModel):
    """Result for healthy alternatives search."""

    original_product: Optional[OpenFoodFactsProduct] = Field(None, description="Original product")
    alternatives: List[Dict[str, Any]] = Field(..., description="List of alternative products")
    total_alternatives_found: int = Field(..., description="Number of alternatives found")
    criteria_used: str = Field(..., description="Criteria used for comparison")


# Transaction API Models (for GraphDB integration)
class TransactionBasic(BaseModel):
    """Basic transaction information model for API responses."""

    transaction_id: str = Field(..., description="Transaction ID")
    amount: float = Field(..., description="Transaction amount")
    date: str = Field(..., description="Transaction date")
    status: str = Field(..., description="Transaction status")
    transaction_type: Optional[str] = Field(None, description="Transaction type")


class TransactionDetailsAPI(BaseModel):
    """Detailed transaction information model for API responses."""

    transaction_id: str = Field(..., description="Transaction ID")
    amount: float = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Currency")
    date: str = Field(..., description="Transaction date")
    value_date: Optional[str] = Field(None, description="Value date")
    status: str = Field(..., description="Transaction status")
    transaction_type: Optional[str] = Field(None, description="Transaction type")
    payer_name: Optional[str] = Field(None, description="Payer name")
    payee_name: Optional[str] = Field(None, description="Payee name")
    merchant: Optional[str] = Field(None, description="Merchant name")
    receipt_id: Optional[str] = Field(None, description="Receipt ID")
    has_receipt: bool = Field(False, description="Has receipt attached")


class ReceiptItemAPI(BaseModel):
    """Receipt line item model for API responses."""

    item_description: str = Field(..., description="Item description")
    quantity: int = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    line_subtotal: float = Field(..., description="Line subtotal")
    product_name: Optional[str] = Field(None, description="Product name")
    category: Optional[str] = Field(None, description="Product category")


class ReceiptDetailsAPI(BaseModel):
    """Receipt details model for API responses."""

    receipt_id: str = Field(..., description="Receipt ID")
    total_amount: float = Field(..., description="Total amount")
    receipt_date: str = Field(..., description="Receipt date")
    receipt_time: Optional[str] = Field(None, description="Receipt time")
    payment_method: Optional[str] = Field(None, description="Payment method")
    merchant: Optional[str] = Field(None, description="Merchant name")
    vat_number: Optional[str] = Field(None, description="VAT number")
    items: List[ReceiptItemAPI] = Field(default_factory=list, description="Receipt items")


class SpendingAnalyticsAPI(BaseModel):
    """Spending analytics model for API responses."""

    total_spending: float = Field(..., description="Total spending amount")
    total_income: float = Field(..., description="Total income amount")
    net_amount: float = Field(..., description="Net amount (income - spending)")
    transaction_count: int = Field(..., description="Total transaction count")
    average_transaction: float = Field(..., description="Average transaction amount")
    top_categories: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top spending categories"
    )
    top_merchants: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top merchants"
    )


# Filter Models
class TransactionFilter(DateRangeFilter):
    """Transaction filter model."""

    status: Optional[TransactionStatus] = Field(
        None, description="Transaction status filter"
    )
    transaction_type: Optional[TransactionType] = Field(
        None, description="Transaction type filter"
    )
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum amount filter")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum amount filter")
    customer_name: Optional[str] = Field(None, description="Customer name filter")
    merchant_name: Optional[str] = Field(None, description="Merchant name filter")

    @validator("max_amount")
    def max_amount_greater_than_min(cls, v, values):
        if v and values.get("min_amount") and v < values.get("min_amount"):
            raise ValueError("max_amount must be greater than min_amount")
        return v


class AccountFilter(BaseModel):
    """Account filter model."""

    account_type: Optional[AccountType] = Field(None, description="Account type filter")
    currency: Optional[Currency] = Field(None, description="Currency filter")
    min_balance: Optional[float] = Field(
        None, ge=0, description="Minimum balance filter"
    )
    max_balance: Optional[float] = Field(
        None, ge=0, description="Maximum balance filter"
    )
    holder_name: Optional[str] = Field(None, description="Account holder name filter")

    @validator("max_balance")
    def max_balance_greater_than_min(cls, v, values):
        if v and values.get("min_balance") and v < values.get("min_balance"):
            raise ValueError("max_balance must be greater than min_balance")
        return v
