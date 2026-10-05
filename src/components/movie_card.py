"""
ReelSense - Reusable Movie Poster Card Component
Matching latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import streamlit as st

FALLBACK_POSTER = "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=600&auto=format&fit=crop"

def render_movie_card(movie, key_prefix="card"):
    if not movie:
        return

    m_id = movie["id"]
    title = movie["title"]
    year = movie.get("release_year", 2024)
    rating = movie.get("rating", 8.5)
    match_pct = movie.get("mood_affinity") or movie.get("vector_match") or 0
    genres = movie.get("genres", ["Drama"])
    genre_str = " / ".join(genres[:2])
    runtime = movie.get("runtime", "2h 00m")
    director = movie.get("director", "Cinema Masterwork")
    poster_url = movie.get("poster_url") or FALLBACK_POSTER

    watchlist = st.session_state.get("watchlist", [])
    in_watchlist = m_id in watchlist
    bookmark_icon = "✓ Saved" if in_watchlist else "+ Vault"

    affinity_html = f"""
                <div class="film-badge-affinity">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: #f2ca50; display: inline-block;"></span>
                    <span>{match_pct}% Match</span>
                </div>""" if match_pct > 0 else ""

    # Poster Card HTML matching Stitch design
    st.markdown(
        f"""
        <div class="film-card">
            <div class="film-poster-container">
                <img src="{poster_url}" class="film-poster-img" alt="{title}" onerror="this.src='{FALLBACK_POSTER}';"/>
                {affinity_html}
                <div class="film-badge-rating">
                    <span class="material-symbols-outlined" style="font-size: 14px; color: #f2ca50;">star</span>
                    <span>{rating:.1f}</span>
                </div>
                <div class="film-poster-meta-bottom">
                    <span class="film-runtime-pill">{runtime}</span>
                    <span class="film-genre-text">{genre_str}</span>
                </div>
            </div>
            <div class="film-card-content">
                <div>
                    <h3 class="film-title" title="{title}">{title}</h3>
                </div>
                <div class="film-footer-row">
                    <div style="display: flex; align-items: center; gap: 4px; color: #99907c;">
                        <span class="material-symbols-outlined" style="font-size: 16px;">person</span>
                        <span>{director[:15]}</span>
                    </div>
                    <span style="font-size: 0.72rem; color: #99907c;">{year}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Action buttons below card
    col1, col2 = st.columns([3.5, 2.5])

    with col1:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        if st.button("Inspect →", key=f"{key_prefix}_det_{m_id}", use_container_width=True):
            st.session_state.selected_movie_id = m_id
            st.session_state.current_page = "movie_details"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.button(bookmark_icon, key=f"{key_prefix}_bm_{m_id}", help="Toggle Watchlist", use_container_width=True):
            if in_watchlist:
                watchlist.remove(m_id)
            else:
                watchlist.append(m_id)
            st.session_state.watchlist = watchlist
            st.rerun()
