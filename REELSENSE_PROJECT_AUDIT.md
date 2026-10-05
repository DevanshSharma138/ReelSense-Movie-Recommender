# REELSENSE — COMPLETE PROJECT AUDIT

> **Audit Date:** 2026-10-05  
> **Auditor:** Automated AI Audit (Antigravity)  
> **Project Root:** `c:\Users\AYUSH\Desktop\RS Project`  
> **Purpose:** Authoritative reference document for another AI coding agent to use for implementation work. Do not rebuild from scratch.

---

## 1. PROJECT STRUCTURE

### 1.1 Directory Tree

```
RS Project/
├── app.py                              # Main Streamlit entry point & page router
├── requirements.txt                    # Python dependencies (5 packages)
├── README.md                           # Project documentation
├── REELSENSE_PROJECT_AUDIT.md          # THIS FILE — audit document
│
├── assets/
│   └── styles.css                      # Custom CSS (684 lines, 18 KB) — design system
│
├── data/
│   ├── loader.py                       # MovieLens CSV loader (cached with lru_cache)
│   ├── movies.csv                      # MovieLens ml-latest-small movies (9,742 rows)
│   ├── ratings.csv                     # MovieLens ml-latest-small ratings (100,836 rows)
│   ├── links.csv                       # MovieLens → TMDB/IMDb ID mapping (9,742 rows)
│   ├── enrich_tmdb.py                  # One-time TMDB metadata enrichment script
│   ├── employee_churn_backup.csv       # UNRELATED — employee churn data (leftover)
│   └── __pycache__/
│
├── src/
│   ├── config.py                       # App constants, color palette, nav items, moods, default user
│   │
│   ├── data/
│   │   ├── sample_movies.py            # Hardcoded 15-movie dataset with rich fictional metadata
│   │   └── __pycache__/
│   │
│   ├── services/
│   │   ├── catalog.py                  # PHASE 3: Unified catalog from MovieLens + optional TMDB metadata
│   │   ├── content_model.py            # PHASE 2: TF-IDF content-based model (reads SAMPLE_MOVIES!)
│   │   ├── hybrid_model.py             # PHASE 3: Hybrid recommender (TF-IDF + SVD collaborative)
│   │   ├── movie_service.py            # PHASE 3: Search, filter, sort over catalog
│   │   ├── recommendation_service.py   # PHASE 3: Unified API — routes to hybrid_model
│   │   └── __pycache__/
│   │
│   ├── components/
│   │   ├── sidebar.py                  # Left sidebar navigation + branding
│   │   ├── topbar.py                   # Top search bar, Curator AI button, notifications, avatar
│   │   ├── hero_banner.py              # Home page featured movie hero spotlight
│   │   ├── movie_card.py               # Reusable movie poster card component
│   │   ├── movie_carousel.py           # Horizontal section with title + movie cards
│   │   ├── trending_grid.py            # Numbered editorial trending rankings (01-05)
│   │   ├── mood_matrix.py              # 6-tile mood vault matrix (Home page)
│   │   └── __pycache__/
│   │
│   └── pages/
│       ├── home.py                     # Home page — hero, recommendations, trending, mood matrix, hidden gems
│       ├── discover.py                 # Discover page — search, multi-filter, movie grid
│       ├── mood_explorer.py            # Mood Explorer — 6 mood cards, calibration toolbar, filtered results
│       ├── movie_details.py            # Movie details — poster, metadata, watchlist, rating, similar movies
│       ├── watchlist.py                # My Watchlist — grid of bookmarked movies
│       ├── ratings.py                  # My Ratings — list of user-rated movies
│       ├── profile.py                  # My Profile — user preferences editor
│       ├── sense_ai.py                 # Sense AI — natural language prompt search
│       ├── about.py                    # About the AI — academic ML documentation (static text)
│       └── __pycache__/
│
├── design_reference/
│   ├── DESIGN.md                       # Stitch design system specification (colors, typography, spacing, components)
│   ├── screen.png                      # Stitch screenshot — Mood Explorer page reference
│   └── code.html                       # Stitch HTML export (101 KB)
│
├── ml_engine/
│   └── dataset_profiler.py             # Generic dataset profiler script (UNRELATED to movie recs)
│
├── notebooks/                          # Empty directory
│
├── tests/
│   └── test_smoke.py                   # Basic import smoke test
│
└── venv/                               # Python virtual environment
```

### 1.2 File Classification

| File | Status |
|------|--------|
| `app.py` | **Actively used** — main entry point |
| `requirements.txt` | **Actively used** — dependency manifest |
| `README.md` | **Actively used** — but partially stale (describes old 25-movie sample state) |
| `assets/styles.css` | **Actively used** — loaded by `app.py` |
| `data/loader.py` | **Actively used** — imported by `catalog.py` and `hybrid_model.py` |
| `data/movies.csv` | **Actively used** — MovieLens ml-latest-small |
| `data/ratings.csv` | **Actively used** — MovieLens ml-latest-small |
| `data/links.csv` | **Used by** `enrich_tmdb.py` only (not used at runtime unless enrichment has been run) |
| `data/enrich_tmdb.py` | **Utility script** — must be run manually with a TMDB API key |
| `data/employee_churn_backup.csv` | **UNRELATED / OBSOLETE** — employee churn data, not used anywhere |
| `src/config.py` | **Actively used** |
| `src/data/sample_movies.py` | **PARTIALLY USED** — imported by `content_model.py` (PHASE 2 legacy code) but NOT by the main catalog/hybrid path. Also imported by `test_smoke.py`. |
| `src/services/catalog.py` | **Actively used** — Phase 3 real catalog |
| `src/services/content_model.py` | **ORPHANED / LEGACY** — Phase 2 standalone content model. Imports `SAMPLE_MOVIES`. Not imported by any active runtime path. |
| `src/services/hybrid_model.py` | **Actively used** — Phase 3 hybrid recommender |
| `src/services/movie_service.py` | **Actively used** |
| `src/services/recommendation_service.py` | **Actively used** — facade for hybrid_model |
| `src/components/*` | **All actively used** |
| `src/pages/*` | **All actively used** (including `about.py` which is routed but is static documentation) |
| `design_reference/*` | **Reference only** — not loaded at runtime |
| `ml_engine/dataset_profiler.py` | **UNRELATED / OBSOLETE** — generic dataset profiler for a "Churn" dataset, never imported |
| `tests/test_smoke.py` | **Test file** — basic import checks, references old sample_movies |
| `notebooks/` | **Empty** |

---

## 2. HOW THE APPLICATION CURRENTLY RUNS

### 2.1 Application Entry Point

- **File:** `app.py`
- **Framework:** Streamlit
- **Run command:** `streamlit run app.py`
- **Working directory must be:** `c:\Users\AYUSH\Desktop\RS Project`

### 2.2 Python Version & Package Manager

- README references Python 3.11
- Virtual environment: `venv/` directory exists
- Package manager: `pip` (standard `requirements.txt`)

### 2.3 Dependencies (`requirements.txt`)

