"""
ReelSense - AI-Powered Movie Discovery & Recommendation Platform
Main Entry Point (app.py)
"""

import os
import streamlit as st
from src.config import APP_NAME, APP_TAGLINE, DEFAULT_USER
from src.services import user_store
from src.components.sidebar import render_sidebar
from src.components.topbar import render_topbar

from src.pages.home import render_home_page
from src.pages.sense_ai import render_sense_ai_page
from src.pages.discover import render_discover_page
from src.pages.mood_explorer import render_mood_explorer_page
from src.pages.movie_details import render_movie_details_page
from src.pages.watchlist import render_watchlist_page
from src.pages.ratings import render_ratings_page
from src.pages.profile import render_profile_page
from src.pages.about import render_about_page

# 1. Page Configuration
st.set_page_config(
    page_title=f"{APP_NAME} - {APP_TAGLINE}",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inject Google Fonts & Custom Stylesheet
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True
)
CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        custom_css = f.read()
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# 3. Initialize Session State Variables from UserStore
if "user_store_initialized" not in st.session_state:
    persisted_state = user_store.load()
    st.session_state.ratings = persisted_state["ratings"]
    st.session_state.watchlist = persisted_state["watchlist"]
    st.session_state.not_interested = persisted_state["not_interested"]
    st.session_state.user_profile = persisted_state["user_profile"]
    st.session_state.user_store_initialized = True

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "ratings" not in st.session_state:
    st.session_state.ratings = {}

if "not_interested" not in st.session_state:
    st.session_state.not_interested = set()

if "user_profile" not in st.session_state:
    st.session_state.user_profile = DEFAULT_USER.copy()

if "global_search" not in st.session_state:
    st.session_state.global_search = ""

if "discover_search" not in st.session_state:
    st.session_state.discover_search = ""

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

if "selected_mood" not in st.session_state:
    st.session_state.selected_mood = "Mind-blown"

# 4. Global App Layout Shell
render_sidebar()
render_topbar()

# 5. Route to Active Page
active_page = st.session_state.get("current_page", "home")

if active_page in ["home", "home-discover"]:
    render_home_page()
elif active_page in ["discover-movies", "discover", "collections"]:
    render_discover_page()
elif active_page in ["mood-explorer", "mood"]:
    render_mood_explorer_page()
elif active_page in ["my-watchlist", "watchlist"]:
    render_watchlist_page()
elif active_page in ["my-ratings", "ratings"]:
    render_ratings_page()
elif active_page in ["about-the-ai", "sense_ai"]:
    render_sense_ai_page()
elif active_page in ["about", "architecture", "capstone"]:
    render_about_page()
elif active_page in ["my-profile", "profile", "settings"]:
    render_profile_page()
elif active_page == "movie_details":
    render_movie_details_page()
else:
    render_home_page()
