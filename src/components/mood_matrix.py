"""
ReelSense - Sensory Spectrum Mood Vault Matrix Component
"""

import streamlit as st
from src.config import MOODS

def render_mood_matrix():
    st.markdown(
        """
        <div class="section-header-box">
            <div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 2px;">
                Sensory Spectrum Discovery
            </div>
            <h2 class="section-header-title">Mood Vault Matrix</h2>
            <p class="section-header-sub">Explore by emotional resonance, color psychology, and cinematographic texture rather than standard genres.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2 rows x 3 columns grid for 6 mood tiles
    row1_cols = st.columns(3)
    row2_cols = st.columns(3)

    grid_cols = row1_cols + row2_cols

    for idx, mood in enumerate(MOODS):
        col = grid_cols[idx]
        m_id = mood["id"]
        label = mood["label"]
        icon = mood["icon"]
        count = mood.get("count", "100+ Films")
        tagline = mood["tagline"]
        tags = mood.get("tags", [])

        tags_html = "".join([f'<span style="background: #131315; border: 1px solid rgba(153,144,124,0.25); color: #99907c; font-size: 0.72rem; padding: 2px 7px; border-radius: 4px; margin-right: 4px;">{t}</span>' for t in tags])

        with col:
            st.markdown(
                f"""
                <div class="mood-tile">
                    <div class="mood-tile-glow"></div>
                    <div>
                        <div class="mood-tile-header">
                            <span class="mood-tile-icon">{icon}</span>
                            <span class="mood-tile-count">{count}</span>
                        </div>
                        <div class="mood-tile-title">{label}</div>
                        <div class="mood-tile-desc">{tagline}</div>
                    </div>
                    <div>
                        <div style="margin-bottom: 0.8rem;">{tags_html}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<div class="gold-btn" style="margin-top: -8px; margin-bottom: 1.2rem;">', unsafe_allow_html=True)
            if st.button(f"Explore {m_id} Vault", key=f"mood_matrix_btn_{m_id}"):
                st.session_state.selected_mood = m_id
                st.session_state.current_page = "mood"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
