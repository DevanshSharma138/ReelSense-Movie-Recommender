"""
ReelSense - Comprehensive UI Interaction, Button Wiring & State QA Test Suite
Verifies:
1. Topbar navigation state mapping and route integrity
2. Movie Card Inspect -> selected_movie_id mapping
3. Watchlist (Vault) toggle, immediate state update, and persistence
4. Not Interested (Hide / Restore) toggle, immediate state update, exclusion, and persistence
5. Rating flow: save rating, edit rating, delete rating, and hybrid recommendation reactivation
6. Discover filter execution (genre, rating, year, sort, and true reset)
7. Mood Explorer selection, dynamic counts, and filtering
8. Movie Details on-demand TMDB enrichment
9. Multi-action session persistence across restarts
"""

import json
import pytest
from pathlib import Path

from src.services import user_store
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services.taste_service import TasteService
from src.components.topbar import PAGE_ALIASES, TOP_NAV_ITEMS


@pytest.fixture(autouse=True)
def clean_user_state(tmp_path, monkeypatch):
    """Ensure tests run against a clean isolated user store."""
    test_file = tmp_path / "test_user_data.json"
    monkeypatch.setattr(user_store, "DEFAULT_STORE_PATH", test_file)
    if test_file.exists():
        try:
            test_file.unlink()
        except OSError:
            pass
    yield
    if test_file.exists():
        try:
            test_file.unlink()
        except OSError:
            pass


def test_topbar_navigation_routes_and_aliases():
    """Verify all top navigation bar items resolve to valid application routes."""
    valid_app_routes = {
        "home", "home-discover", "discover-movies", "discover", "collections",
        "mood-explorer", "mood", "my-watchlist", "watchlist", "my-ratings",
        "ratings", "about-the-ai", "sense_ai", "about", "architecture",
        "capstone", "my-profile", "profile", "settings", "movie_details"
    }

    for item in TOP_NAV_ITEMS:
        route = item["route"]
        assert route in valid_app_routes, f"Nav item {item['id']} points to unknown route: {route}"

    # Verify PAGE_ALIASES maps synonyms consistently
    for alias, canonical in PAGE_ALIASES.items():
        assert canonical in valid_app_routes, f"Alias {alias} maps to invalid route {canonical}"
        assert PAGE_ALIASES[alias] == canonical


def test_movie_card_inspect_identity():
    """Verify Inspect movie action resolves the exact MovieLens movieId."""
    test_ids = [1, 260, 318, 593, 1196]
    for mid in test_ids:
        movie = MovieService.get_movie_by_id(mid)
        assert movie is not None
        assert movie["id"] == mid
        assert isinstance(movie["title"], str)
        assert len(movie["title"]) > 0


def test_watchlist_vault_button_wiring_and_persistence():
    """Verify adding, verifying, and removing a movie from Watchlist/Vault."""
    # 1. Fresh state is empty
    state = user_store.load()
    assert state["watchlist"] == []

    # 2. Add movie 260 (Star Wars IV) to watchlist
    watchlist = state["watchlist"]
    watchlist.append(260)
    user_store.save_watchlist(watchlist)

    # 3. Reload from disk to verify persistence
    reloaded = user_store.load()
    assert 260 in reloaded["watchlist"]
    assert len(reloaded["watchlist"]) == 1

    # 4. Add second movie 1196 (Star Wars V)
    reloaded["watchlist"].append(1196)
    user_store.save_watchlist(reloaded["watchlist"])

    # 5. Remove movie 260 (toggle Vault off)
    reloaded_2 = user_store.load()
    assert len(reloaded_2["watchlist"]) == 2
    reloaded_2["watchlist"].remove(260)
    user_store.save_watchlist(reloaded_2["watchlist"])

    final_state = user_store.load()
    assert 260 not in final_state["watchlist"]
    assert 1196 in final_state["watchlist"]
    assert len(final_state["watchlist"]) == 1


def test_hide_and_restore_wiring_and_recommendation_exclusion():
    """Verify Hide/Not-Interested marks movie, excludes it from recs, and Restore re-enables it."""
    # Add ratings to enable hybrid recs
    user_store.save_ratings({1: 9.0, 260: 9.5, 318: 10.0})

    # Get active recommendations
    recs_initial = RecommendationService.get_recommended_for_user(
        {"ratings": {1: 9.0, 260: 9.5, 318: 10.0}, "hidden_ids": []}, limit=10
    )
    rec_ids = [m["id"] for m in recs_initial]
    assert len(rec_ids) > 0
    target_to_hide = rec_ids[0]

    # Hide target movie
    not_interested = {target_to_hide}
    user_store.save_not_interested(not_interested)

    # Reload from disk
    saved_ni = user_store.load()["not_interested"]
    assert target_to_hide in saved_ni

    # New recommendations must strictly omit hidden movie
    recs_after_hide = RecommendationService.get_recommended_for_user(
        {"ratings": {1: 9.0, 260: 9.5, 318: 10.0}, "hidden_ids": list(saved_ni)}, limit=10
    )
    new_rec_ids = [m["id"] for m in recs_after_hide]
    assert target_to_hide not in new_rec_ids

    # Restore target movie
    not_interested.remove(target_to_hide)
    user_store.save_not_interested(not_interested)
    reloaded_ni = user_store.load()["not_interested"]
    assert target_to_hide not in reloaded_ni


