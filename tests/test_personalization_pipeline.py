"""
ReelSense - End-to-End Personalization Pipeline & Algorithm Tests
Validates the complete personalization pipeline, taste profiling, positive/negative weighting,
watchlist weak signal, exclusions, cache invalidation, and cold-start fallback.
"""

import pytest
from src.services.recommendation_service import RecommendationService
from src.services.hybrid_model import HybridModel, get_model
from src.services.catalog import get_catalog
from src.services.user_store import load, save, get_default_state


def test_empty_user_cold_start_fallback():
    """Requirement 1: Empty user profile produces generic/cold-start recommendations."""
    empty_prefs = {"ratings": {}, "watchlist": [], "hidden_ids": []}
    recs = RecommendationService.get_recommended_for_user(empty_prefs, limit=10)
    assert len(recs) == 10
    mode = RecommendationService.get_recommendation_mode(empty_prefs)
    assert mode == "cold_start"

    # Diagnostics should identify cold start
    diag = RecommendationService.get_user_recommendation_diagnostics(empty_prefs)
    assert diag["strategy"] == "cold_start_generic"
    assert diag["ratings_count"] == 0
    assert diag["has_taste_profile"] is False


def test_single_5star_rating_produces_personalized_candidates():
    """Requirement 2: Even 1 rating (5-star) generates personalized candidates that differ from cold-start."""
    empty_prefs = {"ratings": {}, "watchlist": [], "hidden_ids": []}
    cold_recs = RecommendationService.get_recommended_for_user(empty_prefs, limit=10)
    cold_ids = [m["id"] for m in cold_recs]

    # Rate Toy Story (ID 1) with 5.0 stars
    single_rating_prefs = {"ratings": {1: 5.0}, "watchlist": [], "hidden_ids": []}
    pers_recs = RecommendationService.get_recommended_for_user(single_rating_prefs, limit=10)
    pers_ids = [m["id"] for m in pers_recs]

    assert len(pers_recs) == 10
    # Must NOT be identical to generic cold-start
    assert pers_ids != cold_ids
    # Rated movie itself (1) MUST be excluded
    assert 1 not in pers_ids

    # Diagnostics should show content-dominant personalization
    diag = RecommendationService.get_user_recommendation_diagnostics(single_rating_prefs)
    assert diag["ratings_count"] == 1
    assert diag["positive_count"] == 1
    assert diag["negative_count"] == 0
    assert diag["has_taste_profile"] is True
    assert diag["strategy"] == "content_personalized"


def test_multiple_ratings_builds_taste_profile():
    """Requirement 3: Multiple ratings activate hybrid recommendation and valid taste profile."""
    prefs = {
        "ratings": {1: 5.0, 3114: 5.0, 78499: 4.5},  # Toy Story 1, 2, 3
        "watchlist": [],
        "hidden_ids": [],
    }
    recs = RecommendationService.get_recommended_for_user(prefs, limit=10)
    rec_ids = [m["id"] for m in recs]

    assert len(recs) == 10
    # All 3 rated movies must be excluded
    assert 1 not in rec_ids
    assert 3114 not in rec_ids
    assert 78499 not in rec_ids

    diag = RecommendationService.get_user_recommendation_diagnostics(prefs)
    assert diag["ratings_count"] == 3
    assert diag["strategy"] == "hybrid_personalized"
    assert diag["has_taste_profile"] is True


def test_high_vs_low_rating_shifts_recommendations():
    """Requirement 4: 5-star vs 1-star rating changes ranking and penalizes similar movies."""
    # When user rates Toy Story 5 stars
    positive_prefs = {"ratings": {1: 5.0}, "watchlist": [], "hidden_ids": []}
    recs_pos = RecommendationService.get_recommended_for_user(positive_prefs, limit=20)
    pos_ids = [m["id"] for m in recs_pos]

    # When user rates Toy Story 0.5 stars (strong negative) and Alien (1214) 5.0 stars
    divergent_prefs = {"ratings": {1: 0.5, 1214: 5.0}, "watchlist": [], "hidden_ids": []}
    recs_div = RecommendationService.get_recommended_for_user(divergent_prefs, limit=20)
    div_ids = [m["id"] for m in recs_div]

    # The recommendations must differ significantly
    assert pos_ids != div_ids
    # In positive_prefs, Toy Story 2 (3114) or animation should rank high
    # In divergent_prefs, sci-fi/horror titles like Aliens (1200) should rank high
    assert any(m["id"] == 1200 for m in recs_div), "Aliens should be recommended when Alien is 5 stars"