```
streamlit>=1.30.0
pandas>=2.0.0
pillow>=10.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

**Missing from requirements.txt:**
- `scipy` — required by `hybrid_model.py` (`from scipy.sparse import csr_matrix`)
- `requests` — required by `data/enrich_tmdb.py` (only needed for TMDB enrichment, not runtime)

### 2.4 Import Chains & Potential Runtime Issues

The application uses two different import styles that could cause issues:

1. **`catalog.py` and `hybrid_model.py`** import from `data.loader` (no `src.` prefix):
   ```python
   from data.loader import load_movies, load_ratings, DATA_DIR
   ```
   This works only when `RS Project/` is the CWD and is on `sys.path`.

2. **All other files** use `src.` prefix:
   ```python
   from src.services.catalog import get_catalog
   ```

3. **`content_model.py`** imports `from src.data.sample_movies import SAMPLE_MOVIES` — this file is orphaned and not called by the active runtime path.

### 2.5 Will It Run Successfully?

**Likely YES** with these conditions:
- CWD is `RS Project/`
- `scipy` is installed (not in requirements.txt but needed)
- The `data/movies.csv` and `data/ratings.csv` exist (they do — MovieLens data is present)
- No `tmdb_metadata.json` exists (the catalog will use placeholder images and auto-generated overviews)

**Critical note:** Without running `enrich_tmdb.py` first, all movie posters will be `placehold.co` placeholders and overviews will be generic auto-generated text like "A drama, thriller film from 1994." The application will be functionally correct but visually bare.

---

## 3. FRONTEND / UI AUDIT

### 3.1 Overall Architecture

- **Framework:** Streamlit with heavy use of `st.markdown(unsafe_allow_html=True)` for custom HTML/CSS rendering
- **Styling:** Custom CSS (`assets/styles.css`, 684 lines) loaded via `st.markdown(<style>...)` injection
- **Navigation:** Sidebar buttons that set `st.session_state.current_page` and call `st.rerun()`
- **Layout:** `st.set_page_config(layout="wide")`
- **Fonts:** Outfit (display) + Plus Jakarta Sans (body) loaded via Google Fonts
- **Icons:** Material Symbols Outlined loaded via Google Fonts

### 3.2 Pages / Views

| Page | Route IDs | File | Status |
|------|-----------|------|--------|
| Home | `home`, `home-discover` | `pages/home.py` | **IMPLEMENTED** |
| Discover | `discover-movies`, `discover`, `collections` | `pages/discover.py` | **IMPLEMENTED** |
| Mood Explorer | `mood-explorer`, `mood` | `pages/mood_explorer.py` | **IMPLEMENTED** |
| Movie Details | `movie_details` | `pages/movie_details.py` | **IMPLEMENTED** |
| Watchlist | `my-watchlist`, `watchlist` | `pages/watchlist.py` | **IMPLEMENTED** |
| Ratings | `my-ratings`, `ratings` | `pages/ratings.py` | **IMPLEMENTED** |
| Profile | `my-profile`, `profile`, `settings` | `pages/profile.py` | **IMPLEMENTED** |
| Sense AI | `about-the-ai`, `sense_ai`, `about` | `pages/sense_ai.py` | **IMPLEMENTED** |
| About (Academic) | Routed via same IDs as Sense AI | `pages/about.py` | **EXISTS but NEVER ROUTED** — `about.py` is imported in `app.py` as `render_about_page` but the routing on line 79-80 calls `render_sense_ai_page()` instead. `render_about_page()` is dead code. |

### 3.3 Feature-by-Feature UI Classification

| Feature | Classification | Details |
|---------|---------------|---------|
| **Sidebar navigation** | IMPLEMENTED | 7 nav items, active state highlighting, branding header |
| **Topbar search bar** | IMPLEMENTED | Text input, routes to Sense AI page on input |
| **Topbar Curator AI button** | IMPLEMENTED | Routes to Sense AI page |
| **Topbar notifications icon** | MOCK/HARDCODED | Visual HTML only, notification dot always shows, no click handler, no notification system |
| **Topbar user avatar** | MOCK/HARDCODED | Hardcoded Google avatar URL, click reloads page |
| **Runtime Engine Status panel** | MOCK/HARDCODED | Always shows "Streamlit & Python 3.11", "Vector Embeddings Active", "v2.4" — purely decorative |
| **Hero banner** | IMPLEMENTED | Shows featured movie with backdrop, metadata badges, action buttons |
| **Hero cycle switcher** | PARTIALLY IMPLEMENTED | Shows "01 / 04" always hardcoded, up-next cards navigate to movie details instead of switching the hero |
| **"Stream Now" button** | PARTIALLY IMPLEMENTED | Routes to movie details page (not actual streaming) |
| **Recommended For You carousel** | IMPLEMENTED | Pulls from RecommendationService.get_recommended_for_user() |
| **Trending grid (01-05)** | IMPLEMENTED | Shows ranked movies from catalog |
| **Mood Vault Matrix (Home)** | IMPLEMENTED | 6 mood tiles, clicking navigates to Mood Explorer with selected mood |
| **Hidden Gems section** | IMPLEMENTED | Filters catalog for hidden gem movies |
| **Discover page search** | IMPLEMENTED | Filters by title, overview, director, cast, genre text |
| **Genre multi-select filter** | IMPLEMENTED | Dynamic genres from catalog |
| **Year range slider** | IMPLEMENTED | 1990-2026 range |
| **Rating threshold slider** | IMPLEMENTED | 0.0-10.0 |
| **Language filter** | IMPLEMENTED | Dynamic languages from catalog |
| **Sort options** | IMPLEMENTED | Rating, Year (Newest/Oldest), Title A-Z |
| **Reset filters button** | IMPLEMENTED |  |
| **Empty state (no results)** | IMPLEMENTED | Shows message with clear button |
| **Mood Explorer - 6 mood cards** | IMPLEMENTED | Selection updates session state, active state highlighting |
| **Mood Explorer - Calibration toolbar** | IMPLEMENTED | Genre chips (toggle), min rating slider, Reset All |
| **Mood Explorer - Find Movies button** | MOCK/HARDCODED | Shows a `st.toast()` message but does NOT trigger a re-filter; the results are already filtered reactively |
| **Mood Explorer - results grid** | IMPLEMENTED | Filters movies by mood + genre + rating |
| **Mood Explorer - Affinity/Critical sort** | IMPLEMENTED | Toggles sort mode |
| **Mood Explorer - Curation Rationale box** | MOCK/HARDCODED | Static hardcoded text, never changes |
| **Mood Explorer - Export Calibration** | MOCK/HARDCODED | Shows st.info() with current settings, no actual export |
| **Mood Explorer - Save Selection Rail** | IMPLEMENTED | Adds all 4 displayed movies to watchlist |
| **Movie Details - poster + metadata** | IMPLEMENTED | Shows poster, title, year, rating, genres, runtime, director, cast, overview |
| **Movie Details - watchlist toggle** | IMPLEMENTED | Add/remove from session_state.watchlist |
| **Movie Details - user rating slider** | IMPLEMENTED | Saves to session_state.ratings |
| **Movie Details - "Why We Recommend"** | PARTIALLY IMPLEMENTED | Uses `movie.get("why_recommended")` — for catalog movies this is empty `[]`, falls back to generic text |
| **Movie Details - similar movies** | IMPLEMENTED | Uses hybrid_model.similar() |
| **Watchlist page** | IMPLEMENTED | Grid of saved movies, sorting, remove button |
| **Watchlist - empty state** | IMPLEMENTED | Shows message with "Discover Movies Now" button |
| **Ratings page** | IMPLEMENTED | List of rated movies, update/remove ratings |
| **Ratings - empty state** | IMPLEMENTED | Shows message |
| **Profile page** | IMPLEMENTED | Name, genres, language, era, min rating preferences |
| **Profile - Save Preferences** | IMPLEMENTED | Saves to session_state.user_profile |
| **Sense AI - prompt search** | IMPLEMENTED | Uses hybrid_model.query() (TF-IDF cosine against free text) |
| **Sense AI - preset prompts** | IMPLEMENTED | 5 preset prompt buttons |
| **About page (academic docs)** | EXISTS BUT UNREACHABLE | `render_about_page()` is never called by the router — the "about" routes all go to `render_sense_ai_page()` |
| **Mobile navigation** | NOT IMPLEMENTED | No responsive breakpoints or mobile nav |
| **"Not Interested" feature** | NOT IMPLEMENTED | `hidden_ids` parameter exists in recommendation_service API but no UI exposes it |
| **Taste Profile visualization** | NOT IMPLEMENTED | Profile page saves preferences but there's no visual taste profile |

### 3.4 Hardcoded / Mock Elements

1. **`vector_match` on sample movies** — fictional percentage scores (e.g., 98%, 99%) in `sample_movies.py`
2. **`why_recommended` on sample movies** — fictional explanation text in `sample_movies.py`
3. **`mood_affinity` on sample movies** — fictional affinity percentages
4. **Notifications bell** — always shows a gold dot, no notification system
5. **"4K Ultra HD" and "IMAX Enhanced" badges** — hardcoded in hero banner, not data-driven
6. **"PG-13" rating badge** — hardcoded in hero banner
7. **"Live Stream Analytics" badge** — purely decorative text in trending grid
8. **Runtime Engine Status** — always shows same hardcoded status
9. **Mood "count" values** — "2,118 Available", "1,840 Available" etc. in config.py are fictional static numbers
10. **Mood "frequency" values** — "528 Hz", "432 Hz" etc. are fictional/decorative
11. **Curation Rationale text** — same static paragraph regardless of mood/results

---

## 4. STITCH / DESIGN REFERENCE AUDIT

### 4.1 Design Reference Files

| File | Description |
|------|-------------|
| `design_reference/DESIGN.md` | Complete design system spec — YAML frontmatter with color tokens, typography scale, spacing, component specs |
| `design_reference/screen.png` | Screenshot of Mood Explorer page as designed in Stitch |
| `design_reference/code.html` | Full HTML export from Stitch (101 KB) |

### 4.2 Design System Summary

- **Palette:** Cinematic Obsidian (`#131315` base) + Champagne Gold (`#f2ca50` accent)
- **Typography:** `Outfit` for display headings, `Plus Jakarta Sans` for body/labels
- **Spacing:** 8px rhythm, 1.5rem gutter, 3rem margin (desktop)
- **Shapes:** 16px border-radius for cards, 9999px for pills/buttons
- **Elevation:** No dropshadows — uses translucent layers, micro-borders, ambient gold glow
- **Icons:** Material Symbols Outlined

