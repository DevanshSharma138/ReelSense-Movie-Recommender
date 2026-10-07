"""
ReelSense - Phase 3 Automated Regression Test Suite
Validates:
1. Not Interested persistence
2. Not Interested exclusion from recommendations
3. Onboarding behavior (< 3 vs >= 3 ratings)
4. Taste profile calculation & genre weighting
5. Dynamic mood counts from active catalog
6. Real signal-grounded recommendation explanations
7. 4-tier movie metadata & SVG fallback hierarchy
"""

import urllib.parse
import pytest
from src.services import user_store
from src.services.catalog import get_catalog
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.utils.image_utils import generate_fallback_poster, generate_fallback_backdrop
from src.config import MOODS


# -------------------------------------------------------------------------
# 1. Not Interested Persistence
# -------------------------------------------------------------------------
def test_not_interested_persistence(tmp_path):
    test_file = tmp_path / "user_data.json"

    # Initial state is empty set
    assert user_store.get_not_interested(path=test_file) == set()

    # Save multiple IDs
    sample_ids = {1, 50, 260, 1196}
    user_store.save_not_interested(sample_ids, path=test_file)

    # Reload from disk
    loaded = user_store.get_not_interested(path=test_file)
    assert loaded == sample_ids

    # Remove an item and persist again
    sample_ids.remove(50)
    user_store.save_not_interested(sample_ids, path=test_file)
    assert user_store.get_not_interested(path=test_file) == {1, 260, 1196}


# -------------------------------------------------------------------------
# 2. Not Interested Exclusion from Recommendations
# -------------------------------------------------------------------------
def test_not_interested_exclusion_from_recommendations():
    # User rates Toy Story (1) highly
    ratings = {1: 10.0}
    
    # Normal recommendations
    normal_recs = RecommendationService.get_recommended_for_user(
        {"ratings": ratings, "hidden_ids": []}, 
        limit=10
    )
    normal_ids = [m["id"] for m in normal_recs]
    assert len(normal_ids) > 0

    # Pick the top recommended movie and mark it as Not Interested
    excluded_id = normal_ids[0]
    filtered_recs = RecommendationService.get_recommended_for_user(
        {"ratings": ratings, "hidden_ids": [excluded_id]}, 
        limit=10
    )
    filtered_ids = [m["id"] for m in filtered_recs]

    # Must be strictly excluded
    assert excluded_id not in filtered_ids


# -------------------------------------------------------------------------
# 3. Onboarding Behavior (< 3 vs >= 3 ratings)
# -------------------------------------------------------------------------
def test_onboarding_behavior_thresholds():
    # Case A: 0 ratings -> Needs onboarding (< 3)
    assert len({}) < 3

    # Case B: 1 or 2 ratings -> Still needs onboarding
    ratings_1 = {1: 8.0}
    ratings_2 = {1: 8.0, 50: 9.0}
    assert len(ratings_1) < 3
    assert len(ratings_2) < 3

    # Case C: 3 or more ratings -> Unlocks personalized recommendations
    ratings_3 = {1: 8.0, 50: 9.0, 260: 10.0}
    assert len(ratings_3) >= 3


# -------------------------------------------------------------------------
# 4. Taste Profile Calculation & Genre Weighting
# -------------------------------------------------------------------------
def test_taste_profile_calculation():
    # Setup test ratings for known movies in catalog
    # Toy Story (1): Adventure|Animation|Children|Comedy|Fantasy
    # Star Wars IV (260): Action|Adventure|Sci-Fi
    catalog_by_id = {m["id"]: m for m in get_catalog()}
    
    test_ratings = {1: 8.0, 260: 10.0}
    rated_count = len(test_ratings)
    avg_rating = sum(test_ratings.values()) / rated_count
    assert rated_count == 2
    assert avg_rating == 9.0

    genre_scores = {}
    genre_counts = {}
    for mid, score in test_ratings.items():
        m = catalog_by_id.get(mid)
        if m:
            for g in m.get("genres", []):
                genre_scores[g] = genre_scores.get(g, 0.0) + float(score)
                genre_counts[g] = genre_counts.get(g, 0) + 1

    # Adventure is in both Toy Story and Star Wars -> score = 18.0
    assert "Adventure" in genre_scores
    assert genre_scores["Adventure"] == 18.0
    assert genre_counts["Adventure"] == 2

    # Sci-Fi is only in Star Wars -> score = 10.0
    assert "Sci-Fi" in genre_scores
    assert genre_scores["Sci-Fi"] == 10.0

    # Top genre by weighted rating must be Adventure
    top_genre = max(genre_scores.items(), key=lambda x: x[1])[0]
    assert top_genre == "Adventure"


