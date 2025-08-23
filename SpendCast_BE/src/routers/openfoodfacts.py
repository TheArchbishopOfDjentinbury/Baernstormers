"""Open Food Facts API router."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from src.crud.openfoodfacts import (
    fetch_product_by_barcode,
    search_products_by_query, 
    find_healthy_alternatives,
    analyze_product_nutrition,
    OpenFoodFactsProduct,
    ProductSearchResult,
    HealthyAlternativesResult,
    ProductNutrition
)

router = APIRouter(prefix="/api/v1/openfoodfacts", tags=["Open Food Facts"])

logger = logging.getLogger(__name__)


# Request/Response Models
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


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Response message")


class ProductResponse(BaseResponse):
    """Single product response model."""
    product: Optional[OpenFoodFactsProduct] = Field(None, description="Product data")


class SearchResponse(BaseResponse):
    """Product search response model."""
    data: ProductSearchResult = Field(..., description="Search results")


class AlternativesResponse(BaseResponse):
    """Healthy alternatives response model."""
    data: HealthyAlternativesResult = Field(..., description="Alternative products")


# Endpoints
@router.get("/health")
async def health_check():
    """Health check for Open Food Facts API integration."""
    return {
        "status": "healthy",
        "service": "Open Food Facts API Integration",
        "endpoints": [
            "/search - Search products",
            "/product/{barcode} - Get product by barcode",
            "/analyze/{barcode} - Analyze product nutrition",
            "/alternatives/{barcode} - Find healthy alternatives"
        ]
    }


@router.post("/search", response_model=SearchResponse)
async def search_products(request: ProductSearchRequest):
    """
    Search for food products by name, brand, or keywords.
    
    This endpoint allows you to search the Open Food Facts database for products
    using various criteria like product name, brand, or category.
    
    **Examples:**
    - Search by product name: "nutella"
    - Search by brand: "ferrero"
    - Search by category: "chocolate"
    """
    try:
        logger.info(f"Searching products with query: {request.query}")
        
        result = await search_products_by_query(
            query=request.query,
            page=request.page,
            page_size=request.page_size
        )
        
        message = f"Found {result.total_found} products matching '{request.query}'"
        
        return SearchResponse(
            success=True,
            message=message,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search products: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse)
async def search_products_get(
    query: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Results per page")
):
    """
    Search for food products by name, brand, or keywords (GET method).
    
    Same as POST /search but using query parameters for easier testing.
    """
    request = ProductSearchRequest(query=query, page=page, page_size=page_size)
    return await search_products(request)


@router.get("/product/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(barcode: str):
    """
    Get detailed product information by barcode.
    
    Retrieves comprehensive product information including:
    - Basic details (name, brand, ingredients)
    - Nutritional information per 100g
    - Quality scores (Nutri-Score, Nova Group, Eco-Score)
    - Allergen information
    - Product images and categories
    
    **Parameters:**
    - barcode: Product barcode (EAN, UPC, etc.) - usually 8-13 digits
    
    **Example barcodes:**
    - 5449000011114 (Coca-Cola)
    - 3017620422003 (Nutella)
    """
    try:
        logger.info(f"Fetching product with barcode: {barcode}")
        
        if not barcode or not barcode.strip():
            raise HTTPException(
                status_code=400,
                detail="Barcode is required"
            )
        
        clean_barcode = barcode.strip()
        product = await fetch_product_by_barcode(clean_barcode)
        
        if not product:
            return ProductResponse(
                success=False,
                message=f"Product with barcode {clean_barcode} not found in Open Food Facts database",
                product=None
            )
        
        return ProductResponse(
            success=True,
            message=f"Successfully retrieved product: {product.name}",
            product=product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product by barcode {barcode}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch product: {str(e)}"
        )


@router.get("/analyze/{barcode}", response_model=ProductAnalysisResponse)
async def analyze_product(barcode: str):
    """
    Analyze a product's nutritional information and quality scores.
    
    Provides detailed analysis including:
    - Nutri-Score interpretation (A-E rating)
    - NOVA Group analysis (processing level 1-4)
    - Eco-Score environmental impact (A-E rating)
    - Nutritional facts breakdown
    - Health recommendations
    
    **Parameters:**
    - barcode: Product barcode to analyze
    """
    try:
        logger.info(f"Analyzing product with barcode: {barcode}")
        
        if not barcode or not barcode.strip():
            raise HTTPException(
                status_code=400,
                detail="Barcode is required"
            )
        
        result = await analyze_product_nutrition(barcode.strip())
        
        if "error" in result:
            return ProductAnalysisResponse(
                success=False,
                error=result["error"],
                analysis=None
            )
        
        return ProductAnalysisResponse(
            success=True,
            analysis=result["analysis"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing product {barcode}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze product: {str(e)}"
        )


@router.post("/alternatives", response_model=AlternativesResponse)
async def find_alternatives(request: HealthyAlternativesRequest):
    """
    Find healthier alternatives to a given product.
    
    Searches for products in the same category that have better:
    - Nutri-Score ratings
    - NOVA Group classifications (less processed)
    - Eco-Score ratings (more environmentally friendly)
    
    **Request body:**
    - barcode: Product barcode to find alternatives for
    - criteria: "nutri_score", "nova_group", "eco_score", or "all"
    """
    try:
        logger.info(f"Finding alternatives for barcode: {request.barcode} with criteria: {request.criteria}")
        
        result = await find_healthy_alternatives(
            barcode=request.barcode,
            criteria=request.criteria
        )
        
        if not result.original_product:
            return AlternativesResponse(
                success=False,
                message=f"Original product with barcode {request.barcode} not found",
                data=result
            )
        
        message = f"Found {result.total_alternatives_found} healthier alternatives to {result.original_product.name}"
        
        return AlternativesResponse(
            success=True,
            message=message,
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error finding alternatives: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find alternatives: {str(e)}"
        )


@router.get("/alternatives/{barcode}", response_model=AlternativesResponse)
async def find_alternatives_get(
    barcode: str,
    criteria: str = Query("nutri_score", description="Criteria for healthier alternatives")
):
    """
    Find healthier alternatives to a given product (GET method).
    
    Same as POST /alternatives but using path and query parameters.
    """
    request = HealthyAlternativesRequest(barcode=barcode, criteria=criteria)
    return await find_alternatives(request)


@router.get("/categories")
async def get_popular_categories():
    """
    Get list of popular food categories for search suggestions.
    
    Returns commonly searched categories that can be used
    as search terms or filters.
    """
    try:
        popular_categories = [
            "beverages",
            "snacks", 
            "dairy",
            "bread",
            "chocolate",
            "cereals",
            "fruits",
            "vegetables",
            "meat",
            "fish",
            "frozen-foods",
            "condiments",
            "desserts",
            "pasta",
            "rice",
            "oils",
            "cheese",
            "yogurt",
            "cookies",
            "ice-cream"
        ]
        
        return {
            "success": True,
            "categories": popular_categories,
            "total": len(popular_categories),
            "usage": "Use these categories as search terms in the /search endpoint"
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get("/brands")
async def get_popular_brands():
    """
    Get list of popular food brands for search suggestions.
    
    Returns commonly searched brands that can be used
    as search terms.
    """
    try:
        popular_brands = [
            "Nestle",
            "Ferrero", 
            "Coca-Cola",
            "Pepsi",
            "Danone",
            "Unilever",
            "Kellogg's",
            "Mars",
            "Mondelez",
            "Kraft",
            "General Mills",
            "L'Oreal",
            "Barilla",
            "Heinz",
            "Campbell",
            "Migros",
            "Coop",
            "Denner"
        ]
        
        return {
            "success": True,
            "brands": popular_brands,
            "total": len(popular_brands),
            "usage": "Use these brands as search terms in the /search endpoint"
        }
        
    except Exception as e:
        logger.error(f"Error getting brands: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get brands: {str(e)}"
        )


@router.get("/stats")
async def get_api_stats():
    """
    Get statistics and information about the Open Food Facts integration.
    
    Provides metadata about the service and usage statistics.
    """
    try:
        stats = {
            "service": "Open Food Facts API Integration",
            "version": "1.0.0",
            "database": "Open Food Facts",
            "api_base_url": "https://world.openfoodfacts.org/api/v2/",
            "search_endpoint": "https://world.openfoodfacts.org/cgi/search.pl",
            "features": [
                "Product search by name/brand/category",
                "Detailed product information by barcode",
                "Nutritional analysis and health scores",
                "Healthy alternatives recommendations",
                "Multi-language support",
                "Real-time data from Open Food Facts database"
            ],
            "supported_scores": {
                "nutri_score": "Nutritional quality rating (A-E)",
                "nova_group": "Food processing level (1-4)",
                "eco_score": "Environmental impact rating (A-E)"
            },
            "data_coverage": "Over 2.8 million products worldwide",
            "update_frequency": "Real-time updates from contributors"
        }
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get API stats: {str(e)}"
        )
