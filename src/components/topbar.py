"""
ReelSense - Premium Horizontal Top Navigation & Search Header Component
Obsidian (#0e0e10 / #141316) & Champagne Gold (#f2ca50 / #d4af37)
Completely replaces the vertical left sidebar with a sleek, compact, responsive top navigation bar.
"""

import streamlit as st
from src.utils.ui_helpers import render_html

TOP_NAV_ITEMS = [
    {"id": "home", "label": "🏠 Home", "route": "home"},
    {"id": "discover-movies", "label": "⏰ Discover", "route": "discover-movies"},
    {"id": "mood-explorer", "label": "🎭 Mood Explorer", "route": "mood-explorer"},
    {"id": "my-watchlist", "label": "🔖 Vault", "route": "my-watchlist"},
    {"id": "my-ratings", "label": "👍 Taste", "route": "my-ratings"},
    {"id": "about-the-ai", "label": "✨ Sense AI", "route": "about-the-ai"},
    {"id": "my-profile", "label": "👤 Profile", "route": "my-profile"},
    {"id": "about", "label": "ℹ️ Architecture", "route": "about"},
]

PAGE_ALIASES = {
    "home": "home",
    "home-discover": "home",
    "discover": "discover-movies",
    "discover-movies": "discover-movies",
    "collections": "discover-movies",
    "mood": "mood-explorer",
    "mood-explorer": "mood-explorer",
    "mood_explorer": "mood-explorer",
    "watchlist": "my-watchlist",
    "my-watchlist": "my-watchlist",
    "ratings": "my-ratings",
    "my-ratings": "my-ratings",
    "sense_ai": "about-the-ai",
    "about-the-ai": "about-the-ai",
    "profile": "my-profile",
    "my-profile": "my-profile",
    "settings": "my-profile",
    "about": "about",
    "architecture": "about",
    "capstone": "about",
    "movie_details": "movie_details",
}


def _on_nav_route_click(route):
    st.session_state.current_page = route


def _on_topbar_search_callback():
    q = st.session_state.get("topbar_search_input", "").strip()
    st.session_state.global_search = q
    st.session_state.discover_search = q
    st.session_state.disc_search_input = q
    st.session_state.current_page = "discover-movies"


