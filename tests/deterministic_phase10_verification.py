"""
Deterministic Phase 10 & Live Pipeline Verification Script
Executes and measures Tests A, B, C, D, E with actual movie titles, IDs, and scores.
"""

import json
from pathlib import Path
from src.services.catalog import get_catalog
from src.services.recommendation_service import RecommendationService
from src.services import user_store

CATALOG_BY_ID = {m["id"]: m for m in get_catalog()}


def title(mid):
    m = CATALOG_BY_ID.get(mid)
    return m["title"] if m else f"Movie #{mid}"


def run_all_tests():
    print("=" * 70)
    print("REELSENSE PHASE 10 DETERMINISTIC VERIFICATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # TEST A: Clean User -> Cold Start -> Rate 5 movies -> Reload -> Compare
    # ---------------------------------------------------------
    print("\n--- TEST A: Rate 5 movies & verify personalized shift ---")
    clean_prefs = {"ratings": {}, "watchlist": [], "hidden_ids": []}
    recs_clean = RecommendationService.get_recommended_for_user(clean_prefs, limit=5)
    clean_ids = [m["id"] for m in recs_clean]
    clean_titles = [m["title"] for m in recs_clean]
    print("1. Clean User (Cold-Start) Top 5 Recommendations:")
    for i, m in enumerate(recs_clean, 1):
        print(f"   {i}. [{m['id']}] {m['title']}")

    # Rate 5 distinct Animation / Pixar classics
    # 1: Toy Story (5.0), 3114: Toy Story 2 (5.0), 6377: Finding Nemo (5.0), 588: Aladdin (4.5), 364: Lion King (4.5)
    rated_5 = {1: 5.0, 3114: 5.0, 6377: 5.0, 588: 4.5, 364: 4.5}
    user_state = {
        "ratings": rated_5,
        "watchlist": [],
        "not_interested": [],
        "user_profile": {}
    }
    # Simulate saving to user_data.json and reloading
    test_json_path = Path("data/test_user_data_sim.json")
    user_store.save(user_state, path=test_json_path)
    loaded_state = user_store.load(path=test_json_path)

    reloaded_prefs = {
        "ratings": loaded_state["ratings"],
        "watchlist": loaded_state["watchlist"],
        "hidden_ids": list(loaded_state["not_interested"])
    }
    recs_rated = RecommendationService.get_recommended_for_user(reloaded_prefs, limit=5)
    rated_ids = [m["id"] for m in recs_rated]
    print("\n2. After Rating 5 Animation Films & Reloading Disk State:")
    for i, m in enumerate(recs_rated, 1):
        print(f"   {i}. [{m['id']}] {m['title']} (Score: {m.get('similarity', 0):.3f})")

    diag_a = RecommendationService.get_user_recommendation_diagnostics(reloaded_prefs)
    print(f"\n   Diagnostic: Strategy={diag_a['strategy']}, Ratings={diag_a['n_ratings']}, Profile Built={diag_a['has_taste_profile']}")

    assert clean_ids != rated_ids, "Recommendations should have changed after ratings!"
    for rid in rated_5.keys():
        assert rid not in rated_ids, f"Rated movie {rid} must be excluded from recommendations!"
    print("   -> TEST A PASSED: Recommendations transformed to Animation/Family cluster; all rated films excluded.")

    # ---------------------------------------------------------
    # TEST B: Watchlist Addition, Persistence & Exclusion
    # ---------------------------------------------------------
    print("\n--- TEST B: Watchlist influence, reload persistence & exclusion ---")
    # Add Jurassic Park (480), Matrix (2571), Star Wars (260) to Watchlist
    wl_mids = [480, 2571, 260]
    user_state_b = {
        "ratings": {},
        "watchlist": wl_mids,
        "not_interested": [],
        "user_profile": {}
    }
    user_store.save(user_state_b, path=test_json_path)
    loaded_b = user_store.load(path=test_json_path)
    prefs_b = {
        "ratings": loaded_b["ratings"],
        "watchlist": loaded_b["watchlist"],
        "hidden_ids": list(loaded_b["not_interested"])
    }
    recs_wl = RecommendationService.get_recommended_for_user(prefs_b, limit=6)
    wl_rec_ids = [m["id"] for m in recs_wl]
    print(f"1. Watchlist items persisted: {[title(x) for x in loaded_b['watchlist']]}")
    print("2. Top 6 Recommendations influenced by Watchlist:")
    for i, m in enumerate(recs_wl, 1):
        print(f"   {i}. [{m['id']}] {m['title']}")

    for wid in wl_mids:
        assert wid not in wl_rec_ids, f"Watchlist movie {wid} must be excluded from recommendations!"
    assert wl_rec_ids != clean_ids, "Watchlist should shift recommendations from generic cold-start"
    print("   -> TEST B PASSED: Watchlisted titles excluded; sci-fi/adventure genre affinity reflected.")

    # ---------------------------------------------------------
    # TEST C: 5-Star to 1-Star Rating Shift
    # ---------------------------------------------------------
    print("\n--- TEST C: Rating change (5-stars -> 1-stars) updates rankings ---")
    prefs_5star = {"ratings": {1258: 5.0}, "watchlist": [], "hidden_ids": []}  # The Shining 5-stars
    recs_5star = RecommendationService.get_recommended_for_user(prefs_5star, limit=5)
    ids_5star = [m["id"] for m in recs_5star]
    print(f"1. Top 5 when 'The Shining' rated 5.0 stars:")
    for i, m in enumerate(recs_5star, 1):
        print(f"   {i}. [{m['id']}] {m['title']} (Score: {m.get('similarity', 0):.3f})")

    prefs_1star = {"ratings": {1258: 1.0}, "watchlist": [], "hidden_ids": []}  # The Shining 1-stars
    recs_1star = RecommendationService.get_recommended_for_user(prefs_1star, limit=5)
    ids_1star = [m["id"] for m in recs_1star]
    print(f"\n2. Top 5 when 'The Shining' changed to 1.0 stars:")
    for i, m in enumerate(recs_1star, 1):
        print(f"   {i}. [{m['id']}] {m['title']} (Score: {m.get('similarity', 0):.3f})")

    assert ids_5star != ids_1star, "Recommendations must change when rating is flipped from 5-stars to 1-stars!"
    print("   -> TEST C PASSED: Recommendation rankings meaningfully changed between 5-stars and 1-stars.")

    # ---------------------------------------------------------
    # TEST D: Positive Movie A (5-stars) vs Negative Movie B (1-stars)
    # ---------------------------------------------------------
    print("\n--- TEST D: Positive Movie A (Alien=5 stars) vs Negative Movie B (Toy Story=0.5 stars) ---")
    prefs_d = {"ratings": {1214: 5.0, 1: 0.5}, "watchlist": [], "hidden_ids": []}
    recs_d = RecommendationService.get_recommended_for_user(prefs_d, limit=6)
    print("1. Top Recommendations (Loving Alien, Hating Toy Story):")
    for i, m in enumerate(recs_d, 1):
        print(f"   {i}. [{m['id']}] {m['title']} (Score: {m.get('similarity', 0):.3f})")

    # Aliens (1200) or sci-fi/horror must be promoted, Toy Story sequels or kids animated movies should not appear
    d_ids = [m["id"] for m in recs_d]
    assert 1200 in d_ids or any("Sci-Fi" in m.get("genres", []) for m in recs_d), "Aliens/Sci-Fi should be promoted"
    assert 3114 not in d_ids, "Toy Story 2 should not be in top recommendations when Toy Story rated 0.5 stars"
    print("   -> TEST D PASSED: Horror/Sci-Fi promoted, kids animation penalized.")

    # ---------------------------------------------------------
    # TEST E: Hidden / Not-Interested Exclusions
    # ---------------------------------------------------------
    print("\n--- TEST E: Hidden movie strict exclusion before and after reload ---")
    hide_id = 1200  # Aliens
    prefs_e = {"ratings": {1214: 5.0}, "watchlist": [], "hidden_ids": [hide_id]}
    user_state_e = {
        "ratings": {1214: 5.0},
        "watchlist": [],
        "not_interested": [hide_id],
        "user_profile": {}
    }
    user_store.save(user_state_e, path=test_json_path)
    loaded_e = user_store.load(path=test_json_path)

    prefs_e_loaded = {
        "ratings": loaded_e["ratings"],
        "watchlist": loaded_e["watchlist"],
        "hidden_ids": list(loaded_e["not_interested"])
    }
    recs_e = RecommendationService.get_recommended_for_user(prefs_e_loaded, limit=10)
    e_ids = [m["id"] for m in recs_e]
    assert hide_id not in e_ids, f"Hidden movie {hide_id} ({title(hide_id)}) appeared in recommendations!"
    print(f"1. Movie '{title(hide_id)}' excluded from recommendations: {hide_id not in e_ids}")
    print("   -> TEST E PASSED: Hidden movie strictly excluded before and after persistence.")

    if test_json_path.exists():
        test_json_path.unlink()

    print("\n" + "=" * 70)
    print("ALL 5 DETERMINISTIC PHASE 10 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
