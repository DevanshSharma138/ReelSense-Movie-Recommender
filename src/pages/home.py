"""
ReelSense - Home / Discover Page Module (Phase 5)
Renders the 6 homepage sections in exact specified order:
  1. SECTION 1: HERO (Personalized recommendation hero, never rated/hidden)
  2. SECTION 2: RECOMMENDED FOR YOU (Up to 12 hybrid recommendations, match %, explanations)
  3. SECTION 3: BECAUSE YOU LIKED [MOVIE TITLE] (Up to 3 rows for 4/5★ rated films, most recent first)
  4. SECTION 4: MORE [TOP GENRE] FOR YOU (Rating-weighted top genre hybrid picks)
  5. SECTION 5: TRENDING THIS WEEK (Existing trending velocity ranking, no duplicates)
  6. SECTION 6: MOOD EXPLORER (Sensory spectrum mood matrix)
Global rule: Strict duplicate prevention across all sections.
"""

import streamlit as st
from src.services.catalog import Catalog
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services import user_state
from src.pages.onboarding import render_onboarding_page
from src.components.hero_banner import render_hero_banner
from src.components.movie_carousel import render_movie_carousel
from src.components.trending_grid import render_trending_grid
from src.components.mood_matrix import render_mood_matrix
from src.utils.ui_helpers import render_html


