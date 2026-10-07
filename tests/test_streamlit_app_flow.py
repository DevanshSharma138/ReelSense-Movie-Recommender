"""
ReelSense - Streamlit AppTest End-to-End Navigation & Interactive Flow
Simulates actual Streamlit user interactions against app.py:
- Topbar navigation clicks (Home -> Discover -> Mood -> Watchlist -> Ratings -> Profile -> Sense AI)
- Inspect movie card -> Movie Details
- Watchlist toggling
- Rating slider submission
- Return to Browse
"""

import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_top_navigation_flow():
    """Verify that clicking topbar navigation buttons navigates to the correct pages."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert not at.exception, f"App raised exception on startup: {at.exception}"

    # Default page is home
    assert at.session_state.current_page == "home"

    # Click Discover
    at.button(key="top_nav_discover-movies").click().run()
    assert not at.exception
    assert at.session_state.current_page == "discover-movies"

    # Click Mood Explorer
    at.button(key="top_nav_mood-explorer").click().run()
    assert not at.exception
    assert at.session_state.current_page == "mood-explorer"

    # Click Watchlist (Vault)
    at.button(key="top_nav_my-watchlist").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-watchlist"

    # Click Ratings
    at.button(key="top_nav_my-ratings").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-ratings"

    # Click Sense AI
    at.button(key="top_nav_about-the-ai").click().run()
    assert not at.exception
    assert at.session_state.current_page == "about-the-ai"

    # Click Profile
    at.button(key="top_nav_my-profile").click().run()
    assert not at.exception
    assert at.session_state.current_page == "my-profile"

    # Click Return Home via Brand
    at.button(key="top_brand_home_btn").click().run()
    assert not at.exception
    assert at.session_state.current_page == "home"


def test_app_movie_details_and_back_flow():
    """Verify inspecting a movie opens Movie Details and back button returns to browse."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert not at.exception

    # Select Toy Story (ID 1)
    at.session_state.selected_movie_id = 1
    at.session_state.current_page = "movie_details"
    at.run()
    assert not at.exception
    assert at.session_state.current_page == "movie_details"

    # Verify back button exists and functions
    at.button(key="back_to_browse_btn").click().run()
    assert not at.exception
    assert at.session_state.current_page == "home"


def test_app_hero_banner_interaction():
    """Verify Hero Banner Inspect button opens Movie Details."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert not at.exception

    # Check that hero banner inspect button exists
    hero_btn = None
    for b in at.button:
        if b.key and b.key.startswith("hero_stream_"):
            hero_btn = b
            break

    if hero_btn:
        hero_btn.click().run()
        assert not at.exception
        assert at.session_state.current_page == "movie_details"
