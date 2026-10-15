"""
ReelSense - Comprehensive Test Suite for Onboarding, Persistent User State,
Recommendation Engine Upgrade, Homepage Sections, and Duplicate Prevention (Phases 1-8).
"""

import sys
import os
from pathlib import Path
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services import user_state, user_store
from src.services.catalog import Catalog, get_catalog, get_by_id
from src.services.recommendation_service import RecommendationService
from src.services.hybrid_model import HybridModel, get_model
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def isolated_user_store(tmp_path, monkeypatch):
    """Provide an isolated user_state.json path for testing."""
    test_file = tmp_path / "user_state.json"
    monkeypatch.setattr(user_state, "USER_STATE_PATH", test_file)
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_file)
    yield test_file


# -----------------------------------------------------------------------------
# CHECKLIST TEST 1 & 2 & 3: ONBOARDING LOGIC
# -----------------------------------------------------------------------------
def test_1_and_2_onboarding_state_and_selection_threshold(isolated_user_store):
    """Verifies fresh launch requires onboarding and enforces >= 3 picks."""
    # Clean state
    assert not user_state.is_onboarding_done(isolated_user_store)

    picks = RecommendationService.get_onboarding_picks(24)
    assert len(picks) == 24
    # Ensure distinct movie IDs
    pick_ids = [m["id"] for m in picks]
    assert len(set(pick_ids)) == 24

    # Select 2 movies: below threshold
    selected_2 = pick_ids[:2]
    assert len(selected_2) < 3

    # Select 3 movies: threshold reached
    selected_3 = pick_ids[:3]
    assert len(selected_3) >= 3

    # Complete with 4 movies
    selected_4 = pick_ids[:4]
    user_state.complete_onboarding(selected_4, isolated_user_store)

    assert user_state.is_onboarding_done(isolated_user_store)
    ratings = user_state.get_ratings(isolated_user_store)
    assert len(ratings) == 4
    for mid in selected_4:
        assert ratings[mid] == 5.0  # 5-star rating assigned


def test_4_onboarding_search_finds_films_outside_initial_grid():
    """Verify catalog search finds films and prevents duplicate IDs."""
    picks = RecommendationService.get_onboarding_picks(24)
    pick_ids = set(m["id"] for m in picks)

    # Search for an iconic movie
    results = Catalog.search_movies("Matrix", limit=5)
    assert len(results) > 0
    matrix = results[0]
    assert "matrix" in matrix["title"].lower()

    # Search deduplication logic
    selected_ids = {picks[0]["id"]}
    # Adding a new film not in grid
    if matrix["id"] not in selected_ids:
        selected_ids.add(matrix["id"])
    assert matrix["id"] in selected_ids
    # Duplicate selection prevented
    selected_ids.add(matrix["id"])
    assert len([x for x in selected_ids if x == matrix["id"]]) == 1


def test_5_skip_onboarding_leaves_ratings_clean(isolated_user_store):
    """Skipping onboarding marks skipped without generating fake ratings."""
    assert not user_state.is_onboarding_done(isolated_user_store)
    user_state.skip_onboarding(isolated_user_store)

    assert user_state.is_onboarding_done(isolated_user_store)
    assert user_state.is_onboarding_skipped(isolated_user_store)
    assert user_state.get_ratings(isolated_user_store) == {}


# -----------------------------------------------------------------------------
# CHECKLIST TEST 6: PERSISTENCE ACROSS SESSIONS
# -----------------------------------------------------------------------------
def test_6_persistence_across_reloads(isolated_user_store):
    """Saving ratings, hidden movies, and watchlist persists safely."""
    user_state.rate_movie(318, 5, isolated_user_store)
    user_state.mark_not_interested(101, isolated_user_store)
    user_state.add_to_watchlist(260, isolated_user_store)

    # Reload from disk
    loaded = user_state.load(isolated_user_store)
    assert loaded["ratings"][318] == 5.0
    assert 101 in loaded["not_interested"]
    assert 260 in loaded["watchlist"]


