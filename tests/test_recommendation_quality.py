"""
ReelSense - Phase 4 Recommendation Quality & Personalization Differentiation Test
Verifies:
1. Distinct user preference profiles produce distinctly different, sensible recommendations:
   - Profile A (Sci-Fi / Adventure)
   - Profile B (Drama / Crime)
   - Profile C (Animation / Comedy / Romance)
2. Cold-start threshold: 0-2 ratings -> "cold_start", 3+ ratings -> "hybrid"
"""

import pytest
from src.services.recommendation_service import RecommendationService
from src.services.catalog import get_catalog


def test_recommendation_quality_profiles_differ():
    # Profile A: Sci-Fi / Adventure (Star Wars, Matrix, Jurassic Park)
    profile_a_ratings = {260: 5.0, 2571: 5.0, 480: 5.0}

    # Profile B: Drama / Crime (Shawshank, Godfather, Pulp Fiction)
    profile_b_ratings = {318: 5.0, 858: 5.0, 296: 5.0}

    # Profile C: Animation / Family / Comedy (Toy Story, Aladdin, Lion King)
    profile_c_ratings = {1: 5.0, 588: 5.0, 364: 5.0}

    recs_a = RecommendationService.get_recommended_for_user({"ratings": profile_a_ratings}, limit=6)
    recs_b = RecommendationService.get_recommended_for_user({"ratings": profile_b_ratings}, limit=6)
    recs_c = RecommendationService.get_recommended_for_user({"ratings": profile_c_ratings}, limit=6)

    ids_a = set(m["id"] for m in recs_a)
    ids_b = set(m["id"] for m in recs_b)
    ids_c = set(m["id"] for m in recs_c)

    # 1. Verification that all recommendations return results
    assert len(ids_a) == 6
    assert len(ids_b) == 6
    assert len(ids_c) == 6

    # 2. Recommendations for different profiles must be distinctly different
    overlap_ab = len(ids_a & ids_b)
    overlap_ac = len(ids_a & ids_c)
    overlap_bc = len(ids_b & ids_c)

    assert overlap_ab < 4, f"Profile A and B have too much overlap ({overlap_ab}/6)"
    assert overlap_ac < 4, f"Profile A and C have too much overlap ({overlap_ac}/6)"
    assert overlap_bc < 4, f"Profile B and C have too much overlap ({overlap_bc}/6)"

    # 3. Genre affinity coherence
    genres_a = [g for m in recs_a for g in m.get("genres", [])]
    genres_b = [g for m in recs_b for g in m.get("genres", [])]
    genres_c = [g for m in recs_c for g in m.get("genres", [])]

    # Profile A should feature Sci-Fi / Action / Adventure heavily
    assert any(g in ["Sci-Fi", "Action", "Adventure"] for g in genres_a)

    # Profile B should feature Drama / Crime heavily
    assert any(g in ["Drama", "Crime"] for g in genres_b)

    # Profile C should feature Animation / Children / Comedy / Adventure heavily
    assert any(g in ["Animation", "Children", "Comedy", "Musical"] for g in genres_c)


def test_cold_start_vs_hybrid_thresholds():
    # 0 ratings
    mode_0 = RecommendationService.get_recommendation_mode({"ratings": {}})
    assert mode_0 == "cold_start"

    # 1 rating
    mode_1 = RecommendationService.get_recommendation_mode({"ratings": {1: 4.5}})
    assert mode_1 == "cold_start"

    # 2 ratings
    mode_2 = RecommendationService.get_recommendation_mode({"ratings": {1: 4.5, 260: 5.0}})
    assert mode_2 == "cold_start"

    # 3 ratings
    mode_3 = RecommendationService.get_recommendation_mode({"ratings": {1: 4.5, 260: 5.0, 318: 5.0}})
    assert mode_3 == "hybrid"

    # 4 ratings
    mode_4 = RecommendationService.get_recommendation_mode({"ratings": {1: 4.5, 260: 5.0, 318: 5.0, 296: 4.0}})
    assert mode_4 == "hybrid"
