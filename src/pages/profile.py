"""
ReelSense - My Profile Page Module
"""

import streamlit as st
from src.config import DEFAULT_USER
from src.services.movie_service import MovieService

def render_profile_page():
    st.markdown(
        """
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">person</span>
                <span>User Curator Profile</span>
            </div>
            <h1 class="mood-page-title">
                My <span>Profile</span>
            </h1>
            <p class="mood-page-sub">
                Configure your cinematic preferences and taste profile to calibrate personalized vector recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    user = st.session_state.get("user_profile", DEFAULT_USER)

    st.markdown('<div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 2rem; max-width: 800px;">', unsafe_allow_html=True)

    # 1. Profile Name
    profile_name = st.text_input(
        "User Profile Name",
        value=user.get("name", "Film Curator"),
        key="prof_name_input"
    )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Favorite Genres Multi-Select
    all_genres = MovieService.get_all_genres()
    fav_genres = st.multiselect(
        "Favorite Movie Genres",
        options=all_genres,
        default=user.get("favorite_genres", ["Sci-Fi", "Action", "Drama"]),
        key="prof_genres_input"
    )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # 3. Preferred Language
        all_langs = MovieService.get_all_languages()
        current_lang = user.get("preferred_language", "English")
        lang_idx = all_langs.index(current_lang) if current_lang in all_langs else 0

        pref_language = st.selectbox(
            "Preferred Movie Language",
            options=all_langs,
            index=lang_idx,
            key="prof_lang_input"
        )

    with col2:
        # 4. Preferred Release Era
        eras = ["All Eras", "2020s & Newer", "2010s & Newer", "2000s & Classics"]
        current_era = user.get("preferred_era", "2010s & Newer")
        era_idx = eras.index(current_era) if current_era in eras else 2

        pref_era = st.selectbox(
            "Preferred Release Era",
            options=eras,
            index=era_idx,
            key="prof_era_input"
        )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # 5. Minimum Rating Preference
    min_rating_pref = st.slider(
        "Minimum Baseline Movie Rating",
        min_value=5.0,
        max_value=9.0,
        value=float(user.get("min_rating_pref", 7.5)),
        step=0.5,
        format="⭐ %.1f",
        key="prof_rating_input"
    )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Save Preferences Button
    st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
    if st.button("💾 Save Preferences", key="save_profile_btn"):
        st.session_state.user_profile = {
            "name": profile_name,
            "favorite_genres": fav_genres,
            "preferred_language": pref_language,
            "preferred_era": pref_era,
            "min_rating_pref": min_rating_pref
        }
        st.success("✅ Preferences updated successfully! Recommendations have been adjusted.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
