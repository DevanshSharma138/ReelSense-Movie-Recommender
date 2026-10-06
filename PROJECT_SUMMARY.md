# ReelSense — Executive Project Summary & Viva Reference

> **Target Audience:** B.Tech CSE (AI & ML) Capstone Review Committee, Viva Examiners, and Technical Evaluators  
> **Project:** ReelSense Movie Recommendation Platform  
> **Status:** Phase 4 Completed · Fully Functional · Evaluated  

---

## 1. Executive Summary & Problem Formulation
ReelSense is an end-to-end personalized movie discovery system designed to alleviate streaming choice fatigue. Unlike toy recommenders that rely on hardcoded samples or isolated offline notebooks, ReelSense bridges production ML algorithms with an interactive, persistent web application. It combines real **MovieLens 100k data** with a dual-branch hybrid model (TF-IDF semantic analysis + TruncatedSVD collaborative matrix factorization), transparent explainability signals, atomic user state persistence, negative feedback exclusion, and a dark obsidian/champagne-gold aesthetic.

---

## 2. Final System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER (STREAMLIT)                  │
│  - Home / Premiere Spotlight        - Mood Explorer (Sensory Spectrum) │
│  - Discover & Multi-Facet Filters   - My Ratings & Dynamic Taste Graph │
│  - Sense AI (Vector NLP Search)     - My Watchlist & Excluded Manager  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Session State Event Stream
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          SERVICE ORCHESTRATION LAYER                   │
│  - RecommendationService (Public API, Modes, Real Explanations)        │
│  - MovieService (Search, Filter, Facet Aggregation)                    │
│  - CatalogService (600 Catalog Items, Bayesian Ranking, 4-Tier Fallback)│
│  - UserStore (Atomic JSON Persistence, WinError 32 Lock Resilience)    │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│        CONTENT-BASED ENGINE          │ │    COLLABORATIVE ENGINE       │
│ - Document Composition:              │ │ - Matrix: 610 users x 9,742   │
│   Genres (3x), Moods, Director,      │ │   items (mean-centered)       │
│   Cast, User Tags, Synopses          │ │ - TruncatedSVD (k=50 factors) │
│ - TfidfVectorizer (unigram + bigram) │ │ - V_cat catalog projection    │
│ - Rating-weighted user taste centroid│ │ - Active session fold-in      │
└──────────────────┬───────────────────┘ └───────────────┬───────────────┘
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      HYBRID ENSEMBLE COMBINER                          │
│          Score = 0.40 * Norm(S_content) + 0.60 * Norm(S_collab)        │
│          Cold-Start Fallback: Active when ratings < 3                  │
│          Exclusion Filter: Mask out movie IDs in 'Not Interested'      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Major Components
1. **Hybrid ML Engine (`src/services/hybrid_model.py`):**
   - Implements two complementary learning branches:
     - **Content branch:** Measures textual and categorical affinity using cosine similarity between the user's rating-weighted preference vector and movie TF-IDF embeddings.
     - **Collaborative branch:** Projects the user's ratings into a 50-dimensional latent concept space learned from 610 MovieLens users via TruncatedSVD.
   - Combines normalized score vectors using parameter $\alpha = 0.40$.
2. **Catalog & Image Manager (`src/services/catalog.py`, `src/utils/image_utils.py`):**
   - Curates the top 600 movies by Bayesian review volume.
   - Implements a resilient 4-tier image hierarchy (TMDB Poster -> TMDB Backdrop -> Procedural Local SVG Vector Fallback -> Placeholder), guaranteeing zero broken layout dependency.
3. **User State Persistence (`src/services/user_store.py`):**
   - Provides thread-safe, atomic JSON persistence into `data/user_data.json`.
   - Employs temporary write-and-replace mechanics with exponential backoff retry to defeat Windows transient file locking (`WinError 32`).
4. **Interactive Feedback Subsystem:**
   - **Positive:** Interactive rating sliders with real-time UI feedback.
   - **Negative ("Not Interested"):** Instant exclusion action (`🚫`) that removes movies from recommendations across restarts.
5. **Evaluation Suite (`src/evaluation/evaluate.py`):**
   - Evaluates offline Precision@K, Recall@K, HitRate@10, Catalog Coverage, and Genre Diversity.

