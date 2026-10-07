"""
ReelSense - My Ratings Page Module
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.services import user_store

FALLBACK_POSTER = "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=600&auto=format&fit=crop"

def render_ratings_page():
    st.markdown(
        textwrap.dedent("""
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
        """).strip(),
        unsafe_allow_html=True
    )

    ratings_dict = st.session_state.get("ratings", {})

    if not ratings_dict:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 3.5rem 1rem; text-align: center; margin-top: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">⭐</div>
                <h3 style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; color: var(--text-on-surface); margin-bottom: 0.5rem;">No Rated Movies Yet</h3>
                <p style="font-size: 0.9rem; color: var(--text-outline); margin-bottom: 1.5rem; max-width: 450px; margin-left: auto; margin-right: auto; line-height: 1.6;">
                    Rate films on their Details page or Discover view to teach ReelSense what kind of cinema moves you.
                </p>
            </div>
            """).strip(),
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

    st.markdown(f"<p style='font-size: 1.05rem; font-weight: 700; color: var(--text-on-surface); margin-bottom: 1rem;'>You have evaluated {len(ratings_dict)} titles:</p>", unsafe_allow_html=True)

    for raw_m_id, user_val in list(ratings_dict.items()):
        try:
            m_id = int(raw_m_id)
        except (ValueError, TypeError):
            m_id = raw_m_id
        movie = MovieService.get_movie_by_id(m_id)
        if not movie:
            continue

        poster_url = movie.get("poster_url") or FALLBACK_POSTER

        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
            """).strip(),
            unsafe_allow_html=True
        )
        col_img, col_info, col_ctrl = st.columns([1, 4, 3])

        with col_img:
            st.markdown(
                f'<img src="{poster_url}" style="width: 100%; border-radius: 10px; aspect-ratio: 2/3; object-fit: cover; border: 1px solid rgba(77, 70, 53, 0.3);" onerror="this.src=\'{FALLBACK_POSTER}\';"/>',
                unsafe_allow_html=True
            )

        with col_info:
            st.markdown(
                textwrap.dedent(f"""
                <h3 style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; color: var(--text-on-surface); margin: 0 0 6px 0;">{movie['title']} <span style="font-weight: 400; color: var(--text-outline); font-size: 0.9rem;">({movie['release_year']})</span></h3>
                <p style="font-size: 0.8rem; color: var(--primary-gold); font-weight: 600; margin-bottom: 8px;">{", ".join(movie.get('genres', []))}</p>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-outline);">
                    <span>Community Consensus: ⭐ {movie['rating']}/10</span>
                </div>
                """).strip(),
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
                st.session_state.ratings[m_id] = float(updated_score)
                user_store.save_ratings(st.session_state.ratings)
                st.toast(f"Updated rating to {updated_score}⭐", icon="⭐")
                st.rerun()

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🎬 Details", key=f"rate_det_btn_{m_id}", use_container_width=True):
                    st.session_state.selected_movie_id = m_id
                    st.session_state.current_page = "movie_details"
                    st.rerun()
            with col_b2:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"rate_del_btn_{m_id}", use_container_width=True, help="Remove this rating"):
                    if m_id in st.session_state.ratings:
                        del st.session_state.ratings[m_id]
                    user_store.save_ratings(st.session_state.ratings)
                    st.toast(f"Removed rating for {movie['title']}", icon="🗑️")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
