"""
ReelSense - Movie Carousel & Section Container Component
Renders responsive rows of movie cards (supports up to 12 items across 6-column rows)
"""

import streamlit as st
from src.components.movie_card import render_movie_card
from src.utils.ui_helpers import render_html


def render_movie_carousel(title, subtitle=None, movies=None, tag=None, view_all_page=None, carousel_id="row"):
    if not movies:
        st.info("No eligible movies found for this category.")
        return

    # Section Header Container
    col_head, col_action = st.columns([8.5, 2.5])

    with col_head:
        tag_html = f'<div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 3px;">{tag}</div>' if tag else ''
        sub_html = f'<p class="section-header-sub" style="font-size: 0.88rem; color: #99907c; margin: 3px 0 0 0; line-height: 1.4;">{subtitle}</p>' if subtitle else ''
        render_html(f"""
        <div class="section-header-box" style="margin-bottom: 0.75rem;">
            {tag_html}
            <h2 class="section-header-title" style="font-family: 'Outfit', sans-serif; font-size: 1.45rem; font-weight: 700; color: #e5e1e4; margin: 0; letter-spacing: -0.01em;">{title}</h2>
            {sub_html}
        </div>
        """)

    with col_action:
        if view_all_page:
            def _on_vall_click(target_page=view_all_page):
                st.session_state.current_page = target_page

            st.button("View All →", key=f"vall_{carousel_id}", on_click=_on_vall_click)

    # Render movie cards in chunks of 6 (supports up to 12 or more in neat rows)
    chunk_size = 6
    for row_start in range(0, len(movies), chunk_size):
        row_movies = movies[row_start:row_start + chunk_size]
        cols = st.columns(len(row_movies))
        for col_idx, movie in enumerate(row_movies):
            global_idx = row_start + col_idx
            with cols[col_idx]:
                render_movie_card(movie, key_prefix=f"{carousel_id}_{global_idx}")
        if row_start + chunk_size < len(movies):
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