---

## 4. Complete Data & Recommendation Flows

### A. The Recommendation Flow
1. User interacts with ReelSense (fresh user has 0 ratings).
2. App queries `RecommendationService.get_recommended_for_user()`.
3. If user ratings count $< 3$:
   - Returns **Cold-Start rail**: Bayesian-weighted community masterworks and trending velocity titles.
   - UI displays onboarding progress banner: *"Rate 3 movies to unlock personalized picks"*.
4. When ratings count $\ge 3$:
   - Model computes the user's content centroid $\mathbf{p}_{\text{user}}$ and projects interaction vector $\mathbf{u}$ onto SVD item factors $\mathbf{V}_{\text{cat}}$.
   - Ensembles normalized scores: $S = 0.40 \cdot S_{\text{content}} + 0.60 \cdot S_{\text{collab}}$.
   - Filters out already-rated items and movies marked **Not Interested**.
   - Generates data-grounded explanations (e.g., *"Because you rated 'Toy Story' highly"*).

### B. The User Feedback Loop
```
[User clicks 'Not Interested' 🚫] 
   │
   ├─► Session State updated: st.session_state.not_interested.add(movie_id)
   │
   ├─► Atomic Persistence: user_store.save_not_interested() -> data/user_data.json
   │
   └─► Rerun Triggered:
         - Card displays 'NOT INTERESTED' badge
         - Recommendation engine receives hidden_ids=[movie_id]
         - Item strictly omitted from all recommendation rails across reboots
```

---

## 5. Important Design Decisions & Justifications

| Design Decision | Alternative Considered | Rationale |
| :--- | :--- | :--- |
| **Streamlit + Custom Vanilla CSS** | React / Next.js + FastAPI | Single-language Python stack keeps ML inference in-memory without network serialization latency or multi-process synchronization overhead. Custom CSS delivers streaming-grade aesthetics. |
| **Hybrid Linear Ensembling ($\alpha=0.4$)** | Deep Neural Recommender / NCF | TruncatedSVD + TF-IDF provides instant sub-10ms inference, zero cold-start GPU requirements, and transparent feature attribution for explainability. |
| **Atomic JSON Persistence** | SQLite / PostgreSQL | Zero external database installation required for evaluation; atomic file replacement ensures zero corruption without requiring external server processes. |
| **Procedural Local SVG Image Fallback** | Hardcoded external placeholders | External placeholder CDNs can be rate-limited, fail offline, or be blocked by ad-blockers. Local SVG data URIs render instantly with matching obsidian/gold branding. |
| **3-Rating Cold-Start Threshold** | Immediate single-rating recommender | A single rating produces extreme over-specialization and noisy recommendations. Requiring 3 ratings ensures a stable initial user preference vector. |

---

## 6. Empirical Evaluation Summary

Evaluated on MovieLens *ml-latest-small* (50 active test users, temporal 80/20 train/test split, ground truth: ratings $\ge 3.5 / 5.0$):

- **HitRate@10:** ReelSense Hybrid achieves **76.0%**, outperforming pure Collaborative (70.0%) and Popularity (40.0%).
- **Catalog Coverage:** Hybrid reaches **27.7%** of the catalog (vs 5.3% for Popularity), proving resistance to popularity bias.
- **Precision@10:** Hybrid reaches **0.1540** (a **2.48x improvement** over the Popularity baseline).
- **Intra-List Diversity:** Hybrid achieves **0.5236**, striking the optimal balance between thematic coherence and serendipitous variety.

---

## 7. Known Limitations & Future Improvements
1. **Multi-User Scaling:** Currently stores local state in `user_data.json`. Future iteration could introduce PostgreSQL + JWT authentication for multi-user cloud deployment.
2. **Implicit Signals:** Currently optimizes on explicit signals (ratings, watchlist, not-interested). Can be extended to track dwell time, scroll depth, and carousel interactions.
3. **Deep Learning Latent Embeddings:** Could incorporate two-tower neural networks (e.g. YouTube DNN / NeuMF) trained on large-scale MovieLens 25M data for higher-order non-linear feature interactions.
