"""
ReelSense - Sidebar Navigation Component
Aligned with latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import sys
import textwrap
import streamlit as st
from src.config import NAV_ITEMS

LOGO_URL = "https://lh3.googleusercontent.com/aida/AEtjO1UqatVwITSz6vkkkZbjM6qIgT8DocdolvZp77DmrmugKR9xP3in3RP6I-33riNVsEeEIt6Nbpj3izPXQFQzQ7CXimxHJVUlT3C6NpTtcwlx18CaJLANkJ9etwA6jKhM-UX74-vlDKkWEd842DUfFlSekT1P_j5P9spiQMHlR13Apg0JxTAuLtM-eg5pTwFwo0bL35FavIVZ5BRSREkHhVAIyL5Wl-9ngCcmMIUlFkvfYrdCr3fvDlm1Oy8"

def render_sidebar():
    with st.sidebar:
        # Branding Header
        st.markdown(
            textwrap.dedent(f"""
            <div class="reelsense-brand" onclick="window.location.reload();">
                <img src="{LOGO_URL}" alt="ReelSense Logo" style="height: 32px; width: auto; object-fit: contain;" />
                <div class="reelsense-brand-text">
                    <div class="reelsense-brand-title">Reel<span>Sense</span></div>
                    <div class="reelsense-brand-sub">Cinematic Curation</div>
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

        current_page = st.session_state.get("current_page", "home")

        # Map equivalent page IDs so active state matches
        page_aliases = {
            "home": "home",
            "discover": "discover-movies",
            "discover-movies": "discover-movies",
            "mood": "mood-explorer",
            "mood-explorer": "mood-explorer",
            "watchlist": "my-watchlist",
            "my-watchlist": "my-watchlist",
            "ratings": "my-ratings",
            "my-ratings": "my-ratings",
            "sense_ai": "about-the-ai",
            "about": "about-the-ai",
            "about-the-ai": "about-the-ai",
            "profile": "my-profile",
            "my-profile": "my-profile"
        }
        active_normalized = page_aliases.get(current_page, current_page)

        st.markdown('<div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 2rem;">', unsafe_allow_html=True)
        for item in NAV_ITEMS:
            item_id = item["id"]
            is_active = (active_normalized == item_id)
            label = item["label"]

            css_class = "nav-btn-active" if is_active else "nav-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_btn_{item_id}", use_container_width=True):
                st.session_state.current_page = item_id
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top: auto; padding-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # Runtime Engine Status Panel
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        st.markdown(
            textwrap.dedent(f"""
            <div style="background: #2a2a2c; border: 1px solid rgba(77, 70, 53, 0.35); border-radius: 10px; padding: 0.85rem; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 4px 14px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 0.6875rem; color: #d0c5af; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">Runtime Engine</span>
                    <span style="position: relative; display: flex; width: 8px; height: 8px;">
                        <span style="position: absolute; display: inline-flex; height: 100%; width: 100%; border-radius: 9999px; background: #f2ca50; opacity: 0.75; animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;"></span>
                        <span style="position: relative; display: inline-flex; border-radius: 9999px; height: 8px; width: 8px; background: #f2ca50;"></span>
                    </span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; color: #e5e1e4; font-size: 0.875rem; font-weight: 500;">
                    <span class="material-symbols-outlined" style="font-size: 18px; color: #f2ca50;">terminal</span>
                    <span>Streamlit & Python {py_ver}</span>
                </div>
                <span style="font-size: 0.7rem; color: #e7c17c; font-weight: 500;">Hybrid Recommender Active</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 0.25rem 0.2rem 0.25rem; font-size: 0.72rem;">
                <span style="color: #99907c;">ReelSense Core Engine</span>
                <span style="color: #f2ca50; font-weight: 700;">v1.3 (Phase 3)</span>
            </div>
            <style>
            @keyframes ping {{
                75%, 100% {{ transform: scale(2); opacity: 0; }}
            }}
            </style>
            """).strip(),
            unsafe_allow_html=True
        )
