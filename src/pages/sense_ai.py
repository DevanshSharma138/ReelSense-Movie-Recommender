"""
ReelSense - Sense AI Engine Page Module
Natural language prompt-based vector discovery engine
"""

import streamlit as st
from src.services.recommendation_service import RecommendationService
from src.components.movie_card import render_movie_card

PRESET_PROMPTS = [
    "Deep space sci-fi with Denis Villeneuve cinematography & heavy atmosphere",
    "70mm IMAX neo-noir psychological mystery with rain-slicked streets",
    "Poetic Japanese slow cinema set in Kyoto with warm paper lanterns",
    "Mind-bending temporal loops, quantum paradoxes, and plot twists",
    "Visceral edge-of-seat percussive action thriller with high stakes"
]

def render_sense_ai_page():
    st.markdown(
        """
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">psychology</span>
                <span>Sense AI Vector Alignment</span>
            </div>
            <h1 class="mood-page-title">
                Sense AI / <span>About the AI</span>
            </h1>
            <p class="mood-page-sub">
                Describe the exact visual atmosphere, emotional resonance, lighting style, or director aesthetic you are craving. Our vector embeddings will match your prompt to curated films.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Search Input Bar
    current_prompt = st.session_state.get("sense_ai_prompt", st.session_state.get("global_search", ""))
    
    col_input, col_submit = st.columns([8, 2])
    with col_input:
        user_prompt = st.text_input(
            "Sense AI Query",
            value=current_prompt,
            placeholder="e.g., Anxious neo-noir thriller in a rain-slicked futuristic city with warm amber sodium lights...",
            label_visibility="collapsed",
            key="sense_ai_input_field"
        )
    with col_submit:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        if st.button("✨ Vector Align", key="sense_ai_submit_btn"):
            st.session_state.sense_ai_prompt = user_prompt
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Preset Prompts Row
    st.markdown("<p style='font-size: 0.8rem; color: #99907c; font-weight: 600; margin-top: 0.8rem; margin-bottom: 0.5rem;'>Or try a sample curator prompt:</p>", unsafe_allow_html=True)
    
    preset_cols = st.columns(len(PRESET_PROMPTS))
    for idx, preset in enumerate(PRESET_PROMPTS):
        with preset_cols[idx]:
            if st.button(preset[:32] + "...", key=f"preset_btn_{idx}", help=preset):
                st.session_state.sense_ai_prompt = preset
                st.rerun()

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # Search Results
    query = st.session_state.get("sense_ai_prompt", user_prompt)
    matched_movies = RecommendationService.search_by_prompt(query, limit=12)

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <div>
                <h3 style="font-family: 'Outfit'; font-size: 1.3rem; font-weight: 700; color: #e5e1e4; margin: 0;">
                    Vector Match Results ({len(matched_movies)} Titles Found)
                </h3>
                <p style="font-size: 0.82rem; color: #99907c; margin: 2px 0 0 0;">
                    Sorted by cosine similarity with prompt: <em>"{query if query else 'All Masterworks'}"</em>
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if matched_movies:
        rows = [matched_movies[i:i+4] for i in range(0, len(matched_movies), 4)]
        for r_idx, row in enumerate(rows):
            cols = st.columns(len(row))
            for c_idx, movie in enumerate(row):
                with cols[c_idx]:
                    render_movie_card(movie, key_prefix=f"sense_ai_{r_idx}_{c_idx}")
            st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
    else:
        st.info("No matching films found. Try tweaking your prompt keyword.")