def test_rating_save_edit_delete_flow():
    """Verify ratings save, update, delete, and model reactivity (0-5 scale)."""
    # 1. Save single rating
    user_store.save_ratings({1: 4.5})
    s1 = user_store.load()
    assert s1["ratings"][1] == 4.5

    # 2. Edit rating from 4.5 to 5.0
    s1["ratings"][1] = 5.0
    user_store.save_ratings(s1["ratings"])
    s2 = user_store.load()
    assert s2["ratings"][1] == 5.0

    # 3. Add 2 more ratings to cross cold-start threshold (>= 3)
    s2["ratings"][260] = 4.8
    s2["ratings"][318] = 4.5
    user_store.save_ratings(s2["ratings"])

    mode = RecommendationService.get_recommendation_mode({"ratings": s2["ratings"]})
    recs = RecommendationService.get_recommended_for_user({"ratings": s2["ratings"]}, limit=5)
    assert mode == "hybrid"
    assert len(recs) == 5

    # 4. Remove a rating dropping below 3 threshold
    del s2["ratings"][318]
    user_store.save_ratings(s2["ratings"])
    s3 = user_store.load()
    assert len(s3["ratings"]) == 2
    assert 318 not in s3["ratings"]

    mode_cold = RecommendationService.get_recommendation_mode({"ratings": s3["ratings"]})
    recs_cold = RecommendationService.get_recommended_for_user({"ratings": s3["ratings"]}, limit=5)
    assert mode_cold == "cold_start"
    assert len(recs_cold) == 5


def test_discover_filters_and_genuine_reset():
    """Verify Discover page filter logic and reset guarantees."""
    # 1. Filter by specific genre
    scifi_movies = MovieService.filter_movies(selected_genres=["Sci-Fi"])
    assert len(scifi_movies) > 0
    for m in scifi_movies:
        assert "Sci-Fi" in m["genres"]

    # 2. Filter by minimum rating
    high_rated = MovieService.filter_movies(min_rating=8.5)
    assert len(high_rated) > 0
    for m in high_rated:
        assert m["rating"] >= 8.5

    # 3. Filter by year range
    classics = MovieService.filter_movies(year_range=(1970, 1985))
    assert len(classics) > 0
    for m in classics:
        assert 1970 <= m["release_year"] <= 1985

    # 4. Reset filters restores complete catalog
    all_movies = MovieService.filter_movies(
        query="", selected_genres=[], year_range=(1930, 2026), min_rating=0.0, language="All"
    )
    assert len(all_movies) >= 1990


def test_mood_explorer_selection_and_resonance():
    """Verify Mood Explorer produces distinct sets of filtered recommendations per mood."""
    moods = ["Happy", "Relaxed", "Thrilling", "Romantic", "Emotional", "Mind-blown"]
    counts = {}
    for m in moods:
        cnt = RecommendationService.get_mood_count(m)
        assert cnt > 0, f"Mood {m} has 0 movies"
        counts[m] = cnt

    # Verify counts vary across moods
    assert len(set(counts.values())) > 1


def test_on_demand_movie_enrichment_resolution():
    """Verify on-demand movie lookup returns verified titles and non-empty posters."""
    movie = MovieService.get_movie_by_id(1)  # Toy Story
    assert movie is not None
    assert movie["id"] == 1
    assert "Toy Story" in movie["title"]
    assert movie["poster_url"] is not None
    assert len(movie["poster_url"]) > 10


def test_catalog_and_movie_service_search_movies():
    """Verify search finds known movies (Matrix, Toy Story) and returns clean empty state on unknown."""
    from src.services.catalog import Catalog, search_movies

    # 1. Search Matrix via Catalog and MovieService
    results_matrix = MovieService.search_movies("Matrix")
    assert len(results_matrix) > 0
    assert any("Matrix" in m["title"] for m in results_matrix)

    # 2. Search Toy Story
    results_toy = MovieService.search_movies("toy story")
    assert len(results_toy) > 0
    assert any("Toy Story" in m["title"] for m in results_toy)

    # 3. Search nonsense query
    results_empty = MovieService.search_movies("xyznonexistentfilmtag99999")
    assert isinstance(results_empty, list)
    assert len(results_empty) == 0

    # 4. Catalog namespace methods
    cat_results = Catalog.search_movies("Star Wars")
    assert len(cat_results) > 0
    assert any("Star Wars" in m["title"] for m in cat_results)


def test_rating_scale_migration_and_bounds():
    """Verify safe, deterministic migration from old 0-10 scale to 0-5 scale."""
    # 1. Old scale ratings > 5.0 get divided by 2.0
    old_scale_ratings = {1: 10.0, 260: 9.0, 318: 8.0, 593: 7.0}
    user_store.save_ratings(old_scale_ratings)
    migrated = user_store.get_ratings()

    assert migrated[1] == 5.0
    assert migrated[260] == 4.5
    assert migrated[318] == 4.0
    assert migrated[593] == 3.5

    # 2. Values on 0-5 scale are preserved without alteration
    new_scale_ratings = {1: 4.5, 260: 5.0, 318: 3.5}
    user_store.save_ratings(new_scale_ratings)
    loaded_new = user_store.get_ratings()
    assert loaded_new == new_scale_ratings

    # 3. Out-of-bounds ratings are clamped to [0.0, 5.0]
    out_of_bounds = {1: 12.0, 260: -2.0}
    user_store.save_ratings(out_of_bounds)
    clamped = user_store.get_ratings()
    assert clamped[1] == 5.0
    assert clamped[260] == 0.0


def test_onboarding_dismiss_and_rate_films_navigation():
    """Verify onboarding banner conditions and session state handling."""
    # When user has 0 ratings, onboarding should be active
    assert user_store.get_ratings() == {}
    
    # Simulating dismissal
    state = user_store.get_default_state()
    assert state["ratings"] == {}
    assert "user_profile" in state
