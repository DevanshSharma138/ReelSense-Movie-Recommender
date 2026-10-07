"""
ReelSense - Movie Details Page Module
Matching latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services import user_store
from src.components.movie_card import render_movie_card

FALLBACK_POSTER = "https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=600&auto=format&fit=crop"

def render_movie_details_page():
    raw_movie_id = st.session_state.get("selected_movie_id")
    movie_id = None
    if raw_movie_id is not None:
        try:
            movie_id = int(raw_movie_id)
        except (ValueError, TypeError):
            movie_id = raw_movie_id
    movie = MovieService.get_movie_by_id(movie_id) if movie_id is not None else None

    if not movie:
        all_m = MovieService.get_all_movies()
        if all_m:
            movie = all_m[0]
            movie_id = int(movie["id"])
            st.session_state.selected_movie_id = movie_id
        else:
            st.error("Movie not found in collection.")
            if st.button("← Back to Home"):
                st.session_state.current_page = "home"
                st.rerun()
            return

    # Back Navigation Button
    col_back, _ = st.columns([3, 7])
    with col_back:
        if st.button("← Back to Browse", key="back_to_browse_btn"):
            st.session_state.current_page = "home"
            st.rerun()

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # Hero Backdrop & Poster Header Layout
    poster_url = movie.get("poster_url") or FALLBACK_POSTER
    title = movie["title"]
    year = movie.get("release_year", 2024)
    rating = movie.get("rating", 8.8)
    genres = ", ".join(movie.get("genres", ["Cinema"]))
    runtime = movie.get("runtime", "N/A")
    director = movie.get("director", "Unknown")
    cast = ", ".join(movie.get("cast", []))
    overview = movie.get("overview", "")
    affinity = movie.get("mood_affinity") or movie.get("vector_match") or 0

    # Session State Watchlist & Ratings
    watchlist = st.session_state.get("watchlist", [])
    in_watchlist = movie_id in watchlist
    ratings_dict = st.session_state.get("ratings", {})
    user_saved_rating = float(ratings_dict.get(movie_id, 0.0))

    # Header Card Layout
    col_poster, col_info = st.columns([1, 2.2])

    with col_poster:
        st.markdown(
            textwrap.dedent(f"""
            <div style="border-radius: 16px; overflow: hidden; border: 1.5px solid rgba(212, 175, 55, 0.4); box-shadow: 0 12px 32px rgba(0,0,0,0.7), 0 0 20px rgba(212,175,55,0.15);">
                <img src="{poster_url}" style="width: 100%; aspect-ratio: 2/3; object-fit: cover;" onerror="this.src='{FALLBACK_POSTER}';"/>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    match_badge_html = f"""<span style="background: rgba(242, 202, 80, 0.15); color: #f2ca50; border: 1px solid #f2ca50; padding: 3px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">✨ {affinity}% Vector Match</span>""" if affinity > 0 else ""

    runtime_pill = f"<span style='color: #99907c; font-size: 0.8rem;'>• {runtime}</span>" if runtime and runtime != "N/A" else ""
    dir_cell = f"<div><strong style='color: #e5e1e4;'>Director:</strong> {director}</div>" if director and director != "Unknown" else ""
    cast_cell = f"<div><strong style='color: #e5e1e4;'>Principal Cast:</strong> {cast}</div>" if cast else ""
    meta_row = f"""<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.85rem; color: #99907c; margin-bottom: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(77, 70, 53, 0.25);">{dir_cell}{cast_cell}</div>""" if (dir_cell or cast_cell) else ""

    with col_info:
        st.markdown(
            textwrap.dedent(f"""
            <div style="background: #201f22; border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 16px; padding: 2rem; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
                <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap;">
                    {match_badge_html}
                    <span style="background: #2a2a2c; color: #e5e1e4; padding: 3px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">⭐ {rating}/10</span>
                    <span style="color: #99907c; font-size: 0.8rem;">• {year}</span>
                    {runtime_pill}
                    <span style="color: #99907c; font-size: 0.8rem;">• {movie.get('language', 'English')}</span>
                </div>
                <h1 style="font-family: 'Outfit'; font-size: 2.4rem; font-weight: 700; color: #e5e1e4; margin: 0 0 0.5rem 0; line-height: 1.1;">{title}</h1>
                <p style="font-size: 0.88rem; color: #e7c17c; font-weight: 600; margin-bottom: 1.25rem;">{genres}</p>
                <h4 style="font-size: 0.85rem; font-weight: 700; color: #99907c; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">Logline & Overview</h4>
                <p style="font-size: 0.95rem; color: #d0c5af; line-height: 1.6; margin-bottom: 1.5rem;">{overview}</p>
                {meta_row}
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        col_w_btn, col_r_box = st.columns([1.2, 2])

        with col_w_btn:
            wl_label = "✓ In Watchlist" if in_watchlist else "+ Add to Watchlist"
            css = "gold-btn" if in_watchlist else ""
            if css: st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
            if st.button(wl_label, key=f"det_wl_{movie_id}", use_container_width=True):
                if in_watchlist:
                    watchlist.remove(movie_id)
                else:
                    watchlist.append(movie_id)
                st.session_state.watchlist = watchlist
                user_store.save_watchlist(watchlist)
                st.rerun()
            if css: st.markdown('</div>', unsafe_allow_html=True)

            # Not Interested Toggle
            not_interested = set(st.session_state.get("not_interested", set()))
            is_hidden = movie_id in not_interested
            hide_label = "↩️ Restore to Picks" if is_hidden else "🚫 Not Interested"
            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
            if st.button(hide_label, key=f"det_hide_{movie_id}", use_container_width=True, help="Exclude this film from your personalized recommendations"):
                if is_hidden:
                    not_interested.remove(movie_id)
                    st.toast(f"Restored '{title}' to recommendations", icon="↩️")
                else:
                    not_interested.add(movie_id)
                    st.toast(f"Marked '{title}' as Not Interested. Excluded from recommendations.", icon="🚫")
                st.session_state.not_interested = not_interested
                user_store.save_not_interested(not_interested)
                st.rerun()

        with col_r_box:
            new_user_rating = st.slider(
                "Your Personal Rating",
                min_value=0.0,
                max_value=10.0,
                value=float(user_saved_rating),
                step=0.5,
                key=f"user_rate_slider_{movie_id}",
                format="⭐ %.1f"
            )

            col_sub1, col_sub2 = st.columns([1, 1])
            with col_sub1:
                st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
                if st.button("⭐ Save Rating", key=f"save_rate_btn_{movie_id}", use_container_width=True):
                    if new_user_rating > 0.0:
                        ratings_dict[movie_id] = float(new_user_rating)
                        st.session_state.ratings = ratings_dict
                        user_store.save_ratings(ratings_dict)
                        st.toast(f"Saved rating {new_user_rating}⭐ for {title}!", icon="⭐")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_sub2:
                if user_saved_rating > 0.0:
                    st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Remove Rating", key=f"del_rate_btn_{movie_id}", use_container_width=True):
                        if movie_id in ratings_dict:
                            del ratings_dict[movie_id]
                        st.session_state.ratings = ratings_dict
                        user_store.save_ratings(ratings_dict)
                        st.toast(f"Removed rating for {title}", icon="🗑️")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # Automatic save when slider is dragged/changed
            if new_user_rating != user_saved_rating:
                if new_user_rating == 0.0:
                    if movie_id in ratings_dict:
                        del ratings_dict[movie_id]
                    st.session_state.ratings = ratings_dict
                    user_store.save_ratings(ratings_dict)
                    st.toast(f"Removed rating for {title}", icon="🗑️")
                    st.rerun()
                else:
                    ratings_dict[movie_id] = float(new_user_rating)
                    st.session_state.ratings = ratings_dict
                    user_store.save_ratings(ratings_dict)
                    st.toast(f"Saved rating {new_user_rating}⭐ for {title}!", icon="⭐")
                    st.rerun()

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # Why We Recommend This Section (Dynamic Signals)
    user_ratings = st.session_state.get("ratings", {})
    reasons = RecommendationService.get_recommendation_explanation(movie, user_ratings=user_ratings)
    st.markdown(
        textwrap.dedent(f"""
        <div style="background: #1c1b1e; border: 1px solid rgba(77, 70, 53, 0.3); border-radius: 14px; padding: 1.5rem;">
            <div style="font-family: 'Outfit'; font-size: 1.15rem; font-weight: 700; color: #f2ca50; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: #f2ca50;">auto_awesome</span>
                <span>Why ReelSense Curates "{title}"</span>
            </div>
            <ul style="margin: 0; padding-left: 1.25rem; color: #d0c5af; font-size: 0.9rem; line-height: 1.7;">
                {"".join([f'<li>{r}</li>' for r in reasons])}
            </ul>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # Similar Movies Grid
    similar_movies = RecommendationService.get_similar_movies(movie, limit=4)
    st.markdown(
        textwrap.dedent("""
        <div style="margin-bottom: 1rem;">
            <h3 style="font-family: 'Outfit'; font-size: 1.4rem; font-weight: 700; color: #e5e1e4; margin: 0;">
                Thematic & Vector Similar Masterworks
            </h3>
            <p style="font-size: 0.85rem; color: #99907c; margin-top: 2px;">
                Films sharing director aesthetic, color grading, and sonic mood profile.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    cols = st.columns(4)
    for idx, sim_m in enumerate(similar_movies):
        with cols[idx]:
            render_movie_card(sim_m, key_prefix=f"sim_card_{idx}")