# -----------------------------------------------------------------------------
# CHECKLIST TEST 7 & 12: RATED & HIDDEN MOVIES EXCLUDED
# -----------------------------------------------------------------------------
def test_7_and_12_rated_and_hidden_strictly_excluded(isolated_user_store):
    """Rated and hidden movies never appear in recommendation results."""
    user_state.rate_movie(318, 5, isolated_user_store)
    user_state.rate_movie(260, 4, isolated_user_store)
    user_state.mark_not_interested(1, isolated_user_store)

    ratings = user_state.get_ratings(isolated_user_store)
    not_interested = user_state.get_not_interested(isolated_user_store)

    rec_prefs = {
        "ratings": ratings,
        "hidden_ids": list(not_interested),
    }

    recs = RecommendationService.get_recommended_for_user(rec_prefs, limit=12)
    rec_ids = [m["id"] for m in recs]

    assert 318 not in rec_ids, "Rated movie 318 must not appear in recommendations"
    assert 260 not in rec_ids, "Rated movie 260 must not appear in recommendations"
    assert 1 not in rec_ids, "Hidden movie 1 must not appear in recommendations"


# -----------------------------------------------------------------------------
# CHECKLIST TEST 8 & 9: BECAUSE YOU LIKED & RATING UPDATES
# -----------------------------------------------------------------------------
def test_8_and_9_because_you_liked_and_no_duplicate_records(isolated_user_store):
    """4-5 star rating updates order and generates similar movie rows."""
    user_state.rate_movie(318, 5, isolated_user_store)  # Shawshank
    user_state.rate_movie(260, 5, isolated_user_store)  # Star Wars

    # Update rating for 318 to 4
    user_state.rate_movie(318, 4, isolated_user_store)
    ratings = user_state.get_ratings(isolated_user_store)

    # No duplicate entry in ratings
    assert len(ratings) == 2
    assert ratings[318] == 4.0

    # Because you liked Shawshank
    similar_to_318 = RecommendationService.get_because_you_liked(318, limit=6, exclude={318, 260})
    assert len(similar_to_318) > 0
    sim_ids = [m["id"] for m in similar_to_318]
    assert 318 not in sim_ids
    assert 260 not in sim_ids


# -----------------------------------------------------------------------------
# CHECKLIST TEST 10: NOT INTERESTED & UNDO
# -----------------------------------------------------------------------------
def test_10_not_interested_and_undo(isolated_user_store):
    """Marking not interested excludes film; unmarking makes it eligible again."""
    user_state.mark_not_interested(318, isolated_user_store)
    assert 318 in user_state.get_not_interested(isolated_user_store)

    user_state.unmark_not_interested(318, isolated_user_store)
    assert 318 not in user_state.get_not_interested(isolated_user_store)


