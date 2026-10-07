"""
ReelSense - Phase 5.5 Catalog Expansion & Metadata / Poster Integrity Tests

Verifies:
  Test A: Movie identity consistency (unique IDs, unique catalog entries)
  Test B: TMDB mapping sanity (cross-source title & year matching, path syntax)
  Test C: 4-tier image fallback hierarchy (Tier 1 -> Tier 2 -> Tier 3 -> Tier 4 resilience)
  Test D: Expanded catalog size (within 1,500-2,500 range, no missing years/genres)
  Test E: Search & filter functionality across the expanded catalog
  Test F: Recommendation engine outputs only valid active-catalog movies
  Test G: Not Interested exclusions are strictly respected in expanded catalog
"""

import pandas as pd
import pytest

from src.services.catalog import CATALOG_SIZE, get_catalog, get_by_id
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.utils.metadata_validator import (
    TMDB_CDN_BASE,
    audit_catalog_integrity,
    calculate_title_similarity,
    is_valid_tmdb_path,
    normalize_title,
    resolve_movie_images,
    validate_tmdb_mapping,
)


# -------------------------------------------------------------------------
# Test A — Movie Identity Consistency
# -------------------------------------------------------------------------
def test_movie_identity_consistency():
    catalog = get_catalog()
    ids = [m["id"] for m in catalog]
    assert len(ids) == len(set(ids)), "All catalog movie IDs must be strictly unique"
    assert len(catalog) == CATALOG_SIZE


# -------------------------------------------------------------------------
# Test B — TMDB Mapping Sanity
# -------------------------------------------------------------------------
def test_tmdb_mapping_sanity():
    # Valid matching record
    valid_res = validate_tmdb_mapping(
        movie_id=1,
        ml_title="Toy Story (1995)",
        ml_year=1995,
        tmdb_meta={
            "tmdb_id": 862,
            "title": "Toy Story",
            "release_date": "1995-10-30",
            "poster": "/uXDfjJbdP4ijW5hWSBrFu1DIKBL.jpg",
            "backdrop": "/3Rfvhy1Nl6sSGJwyHbRyZ3Jwz1T.jpg",
        },
        expected_tmdb_id=862,
    )
    assert valid_res["is_valid"] is True
    assert valid_res["status"] == "VALID_TMDB"
    assert valid_res["poster_path"] == "/uXDfjJbdP4ijW5hWSBrFu1DIKBL.jpg"

    # Suspicious mismatched title
    mismatch_title_res = validate_tmdb_mapping(
        movie_id=1,
        ml_title="Toy Story (1995)",
        ml_year=1995,
        tmdb_meta={
            "tmdb_id": 862,
            "title": "The Godfather Part II",
            "release_date": "1995-10-30",
            "poster": "/poster.jpg",
        },
        expected_tmdb_id=862,
    )
    assert mismatch_title_res["is_valid"] is False
    assert mismatch_title_res["status"] == "MISMATCH_TITLE"

    # Suspicious divergent release year
    mismatch_year_res = validate_tmdb_mapping(
        movie_id=1,
        ml_title="Total Recall (1990)",
        ml_year=1990,
        tmdb_meta={
            "tmdb_id": 1234,
            "title": "Total Recall",
            "release_date": "2012-08-03",
            "poster": "/remake.jpg",
        },
        expected_tmdb_id=1234,
    )
    # Different year versions must be flagged if IDs don't match or year diverges widely
    # (Here year differs by 22 years)
    assert mismatch_year_res["is_valid"] is False
    assert mismatch_year_res["status"] == "MISMATCH_YEAR"

    # Malicious or malformed poster path
    bad_path_res = validate_tmdb_mapping(
        movie_id=2,
        ml_title="Jumanji (1995)",
        ml_year=1995,
        tmdb_meta={
            "tmdb_id": 8844,
            "title": "Jumanji",
            "release_date": "1995-12-15",
            "poster": "javascript:alert(1)",
        },
        expected_tmdb_id=8844,
    )
    assert bad_path_res["poster_path"] is None, "Malformed poster path must be rejected"


