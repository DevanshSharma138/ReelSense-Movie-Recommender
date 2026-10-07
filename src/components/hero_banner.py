"""
ReelSense - Featured Movie Hero Banner & Spotlight Component
"""

import streamlit as st
from src.services import user_store
from src.utils.ui_helpers import render_html


def render_hero_banner(featured_movie, cycle_movies=None):
    if not featured_movie:
        return

    m_id = featured_movie["id"]
    title = featured_movie["title"]
    year = featured_movie["release_year"]
    raw_rating = featured_movie.get("rating", 9.2)
    rating_5 = raw_rating / 2.0 if raw_rating > 5.0 else raw_rating
    match_pct = featured_movie.get("vector_match", 98)
    runtime = featured_movie.get("runtime", "152 MIN")
    director = featured_movie.get("director", "")
    overview = featured_movie["overview"]
    backdrop_url = featured_movie.get("backdrop_url", "")

    watchlist = st.session_state.get("watchlist", [])
    in_watchlist = m_id in watchlist
    watchlist_text = "✓ In Vault" if in_watchlist else "+ Add to Vault"

    genres = featured_movie.get("genres", [])
    genre_badges = "".join([f'<span class="hero-badge-tag">{g}</span>' for g in genres[:2]])
    runtime_badge = f'<span class="hero-badge-tag">{runtime}</span>' if runtime and runtime != "N/A" else ""
    director_badge = f'<span style="font-size: 0.76rem; color: #99907c; margin-left: 4px;">Dir. {director}</span>' if director and director != "Denis Villeneuve Esthetic" else ""

    # Main Hero Spotlight Container
    col_hero_content, col_switcher = st.columns([8.5, 3.5])

    with col_hero_content:
        hero_html = f"""
        <div class="hero-spotlight-container" style="background-image: url('{backdrop_url}');">
            <div class="hero-spotlight-overlay">
                <div class="hero-tag-row">
                    <span class="hero-badge-match">✨ {match_pct}% ReelSense Match</span>
                    <span class="hero-badge-tag">{year}</span>
                    <span class="hero-badge-tag">⭐ {rating_5:.1f}/5</span>
                    {runtime_badge}
                    {genre_badges}
                    {director_badge}
                </div>
                <div style="font-size: 0.8rem; font-weight: 700; color: #f2ca50; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 2px;">
                    Curator Premiere Spotlight
                </div>
                <h1 class="hero-spotlight-title">{title}</h1>
                <p class="hero-spotlight-logline">{overview}</p>
            </div>
        </div>
        """
        render_html(hero_html)

        # Action CTAs Below Hero
        def _on_hero_details_click():
            st.session_state.previous_page = "home"
            st.session_state.selected_movie_id = m_id
            st.session_state.current_page = "movie_details"

        def _on_hero_vault_toggle():
            wl = list(st.session_state.get("watchlist", []))
            if m_id in wl:
                wl.remove(m_id)
            else:
                wl.append(m_id)
            st.session_state.watchlist = wl
            user_store.save_watchlist(wl)

        def _on_hero_mood_click():
            st.session_state.current_page = "mood-explorer"

        col_c1, col_c2, col_c3 = st.columns([3, 3, 4])
        with col_c1:
            st.button("🎬 View Movie Details", key=f"hero_stream_{m_id}", use_container_width=True, on_click=_on_hero_details_click, type="primary")

        with col_c2:
            st.button(watchlist_text, key=f"hero_vault_{m_id}", use_container_width=True, on_click=_on_hero_vault_toggle)

        with col_c3:
            st.button("⚡ Explore Mood Resonance", key=f"hero_mood_{m_id}", use_container_width=True, on_click=_on_hero_mood_click)

    with col_switcher:
        switcher_header = """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.8rem;">
            <span style="font-size: 0.72rem; color: #99907c; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700;">Featured Cycle</span>
            <span style="font-size: 0.76rem; color: #f2ca50; font-weight: 700;">01 / 04</span>
        </div>
        """
        render_html(switcher_header)

        active_card_html = f"""
        <div style="background: rgba(32, 31, 34, 0.95); border: 1px solid #f2ca50; border-radius: 14px; padding: 1rem; margin-bottom: 0.75rem; box-shadow: 0 8px 24px rgba(0,0,0,0.6);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-family: 'Outfit'; font-weight: 700; font-size: 1.05rem; color: #e5e1e4;">{title}</span>
                <span style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; background: rgba(242,202,80,0.15); padding: 2px 8px; border-radius: 9999px;">Active</span>
            </div>
            <div style="width: 100%; background: #353437; height: 4px; border-radius: 9999px; overflow: hidden;">
                <div style="background: #f2ca50; width: 75%; height: 100%;"></div>
            </div>
        </div>
        """
        render_html(active_card_html)

        # Up Next Items
        if cycle_movies:
            for idx, c_mov in enumerate(cycle_movies[:3]):
                c_title = c_mov["title"]
                c_genre = c_mov.get("genres", ["Sci-Fi"])[0]
                c_match = c_mov.get("vector_match", 96)

                next_card_html = f"""
                <div style="background: rgba(28, 27, 30, 0.6); border: 1px solid rgba(153, 144, 124, 0.2); border-radius: 12px; padding: 0.75rem 0.9rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 0.88rem; font-weight: 600; color: #e5e1e4;">{c_title}</div>
                        <div style="font-size: 0.75rem; color: #99907c;">{c_genre} · {c_match}% Match</div>
                    </div>
                    <span style="color: #99907c; font-size: 1rem;">▶</span>
                </div>
                """
                def _on_hero_switch_click(target_m_id=c_mov["id"]):
                    st.session_state.previous_page = "home"
                    st.session_state.selected_movie_id = target_m_id
                    st.session_state.current_page = "movie_details"

                st.button(f"Switch to {c_title}", key=f"hero_switch_{c_mov['id']}", use_container_width=True, on_click=_on_hero_switch_click)
