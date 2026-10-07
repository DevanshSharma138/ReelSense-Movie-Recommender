"""
ReelSense - Movie Details Page Module
Matching latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import textwrap
import streamlit as st
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services.taste_service import TasteService
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

    backdrop_url = movie.get("backdrop_url")
    card_bg = (
        f"background: linear-gradient(135deg, rgba(32, 31, 34, 0.92) 0%, rgba(20, 19, 22, 0.97) 100%), url('{backdrop_url}'); background-size: cover; background-position: center;"
        if backdrop_url
        else "background: #201f22;"
    )

    with col_info:
        st.markdown(
            textwrap.dedent(f"""
            <div style="{card_bg} border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 16px; padding: 2rem; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
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

    # -------------------------------------------------------------------------
    # Recommendation Breakdown / Why Recommended 2.0 (Phase 6)
    # -------------------------------------------------------------------------
    user_ratings = st.session_state.get("ratings", {})
    breakdown = TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)
    legacy_reasons = RecommendationService.get_recommendation_explanation(movie, user_ratings=user_ratings)

    is_cold = breakdown.get("is_cold_start", True)

    def _block_bar(pct, total_blocks=10):
        val = pct if pct is not None else 0
        filled = int(round((val / 100.0) * total_blocks))
        filled = max(0, min(total_blocks, filled))
        return "█" * filled + "░" * (total_blocks - filled)

    if is_cold:
        cold_refs_html = ""
        if breakdown.get("positive_references"):
            ref_items = []
            for ref in breakdown["positive_references"][:2]:
                shared = f" (Shared: {', '.join(ref['shared_genres'])})" if ref.get("shared_genres") else ""
                ref_items.append(
                    f"<li style='margin-bottom: 4px;'><strong>{ref['title']}</strong> — rated {ref['user_rating']:g}/10 "
                    f"<span style='color: #f2ca50;'>({int(ref['similarity']*100)}% content similarity)</span>{shared}</li>"
                )
            cold_refs_html = f"""
            <div style="margin-top: 0.85rem; padding-top: 0.85rem; border-top: 1px solid rgba(77, 70, 53, 0.3);">
                <div style="font-size: 0.8rem; font-weight: 700; color: #f2ca50; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    Early Signal References ({len(breakdown['positive_references'])} rated)
                </div>
                <ul style="margin: 0; padding-left: 1.2rem; color: #d0c5af; font-size: 0.86rem; line-height: 1.6;">
                    {''.join(ref_items)}
                </ul>
            </div>
            """

        narrative_source = breakdown.get("narrative") or legacy_reasons
        narrative_items = "".join([f"<li style='margin-bottom: 4px;'>{n}</li>" for n in narrative_source])

        st.markdown(
            textwrap.dedent(f"""
            <div style="background: #1c1b1e; border: 1px solid rgba(77, 70, 53, 0.4); border-radius: 14px; padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 0.75rem;">
                    <div style="font-family: 'Outfit'; font-size: 1.25rem; font-weight: 700; color: #f2ca50; display: flex; align-items: center; gap: 8px;">
                        <span class="material-symbols-outlined" style="color: #f2ca50;">auto_awesome</span>
                        <span>Why ReelSense Curates "{title}"</span>
                    </div>
                    <span style="background: rgba(242, 202, 80, 0.12); color: #f2ca50; border: 1px solid rgba(242, 202, 80, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">
                        {breakdown.get('strength_label', 'Community Curated')}
                    </span>
                </div>
                <div style="font-size: 0.86rem; color: #99907c; margin-bottom: 1rem; line-height: 1.5;">
                    You are currently in <strong>Catalog Discovery mode</strong>. ReelSense grounds this recommendation in MovieLens community ratings, genre balance, and active catalog signals.
                </div>
                <ul style="margin: 0; padding-left: 1.25rem; color: #d0c5af; font-size: 0.88rem; line-height: 1.7;">
                    {narrative_items}
                </ul>
                {cold_refs_html}
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    else:
        c_pct = breakdown.get("content_match_pct", 0)
        t_pct = breakdown.get("taste_match_pct", 0)
        cl_pct = breakdown.get("collab_match_pct", 0)
        h_score = breakdown.get("hybrid_score", 0.0)
        c_contrib = breakdown.get("content_contrib", 0.0)
        cl_contrib = breakdown.get("collab_contrib", 0.0)
        strength = breakdown.get("strength_label", "Strong")

        c_bar = _block_bar(c_pct)
        t_bar = _block_bar(t_pct)
        cl_bar = _block_bar(cl_pct)

        refs_html = ""
        if breakdown.get("positive_references"):
            ref_list = []
            for ref in breakdown["positive_references"]:
                shared_str = f" · Shared: {', '.join(ref['shared_genres'])}" if ref.get("shared_genres") else ""
                ref_list.append(
                    f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(77, 70, 53, 0.2); font-size: 0.86rem;'>"
                    f"  <span style='color: #e5e1e4; font-weight: 600;'>• {ref['title']} <span style='color: #99907c; font-weight: 400;'>({ref['user_rating']:g}/10){shared_str}</span></span>"
                    f"  <span style='font-family: monospace; color: #f2ca50; font-size: 0.82rem;'>{ref['similarity']:.2f} cosine sim</span>"
                    f"</div>"
                )
            refs_html = f"""
            <div style="margin-top: 1.25rem; background: #141316; border: 1px solid rgba(77, 70, 53, 0.3); border-radius: 10px; padding: 1rem;">
                <div style="font-size: 0.76rem; font-weight: 700; color: #f2ca50; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
                    Because You Liked (Positively Rated References):
                </div>
                {''.join(ref_list)}
            </div>
            """

        matches_html = ""
        matched_items = breakdown.get("matched_genres", []) + breakdown.get("matched_moods", [])
        if matched_items:
            badges = "".join([
                f"<span style='background: #2a2a2d; color: #e5e1e4; padding: 3px 8px; border-radius: 6px; font-size: 0.78rem; border: 1px solid rgba(77, 70, 53, 0.4);'>{m}</span>"
                for m in matched_items[:5]
            ])
            matches_html = f"""
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 1rem;">
                <span style="font-size: 0.78rem; font-weight: 700; color: #99907c; text-transform: uppercase; letter-spacing: 0.05em;">Strong Matches:</span>
                {badges}
            </div>
            """

        narrative_source = breakdown.get("narrative") or legacy_reasons
        narrative_items = "".join([f"<li style='margin-bottom: 4px;'>{n}</li>" for n in narrative_source])

        st.markdown(
            textwrap.dedent(f"""
            <div style="background: #1c1b1e; border: 1px solid rgba(77, 70, 53, 0.4); border-radius: 14px; padding: 1.5rem;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 0.5rem;">
                    <div style="font-family: 'Outfit'; font-size: 1.25rem; font-weight: 700; color: #f2ca50; display: flex; align-items: center; gap: 8px;">
                        <span class="material-symbols-outlined" style="color: #f2ca50;">insights</span>
                        <span>Recommendation Breakdown: Why ReelSense Curates "{title}"</span>
                    </div>
                    <span style="background: rgba(242, 202, 80, 0.15); color: #f2ca50; border: 1px solid rgba(242, 202, 80, 0.4); padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">
                        Strength: {strength}
                    </span>
                </div>
                <p style="font-size: 0.85rem; color: #99907c; margin: 0 0 1.25rem 0;">
                    Transparent signals derived from your TF-IDF content profile, MovieLens collaborative SVD factor matrix, and rating history.
                </p>

                <!-- Signal Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-bottom: 1.25rem;">
                    <!-- Content Match -->
                    <div style="background: #141316; border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 10px; padding: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.74rem; font-weight: 700; color: #99907c; text-transform: uppercase; letter-spacing: 0.06em;">Content Match</span>
                            <span style="font-family: monospace; font-size: 0.95rem; font-weight: 700; color: #f2ca50;">{c_pct}%</span>
                        </div>
                        <div style="font-family: monospace; color: #f2ca50; font-size: 0.85rem; letter-spacing: 1px; margin-bottom: 4px;">{c_bar}</div>
                        <div style="font-size: 0.72rem; color: #99907c;">TF-IDF vector alignment</div>
                    </div>

                    <!-- Taste Match -->
                    <div style="background: #141316; border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 10px; padding: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.74rem; font-weight: 700; color: #99907c; text-transform: uppercase; letter-spacing: 0.06em;">Taste Alignment</span>
                            <span style="font-family: monospace; font-size: 0.95rem; font-weight: 700; color: #e7c17c;">{t_pct}%</span>
                        </div>
                        <div style="font-family: monospace; color: #e7c17c; font-size: 0.85rem; letter-spacing: 1px; margin-bottom: 4px;">{t_bar}</div>
                        <div style="font-size: 0.72rem; color: #99907c;">Genre distribution affinity</div>
                    </div>

                    <!-- Collaborative Signal -->
                    <div style="background: #141316; border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 10px; padding: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.74rem; font-weight: 700; color: #99907c; text-transform: uppercase; letter-spacing: 0.06em;">Collaborative Signal</span>
                            <span style="font-family: monospace; font-size: 0.95rem; font-weight: 700; color: #d4af37;">{cl_pct}%</span>
                        </div>
                        <div style="font-family: monospace; color: #d4af37; font-size: 0.85rem; letter-spacing: 1px; margin-bottom: 4px;">{cl_bar}</div>
                        <div style="font-size: 0.72rem; color: #99907c;">Similar viewer consensus</div>
                    </div>
                </div>

                <!-- Mathematical Transparency Box -->
                <div style="background: rgba(242, 202, 80, 0.06); border: 1px solid rgba(242, 202, 80, 0.25); border-radius: 8px; padding: 0.85rem 1rem; font-size: 0.84rem; color: #d0c5af; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 1rem;">
                    <div>
                        <strong style="color: #f2ca50;">Score Breakdown:</strong>
                        0.4 × Content ({c_contrib:.2f}) + 0.6 × Collaborative ({cl_contrib:.2f})
                    </div>
                    <div style="font-family: monospace; font-weight: 700; color: #f2ca50; font-size: 0.95rem;">
                        Final Hybrid Score: {h_score:.2f}
                    </div>
                </div>

                <ul style="margin: 0; padding-left: 1.25rem; color: #d0c5af; font-size: 0.88rem; line-height: 1.7;">
                    {narrative_items}
                </ul>

                {refs_html}
                {matches_html}
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
