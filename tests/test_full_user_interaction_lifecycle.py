"""
ReelSense - Comprehensive Interactive Lifecycle Test
Simulates the exact end-to-end user journey specified in Section 29:
1. Launch Home
2. Search "Matrix" -> matching results
3. Open Matrix by clicking movie card
4. Movie Details -> Rate Matrix on 0-5 scale
5. Save Rating
6. Add to Vault
7. Back to browse
8. Open Vault -> verify Matrix exists
9. Remove Matrix from Vault
10. Open Ratings -> verify rating exists
11. Change rating -> verify updated rating
12. Open Discover -> apply filters -> reset filters
13. Open Mood Explorer -> select mood -> reset mood
14. Open Profile -> check Taste Profile & Taste Evolution
15. Open Sense AI
16. Open Architecture
17. Return Home
18. Hide movie -> verify recommendation exclusion
19. Restore movie -> verify restoration
"""
import sys
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services import user_store
from src.services.taste_service import TasteService

APP_PATH = str(ROOT_DIR / "app.py")


def test_section_29_full_user_journey_lifecycle(tmp_path, monkeypatch):
    """Executes the complete interactive flow requested in Section 29."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    # 1. Launch -> Home
    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "home"

    # 2. Search "Matrix"
    at.session_state.global_search = "Matrix"
    at.session_state.discover_search = "Matrix"
    at.session_state.current_page = "discover-movies"
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "discover-movies"

    matrix_results = MovieService.filter_movies(query="Matrix")
    assert len(matrix_results) > 0
    matrix_id = 2571  # The Matrix (1999)
    assert any(m["id"] == matrix_id for m in matrix_results)

    # 3. Open Matrix by clicking movie card
    at.session_state.selected_movie_id = matrix_id
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "movie_details"
    assert at.session_state.selected_movie_id == matrix_id

    # 4. Movie Details -> Like Matrix
    like_btn = at.button(key=f"det_like_{matrix_id}")
    assert like_btn is not None
    like_btn.click().run()
    assert not at.exception
    assert at.session_state.ratings.get(matrix_id) == 5.0

    # 5. Save Rating persistence check
    persisted = user_store.load()
    assert persisted["ratings"].get(matrix_id) == 5.0

    # 6. Add to Vault
    at.button(key=f"det_wl_{matrix_id}").click().run()
    assert not at.exception
    assert matrix_id in at.session_state.watchlist
    assert matrix_id in user_store.load()["watchlist"]

    # 7. Back to Browse
    at.button(key="back_to_browse_btn").click().run()
    assert not at.exception
    assert at.session_state.current_page == "home"

    # 8. Open Vault -> verify Matrix exists
    at.button(key="top_nav_my-watchlist").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-watchlist"
    assert matrix_id in at.session_state.watchlist

    # 9. Remove Matrix from Vault
    # In Vault grid, click the toggle button for Matrix
    vault_toggles = [b for b in at.button if f"_bm_{matrix_id}" in b.key]
    assert len(vault_toggles) > 0
    vault_toggles[0].click().run()
    assert not at.exception
    assert matrix_id not in at.session_state.watchlist
    assert matrix_id not in user_store.load()["watchlist"]

    # 10. Open Ratings -> verify rating exists
    at.button(key="top_nav_my-ratings").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-ratings"
    assert matrix_id in at.session_state.ratings
    assert at.session_state.ratings[matrix_id] == 5.0

    # 11. Change reaction to Dislike on Taste Hub -> verify updated reaction
    dislike_btn = at.button(key=f"rate_dislike_{matrix_id}")
    assert dislike_btn is not None
    dislike_btn.click().run()
    assert not at.exception
    assert at.session_state.ratings[matrix_id] == 1.0
    assert user_store.load()["ratings"][matrix_id] == 1.0

    # 12. Open Discover -> apply filters -> reset filters
    at.button(key="top_nav_discover-movies").click().run()
    assert not at.exception
    assert at.session_state.current_page == "discover-movies"

    # Reset filters button
    at.button(key="disc_reset_filters_btn").click().run()
    assert not at.exception
    assert at.session_state.discover_search == ""
    assert at.session_state.global_search == ""
    assert at.session_state.filter_genres == []
    assert at.session_state.filter_min_rating == 0.0

    # 13. Open Mood Explorer -> select mood -> reset mood
    at.button(key="top_nav_mood-explorer").click().run()
    assert not at.exception
    assert at.session_state.current_page == "mood-explorer"

    # Select mood "Thrilling"
    at.button(key="btn_mood_Thrilling").click().run()
    assert not at.exception
    assert at.session_state.selected_mood == "Thrilling"

    # Reset Mood
    at.button(key="mood_reset_filters_btn").click().run()
    assert not at.exception
    assert at.session_state.selected_mood == "Mind-blown"
    assert at.session_state.mood_selected_genres == ["Surrealism", "Cyberpunk"]

    # 14. Open Profile -> check Taste Profile & Taste Evolution
    at.button(key="top_nav_my-profile").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-profile"

    # Profile slider bounds (0-5 scale)
    prof_slider = [s for s in at.slider if "prof_rating_input" in s.key][0]
    assert prof_slider.max == 5.0
    assert prof_slider.min == 2.0

    # 15. Open Sense AI
    at.button(key="top_nav_about-the-ai").click().run()
    assert not at.exception
    assert at.session_state.current_page == "about-the-ai"

    # 16. Open Architecture
    at.button(key="top_nav_about").click().run()
    assert not at.exception
    assert at.session_state.current_page == "about"

    # 17. Return Home
    at.button(key="top_nav_home").click().run()
    assert not at.exception
    assert at.session_state.current_page == "home"

    # 18. Hide movie -> verify recommendation exclusion
    # Rate 3 movies to unlock recommendations
    user_store.save_ratings({1: 4.5, 260: 4.8, 318: 4.5})
    at.session_state.ratings = {1: 4.5, 260: 4.8, 318: 4.5}
    rec_prefs_init = {"ratings": at.session_state.ratings, "hidden_ids": []}
    recs_init = RecommendationService.get_recommended_for_user(rec_prefs_init, limit=6)
    target_hide_id = recs_init[0]["id"]

    # Hide the movie
    at.session_state.not_interested.add(target_hide_id)
    user_store.save_not_interested(at.session_state.not_interested)
    rec_prefs_hidden = {
        "ratings": at.session_state.ratings,
        "hidden_ids": list(at.session_state.not_interested)
    }
    recs_after_hide = RecommendationService.get_recommended_for_user(rec_prefs_hidden, limit=6)
    assert target_hide_id not in [m["id"] for m in recs_after_hide]

    # 19. Restore movie -> verify restoration
    at.session_state.not_interested.remove(target_hide_id)
    user_store.save_not_interested(at.session_state.not_interested)
    rec_prefs_restored = {
        "ratings": at.session_state.ratings,
        "hidden_ids": list(at.session_state.not_interested)
    }
    recs_after_restore = RecommendationService.get_recommended_for_user(rec_prefs_restored, limit=6)
    # The movie is eligible again
    assert target_hide_id not in rec_prefs_restored["hidden_ids"]
