"""
ReelSense - Dedicated First-Time Taste Selection Onboarding (Phase 3)
Allows first-time users to select 3-4 movies they love to calibrate hybrid recommendation vectors.
"""

import streamlit as st
from src.services.recommendation_service import RecommendationService
from src.services.catalog import Catalog
from src.services import user_state
from src.utils.ui_helpers import render_html

FALLBACK_POSTER = "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=600&auto=format&fit=crop"


def render_onboarding_page():
    if "onboarding_selected_ids" not in st.session_state:
        st.session_state.onboarding_selected_ids = set()

    selected_ids = st.session_state.onboarding_selected_ids
    n_selected = len(selected_ids)
    can_proceed = n_selected >= 3

    # Header and instructions
    status_label = f"{n_selected} of 4 selected" if n_selected < 4 else f"{n_selected} selected (Goal reached!)"
    badge_color = "#f2ca50" if can_proceed else "#99907c"

    render_html(f"""
    <div style="text-align: center; max-width: 800px; margin: 1.5rem auto 1.5rem auto; padding: 0 1rem;">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(242, 202, 80, 0.12); border: 1px solid rgba(242, 202, 80, 0.3); padding: 4px 16px; border-radius: 9999px; margin-bottom: 0.8rem;">
            <span style="color: {badge_color}; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">
                ✨ Taste Calibration · {status_label}
            </span>
        </div>
        <h1 style="font-family: 'Outfit', sans-serif; font-size: 2.6rem; font-weight: 800; color: #e5e1e4; margin: 0 0 0.5rem 0; letter-spacing: -0.02em;">
            Pick 4 movies you love
        </h1>
        <p style="font-size: 1.05rem; color: #d0c5af; line-height: 1.6; margin: 0 auto; max-width: 600px;">
            Choose films you enjoy so we can personalize your recommendations. Select at least 3 to activate your custom hybrid taste vectors.
        </p>
    </div>
    """)

    # Action Toolbar: Count + Show My Picks + Skip
    col_l, col_btn_main, col_btn_skip, col_r = st.columns([2.5, 3.5, 2.5, 2.5], vertical_alignment="center")

    with col_btn_main:
        btn_label = f"✨ Show my picks ({n_selected})" if can_proceed else f"Select at least 3 ({n_selected}/3)"
        if st.button(
            btn_label,
            key="onboard_submit_picks",
            type="primary",
            disabled=not can_proceed,
            use_container_width=True
        ):
            # Save selected movies as 5-star ratings and complete onboarding
            user_state.complete_onboarding(list(selected_ids))
            # Sync session state
            st.session_state.ratings = user_state.get_ratings()
            st.session_state.onboarding_completed = True
            st.session_state.onboarding_skipped = False
            st.session_state.current_page = "home"
            st.rerun()

    with col_btn_skip:
        if st.button(
            "Skip for now →",
            key="onboard_skip_btn",
            help="Explore trending films without personal ratings",
            use_container_width=True
        ):
            user_state.skip_onboarding()
            st.session_state.onboarding_skipped = True
            st.session_state.onboarding_completed = False
            st.session_state.current_page = "home"
            st.rerun()

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Search Catalog Section
    st.markdown("""
    <div style="max-width: 700px; margin: 0 auto 1.5rem auto;">
    """, unsafe_allow_html=True)
    search_q = st.text_input(
        "Search full catalog for other favorites:",
        placeholder="Search by title, director, or keyword (e.g. Inception, Nolan, animation)...",
        key="onboard_search_input"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # If search active, show search results
    if search_q and search_q.strip():
        search_results = Catalog.search_movies(search_q.strip(), limit=12)
        st.markdown(f"<h3 style='font-family: Outfit; font-size: 1.25rem; color: #f2ca50; margin: 1rem 0;'>Search Results for '{search_q}'</h3>", unsafe_allow_html=True)
        if not search_results:
            st.info(f"No movies found matching '{search_q}'. Try a different title or select from the curated films below.")
        else:
            _render_movie_selection_grid(search_results, selected_ids, key_prefix="search")
            st.markdown("<div style='margin: 2rem 0; border-bottom: 1px solid rgba(77, 70, 53, 0.3);'></div>", unsafe_allow_html=True)

    # Curated 24 Popular Diverse Films
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <div>
            <h3 style="font-family: 'Outfit'; font-size: 1.35rem; font-weight: 700; color: #e5e1e4; margin: 0;">Popular Curated Selections</h3>
            <p style="font-size: 0.85rem; color: #99907c; margin: 2px 0 0 0;">Spanning diverse genres from cinema history</p>
        </div>
        <span style="font-size: 0.8rem; color: #f2ca50; font-weight: 600;">Click to select or deselect</span>
    </div>
    """, unsafe_allow_html=True)

    curated_movies = RecommendationService.get_onboarding_picks(24)
    _render_movie_selection_grid(curated_movies, selected_ids, key_prefix="curated")


def _render_movie_selection_grid(movies, selected_ids, key_prefix="grid"):
    """Render movies in responsive 6-column grid with selectable poster cards."""
    # 6 columns per row
    chunk_size = 6
    for row_start in range(0, len(movies), chunk_size):
        row_items = movies[row_start:row_start + chunk_size]
        cols = st.columns(len(row_items))

        for idx, movie in enumerate(row_items):
            m_id = movie["id"]
            title = movie["title"]
            year = movie.get("release_year", "")
            genres = " / ".join(movie.get("genres", [])[:2])
            poster = movie.get("poster_url") or FALLBACK_POSTER
            is_selected = m_id in selected_ids

            border_style = "2px solid #f2ca50" if is_selected else "1px solid rgba(77, 70, 53, 0.3)"
            glow_style = "box-shadow: 0 0 20px rgba(242, 202, 80, 0.45);" if is_selected else ""
            badge_html = """
            <div style="position: absolute; top: 8px; right: 8px; background: #f2ca50; color: #131315; font-weight: 800; font-size: 0.72rem; padding: 3px 8px; border-radius: 9999px; display: flex; align-items: center; gap: 4px; z-index: 5;">
                ✓ 5★ PICK
            </div>
            """ if is_selected else ""

            with cols[idx]:
                card_html = f"""
                <div style="background: #1c1b1e; border: {border_style}; {glow_style} border-radius: 12px; overflow: hidden; position: relative; margin-bottom: 8px; transition: transform 0.2s;">
                    <div style="position: relative; aspect-ratio: 2/3; overflow: hidden; background: #0e0e10;">
                        <img src="{poster}" style="width: 100%; height: 100%; object-fit: cover;" alt="{title}" onerror="this.src='{FALLBACK_POSTER}';"/>
                        {badge_html}
                    </div>
                    <div style="padding: 10px 8px;">
                        <div style="font-family: 'Outfit'; font-weight: 700; font-size: 0.88rem; color: #e5e1e4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{title}">{title}</div>
                        <div style="font-size: 0.72rem; color: #99907c; margin-top: 2px;">{year} · {genres}</div>
                    </div>
                </div>
                """
                render_html(card_html)

                btn_label = "✓ Deselect" if is_selected else "+ Select"
                btn_type = "primary" if is_selected else "secondary"

                def _toggle_selection(target_id=m_id):
                    sel = st.session_state.onboarding_selected_ids
                    if target_id in sel:
                        sel.remove(target_id)
                    else:
                        sel.add(target_id)
                    st.session_state.onboarding_selected_ids = sel

                st.button(
                    btn_label,
                    key=f"{key_prefix}_pick_{m_id}",
                    type=btn_type,
                    use_container_width=True,
                    on_click=_toggle_selection,
                )
