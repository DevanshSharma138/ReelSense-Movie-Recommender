# ReelSense — AI-Powered Movie Discovery & Recommendation Platform

> **Tagline:** Cinematic Curation & Machine Learning Recommendation Engine  
> **Domain:** Personalized Recommendation Systems, Machine Learning, Information Retrieval  
> **Interface:** Streamlit (Python) with Obsidian & Champagne-Gold Cinematic Design System

---

## 1. Project Title
**ReelSense: Hybrid Machine Learning Movie Recommendation Platform**

---

## 2. Problem Statement
Modern streaming consumers face the classic "choice overload" dilemma: browsing through thousands of catalog items with generic, non-transparent algorithms leads to decision fatigue. Traditional single-model recommenders suffer from fundamental weaknesses:
- **Pure Collaborative Filtering** fails in cold-start scenarios where new users have few or no ratings, and suffers from extreme popularity bias.
- **Pure Content-Based Filtering** creates an echo chamber / over-specialization bubble, repeatedly recommending only identical genres and lacking serendipitous discovery.
- **Black-box algorithms** provide zero justification, eroding user trust.

ReelSense solves this by implementing an explainable, interactive, hybrid recommendation system that combines textual TF-IDF semantic profiling with TruncatedSVD matrix factorization, backed by atomic state persistence, negative feedback filtering, and dynamic sensory mood calibration.

---

## 3. Key Features
- **Cinematic Discovery & Spotlight:** Featured premiere spotlight hero with real MovieLens metadata, rating badges, and catalog velocity ranking.
- **Dynamic Hybrid Personalization:** Seamless transition from cold-start Bayesian popularity to personalized hybrid recommendations once 3 ratings are recorded.
- **First-Time User Onboarding:** Dismissible progressive counter (`{n} / 3 Rated`) guiding users to calibrate recommendations.
- **Interactive Negative Feedback ("Not Interested"):** One-click exclusion button (`🚫`) on every movie card and details view that persists across application reboots and removes titles from all recommendation rails.
- **Live Taste Profile Visualization:** Real-time mathematical calculation of user taste (total ratings, mean rating, dominant genre, and rating-weighted genre strength bars `████████`).
- **Sensory Mood Explorer:** 6 curated emotional spectrum states (Happy, Relaxed, Thrilling, Romantic, Emotional, Mind-blown) with dynamic catalog availability counts.
- **Transparent "Why Recommended" Explanations:** Real data-driven justifications (shared genres, user rating overlap, community velocity rank, review consensus).
- **Natural Language Vector Search (Sense AI):** TF-IDF and cosine similarity search matching user free-text vibes (e.g. *"slow sci-fi"*, *"emotional drama"*) against plot summaries, tags, and genres.
- **Offline 4-Tier Image Fallback Hierarchy:** TMDB Poster -> TMDB Backdrop -> Procedural Local SVG Vector Art -> Placeholder (guarantees zero broken layout dependency).

---

## 4. Dataset
ReelSense is powered by the benchmark **MovieLens (ml-latest-small)** dataset:
- **100,836 real ratings** across **9,742 movies** created by **610 users**.
- **Active Curated Catalog:** Top 2,000 most-rated films indexed with Bayesian popularity ranking (expanded in Phase 5.5 from 600 for rich discovery across 1922-2018):
  $$BayesScore = \frac{v \cdot R + m \cdot C}{v + m}$$
  where $v$ is vote count, $R$ is average rating, $C$ is catalog mean, and $m$ is the 60th-percentile minimum vote threshold.
- Enhanced with MovieLens user tags (`tags.csv`), sensory mood mappings, and cross-validated TMDB metadata / procedural SVG fallbacks.

---

## 5. Recommendation Architecture
ReelSense utilizes a dual-engine architecture coordinated through a centralized service layer:

