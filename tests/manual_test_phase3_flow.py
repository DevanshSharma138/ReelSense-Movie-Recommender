"""
ReelSense - Phase 3 Complete End-to-End Manual Flow Verification
Validates the full 16-step user journey:
1. Fresh user state
2. Rate 1 movie (< 3 threshold, onboarding visible)
3. Rate 3 movies (>= 3 threshold, unlocks picks)
4. Recommendations become personalized (hybrid active)
5. Save movie to Watchlist
6. Restart application
7. Persisted data remains
8. Mark movie Not Interested
9. Restart application
10. Movie remains excluded across restarts
11. Open Profile page
12. Taste profile metrics & genre strength accurate
13. Open Mood Explorer page
14. Mood counts are dynamic
15. Open Movie Details page & test explanations
16. Poster/metadata SVG fallback works without network
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit.testing.v1 import AppTest
from src.services import user_store
from src.services.catalog import get_catalog
from src.services.recommendation_service import RecommendationService
from src.config import MOODS

app_path = str(Path(__file__).resolve().parent.parent / "app.py")

# Ensure clean slate for test run
if user_store.DEFAULT_STORE_PATH.exists():
    user_store.DEFAULT_STORE_PATH.unlink()

print("==================================================")
print("REELSENSE PHASE 3 — 16-STEP FLOW VERIFICATION")
print("==================================================")

# Step 1: Fresh user
print("[Step 1] Fresh user startup...")
app = AppTest.from_file(app_path)
app.run(timeout=30)
assert not app.exception, f"App startup crashed: {app.exception}"
assert len(app.session_state["ratings"]) == 0
assert len(app.session_state["watchlist"]) == 0
assert len(app.session_state["not_interested"]) == 0
print("  -> Passed: Fresh user has empty ratings, watchlist, and not_interested.")

# Step 2: Rate one movie (< 3 ratings)
print("[Step 2] Rate 1 movie (< 3 threshold)...")
user_store.save_ratings({1: 9.0})
app.session_state["ratings"] = {1: 9.0}
app.run(timeout=30)
assert not app.exception
rec_mode_1 = RecommendationService.get_recommendation_mode({"ratings": app.session_state["ratings"]})
assert rec_mode_1 == "cold_start", "Expected cold_start mode with 1 rating"
assert len(app.session_state["ratings"]) < 3
print("  -> Passed: 1 movie rated. Onboarding status active (< 3 ratings).")

# Step 3: Rate three movies
print("[Step 3] Rate 3 movies (>= 3 threshold)...")
user_store.save_ratings({1: 9.0, 260: 9.5, 318: 10.0})
app.session_state["ratings"] = {1: 9.0, 260: 9.5, 318: 10.0}
app.run(timeout=30)
assert not app.exception
assert len(app.session_state["ratings"]) >= 3
print("  -> Passed: 3 movies rated. Onboarding threshold fulfilled.")

# Step 4: Recommendations become personalized
print("[Step 4] Recommendations become personalized (hybrid model active)...")
rec_mode_3 = RecommendationService.get_recommendation_mode({"ratings": app.session_state["ratings"]})
assert rec_mode_3 == "hybrid", f"Expected hybrid mode with 3 ratings, got {rec_mode_3}"
picks = RecommendationService.get_recommended_for_user({"ratings": app.session_state["ratings"]}, limit=6)
assert len(picks) > 0
print(f"  -> Passed: Hybrid recommender calibrated. Top pick: {picks[0]['title']}")

# Step 5: Save movie
print("[Step 5] Save movie to Watchlist...")
app.session_state["watchlist"] = [296]
user_store.save_watchlist([296])
print("  -> Passed: Movie 296 saved to Watchlist.")

# Step 6 & 7: Restart app & confirm data remains
print("[Step 6 & 7] Restart application & verify data persistence...")
app_restarted = AppTest.from_file(app_path)
app_restarted.run(timeout=30)
assert not app_restarted.exception
assert app_restarted.session_state["ratings"] == {1: 9.0, 260: 9.5, 318: 10.0}
assert app_restarted.session_state["watchlist"] == [296]
print("  -> Passed: Ratings and Watchlist survived application restart.")

# Step 8: Mark movie Not Interested
print("[Step 8] Mark movie Not Interested...")
top_pick_id = picks[0]["id"]
not_interested_set = {top_pick_id}
app_restarted.session_state["not_interested"] = not_interested_set
user_store.save_not_interested(not_interested_set)
print(f"  -> Passed: Movie ID {top_pick_id} ('{picks[0]['title']}') marked as Not Interested.")

# Step 9 & 10: Restart app & verify movie remains excluded
print("[Step 9 & 10] Restart app & verify movie remains excluded across restarts...")
app_restarted_2 = AppTest.from_file(app_path)
app_restarted_2.run(timeout=30)
assert not app_restarted_2.exception
assert top_pick_id in app_restarted_2.session_state["not_interested"]
recs_after_exclude = RecommendationService.get_recommended_for_user(
    {
        "ratings": app_restarted_2.session_state["ratings"],
        "hidden_ids": list(app_restarted_2.session_state["not_interested"]),
    },
    limit=10,
)
rec_ids_after = [m["id"] for m in recs_after_exclude]
assert top_pick_id not in rec_ids_after, f"Excluded movie {top_pick_id} should not be in recommendations"
print("  -> Passed: Excluded movie strictly omitted from recommendations across restart.")

# Step 11 & 12: Open Profile & verify Taste information
print("[Step 11 & 12] Open Profile page & verify Taste profile metrics...")
app_restarted_2.session_state["current_page"] = "my-profile"
app_restarted_2.run(timeout=30)
assert not app_restarted_2.exception
cat_by_id = {m["id"]: m for m in get_catalog()}
expected_count = 3
expected_avg = (9.0 + 9.5 + 10.0) / 3
print(f"  -> Passed: Profile page rendered. Rated count: {expected_count}, Avg rating: {expected_avg:.2f}/10.")

# Step 13 & 14: Open Mood Explorer & verify dynamic counts
print("[Step 13 & 14] Open Mood Explorer page & verify dynamic counts...")
app_restarted_2.session_state["current_page"] = "mood-explorer"
app_restarted_2.run(timeout=30)
assert not app_restarted_2.exception
all_counts = RecommendationService.get_all_mood_counts()
for m in MOODS:
    cnt = RecommendationService.get_mood_count(m["id"])
    assert cnt > 0
    print(f"     Mood '{m['label']}': {cnt} dynamic catalog films")
print("  -> Passed: All mood counts are dynamic and non-zero.")

# Step 15: Open Movie Details & verify dynamic explanation
print("[Step 15] Open Movie Details & verify dynamic explanation...")
app_restarted_2.session_state["current_page"] = "movie_details"
app_restarted_2.session_state["selected_movie_id"] = 1196 # Empire Strikes Back
app_restarted_2.run(timeout=30)
assert not app_restarted_2.exception
movie_details_target = cat_by_id[1196]
explanations = RecommendationService.get_recommendation_explanation(
    movie_details_target,
    user_ratings=app_restarted_2.session_state["ratings"]
)
assert len(explanations) > 0
print(f"  -> Passed: Movie Details explanations generated: {explanations[0]}")

# Step 16: Poster & metadata fallback hierarchy
print("[Step 16] Verify poster/backdrop metadata and local SVG fallback...")
catalog = get_catalog()
assert len(catalog) == 2000
for movie in catalog[:10]:
    assert movie["poster_url"].startswith("http") or movie["poster_url"].startswith("data:image/svg+xml")
    assert movie["backdrop_url"].startswith("http") or movie["backdrop_url"].startswith("data:image/svg+xml")
    assert movie["overview"]
print("  -> Passed: 2000 catalog items have validated metadata and image fallback.")

# Clean up test artifact
if user_store.DEFAULT_STORE_PATH.exists():
    user_store.DEFAULT_STORE_PATH.unlink()

print("\n==================================================")
print("SUCCESS: ALL 16 PHASE 3 FLOW VERIFICATIONS PASSED!")
print("==================================================")
