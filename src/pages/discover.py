"""
ReelSense - Discover Page Module
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.components.movie_card import render_movie_card
from src.components.onboarding_banner import render_onboarding_banner

def render_discover_page():
    st.markdown(
        textwrap.dedent("""
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">explore</span>
                <span>Curated Catalogue Discovery</span>
            </div>
            <h1 class="mood-page-title">
                Discover <span>Movies</span>
            </h1>
            <p class="mood-page-sub">
                Explore the complete ReelSense master library. Calibrate by cinematographic genre, release era, director aesthetic, and critical acclaim.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # First-Time User Onboarding Guide
    render_onboarding_banner()

    # Search Bar
    search_query = st.text_input(
        "Search Movies",
        value=st.session_state.get("discover_search", ""),
        placeholder="Search by title, director, cast, or genre...",
        label_visibility="collapsed",
        key="disc_search_input"
    )
    st.session_state.discover_search = search_query

    # Filters Section Collapsible / Expandable Container
    with st.expander("🎛️ Filter & Sort Controls", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        all_genres = MovieService.get_all_genres()
        all_languages = ["All"] + MovieService.get_all_languages()

        with col1:
            selected_genres = st.multiselect(
                "Genres",
                options=all_genres,
                default=[],
                placeholder="Select genres..."
            )

        with col2:
            min_rating = st.slider(
                "Minimum Rating",
                min_value=0.0,
                max_value=10.0,
                value=0.0,
                step=0.5,
                format="⭐ %.1f"
            )

        with col3:
            language = st.selectbox(
                "Language",
                options=all_languages,
                index=0
            )

        with col4:
            sort_by = st.selectbox(
                "Sort By",
                options=[
                    "Rating (High to Low)",
                    "Release Year (Newest First)",
                    "Release Year (Oldest First)",
                    "Title (A-Z)"
                ],
                index=0
            )

        col_year, col_reset = st.columns([3, 1])
        with col_year:
            year_range = st.slider(
                "Release Year Range",
                min_value=1930,
                max_value=2026,
                value=(1930, 2026),
                step=1
            )

        with col_reset:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Reset Filters", key="reset_filters_btn"):
                st.session_state.discover_search = ""
                st.session_state.global_search = ""
                st.rerun()

    # Apply filters using MovieService
    filtered_movies = MovieService.filter_movies(
        query=search_query,
        selected_genres=selected_genres,
        year_range=year_range,
        min_rating=min_rating,
        language=language,
        sort_by=sort_by
    )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Result Header Count
    count = len(filtered_movies)
    st.markdown(
        textwrap.dedent(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;">
            <span style="font-size: 1rem; font-weight: 700; color: var(--text-on-surface);">Showing {count} Curated Titles</span>
            <span style="font-size: 0.8rem; color: var(--text-outline);">Sorted by: {sort_by}</span>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # Display Movie Grid
    if filtered_movies:
        # Display in rows of 4 cards
        n_cols = 4
        for i in range(0, len(filtered_movies), n_cols):
            row_movies = filtered_movies[i : i + n_cols]
            cols = st.columns(n_cols)
            for j, movie in enumerate(row_movies):
                with cols[j]:
                    render_movie_card(movie, key_prefix=f"disc_grid_{movie['id']}")
            st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
    else:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 3.5rem 1rem; text-align: center; margin-top: 1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎬</div>
                <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: var(--text-on-surface); margin-bottom: 0.5rem;">No Matching Movies Found</h3>
                <p style="font-size: 0.88rem; color: var(--text-outline); margin-bottom: 1.5rem; max-width: 480px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    Try adjusting your search keywords, lowering the minimum rating threshold, or resetting your active genre filters.
                </p>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        col_c, _ = st.columns([3, 7])
        with col_c:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            if st.button("Clear All Search & Filters", key="disc_empty_clear_btn"):
                st.session_state.discover_search = ""
                st.session_state.global_search = ""
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
