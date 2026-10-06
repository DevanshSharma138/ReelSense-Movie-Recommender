"""
ReelSense - Reusable Movie Poster Card Component
Matching latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import streamlit as st
from src.services import user_store

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
    director_val = movie.get("director", "")
    director = director_val if director_val else (genres[0] if genres else "Cinema")
    runtime_val = movie.get("runtime", "")
    runtime = runtime_val if runtime_val and runtime_val != "N/A" else str(year)
    poster_url = movie.get("poster_url") or FALLBACK_POSTER

    watchlist = st.session_state.get("watchlist", [])
    in_watchlist = m_id in watchlist
    bookmark_icon = "✓ Saved" if in_watchlist else "+ Vault"

    not_interested = set(st.session_state.get("not_interested", set()))
    in_not_interested = m_id in not_interested

    affinity_html = f"""
                <div class="film-badge-affinity">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: #f2ca50; display: inline-block;"></span>
                    <span>{match_pct}% Match</span>
                </div>""" if match_pct > 0 else ""

    hidden_tag = """
                <div style="position: absolute; top: 10px; left: 10px; background: rgba(220, 53, 69, 0.85); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; z-index: 3;">
                    NOT INTERESTED
                </div>""" if in_not_interested else ""

    # Poster Card HTML matching Stitch design
    st.markdown(
        f"""
        <div class="film-card" style="{'opacity: 0.55;' if in_not_interested else ''}">
            <div class="film-poster-container">
                <img src="{poster_url}" class="film-poster-img" alt="{title}" onerror="this.src='{FALLBACK_POSTER}';"/>
                {hidden_tag}
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

    # Action buttons below card: Inspect, Bookmark, and Not Interested
    col1, col2, col3 = st.columns([3.0, 2.0, 1.4])

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
            user_store.save_watchlist(watchlist)
            st.rerun()

    with col3:
        hide_btn_icon = "↩️" if in_not_interested else "🚫"
        hide_help = "Restore to recommendations" if in_not_interested else "Mark Not Interested (exclude from picks)"
        if st.button(hide_btn_icon, key=f"{key_prefix}_hide_{m_id}", help=hide_help, use_container_width=True):
            if in_not_interested:
                not_interested.remove(m_id)
                st.toast(f"Restored '{title}' to recommendations", icon="↩️")
            else:
                not_interested.add(m_id)
                st.toast(f"Marked '{title}' as Not Interested", icon="🚫")
            st.session_state.not_interested = not_interested
            user_store.save_not_interested(not_interested)
            st.rerun()
