"""
ReelSense - Reusable Movie Poster Card Component
Matching Obsidian & Champagne Gold Cinematic Design System
Features:
  - Working 1-5 star quick-rating control
  - Watchlist (Vault) toggle
  - Not Interested (Hide / Restore) toggle
  - Match percentage badge
  - Concise honest recommendation explanations
"""

import streamlit as st
from src.services import user_store
from src.utils.ui_helpers import render_html

FALLBACK_POSTER = "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=600&auto=format&fit=crop"


def render_movie_card(movie, key_prefix="card"):
    if not movie:
        return

    m_id = movie["id"]
    title = movie["title"]
    year = movie.get("release_year", 2024)
    raw_rating = movie.get("rating", 8.5)
    # Normalize displayed community rating to 0-5 scale
    star_rating = raw_rating / 2.0 if raw_rating > 5.0 else raw_rating
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

    user_ratings = st.session_state.get("ratings", {})
    user_val = user_ratings.get(m_id)
    is_liked = (user_val is not None and float(user_val) >= 3.5)
    is_disliked = (user_val is not None and float(user_val) < 3.5)

    affinity_html = (
        f'<div class="film-badge-affinity">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background: #f2ca50; display: inline-block;"></span>'
        f'<span>{match_pct}% Match</span></div>'
    ) if match_pct > 0 else ""

    hidden_tag = (
        '<div style="position: absolute; top: 10px; left: 10px; background: rgba(220, 53, 69, 0.9); '
        'color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; z-index: 3;">'
        'NOT INTERESTED</div>'
    ) if in_not_interested else ""

    user_reaction_tag = ""
    rating_top_offset = "top: 10px;"
    if is_liked:
        user_reaction_tag = (
            '<div style="position: absolute; top: 10px; right: 10px; background: rgba(242, 202, 80, 0.95); '
            'color: #131315; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; z-index: 4; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 4px;">'
            '👍 LIKED</div>'
        )
        rating_top_offset = "top: 38px;"
    elif is_disliked:
        user_reaction_tag = (
            '<div style="position: absolute; top: 10px; right: 10px; background: rgba(220, 53, 69, 0.95); '
            'color: #ffffff; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; z-index: 4; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 4px;">'
            '👎 DISLIKED</div>'
        )
        rating_top_offset = "top: 38px;"

    card_opacity = "opacity: 0.55;" if in_not_interested else ""

    # Concise explanation if available
    why_list = movie.get("why_recommended", [])
    why_text = why_list[0] if why_list else ""
    why_html = f'<div style="font-size: 0.72rem; color: #f2ca50; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{why_text}">💡 {why_text}</div>' if why_text else ""

    # Poster Card HTML matching Stitch design
    card_html = f"""
    <div class="film-card" style="{card_opacity}">
        <div class="film-poster-container">
            <img src="{poster_url}" class="film-poster-img" alt="{title}" onerror="this.src='{FALLBACK_POSTER}';"/>
            {hidden_tag}
            {user_reaction_tag}
            {affinity_html}
            <div class="film-badge-rating" style="{rating_top_offset}">
                <span class="material-symbols-outlined" style="font-size: 14px; color: #f2ca50;">star</span>
                <span>{star_rating:.1f}</span>
            </div>
            <div class="film-poster-meta-bottom">
                <span class="film-runtime-pill">{runtime}</span>
                <span class="film-genre-text">{genre_str}</span>
            </div>
        </div>
        <div class="film-card-content">
            <div>
                <h3 class="film-title" title="{title}">{title}</h3>
                {why_html}
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
    """

    def _on_card_click(target_id, origin_page):
        st.session_state.previous_page = origin_page
        st.session_state.selected_movie_id = target_id
        st.session_state.current_page = "movie_details"

    def _on_watchlist_toggle(target_id):
        wl = list(st.session_state.get("watchlist", []))
        if target_id in wl:
            wl.remove(target_id)
        else:
            wl.append(target_id)
        st.session_state.watchlist = wl
        user_store.save_watchlist(wl)

    def _on_hide_toggle(target_id):
        ni = set(st.session_state.get("not_interested", set()))
        if target_id in ni:
            ni.remove(target_id)
        else:
            ni.add(target_id)
        st.session_state.not_interested = ni
        user_store.save_not_interested(ni)

    def _on_like_toggle(target_id):
        cur = dict(st.session_state.get("ratings", {}))
        cur_val = cur.get(target_id)
        if cur_val is not None and float(cur_val) >= 3.5:
            user_store.remove_rating(target_id)
        else:
            user_store.rate_movie(target_id, 5.0)
        st.session_state.ratings = user_store.get_ratings()

    def _on_dislike_toggle(target_id):
        cur = dict(st.session_state.get("ratings", {}))
        cur_val = cur.get(target_id)
        if cur_val is not None and float(cur_val) < 3.5:
            user_store.remove_rating(target_id)
        else:
            user_store.rate_movie(target_id, 1.0)
        st.session_state.ratings = user_store.get_ratings()

    # Clickable Movie Card Container
    with st.container(key=f"card_box_{key_prefix}_{m_id}"):
        render_html(card_html)
        st.button(
            f"View {title}",
            key=f"{key_prefix}_card_{m_id}",
            help=f"View details for {title}",
            use_container_width=True,
            on_click=_on_card_click,
            args=(m_id, st.session_state.get("current_page", "home"))
        )

    # Actions Row 1: Like & Dislike Quick Reactions
    col_like, col_dislike = st.columns(2)
    with col_like:
        like_btn_label = "👍 Liked" if is_liked else "👍 Like"
        like_btn_type = "primary" if is_liked else "secondary"
        st.button(
            like_btn_label,
            key=f"{key_prefix}_like_{m_id}",
            help="Like this movie to calibrate recommendations",
            use_container_width=True,
            type=like_btn_type,
            on_click=_on_like_toggle,
            args=(m_id,)
        )

    with col_dislike:
        dislike_btn_label = "👎 Disliked" if is_disliked else "👎 Dislike"
        dislike_btn_key = f"{key_prefix}_dislike_active_{m_id}" if is_disliked else f"{key_prefix}_dislike_{m_id}"
        st.button(
            dislike_btn_label,
            key=dislike_btn_key,
            help="Dislike this movie to avoid similar picks",
            use_container_width=True,
            on_click=_on_dislike_toggle,
            args=(m_id,)
        )

    # Actions Row 2: Watchlist (Vault) & Hide/Restore
    col_bm, col_hide = st.columns(2)
    with col_bm:
        st.button(
            bookmark_icon,
            key=f"{key_prefix}_bm_{m_id}",
            help="Toggle Watchlist",
            use_container_width=True,
            on_click=_on_watchlist_toggle,
            args=(m_id,)
        )

    with col_hide:
        hide_btn_label = "↩️ Restore" if in_not_interested else "🚫 Hide"
        hide_help = "Restore to recommendations" if in_not_interested else "Mark Not Interested (exclude from picks)"
        st.button(
            hide_btn_label,
            key=f"{key_prefix}_hide_{m_id}",
            help=hide_help,
            use_container_width=True,
            on_click=_on_hide_toggle,
            args=(m_id,)
        )
