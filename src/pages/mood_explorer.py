"""
ReelSense - Mood Explorer: Sensory & Emotional Resonance
Faithful implementation of latest Stitch UI Reference (screen.png & code.html)
"""

import textwrap
import streamlit as st
from src.config import MOODS
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services import user_store
from src.components.movie_card import render_movie_card

MOOD_EMOJIS = {
    "Mind-blown": "🌀",
    "Heartwarming": "☀️",
    "Adrenaline": "⚡",
    "Chilling": "❄️",
    "Melancholy": "🌧️",
    "Thought-provoking": "🧘",
}

GENRE_OPTIONS = ["Surrealism", "Cyberpunk", "Mystery", "Drama", "Thriller", "Romance"]

def _reset_mood_filters_callback():
    st.session_state.selected_mood = "Mind-blown"
    st.session_state.mood_selected_genres = ["Surrealism", "Cyberpunk"]
    st.session_state.mood_min_rating = 8.5
    st.session_state.mood_score_slider = 8.5
    st.session_state.mood_sort_by = "Affinity Score"


def render_mood_explorer_page():
    # Initialize session states for Mood Explorer
    if "selected_mood" not in st.session_state:
        st.session_state.selected_mood = "Mind-blown"

    if "mood_selected_genres" not in st.session_state:
        st.session_state.mood_selected_genres = ["Surrealism", "Cyberpunk"]

    if "mood_min_rating" not in st.session_state:
        st.session_state.mood_min_rating = 8.5

    if "mood_sort_by" not in st.session_state:
        st.session_state.mood_sort_by = "Affinity Score"

    selected_mood_id = st.session_state.selected_mood
    current_mood_data = next((m for m in MOODS if m["id"] == selected_mood_id), MOODS[5])

    # ---------------------------------------------------------
    # PAGE HEADER
    # ---------------------------------------------------------
    st.markdown(
        textwrap.dedent(f"""
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">tune</span>
                <span>Atmospheric Spectrum Calibration</span>
            </div>
            <h1 class="mood-page-title">
                Mood Explorer: <span>Sensory & Emotional Resonance</span>
            </h1>
            <p class="mood-page-sub">
                Choose the exact emotional texture you want to experience tonight. ReelSense maps emotional vectors directly to cinematic compositions, tempo signatures, and color grading palettes.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # ACTIVE MOOD QUICK STATS ROW
    # ---------------------------------------------------------
    stat_acoustic = current_mood_data.get("acoustic", "Dynamic Ambient")
    stat_luminance = current_mood_data.get("luminance", "Low Key Noir")
    stat_pacing = current_mood_data.get("pacing", "Deliberate")
    mood_match_cnt = RecommendationService.get_mood_count(selected_mood_id)
    stat_matches = f"{mood_match_cnt:,} Available"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            textwrap.dedent(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-card-label">Acoustic Vector</div>
                    <div class="stat-card-val">{stat_acoustic}</div>
                </div>
                <span class="material-symbols-outlined" style="color: #e7c17c; font-size: 24px;">graphic_eq</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            textwrap.dedent(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-card-label">Luminance Bias</div>
                    <div class="stat-card-val">{stat_luminance}</div>
                </div>
                <span class="material-symbols-outlined" style="color: #e7c17c; font-size: 24px;">contrast</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            textwrap.dedent(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-card-label">Pacing Ratio</div>
                    <div class="stat-card-val">{stat_pacing}</div>
                </div>
                <span class="material-symbols-outlined" style="color: #e7c17c; font-size: 24px;">speed</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            textwrap.dedent(f"""
            <div class="stat-card">
                <div>
                    <div class="stat-card-label">Curated Matches</div>
                    <div class="stat-card-val highlight">{stat_matches}</div>
                </div>
                <span class="material-symbols-outlined" style="color: #f2ca50; font-size: 24px;">auto_awesome</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 1. DOMINANT SENSORY STATE (6 MOOD CARDS)
    # ---------------------------------------------------------
    col_label, col_badge = st.columns([8, 4])
    with col_label:
        st.markdown(
            textwrap.dedent("""
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.95rem; font-weight: 700; color: #e5e1e4; text-transform: uppercase; letter-spacing: 0.08em;">
                    1. Select Dominant Sensory State
                </span>
                <span style="font-size: 0.85rem; color: #99907c;">(Single selection required)</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with col_badge:
        st.markdown(
            textwrap.dedent(f"""
            <div style="display: flex; justify-content: flex-end;">
                <span style="background: rgba(242, 202, 80, 0.12); color: #f2ca50; border-radius: 9999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 700;">
                    Active Mood: <strong>{selected_mood_id}</strong>
                </span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    # 2 rows of 3 columns
    row1 = MOODS[:3]
    row2 = MOODS[3:]

    for row_moods in [row1, row2]:
        cols = st.columns(3)
        for idx, m in enumerate(row_moods):
            m_id = m["id"]
            is_active = (m_id == selected_mood_id)
            card_class = "sensory-card active" if is_active else "sensory-card"
            m_emoji = MOOD_EMOJIS.get(m_id, "🎬")
            m_icon = m.get("icon", "movie")

            with cols[idx]:
                check_html = """
                <div class="sensory-check">
                    <span class="material-symbols-outlined" style="font-size: 16px;">check</span>
                </div>
                """ if is_active else '<div style="width: 26px; height: 26px;"></div>'

                st.markdown(
                    textwrap.dedent(f"""
                    <div class="{card_class}">
                        <div>
                            <div class="sensory-card-header">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div class="sensory-icon-box">
                                        <span class="material-symbols-outlined" style="font-size: 24px;">{m_icon}</span>
                                        <span style="font-size: 18px; margin-left: 2px;">{m_emoji}</span>
                                    </div>
                                    <div>
                                        <div class="sensory-tier">{m['tier']}</div>
                                        <h3 class="sensory-name">{m['label']}</h3>
                                    </div>
                                </div>
                                {check_html}
                            </div>
                            <p class="sensory-desc">{m['tagline']}</p>
                        </div>
                        <div class="sensory-footer">
                            <div class="audio-wave">
                                <div class="audio-bar bar-1"></div>
                                <div class="audio-bar bar-2"></div>
                                <div class="audio-bar bar-3"></div>
                                <div class="audio-bar bar-4"></div>
                                <div class="audio-bar bar-5"></div>
                            </div>
                            <span class="sensory-freq">{RecommendationService.get_mood_count(m_id):,} Curated Films</span>
                        </div>
                    </div>
                    """).strip(),
                    unsafe_allow_html=True
                )
                
                # Selection Button
                btn_text = f"● Active: {m['label']}" if is_active else f"Select {m['label']}"
                if is_active:
                    st.markdown('<div class="gold-btn" style="margin-top: 6px; margin-bottom: 1.5rem;">', unsafe_allow_html=True)
                    st.button(btn_text, key=f"btn_mood_{m_id}", use_container_width=True, disabled=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="margin-top: 6px; margin-bottom: 1.5rem;">', unsafe_allow_html=True)
                    if st.button(btn_text, key=f"btn_mood_{m_id}", use_container_width=True):
                        st.session_state.selected_mood = m_id
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. CALIBRATION & GENRE VECTORS TOOLBAR
    # ---------------------------------------------------------
    st.markdown('<div class="calibration-box">', unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([8, 4])
    with col_t1:
        st.markdown(
            textwrap.dedent("""
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="material-symbols-outlined" style="color: #f2ca50; font-size: 20px;">filter_alt</span>
                <span style="font-size: 0.95rem; font-weight: 700; color: #e5e1e4; text-transform: uppercase; letter-spacing: 0.08em;">
                    2. Calibration & Genre Vectors
                </span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with col_t2:
        st.markdown('<div style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        st.button("↺ Reset All", key="mood_reset_filters_btn", on_click=_reset_mood_filters_callback)
        st.markdown('</div>', unsafe_allow_html=True)

    col_genres, col_slider = st.columns([7, 5])

    with col_genres:
        st.markdown("<div style='font-size: 0.72rem; color: #99907c; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-bottom: 8px;'>Compatible Genres (Multi-Select)</div>", unsafe_allow_html=True)
        
        selected_genres = st.session_state.mood_selected_genres
        genre_cols = st.columns(len(GENRE_OPTIONS))
        
        for g_idx, genre in enumerate(GENRE_OPTIONS):
            is_genre_active = genre in selected_genres
            btn_label = f"✓ {genre}" if is_genre_active else genre
            
            with genre_cols[g_idx]:
                css_class = "gold-btn" if is_genre_active else ""
                if css_class:
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(btn_label, key=f"chip_genre_{genre}", use_container_width=True):
                    if is_genre_active:
                        if len(selected_genres) > 1:
                            selected_genres.remove(genre)
                    else:
                        selected_genres.append(genre)
                    st.session_state.mood_selected_genres = selected_genres
                    st.rerun()
                if css_class:
                    st.markdown('</div>', unsafe_allow_html=True)

    with col_slider:
        current_slider_val = st.session_state.mood_min_rating
        st.markdown(
            textwrap.dedent(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.72rem; color: #99907c; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">Minimum Critical Score</span>
                <span style="font-size: 0.88rem; color: #f2ca50; font-weight: 800; display: flex; align-items: center; gap: 4px;">
                    <span class="material-symbols-outlined" style="font-size: 16px; color: #f2ca50;">star</span>
                    {current_slider_val:.1f}★
                </span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        slider_val = st.slider(
            "Minimum Critical Score",
            min_value=7.0,
            max_value=9.5,
            value=float(current_slider_val),
            step=0.1,
            label_visibility="collapsed",
            key="mood_score_slider"
        )
        if slider_val != current_slider_val:
            st.session_state.mood_min_rating = slider_val
            st.rerun()

    # Toolbar Bottom Action Row
    st.markdown("<div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(77, 70, 53, 0.25); display: flex; align-items: center; justify-content: space-between;'>", unsafe_allow_html=True)
    c_status, c_find = st.columns([8, 4])
    with c_status:
        st.markdown(
            textwrap.dedent("""
            <div style="display: flex; align-items: center; gap: 8px; color: #d0c5af; font-size: 0.85rem; height: 100%; padding-top: 8px;">
                <span class="material-symbols-outlined" style="color: #f2ca50; font-size: 18px;">psychology_alt</span>
                <span>Sense Neural Filter ready for recalculation</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with c_find:
        st.markdown('<div class="gold-btn" style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
        if st.button("🎬 Find Movies", key="btn_find_calibrated_movies", use_container_width=True):
            st.toast(f"Recalibrated neural vectors for {selected_mood_id} resonance!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 3. VECTOR ALIGNMENTS DYNAMIC RESULTS
    # ---------------------------------------------------------
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # Query matching films from RecommendationService
    all_movies = MovieService.get_all_movies()
    hidden_ids = set(st.session_state.get("not_interested", set()))
    filtered_movies = []

    # Filter films matching active mood or fallback (excluding not_interested)
    for m in all_movies:
        if m["id"] in hidden_ids:
            continue
        has_mood = selected_mood_id in m.get("moods", [])
        has_genre = any(g in m.get("genres", []) for g in st.session_state.mood_selected_genres)
        rating_ok = m.get("rating", 0) >= (st.session_state.mood_min_rating - 0.5)

        if has_mood or (has_genre and rating_ok):
            filtered_movies.append(m)

    # Sort based on Affinity Score or Critical Acclaim
    if st.session_state.mood_sort_by == "Critical Acclaim":
        filtered_movies.sort(key=lambda x: x.get("rating", 0), reverse=True)
    else:
        filtered_movies.sort(key=lambda x: x.get("mood_affinity", x.get("vector_match", 88)), reverse=True)

    available_catalog = [m for m in all_movies if m["id"] not in hidden_ids]
    results_to_display = filtered_movies[:4] if len(filtered_movies) >= 4 else (filtered_movies + available_catalog[:4])[:4]

    col_res_title, col_res_sort = st.columns([7, 5])
    with col_res_title:
        st.markdown(
            textwrap.dedent(f"""
            <div>
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #f2ca50; display: inline-block;"></span>
                    <span style="font-size: 0.72rem; color: #f2ca50; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;">Vector Alignments</span>
                </div>
                <h2 style="font-family: 'Outfit'; font-size: 1.5rem; font-weight: 700; color: #e5e1e4; margin: 0;">
                    Matches for <span style="color: #f2ca50; font-style: italic;">{selected_mood_id}</span> Resonance
                </h2>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
    with col_res_sort:
        st.markdown(
            textwrap.dedent(f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; height: 100%;">
                <span style="font-size: 0.8rem; color: #99907c;">{len(results_to_display)} Curated Screenings Found</span>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            is_aff = st.session_state.mood_sort_by == "Affinity Score"
            css = "gold-btn" if is_aff else ""
            if css: st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
            if st.button("Affinity Score", key="sort_affinity"):
                st.session_state.mood_sort_by = "Affinity Score"
                st.rerun()
            if css: st.markdown('</div>', unsafe_allow_html=True)
        with c_s2:
            is_crit = st.session_state.mood_sort_by == "Critical Acclaim"
            css = "gold-btn" if is_crit else ""
            if css: st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
            if st.button("Critical Acclaim", key="sort_critical"):
                st.session_state.mood_sort_by = "Critical Acclaim"
                st.rerun()
            if css: st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # 4 Film Cards Grid (Reusing consistent movie card component with poster fallbacks & actions)
    if results_to_display:
        grid_cols = st.columns(len(results_to_display))
        for idx, movie in enumerate(results_to_display):
            with grid_cols[idx]:
                render_movie_card(movie, key_prefix=f"mood_film_{movie['id']}_{idx}")
    else:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 3rem 1.5rem; text-align: center; margin-top: 1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="font-size: 2.8rem; margin-bottom: 0.5rem;">🎭</div>
                <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: #e5e1e4; margin: 0 0 0.5rem 0;">No Available Films for this Mood Calibration</h3>
                <p style="font-size: 0.88rem; color: #99907c; max-width: 480px; margin: 0 auto; line-height: 1.6;">
                    All titles matching this mood may have been marked as Not Interested or the rating threshold is set too high. Try lowering the Minimum Critical Score or resetting your filters.
                </p>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # 4. CURATION RATIONALE FOOTER
    # ---------------------------------------------------------
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        textwrap.dedent("""
        <div class="rationale-box">
            <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 320px;">
                <div class="rationale-icon">
                    <span class="material-symbols-outlined" style="font-size: 32px;">auto_awesome</span>
                </div>
                <div class="rationale-text">
                    <h4 class="rationale-title">Curation Rationale</h4>
                    <p class="rationale-desc">
                        These selections reflect high semantic coherence with non-linear storytelling, deep tonal complexity, and layered sonic landscapes calibrated for contemplative evening viewing.
                    </p>
                </div>
            </div>
        """).strip(),
        unsafe_allow_html=True
    )

    c_act1, c_act2 = st.columns([2, 2])
    with c_act1:
        if st.button("Export Calibration", key="btn_export_calibration", use_container_width=True):
            st.info(f"Calibration exported: {selected_mood_id} ({stat_matches}, {len(st.session_state.mood_selected_genres)} genres, {st.session_state.mood_min_rating}★ min)")

    with c_act2:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        if st.button("Save Selection Rail", key="btn_save_selection_rail", use_container_width=True):
            # Save all 4 films to user's watchlist
            current_wl = st.session_state.get("watchlist", [])
            for m in results_to_display:
                if m["id"] not in current_wl:
                    current_wl.append(m["id"])
            st.session_state.watchlist = current_wl
            user_store.save_watchlist(current_wl)
            st.toast("Saved 4 calibrated films to your Vault Watchlist! 🔖")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
