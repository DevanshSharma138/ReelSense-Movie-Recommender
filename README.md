# ReelSense — AI-Powered Movie Discovery & Recommendation Platform

> **Tagline:** Find films that feel like you.  
> **Project Type:** B.Tech CSE (AI & ML) Capstone Frontend & Recommendation Platform

---

## 📌 Project Overview

**ReelSense** is a premium cinematic streaming-style web interface and movie recommendation system built using Python and Streamlit. Designed with modern streaming platform UI aesthetics (Obsidian Black, Charcoal, and Champagne Gold accent palette), ReelSense provides an intuitive interface for movie discovery, mood-based exploration, personal watchlists, user ratings, and explainable AI recommendations.

---

## 🎨 Design System & Color Palette

- **Main Background:** Obsidian Black (`#101010`)
- **Sidebar & Cards:** Charcoal (`#202020`)
- **Secondary Surfaces:** Dark Charcoal (`#292929`)
- **Primary Accent:** Champagne Gold (`#D6AD60`)
- **Primary Text:** Warm Ivory (`#F4EBDD`)
- **Secondary Text:** Soft Grey (`#A0A0A0`)
- **Borders & Dividers:** Subtle Grey (`#363636`)

---

## ✨ Features & Implemented Pages

1. **🎬 Home Page:**
   - Cinematic Featured Hero Banner featuring *Interstellar* with dark gradient overlay, metadata badges, overview, and quick action buttons.
   - **Recommended for You:** Personalized recommendation carousel powered by user genre-affinity heuristic.
   - **Trending Now:** Highlighting popular trending titles.
   - **Hidden Gems:** Curated lesser-known masterworks.
   - **Explore by Mood:** Interactive mood selection cards (Happy, Relaxed, Thrilling, Romantic, Emotional, Mind-blown).
   - **Why This Movie Was Recommended:** Transparent AI explanation box detailing key similarity rationale.
   - **My Watchlist Preview:** Quick access row to saved movies.

2. **🔍 Discover Page:**
   - Real-time global search field filtering by movie title, director, cast, or genre.
   - Multi-select genre filters, release year range slider, minimum rating threshold, language filter, and sorting (Rating, Release Year, Title).
   - Responsive poster grid with matching movie counts and reset options.

3. **🎭 Mood Explorer Page:**
   - 6 mood filters with visual icon cards.
   - Optional genre refinement, release era selection, and minimum rating criteria.
   - Visual recommendation grid matching chosen emotional vibes.

4. **🎞️ Movie Details Page:**
   - Cinematic backdrop banner, poster, metadata badges, director, cast, and full overview.
   - Interactive Watchlist toggle and persistent User Rating slider.
   - "Why We Recommend This" rationale section.
   - "Similar Movies You Might Enjoy" carousel.

5. **🔖 My Watchlist Page:**
   - Grid layout of saved titles with sorting options and instant remove buttons.
   - Persistent across navigation via Streamlit session state.

6. **⭐ My Ratings Page:**
   - Manage previously rated movies, update ratings on the fly, or delete ratings.

7. **👤 My Profile Page:**
   - User profile customization (Name, Favorite Genres, Preferred Language, Preferred Era, Minimum Rating).

8. **🤖 About the AI Page (Academic Documentation):**
   - In-depth explanation of Content-Based (TF-IDF + Cosine Similarity), Collaborative Filtering (Matrix Factorization / SVD), Hybrid Ensembling, Explainability, Evaluation Metrics (Precision@K, Recall@K, MAP, Diversity), and dataset technical architecture.

---

## 📁 Directory Structure

```
RS Project/
├── app.py                     # Main application entry point & layout shell
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── assets/
│   └── styles.css             # Custom CSS styling (Obsidian, Charcoal, Champagne Gold)
└── src/
    ├── config.py              # Palette tokens & app constants
    ├── data/
    │   └── sample_movies.py   # Curated 25+ movie dataset with rich metadata
    ├── services/
    │   ├── movie_service.py          # Search, filtering, & sorting service
    │   └── recommendation_service.py  # Recommendation algorithms & ML hooks
    ├── components/
    │   ├── sidebar.py         # Branding & left sidebar navigation
    │   ├── topbar.py          # Search bar & user header
    │   ├── hero_banner.py     # Featured movie hero banner
    │   ├── movie_card.py       # Reusable poster card component
    │   └── movie_carousel.py   # Horizontal carousel / grid layout
    └── pages/
        ├── home.py            # Home page logic
        ├── discover.py        # Discover & search page logic
        ├── mood_explorer.py   # Mood-based engine logic
        ├── movie_details.py   # Details & rating logic
        ├── watchlist.py       # Watchlist management logic
        ├── ratings.py         # User ratings page logic
        ├── profile.py         # Profile & preferences logic
        └── about.py           # Academic ML documentation logic
```

---

## 🚀 How to Run the Application

1. Open PowerShell or Command Prompt in the project root:
   ```bash
   cd "c:\Users\Devansh Sharma\OneDrive\Dokumen\RS Project"
   ```

2. Activate the virtual environment (if not already active):
   ```bash
   venv\Scripts\activate
   ```

3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

4. The application will open automatically in your default browser at `http://localhost:8501`.

---

## 🛠️ ML Engine Integration Guide (For Future Model Training)

The application features a modular service layer located in `src/services/recommendation_service.py`. When you train your ML model (e.g., TF-IDF on TMDB 5000, Cosine Similarity matrix, or PyTorch Collaborative Filtering embeddings), simply update the functions in `recommendation_service.py`:
- `get_recommended_for_user(user_preferences)`
- `get_similar_movies(movie)`
- `get_movies_by_mood(mood_name)`

The frontend UI components will automatically utilize your trained model predictions without requiring any UI modifications.
