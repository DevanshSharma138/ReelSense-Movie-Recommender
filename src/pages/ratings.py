"""
ReelSense - My Reactions & Taste Feedback Page Module
"""

import streamlit as st
from src.services.movie_service import MovieService
from src.services import user_store
from src.utils.ui_helpers import render_html

FALLBACK_POSTER = "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=600&auto=format&fit=crop"


def render_ratings_page():
    render_html("""
    <div class="mood-page-header">
        <div class="mood-spectrum-badge">
            <span class="material-symbols-outlined" style="font-size: 16px;">thumb_up</span>
            <span>Taste & Preference Feedback</span>
        </div>
        <h1 class="mood-page-title">
            My <span>Feedback</span>
        </h1>
        <p class="mood-page-sub">
            Review your liked and disliked movies to continuously calibrate ReelSense's neural recommendation vectors.
        </p>
    </div>
    """)

    ratings_dict = st.session_state.get("ratings", {})

    if not ratings_dict:
        render_html("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 3.5rem 1rem; text-align: center; margin-top: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">👍</div>
            <h3 style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; color: var(--text-on-surface); margin-bottom: 0.5rem;">No Movie Reactions Yet</h3>
            <p style="font-size: 0.9rem; color: var(--text-outline); margin-bottom: 1.5rem; max-width: 480px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                Use the Like (👍) and Dislike (👎) buttons on any movie card or details page to teach ReelSense what kind of cinema moves you.
            </p>
        </div>
        """)
        col_c, _ = st.columns([3, 7])
        with col_c:
            def _on_empty_disc():
                st.session_state.current_page = "discover-movies"
                st.session_state.nav_route = "discover-movies"

            st.button(
                "🔍 Discover Movies to React",
                key="ratings_empty_disc_btn",
                type="primary",
                on_click=_on_empty_disc
            )
        return

    # Categorize into Liked vs Disliked
    liked_entries = [(k, v) for k, v in ratings_dict.items() if float(v) >= 3.5]
    disliked_entries = [(k, v) for k, v in ratings_dict.items() if float(v) < 3.5]

    col_filter, col_counts = st.columns([6, 4], vertical_alignment="center")
    with col_filter:
        tab_choice = st.radio(
            "Filter Reactions",
            options=["All", "Liked", "Disliked"],
            format_func=lambda x: f"All ({len(ratings_dict)})" if x == "All" else (f"👍 Liked ({len(liked_entries)})" if x == "Liked" else f"👎 Disliked ({len(disliked_entries)})"),
            horizontal=True,
            key="feedback_tab_filter",
            label_visibility="collapsed"
        )
    with col_counts:
        render_html(f"""
        <div style="text-align: right; font-size: 0.85rem; color: #99907c;">
            <span style="color: #f2ca50; font-weight: 700;">{len(liked_entries)}</span> Liked &nbsp;·&nbsp;
            <span style="color: #ff6b6b; font-weight: 700;">{len(disliked_entries)}</span> Disliked
        </div>
        """)

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    if tab_choice == "Liked":
        entries = liked_entries
    elif tab_choice == "Disliked":
        entries = disliked_entries
    else:
        entries = list(ratings_dict.items())

    if not entries:
        st.info(f"No {tab_choice.lower()} films found.")
        return

    for raw_m_id, user_val in entries:
        try:
            m_id = int(raw_m_id)
        except (ValueError, TypeError):
            m_id = raw_m_id
        movie = MovieService.get_movie_by_id(m_id)
        if not movie:
            continue

        is_liked = (float(user_val) >= 3.5)
        poster_url = movie.get("poster_url") or FALLBACK_POSTER

        with st.container(key=f"rating_card_{m_id}"):
            col_img, col_info, col_ctrl = st.columns([1, 4.5, 2.5])

            with col_img:
                render_html(f'<img src="{poster_url}" style="width: 100%; border-radius: 10px; aspect-ratio: 2/3; object-fit: cover; border: 1px solid rgba(77, 70, 53, 0.3);" onerror="this.src=\'{FALLBACK_POSTER}\';"/>')

            with col_info:
                genres_str = ", ".join(movie.get("genres", []))
                raw_cat_rating = float(movie.get("rating", 8.0))
                badge_html = (
                    '<span style="background: rgba(242, 202, 80, 0.15); color: #f2ca50; border: 1px solid rgba(242, 202, 80, 0.4); padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem;">👍 You Liked This</span>'
                    if is_liked
                    else '<span style="background: rgba(220, 53, 69, 0.15); color: #ff6b6b; border: 1px solid rgba(220, 53, 69, 0.4); padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.78rem;">👎 You Disliked This</span>'
                )
                render_html(f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    {badge_html}
                    <span style="font-size: 0.78rem; color: #99907c;">IMDb {raw_cat_rating:.1f}</span>
                </div>
                <h3 style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; color: var(--text-on-surface); margin: 0 0 6px 0;">{movie['title']} <span style="font-weight: 400; color: var(--text-outline); font-size: 0.9rem;">({movie['release_year']})</span></h3>
                <p style="font-size: 0.82rem; color: var(--primary-gold); font-weight: 600; margin-bottom: 6px;">{genres_str}</p>
                <p style="font-size: 0.82rem; color: #99907c; margin: 0;">Dir. {movie.get('director', 'Cinema')}</p>
                """)

            with col_ctrl:
                # Toggle Buttons
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    def _on_rate_like(target_id=m_id):
                        user_store.rate_movie(target_id, 5.0)
                        st.session_state.ratings = user_store.get_ratings()

                    st.button(
                        "👍 Like",
                        key=f"rate_like_{m_id}",
                        use_container_width=True,
                        type="primary" if is_liked else "secondary",
                        help="Mark as Liked",
                        on_click=_on_rate_like,
                        args=(m_id,)
                    )
                with col_t2:
                    def _on_rate_dislike(target_id=m_id):
                        user_store.rate_movie(target_id, 1.0)
                        st.session_state.ratings = user_store.get_ratings()

                    dislike_btn_key = f"rate_dislike_active_{m_id}" if not is_liked else f"rate_dislike_{m_id}"
                    st.button(
                        "👎 Dislike",
                        key=dislike_btn_key,
                        use_container_width=True,
                        help="Mark as Disliked",
                        on_click=_on_rate_dislike,
                        args=(m_id,)
                    )

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    def _on_rate_details_click(target_id=m_id):
                        st.session_state.previous_page = "my-ratings"
                        st.session_state.selected_movie_id = target_id
                        st.session_state.current_page = "movie_details"

                    st.button("🎬 Details", key=f"rate_det_btn_{m_id}", use_container_width=True, on_click=_on_rate_details_click)
                with col_b2:
                    def _on_rate_del_click(target_id=m_id):
                        user_store.remove_rating(target_id)
                        st.session_state.ratings = user_store.get_ratings()

                    st.button("🗑️ Remove", key=f"rate_del_btn_{m_id}", use_container_width=True, help="Clear this reaction", on_click=_on_rate_del_click)

            st.markdown("<div style='margin-bottom: 1rem; border-bottom: 1px solid rgba(77, 70, 53, 0.2);'></div>", unsafe_allow_html=True)

