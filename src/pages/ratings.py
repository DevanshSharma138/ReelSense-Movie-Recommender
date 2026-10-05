"""
ReelSense - My Ratings Page Module
"""

import streamlit as st
from src.services.movie_service import MovieService

FALLBACK_POSTER = "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=600&auto=format&fit=crop"

def render_ratings_page():
    st.markdown(
        """
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">star</span>
                <span>Critical Affinity Feedback</span>
            </div>
            <h1 class="mood-page-title">
                My <span>Ratings</span>
            </h1>
            <p class="mood-page-sub">
                Manage your subjective evaluation scores to continuously calibrate ReelSense's neural embedding weights.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    ratings_dict = st.session_state.get("ratings", {})

    if not ratings_dict:
        st.markdown(
            """
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 3.5rem 1rem; text-align: center; margin-top: 1.5rem;">
                <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">⭐</div>
                <h3 style="font-size: 1.3rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">No Rated Movies Yet</h3>
                <p style="font-size: 0.9rem; color: #A0A0A0; margin-bottom: 1.5rem; max-width: 450px; margin-left: auto; margin-right: auto;">
                    Rate films on their Details page to teach ReelSense what kind of cinema moves you.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_c, _ = st.columns([3, 7])
        with col_c:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            if st.button("🔍 Discover Movies to Rate", key="ratings_empty_disc_btn"):
                st.session_state.current_page = "discover"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown(f"<p style='font-size: 1.05rem; font-weight: 700; color: #F4EBDD; margin-bottom: 1rem;'>You have rated {len(ratings_dict)} films:</p>", unsafe_allow_html=True)

    for m_id, user_val in list(ratings_dict.items()):
        movie = MovieService.get_movie_by_id(m_id)
        if not movie:
            continue

        poster_url = movie.get("poster_url") or FALLBACK_POSTER

        st.markdown('<div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
        col_img, col_info, col_ctrl = st.columns([1, 4, 3])

        with col_img:
            st.markdown(
                f'<img src="{poster_url}" style="width: 100%; border-radius: 8px; aspect-ratio: 2/3; object-fit: cover;" onerror="this.src=\'{FALLBACK_POSTER}\';"/>',
                unsafe_allow_html=True
            )

        with col_info:
            st.markdown(
                f"""
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #F4EBDD; margin-bottom: 4px;">{movie['title']} ({movie['release_year']})</h3>
                <p style="font-size: 0.8rem; color: #D6AD60; margin-bottom: 8px;">{", ".join(movie.get('genres', []))}</p>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #A0A0A0;">
                    <span>Global Rating: ⭐ {movie['rating']}/10</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_ctrl:
            updated_score = st.slider(
                "Your Given Rating",
                min_value=1.0,
                max_value=10.0,
                value=float(user_val),
                step=0.5,
                key=f"rate_page_slider_{m_id}",
                format="⭐ %.1f"
            )
            
            if updated_score != user_val:
                st.session_state.ratings[m_id] = updated_score
                st.toast(f"Updated rating to {updated_score}⭐", icon="⭐")
                st.rerun()

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Details", key=f"rate_det_btn_{m_id}"):
                    st.session_state.selected_movie_id = m_id
                    st.session_state.current_page = "movie_details"
                    st.rerun()
            with col_b2:
                if st.button("Remove", key=f"rate_del_btn_{m_id}"):
                    del st.session_state.ratings[m_id]
                    st.toast(f"Removed rating for {movie['title']}", icon="🗑️")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