### 4.3 Design vs Implementation Match

| Aspect | Design Reference | Current App | Match? |
|--------|-----------------|-------------|--------|
| Color palette | Obsidian/Gold per DESIGN.md | CSS tokens match closely | GOOD MATCH |
| Typography | Outfit + Plus Jakarta Sans | Both loaded and used | GOOD MATCH |
| Sidebar navigation | 7 items, brand header, runtime engine panel | Implemented faithfully | GOOD MATCH |
| Mood Explorer layout | 6 mood cards, calibration toolbar, 4-card results | Implemented faithfully per screen.png | EXCELLENT MATCH |
| Movie cards | 2:3 poster, affinity badge, rating badge, runtime, genre | CSS matches design spec | GOOD MATCH |
| Buttons | Pill shape, gold gradient primary, translucent secondary | Implemented | GOOD MATCH |
| Audio wave visualizer | Animated bars on mood cards | CSS animation implemented | GOOD MATCH |
| Home page | Not shown in screen.png (only Mood Explorer) | Home page follows same design language | NO REFERENCE |
| Responsive/Mobile | Design spec mentions tablet/mobile breakpoints | NOT implemented | NOT IMPLEMENTED |
| Glassmorphism depth | backdrop-filter blur on floating elements | Partially applied in CSS | PARTIAL |

### 4.4 Conclusion

The Mood Explorer page very closely matches the Stitch reference screenshot. The overall design system (colors, typography, spacing, components) is faithfully translated into Streamlit CSS. The design reference files should be **preserved as-is** for reference.

---

## 5. BACKEND / APPLICATION LOGIC

### 5.1 Framework

**Streamlit** — no separate backend framework (Flask, FastAPI, etc.). All logic runs in the Streamlit process.

### 5.2 Service Layer Architecture

```
app.py (entry point + router)
  ├── src/config.py (constants)
  ├── src/components/* (UI rendering)
  └── src/pages/* (page logic)
        ├── MovieService (search, filter, sort)
        │     └── catalog.get_catalog() → MovieLens data
        └── RecommendationService (recommendations, trending, mood, search)
              └── hybrid_model.get_model() → HybridModel
                    ├── catalog.get_catalog() → content features
                    ├── data.loader.load_ratings() → collaborative features
                    ├── TfidfVectorizer → content similarity matrix
                    └── TruncatedSVD → collaborative item embeddings
```

### 5.3 Key Services

#### `catalog.py` — Unified Movie Catalog (Phase 3)
- **Purpose:** Builds a list of 600 movie dicts from MovieLens + optional TMDB metadata
- **Data flow:** `load_movies()` + `load_ratings()` → compute Bayesian average ratings → determine trending → merge TMDB metadata (if `tmdb_metadata.json` exists) → return list of dicts
- **Caching:** `@lru_cache(maxsize=1)` — computed once per process lifetime
- **Actually used:** YES — called by all services
- **Complete:** YES

#### `hybrid_model.py` — Hybrid Recommender (Phase 3)
- **Purpose:** Content-based (TF-IDF) + Collaborative (TruncatedSVD) hybrid recommendations
- **Score formula:** `score = ALPHA * content + (1 - ALPHA) * collaborative` where `ALPHA = 0.4`
- **Cold start:** Falls back to trending/genre-based when user has < 3 ratings
- **Methods:** `recommend()`, `similar()`, `query()`
- **Caching:** Global singleton `_model` — computed once per process
- **Actually used:** YES — called by `recommendation_service.py`
- **Complete:** YES — this is a functional hybrid recommender

#### `content_model.py` — Content-Based Model (Phase 2, LEGACY)
- **Purpose:** TF-IDF + cosine similarity over `SAMPLE_MOVIES` (15 hardcoded movies)
- **Actually used:** NO — not imported by any active runtime path
- **Status:** **ORPHANED LEGACY CODE** from Phase 2. The hybrid model in Phase 3 includes its own content-based component.

#### `movie_service.py` — Movie Data Service (Phase 3)
- **Purpose:** `get_all_movies()`, `get_movie_by_id()`, `get_all_genres()`, `get_all_languages()`, `filter_movies()`
- **Actually used:** YES
- **Complete:** YES

#### `recommendation_service.py` — Recommendation API (Phase 3)
- **Purpose:** Unified facade that routes to `hybrid_model`
- **Methods:** `get_recommended_for_user()`, `get_trending_movies()`, `get_hidden_gems()`, `get_movies_by_mood()`, `search_by_prompt()`, `get_similar_movies()`, `get_recommendation_explanation()`
- **Actually used:** YES
- **Complete:** YES