def test_watchlist_affects_taste_weakly():
    """Requirement 5: Watchlist provides a positive signal without overwhelming explicit ratings."""
    # User with only watchlist (no ratings)
    watchlist_only_prefs = {"ratings": {}, "watchlist": [1], "hidden_ids": []}  # Toy Story on watchlist
    recs = RecommendationService.get_recommended_for_user(watchlist_only_prefs, limit=10)
    rec_ids = [m["id"] for m in recs]

    # 1. Watchlisted movie itself must be excluded from "Recommended for You"
    assert 1 not in rec_ids

    # 2. Taste profile was built from watchlist
    diag = RecommendationService.get_user_recommendation_diagnostics(watchlist_only_prefs)
    assert diag["watchlist_count"] == 1
    assert diag["has_taste_profile"] is True

    # 3. Compared to generic cold-start, recommendations are influenced by Toy Story
    empty_prefs = {"ratings": {}, "watchlist": [], "hidden_ids": []}
    cold_recs = RecommendationService.get_recommended_for_user(empty_prefs, limit=10)
    cold_ids = [m["id"] for m in cold_recs]
    assert rec_ids != cold_ids


def test_rated_movies_excluded():
    """Requirement 6: Rated movies are strictly excluded from recommendation results."""
    rated_ids = [1, 260, 318, 588]
    prefs = {"ratings": {mid: 5.0 for mid in rated_ids}, "watchlist": [], "hidden_ids": []}
    recs = RecommendationService.get_recommended_for_user(prefs, limit=20)
    rec_ids = {m["id"] for m in recs}

    for mid in rated_ids:
        assert mid not in rec_ids, f"Rated movie {mid} appeared in recommendations!"


def test_watchlisted_movies_excluded():
    """Requirement 7: Watchlisted movies are strictly excluded from Recommended For You."""
    wl_ids = [296, 593, 2571]
    prefs = {"ratings": {1: 5.0, 318: 5.0, 260: 4.5}, "watchlist": wl_ids, "hidden_ids": []}
    recs = RecommendationService.get_recommended_for_user(prefs, limit=20)
    rec_ids = {m["id"] for m in recs}

    for mid in wl_ids:
        assert mid not in rec_ids, f"Watchlisted movie {mid} appeared in recommendations!"


def test_hidden_movies_excluded():
    """Requirement 8: Hidden / Not Interested movies are strictly excluded from recommendations."""
    hidden = [480, 1196, 1210]  # Jurassic Park, Empire Strikes Back, Return of Jedi
    prefs = {"ratings": {260: 5.0}, "watchlist": [], "hidden_ids": hidden}  # Rated Star Wars A New Hope
    recs = RecommendationService.get_recommended_for_user(prefs, limit=20)
    rec_ids = {m["id"] for m in recs}

    for mid in hidden:
        assert mid not in rec_ids, f"Hidden movie {mid} appeared in recommendations!"


def test_preference_version_and_cache_invalidation():
    """Requirement 9: Changing user preference updates cache key and recalculates fresh results."""
    prefs_v1 = {"ratings": {1: 5.0}, "watchlist": [], "hidden_ids": []}
    recs_v1 = RecommendationService.get_recommended_for_user(prefs_v1, limit=6)

    # Now change rating to 1.0
    prefs_v2 = {"ratings": {1: 1.0}, "watchlist": [], "hidden_ids": []}
    recs_v2 = RecommendationService.get_recommended_for_user(prefs_v2, limit=6)

    ids_v1 = [m["id"] for m in recs_v1]
    ids_v2 = [m["id"] for m in recs_v2]

    # Recommendations must change when preference version/values change
    assert ids_v1 != ids_v2


