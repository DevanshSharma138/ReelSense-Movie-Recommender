"""
ReelSense - Numbered Editorial Rankings Component (01 to 05 Trending Grid)
"""

import streamlit as st
from src.components.movie_card import render_movie_card

def render_trending_grid(ranked_movies):
    if not ranked_movies:
        return

    st.markdown(
        """
        <div style="background: rgba(28, 27, 30, 0.4); border-radius: 20px; padding: 2rem 1.5rem; margin-top: 2rem; margin-bottom: 2.5rem; border: 1px solid rgba(153, 144, 124, 0.2);">
            <div style="display: flex; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; margin-bottom: 1.5rem;">
                <div>
                    <div style="font-size: 0.72rem; color: #f2ca50; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;">Global Screening Velocity</div>
                    <h2 class="section-header-title" style="margin-top: 2px;">Trending Across ReelSense</h2>
                </div>
                <div style="background: #201f22; border: 1px solid rgba(153, 144, 124, 0.3); border-radius: 9999px; padding: 4px 12px; font-size: 0.75rem; color: #d0c5af; display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #f2ca50;"></span>
                    Live Stream Analytics
                </div>
            </div>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns(min(len(ranked_movies), 5))

    for idx, movie in enumerate(ranked_movies[:5]):
        rank_num = f"0{idx + 1}"
        m_id = movie["id"]
        title = movie["title"]
        director = movie.get("director", "Cinema Masterwork")
        growth = movie.get("trending_growth", "+25% this week")
        poster_url = movie.get("poster_url", "")

        with cols[idx]:
            st.markdown(
                f"""
                <div class="trending-rank-card">
                    <div class="trending-watermark-number">{rank_num}</div>
                    <div class="trending-card-content">
                """,
                unsafe_allow_html=True
            )
            render_movie_card(movie, key_prefix=f"trend_rank_{idx}")
            st.markdown(
                f"""
                        <div style="margin-top: 6px; display: flex; flex-direction: column;">
                            <span style="font-size: 0.72rem; color: #f2ca50; font-weight: 700;">{growth}</span>
                            <span style="font-size: 0.76rem; color: #99907c;">Dir. {director}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)