### 5.4 State Management

All state is managed via `st.session_state`:
- `current_page` — current active page ID
- `watchlist` — list of movie IDs (initialized with `[101, 102]` — these are from sample_movies, likely won't exist in MovieLens catalog)
- `ratings` — dict of `{movieId: rating}` (initialized with `{101: 9.5, 102: 9.0}` — same problem)
- `user_profile` — dict from DEFAULT_USER in config.py
- `global_search` — topbar search text
- `discover_search` — discover page search text
- `selected_movie_id` — currently selected movie (initialized to `101` — may not exist in catalog)
- `selected_mood` — currently selected mood (initialized to "Mind-blown")

---

## 6. DATA AUDIT

### 6.1 Dataset Inventory

| File | Source | Format | Rows | Columns | Used? | Purpose |
|------|--------|--------|------|---------|-------|---------|
| `data/movies.csv` | MovieLens ml-latest-small | CSV | 9,742 | 3 (`movieId`, `title`, `genres`) | **YES** | Core movie metadata |
| `data/ratings.csv` | MovieLens ml-latest-small | CSV | 100,836 | 4 (`userId`, `movieId`, `rating`, `timestamp`) | **YES** | Core ratings for collaborative filtering |
| `data/links.csv` | MovieLens ml-latest-small | CSV | 9,742 | 3 (`movieId`, `imdbId`, `tmdbId`) | **Only by `enrich_tmdb.py`** | Maps MovieLens IDs to TMDB IDs |
| `data/employee_churn_backup.csv` | Unknown | CSV | ~8 | 6 (`Age`, `Salary`, `Experience`, `Education`, `City`, `Churn`) | **NO** | Completely unrelated — leftover from another project |
| `src/data/sample_movies.py` | Hand-crafted | Python list of dicts | 15 movies | ~25 fields each | **Only by orphaned `content_model.py`** | Fictional/curated movie data with rich metadata |

### 6.2 MovieLens Dataset Details

- **Source:** MovieLens ml-latest-small (from GroupLens)
- **movies.csv columns:** `movieId`, `title`, `genres` (pipe-separated)
- **ratings.csv columns:** `userId`, `movieId`, `rating` (0.5-5.0 scale), `timestamp`
- **Title format:** `"Movie Title (Year)"` — year is extracted by `loader.py`
- **Genre format:** `"Action|Adventure|Comedy"` — pipe-separated
- **This is a proper, real-world movie recommendation dataset.**

### 6.3 TMDB Metadata

- `data/tmdb_metadata.json` — **DOES NOT EXIST** in the current project
- `data/enrich_tmdb.py` is the script to create it (requires a TMDB API key)
- Without this file, the catalog uses:
  - Placeholder images from `placehold.co`
  - Auto-generated overviews like "A drama, thriller film from 1994."
  - Empty director and cast fields
  - Default language "English"

### 6.4 Sample Movies Data (`src/data/sample_movies.py`)

- 15 hand-crafted movie entries
- Mixture of real movies (Interstellar, Inception, Blade Runner 2049, Oppenheimer, Dune: Part Two) and fictional movies (Chronos: Redemption, Solitude Protocol, etc.)
- Uses poster/backdrop URLs from Unsplash and Google AIDA
- Includes rich metadata: `why_recommended`, `vector_match`, `mood_affinity`, `is_trending`, `is_hidden_gem`, `trending_rank`, `trending_growth`
- Movie IDs: mix of single-digit (1, 2, 8, 16) and 100-series (101-112)
- **This dataset served as the Phase 1/2 prototype data. It is NOT used by the Phase 3 active runtime** (except by the orphaned `content_model.py`).

### 6.5 ID Conflicts

The session state is initialized with sample_movies IDs:
- `watchlist = [101, 102]` — these IDs exist in `sample_movies.py` but are valid MovieLens IDs too (Toy Story Sequel, etc.)
- `ratings = {101: 9.5, 102: 9.0}` — same issue
- `selected_movie_id = 101` — same issue

In MovieLens, movieId=101 is "Bottle Rocket (1996)" and movieId=102 is "Mr. Holland's Opus (1995)". So the default state will show these MovieLens movies, NOT the fictional Chronos/Solitude movies — which is actually correct behavior for Phase 3.

---

## 7. MACHINE LEARNING / RECOMMENDATION ENGINE AUDIT

### 7.1 Content-Based Filtering

| Aspect | Status | Details |
|--------|--------|---------|
| TF-IDF vectorization | **REAL / FUNCTIONAL** | `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)` in `hybrid_model.py` |
| Text document construction | **REAL / FUNCTIONAL** | Combines genres (x3 weight), moods, director, cast, tags, title, overview into a single document per movie |
| Cosine similarity matrix | **REAL / FUNCTIONAL** | `cosine_similarity(self.X)` precomputed on init — full n x n matrix |
| User taste profile via TF-IDF | **REAL / FUNCTIONAL** | Weighted mean of TF-IDF vectors of liked movies shapes content score |

### 7.2 Collaborative Filtering

| Aspect | Status | Details |
|--------|--------|---------|
| User-item rating matrix | **REAL / FUNCTIONAL** | Built from `ratings.csv` as scipy `csr_matrix`, mean-centered |
| Matrix factorization (SVD) | **REAL / FUNCTIONAL** | `TruncatedSVD(n_components=min(k, min(M.shape)-1))` with k=50 |
| Item-item similarity | **REAL / FUNCTIONAL** | Computed from SVD item embeddings: `Vn @ Vn.T` |
| New user fold-in | **REAL / FUNCTIONAL** | New user ratings are projected into SVD space: `u @ V.T @ Vcat` |
| Rating prediction | **REAL / FUNCTIONAL** | Collaborative scores via SVD projection |

### 7.3 Hybrid Recommendation

| Aspect | Status | Details |
|--------|--------|---------|
| Score combination | **REAL / FUNCTIONAL** | `score = 0.4 * content + 0.6 * collaborative` (normalized) |
| Alpha weighting | **REAL / FUNCTIONAL** | `ALPHA = 0.4` (configurable constant) |
| Ranking and top-N | **REAL / FUNCTIONAL** | `np.argsort(-score)[:n]` |
| Genre filtering | **REAL / FUNCTIONAL** | Optional genre mask applied to scores |
| Exclusion of rated/hidden movies | **REAL / FUNCTIONAL** | Banned set applied |

### 7.4 Cold Start

| Aspect | Status | Details |
|--------|--------|---------|
| Detection | **REAL / FUNCTIONAL** | `MIN_RATINGS = 3` — fewer than 3 user ratings triggers cold start |
| Fallback strategy | **REAL / FUNCTIONAL** | Returns trending movies sorted by `trending_rank` then `popularity` |
| Genre-aware cold start | **REAL / FUNCTIONAL** | Optional genre filter applied to trending fallback |
| Cold start messaging | **REAL / FUNCTIONAL** | Returns "Rate 3 films to unlock personalised picks" in explanation |

### 7.5 Personalization

| Aspect | Status | Details |
|--------|--------|---------|
| User ratings to ML | **REAL / FUNCTIONAL** | `st.session_state.ratings` fed to `recommend(ratings=...)` |
| Genre preferences | **PARTIALLY IMPLEMENTED** | Profile page saves `favorite_genres` but `home.py` passes `user_prefs` (the full profile dict, not `ratings`) to `get_recommended_for_user()` — this doesn't pass actual `ratings` from session state! |
| Watch history | **NOT IMPLEMENTED** | No watch tracking |
| Favorites list | **NOT IMPLEMENTED** | Only watchlist exists |
| Negative feedback | **NOT IMPLEMENTED** | `hidden_ids` parameter exists in API but no UI for "Not Interested" |

### 7.6 Recommendation Explanations

| Aspect | Status | Details |
|--------|--------|---------|
| "Because you rated X" | **REAL / FUNCTIONAL** | `hybrid_model.py` line 131: finds most similar liked movie and generates explanation |
| Shared genres explanation | **REAL / FUNCTIONAL** | Line 132-134: "Shared genres: Drama, Thriller" |
| Collaborative signal | **REAL / FUNCTIONAL** | Line 135-136: "Viewers with similar taste rated it highly" |
| Hybrid score breakdown | **REAL / FUNCTIONAL** | Line 137: "Hybrid score 0.85 (content 0.72, collaborative 0.91)" |
| Cold start explanations | **REAL / FUNCTIONAL** | "Trending with the community right now" or "Rate 3 films to unlock personalised picks" |
| Similar movie explanations | **REAL / FUNCTIONAL** | "Similar to X, Content 0.85 - audience 0.72" |

### 7.7 Summary

**The ML/recommendation engine is genuinely functional.** It is NOT a mock or simulation. It implements:
- Real TF-IDF content-based filtering on MovieLens data
- Real TruncatedSVD collaborative filtering on 100K+ ratings
- Real hybrid combination with configurable alpha
- Real cold start handling
- Real data-driven explanations

**The biggest ML issue** is that the Home page doesn't actually feed user ratings to the recommender (see Section 7.5).

---

## 8. USER STATE / PERSISTENCE

### 8.1 State Storage

| Data | Storage Mechanism | Survives Page Navigation? | Survives Refresh? | Survives Restart? |
|------|-------------------|--------------------------|--------------------|--------------------|
| Watchlist | `st.session_state.watchlist` | Yes | No | No |
| Ratings | `st.session_state.ratings` | Yes | No | No |
| User profile | `st.session_state.user_profile` | Yes | No | No |
| Current page | `st.session_state.current_page` | Yes | No | No |
| Selected movie | `st.session_state.selected_movie_id` | Yes | No | No |
| Selected mood | `st.session_state.selected_mood` | Yes | No | No |
| Search queries | `st.session_state.global_search` / `discover_search` | Yes | No | No |

### 8.2 Persistence Classification

**Session-only (Streamlit session state).** ALL user data is lost on browser refresh or server restart.

There is:
- No localStorage
- No JSON file persistence
- No SQLite database
- No cookies
- No file-based session store

---

## 9. SEARCH / FILTERING / DISCOVERY

### 9.1 Discover Page Search

| Capability | Status | Details |
|------------|--------|---------|
| Title search | **IMPLEMENTED** | Substring match, case-insensitive |
| Genre search | **IMPLEMENTED** | Substring match in genre strings |
| Director search | **IMPLEMENTED** | Substring match |
| Cast search | **IMPLEMENTED** | Substring match in cast array |
| Overview/plot search | **IMPLEMENTED** | Substring match |
| Fuzzy matching | **NOT IMPLEMENTED** | Exact substring only |
| Semantic search | **NOT IMPLEMENTED** | Plain text matching, no embeddings |

### 9.2 Sense AI Prompt Search

| Capability | Status | Details |
|------------|--------|---------|
| Natural language query | **IMPLEMENTED** | Uses `hybrid_model.query()` — TF-IDF cosine similarity against movie documents |
| Genre/mood keywords | **IMPLEMENTED** | Genres and moods are part of TF-IDF document |
| Director/cast keywords | **IMPLEMENTED** | Included in document |
| Plot description | **IMPLEMENTED** | Overview is part of document |
| True semantic search | **NOT IMPLEMENTED** | TF-IDF keyword matching, not semantic embeddings |

### 9.3 Filtering

| Filter | Status | Location |
|--------|--------|----------|
| Genre multi-select | **IMPLEMENTED** | Discover page |
| Year range slider | **IMPLEMENTED** | Discover page (1990-2026) |
| Rating threshold | **IMPLEMENTED** | Discover page (0.0-10.0) |
| Language dropdown | **IMPLEMENTED** | Discover page |
| Sorting | **IMPLEMENTED** | Rating, Year, Title |
| Mood-based filtering | **IMPLEMENTED** | Mood Explorer (genre-to-mood mapping) |
| Pagination | **NOT IMPLEMENTED** | All results shown at once |

---

## 10. EXTERNAL SERVICES / APIs

### 10.1 TMDB API

| Aspect | Details |
|--------|---------|
| Service | The Movie Database (TMDB) API v3 |
| Purpose | Enrich MovieLens movies with poster, backdrop, overview, runtime, director, cast, language |
| Integration file | `data/enrich_tmdb.py` |
| API key required? | YES — free key from themoviedb.org |
| Currently functional? | **NOT RUN** — `tmdb_metadata.json` does not exist in the project |
| Runtime dependency? | NO — the app runs without it, using placeholder data |
| Failure behavior | Graceful — catalog falls back to `placehold.co` images and auto-generated overviews |

### 10.2 External Image Hosts

| Service | Usage |
|---------|-------|
| Unsplash (`images.unsplash.com`) | Poster/backdrop URLs in `sample_movies.py` (not used by Phase 3 catalog) |
| Google AIDA (`lh3.googleusercontent.com/aida-public/`) | Poster URLs for some sample movies + sidebar logo + topbar avatar |
| Placehold.co | Fallback poster/backdrop generator in `catalog.py` |
| TMDB Image CDN (`image.tmdb.org/t/p/`) | Used by `catalog.py` when `tmdb_metadata.json` exists |
| Google Fonts | Outfit, Plus Jakarta Sans, Material Symbols Outlined |

### 10.3 No Other External APIs

No Flask/FastAPI backend, no database server, no auth service, no analytics.

---

## 11. BUGS AND TECHNICAL DEBT

### CRITICAL

1. **`scipy` missing from `requirements.txt`** — `hybrid_model.py` imports `from scipy.sparse import csr_matrix`. The app will crash on first load if scipy is not installed.
   - File: `requirements.txt`

2. **Home page does NOT feed user ratings to the recommender** — `home.py` line 24-25 passes `user_prefs = st.session_state.get("user_profile", {})` to `get_recommended_for_user()`. The user_profile dict contains `name`, `favorite_genres`, etc. but NOT `ratings`. The recommendation service expects `ratings` key in the preferences dict. This means the "Recommended For You" section NEVER uses the hybrid model's collaborative filtering — it always falls back to cold start.
   - File: `src/pages/home.py` lines 24-25

### HIGH

3. **Default session state IDs are arbitrary** — `watchlist = [101, 102]`, `ratings = {101: 9.5, 102: 9.0}`, `selected_movie_id = 101`. These map to MovieLens movies (Bottle Rocket, Mr. Holland's Opus) which will appear pre-loaded in the watchlist/ratings with no context for the user. The ratings are on a 0-10 scale but MovieLens uses 0.5-5.0 — `hybrid_model.recommend()` clips values with `np.clip(vals - 2.5, 0, None)` so 9.5 would still work but is inconsistent.
   - File: `app.py` lines 42-46

4. **`about.py` is dead code** — `render_about_page()` is imported but never called. The "about-the-ai" route calls `render_sense_ai_page()` instead. The academic ML documentation page is unreachable.
   - File: `app.py` lines 20, 79-80

5. **No persistence** — All user data (watchlist, ratings, profile) is lost on page refresh. For a recommendation system that depends on accumulated user ratings, this is a fundamental problem.

### MEDIUM

6. **`content_model.py` is orphaned** — Phase 2 legacy code that imports `SAMPLE_MOVIES`. Not called by any active path. Creates confusion about which recommendation model is active.
   - File: `src/services/content_model.py`

7. **`employee_churn_backup.csv` is unrelated data** — A leftover from another project sitting in the `data/` directory.
   - File: `data/employee_churn_backup.csv`

8. **`ml_engine/dataset_profiler.py` is unrelated** — Generic dataset profiler targeting a "Churn" classification task. Never imported, not related to movie recommendations.
   - File: `ml_engine/dataset_profiler.py`

9. **Mood counts in `config.py` are fictional** — "2,118 Available", "1,482 Available" etc. are hardcoded static numbers that don't reflect actual catalog counts.
   - File: `src/config.py` lines 74, 89, etc.

10. **`get_movies_by_mood()` references `popularity` field** — `recommendation_service.py` line 52 sorts by `m["popularity"]`, which exists on catalog movies but used to not exist on sample movies. This would crash if sample_movies were used.
    - File: `src/services/recommendation_service.py` line 52

11. **README.md is stale** — Describes "25+ curated films" and a user path at `c:\Users\Devansh Sharma\OneDrive\...` which is incorrect. Does not mention Phase 3 MovieLens integration.
    - File: `README.md`

12. **Import style inconsistency** — `catalog.py` and `hybrid_model.py` use `from data.loader import ...` (no `src.` prefix) while everything else uses `from src.services...`. This works because Streamlit adds CWD to sys.path, but it's fragile.

### LOW

13. **Hero cycle shows "01 / 04" hardcoded** — The feature cycle counter never updates.
    - File: `src/components/hero_banner.py` line 81

14. **"Find Movies" button in Mood Explorer** is cosmetic — Shows a toast but results are already reactively filtered. The button is misleading.
    - File: `src/pages/mood_explorer.py` lines 304-305

15. **Notification bell is purely decorative** — Always shows a gold notification dot, no actual notification system.
    - File: `src/components/topbar.py` lines 46-54

16. **CSS file is 684 lines** — Some Streamlit-specific selectors may break on Streamlit updates.

---

## 12. DUPLICATE / CONFLICTING SYSTEMS

### 12.1 Two Movie Datasets

| System | File | Status |
|--------|------|--------|
| **MovieLens catalog** (Phase 3) | `data/movies.csv` + `data/ratings.csv` via `catalog.py` | **ACTIVE — the real system** |
| **Sample movies** (Phase 1/2) | `src/data/sample_movies.py` | **LEGACY — only used by orphaned `content_model.py`** |

### 12.2 Two Recommendation Implementations

| System | File | Status |
|--------|------|--------|
| **Hybrid model** (Phase 3) | `src/services/hybrid_model.py` | **ACTIVE — the real system** |
| **Content model** (Phase 2) | `src/services/content_model.py` | **ORPHANED — not imported anywhere active** |

### 12.3 Two "About" Pages

| System | File | Status |
|--------|------|--------|
| **Sense AI page** | `src/pages/sense_ai.py` | **ACTIVE — receives all "about" routes** |
| **Academic About page** | `src/pages/about.py` | **DEAD CODE — imported but never called** |

### 12.4 Conclusion

The **Phase 3 system** (catalog.py + hybrid_model.py + MovieLens data) is the active, real application. The Phase 1/2 remnants (sample_movies.py, content_model.py) are legacy code that should either be removed or repurposed. There is no actual conflict at runtime — the old code simply never executes.

---

## 13. CURRENT FEATURE MATRIX

| Feature | UI Exists | Logic Exists | Backend/Data Exists | Persistent | Real ML | Status |
|---------|-----------|-------------|---------------------|------------|---------|--------|
| Home page | Yes | Yes | Yes | No | Cold-start only (bug) | IMPLEMENTED (with bug) |
| Discover page | Yes | Yes | Yes | No | N/A (filter-based) | IMPLEMENTED |
| Search (Discover) | Yes | Yes | Yes | No | N/A (substring) | IMPLEMENTED |
| Search (Sense AI) | Yes | Yes | Yes | No | Yes TF-IDF | IMPLEMENTED |
| Genre filters | Yes | Yes | Yes | No | N/A | IMPLEMENTED |
| Year filters | Yes | Yes | Yes | No | N/A | IMPLEMENTED |
| Language filters | Yes | Yes | Yes | No | N/A | IMPLEMENTED |
| Movie details | Yes | Yes | Yes | No | N/A | IMPLEMENTED |
| Recommendations | Yes | Yes | Yes | No | Yes Hybrid | IMPLEMENTED (bug: ratings not passed on Home) |
| Similar movies | Yes | Yes | Yes | No | Yes Hybrid sim | IMPLEMENTED |
| Mood Explorer | Yes | Yes | Yes | No | Partial (genre mapping) | IMPLEMENTED |
| Watchlist | Yes | Yes | Session only | No | N/A | IMPLEMENTED (session only) |
| Ratings | Yes | Yes | Session only | No | Yes (when fed to ML) | IMPLEMENTED (session only) |
| Not Interested | No | Yes (API param) | No | No | Yes (exclusion) | NOT IMPLEMENTED (UI missing) |
| Top This Week / Trending | Yes | Yes | Yes | N/A | N/A (statistical) | IMPLEMENTED |
| Recommendation explanation | Yes | Yes | Yes | N/A | Yes | IMPLEMENTED |
| Sense AI / Prompt search | Yes | Yes | Yes | No | Yes TF-IDF | IMPLEMENTED |
| Taste profile visualization | No | No | Session only | No | No | NOT IMPLEMENTED |
| Mobile navigation | No | No | No | N/A | N/A | NOT IMPLEMENTED |
| About (Academic docs) | Yes (unreachable) | Yes | N/A | N/A | N/A | EXISTS but UNREACHABLE |
| User profile preferences | Yes | Yes | Session only | No | Not fully wired | PARTIALLY IMPLEMENTED |
| Notifications | Yes (visual only) | No | No | No | No | MOCK/HARDCODED |

---

## 14. REQUIREMENTS FOR THE FINAL PRODUCT

### MUST HAVE

1. **Fix the ratings to recommendation pipeline** — Home page "Recommended For You" must actually use the user's ratings from session state, not just the profile dict. This is a one-line fix.
2. **Run TMDB enrichment** — Execute `enrich_tmdb.py` with a TMDB API key to get real posters, backdrops, overviews, directors, cast. Without this, the app looks empty/broken.
3. **Add `scipy` to requirements.txt** — The app crashes without it.
4. **Basic persistence** — At minimum, save ratings and watchlist to a JSON file so they survive page refreshes. For a recommendation system, losing all user data on refresh defeats the purpose.
5. **Fix default session state** — Don't initialize watchlist/ratings with arbitrary movie IDs. Start empty.
6. **Route the About page** — Either make it reachable or remove it.

### SHOULD HAVE

7. **Responsive/mobile layout** — At least basic CSS media queries for tablet/mobile
8. **"Not Interested" button** — The ML backend already supports exclusion; just add a UI button
9. **Taste profile summary** — Show the user a visual summary of their taste based on their ratings
10. **Better poster fallbacks** — When TMDB data is missing, use a more visually appealing fallback than placehold.co
11. **Dynamic mood counts** — Replace hardcoded "2,118 Available" with actual counts from catalog
12. **Clean up dead code** — Remove or archive `content_model.py`, `sample_movies.py`, `employee_churn_backup.csv`, `dataset_profiler.py`

### NICE TO HAVE

13. **Fuzzy search** — Typo-tolerant search (e.g., using rapidfuzz)
14. **Paginated results** — Show results in pages rather than all at once
15. **Loading states** — Show spinners during initial model computation
16. **Better explanation UI** — Show content vs collaborative breakdown visually
17. **User onboarding** — Guide new users to rate 3+ movies to unlock personalized recommendations
18. **Export/import user data** — Save/load ratings as JSON

### DO NOT NEED RIGHT NOW

19. Deep learning models (PyTorch, neural CF)
20. Real-time collaborative filtering (requires multi-user infrastructure)
21. User authentication / multi-user support
22. Production deployment (Docker, cloud)
23. A/B testing framework
24. Analytics dashboard
25. Social features (sharing, friends)

---

## 15. RECOMMENDED FUTURE ARCHITECTURE

```
+-------------------------------------------------------------+
|  Streamlit Frontend (app.py)                                |
|  +-- Components (sidebar, topbar, cards, carousel, etc.)    |
|  +-- Pages (home, discover, mood, details, etc.)            |
|  +-- assets/styles.css                                      |
+----------------------------+--------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|  Service Layer                                              |
|  +-- MovieService     (search, filter, sort)                |
|  +-- RecommendationService  (recommendations API facade)    |
|  +-- UserService (NEW) (persist ratings, watchlist, prefs)  |
+----------------------------+--------------------------------+
                             |
              +--------------+--------------+
              v                             v
+------------------------+  +-------------------------+
|  HybridModel           |  |  UserStore (NEW)        |
|  +-- TF-IDF Content    |  |  +-- JSON file I/O      |
|  +-- SVD Collab        |  |  +-- Ratings             |
|  +-- Hybrid alpha=0.4  |  |  +-- Watchlist           |
|  +-- Cold Start        |  |  +-- Preferences         |
+----------+-------------+  +-------------------------+
           |
           v
+-------------------------------------------------------------+
|  Data Layer                                                 |
|  +-- data/movies.csv          (MovieLens)                   |
|  +-- data/ratings.csv         (MovieLens)                   |
|  +-- data/links.csv           (MovieLens to TMDB)           |
|  +-- data/tmdb_metadata.json  (enriched metadata)           |
|  +-- data/loader.py           (cached CSV reader)           |
+-------------------------------------------------------------+
```

**Key architectural decisions:**
1. **Keep Streamlit** — it's working well, the UI is polished, no need for a separate backend
2. **Add a simple `UserStore` service** — JSON file read/write for persistence
3. **Keep the existing HybridModel** — it's genuinely functional ML code
4. **Do NOT introduce Flask/FastAPI** — unnecessary complexity for this project scale
5. **Do NOT introduce a database** — JSON file persistence is sufficient for a capstone project

---

## 16. IMPLEMENTATION ROADMAP

### Phase 1: Critical Fixes (30-45 minutes)

**Objective:** Make the existing app fully functional and free of bugs.

| Task | File(s) | Priority |
|------|---------|----------|
| Add `scipy` to requirements.txt | `requirements.txt` | CRITICAL |
| Fix Home page to pass user ratings to recommender | `src/pages/home.py` | CRITICAL |
| Fix default session state (empty watchlist/ratings, valid default movie) | `app.py` | HIGH |
| Route "about" page properly (either add a nav route or merge into sense_ai) | `app.py` | HIGH |

**Files NOT to touch:** All services, components, CSS, data files.
**Expected result:** App runs without crashes, recommendations actually use user ratings.
**Risks:** Low — these are targeted one-line to few-line fixes.

### Phase 2: TMDB Enrichment (15-30 minutes)

**Objective:** Get real movie posters, backdrops, overviews, director, cast.

| Task | File(s) | Priority |
|------|---------|----------|
| Get a free TMDB API key | External | REQUIRED |
| Run `python data/enrich_tmdb.py` | `data/enrich_tmdb.py` | HIGH |
| Verify posters load correctly | Manual testing | HIGH |

**Files NOT to touch:** All source code — this is a data-only operation.
**Expected result:** 600 movies with real TMDB metadata, images, and descriptions.
**Risks:** Rate limiting (TMDB free tier is generous), network issues. Script is resumable.

### Phase 3: User Persistence (45-60 minutes)

**Objective:** Save user ratings, watchlist, and preferences to a JSON file.

| Task | File(s) | Priority |
|------|---------|----------|
| Create `src/services/user_store.py` | New file | HIGH |
| Implement JSON read/write for ratings, watchlist, preferences | New file | HIGH |
| Integrate into `app.py` session state initialization | `app.py` | HIGH |
| Integrate save calls into ratings page, watchlist page, profile page, movie details | `src/pages/ratings.py`, `watchlist.py`, `profile.py`, `movie_details.py` | HIGH |

**Files NOT to touch:** ML models, catalog, CSS, components.
**Expected result:** User data survives page refresh and app restart.
**Risks:** Medium — need to handle file I/O errors, concurrent writes in Streamlit.

### Phase 4: UI Polish and Cleanup (30-45 minutes)

**Objective:** Clean up dead code, fix mock elements, improve UX.

| Task | File(s) | Priority |
|------|---------|----------|
| Remove `content_model.py` (orphaned) | `src/services/content_model.py` | MEDIUM |
| Remove `employee_churn_backup.csv` | `data/employee_churn_backup.csv` | LOW |
| Remove `ml_engine/dataset_profiler.py` | `ml_engine/dataset_profiler.py` | LOW |
| Replace hardcoded mood counts with actual catalog counts | `src/pages/mood_explorer.py` or `src/config.py` | MEDIUM |
| Add "Not Interested" button to movie cards/details | Components + recommendation_service | MEDIUM |
| Update README.md | `README.md` | LOW |

**Files NOT to touch:** ML models, core catalog logic, CSS design system.
**Expected result:** Cleaner codebase, dynamic mood counts, "Not Interested" feature.
**Risks:** Low.

### Phase 5: Optional Enhancements (60-90 minutes if time permits)

| Task | Priority |
|------|----------|
| User onboarding flow (rate 3+ movies prompt) | NICE TO HAVE |
| Taste profile visualization on Profile page | NICE TO HAVE |
| Responsive CSS media queries | NICE TO HAVE |
| Loading spinner during model init | NICE TO HAVE |

**Total estimated time to strong MVP: 2-3 hours**

---

## 17. CLAUDE IMPLEMENTATION BRIEF

### Current Architecture

- **Framework:** Streamlit (Python)
- **Entry point:** `app.py` — run with `streamlit run app.py`
- **CSS:** `assets/styles.css` (684 lines, custom design system)
- **Config:** `src/config.py` (constants, colors, nav, moods, default user)

### Current Data Sources

1. `data/movies.csv` — MovieLens ml-latest-small (9,742 movies)
2. `data/ratings.csv` — MovieLens ml-latest-small (100,836 ratings from 610 users)
3. `data/links.csv` — MovieLens to TMDB ID mapping
4. `data/tmdb_metadata.json` — **DOES NOT YET EXIST** (created by `data/enrich_tmdb.py`)

### Current Recommendation Implementation

- **Active model:** `src/services/hybrid_model.py` — `HybridModel` class
  - Content: TF-IDF on genres/moods/director/cast/tags/overview
  - Collaborative: TruncatedSVD (k=50) on user-item rating matrix
  - Hybrid: alpha=0.4 content + 0.6 collaborative
  - Cold start: trending/genre fallback when < 3 ratings
  - Explanations: data-driven "Because you rated X" + shared genres + collaborative signal
- **API facade:** `src/services/recommendation_service.py`
- **Catalog builder:** `src/services/catalog.py`
- **Data loader:** `data/loader.py`

### Critical Problems to Fix

1. **Add `scipy` to `requirements.txt`** — crashes without it
2. **Fix `home.py` to pass `st.session_state.ratings` to the recommender** — currently passes profile dict instead of ratings, so Home page always shows cold-start results
3. **Fix default session state** — remove pre-loaded watchlist/ratings IDs (101, 102)
4. **Run TMDB enrichment** or handle missing metadata gracefully

### Target Architecture

Same as current, plus:
- **New:** `src/services/user_store.py` — JSON file persistence for ratings/watchlist/preferences
- **Fix:** Wire user ratings from session state into recommendation calls
- **Clean:** Remove orphaned files (`content_model.py`, `sample_movies.py`, `employee_churn_backup.csv`, `dataset_profiler.py`)

### Implementation Order

1. Fix critical bugs (scipy, ratings pipeline, defaults)
2. Run TMDB enrichment
3. Add JSON persistence
4. Clean up dead code
5. Optional UI polish

### Important Files — DO NOT unnecessarily rewrite

| File | Reason to preserve |
|------|-------------------|
| `src/services/hybrid_model.py` | **Core ML engine — working and functional** |
| `src/services/catalog.py` | **Working catalog builder** |
| `src/services/recommendation_service.py` | **Clean API facade** |
| `data/loader.py` | **Working data loader** |
| `assets/styles.css` | **684 lines of polished CSS — matches Stitch design** |
| `src/config.py` | **Design tokens and app constants** |
| `src/pages/mood_explorer.py` | **Most complex page — faithfully matches Stitch reference** |
| `design_reference/*` | **Keep as reference** |

### Design Constraints

- Obsidian (#131315) + Champagne Gold (#f2ca50) color scheme — do not change
- Outfit + Plus Jakarta Sans typography — do not change
- Material Symbols Outlined icons — do not change
- Dark mode only — do not add light mode
- Streamlit framework — do not replace with React/Next.js

### Functional Requirements

- Movie recommendations must use hybrid ML model (not hardcoded)
- Cold start must work for new users (< 3 ratings)
- Recommendations must improve as user rates more movies
- Explanations must be data-driven
- All MovieLens data must be the primary source
- TMDB metadata must enrich but not replace MovieLens data

### ML Requirements

- TF-IDF content-based filtering — ALREADY WORKS
- TruncatedSVD collaborative filtering — ALREADY WORKS
- Hybrid combination — ALREADY WORKS
- Cold start handling — ALREADY WORKS
- User ratings must flow from UI to session state to recommendation service to hybrid model

### Persistence Requirements

- Ratings must survive page refresh
- Watchlist must survive page refresh
- User preferences must survive page refresh
- JSON file is sufficient (no database needed)

### Testing Requirements

- `tests/test_smoke.py` exists but tests old sample_movies imports
- Update to test current catalog/hybrid pipeline
- Basic smoke tests: app starts, catalog loads, recommendations return results

> **Do not rebuild the project from scratch.**
> The ML engine, catalog, service layer, components, and CSS are all functional.
> Focus on targeted fixes, TMDB enrichment, and persistence.

---

## 18. FINAL EXECUTIVE SUMMARY

### 1. What Currently Works

- Full Streamlit UI with 8 pages and premium Obsidian/Gold design
- MovieLens data loading (9,742 movies, 100,836 ratings)
- TF-IDF content-based model on real MovieLens data
- TruncatedSVD collaborative filtering on real ratings
- Hybrid recommendation with alpha=0.4 weighting
- Cold start fallback for new users
- Data-driven recommendation explanations
- Natural language prompt search (TF-IDF cosine)
- Multi-filter Discover page (genre, year, rating, language, sort)
- Mood Explorer with 6 moods and calibration toolbar
- Watchlist and ratings management (session-scoped)
- Similar movies via hybrid similarity
- Movie details with poster, metadata, watchlist toggle, rating slider

### 2. What is Fake/Mock

- Notification bell (purely visual)
- Runtime Engine Status panel (hardcoded text)
- "4K Ultra HD", "IMAX Enhanced", "PG-13" badges (hardcoded)
- "Live Stream Analytics" badge (decorative)
- Mood counts ("2,118 Available") — hardcoded, not from catalog
- Curation Rationale text — static, never changes
- Hero cycle counter "01 / 04" — hardcoded
- "Find Movies" button — shows toast only

### 3. What is Missing

- Persistence (all user data lost on refresh)
- TMDB metadata (posters, overviews, directors, cast)
- "Not Interested" UI (backend supports it)
- Taste profile visualization
- Mobile responsive layout
- User onboarding
- About page is unreachable

### 4. Biggest Technical Problem

**No persistence.** All user ratings, watchlist, and preferences are stored only in Streamlit session state and are lost on page refresh. For a recommendation system that depends on accumulated user feedback, this is the most fundamental gap.

### 5. Biggest ML Problem

**Home page doesn't feed user ratings to the recommender.** The `home.py` passes the user profile dict (name, favorite_genres, etc.) to `get_recommended_for_user()` instead of the actual ratings dict from session state. This means the hybrid model's collaborative filtering never activates from the Home page — users always see cold-start trending results.

### 6. Biggest UI Problem

**No TMDB metadata = no real movie posters or descriptions.** Without running the TMDB enrichment script, all 600 catalog movies show `placehold.co` placeholder images and auto-generated one-line descriptions. The UI looks visually empty despite having a premium CSS design system.

### 7. Fastest Path to a Strong MVP

1. Add `scipy` to requirements.txt (1 min)
2. Fix `home.py` to pass ratings (5 min)
3. Fix default session state (5 min)
4. Run TMDB enrichment (15 min)
5. Add JSON persistence (45 min)
6. Clean up dead code (15 min)

### 8. Estimated Total Implementation Time

**2-3 hours** for a strong, polished MVP with real ML recommendations, real movie metadata, and persistent user data.

### 9. Recommended Implementation Order

1. **Critical bug fixes** (scipy, ratings pipeline, defaults) — 30 min
2. **TMDB enrichment** — 15-30 min
3. **JSON persistence** — 45-60 min
4. **Dead code cleanup** — 15 min
5. **Optional polish** (responsive, onboarding, taste viz) — 60+ min if time permits
