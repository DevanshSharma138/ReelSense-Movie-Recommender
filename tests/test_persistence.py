"""
ReelSense - Persistence Verification Suite (Phase 2)
Verifies safe JSON persistence, atomic writes, corruption resistance,
and recommendation engine integration across all 10 required test criteria.
"""
import sys
import os
from pathlib import Path
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import DEFAULT_USER
from src.services import user_store
from src.services.recommendation_service import RecommendationService
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def temp_store(tmp_path):
    """Provide a clean temporary JSON store path for isolated persistence tests."""
    return tmp_path / "user_data.json"


def test_1_fresh_state_returns_empty_defaults(temp_store):
    """TEST 1: Fresh state returns empty defaults."""
    assert not temp_store.exists()
    state = user_store.load(temp_store)
    assert state["ratings"] == {}
    assert state["watchlist"] == []
    assert state["not_interested"] == set()
    assert state["user_profile"]["name"] == DEFAULT_USER["name"]
    assert state["user_profile"]["favorite_genres"] == DEFAULT_USER["favorite_genres"]


def test_2_save_single_rating(temp_store):
    """TEST 2: Save a rating -> load -> rating remains (0-5 scale)."""
    ok = user_store.save_ratings({356: 4.5}, path=temp_store)
    assert ok is True
    assert temp_store.exists()

    loaded_ratings = user_store.get_ratings(path=temp_store)
    assert 356 in loaded_ratings
    assert loaded_ratings[356] == 4.5
    # Verify integer key type
    assert isinstance(list(loaded_ratings.keys())[0], int)


def test_3_save_multiple_ratings(temp_store):
    """TEST 3: Save multiple ratings -> load -> all remain (0-5 scale)."""
    test_ratings = {356: 4.5, 318: 4.8, 296: 4.0, 593: 4.2}
    user_store.save_ratings(test_ratings, path=temp_store)

    loaded = user_store.get_ratings(path=temp_store)
    assert len(loaded) == 4
    for mid, score in test_ratings.items():
        assert loaded[mid] == score


def test_4_save_watchlist(temp_store):
    """TEST 4: Save watchlist -> load -> watchlist remains."""
    # Test deduplication and order preservation
    items = [356, 318, 296, 356]
    user_store.save_watchlist(items, path=temp_store)

    loaded = user_store.get_watchlist(path=temp_store)
    assert loaded == [356, 318, 296]
    assert all(isinstance(x, int) for x in loaded)


def test_5_save_not_interested(temp_store):
    """TEST 5: Save not_interested -> load -> values remain."""
    exclusions = {101, 102, 103}
    user_store.save_not_interested(exclusions, path=temp_store)

    loaded = user_store.get_not_interested(path=temp_store)
    assert loaded == exclusions
    assert isinstance(loaded, set)


def test_6_save_profile(temp_store):
    """TEST 6: Save profile -> load -> profile remains (0-5 scale)."""
    custom_profile = {
        "name": "Cinematic Pioneer",
        "favorite_genres": ["Sci-Fi", "Noir", "Thriller"],
        "preferred_language": "French",
        "preferred_era": "2020s & Newer",
        "min_rating_pref": 4.0,
    }
    user_store.save_profile(custom_profile, path=temp_store)

    loaded = user_store.get_profile(path=temp_store)
    assert loaded["name"] == "Cinematic Pioneer"
    assert loaded["favorite_genres"] == ["Sci-Fi", "Noir", "Thriller"]
    assert loaded["preferred_language"] == "French"
    assert loaded["min_rating_pref"] == 4.0


def test_7_malformed_json_fallback(temp_store):
    """TEST 7: Malformed JSON does not crash the application."""
    # Test corrupt JSON syntax
    temp_store.write_text("{ unclosed bad json [!@#", encoding="utf-8")
    loaded = user_store.load(path=temp_store)
    assert loaded["ratings"] == {}
    assert loaded["watchlist"] == []
    assert loaded["not_interested"] == set()

    # Test empty file
    temp_store.write_text("", encoding="utf-8")
    loaded_empty = user_store.load(path=temp_store)
    assert loaded_empty["ratings"] == {}

    # Test wrong root type (list instead of dict)
    temp_store.write_text("[\"unexpected\", \"list\"]", encoding="utf-8")
    loaded_list = user_store.load(path=temp_store)
    assert loaded_list["ratings"] == {}


def test_8_app_starts_with_no_user_data_json():
    """TEST 8: Application can start with no user_data.json."""
    real_store = user_store.DEFAULT_STORE_PATH
    backup_text = None
    if real_store.exists():
        backup_text = real_store.read_text(encoding="utf-8")
        real_store.unlink()

    try:
        at = AppTest.from_file(APP_PATH)
        at.run(timeout=30)
        assert not at.exception, f"App crashed on startup without user_data.json: {at.exception}"
        assert at.session_state["ratings"] == {}
        assert at.session_state["watchlist"] == []
        assert at.session_state["not_interested"] == set()
    finally:
        if backup_text is not None:
            real_store.write_text(backup_text, encoding="utf-8")
        elif real_store.exists():
            real_store.unlink()


