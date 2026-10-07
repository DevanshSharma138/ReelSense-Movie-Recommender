"""
ReelSense - Sensory Spectrum Mood Vault Matrix Component
"""

import streamlit as st
from src.config import MOODS
from src.services.recommendation_service import RecommendationService
from src.utils.ui_helpers import render_html

MOOD_EMOJIS = {
    "Happy": "☀️",
    "Relaxed": "🧘",
    "Thrilling": "⚡",
    "Romantic": "❤️",
    "Emotional": "💧",
    "Mind-blown": "🧠",
}


def render_mood_matrix():
    render_html("""
    <div class="section-header-box">
        <div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 2px;">
            Sensory Spectrum Discovery
        </div>
        <h2 class="section-header-title">Mood Vault Matrix</h2>
        <p class="section-header-sub">Explore by emotional resonance, color psychology, and cinematographic texture rather than standard genres.</p>
    </div>
    """)

    # 2 rows x 3 columns grid for 6 mood tiles
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)
    grid_cols = row1_cols + row2_cols

    for idx, mood in enumerate(MOODS):
        col = grid_cols[idx]
        m_id = mood["id"]
        label = mood["label"]
        icon = mood["icon"]
        emoji = MOOD_EMOJIS.get(m_id, "🎬")
        mood_cnt = RecommendationService.get_mood_count(m_id)
        count = f"{mood_cnt:,} Films"
        tagline = mood["tagline"]
        tags = mood.get("tags", [])

        tags_html = "".join([f'<span style="background: #131315; border: 1px solid rgba(153,144,124,0.25); color: #99907c; font-size: 0.72rem; padding: 2px 7px; border-radius: 4px; margin-right: 4px;">{t}</span>' for t in tags])

        with col:
            tile_html = f"""
            <div class="mood-tile">
                <div class="mood-tile-glow"></div>
                <div>
                    <div class="mood-tile-header">
                        <span class="mood-tile-icon" style="display: flex; align-items: center; gap: 6px;">
                            <span class="material-symbols-outlined" style="font-size: 22px;">{icon}</span>
                            <span style="font-size: 1.2rem;">{emoji}</span>
                        </span>
                        <span class="mood-tile-count">{count}</span>
                    </div>
                    <div class="mood-tile-title">{label}</div>
                    <div class="mood-tile-desc">{tagline}</div>
                </div>
                <div>
                    <div style="margin-bottom: 0.8rem;">{tags_html}</div>
                </div>
            </div>
            """
            render_html(tile_html)
            def _on_mood_matrix_click(target_m_id):
                st.session_state.selected_mood = target_m_id
                st.session_state.current_page = "mood-explorer"
                st.session_state.nav_route = "mood-explorer"

            st.button(
                f"Explore {m_id} Vault",
                key=f"mood_matrix_btn_{m_id}",
                use_container_width=True,
                type="primary",
                on_click=_on_mood_matrix_click,
                args=(m_id,),
            )
