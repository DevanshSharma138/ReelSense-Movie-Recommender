"""
ReelSense - Home / Discover Page Module
"""

import streamlit as st
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.components.hero_banner import render_hero_banner
from src.components.movie_carousel import render_movie_carousel
from src.components.trending_grid import render_trending_grid
from src.components.mood_matrix import render_mood_matrix

def render_home_page():
    # 1. Featured Hero Spotlight Banner
    trending = RecommendationService.get_trending_movies(limit=5)
    all_movies = MovieService.get_all_movies()
    featured_movie = trending[0] if trending else (all_movies[0] if all_movies else None)
    cycle_movies = trending[1:4] if len(trending) > 1 else all_movies[1:4]

    render_hero_banner(featured_movie, cycle_movies=cycle_movies)

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # 2. Recommended For You Carousel (Real Ratings -> Hybrid Recommender)
    user_ratings = st.session_state.get("ratings", {})
    user_profile = st.session_state.get("user_profile", {})
    not_interested = list(st.session_state.get("not_interested", set()))

    rec_prefs = {
        "ratings": user_ratings,
        "favorite_genres": user_profile.get("favorite_genres", []),
        "hidden_ids": not_interested,
    }
    recommended_movies = RecommendationService.get_recommended_for_user(rec_prefs, limit=6)
    rec_mode = RecommendationService.get_recommendation_mode(rec_prefs)

    n_ratings = len(user_ratings)
    if rec_mode == "hybrid":
        rec_title = "Recommended For You (Hybrid Personalization)"
        rec_subtitle = f"Calibrated from your {n_ratings} ratings using TF-IDF content similarity & SVD collaborative taste vectors."
        rec_tag = "Hybrid Recommendation Active"
    else:
        rec_title = "Recommended For You (Community Favorites)"
        rec_subtitle = f"Rate {max(0, 3 - n_ratings)} more movie{'s' if (3 - n_ratings) != 1 else ''} to unlock personalized hybrid recommendations."
        rec_tag = "Trending Fallback Active"

    render_movie_carousel(
        title=rec_title,
        subtitle=rec_subtitle,
        movies=recommended_movies,
        tag=rec_tag,
        view_all_page="discover",
        carousel_id="home_rec"
    )

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # 3. Trending Across ReelSense (Numbered Editorial Rankings 01-05)
    ranked_movies = RecommendationService.get_movies_by_rank()
    render_trending_grid(ranked_movies)

    # 4. Mood Vault Matrix (6 Sensory Spectrum Gradient Tiles)
    render_mood_matrix()

    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

    # 5. Hidden Gems Section
    hidden_gems = RecommendationService.get_hidden_gems(limit=6)
    render_movie_carousel(
        title="Curator Hidden Gems",
        subtitle="Critically acclaimed masterworks waiting to be discovered.",
        movies=hidden_gems,
        tag="Curator Selection",
        view_all_page="discover",
        carousel_id="home_gems"
    )