```
                      [ User Interactions: Ratings & Feedback ]
                                         │
                                         ▼
                                [ UserStore Persistence ]
                                  (data/user_data.json)
                                         │
             ┌───────────────────────────┴───────────────────────────┐
             ▼                                                       ▼
[ Content Engine (TF-IDF) ]                             [ Collaborative Engine (SVD) ]
 - Genres (3x weight)                                    - User-Item Interaction Matrix
 - User tags & Mood vectors                              - Mean-centered ratings
 - Plot summary & Director                               - TruncatedSVD (k=50 factors)
 - Cosine Similarity                                     - Fold-in User Projection
             │                                                       │
             └───────────────────────────┬───────────────────────────┘
                                         ▼
                           [ Dynamic Hybrid Ensembling ]
                    Score = 0.40 * S_content + 0.60 * S_collab
                                         │
                                         ▼
                         [ Negative Feedback Filter ]
                         (Exclude 'Not Interested' IDs)
                                         │
                                         ▼
                     [ Ranked & Explained Recommendations ]
```

---

## 6. Content-Based Filtering
1. **Feature Extraction:** Constructs rich textual document representations combining genres (weighted 3x), sensory moods, director, cast, title, and user tags:
   $$\text{Doc}_m = \text{Genres}_m^3 \cup \text{Moods}_m \cup \text{Director}_m \cup \text{Tags}_m \cup \text{Overview}_m$$
2. **Vectorization:** `TfidfVectorizer` with sublinear term-frequency scaling and unigram/bigram tokenization $(1, 2)$.
3. **User Profile Vector:** Built as the rating-weighted centroid of liked movies ($r_m \ge 2.5$ stars):
   $$\mathbf{p}_{\text{user}} = \frac{\sum_{m \in R_u} (r_{um} - 2.5) \cdot \mathbf{v}_m}{\left\| \sum_{m \in R_u} (r_{um} - 2.5) \cdot \mathbf{v}_m \right\|_2}$$
4. **Scoring:** Cosine similarity $S_{\text{content}} = \mathbf{X} \cdot \mathbf{p}_{\text{user}}$.

---

## 7. Collaborative Filtering
1. **Matrix Factorization:** Forms the sparse user-item interaction matrix $\mathbf{M} \in \mathbb{R}^{610 \times 9742}$ from MovieLens community ratings, centered by global mean rating:
   $$\mathbf{M}_{u, i} = R_{u, i} - \mu$$
2. **SVD Decomposition:** `TruncatedSVD(n_components=50, random_state=42)` decomposes $\mathbf{M} \approx \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T$, yielding latent item concept factors $\mathbf{V}_{\text{cat}} \in \mathbb{R}^{50 \times 2000}$.
3. **Fold-In Projection:** The active session user vector $\mathbf{u} \in \mathbb{R}^{9742}$ is projected into the latent feature space without retraining:
   $$S_{\text{collab}} = (\mathbf{u} \mathbf{V}^T) \mathbf{V}_{\text{cat}}$$

---

## 8. Hybrid Formula
ReelSense balances novelty and semantic accuracy using min-max normalized linear weighting:
$$\text{Score}(m) = \alpha \cdot \text{Norm}(S_{\text{content}}(m)) + (1 - \alpha) \cdot \text{Norm}(S_{\text{collab}}(m))$$
with $\alpha = 0.40$ (giving 40% weight to content similarity and 60% weight to collaborative community patterns).

---

## 9. Cold-Start Strategy
- **Fewer than 3 Ratings:** Automatically engages the cold-start fallback rail. Displays Bayesian-ranked community favorites and trending velocity items.
- **3 or More Ratings:** Seamlessly unlocks personalized hybrid recommendations.
- **Onboarding Banner:** Explains the 3-rating requirement to the user and tracks progress in real time.

---

## 10. Explainable Recommendations & Recommendation Intelligence (Phase 6)
Every recommendation surfaces human-understandable, mathematically grounded rationale derived directly from the underlying models and persisted user state (zero synthetic or hardcoded AI metrics):
- **Recommendation Breakdown / Why Recommended 2.0 (Movie Details):**
  - **Content Match:** Normalized TF-IDF cosine similarity between movie features and user preference centroid.
  - **Taste Alignment:** User rating-weighted genre preference alignment against movie genre distribution.
  - **Collaborative Signal:** Normalized SVD latent concept alignment from community viewer factorization.
  - **Score Contribution Transparency:** Exact formula display: `Final Hybrid Score = 0.40 × Content + 0.60 × Collaborative`.
  - **Positive Reference Anchors:** Top 2–3 positively rated reference titles with real TF-IDF cosine similarities and shared genres/moods.
  - **Cold-Start Fallback:** Truthful catalog curation rationale (MovieLens review consensus, Bayesian ranking, trending status) when user has fewer than 3 ratings without claiming unavailable personalization.

