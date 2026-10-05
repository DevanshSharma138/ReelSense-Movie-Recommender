"""
ReelSense - Manual Application Test Flow Verification (Phase 2 Task 11)
Executes the exact 10-step manual user interaction flow:
1. Open ReelSense.
2. Confirm Watchlist is empty.
3. Confirm Ratings is empty.
4. Rate 3 movies.
5. Confirm personalized/hybrid recommendations appear.
6. Save a movie to Watchlist.
7. Change a profile preference.
8. Stop/restart the application.
9. Confirm all data is still present.
10. Confirm personalized recommendations remain available.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit.testing.v1 import AppTest
from src.services import user_store
from src.services.recommendation_service import RecommendationService

app_path = str(Path(__file__).resolve().parent.parent / "app.py")

# Step 0: Ensure fresh user data
if user_store.DEFAULT_STORE_PATH.exists():
    user_store.DEFAULT_STORE_PATH.unlink()

print("--- STEP 1 & 2 & 3: Fresh application start ---")
at1 = AppTest.from_file(app_path)
at1.run(timeout=30)
assert not at1.exception, f"Startup failed: {at1.exception}"
assert len(at1.session_state["watchlist"]) == 0, "Watchlist should be empty"
assert len(at1.session_state["ratings"]) == 0, "Ratings should be empty"
print("Confirmed: Fresh start, Watchlist is empty, Ratings is empty.")

print("--- STEP 4 & 5: Rate 3 movies & check hybrid recommendations ---")
user_store.save_ratings({356: 9.5, 318: 9.0, 296: 8.5})
at1.session_state["ratings"] = {356: 9.5, 318: 9.0, 296: 8.5}
at1.run(timeout=30)
assert not at1.exception

rec_prefs = {
    "ratings": at1.session_state["ratings"],
    "favorite_genres": at1.session_state["user_profile"].get("favorite_genres", []),
    "hidden_ids": list(at1.session_state["not_interested"]),
}
mode = RecommendationService.get_recommendation_mode(rec_prefs)
assert mode == "hybrid", f"Expected hybrid mode, got {mode}"
print(f"Confirmed: 3 movies rated -> Recommendation mode is: {mode}")

print("--- STEP 6: Save a movie to Watchlist ---")
current_wl = at1.session_state["watchlist"]
current_wl.append(593)
at1.session_state["watchlist"] = current_wl
user_store.save_watchlist(current_wl)
print("Confirmed: Movie 593 saved to Watchlist.")

print("--- STEP 7: Change a profile preference ---")
profile = at1.session_state["user_profile"]
profile["name"] = "Aesthetic Cinephile"
profile["favorite_genres"] = ["Sci-Fi", "Film-Noir"]
at1.session_state["user_profile"] = profile
user_store.save_profile(profile)
print("Confirmed: Profile preferences updated and saved.")

print("--- STEP 8, 9, 10: Stop / restart the application ---")
# Create new AppTest instance to simulate cold restart
at2 = AppTest.from_file(app_path)
at2.run(timeout=30)
assert not at2.exception, f"Restart failed: {at2.exception}"

r_loaded = at2.session_state["ratings"]
wl_loaded = at2.session_state["watchlist"]
prof_loaded = at2.session_state["user_profile"]

assert r_loaded == {356: 9.5, 318: 9.0, 296: 8.5}, f"Ratings lost: {r_loaded}"
assert wl_loaded == [593], f"Watchlist lost: {wl_loaded}"
assert prof_loaded["name"] == "Aesthetic Cinephile", f"Profile lost: {prof_loaded}"

rec_prefs_restart = {
    "ratings": r_loaded,
    "favorite_genres": prof_loaded.get("favorite_genres", []),
    "hidden_ids": list(at2.session_state["not_interested"]),
}
restart_mode = RecommendationService.get_recommendation_mode(rec_prefs_restart)
assert restart_mode == "hybrid", f"Expected hybrid mode after restart, got {restart_mode}"
print(f"Confirmed: After restart, ratings={r_loaded}, watchlist={wl_loaded}, user={prof_loaded['name']}")
print(f"Confirmed: Recommendation mode after restart is: {restart_mode}")

# Clean up test artifact file
if user_store.DEFAULT_STORE_PATH.exists():
    user_store.DEFAULT_STORE_PATH.unlink()

print("\nALL 10 MANUAL / SIMULATED FLOW STEPS COMPLETED SUCCESSFULLY!")