def test_9_app_restarts_with_existing_user_data_json():
    """TEST 9: Application can restart with existing user_data.json."""
    real_store = user_store.DEFAULT_STORE_PATH
    backup_text = real_store.read_text(encoding="utf-8") if real_store.exists() else None

    try:
        # Pre-seed persistence
        persisted_data = {
            "ratings": {356: 4.5, 318: 4.0},
            "watchlist": [296, 593],
            "not_interested": {101},
            "user_profile": {"name": "Test Restored User"},
        }
        user_store.save(persisted_data, path=real_store)

        # Run application startup
        at = AppTest.from_file(APP_PATH)
        at.run(timeout=30)
        assert not at.exception, f"App crashed on restart with existing user_data.json: {at.exception}"

        # Verify state was restored into session_state
        assert at.session_state["ratings"] == {356: 4.5, 318: 4.0}
        assert at.session_state["watchlist"] == [296, 593]
        assert at.session_state["not_interested"] == {101}
        assert at.session_state["user_profile"]["name"] == "Test Restored User"
    finally:
        if backup_text is not None:
            real_store.write_text(backup_text, encoding="utf-8")
        elif real_store.exists():
            real_store.unlink()


def test_10_persisted_ratings_activate_hybrid_recommendations():
    """TEST 10: Persisted ratings activate hybrid recommendations when user has enough ratings."""
    real_store = user_store.DEFAULT_STORE_PATH
    backup_text = real_store.read_text(encoding="utf-8") if real_store.exists() else None

    try:
        # Save 3 ratings in persistent storage (0-5 scale)
        three_ratings = {356: 4.5, 318: 4.8, 296: 4.0}
        user_store.save_ratings(three_ratings, path=real_store)

        # Restart application and render Home
        at = AppTest.from_file(APP_PATH)
        at.run(timeout=30)
        assert not at.exception, f"App failed to render with 3 persisted ratings: {at.exception}"

        # Verify session state received the 3 ratings
        assert len(at.session_state["ratings"]) == 3

        # Verify recommendation service activates hybrid mode with explainability
        rec_prefs = {
            "ratings": at.session_state["ratings"],
            "favorite_genres": at.session_state["user_profile"].get("favorite_genres", []),
            "hidden_ids": list(at.session_state["not_interested"]),
        }
        mode = RecommendationService.get_recommendation_mode(rec_prefs)
        assert mode == "hybrid", f"Expected hybrid recommendation mode, got {mode}"

        recs = RecommendationService.get_recommended_for_user(rec_prefs, limit=6)
        assert len(recs) == 6
        assert any(len(m.get("why_recommended", [])) > 0 for m in recs), "Expected why_recommended reasons"
    finally:
        if backup_text is not None:
            real_store.write_text(backup_text, encoding="utf-8")
        elif real_store.exists():
            real_store.unlink()


def test_11_movie_details_interactive_rating_flow():
    """TEST 11: Interactive rating on Movie Details persists to session_state and user_data.json."""
    real_store = user_store.DEFAULT_STORE_PATH
    backup_text = real_store.read_text(encoding="utf-8") if real_store.exists() else None

    try:
        user_store.save({"ratings": {}, "watchlist": [], "not_interested": [], "user_profile": DEFAULT_USER.copy()}, path=real_store)

        at = AppTest.from_file(APP_PATH)
        at.run(timeout=30)
        at.session_state.selected_movie_id = 356
        at.session_state.current_page = "movie_details"
        at.run(timeout=10)

        # Click Like button (det_like_356)
        like_btn = at.button(key="det_like_356")
        assert like_btn is not None
        like_btn.click().run(timeout=10)

        assert at.session_state.ratings.get(356) == 5.0
        persisted = user_store.load(real_store)
        assert persisted["ratings"].get(356) == 5.0

        # Navigate to Taste Hub and check movie is listed
        at.session_state.current_page = "my-ratings"
        at.run(timeout=10)
        assert not at.exception
        assert at.session_state.ratings.get(356) == 5.0
    finally:
        if backup_text is not None:
            real_store.write_text(backup_text, encoding="utf-8")
        elif real_store.exists():
            real_store.unlink()


def test_12_windows_file_lock_resilience(temp_store):
    """TEST 12: Saving handles open file handles without crashing or raising WinError 32."""
    user_store.save({"ratings": {356: 4.0}}, path=temp_store)

    # Open file handle for reading to simulate active file reader / watcher
    with open(temp_store, "r", encoding="utf-8"):
        ok = user_store.save({"ratings": {356: 4.5}}, path=temp_store)
        assert ok is True

    loaded = user_store.load(temp_store)
    assert loaded["ratings"] == {356: 4.5}