def render_home_page():
    # Phase 3: First-time taste onboarding check
    # When no ratings exist and onboarding has not been done or skipped, show dedicated onboarding view
    if not user_state.is_onboarding_done():
        render_onboarding_page()
        return

    # Gather persisted user state
    user_ratings = st.session_state.get("ratings", {})
    user_profile = st.session_state.get("user_profile", {})
    not_interested = set(st.session_state.get("not_interested", set()))
    watchlist = list(st.session_state.get("watchlist", []))

    # Global duplicate prevention tracker:
    # A movie must appear at most once across the entire homepage!
    # Initialize with all rated movies and hidden movies so they are strictly never recommended.
    displayed_movie_ids = set(int(k) for k in user_ratings.keys()) | set(int(x) for x in not_interested)

    n_ratings = len(user_ratings)
    if n_ratings >= 3:
        render_html(f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1.25rem;">
            <span style="background: rgba(242, 202, 80, 0.15); color: #f2ca50; border: 1px solid rgba(242, 202, 80, 0.35); padding: 4px 14px; border-radius: 9999px; font-size: 0.8rem; font-weight: 700;">
                ✨ Personalized Picks Active · {n_ratings} Ratings Calibrated
            </span>
        </div>
        """)

    # -------------------------------------------------------------------------
    # SECTION 1: HERO
    # Feature highest-ranked eligible personalized recommendation, never rated/hidden
    # -------------------------------------------------------------------------
    rec_prefs = {
        "ratings": user_ratings,
        "watchlist": watchlist,
        "favorite_genres": user_profile.get("favorite_genres", []),
        "hidden_ids": list(not_interested),
    }

    hero_candidates = RecommendationService.get_recommended_for_user(
        rec_prefs,
        limit=6,
        exclude=displayed_movie_ids
    )

    if not hero_candidates:
        hero_candidates = RecommendationService.get_trending_movies(
            limit=6,
            exclude=displayed_movie_ids
        )

    featured_movie = hero_candidates[0] if hero_candidates else None
    cycle_movies = hero_candidates[1:5] if len(hero_candidates) > 1 else []

    if featured_movie:
        displayed_movie_ids.add(featured_movie["id"])
        for cm in cycle_movies:
            displayed_movie_ids.add(cm["id"])

    render_hero_banner(featured_movie, cycle_movies=cycle_movies)
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 2: RECOMMENDED FOR YOU
    # Up to 12 eligible recommendations ranked by hybrid engine
    # -------------------------------------------------------------------------
    recommended_movies = RecommendationService.get_recommended_for_user(
        rec_prefs,
        limit=12,
        exclude=displayed_movie_ids
    )

    # Strictly filter against displayed IDs and deduplicate
    final_rec_movies = []
    for m in recommended_movies:
        mid = m["id"]
        if mid not in displayed_movie_ids:
            final_rec_movies.append(m)
            displayed_movie_ids.add(mid)
        if len(final_rec_movies) >= 12:
            break

    rec_mode = RecommendationService.get_recommendation_mode(rec_prefs)
    if rec_mode == "hybrid":
        rec_title = "Recommended For You (Hybrid Personalization)"
        rec_subtitle = f"Calibrated from your {n_ratings} ratings using TF-IDF content similarity & SVD collaborative taste vectors."
        rec_tag = "Hybrid Recommendation Active"
    elif n_ratings > 0 or len(watchlist) > 0:
        rec_title = "Recommended For You (Personalized for Your Taste)"
        rec_subtitle = f"Calibrated from your {n_ratings} ratings and {len(watchlist)} saved vault titles."
        rec_tag = "Personalized Picks Active"
    else:
        rec_title = "Recommended For You (Community Favorites)"
        rec_subtitle = "Rate movies or save titles to your Vault to unlock personalized recommendations."
        rec_tag = "Trending Fallback Active"

    render_movie_carousel(
        title=rec_title,
        subtitle=rec_subtitle,
        movies=final_rec_movies,
        tag=rec_tag,
        view_all_page="discover",
        carousel_id="home_rec"
    )
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 3: BECAUSE YOU LIKED [MOVIE TITLE]
    # One row for each film rated 4 or 5 stars (up to 3 rows, most recent first)
    # -------------------------------------------------------------------------
    liked_movie_ids = [
        int(mid) for mid, score in reversed(list(user_ratings.items()))
        if float(score) >= 4.0 and int(mid) not in not_interested
    ]

    cat_by_id = Catalog.get_by_id()
    n_liked_rows = 0
    for liked_mid in liked_movie_ids:
        if n_liked_rows >= 3:
            break
        liked_movie = cat_by_id.get(liked_mid)
        if not liked_movie:
            continue

        similar_movies = RecommendationService.get_because_you_liked(
            liked_mid,
            limit=6,
            exclude=displayed_movie_ids
        )

        final_similar = []
        for m in similar_movies:
            mid = m["id"]
            if mid not in displayed_movie_ids:
                final_similar.append(m)
                displayed_movie_ids.add(mid)
            if len(final_similar) >= 6:
                break

        if final_similar:
            liked_title = liked_movie["title"]
            render_movie_carousel(
                title=f"Because You Liked {liked_title}",
                subtitle=f"Titles sharing thematic resonance and critical affinity with {liked_title}.",
                movies=final_similar,
                tag="Similarity Resonance",
                view_all_page="discover",
                carousel_id=f"byl_{liked_mid}"
            )
            st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
            n_liked_rows += 1

    # -------------------------------------------------------------------------
    # SECTION 4: MORE [TOP GENRE] FOR YOU
    # Determined using rating-weighted genre strength, filtered by hybrid engine
    # -------------------------------------------------------------------------
    top_genre, genre_picks = RecommendationService.get_top_genre_picks(
        ratings=user_ratings,
        limit=6,
        exclude=displayed_movie_ids
    )

    final_genre_picks = []
    for m in genre_picks:
        mid = m["id"]
        if mid not in displayed_movie_ids:
            final_genre_picks.append(m)
            displayed_movie_ids.add(mid)
        if len(final_genre_picks) >= 6:
            break

    if final_genre_picks:
        if top_genre:
            genre_title = f"More {top_genre} For You"
            genre_sub = f"Spotlight on your highest-rated cinema genre: {top_genre}."
            genre_tag = f"{top_genre} Affinity"
        else:
            genre_title = "More Acclaimed Cinema For You"
            genre_sub = "Curated high-rating selections across the master library."
            genre_tag = "Curator Spotlight"

        render_movie_carousel(
            title=genre_title,
            subtitle=genre_sub,
            movies=final_genre_picks,
            tag=genre_tag,
            view_all_page="discover",
            carousel_id="home_genre"
        )
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 5: TRENDING THIS WEEK
    # Editorial community velocity rankings (01-05), strictly excluding displayed
    # -------------------------------------------------------------------------
    ranked_trending = RecommendationService.get_trending_movies(
        limit=5,
        exclude=displayed_movie_ids
    )

    final_trending = []
    for m in ranked_trending:
        mid = m["id"]
        if mid not in displayed_movie_ids:
            final_trending.append(m)
            displayed_movie_ids.add(mid)
        if len(final_trending) >= 5:
            break

    if final_trending:
        render_trending_grid(final_trending)
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 6: MOOD EXPLORER
    # Sensory Spectrum Mood Matrix (6 gradient spectrum tiles)
    # -------------------------------------------------------------------------
    render_mood_matrix()
