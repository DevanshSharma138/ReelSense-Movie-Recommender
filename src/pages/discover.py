"""
ReelSense - Discover Page Module
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.components.movie_card import render_movie_card
from src.components.onboarding_banner import render_onboarding_banner

def _reset_discover_filters_callback():
    st.session_state.discover_search = ""
    st.session_state.global_search = ""
    st.session_state.disc_search_input = ""
    st.session_state.topbar_global_search_input = ""
    st.session_state.filter_genres = []
    st.session_state.filter_min_rating = 0.0
    st.session_state.filter_language = "All"
    st.session_state.filter_sort_by = "Rating (High to Low)"
    st.session_state.filter_year_range = (1930, 2026)
    st.session_state.filter_genres_widget = []
    st.session_state.filter_min_rating_widget = 0.0
    st.session_state.filter_language_widget = "All"
    st.session_state.filter_sort_by_widget = "Rating (High to Low)"
    st.session_state.filter_year_range_widget = (1930, 2026)


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
    if "disc_search_input" not in st.session_state:
        st.session_state.disc_search_input = st.session_state.get("discover_search", "")

    search_query = st.text_input(
        "Search Movies",
        value=st.session_state.get("disc_search_input", ""),
        placeholder="Search by title, director, cast, or genre...",
        label_visibility="collapsed",
        key="disc_search_input"
    )
    if search_query != st.session_state.get("discover_search", ""):
        st.session_state.discover_search = search_query
        st.session_state.global_search = search_query
        st.session_state.topbar_global_search_input = search_query

    # Initialize filter state defaults
    if "filter_genres" not in st.session_state:
        st.session_state.filter_genres = []
    if "filter_min_rating" not in st.session_state:
        st.session_state.filter_min_rating = 0.0
    if "filter_language" not in st.session_state:
        st.session_state.filter_language = "All"
    if "filter_sort_by" not in st.session_state:
        st.session_state.filter_sort_by = "Rating (High to Low)"
    if "filter_year_range" not in st.session_state:
        st.session_state.filter_year_range = (1930, 2026)

    # Filters Section Collapsible / Expandable Container
    with st.expander("🎛️ Filter & Sort Controls", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        all_genres = MovieService.get_all_genres()
        all_languages = ["All"] + MovieService.get_all_languages()
        sort_options = [
            "Rating (High to Low)",
            "Release Year (Newest First)",
            "Release Year (Oldest First)",
            "Title (A-Z)"
        ]

        with col1:
            selected_genres = st.multiselect(
                "Genres",
                options=all_genres,
                default=st.session_state.filter_genres,
                placeholder="Select genres...",
                key="filter_genres_widget"
            )

        with col2:
            min_rating = st.slider(
                "Minimum Rating",
                min_value=0.0,
                max_value=10.0,
                value=float(st.session_state.filter_min_rating),
                step=0.5,
                format="⭐ %.1f",
                key="filter_min_rating_widget"
            )

        with col3:
            curr_lang = st.session_state.filter_language
            lang_idx = all_languages.index(curr_lang) if curr_lang in all_languages else 0
            language = st.selectbox(
                "Language",
                options=all_languages,
                index=lang_idx,
                key="filter_language_widget"
            )

        with col4:
            curr_sort = st.session_state.filter_sort_by
            sort_idx = sort_options.index(curr_sort) if curr_sort in sort_options else 0
            sort_by = st.selectbox(
                "Sort By",
                options=sort_options,
                index=sort_idx,
                key="filter_sort_by_widget"
            )

        col_year, col_reset = st.columns([3, 1])
        with col_year:
            year_range = st.slider(
                "Release Year Range",
                min_value=1930,
                max_value=2026,
                value=st.session_state.filter_year_range,
                step=1,
                key="filter_year_range_widget"
            )

        with col_reset:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("🔄 Reset Filters", key="disc_reset_filters_btn", on_click=_reset_discover_filters_callback)

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