# -------------------------------------------------------------------------
# Test C — 4-Tier Image Fallback Hierarchy
# -------------------------------------------------------------------------
def test_image_fallback_hierarchy():
    # Case 1: Valid TMDB poster -> Tier 1
    p1, b1, a1 = resolve_movie_images(
        movie_title="Fight Club (1999)",
        release_year=1999,
        genre="Drama",
        tmdb_meta={"poster": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", "backdrop": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg"},
    )
    assert a1["tier_poster"] == 1
    assert "image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg" in p1

    # Case 2: No TMDB poster, valid TMDB backdrop -> Tier 2
    p2, b2, a2 = resolve_movie_images(
        movie_title="Fight Club (1999)",
        release_year=1999,
        genre="Drama",
        tmdb_meta={"poster": None, "backdrop": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg"},
    )
    assert a2["tier_poster"] == 2
    assert "image.tmdb.org/t/p/w780/hZkgoQYus5vegHoetLkCJzb17zJ.jpg" in p2

    # Case 3: No TMDB metadata -> Tier 3 (Local SVG Vector Fallback)
    p3, b3, a3 = resolve_movie_images(
        movie_title="The Dark Knight (2008)",
        release_year=2008,
        genre="Action",
        tmdb_meta=None,
    )
    assert a3["tier_poster"] == 3
    assert p3.startswith("data:image/svg+xml;utf8,")
    assert "Dark%20Knight" in p3
    assert b3.startswith("data:image/svg+xml;utf8,")

    # Case 4: Corrupted inputs / SVG generator failure recovery -> Tier 4
    # Even with odd title characters, resolve_movie_images must not crash
    p4, b4, a4 = resolve_movie_images(
        movie_title="Movie With Null \x00 Byte",
        release_year=None,
        genre=None,
        tmdb_meta={"corrupted": "payload"},
    )
    assert p4 is not None and len(p4) > 0
    assert b4 is not None and len(b4) > 0


# -------------------------------------------------------------------------
# Test D — Expanded Active Catalog Properties
# -------------------------------------------------------------------------
def test_expanded_catalog_properties():
    catalog = get_catalog()
    # Catalog size within requested 1,500 - 2,500 target
    assert 1500 <= len(catalog) <= 2500
    assert len(catalog) == 2000

    links_df = pd.read_csv("data/links.csv")
    audit = audit_catalog_integrity(catalog, links_df=links_df)
    assert audit["is_healthy"] is True
    assert audit["missing_years"] == 0
    assert audit["missing_genres"] == 0
    assert audit["unique_movie_ids"] == len(catalog)

    # Every item has valid metadata attributes
    for m in catalog[:100]:
        assert m["id"] > 0
        assert m["title"].strip() != ""
        assert m["release_year"] >= 1900
        assert len(m["genres"]) > 0
        assert m["rating"] >= 0.0
        assert m["poster_url"].startswith("http") or m["poster_url"].startswith("data:image/svg+xml")
        assert m["backdrop_url"].startswith("http") or m["backdrop_url"].startswith("data:image/svg+xml")


# -------------------------------------------------------------------------
# Test E — Search & Multi-Facet Filtering on Expanded Catalog
# -------------------------------------------------------------------------
def test_search_and_filters_expanded_catalog():
    # Title search
    res_matrix = MovieService.filter_movies(query="matrix")
    assert len(res_matrix) >= 1
    assert any("matrix" in m["title"].lower() for m in res_matrix)

    # Multi-genre filter
    res_animation = MovieService.filter_movies(selected_genres=["Animation"])
    assert len(res_animation) > 50

    # Decade range filter
    res_classic = MovieService.filter_movies(year_range=(1930, 1960))
    assert len(res_classic) > 20
    assert all(1930 <= m["release_year"] <= 1960 for m in res_classic)

    # Combined filters
    res_combo = MovieService.filter_movies(
        query="star",
        selected_genres=["Sci-Fi"],
        year_range=(1970, 2025),
        min_rating=7.0,
    )
    assert len(res_combo) >= 1


# -------------------------------------------------------------------------
# Test F — Recommendation Engine Catalog Integrity
# -------------------------------------------------------------------------
def test_recommendation_catalog_integrity():
    cat_by_id = get_by_id()
    ratings_input = {1: 9.5, 260: 9.0, 318: 10.0}

    recs = RecommendationService.get_recommended_for_user({"ratings": ratings_input}, limit=12)
    assert len(recs) == 12

    # Every recommended movie must exist in the authoritative catalog
    for r in recs:
        assert r["id"] in cat_by_id
        assert r["id"] not in ratings_input, "Rated movies should not be re-recommended"
        assert r["title"] == cat_by_id[r["id"]]["title"]


# -------------------------------------------------------------------------
# Test G — Negative Feedback Exclusions in Expanded Catalog
# -------------------------------------------------------------------------
def test_exclusion_filtering_expanded_catalog():
    ratings_input = {1: 9.5, 260: 9.0, 318: 10.0}
    # Initial recs
    initial_recs = RecommendationService.get_recommended_for_user({"ratings": ratings_input}, limit=6)
    target_exclude_id = initial_recs[0]["id"]

    # Exclude top recommendation
    recs_with_exclusion = RecommendationService.get_recommended_for_user(
        {"ratings": ratings_input, "hidden_ids": [target_exclude_id]},
        limit=6,
    )
    rec_ids = [m["id"] for m in recs_with_exclusion]
    assert target_exclude_id not in rec_ids, f"Excluded movie {target_exclude_id} must not appear in recommendations"
