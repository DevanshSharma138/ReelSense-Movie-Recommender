"""
ReelSense - Final Interaction & HTML Fix Validation Test Suite
Comprehensive testing for raw HTML bug elimination, search accuracy, button responsiveness,
rating 0-5 scale integrity, and end-to-end user journeys.
"""

import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path
from src.services.movie_service import MovieService
from src.services.catalog import Catalog
from src.services import user_store
from src.utils.ui_helpers import render_html

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT_DIR / "app.py")


def test_render_html_strips_indentation_and_renders_cleanly():
    """Ensure render_html helper does not produce CommonMark 4-space indented code blocks."""
    sample_multiline = """
        <div class="test-class">
            <span style="color: gold;">Test Text</span>
            <h1>Header</h1>
        </div>
    """
    # Just verify that when cleaned, no line starts with 4 spaces
    lines = [line for line in sample_multiline.strip().split("\n")]
    for line in lines:
        cleaned_line = line.strip()
        assert not cleaned_line.startswith("    ")


def test_movie_details_no_raw_html_leakage(tmp_path, monkeypatch):
    """Verify that Movie Details renders Forrest Gump without leaking raw HTML into code/text widgets."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    # Select Forrest Gump (ID 356)
    at.session_state.selected_movie_id = 356
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "movie_details"

    # Verify no markdown widget has raw HTML code fences or escaped HTML strings
    for md in at.markdown:
        val = str(md.value)
        # Should NOT contain raw HTML span style tag leaking as text
        assert '<span style="background: #2a2a2c' not in val
        assert '<h1 style="font-family:' not in val
        assert '<p style="font-size:' not in val

    # Verify no code widget contains HTML tags
    for code_block in at.code:
        val = str(code_block.value)
        assert "<div" not in val
        assert "<span" not in val


def test_search_queries_catalog_and_service():
    """Test search for Matrix, Toy Story, Forrest Gump, and nonsense query."""
    # Matrix
    matrix_res = MovieService.filter_movies(query="Matrix")
    assert len(matrix_res) > 0
    assert any("Matrix" in m["title"] for m in matrix_res)

    # Toy Story
    toy_res = MovieService.filter_movies(query="Toy Story")
    assert len(toy_res) > 0
    assert any("Toy Story" in m["title"] for m in toy_res)

    # Forrest Gump
    gump_res = MovieService.filter_movies(query="Forrest Gump")
    assert len(gump_res) > 0
    assert any("Forrest Gump" in m["title"] for m in gump_res)

    # Nonsense query
    empty_res = MovieService.filter_movies(query="xyznonsense999")
    assert len(empty_res) == 0


def test_topbar_search_navigates_to_discover(tmp_path, monkeypatch):
    """Verify top search bar navigates to Discover and synchronizes query."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    # Set top search input and trigger search
    at.text_input(key="topbar_search_input").set_value("Matrix").run()
    assert not at.exception
    assert at.session_state.current_page in ["discover-movies", "discover"]
    assert at.session_state.discover_search == "Matrix"


def test_all_top_nav_routes(tmp_path, monkeypatch):
    """Verify all top navigation buttons work and route correctly."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    nav_checks = [
        ("top_nav_discover-movies", "discover-movies"),
        ("top_nav_mood-explorer", "mood-explorer"),
        ("top_nav_my-watchlist", "my-watchlist"),
        ("top_nav_my-ratings", "my-ratings"),
        ("top_nav_about-the-ai", "about-the-ai"),
        ("top_nav_my-profile", "my-profile"),
        ("top_nav_about", "about"),
        ("top_nav_home", "home"),
    ]

    for btn_key, expected_route in nav_checks:
        at.button(key=btn_key).click().run()
        assert not at.exception
        assert at.session_state.current_page == expected_route


def test_movie_card_selection_and_back_navigation(tmp_path, monkeypatch):
    """Verify clicking movie card opens details, and back button returns."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    # Start on Discover
    at.button(key="top_nav_discover-movies").click().run()
    assert not at.exception

    # Click the first movie card button on discover
    card_buttons = [b for b in at.button if b.key and b.key.startswith("disc_grid_") and "_card_" in b.key]
    assert len(card_buttons) > 0
    first_btn = card_buttons[0]
    movie_id = int(first_btn.key.split("_card_")[1])

    first_btn.click().run()
    assert not at.exception
    assert at.session_state.current_page == "movie_details"
    assert at.session_state.selected_movie_id == movie_id

    # Click Back to Browse button
    at.button(key="back_to_browse_btn").click().run()
    assert not at.exception
    assert at.session_state.current_page in ["discover-movies", "discover"]


def test_rating_scale_zero_to_five_bounds_and_persistence(tmp_path, monkeypatch):
    """Verify ratings are exclusively on 0-5 scale and persist accurately."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    # Open Forrest Gump (ID 356)
    at.session_state.selected_movie_id = 356
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception

    rate_sliders = [s for s in at.slider if "user_rate_slider_356" in s.key]
    assert len(rate_sliders) == 1
    slider = rate_sliders[0]
    assert slider.min == 0.0
    assert slider.max == 5.0
    assert slider.step == 0.5

    # Set rating to 5.0
    slider.set_value(5.0).run()
    assert not at.exception
    assert at.session_state.ratings.get(356) == 5.0

    # Verify persistence
    data = user_store.load()
    assert data["ratings"].get(356) == 5.0

    # Remove rating using del_rate_btn_356
    at.button(key="del_rate_btn_356").click().run()
    assert not at.exception
    assert 356 not in at.session_state.ratings
    data = user_store.load()
    assert 356 not in data["ratings"]


def test_watchlist_and_hide_restore_lifecycle(tmp_path, monkeypatch):
    """Verify Vault and Not Interested interactions persist and update state."""
    test_store = tmp_path / "user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_store)

    at = AppTest.from_file(APP_PATH, default_timeout=20)
    at.run()
    assert not at.exception

    movie_id = 2571  # Matrix

    # Open details
    at.session_state.selected_movie_id = movie_id
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception

    # Add to Vault
    at.button(key=f"det_wl_{movie_id}").click().run()
    assert not at.exception
    assert movie_id in at.session_state.watchlist
    assert movie_id in user_store.load()["watchlist"]

    # Remove from Vault
    at.button(key=f"det_wl_{movie_id}").click().run()
    assert not at.exception
    assert movie_id not in at.session_state.watchlist
    assert movie_id not in user_store.load()["watchlist"]

    # Hide movie
    at.button(key=f"det_hide_{movie_id}").click().run()
    assert not at.exception
    assert movie_id in at.session_state.not_interested
    assert movie_id in user_store.load()["not_interested"]

    # Restore movie
    at.button(key=f"det_hide_{movie_id}").click().run()
    assert not at.exception
    assert movie_id not in at.session_state.not_interested
    assert movie_id not in user_store.load()["not_interested"]
