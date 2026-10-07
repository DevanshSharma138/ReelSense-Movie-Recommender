"""
ReelSense - Onboarding Banner Component (Phase 3)
Lightweight, dismissible banner shown when the user has fewer than 3 ratings.
Directs the user toward movies they can rate to unlock hybrid recommendations.
"""

import streamlit as st
from src.utils.ui_helpers import render_html


def render_onboarding_banner():
    ratings = st.session_state.get("ratings", {})
    n_ratings = len(ratings)

    # Automatically hide if the user has unlocked personalized hybrid recommendations (>= 3 ratings)
    if n_ratings >= 3:
        return

    # Respect user dismissal
    if st.session_state.get("onboarding_dismissed", False):
        return

    needed = 3 - n_ratings
    plural = "s" if needed != 1 else ""

    with st.container(key="onboarding_banner_card"):
        col_content, col_actions = st.columns([8.2, 3.8], vertical_alignment="center")

        with col_content:
            render_html(f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="background: rgba(242, 202, 80, 0.15); color: #f2ca50; border: 1px solid rgba(242, 202, 80, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">
                    ✨ First-Time Curation
                </span>
                <span style="font-size: 0.8rem; color: #99907c; font-weight: 600;">{n_ratings} of 3 Rated</span>
            </div>
            <h3 style="font-family: 'Outfit'; font-size: 1.35rem; font-weight: 700; color: #e5e1e4; margin: 0 0 6px 0;">
                Rate 3 movies to unlock personalized picks
            </h3>
            <p style="font-size: 0.9rem; color: #d0c5af; line-height: 1.5; margin: 0;">
                ReelSense blends TF-IDF content similarity with SVD collaborative filtering. Rate <strong>{needed} more film{plural}</strong> to activate your personalized neural recommendation vectors.
            </p>
            """)

        def _on_onboard_rate_click():
            st.session_state.current_page = "discover-movies"

        def _on_onboard_dismiss_click():
            st.session_state.onboarding_dismissed = True

        with col_actions:
            col_btn1, col_btn2 = st.columns([1.5, 1.1], vertical_alignment="center")
            with col_btn1:
                st.button("⭐ Rate Films", key="onboard_browse_btn", use_container_width=True, on_click=_on_onboard_rate_click, type="primary")
            with col_btn2:
                st.button("✕ Dismiss", key="onboard_dismiss_btn", use_container_width=True, help="Dismiss onboarding banner", on_click=_on_onboard_dismiss_click)
