"""
ReelSense - Movie Carousel & Section Container Component
"""

import streamlit as st
from src.components.movie_card import render_movie_card

def render_movie_carousel(title, subtitle=None, movies=None, tag=None, view_all_page=None, carousel_id="row"):
    if not movies:
        st.info("No movies found for this category.")
        return

    # Section Header Container
    col_head, col_action = st.columns([8.5, 2.5])

    with col_head:
        st.markdown(
            f"""
            <div class="section-header-box">
                {f'<div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 2px;">{tag}</div>' if tag else ''}
                <h2 class="section-header-title">{title}</h2>
                {f'<p class="section-header-sub">{subtitle}</p>' if subtitle else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_action:
        if view_all_page:
            st.markdown('<div style="display: flex; justify-content: flex-end; align-items: flex-end; height: 100%; padding-bottom: 0.8rem;">', unsafe_allow_html=True)
            if st.button("View All →", key=f"vall_{carousel_id}"):
                st.session_state.current_page = view_all_page
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Render movie cards in columns
    cols = st.columns(min(len(movies), 6))
    for idx, movie in enumerate(movies[:6]):
        with cols[idx]:
            render_movie_card(movie, key_prefix=f"{carousel_id}_{idx}")
