"""Open Food Facts API CRUD operations."""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus

import httpx

from src.models import (
    ProductNutrition,
    OpenFoodFactsProduct,
    ProductSearchResult,
    NutritionAnalysis,
    HealthyAlternativesResult,
)

logger = logging.getLogger(__name__)


# CRUD Functions
async def fetch_product_by_barcode(barcode: str) -> Optional[OpenFoodFactsProduct]:
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
        logger.error(f"HTTP error fetching product {barcode}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching product {barcode}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching product {barcode}: {e}")
        return None


async def search_products_by_query(
    query: str, page: int = 1, page_size: int = 10
) -> ProductSearchResult:
    """
    Search for products in Open Food Facts by name or brand.

    :param query: Search query
    :param page: Page number (1-based)
    :param page_size: Number of results per page
    :return: Search results
    """
    if not query or len(query.strip()) < 2:
        return ProductSearchResult(
            products=[], total_found=0, page=page, page_size=page_size, query=query
        )

    encoded_query = quote_plus(query)
    url = f"https://world.openfoodfacts.org/cgi/search.pl"

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

            return ProductSearchResult(
                products=products,
                total_found=len(products),
                page=page,
                page_size=page_size,
                query=query,
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error searching products: {e.response.status_code}")
        return ProductSearchResult(
            products=[], total_found=0, page=page, page_size=page_size, query=query
        )
    except httpx.RequestError as e:
        logger.error(f"Request error searching products: {e}")
        return ProductSearchResult(
            products=[], total_found=0, page=page, page_size=page_size, query=query
        )
    except Exception as e:
        logger.error(f"Unexpected error searching products: {e}")
        return ProductSearchResult(
            products=[], total_found=0, page=page, page_size=page_size, query=query
        )


async def find_healthy_alternatives(
    barcode: str, criteria: str = "nutri_score"
) -> HealthyAlternativesResult:
    """
    Find healthier alternatives to a given product.

    :param barcode: Barcode of the product to find alternatives for
    :param criteria: Criteria for "healthier" - "nutri_score", "nova_group", "eco_score", or "all"
    :return: Healthier alternatives
    """
    try:
        # First, get the original product
        original_product = await fetch_product_by_barcode(barcode.strip())

        if not original_product:
            return HealthyAlternativesResult(
                original_product=None,
                alternatives=[],
                total_alternatives_found=0,
                criteria_used=criteria,
            )

        # Extract main category for searching alternatives
        categories = original_product.categories or ""
        main_category = categories.split(",")[0].strip() if categories else ""

        if not main_category:
            return HealthyAlternativesResult(
                original_product=original_product,
                alternatives=[],
                total_alternatives_found=0,
                criteria_used=criteria,
            )

        # Search for products in the same category
        search_result = await search_products_by_query(
            main_category, page=1, page_size=20
        )
        alternative_products = search_result.products

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

        return HealthyAlternativesResult(
            original_product=original_product,
            alternatives=better_alternatives,
            total_alternatives_found=len(better_alternatives),
            criteria_used=criteria,
        )

    except Exception as e:
        logger.error(f"Error finding healthy alternatives: {e}")
        return HealthyAlternativesResult(
            original_product=None,
            alternatives=[],
            total_alternatives_found=0,
            criteria_used=criteria,
        )


async def analyze_product_nutrition(barcode: str) -> Dict[str, Any]:
    """
    Analyze a single product's nutritional information.

    :param barcode: Product barcode
    :return: Nutritional analysis
    """
    try:
        product = await fetch_product_by_barcode(barcode)

        if not product:
            return {
                "error": f"Product with barcode {barcode} not found",
                "analysis": None,
            }

        # Create nutritional analysis
        analysis = {
            "product": product.dict(),
            "health_scores": {
                "nutri_score": {
                    "grade": product.nutri_score or "unknown",
                    "meaning": _get_nutri_score_meaning(product.nutri_score),
                },
                "nova_group": {
                    "group": product.nova_group or "unknown",
                    "meaning": _get_nova_group_meaning(product.nova_group),
                },
                "eco_score": {
                    "grade": product.eco_score or "unknown",
                    "meaning": _get_eco_score_meaning(product.eco_score),
                },
            },
            "nutrition_facts": product.nutrition_facts.dict()
            if product.nutrition_facts
            else None,
            "recommendations": _generate_product_recommendations(product),
        }

        return {"analysis": analysis}

    except Exception as e:
        logger.error(f"Error analyzing product nutrition: {e}")
        return {"error": f"Failed to analyze product: {str(e)}", "analysis": None}


def _get_nutri_score_meaning(score: Optional[str]) -> str:
    """Get meaning of Nutri-Score grade."""
    meanings = {
        "A": "Очень хорошее питательное качество",
        "B": "Хорошее питательное качество",
        "C": "Удовлетворительное питательное качество",
        "D": "Плохое питательное качество",
        "E": "Очень плохое питательное качество",
    }
    return meanings.get(score, "Оценка недоступна")


def _get_nova_group_meaning(group: Optional[int]) -> str:
    """Get meaning of NOVA group."""
    meanings = {
        1: "Необработанные или минимально обработанные продукты",
        2: "Обработанные кулинарные ингредиенты",
        3: "Обработанные продукты",
        4: "Ультраобработанные продукты",
    }
    return meanings.get(group, "Группа недоступна")


def _get_eco_score_meaning(score: Optional[str]) -> str:
    """Get meaning of Eco-Score grade."""
    meanings = {
        "A": "Очень низкое воздействие на окружающую среду",
        "B": "Низкое воздействие на окружающую среду",
        "C": "Умеренное воздействие на окружающую среду",
        "D": "Высокое воздействие на окружающую среду",
        "E": "Очень высокое воздействие на окружающую среду",
    }
    return meanings.get(score, "Оценка недоступна")


def _generate_product_recommendations(product: OpenFoodFactsProduct) -> List[str]:
    """Generate recommendations based on product analysis."""
    recommendations = []

    # Nutri-Score recommendations
    if product.nutri_score in ["D", "E"]:
        recommendations.append(
            "Рассмотрите выбор продуктов с лучшими оценками Nutri-Score (A, B, C)"
        )

    # NOVA group recommendations
    if product.nova_group == 4:
        recommendations.append(
            "Это ультраобработанный продукт. Рассмотрите менее обработанные альтернативы"
        )

    # Eco-Score recommendations
    if product.eco_score in ["D", "E"]:
        recommendations.append(
            "Этот продукт имеет высокое воздействие на окружающую среду. Рассмотрите более экологичные варианты"
        )

    # Nutritional recommendations
    if product.nutrition_facts:
        nutrition = product.nutrition_facts
        if nutrition.sugars and nutrition.sugars > 20:
            recommendations.append("Высокое содержание сахара. Ограничьте потребление")
        if nutrition.salt and nutrition.salt > 1.5:
            recommendations.append(
                "Высокое содержание соли. Обратите внимание на потребление натрия"
            )
        if nutrition.saturated_fat and nutrition.saturated_fat > 5:
            recommendations.append("Высокое содержание насыщенных жиров")

    if not recommendations:
        recommendations.append("Продукт имеет приемлемые показатели качества")

    return recommendations
