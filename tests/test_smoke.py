"""
ReelSense - Comprehensive Smoke & Integration Tests
Validates real MovieLens catalog, hybrid ML model, cold start, and module imports.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_imports():
    from src.config import NAV_ITEMS, MOODS, COLOR_PALETTE, DEFAULT_USER
    from src.services.catalog import get_catalog, get_by_id
    from src.services.movie_service import MovieService
    from src.services.hybrid_model import get_model
    from src.services.recommendation_service import RecommendationService
    from src.components.sidebar import render_sidebar
    from src.components.topbar import render_topbar
    from src.components.movie_card import render_movie_card
    from src.components.hero_banner import render_hero_banner
    from src.components.movie_carousel import render_movie_carousel
    from src.components.trending_grid import render_trending_grid
    from src.components.mood_matrix import render_mood_matrix
    from src.pages.home import render_home_page
    from src.pages.discover import render_discover_page
    from src.pages.mood_explorer import render_mood_explorer_page
    from src.pages.movie_details import render_movie_details_page
    from src.pages.watchlist import render_watchlist_page
    from src.pages.ratings import render_ratings_page
    from src.pages.sense_ai import render_sense_ai_page
    from src.pages.profile import render_profile_page
    from src.pages.about import render_about_page

    assert len(NAV_ITEMS) >= 7, "Expected at least 7 nav items"
    assert len(MOODS) == 6, "Expected 6 moods"
    print("All module imports succeeded.")


def test_movielens_catalog():
    from src.services.catalog import get_catalog, get_by_id
    from src.services.movie_service import MovieService

    catalog = get_catalog()
    assert len(catalog) > 100, f"Expected catalog size > 100, got {len(catalog)}"

    first = catalog[0]
    required_keys = {"id", "title", "genres", "rating", "popularity", "overview", "poster_url"}
    assert required_keys.issubset(first.keys()), f"Missing keys in catalog movie: {required_keys - set(first.keys())}"

    # Check that MovieService retrieves movies from catalog
    all_movies = MovieService.get_all_movies()
    assert len(all_movies) == len(catalog)

    # Check search and filtering
    filtered = MovieService.filter_movies(query="shawshank")
    assert any("shawshank" in m["title"].lower() for m in filtered), "Expected Shawshank in search results"
    print(f"Catalog loaded {len(catalog)} MovieLens movies. Search verified.")


def test_cold_start():
    from src.services.recommendation_service import RecommendationService

    # 0 ratings
    res0 = RecommendationService.get_recommended_for_user({"ratings": {}}, limit=6)
    mode0 = RecommendationService.get_recommendation_mode({"ratings": {}})
    assert len(res0) == 6, f"Expected 6 cold start recommendations, got {len(res0)}"
    assert mode0 == "cold_start", f"Expected cold_start mode for 0 ratings, got {mode0}"

    # 2 ratings (still cold start)
    cat_ids = [m["id"] for m in res0[:2]]
    res2 = RecommendationService.get_recommended_for_user({"ratings": {cat_ids[0]: 4.5, cat_ids[1]: 5.0}}, limit=6)
    mode2 = RecommendationService.get_recommendation_mode({"ratings": {cat_ids[0]: 4.5, cat_ids[1]: 5.0}})
    assert mode2 == "cold_start", f"Expected cold_start mode for 2 ratings, got {mode2}"
    print("Cold-start verification passed (0 and 2 ratings).")


def test_hybrid_personalization():
    from src.services.catalog import get_catalog
    from src.services.recommendation_service import RecommendationService

    cat = get_catalog()
    ids = [cat[0]["id"], cat[1]["id"], cat[2]["id"]]

    # 3 ratings triggers hybrid model
    # Test with 10-point UI ratings to verify scaling normalization
    ui_ratings = {ids[0]: 9.5, ids[1]: 9.0, ids[2]: 8.0}
    res_hybrid = RecommendationService.get_recommended_for_user({"ratings": ui_ratings}, limit=6)
    mode_hybrid = RecommendationService.get_recommendation_mode({"ratings": ui_ratings})

    assert mode_hybrid == "hybrid", f"Expected hybrid mode for 3 ratings, got {mode_hybrid}"
    assert len(res_hybrid) == 6, f"Expected 6 hybrid recommendations, got {len(res_hybrid)}"

    # Verify explainability reasons exist
    assert any(len(m.get("why_recommended", [])) > 0 for m in res_hybrid), "Expected recommendation explanations"
    print("Hybrid personalization verification passed (3+ ratings with real explainability).")


if __name__ == "__main__":
    test_imports()
    test_movielens_catalog()
    test_cold_start()
    test_hybrid_personalization()
    print("\nALL SMOKE & INTEGRATION TESTS PASSED SUCCESSFULLY!")
