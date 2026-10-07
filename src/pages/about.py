"""
ReelSense - About the AI Page Module (Academic ML System Architecture & Evaluation)
"""

import textwrap
import streamlit as st

def render_about_page():
    st.markdown(
        textwrap.dedent("""
        <div class="mood-page-header">
            <div class="mood-spectrum-badge">
                <span class="material-symbols-outlined" style="font-size: 16px;">psychology</span>
                <span>B.Tech CSE (AI & ML) Capstone Project Architecture</span>
            </div>
            <h1 class="mood-page-title">
                ReelSense <span>AI & ML Architecture</span>
            </h1>
            <p class="mood-page-sub">
                Comprehensive technical overview, hybrid recommendation algorithms, offline benchmark evaluations on MovieLens 100k, and system design specifications.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # 1. System Overview
    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
            <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: var(--primary-gold); margin: 0 0 0.5rem 0;">1. System Overview & Problem Formulation</h3>
            <p style="font-size: 0.92rem; color: var(--text-variant); line-height: 1.65; margin: 0;">
                <strong>ReelSense</strong> is an AI-powered personalized movie discovery platform engineered to address streaming catalog choice overload. Single-model recommenders suffer from fundamental trade-offs: pure collaborative filtering encounters cold-start isolation, while pure content-based filtering creates narrow over-specialization bubbles. ReelSense unifies textual TF-IDF semantic profiling with TruncatedSVD latent factor matrix factorization, backed by atomic state persistence, negative feedback filtering, and dynamic sensory mood calibration.
            </p>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # 2. Recommendation Algorithms Breakdown (Grid)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">📄</span>
                    <h4 style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; color: var(--text-on-surface); margin: 0;">Content-Based Filtering</h4>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-variant); line-height: 1.55; margin-bottom: 1rem;">
                    Extracts rich feature vectors from textual metadata (genres weighted 3x, director, cast, plot synopsis, and sensory tags) using <strong>TF-IDF vectorization</strong> with sublinear term-frequency scaling. Computes similarity against the user's rating-weighted centroid:
                </p>
                <div style="background: var(--bg-surface-high); padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; color: var(--primary-gold); border: 1px solid rgba(77, 70, 53, 0.4);">
                    S_content = (X · p_user) / (||X|| · ||p_user||)
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">👥</span>
                    <h4 style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; color: var(--text-on-surface); margin: 0;">Collaborative Filtering (SVD)</h4>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-variant); line-height: 1.55; margin-bottom: 1rem;">
                    Factorizes the mean-centered sparse interaction matrix of 610 MovieLens users across 9,742 titles using <strong>TruncatedSVD (k=50 concept dimensions)</strong>. Projects the active session user vector into latent factor space without retraining:
                </p>
                <div style="background: var(--bg-surface-high); padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; color: var(--primary-gold); border: 1px solid rgba(77, 70, 53, 0.4);">
                    S_collab = (u · Vᵀ) · V_cat
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">🔀</span>
                    <h4 style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; color: var(--text-on-surface); margin: 0;">Dynamic Hybrid Ensembling</h4>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-variant); line-height: 1.55; margin-bottom: 1rem;">
                    Combines normalized score distributions using an empirical linear parameter $\\alpha = 0.40$ (40% semantic content affinity, 60% collaborative community behavior):
                </p>
                <div style="background: var(--bg-surface-high); padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; color: var(--primary-gold); border: 1px solid rgba(77, 70, 53, 0.4);">
                    Score = 0.40 · Norm(S_content) + 0.60 · Norm(S_collab)
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            textwrap.dedent("""
            <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">💡</span>
                    <h4 style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; color: var(--text-on-surface); margin: 0;">Transparent Explainability</h4>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-variant); line-height: 1.55; margin-bottom: 1rem;">
                    Extracts transparent rationale from genuine data points: shared genres, user rating overlap, community velocity rank, and review consensus. Replaces opaque predictions with clear user justification:
                </p>
                <div style="background: var(--bg-surface-high); padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; color: var(--primary-gold); border: 1px solid rgba(77, 70, 53, 0.4);">
                    "Because you rated 'Toy Story' highly (Shared: Adventure)"
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # 3. Real Offline Benchmark Evaluation Table
    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 8px;">
                <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: var(--primary-gold); margin: 0;">
                    3. Offline Evaluation Benchmarks (MovieLens ml-latest-small)
                </h3>
                <span style="font-size: 0.8rem; color: var(--text-outline); background: var(--bg-surface-high); padding: 3px 10px; border-radius: 6px;">
                    50 Evaluated Users · Temporal 80/20 Split · Ground Truth ≥ 3.5★
                </span>
            </div>
            <p style="font-size: 0.88rem; color: var(--text-variant); line-height: 1.5; margin-bottom: 1rem;">
                Evaluated using <code>src/evaluation/evaluate.py</code> on real MovieLens user interaction history. Ground truth relevance defined as held-out ratings ≥ 3.5 / 5.0 (≥ 7.0 / 10).
            </p>
            <div class="eval-table-container">
                <table class="eval-table">
                    <thead>
                        <tr>
                            <th>Model Architecture</th>
                            <th>Precision@5</th>
                            <th>Precision@10</th>
                            <th>Recall@5</th>
                            <th>Recall@10</th>
                            <th>Hit Rate@10</th>
                            <th>Catalog Coverage</th>
                            <th>Intra-List Diversity</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Popularity Baseline</strong> (Cold-Start)</td>
                            <td>0.0720</td>
                            <td>0.0620</td>
                            <td>0.0294</td>
                            <td>0.0490</td>
                            <td>40.0%</td>
                            <td>5.3%</td>
                            <td>0.7714</td>
                        </tr>
                        <tr>
                            <td><strong>Content-Based</strong> (TF-IDF Cosine)</td>
                            <td>0.0800</td>
                            <td>0.0620</td>
                            <td>0.0459</td>
                            <td>0.0655</td>
                            <td>36.0%</td>
                            <td>22.8%</td>
                            <td>0.3219</td>
                        </tr>
                        <tr>
                            <td><strong>Collaborative</strong> (TruncatedSVD)</td>
                            <td><strong>0.2440</strong></td>
                            <td><strong>0.2040</strong></td>
                            <td><strong>0.1087</strong></td>
                            <td><strong>0.1647</strong></td>
                            <td>70.0%</td>
                            <td>26.0%</td>
                            <td>0.7798</td>
                        </tr>
                        <tr class="highlight">
                            <td>✨ <strong>ReelSense Hybrid (α=0.40)</strong></td>
                            <td>0.1840</td>
                            <td>0.1540</td>
                            <td>0.0906</td>
                            <td>0.1418</td>
                            <td><strong>76.0%</strong></td>
                            <td><strong>27.7%</strong></td>
                            <td>0.5236</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div style="background: rgba(242, 202, 80, 0.08); border-left: 3px solid var(--primary-gold); padding: 12px 16px; border-radius: 0 8px 8px 0; margin-top: 1rem;">
                <h5 style="color: var(--primary-gold); font-size: 0.9rem; font-weight: 700; margin: 0 0 4px 0;">Evaluation Insights & Trade-Off Analysis:</h5>
                <p style="font-size: 0.85rem; color: var(--text-variant); margin: 0; line-height: 1.55;">
                    While pure SVD collaborative filtering delivers higher precision on historical patterns, the <strong>ReelSense Hybrid model achieves the highest Hit Rate@10 (76.0%) and highest Catalog Coverage (27.7%)</strong>. Furthermore, it achieves an optimal <strong>Intra-List Diversity of 0.5236</strong>, preventing the narrow echo-chamber bubble of pure content-based filtering (0.3219) while maintaining personalized relevance.
                </p>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )

    # 4. Tech Stack & Implementation Roadmap
    st.markdown(
        textwrap.dedent("""
        <div style="background: var(--bg-surface-container); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
            <h3 style="font-family: var(--font-display); font-size: 1.25rem; font-weight: 700; color: var(--primary-gold); margin: 0 0 0.8rem 0;">4. System Specifications & Tech Stack</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 1rem;">
                <div style="background: var(--bg-surface-high); padding: 12px; border-radius: 8px; border: 1px solid rgba(77, 70, 53, 0.3);">
                    <div style="font-size: 0.72rem; color: var(--primary-gold); text-transform: uppercase; font-weight: 700;">Frontend & Presentation</div>
                    <div style="font-size: 0.88rem; color: var(--text-on-surface); font-weight: 600; margin-top: 2px;">Python · Streamlit · Custom Vanilla CSS</div>
                </div>
                <div style="background: var(--bg-surface-high); padding: 12px; border-radius: 8px; border: 1px solid rgba(77, 70, 53, 0.3);">
                    <div style="font-size: 0.72rem; color: var(--primary-gold); text-transform: uppercase; font-weight: 700;">ML & Vector Processing</div>
                    <div style="font-size: 0.88rem; color: var(--text-on-surface); font-weight: 600; margin-top: 2px;">Scikit-Learn · TF-IDF · TruncatedSVD</div>
                </div>
                <div style="background: var(--bg-surface-high); padding: 12px; border-radius: 8px; border: 1px solid rgba(77, 70, 53, 0.3);">
                    <div style="font-size: 0.72rem; color: var(--primary-gold); text-transform: uppercase; font-weight: 700;">Data Engineering & Matrices</div>
                    <div style="font-size: 0.88rem; color: var(--text-on-surface); font-weight: 600; margin-top: 2px;">Pandas · NumPy · SciPy CSR Matrices</div>
                </div>
                <div style="background: var(--bg-surface-high); padding: 12px; border-radius: 8px; border: 1px solid rgba(77, 70, 53, 0.3);">
                    <div style="font-size: 0.72rem; color: var(--primary-gold); text-transform: uppercase; font-weight: 700;">Dataset Benchmark</div>
                    <div style="font-size: 0.88rem; color: var(--text-on-surface); font-weight: 600; margin-top: 2px;">MovieLens ml-latest-small (100k Ratings)</div>
                </div>
            </div>
            <div style="background: rgba(214, 173, 96, 0.08); border: 1px dashed rgba(212, 175, 55, 0.5); border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; color: var(--secondary-gold); line-height: 1.55;">
                📌 <strong>State Persistence & Fallback:</strong> Real-time user ratings, watchlist items, and "Not Interested" exclusion sets persist atomically to <code>data/user_data.json</code> with Windows file-lock resilience. Offline 4-tier image fallback hierarchy (TMDB Poster -> Backdrop -> Local SVG -> Placeholder) ensures 100% resilient rendering without external network fragility.
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True
    )
