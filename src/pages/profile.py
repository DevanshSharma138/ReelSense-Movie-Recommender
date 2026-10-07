"""
ReelSense - My Profile Page Module
"""

import textwrap
import streamlit as st
from src.config import DEFAULT_USER
from src.services.movie_service import MovieService
from src.services import user_store

def render_profile_page():
    st.markdown(
        textwrap.dedent("""
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
        """).strip(),
        unsafe_allow_html=True
    )

    user = st.session_state.get("user_profile", DEFAULT_USER)

    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 2rem; max-width: 840px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
        """).strip(),
        unsafe_allow_html=True
    )

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
        updated_profile = {
            "name": profile_name,
            "favorite_genres": fav_genres,
            "preferred_language": pref_language,
            "preferred_era": pref_era,
            "min_rating_pref": min_rating_pref
        }
        st.session_state.user_profile = updated_profile
        user_store.save_profile(updated_profile)
        st.success("✅ Preferences updated successfully! Recommendations have been adjusted.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. TASTE PROFILE (Calculated from Actual Ratings)
    # ---------------------------------------------------------
    ratings = st.session_state.get("ratings", {})
    n_rated = len(ratings)

    st.markdown(
        textwrap.dedent("""
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2px;">
                Mathematical Aesthetic Signature
            </div>
            <h2 style="font-family: 'Outfit'; font-size: 1.5rem; font-weight: 700; color: #e5e1e4; margin: 0;">
                Your Taste Profile
            </h2>
            <p style="font-size: 0.85rem; color: #99907c; margin: 2px 0 0 0;">
                Derived in real-time from your actual subjective film evaluations and MovieLens feature vectors.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 2rem; max-width: 840px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
        """).strip(),
        unsafe_allow_html=True
    )

    if n_rated == 0:
        st.markdown(
            textwrap.dedent("""
            <div style="text-align: center; padding: 2rem 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
                <h4 style="font-family: var(--font-display); font-size: 1.15rem; color: #e5e1e4; margin-bottom: 0.5rem;">No Evaluation Data Recorded Yet</h4>
                <p style="font-size: 0.88rem; color: #99907c; max-width: 450px; margin: 0 auto 1.5rem auto; line-height: 1.6;">
                    Rate 3 films across the catalog to generate your weighted genre preference distribution and activate hybrid collaborative filtering.
                </p>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        col_c, _ = st.columns([4, 6])
        with col_c:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            if st.button("🔍 Discover Films to Rate", key="prof_empty_rate_btn"):
                st.session_state.current_page = "discover-movies"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        avg_rating = sum(ratings.values()) / n_rated

        # Weight genre preference using actual user ratings
        genre_weights = {}
        genre_counts = {}
        for mid, score in ratings.items():
            m = MovieService.get_movie_by_id(mid)
            if m:
                for g in m.get("genres", []):
                    genre_weights[g] = genre_weights.get(g, 0.0) + float(score)
                    genre_counts[g] = genre_counts.get(g, 0) + 1

        top_genre = max(genre_weights, key=genre_weights.get) if genre_weights else "Diverse"

        # Summary Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                textwrap.dedent(f"""
                <div style="background: var(--bg-surface-low); border: 1px solid rgba(77, 70, 53, 0.4); border-radius: 12px; padding: 1.1rem; text-align: center;">
                    <div style="font-size: 0.72rem; color: var(--text-outline); text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">Rated Titles</div>
                    <div style="font-family: 'Outfit'; font-size: 1.8rem; font-weight: 800; color: var(--primary-gold); margin-top: 4px;">{n_rated}</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                textwrap.dedent(f"""
                <div style="background: var(--bg-surface-low); border: 1px solid rgba(77, 70, 53, 0.4); border-radius: 12px; padding: 1.1rem; text-align: center;">
                    <div style="font-size: 0.72rem; color: var(--text-outline); text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">Mean Rating</div>
                    <div style="font-family: 'Outfit'; font-size: 1.8rem; font-weight: 800; color: var(--primary-gold); margin-top: 4px;">⭐ {avg_rating:.1f}</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                textwrap.dedent(f"""
                <div style="background: var(--bg-surface-low); border: 1px solid rgba(77, 70, 53, 0.4); border-radius: 12px; padding: 1.1rem; text-align: center;">
                    <div style="font-size: 0.72rem; color: var(--text-outline); text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">Dominant Genre</div>
                    <div style="font-family: 'Outfit'; font-size: 1.8rem; font-weight: 800; color: var(--primary-gold); margin-top: 4px;">{top_genre}</div>
                </div>
                """).strip(),
                unsafe_allow_html=True
            )

        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-family: var(--font-display); font-size: 1rem; font-weight: 700; color: #e5e1e4; margin-bottom: 0.8rem;'>Genre Preference Strength (Weighted by Ratings)</h4>", unsafe_allow_html=True)

        if genre_weights:
            max_w = max(genre_weights.values())
            sorted_genres = sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)[:6]

            for g, total_score in sorted_genres:
                c = genre_counts.get(g, 0)
                pct = int(round((total_score / max_w) * 100))
                bar_chars = "█" * max(1, int(round((total_score / max_w) * 12)))

                st.markdown(
                    textwrap.dedent(f"""
                    <div style="margin-bottom: 0.85rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 600; color: #e5e1e4; font-size: 0.88rem;">{g} <span style="font-family: monospace; color: #f2ca50; font-size: 0.8rem; margin-left: 6px;">{bar_chars}</span></span>
                            <span style="font-size: 0.78rem; color: #99907c;">{total_score:.1f} pts ({c} film{'s' if c != 1 else ''})</span>
                        </div>
                        <div style="width: 100%; height: 6px; background: #2a2a2d; border-radius: 3px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #f2ca50, #d4af37);"></div>
                        </div>
                    </div>
                    """).strip(),
                    unsafe_allow_html=True
                )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 3. NOT INTERESTED EXCLUSIONS MANAGEMENT
    # ---------------------------------------------------------
    not_interested_set = set(st.session_state.get("not_interested", set()))
    n_hidden = len(not_interested_set)

    st.markdown(
        textwrap.dedent(f"""
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2px;">
                Negative Feedback Filter
            </div>
            <h2 style="font-family: 'Outfit'; font-size: 1.5rem; font-weight: 700; color: #e5e1e4; margin: 0;">
                Excluded Films ({n_hidden})
            </h2>
            <p style="font-size: 0.85rem; color: #99907c; margin: 2px 0 0 0;">
                Films marked as "Not Interested" are strictly excluded from all personalized recommendations and carousels.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; max-width: 840px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
        """).strip(),
        unsafe_allow_html=True
    )

    if n_hidden == 0:
        st.markdown(
            textwrap.dedent("""
            <p style="color: #99907c; font-size: 0.88rem; margin: 0; line-height: 1.6;">
                No films are currently excluded. Click the <strong>🚫</strong> button on any movie card or details page to hide titles you don't wish to see.
            </p>
            """).strip(),
            unsafe_allow_html=True
        )
    else:
        for hid in sorted(list(not_interested_set)):
            hm = MovieService.get_movie_by_id(hid)
            h_title = hm["title"] if hm else f"Movie #{hid}"
            h_year = hm.get("release_year", "") if hm else ""
            h_genres = ", ".join(hm.get("genres", [])) if hm else ""

            col_info, col_act = st.columns([8, 2])
            with col_info:
                st.markdown(
                    textwrap.dedent(f"""
                    <div style="padding: 6px 0;">
                        <span style="font-weight: 600; color: #e5e1e4; font-size: 0.9rem;">{h_title}</span>
                        <span style="color: #99907c; font-size: 0.8rem; margin-left: 6px;">({h_year}) · {h_genres}</span>
                    </div>
                    """).strip(),
                    unsafe_allow_html=True
                )
            with col_act:
                if st.button("↩️ Restore", key=f"restore_hidden_{hid}", use_container_width=True):
                    not_interested_set.remove(hid)
                    st.session_state.not_interested = not_interested_set
                    user_store.save_not_interested(not_interested_set)
                    st.toast(f"Restored '{h_title}' to recommendations", icon="↩️")
                    st.rerun()

        st.markdown("<div style='margin-top: 1.25rem; border-top: 1px solid rgba(77, 70, 53, 0.3); padding-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("🔄 Reset All Excluded Films", key="reset_all_not_interested_btn"):
            st.session_state.not_interested = set()
            user_store.save_not_interested(set())
            st.toast("Reset all exclusions. All films restored.", icon="🔄")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
