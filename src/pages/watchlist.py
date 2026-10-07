"""
ReelSense - My Watchlist Page Module
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.services import user_store
from src.components.movie_card import render_movie_card

def render_watchlist_page():
    st.markdown(
        textwrap.dedent("""
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">bookmark</span>
                <span>Personal Vault Screening Queue</span>
            </div>
            <h1 class="mood-page-title">
                My <span>Watchlist</span>
            </h1>
            <p class="mood-page-sub">
                Your private theater collection of calibrated cinematic experiences, saved rails, and bookmarked masterworks.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    watchlist_ids = st.session_state.get("watchlist", [])
    saved_movies = [MovieService.get_movie_by_id(mid) for mid in watchlist_ids if MovieService.get_movie_by_id(mid)]

    if not saved_movies:
        st.markdown(
            textwrap.dedent("""
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 3.5rem 1rem; text-align: center; margin-top: 1.5rem;">
                <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🔖</div>
                <h3 style="font-size: 1.3rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">Your Watchlist is Empty</h3>
                <p style="font-size: 0.9rem; color: #A0A0A0; margin-bottom: 1.5rem; max-width: 450px; margin-left: auto; margin-right: auto;">
                    Bookmark movies across Home, Discover, and Mood Explorer to save them directly to your personal watchlist.
                </p>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        col_c, _ = st.columns([3, 7])
        with col_c:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            if st.button("🔍 Discover Movies Now", key="wl_empty_disc_btn"):
                st.session_state.current_page = "discover"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # Controls Header (Count & Sort)
    col_count, col_sort = st.columns([6, 4])
    with col_count:
        st.markdown(f"<span style='font-size: 1.05rem; font-weight: 700; color: #F4EBDD;'>{len(saved_movies)} Saved Movies</span>", unsafe_allow_html=True)

    with col_sort:
        sort_choice = st.selectbox(
            "Sort Watchlist",
            options=["Title (A-Z)", "Rating (High to Low)", "Release Year (Newest)"],
            label_visibility="collapsed",
            key="wl_sort_select"
        )

    if sort_choice == "Title (A-Z)":
        saved_movies.sort(key=lambda x: x["title"])
    elif sort_choice == "Rating (High to Low)":
        saved_movies.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_choice == "Release Year (Newest)":
        saved_movies.sort(key=lambda x: x["release_year"], reverse=True)

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    n_cols = 4
    for i in range(0, len(saved_movies), n_cols):
        row_m = saved_movies[i : i + n_cols]
        cols = st.columns(n_cols)
        for j, movie in enumerate(row_m):
            with cols[j]:
                render_movie_card(movie, key_prefix=f"wl_grid_{movie['id']}")
                if st.button("🗑️ Remove", key=f"wl_remove_{movie['id']}"):
                    st.session_state.watchlist.remove(movie["id"])
                    user_store.save_watchlist(st.session_state.watchlist)
                    st.toast(f"Removed {movie['title']} from Watchlist", icon="🗑️")
                    st.rerun()
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