- **Taste Evolution (Profile):**
  - Visual timeline tracking how user genre preferences shift across rating milestones (`1st Rating` $\to$ `3rd Rating` $\to$ `5th Rating` $\to$ `10th Rating` $\to$ `Current`).
  - Reconstructed from persisted rating history in `data/user_data.json` preserving evaluation order (no synthetic timestamps).
  - Reuses identical rating-weighted genre formula ($\sum \text{score}$) for mathematical consistency.
  - Automated taste shift detection: identifies emerging preferences, most consistent genres, and biggest percentage shifts.

---

## 11. Persistence Architecture
User state is managed via [`src/services/user_store.py`](file:///c:/Users/AYUSH/Desktop/RS%20Project/src/services/user_store.py) and stored in [`data/user_data.json`](file:///c:/Users/AYUSH/Desktop/RS%20Project/data/user_data.json):
- **Atomic File Writing:** Writes to a temporary file, flushes, fsyncs, and applies atomic replacement (`os.replace`) with retry logic.
- **Windows File Lock Resilience:** Direct fallback write with exception handling to withstand Windows antivirus/indexer transient locks (`WinError 32`).
- **Data Preserved:** User ratings (`ratings`), Watchlist (`watchlist`), Excluded films (`not_interested`), and Curator profile preferences (`user_profile`).

---

## 12. User Feedback Loop
- **Positive Feedback (Ratings):** Adding or adjusting a 1–10 star rating updates user vectors and triggers immediate recommendation recalculation.
- **Negative Feedback ("Not Interested"):** Clicking `🚫` adds movie IDs to `not_interested`, immediately removing them from all carousels, discovery grids, and search results across sessions.
- **Watchlist:** Saved titles are kept in the personal screening queue without distorting user rating vectors.

---

## 13. Tech Stack
- **Language:** Python 3.11+ / 3.14
- **Web Interface:** Streamlit (Vanilla CSS design system)
- **Machine Learning & NLP:** Scikit-Learn (TF-IDF Vectorizer, TruncatedSVD, Cosine Similarity)
- **Data Engineering:** Pandas, NumPy, SciPy (Sparse CSR matrices)
- **Testing:** Pytest, Streamlit `AppTest` framework

---

## 14. Installation
```powershell
# Clone or navigate to the repository
cd "c:\Users\AYUSH\Desktop\RS Project"

# Install dependencies
pip install -r requirements.txt
```

---

## 15. Virtual Environment Activation
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt
.\.venv\Scripts\activate.bat
```

---

## 16. How to Run the Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 17. How to Run Tests & Evaluation
```powershell
# Run the complete automated test suite (51 tests)
pytest -v

# Run the Phase 6 recommendation intelligence verification flow
python tests/manual_test_phase6_flow.py

# Run the 16-step end-to-end user journey test
python tests/manual_test_phase3_flow.py

# Run the 10-step persistence and restart flow test
python tests/manual_test_flow.py

# Run offline recommender evaluation on MovieLens
python src/evaluation/evaluate.py
```

---

## 18. Project Structure
```
RS Project/
├── app.py                              # Streamlit entry point & global layout shell
├── requirements.txt                    # Project dependencies
├── README.md                           # Comprehensive documentation
├── PROJECT_SUMMARY.md                  # Viva / Presentation summary
├── assets/
│   └── styles.css                      # Obsidian & Champagne-Gold styling
├── data/
│   ├── movies.csv                      # MovieLens raw movies
│   ├── ratings.csv                     # MovieLens 100k ratings
│   ├── links.csv                       # TMDB / IMDb identifier mappings
│   ├── loader.py                       # High-performance cached data loader
│   └── user_data.json                  # Persistent JSON storage (ignored in git)
├── src/
│   ├── config.py                       # App constants, moods, color tokens
│   ├── components/
│   │   ├── hero_banner.py              # Spotlight hero component
│   │   ├── mood_matrix.py              # Sensory mood vault grid
│   │   ├── movie_card.py               # Card with 🚫/↩️ toggle and poster fallback
│   │   ├── movie_carousel.py           # Horizontal movie row container
│   │   ├── onboarding_banner.py        # 3-rating dismissible progress banner
│   │   ├── sidebar.py                  # Brand header & navigation
│   │   ├── topbar.py                   # Search bar & user header
│   │   └── trending_grid.py            # Editorial 01-05 velocity ranking
│   ├── pages/
│   │   ├── home.py                     # Home feed & personalized carousels
│   │   ├── discover.py                 # Filter & multi-faceted search
│   │   ├── mood_explorer.py            # Atmospheric resonance explorer
│   │   ├── movie_details.py            # Rich metadata, ratings & explanations
│   │   ├── watchlist.py                # Vault saved screening queue
│   │   ├── ratings.py                  # Interactive rating manager
│   │   ├── profile.py                  # Taste profile & excluded films manager
│   │   ├── sense_ai.py                 # Natural language vector search
│   │   └── about.py                    # Academic ML architecture breakdown
│   ├── services/
│   │   ├── catalog.py                  # 2,000-title active catalog & 4-tier image fallback
│   │   ├── hybrid_model.py             # TF-IDF + TruncatedSVD hybrid engine
│   │   ├── movie_service.py            # Catalog query & filter service
│   │   ├── recommendation_service.py   # Public recommender API & explanations
│   │   └── user_store.py               # Atomic JSON persistence service
│   ├── utils/
│   │   ├── image_utils.py              # Procedural SVG fallback poster generators
│   │   └── metadata_validator.py       # MovieLens ↔ TMDB metadata & poster integrity validator
│   └── evaluation/
│       └── evaluate.py                 # Offline evaluation engine (P@K, R@K, Diversity)
└── tests/
    ├── test_persistence.py             # User store & restart persistence tests (12 tests)
    ├── test_phase3.py                  # Personalization & metadata tests (7 tests)
    ├── test_metadata_integrity.py      # Catalog expansion & poster integrity tests (7 tests)
    ├── test_recommendation_quality.py  # Profile differentiation & threshold tests (2 tests)
    ├── test_error_empty_states.py      # Edge case & empty state tests (5 tests)
    ├── test_smoke.py                   # Basic sanity & import tests (4 tests)
    └── manual_test_phase3_flow.py      # 16-step end-to-end integration test
```

---

## 19. Evaluation Results
Evaluated on MovieLens *ml-latest-small* across 50 active users using temporal 80/20 train/test splits (Ground truth: held-out ratings $\ge 3.5 / 5.0$):

| Recommendation Model | Precision@5 | Precision@10 | Recall@5 | Recall@10 | HitRate@10 | Catalog Coverage | Intra-List Diversity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Popularity Baseline** | 0.0720 | 0.0620 | 0.0294 | 0.0490 | 40.0% | 5.3% | 0.7714 |
| **Content-Based (TF-IDF)** | 0.0800 | 0.0620 | 0.0459 | 0.0655 | 36.0% | 22.8% | 0.3219 |
| **Collaborative (SVD)** | 0.2440 | 0.2040 | 0.1087 | 0.1647 | 70.0% | 26.0% | 0.7798 |
| **ReelSense Hybrid ($\alpha=0.4$)** | **0.1840** | **0.1540** | **0.0906** | **0.1418** | **76.0%** | **27.7%** | **0.5236** |

### Key Findings:
- **HitRate@10:** ReelSense Hybrid achieves **76.0%**, outperforming pure Collaborative (70.0%) and Popularity (40.0%).
- **Catalog Coverage:** Hybrid reaches **27.7%** of the catalog, preventing popularity concentration.
- **Diversity:** Hybrid achieves **0.5236** intra-list diversity, avoiding both the extreme genre echo chamber of Content-Only (0.3219) and the diffuse randomness of Popularity.

---

## 20. Known Limitations
1. **Single-Node Local Persistence:** The application is architected for local deployment with JSON storage; scaling to concurrent multi-tenant production would require an external database (e.g. PostgreSQL) and user authentication.
2. **Offline TMDB Cache Dependency:** Posters rely on cached metadata or attractive procedural SVG fallbacks when external TMDB network requests are disabled or rate-limited.
3. **Implicit Feedback:** Feedback is currently collected explicitly (ratings, watchlist, not-interested) rather than implicitly (dwell time, clicks).
