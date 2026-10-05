"""
ReelSense - Topbar Search & Profile Header Component
Matching latest Stitch UI Reference (Obsidian & Champagne Gold)
"""

import streamlit as st

AVATAR_URL = "https://lh3.googleusercontent.com/aida-public/AB6AXuDItCNg058KG_NwgrV_LcD7qYcVPOhnWFOfQ6LWrz2lfrMb--8qPyTxOXfkElVzVHJX8eUHS80vR64MpXgLH2t8qTigWUAtCu116fvl5Z1VZWxXB8ZMBmNSzd-lh3-UU18vv9rabJGTz4fdFNMuP1FHJwMXxy6i2TjGjiSZoTCJIhQAHO-tZFdtOp9IkHJ--vfIAn3LV3RNmjK9cd8ovQxEXfP1r5cDjBwAbxAzGzmixlUNdUqpJGJK"

def render_topbar():
    user = st.session_state.get("user_profile", {})
    user_name = user.get("name", "Film Curator")

    col_tune, col_search, col_actions, col_notif, col_user = st.columns([0.6, 6.4, 2.0, 0.6, 0.6])

    with col_tune:
        if st.button("🎛️", key="topbar_filter_btn", help="Filter in Discover Movies"):
            st.session_state.current_page = "discover-movies"
            st.rerun()

    with col_search:
        current_search = st.session_state.get("global_search", "")
        search_input = st.text_input(
            "Search",
            value=current_search,
            placeholder="Search films, directors, mood keywords, or AI prompts...",
            label_visibility="collapsed",
            key="topbar_search_input"
        )

        if search_input != current_search:
            st.session_state.global_search = search_input
            st.session_state.discover_search = search_input
            if search_input.strip():
                st.session_state.current_page = "about-the-ai"
                st.rerun()

    with col_actions:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        if st.button("✨ Curator AI", key="topbar_curator_ai_btn", use_container_width=True):
            st.session_state.current_page = "about-the-ai"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_notif:
        st.markdown(
            """
            <div style="position: relative; width: 38px; height: 38px; border-radius: 50%; background: #201f22; border: 1px solid rgba(77, 70, 53, 0.35); display: flex; align-items: center; justify-content: center; cursor: pointer; color: #d0c5af;" title="Notifications">
                <span class="material-symbols-outlined" style="font-size: 18px;">notifications</span>
                <span style="position: absolute; top: 4px; right: 4px; width: 8px; height: 8px; background: #f2ca50; border-radius: 50%; border: 2px solid #0e0e10;"></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_user:
        st.markdown(
            f"""
            <div onclick="window.location.reload();" style="position: relative; width: 38px; height: 38px; border-radius: 50%; cursor: pointer;" title="Profile: {user_name}">
                <img src="{AVATAR_URL}" alt="Profile" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover; border: 1.5px solid rgba(212, 175, 55, 0.5);" />
                <span style="position: absolute; bottom: 0; right: 0; width: 9px; height: 9px; border-radius: 50%; background: #f2ca50; border: 2px solid #0e0e10;"></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