def test_deterministic_different_users_produce_distinct_recommendations():
    """Requirement 11 & 16: Two users with distinct tastes receive meaningfully distinct recommendations.
    User A: Toy Story (1)=5, Finding Nemo (6377)=5, The Lion King (364)=4  [Animation / Family]
    User B: The Shining (1258)=5, Alien (1214)=5, Psycho (1219)=4        [Horror / Sci-Fi / Thriller]
    """
    user_a_prefs = {
        "ratings": {1: 5.0, 6377: 5.0, 364: 4.0},
        "watchlist": [],
        "hidden_ids": [],
    }
    user_b_prefs = {
        "ratings": {1258: 5.0, 1214: 5.0, 1219: 4.0},
        "watchlist": [],
        "hidden_ids": [],
    }

    recs_a = RecommendationService.get_recommended_for_user(user_a_prefs, limit=12)
    recs_b = RecommendationService.get_recommended_for_user(user_b_prefs, limit=12)

    ids_a = set(m["id"] for m in recs_a)
    ids_b = set(m["id"] for m in recs_b)

    assert len(ids_a) == 12
    assert len(ids_b) == 12

    # Overlap between Animation-lover and Horror-lover must be minimal (at most 2 out of 12)
    overlap = len(ids_a & ids_b)
    assert overlap <= 2, f"Too much overlap between User A and User B: {overlap}/12 (IDs: {ids_a & ids_b})"

    # User A recommendations should heavily feature Animation or Children or Adventure
    genres_a = [g for m in recs_a for g in m.get("genres", [])]
    assert any(g in ["Animation", "Children"] for g in genres_a)

    # User B recommendations should heavily feature Horror, Sci-Fi, or Thriller
    genres_b = [g for m in recs_b for g in m.get("genres", [])]
    assert any(g in ["Horror", "Sci-Fi", "Thriller"] for g in genres_b)


def test_no_user_state_fallback_does_not_crash():
    """Requirement 12: None or empty dictionary inputs do not raise unhandled exceptions."""
    recs_none = RecommendationService.get_recommended_for_user(None, limit=5)
    assert len(recs_none) == 5

    recs_empty = RecommendationService.get_recommended_for_user({}, limit=5)
    assert len(recs_empty) == 5


def test_nonexistent_catalog_ids_do_not_crash():
    """Requirement 13: Ratings or exclusions for IDs not in catalog are safely handled."""
    crazy_prefs = {
        "ratings": {99999999: 5.0, -1: 3.0, 1: 5.0},
        "watchlist": [88888888],
        "hidden_ids": [77777777],
    }
    recs = RecommendationService.get_recommended_for_user(crazy_prefs, limit=6)
    assert len(recs) == 6
    # Valid ID 1 is rated so must be excluded
    rec_ids = [m["id"] for m in recs]
    assert 1 not in rec_ids


def test_duplicate_and_string_ratings_handled():
    """Requirement 14: String keys from JSON persistence are properly normalized and parsed."""
    str_prefs = {
        "ratings": {"1": "5.0", "318": 4.0},
        "watchlist": ["260", 480],
        "hidden_ids": ["296"],
    }
    recs = RecommendationService.get_recommended_for_user(str_prefs, limit=8)
    assert len(recs) == 8
    rec_ids = [m["id"] for m in recs]
    assert 1 not in rec_ids
    assert 318 not in rec_ids
    assert 260 not in rec_ids
    assert 480 not in rec_ids
    assert 296 not in rec_ids


def test_recommendation_count_remains_correct_after_heavy_filtering():
    """Requirement 15: Output count meets requested limit even when many top candidates are excluded."""
    # Exclude 30 popular movies
    excluded = list(range(1, 31))
    prefs = {"ratings": {100: 5.0}, "watchlist": [], "hidden_ids": excluded}
    recs = RecommendationService.get_recommended_for_user(prefs, limit=12)
    assert len(recs) == 12
    rec_ids = set(m["id"] for m in recs)
    assert rec_ids.isdisjoint(set(excluded))


def test_persisted_user_data_works_after_fresh_initialization(tmp_path):
    """Requirement 10: Persisted user data loaded from disk generates personalized recommendations."""
    temp_file = tmp_path / "test_user_data.json"
    user_state = {
        "ratings": {1: 5.0, 3114: 4.5},
        "watchlist": [260],
        "not_interested": [296],
        "user_profile": {}
    }
    # Save to disk
    assert save(user_state, path=temp_file) is True

    # Fresh reload from disk
    loaded = load(path=temp_file)
    assert 1 in loaded["ratings"]
    assert 260 in loaded["watchlist"]
    assert 296 in loaded["not_interested"]

    # Generate recommendations from loaded state
    prefs = {
        "ratings": loaded["ratings"],
        "watchlist": loaded["watchlist"],
        "hidden_ids": list(loaded["not_interested"])
    }
    recs = RecommendationService.get_recommended_for_user(prefs, limit=10)
    assert len(recs) == 10
    rec_ids = [m["id"] for m in recs]

    # Exclusions must hold
    assert 1 not in rec_ids
    assert 3114 not in rec_ids
    assert 260 not in rec_ids
    assert 296 not in rec_ids

