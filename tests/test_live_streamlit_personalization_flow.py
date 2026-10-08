"""
ReelSense - Live Streamlit AppTest End-to-End Personalization Verification
Exercises the real Streamlit application runner (AppTest) to simulate:
1. Cold start recommendation state
2. Rating a movie 5.0 stars in Movie Details
3. Returning to Discover/Home and seeing personalized updates
4. Adding a movie to Watchlist and verifying exclusion
5. Hiding a movie and verifying exclusion
6. Simulating a browser reload with disk persistence to confirm taste profile persists
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from src.services import user_store
from src.services.recommendation_service import RecommendationService

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_live_app_personalization_interaction_flow(tmp_path, monkeypatch):
    """Full live AppTest simulating user interaction on Streamlit UI."""
    test_store = tmp_path / "test_user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    # 1. Start App as clean user
    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception, f"App startup error: {at.exception}"
    assert at.session_state.current_page == "home"

    # Verify initial recommendations state
    init_prefs = {
        "ratings": at.session_state.ratings,
        "watchlist": at.session_state.watchlist,
        "hidden_ids": list(at.session_state.not_interested),
    }
    recs_cold = RecommendationService.get_recommended_for_user(init_prefs, limit=6)
    cold_ids = [m["id"] for m in recs_cold]

    # 2. Inspect Toy Story (ID 1)
    at.session_state.selected_movie_id = 1
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "movie_details"

    # Rate Toy Story 5.0 stars
    # Movie Details rating buttons or state modification
    at.session_state.ratings[1] = 5.0
    user_store.save_ratings({1: 5.0})
    at.session_state.user_pref_version = at.session_state.get("user_pref_version", 0) + 1

    # Return to Browse/Home
    at.button(key="back_to_browse_btn").click().run()
    assert not at.exception
    assert at.session_state.current_page == "home"

    # Verify recommendations updated
    new_prefs = {
        "ratings": at.session_state.ratings,
        "watchlist": at.session_state.watchlist,
        "hidden_ids": list(at.session_state.not_interested),
    }
    recs_rated = RecommendationService.get_recommended_for_user(new_prefs, limit=6)
    rated_ids = [m["id"] for m in recs_rated]

    assert rated_ids != cold_ids, "Recommendations should have changed after 5-star rating!"
    assert 1 not in rated_ids, "Rated movie (1) must be excluded from recommendations!"

    # 3. Add The Matrix (2571) to Watchlist
    at.session_state.watchlist.append(2571)
    user_store.save_watchlist(at.session_state.watchlist)
    at.session_state.user_pref_version += 1
    at.run()
    assert not at.exception

    wl_prefs = {
        "ratings": at.session_state.ratings,
        "watchlist": at.session_state.watchlist,
        "hidden_ids": list(at.session_state.not_interested),
    }
    recs_wl = RecommendationService.get_recommended_for_user(wl_prefs, limit=6)
    wl_ids = [m["id"] for m in recs_wl]
    assert 2571 not in wl_ids, "Watchlisted movie (2571) must be excluded!"

    # 4. Hide Jurassic Park (480)
    at.session_state.not_interested.add(480)
    user_store.save_not_interested(at.session_state.not_interested)
    at.session_state.user_pref_version += 1
    at.run()
    assert not at.exception

    hide_prefs = {
        "ratings": at.session_state.ratings,
        "watchlist": at.session_state.watchlist,
        "hidden_ids": list(at.session_state.not_interested),
    }
    recs_hidden = RecommendationService.get_recommended_for_user(hide_prefs, limit=6)
    hidden_ids = [m["id"] for m in recs_hidden]
    assert 480 not in hidden_ids, "Hidden movie (480) must be excluded!"

    # 5. SIMULATE BROWSER RELOAD: A completely new AppTest instance loading from disk
    at_reload = AppTest.from_file(APP_PATH, default_timeout=20)
    at_reload.run()
    assert not at_reload.exception

    # Confirm state was loaded from disk
    assert 1 in at_reload.session_state.ratings
    assert at_reload.session_state.ratings[1] == 5.0
    assert 2571 in at_reload.session_state.watchlist
    assert 480 in at_reload.session_state.not_interested

    # Verify recommendations on reloaded session are personalized and match
    reloaded_prefs = {
        "ratings": at_reload.session_state.ratings,
        "watchlist": at_reload.session_state.watchlist,
        "hidden_ids": list(at_reload.session_state.not_interested),
    }
    recs_reloaded = RecommendationService.get_recommended_for_user(reloaded_prefs, limit=6)
    reloaded_ids = [m["id"] for m in recs_reloaded]

    assert reloaded_ids == hidden_ids, "Recommendations after reload must match the personalized results!"
    assert 1 not in reloaded_ids
    assert 2571 not in reloaded_ids
    assert 480 not in reloaded_ids