def render_topbar():
    """Renders the compact horizontal top navigation system above page content."""
    current_page = st.session_state.get("current_page", "home")
    active_normalized = PAGE_ALIASES.get(current_page, current_page)

    watchlist_count = len(st.session_state.get("watchlist", []))
    ratings_count = len(st.session_state.get("ratings", {}))

    with st.container(key="top_nav_container"):
        # =========================================================================
        # ROW 1: BRAND HEADER + SEARCH BAR
        # =========================================================================
        col_brand, col_search = st.columns(
            [2.4, 8.6],
            vertical_alignment="center"
        )

        with col_brand:
            with st.container(key="top_brand_container"):
                render_html("""
                <div class="reelsense-top-brand">
                    <svg class="brand-reel-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="10" stroke="url(#goldGrad)" stroke-width="2"/>
                        <circle cx="12" cy="12" r="3" fill="#f2ca50"/>
                        <circle cx="12" cy="6" r="1.5" fill="#f2ca50"/>
                        <circle cx="12" cy="18" r="1.5" fill="#f2ca50"/>
                        <circle cx="6" cy="12" r="1.5" fill="#f2ca50"/>
                        <circle cx="18" cy="12" r="1.5" fill="#f2ca50"/>
                        <defs>
                            <linearGradient id="goldGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                                <stop stop-color="#f2ca50"/>
                                <stop offset="1" stop-color="#d4af37"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <div class="reelsense-brand-text">
                        <div class="reelsense-brand-title">Reel<span>Sense</span></div>
                        <div class="reelsense-brand-sub">Cinematic Curation</div>
                    </div>
                </div>
                """)
                st.button("ReelSense Home", key="top_brand_home_btn", help="Return to Home", on_click=_on_nav_route_click, args=("home",))

        with col_search:
            col_s_box, col_s_btn = st.columns([4.2, 1.2], vertical_alignment="center")
            with col_s_box:
                if "topbar_search_input" not in st.session_state:
                    st.session_state.topbar_search_input = st.session_state.get("discover_search", "")
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

                .st-key-topbar_search_input div[data-baseweb="input"],
                .st-key-topbar_search_input > div > div {
                    height: 46px !important;
                    min-height: 46px !important;
                    background: rgba(20, 19, 23, 0.96) !important;
                    border: 1.5px solid rgba(212, 175, 55, 0.55) !important;
                    border-radius: 9999px !important;
                    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3) !important;
                    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
                }
                .st-key-topbar_search_input div[data-baseweb="input"]:focus-within,
                .st-key-topbar_search_input > div > div:focus-within {
                    border-color: #f2ca50 !important;
                    box-shadow: 0 0 0 3px rgba(242, 202, 80, 0.22), 0 0 22px rgba(242, 202, 80, 0.45) !important;
                    background: rgba(28, 27, 32, 0.98) !important;
                }

                /* Pure Crisp White Text while Entering Text & Focused */
                .st-key-topbar_search_input input,
                .st-key-topbar_search_input input[type="text"],
                .st-key-topbar_search_input input[type="search"],
                .st-key-topbar_search_input input.react-aria-Input,
                .st-key-topbar_search_input [data-testid="stTextInputField"],
                .st-key-topbar_search_input input:focus,
                .st-key-topbar_search_input input:active,
                .st-key-topbar_search_input input[data-focused],
                .st-key-topbar_search_input input[data-focused="true"],
                div[data-testid="stTextInputRootElement"]:focus-within input,
                div[data-testid="stTextInputRootElement"] input,
                div[data-testid="stTextInput"] input {
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

                .st-key-topbar_search_input input::placeholder,
                .st-key-topbar_search_input input::-webkit-input-placeholder,
                div[data-testid="stTextInputRootElement"] input::placeholder,
                div[data-testid="stTextInputRootElement"] input::-webkit-input-placeholder {
                    color: #ede1c8 !important;
                    -webkit-text-fill-color: #ede1c8 !important;
                    opacity: 0.85 !important;
                    font-size: 0.95rem !important;
                    font-weight: 500 !important;
                }

                .st-key-topbar_search_submit_btn > button {
                    height: 46px !important;
                    min-height: 46px !important;
                    background: linear-gradient(135deg, #f2ca50 0%, #e5b93b 50%, #d4af37 100%) !important;
                    color: #0e0e10 !important;
                    border: none !important;
                    border-radius: 9999px !important;
                    font-weight: 800 !important;
                    font-size: 0.95rem !important;
                    letter-spacing: 0.04em !important;
                    box-shadow: 0 4px 18px rgba(242, 202, 80, 0.35) !important;
                    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                }
                .st-key-topbar_search_submit_btn > button:hover {
                    transform: translateY(-1px) scale(1.02) !important;
                    box-shadow: 0 6px 22px rgba(242, 202, 80, 0.5) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                st.text_input(
                    "Quick Search",
                    placeholder="🔍 Search films, directors, genres (e.g. Matrix, Toy Story)...",
                    label_visibility="collapsed",
                    key="topbar_search_input",
                    on_change=_on_topbar_search_callback
                )
            with col_s_btn:
                st.button(
                    "Search",
                    key="topbar_search_submit_btn",
                    use_container_width=True,
                    help="Search MovieLens Catalog",
                    on_click=_on_topbar_search_callback,
                    type="primary"
                )

        # =========================================================================
        # DIVIDER: SUBTLE LUXURY GOLDEN GRADIENCE
        # =========================================================================
        st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)

        # =========================================================================
        # ROW 2: HORIZONTAL NAVIGATION STRIP (Pill Buttons)
        # =========================================================================
        st.markdown('<div class="top-nav-ribbon">', unsafe_allow_html=True)

        nav_cols = st.columns(len(TOP_NAV_ITEMS), vertical_alignment="center")

        for idx, item in enumerate(TOP_NAV_ITEMS):
            item_id = item["id"]
            base_label = item["label"]
            route = item["route"]
            target_canonical = PAGE_ALIASES.get(route, route)
            is_active = (active_normalized == target_canonical)

            # Dynamic badge annotations
            if item_id == "my-watchlist" and watchlist_count > 0:
                display_label = f"🔖 Vault ({watchlist_count})"
            elif item_id == "my-ratings" and ratings_count > 0:
                display_label = f"👍 Taste ({ratings_count})"
            else:
                display_label = base_label

            with nav_cols[idx]:
                st.button(
                    display_label,
                    key=f"top_nav_{item_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    on_click=_on_nav_route_click,
                    args=(route,)
                )

        st.markdown('</div>', unsafe_allow_html=True)
