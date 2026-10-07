"""
ReelSense - Premium Horizontal Top Navigation & Search Header Component
Obsidian (#0e0e10 / #141316) & Champagne Gold (#f2ca50 / #d4af37)
Completely replaces the vertical left sidebar with a sleek, compact, responsive top navigation bar.
"""

import textwrap
import streamlit as st

TOP_NAV_ITEMS = [
    {"id": "home", "label": "🎬 Home", "route": "home"},
    {"id": "discover-movies", "label": "🧭 Discover", "route": "discover-movies"},
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
}


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
            [2.6, 5.2, 1.8, 1.5],
            vertical_alignment="center"
        )

        with col_brand:
            # Cinematic Brand Display with inline SVG Reel Icon
            st.markdown(
                textwrap.dedent("""
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
                """).strip(),
                unsafe_allow_html=True
            )
            # Functional brand home button (tested via key="top_brand_home_btn", styled as invisible overlay)
            if st.button("ReelSense Home", key="top_brand_home_btn", help="Return to Home"):
                st.session_state.current_page = "home"
                st.rerun()

        with col_search:
            current_search = st.session_state.get("global_search", "")
            search_input = st.text_input(
                "Quick Search",
                value=current_search,
                placeholder="🔍 Search films, directors, genres, moods...",
                label_visibility="collapsed",
                key="topbar_global_search_input"
            )
            if search_input != current_search:
                st.session_state.global_search = search_input
                st.session_state.discover_search = search_input
                st.session_state.disc_search_input = search_input
                if search_input.strip():
                    st.session_state.current_page = "discover-movies"
                    st.rerun()

        with col_curator:
            if st.button("✨ Curator AI", key="topbar_curator_ai_btn", use_container_width=True, help="Explore Sense AI Vector Matching"):
                st.session_state.current_page = "about-the-ai"
                st.rerun()

        with col_user:
            profile_label = f"👤 {user_name[:12]}"
            if st.button(profile_label, key="topbar_user_profile_btn", use_container_width=True, help=f"Curator Profile: {user_name}"):
                st.session_state.current_page = "my-profile"
                st.rerun()

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
            is_active = (active_normalized == item_id)

            # Dynamic badge annotations
            if item_id == "my-watchlist" and watchlist_count > 0:
                display_label = f"🔖 Vault ({watchlist_count})"
            elif item_id == "my-ratings" and ratings_count > 0:
                display_label = f"⭐ Ratings ({ratings_count})"
            else:
                display_label = base_label

            with nav_cols[idx]:
                if st.button(
                    display_label,
                    key=f"top_nav_{item_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.current_page = route
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
