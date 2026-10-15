"""
ReelSense - Sense AI Engine Page Module
Natural language prompt-based vector discovery engine
"""

import streamlit as st
from src.services.recommendation_service import RecommendationService
from src.components.movie_card import render_movie_card
from src.pages.about import render_about_page
from src.utils.ui_helpers import render_html

PRESET_PROMPTS = [
    "slow sci-fi",
    "emotional drama",
    "funny movie",
    "action movie",
    "mind-bending thriller"
]


def render_sense_ai_page():
    tab_search, tab_arch = st.tabs(["✨ Natural Language Vector Search", "📐 ML Architecture & Technical Specs"])

    with tab_arch:
        render_about_page()

    with tab_search:
        render_html("""
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">psychology</span>
                <span>Sense AI Vector Alignment</span>
            </div>
            <h1 class="mood-page-title">
                Sense AI / <span>Natural Language Search</span>
            </h1>
            <p class="mood-page-sub">
                Describe a mood, theme, genre, or vibe (e.g., <em>emotional drama</em>, <em>slow sci-fi</em>, <em>funny movie</em>). ReelSense matches your prompt against plot summaries, genres, and movie tags using TF-IDF feature vectors and cosine similarity.
            </p>
        </div>
        """)

        # Search Input Bar
        current_prompt = st.session_state.get("sense_ai_prompt", st.session_state.get("global_search", ""))

        def _on_sense_ai_submit():
            st.session_state.sense_ai_prompt = st.session_state.get("sense_ai_input_field", "")

        col_input, col_submit = st.columns([8, 2], vertical_alignment="center")
        with col_input:
            st.markdown("""
            <style>
            /* Permanently Hide "Press Enter to apply" prompt */
            [data-testid="InputInstructions"],
            div[data-testid="InputInstructions"],
            span[data-testid="InputInstructions"],
            .stInputInstructions,
            .e1kt9bl72,
            div[class*="e1kt9bl72"],
            .eqy66r58,
            div[class*="eqy66r58"],
            .epumps80,
            span[class*="epumps80"],
            .stChatInputInstructions {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0 !important;
                width: 0 !important;
                position: absolute !important;
                left: -9999px !important;
                pointer-events: none !important;
            }
            .st-key-sense_ai_input_field div[data-baseweb="input"],
            .st-key-sense_ai_input_field > div > div {
                height: 46px !important;
                min-height: 46px !important;
                background: rgba(20, 19, 23, 0.96) !important;
                border: 1.5px solid rgba(212, 175, 55, 0.55) !important;
                border-radius: 9999px !important;
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            }
            .st-key-sense_ai_input_field div[data-baseweb="input"]:focus-within,
            .st-key-sense_ai_input_field > div > div:focus-within {
                border-color: #f2ca50 !important;
                box-shadow: 0 0 0 3px rgba(242, 202, 80, 0.22), 0 0 22px rgba(242, 202, 80, 0.45) !important;
                background: rgba(28, 27, 32, 0.98) !important;
            }
            .st-key-sense_ai_input_field input,
            .st-key-sense_ai_input_field input[type="text"],
            .st-key-sense_ai_input_field input[type="search"],
            .st-key-sense_ai_input_field input.react-aria-Input,
            .st-key-sense_ai_input_field [data-testid="stTextInputField"],
            .st-key-sense_ai_input_field input:focus,
            .st-key-sense_ai_input_field input:active,
            .st-key-sense_ai_input_field input[data-focused],
            .st-key-sense_ai_input_field input[data-focused="true"],
            .st-key-sense_ai_input_field div[data-testid="stTextInputRootElement"]:focus-within input {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                caret-color: #f2ca50 !important;
                font-size: 1.05rem !important;
                font-weight: 600 !important;
                letter-spacing: 0.015em !important;
                text-shadow: 0 0 1px rgba(255, 255, 255, 0.35) !important;
                padding-left: 1.25rem !important;
                padding-right: 1.25rem !important;
                background: transparent !important;
                opacity: 1 !important;
            }
            .st-key-sense_ai_input_field input::placeholder,
            .st-key-sense_ai_input_field input::-webkit-input-placeholder {
                color: #ede1c8 !important;
                -webkit-text-fill-color: #ede1c8 !important;
                opacity: 0.85 !important;
                font-size: 0.95rem !important;
                font-weight: 500 !important;
            }
            .st-key-sense_ai_submit_btn > button {
                height: 46px !important;
                min-height: 46px !important;
                border-radius: 9999px !important;
                font-weight: 800 !important;
                font-size: 0.95rem !important;
            }
            </style>
            """, unsafe_allow_html=True)
            user_prompt = st.text_input(
                "Sense AI Query",
                value=current_prompt,
                placeholder="e.g., slow sci-fi, emotional drama, funny movie...",
                label_visibility="collapsed",
                key="sense_ai_input_field",
                on_change=_on_sense_ai_submit
            )
        with col_submit:
            st.button("✨ Vector Align", key="sense_ai_submit_btn", on_click=_on_sense_ai_submit, type="primary")

        # Preset Prompts Row
        st.markdown("<p style='font-size: 0.8rem; color: #99907c; font-weight: 600; margin-top: 0.8rem; margin-bottom: 0.5rem;'>Or try a sample curator prompt:</p>", unsafe_allow_html=True)

        def _on_preset_click(preset_text):
            st.session_state.sense_ai_prompt = preset_text
            st.session_state.sense_ai_input_field = preset_text

        preset_cols = st.columns(len(PRESET_PROMPTS))
        for idx, preset in enumerate(PRESET_PROMPTS):
            is_active = (current_prompt == preset)
            with preset_cols[idx]:
                st.button(
                    preset,
                    key=f"preset_btn_{idx}",
                    help=preset,
                    on_click=_on_preset_click,
                    args=(preset,),
                    type="primary" if is_active else "secondary"
                )

        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

        # Search Results
        query = st.session_state.get("sense_ai_prompt", user_prompt)
        raw_matched = RecommendationService.search_by_prompt(query, limit=16)
        hidden_ids = set(st.session_state.get("not_interested", set()))
        matched_movies = [m for m in raw_matched if m["id"] not in hidden_ids][:12]

        render_html(f"""
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
        """)

        if matched_movies:
            rows = [matched_movies[i:i+4] for i in range(0, len(matched_movies), 4)]
            for r_idx, row in enumerate(rows):
                cols = st.columns(len(row))
                for c_idx, movie in enumerate(row):
                    with cols[c_idx]:
                        render_movie_card(movie, key_prefix=f"sense_ai_{r_idx}_{c_idx}")
                st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
        else:
            render_html(f"""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 3rem 1.5rem; text-align: center; margin-top: 1rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="font-size: 2.8rem; margin-bottom: 0.5rem;">🔍</div>
                <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: #e5e1e4; margin: 0 0 0.5rem 0;">No Direct Vector Matches for "{query}"</h3>
                <p style="font-size: 0.88rem; color: #99907c; max-width: 480px; margin: 0 auto; line-height: 1.6;">
                    Try a broader thematic prompt such as <em>"slow sci-fi"</em>, <em>"emotional drama"</em>, or <em>"mind-bending thriller"</em> to match MovieLens plot vectors and curator tags.
                </p>
            </div>
            """)