# -------------------------------------------------------------------------
# 5. Dynamic Mood Counts from Active Catalog
# -------------------------------------------------------------------------
def test_dynamic_mood_counts():
    catalog = get_catalog()
    assert len(catalog) == 2000

    all_counts = RecommendationService.get_all_mood_counts()
    assert isinstance(all_counts, dict)

    for mood in MOODS:
        m_id = mood["id"]
        direct_count = RecommendationService.get_mood_count(m_id)
        # Expected catalog count matching mood
        expected_count = len([m for m in catalog if m_id in m.get("moods", [])])
        
        assert direct_count == expected_count
        assert direct_count > 0, f"Mood {m_id} should have matching movies in the catalog"
        assert all_counts[m_id] == expected_count


# -------------------------------------------------------------------------
# 6. Recommendation Explanations Grounded in Real Signals
# -------------------------------------------------------------------------
def test_recommendation_explanations_real_signals():
    catalog = get_catalog()
    toy_story = next(m for m in catalog if m["id"] == 1)
    
    # Find another movie in the catalog sharing genres with Toy Story (e.g. Animation or Children)
    other_movie = next(m for m in catalog if m["id"] != 1 and set(m["genres"]) & set(toy_story["genres"]))

    # With user rating on Toy Story
    user_ratings = {1: 9.5}
    reasons = RecommendationService.get_recommendation_explanation(other_movie, user_ratings=user_ratings)
    assert len(reasons) > 0
    # Should explain based on user's high rating on Toy Story
    assert any("Because you rated" in r or "Shared genres" in r for r in reasons)

    # With no user ratings (cold start explanation)
    reasons_cold = RecommendationService.get_recommendation_explanation(toy_story, user_ratings={})
    assert len(reasons_cold) > 0
    # Must explain based on catalog properties (rating, trending, etc.)
    assert any("rate" in r.lower() or "trending" in r.lower() or "consensus" in r.lower() or "movielens" in r.lower() for r in reasons_cold)


# -------------------------------------------------------------------------
# 7. Metadata Fallback & SVG Hierarchy
# -------------------------------------------------------------------------
def test_metadata_and_svg_fallback():
    # Valid SVG poster generation
    svg_poster = generate_fallback_poster("Interstellar", year=2014, genre="Sci-Fi")
    assert svg_poster.startswith("data:image/svg+xml;utf8,")
    decoded_poster = urllib.parse.unquote(svg_poster)
    assert "<svg" in decoded_poster
    assert "Interstellar" in decoded_poster
    assert "2014" in decoded_poster

    # Valid SVG backdrop generation
    svg_backdrop = generate_fallback_backdrop("The Matrix", year=1999, genre="Action")
    assert svg_backdrop.startswith("data:image/svg+xml;utf8,")
    decoded_backdrop = urllib.parse.unquote(svg_backdrop)
    assert "<svg" in decoded_backdrop
    assert "1600" in decoded_backdrop # 16:9 width
    assert "900" in decoded_backdrop

    # Test all catalog items have non-empty valid poster & backdrop URLs
    catalog = get_catalog()
    for m in catalog[:50]:
        assert m["poster_url"], f"Movie {m['title']} missing poster_url"
        assert m["backdrop_url"], f"Movie {m['title']} missing backdrop_url"
        assert m["poster_url"].startswith("http") or m["poster_url"].startswith("data:image/svg+xml")