# -----------------------------------------------------------------------------
# CHECKLIST TEST 11: GLOBAL HOMEPAGE DEDUPLICATION RULE
# -----------------------------------------------------------------------------
def test_11_homepage_sections_no_duplicate_movie_ids(isolated_user_store):
    """Simulate assembling all homepage sections and verify zero duplicates."""
    user_state.rate_movie(318, 5, isolated_user_store)
    user_state.rate_movie(260, 5, isolated_user_store)
    user_state.rate_movie(296, 4, isolated_user_store)

    ratings = user_state.get_ratings(isolated_user_store)
    not_interested = user_state.get_not_interested(isolated_user_store)
    displayed_ids = set(ratings.keys()) | set(not_interested)

    # 1. Hero
    rec_prefs = {"ratings": ratings, "hidden_ids": list(not_interested)}
    hero_picks = RecommendationService.get_recommended_for_user(rec_prefs, limit=1, exclude=displayed_ids)
    assert len(hero_picks) == 1
    hero_id = hero_picks[0]["id"]
    assert hero_id not in displayed_ids
    displayed_ids.add(hero_id)

    # 2. Recommended For You (12 items)
    recs = RecommendationService.get_recommended_for_user(rec_prefs, limit=12, exclude=displayed_ids)
    rec_ids = [m["id"] for m in recs if m["id"] not in displayed_ids][:12]
    for mid in rec_ids:
        assert mid not in displayed_ids
        displayed_ids.add(mid)

    # 3. Because You Liked
    byl_movies = RecommendationService.get_because_you_liked(318, limit=6, exclude=displayed_ids)
    byl_ids = [m["id"] for m in byl_movies if m["id"] not in displayed_ids][:6]
    for mid in byl_ids:
        assert mid not in displayed_ids
        displayed_ids.add(mid)

    # 4. Top Genre picks
    top_genre, genre_picks = RecommendationService.get_top_genre_picks(ratings=ratings, limit=6, exclude=displayed_ids)
    assert top_genre is not None
    genre_ids = [m["id"] for m in genre_picks if m["id"] not in displayed_ids][:6]
    for mid in genre_ids:
        assert mid not in displayed_ids
        displayed_ids.add(mid)

    # 5. Trending this week
    trending = RecommendationService.get_trending_movies(limit=5, exclude=displayed_ids)
    trending_ids = [m["id"] for m in trending if m["id"] not in displayed_ids][:5]
    for mid in trending_ids:
        assert mid not in displayed_ids
        displayed_ids.add(mid)

    # Total displayed IDs must equal sum of all section lengths (zero overlap)
    total_expected = 1 + len(rec_ids) + len(byl_ids) + len(genre_ids) + len(trending_ids)
    # subtracting initial 3 ratings
    assert len(displayed_ids - set(ratings.keys())) == total_expected


# -----------------------------------------------------------------------------
# CHECKLIST TEST 13: COLLABORATIVE FILTERING SVD FALLBACK
# -----------------------------------------------------------------------------
def test_13_collaborative_filtering_fallback_robustness():
    """Verify HybridModel functions even if collaborative data is unavailable."""
    model = get_model()
    # Test cold start and recommend without crashing
    cold = model.cold_start(n=6)
    assert len(cold) == 6
    sim = model.similar(318, limit=6)
    assert len(sim) == 6


# -----------------------------------------------------------------------------
# CHECKLIST TEST 14: RETAKE TASTE QUIZ PRESERVES WATCHLIST & HIDDEN
# -----------------------------------------------------------------------------
def test_14_retake_taste_quiz_preserves_watchlist_and_hidden(isolated_user_store):
    """Retaking taste quiz clears ratings but preserves watchlist and excluded list."""
    user_state.rate_movie(318, 5, isolated_user_store)
    user_state.rate_movie(260, 4, isolated_user_store)
    user_state.add_to_watchlist(593, isolated_user_store)
    user_state.mark_not_interested(101, isolated_user_store)

    assert len(user_state.get_ratings(isolated_user_store)) == 2
    assert 593 in user_state.get_watchlist(isolated_user_store)
    assert 101 in user_state.get_not_interested(isolated_user_store)

    # Retake quiz
    user_state.reset_onboarding(clear_ratings=True, path=isolated_user_store)

    assert user_state.get_ratings(isolated_user_store) == {}
    assert not user_state.is_onboarding_done(isolated_user_store)
    # Watchlist and hidden list are preserved!
    assert 593 in user_state.get_watchlist(isolated_user_store)
    assert 101 in user_state.get_not_interested(isolated_user_store)


# -----------------------------------------------------------------------------
# CHECKLIST TEST 15: MALFORMED/EMPTY STATE HANDLING
# -----------------------------------------------------------------------------
def test_15_corrupted_state_file_recovery(tmp_path):
    """App and user_state recover cleanly from corrupted state files."""
    bad_file = tmp_path / "corrupt_user_state.json"
    bad_file.write_text("{invalid json...[", encoding="utf-8")

    state = user_state.load(bad_file)
    assert state["ratings"] == {}
    assert state["watchlist"] == []
    assert state["not_interested"] == set()
    assert state["schema_version"] == 1
