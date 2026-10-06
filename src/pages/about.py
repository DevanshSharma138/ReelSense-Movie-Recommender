"""
ReelSense - About the AI Page Module (Academic ML System Architecture)
"""

import streamlit as st

def render_about_page():
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="background: rgba(214, 173, 96, 0.15); border: 1px solid #D6AD60; color: #D6AD60; padding: 4px 12px; border-radius: 6px; display: inline-block; font-size: 0.8rem; font-weight: 700; margin-bottom: 8px;">
                B.Tech CSE (AI & ML) Capstone Project Architecture
            </div>
            <h1 style="font-size: 2rem; font-weight: 800; color: #F4EBDD; margin-bottom: 4px;">🤖 About ReelSense AI Engine</h1>
            <p style="font-size: 0.9rem; color: #A0A0A0;">Technical overview, recommendation algorithms, evaluation metrics, and system design.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. System Overview
    st.markdown(
        """
        <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h3 style="font-size: 1.2rem; font-weight: 700; color: #D6AD60; margin-bottom: 0.5rem;">1. System Overview</h3>
            <p style="font-size: 0.9rem; color: #D0D0D0; line-height: 1.6;">
                <strong>ReelSense</strong> is an AI-powered personalized movie discovery platform engineered to address the classic information overload problem in streaming catalog search. Combining natural language metadata processing with interactive user state modeling, ReelSense delivers transparent, explainable recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Recommendation Algorithms Breakdown (Grid)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; height: 100%;">
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">📄 Content-Based Filtering</h4>
                <p style="font-size: 0.85rem; color: #A0A0A0; line-height: 1.5;">
                    Extracts feature vectors from textual metadata (genres, synopsis, cast, director) using <strong>TF-IDF (Term Frequency-Inverse Document Frequency)</strong> vectorization and measures similarity using <strong>Cosine Similarity</strong>.
                </p>
                <div style="background: #181818; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 0.8rem; color: #D6AD60; border: 1px solid #282828;">
                    Similarity(A, B) = (A · B) / (||A|| ||B||)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; height: 100%;">
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">👥 Collaborative Filtering</h4>
                <p style="font-size: 0.85rem; color: #A0A0A0; line-height: 1.5;">
                    Analyzes user-item rating matrices using matrix factorization techniques like <strong>Singular Value Decomposition (SVD)</strong> and item-based cosine similarity to predict unobserved user ratings based on community behavior.
                </p>
                <div style="background: #181818; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 0.8rem; color: #D6AD60; border: 1px solid #282828;">
                    R ≈ U · Σ · Vᵀ
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            """
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; height: 100%;">
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">🔀 Hybrid Ensembling</h4>
                <p style="font-size: 0.85rem; color: #A0A0A0; line-height: 1.5;">
                    Combines Content-Based and Collaborative Filtering using a dynamic weighted linear combination:
                </p>
                <div style="background: #181818; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 0.8rem; color: #D6AD60; border: 1px solid #282828;">
                    Score = α · S_content + (1 - α) · S_collab
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; height: 100%;">
                <h4 style="font-size: 1.1rem; font-weight: 700; color: #F4EBDD; margin-bottom: 0.5rem;">💡 Explainable Recommendations</h4>
                <p style="font-size: 0.85rem; color: #A0A0A0; line-height: 1.5;">
                    Generates human-understandable natural language rationale explaining why a specific movie was selected, highlighting shared feature weights and user historical preference overlap.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3. Evaluation Metrics Section
    st.markdown(
        """
        <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h3 style="font-size: 1.2rem; font-weight: 700; color: #D6AD60; margin-bottom: 0.8rem;">📊 Model Evaluation Metrics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
                <div style="background: #292929; border: 1px solid #363636; padding: 12px; border-radius: 8px;">
                    <strong style="color: #F4EBDD; font-size: 0.9rem;">Precision@K</strong>
                    <p style="font-size: 0.8rem; color: #A0A0A0; margin-top: 4px;">Fraction of recommended items in Top-K that are relevant to the user.</p>
                </div>
                <div style="background: #292929; border: 1px solid #363636; padding: 12px; border-radius: 8px;">
                    <strong style="color: #F4EBDD; font-size: 0.9rem;">Recall@K</strong>
                    <p style="font-size: 0.8rem; color: #A0A0A0; margin-top: 4px;">Fraction of all relevant items successfully retrieved in Top-K.</p>
                </div>
                <div style="background: #292929; border: 1px solid #363636; padding: 12px; border-radius: 8px;">
                    <strong style="color: #F4EBDD; font-size: 0.9rem;">MAP & NDCG</strong>
                    <p style="font-size: 0.8rem; color: #A0A0A0; margin-top: 4px;">Evaluates ranking quality and position sensitivity of recommended items.</p>
                </div>
                <div style="background: #292929; border: 1px solid #363636; padding: 12px; border-radius: 8px;">
                    <strong style="color: #F4EBDD; font-size: 0.9rem;">Catalog Diversity</strong>
                    <p style="font-size: 0.8rem; color: #A0A0A0; margin-top: 4px;">Measures intra-list dissimilarity to prevent popularity bias bubble.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Tech Stack & Implementation Roadmap
    st.markdown(
        """
        <div style="background: #202020; border: 1px solid #363636; border-radius: 12px; padding: 1.5rem;">
            <h3 style="font-size: 1.2rem; font-weight: 700; color: #D6AD60; margin-bottom: 0.8rem;">🛠️ Tech Stack & Architecture Status</h3>
            <ul style="color: #F4EBDD; font-size: 0.9rem; line-height: 1.7; margin-bottom: 1rem;">
                <td><strong>Frontend Interface:</strong> Python, Streamlit, Custom Vanilla CSS</td>
                <td><strong>Data Processing & Analytics:</strong> Pandas, NumPy</td>
                <td><strong>ML & Recommendation Engine:</strong> Scikit-Learn (TF-IDF Content Vectorizer, TruncatedSVD Collaborative Filtering, Hybrid Ensemble)</td>
                <td><strong>Dataset:</strong> MovieLens ml-latest-small (600 active curated catalog films, 100,000+ real ratings, 610 users)</td>
            </ul>
            <div style="background: rgba(214, 173, 96, 0.08); border: 1px dashed #D6AD60; border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: #D6AD60;">
                📌 <strong>Live System Note:</strong> ReelSense runs an active hybrid recommender combining content-based TF-IDF cosine similarity with collaborative filtering matrix factorization. User ratings dynamically calibrate personalized recommendations, persistent taste profiles, and real-time movie exclusion.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
