"""
ReelSense - Error and Empty States Regression Test Suite (Phase 4 Task 5)
Verifies resilience across:
1. Empty ratings state
2. Empty watchlist state
3. Empty exclusions state
4. Missing / invalid movie ID lookup
5. Missing or corrupted user_data.json recovery
6. No-results search query handling
"""

import json
import pytest
from src.services import user_store
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService


def test_invalid_movie_id_lookup():
    # ID not in catalog
    invalid_movie = MovieService.get_movie_by_id(99999999)
    assert invalid_movie is None


def test_empty_search_and_no_match_filtering():
    # Query with no matches
    results = MovieService.filter_movies(query="xyznonexistentfilmtag12345")
    assert results == []

    # Filter with impossible rating
    results_high = MovieService.filter_movies(min_rating=10.5)
    assert results_high == []


def test_corrupted_user_data_recovery(tmp_path):
    bad_file = tmp_path / "user_data.json"
    bad_file.write_text("{corrupt: json! broken...", encoding="utf-8")

    # user_store.load must not crash and must return clean default structure
    recovered = user_store.load(path=bad_file)
    assert isinstance(recovered, dict)
    assert recovered["ratings"] == {}
    assert recovered["watchlist"] == []
    assert recovered["not_interested"] == set()
    assert "user_profile" in recovered


def test_missing_user_data_recovery(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    state = user_store.load(path=missing_file)
    assert state["ratings"] == {}
    assert state["watchlist"] == []
    assert state["not_interested"] == set()


def test_empty_state_recommendations():
    # Empty preferences must cleanly provide cold-start recommendations
    recs = RecommendationService.get_recommended_for_user({}, limit=6)
    assert len(recs) == 6
    assert all("id" in m and "title" in m for m in recs)

    mode = RecommendationService.get_recommendation_mode({})
    assert mode == "cold_start"
