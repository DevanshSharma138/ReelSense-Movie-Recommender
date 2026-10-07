"""
ReelSense - Premium Horizontal Top Navigation & Search Header Component
Obsidian (#0e0e10 / #141316) & Champagne Gold (#f2ca50 / #d4af37)
Completely replaces the vertical left sidebar with a sleek, responsive top navigation bar.
"""

import textwrap
import streamlit as st

LOGO_URL = "https://lh3.googleusercontent.com/aida/AEtjO1UqatVwITSz6vkkkZbjM6qIgT8DocdolvZp77DmrmugKR9xP3in3RP6I-33riNVsEeEIt6Nbpj3izPXQFQzQ7CXimxHJVUlT3C6NpTtcwlx18CaJLANkJ9etwA6jKhM-UX74-vlDKkWEd842DUfFlSekT1P_j5P9spiQMHlR13Apg0JxTAuLtM-eg5pTwFwo0bL35FavIVZ5BRSREkHhVAIyL5Wl-9ngCcmMIUlFkvfYrdCr3fvDlm1Oy8"
AVATAR_URL = "https://lh3.googleusercontent.com/aida-public/AB6AXuDItCNg058KG_NwgrV_LcD7qYcVPOhnWFOfQ6LWrz2lfrMb--8qPyTxOXfkElVzVHJX8eUHS80vR64MpXgLH2t8qTigWUAtCu116fvl5Z1VZWxXB8ZMBmNSzd-lh3-UU18vv9rabJGTz4fdFNMuP1FHJwMXxy6i2TjGjiSZoTCJIhQAHO-tZFdtOp9IkHJ--vfIAn3LV3RNmjK9cd8ovQxEXfP1r5cDjBwAbxAzGzmixlUNdUqpJGJK"

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
    """Renders the horizontal top navigation system above the page content."""
    user = st.session_state.get("user_profile", {})
    user_name = user.get("name", "Film Curator")
    current_page = st.session_state.get("current_page", "home")
    active_normalized = PAGE_ALIASES.get(current_page, current_page)

    watchlist_count = len(st.session_state.get("watchlist", []))
    ratings_count = len(st.session_state.get("ratings", {}))

    # =========================================================================
    # ROW 1: BRANDING HEADER + SEARCH + QUICK CURATOR ACTIONS
    # =========================================================================
    st.markdown('<div class="top-nav-wrapper">', unsafe_allow_html=True)
    
    col_brand, col_search, col_curator, col_user = st.columns([2.8, 5.0, 1.8, 1.4])

    with col_brand:
        # Brand logo and title
        st.markdown(
            textwrap.dedent(f"""
            <div class="reelsense-top-brand">
                <img src="{LOGO_URL}" alt="ReelSense Logo" style="height: 34px; width: auto; object-fit: contain;" />
                <div class="reelsense-brand-text">
                    <div class="reelsense-brand-title">Reel<span>Sense</span></div>
                    <div class="reelsense-brand-sub">Cinematic Curation</div>
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )
        if st.button("🏠 Home", key="top_brand_home_btn", help="Return to Home Screen", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()

    with col_search:
        current_search = st.session_state.get("global_search", "")
        search_input = st.text_input(
            "Quick Search",
            value=current_search,
            placeholder="Search films, directors, mood keywords, or AI vector prompts...",
            label_visibility="collapsed",
            key="topbar_global_search_input"
        )
        if search_input != current_search:
            st.session_state.global_search = search_input
            st.session_state.discover_search = search_input
            if search_input.strip():
                st.session_state.current_page = "discover-movies"
                st.rerun()

    with col_curator:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        if st.button("✨ Curator AI", key="topbar_curator_ai_btn", use_container_width=True, help="Explore Sense AI Vector Matching"):
            st.session_state.current_page = "about-the-ai"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_user:
        profile_label = f"👤 {user_name[:12]}"
        is_prof_active = (active_normalized == "my-profile")
        p_css = "top-nav-pill-active" if is_prof_active else "top-nav-pill"
        st.markdown(f'<div class="{p_css}">', unsafe_allow_html=True)
        if st.button(profile_label, key="topbar_user_profile_btn", use_container_width=True, help=f"Curator Profile: {user_name}"):
            st.session_state.current_page = "my-profile"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================================================================
    # ROW 2: HORIZONTAL NAVIGATION STRIP (Pill Buttons)
    # =========================================================================
    st.markdown('<div class="top-nav-ribbon">', unsafe_allow_html=True)

    nav_cols = st.columns(len(TOP_NAV_ITEMS))

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

        css_class = "top-nav-pill-active" if is_active else "top-nav-pill"

        with nav_cols[idx]:
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(display_label, key=f"top_nav_{item_id}", use_container_width=True):
                st.session_state.current_page = route
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
