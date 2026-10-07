"""
ReelSense - Phase 6 Test Suite: Recommendation Intelligence & Taste Evolution
Covers:
  - Recommendation Breakdown 2.0 (Tests 1-7)
  - Taste Evolution Analytics (Tests A-G)
"""
import time
import pytest
from src.services.catalog import get_catalog
from src.services.hybrid_model import get_model
from src.services.recommendation_service import RecommendationService
from src.services.taste_service import TasteService
from src.services.movie_service import MovieService


# =============================================================================
# FEATURE 1: RECOMMENDATION BREAKDOWN / WHY RECOMMENDED 2.0 (TESTS 1 - 7)
# =============================================================================

def test_1_user_with_3_plus_ratings_receives_explanation():
    """Test 1: A user with 3+ ratings receives an explanation."""
    # Toy Story (1), Star Wars (260), Jurassic Park (480)
    user_ratings = {1: 9.0, 260: 9.5, 480: 8.5}
    # Matrix (2571)
    movie = MovieService.get_movie_by_id(2571)
    assert movie is not None

    breakdown = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)
    assert breakdown.get("in_catalog") is True
    assert breakdown.get("is_cold_start") is False
    assert breakdown.get("content_match_pct") is not None
    assert breakdown.get("collab_match_pct") is not None
    assert breakdown.get("hybrid_score") is not None
    assert len(breakdown.get("narrative", [])) > 0


def test_2_explanation_uses_actual_recommendation_signals():
    """Test 2: Explanation uses actual recommendation signals."""
    user_ratings = {1: 8.0, 260: 10.0, 480: 9.0}
    movie = MovieService.get_movie_by_id(2571)
    
    breakdown = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)
    c_score = breakdown["content_score"]
    cl_score = breakdown["collab_score"]
    h_score = breakdown["hybrid_score"]
    expected_hybrid = round(0.4 * c_score + 0.6 * cl_score, 3)
    assert abs(h_score - expected_hybrid) <= 0.01
    assert breakdown["content_contrib"] == round(0.4 * c_score, 3)
    assert breakdown["collab_contrib"] == round(0.6 * cl_score, 3)


def test_3_explanation_does_not_contain_fabricated_values():
    """Test 3: Explanation does not contain fabricated/random values."""
    user_ratings = {1: 9.0, 260: 9.0, 318: 10.0}
    movie = MovieService.get_movie_by_id(296)  # Pulp Fiction

    b1 = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)
    b2 = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)

    assert b1["content_score"] == b2["content_score"]
    assert b1["collab_score"] == b2["collab_score"]
    assert b1["hybrid_score"] == b2["hybrid_score"]
    assert b1["positive_references"] == b2["positive_references"]
    assert 0.0 <= b1["content_score"] <= 1.0
    assert 0.0 <= b1["collab_score"] <= 1.0
    assert 0.0 <= b1["hybrid_score"] <= 1.0


def test_4_cold_start_explanation_does_not_claim_personalization():
    """Test 4: Cold-start explanation does not claim unavailable personalization."""
    movie = MovieService.get_movie_by_id(1)
    b_zero = TasteService.get_recommendation_breakdown(movie, user_ratings={})
    assert b_zero["is_cold_start"] is True
    assert b_zero["content_score"] is None
    assert b_zero["collab_score"] is None
    assert b_zero["hybrid_score"] is None
    assert any("uninitialized" in n.lower() or "cold-start" in n.lower() or "rate 3" in n.lower() for n in b_zero["narrative"])

    b_one = TasteService.get_recommendation_breakdown(movie, user_ratings={260: 9.0})
    assert b_one["is_cold_start"] is True
    assert b_one["collab_score"] is None
    assert any("developing" in n.lower() or "unlocks at 3" in n.lower() for n in b_one["narrative"])


def test_5_positive_reference_movies_come_from_actual_user_ratings():
    """Test 5: Positive reference movies come from the user's actual ratings."""
    user_ratings = {1: 9.5, 260: 10.0, 318: 9.0, 593: 8.5}
    movie = MovieService.get_movie_by_id(1196)
    b = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)

    refs = b["positive_references"]
    assert len(refs) > 0
    ref_ids = [r["id"] for r in refs]
    for rid in ref_ids:
        assert rid in user_ratings
    assert refs[0]["id"] == 260
    assert refs[0]["similarity"] > 0.5


def test_6_excluded_movies_are_not_used_as_active_recommendations():
    """Test 6: Excluded movies are not used as active recommendations."""
    user_ratings = {1: 9.0, 260: 9.0, 318: 9.0}
    recs = RecommendationService.get_recommended_for_user(
        {"ratings": user_ratings, "hidden_ids": [1196, 2571]}, limit=10
    )
    rec_ids = [m["id"] for m in recs]
    assert 1196 not in rec_ids
    assert 2571 not in rec_ids


