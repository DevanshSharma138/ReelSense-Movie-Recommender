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
    {"id": "my-ratings", "label": "⭐ Ratings", "route": "my-ratings"},
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
    user = st.session_state.get("user_profile", {})
    user_name = user.get("name", "Film Curator")
    current_page = st.session_state.get("current_page", "home")
    active_normalized = PAGE_ALIASES.get(current_page, current_page)

    watchlist_count = len(st.session_state.get("watchlist", []))
    ratings_count = len(st.session_state.get("ratings", {}))

    with st.container(key="top_nav_container"):
        # =========================================================================
        # ROW 1: BRAND HEADER + SEARCH BAR + CURATOR AI + PROFILE
        # =========================================================================
        col_brand, col_search, col_curator, col_user = st.columns(
            [2.4, 5.2, 1.8, 1.6],
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
                st.text_input(
                    "Quick Search",
                    value=st.session_state.get("discover_search", ""),
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

        with col_curator:
            st.button(
                "✨ Curator AI",
                key="topbar_curator_ai_btn",
                use_container_width=True,
                help="Explore Sense AI Vector Matching",
                on_click=_on_nav_route_click,
                args=("about-the-ai",)
            )

        with col_user:
            profile_label = f"👤 {user_name[:12]}"
            st.button(
                profile_label,
                key="topbar_user_profile_btn",
                use_container_width=True,
                help=f"Curator Profile: {user_name}",
                on_click=_on_nav_route_click,
                args=("my-profile",)
            )

        # =========================================================================
        # DIVIDER: SUBTLE LUXURY GOLDEN GRADIENT HAIRLINE
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
                display_label = f"⭐ Ratings ({ratings_count})"
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
