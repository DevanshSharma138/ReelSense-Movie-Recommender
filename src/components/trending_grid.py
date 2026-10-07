"""
ReelSense - Numbered Editorial Rankings Component (01 to 05 Trending Grid)
"""

import streamlit as st
from src.components.movie_card import render_movie_card
from src.utils.ui_helpers import render_html


def render_trending_grid(ranked_movies):
    if not ranked_movies:
        return

    render_html("""
    <div style="margin-top: 2rem; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div>
                <div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 3px;">Global Screening Velocity</div>
                <h2 class="section-header-title" style="font-family: 'Outfit', sans-serif; font-size: 1.45rem; font-weight: 700; color: #e5e1e4; margin: 0; letter-spacing: -0.01em;">Trending Across ReelSense</h2>
            </div>
            <div style="background: #201f22; border: 1px solid rgba(153, 144, 124, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.75rem; color: #d0c5af; display: flex; align-items: center; gap: 6px;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background: #f2ca50; display: inline-block;"></span>
                <span>Community Velocity</span>
            </div>
        </div>
    </div>
    """)

    n_items = min(len(ranked_movies), 5)
    cols = st.columns(n_items if n_items > 0 else 1)

    for idx, movie in enumerate(ranked_movies[:n_items]):
        rank_num = f"0{idx + 1}"
        with cols[idx]:
            render_html(f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 800; color: #f2ca50; line-height: 1;">{rank_num}</span>
                <span style="font-size: 0.72rem; color: #99907c; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Rank</span>
            </div>
            """)
            render_movie_card(movie, key_prefix=f"trend_rank_{idx}")