def test_7_explanation_handles_missing_weak_signals_gracefully():
    """Test 7: Explanation handles missing/weak signals gracefully."""
    b_invalid = TasteService.get_recommendation_breakdown(99999999, user_ratings={1: 9.0})
    assert b_invalid.get("in_catalog") is False

    b_none = TasteService.get_recommendation_breakdown(None, user_ratings=None)
    assert b_none.get("in_catalog") is False

    movie = MovieService.get_movie_by_id(1)
    b_sparse = TasteService.get_recommendation_breakdown(movie, user_ratings={1: 2.0, 2: 2.0, 3: 2.0})
    assert b_sparse.get("in_catalog") is True
    assert b_sparse.get("strength_label") is not None


# =============================================================================
# FEATURE 2: TASTE EVOLUTION ANALYTICS (TESTS A - G)
# =============================================================================

def test_a_zero_ratings_valid_empty_state():
    """Test A: Zero ratings -> valid empty state."""
    evo = TasteService.get_taste_evolution({})
    assert evo["is_empty"] is True
    assert evo["is_minimal"] is False
    assert evo["total_rated"] == 0
    assert evo["milestones"] == []
    assert evo["insights"]["emerging"] is None
    assert "Rate movies" in evo["insights"]["summary"]


def test_b_one_rating_valid_minimal_state():
    """Test B: One rating -> valid minimal state."""
    evo = TasteService.get_taste_evolution({1: 9.0})
    assert evo["is_empty"] is False
    assert evo["is_minimal"] is True
    assert evo["total_rated"] == 1
    assert len(evo["milestones"]) == 1
    assert evo["milestones"][0]["cutoff"] == 1
    assert "1st Rating" in evo["milestones"][0]["label"]
    assert "developing" in evo["insights"]["summary"].lower() or "forming" in evo["insights"]["summary"].lower()


def test_c_three_ratings_evolution_data_generated():
    """Test C: Three ratings -> evolution data generated."""
    evo = TasteService.get_taste_evolution({1: 9.0, 260: 9.5, 318: 10.0})
    assert evo["is_empty"] is False
    assert evo["is_minimal"] is False
    assert evo["total_rated"] == 3
    cutoffs = [m["cutoff"] for m in evo["milestones"]]
    assert cutoffs == [1, 3]
    assert "1st Rating" in evo["milestones"][0]["label"]
    assert "3rd Rating" in evo["milestones"][1]["label"]
    assert len(evo["top_genres"]) > 0
    assert len(evo["evolution_matrix"]) > 0


def test_d_genre_calculations_match_existing_taste_profile_logic():
    """Test D: Genre calculations match existing taste-profile logic."""
    test_ratings = {1: 8.0, 260: 10.0}
    evo = TasteService.get_taste_evolution(test_ratings)
    current_m = evo["milestones"][-1]

    cat_by_id = {m["id"]: m for m in get_catalog()}
    expected_weights = {}
    for mid, score in test_ratings.items():
        m = cat_by_id.get(mid)
        if m:
            for g in m.get("genres", []):
                expected_weights[g] = expected_weights.get(g, 0.0) + float(score)

    assert current_m["genre_weights"] == expected_weights
    assert current_m["genre_weights"]["Adventure"] == 18.0
    assert current_m["dominant_genre"] == "Adventure"


def test_e_milestones_never_exceed_actual_rating_count():
    """Test E: Milestones never exceed actual rating count."""
    for n in [1, 2, 3, 4, 7, 10, 15]:
        cat = get_catalog()
        ratings_sample = {cat[i]["id"]: 8.0 for i in range(n)}
        evo = TasteService.get_taste_evolution(ratings_sample)
        for m in evo["milestones"]:
            assert m["cutoff"] <= n, f"Milestone cutoff {m['cutoff']} exceeded rating count {n}"


def test_f_taste_changes_are_calculated_rather_than_hardcoded():
    """Test F: Taste changes are calculated rather than hardcoded."""
    user_ratings = {1: 6.0, 260: 10.0, 1196: 10.0, 1210: 10.0, 2571: 10.0}
    evo = TasteService.get_taste_evolution(user_ratings)
    shifts = evo["taste_shifts"]
    sci_fi_shift = next((s for s in shifts if s["genre"] == "Sci-Fi"), None)
    assert sci_fi_shift is not None
    assert sci_fi_shift["direction"] == "up"
    assert sci_fi_shift["delta"] > 0
    # Emerging genre must be dynamically detected among the newly introduced genres
    assert evo["insights"]["emerging"] in ["Sci-Fi", "Action"]


def test_g_large_rating_histories_remain_performant():
    """Test G: Large rating histories remain performant."""
    cat = get_catalog()
    large_ratings = {cat[i]["id"]: 7.5 + (i % 5) * 0.5 for i in range(100)}

    t0 = time.time()
    evo = TasteService.get_taste_evolution(large_ratings)
    elapsed = time.time() - t0

    assert evo["total_rated"] == 100
    assert elapsed < 0.1, f"Taste evolution calculation took too long: {elapsed:.3f}s"
    assert len(evo["milestones"]) <= 7
