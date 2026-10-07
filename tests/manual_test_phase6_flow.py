"""
ReelSense - Phase 6 Interactive Feature Flow Test
Simulates and verifies:
1. Fresh user startup (Taste Evolution empty state)
2. 1-rating state (Cold-start Breakdown with early references, Taste Evolution minimal state)
3. 3-rating state (Unlocks Hybrid Breakdown 2.0 with content/collab contributions & reference movies)
4. Taste Evolution across milestones (1st -> 3rd -> Current)
5. Detected taste shifts and automated insights
6. 5-rating expansion and milestone adaptation
"""
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.services.catalog import get_catalog
from src.services.movie_service import MovieService
from src.services.recommendation_service import RecommendationService
from src.services.taste_service import TasteService
from src.services import user_store


def run_phase6_manual_flow():
    print("=" * 60)
    print("REELSENSE PHASE 6 — INTERACTIVE VERIFICATION FLOW")
    print("=" * 60)

    # 1. Fresh user startup
    print("\n[Step 1] Fresh user startup...")
    evo_empty = TasteService.get_taste_evolution({})
    assert evo_empty["is_empty"] is True
    assert evo_empty["total_rated"] == 0
    print("  -> Passed: Fresh user has empty taste evolution state.")

    # 2. Rate 1 movie (< 3 threshold)
    print("\n[Step 2] Rate 1 movie (< 3 threshold: Toy Story ID 1 rated 4.5)...")
    ratings_1 = {1: 4.5}
    # Inspect movie details breakdown for Jurassic Park (ID 480)
    jp_movie = MovieService.get_movie_by_id(480)
    bd_cold = TasteService.get_recommendation_breakdown(jp_movie, user_ratings=ratings_1)
    assert bd_cold["is_cold_start"] is True
    assert bd_cold["content_score"] is None
    assert bd_cold["collab_score"] is None
    assert len(bd_cold["positive_references"]) == 1
    assert bd_cold["positive_references"][0]["id"] == 1
    print(f"  -> Passed: Cold-start breakdown explains curation and references Toy Story (sim: {bd_cold['positive_references'][0]['similarity']}).")

    # 3. Taste Evolution minimal state (1 rating)
    print("\n[Step 3] Taste Evolution with 1 rating...")
    evo_1 = TasteService.get_taste_evolution(ratings_1)
    assert evo_1["is_minimal"] is True
    assert len(evo_1["milestones"]) == 1
    assert evo_1["milestones"][0]["label"] == "1st Rating"
    print(f"  -> Passed: Minimal evolution anchors in {evo_1['milestones'][0]['dominant_genre']}.")

    # 4. Rate 3 movies (Hybrid threshold reached)
    print("\n[Step 4] Rate 3 movies (Toy Story: 4.0, Star Wars IV: 5.0, Jurassic Park: 4.5)...")
    ratings_3 = {1: 4.0, 260: 5.0, 480: 4.5}
    matrix_movie = MovieService.get_movie_by_id(2571)  # The Matrix
    bd_hybrid = TasteService.get_recommendation_breakdown(matrix_movie, user_ratings=ratings_3)
    assert bd_hybrid["is_cold_start"] is False
    assert bd_hybrid["content_score"] is not None
    assert bd_hybrid["collab_score"] is not None
    assert bd_hybrid["hybrid_score"] is not None
    assert bd_hybrid["content_contrib"] is not None
    assert bd_hybrid["collab_contrib"] is not None
    print(f"  -> Passed: Hybrid Breakdown active! Content: {bd_hybrid['content_match_pct']}%, Collab: {bd_hybrid['collab_match_pct']}%, Hybrid: {bd_hybrid['hybrid_score']:.2f}")
    print(f"     Contribution: 0.4x{bd_hybrid['content_score']:.2f} ({bd_hybrid['content_contrib']:.2f}) + 0.6x{bd_hybrid['collab_score']:.2f} ({bd_hybrid['collab_contrib']:.2f})")
    assert len(bd_hybrid["positive_references"]) > 0
    top_ref = bd_hybrid["positive_references"][0]
    print(f"     Top positive reference: {top_ref['title']} ({top_ref['similarity']:.2f} sim)")

    # 5. Taste Evolution with 3 ratings
    print("\n[Step 5] Taste Evolution with 3 ratings...")
    evo_3 = TasteService.get_taste_evolution(ratings_3)
    assert evo_3["is_minimal"] is False
    assert len(evo_3["milestones"]) == 2  # 1st and 3rd
    assert "1st Rating" in evo_3["milestones"][0]["label"]
    assert "3rd Rating" in evo_3["milestones"][1]["label"]
    print(f"  -> Passed: Milestones generated: {[m['label'] for m in evo_3['milestones']]}")
    print(f"     Dominant genres: {evo_3['milestones'][0]['dominant_genre']} -> {evo_3['milestones'][1]['dominant_genre']}")

    # 6. Rate 5 movies to test milestone adaptation and taste shifts
    print("\n[Step 6] Rate 5 movies (expanding into Sci-Fi and Thriller)...")
    # Add Empire Strikes Back (1196: 5.0) and Matrix (2571: 5.0)
    ratings_5 = {1: 3.5, 260: 5.0, 480: 4.25, 1196: 5.0, 2571: 5.0}
    evo_5 = TasteService.get_taste_evolution(ratings_5)
    assert len(evo_5["milestones"]) == 3  # 1st, 3rd, 5th
    assert "5th Rating" in evo_5["milestones"][2]["label"]
    assert len(evo_5["taste_shifts"]) > 0
    shift_summaries = [f"{s['genre']} ({'+' if s['delta'] > 0 else ''}{s['delta']}%)" for s in evo_5["taste_shifts"]]
    print(f"  -> Passed: Detected taste shifts: {shift_summaries}")
    print(f"     Automated Insight - Emerging: {evo_5['insights']['emerging']}")
    print(f"     Automated Insight - Consistent: {evo_5['insights']['consistent']}")
    print(f"     Automated Insight - Biggest change: {evo_5['insights']['biggest_change']}")

    # 7. Exclusions test
    print("\n[Step 7] Exclude movie from recommendations...")
    recs = RecommendationService.get_recommended_for_user(
        {"ratings": ratings_5, "hidden_ids": [1196, 2571]}, limit=6
    )
    rec_ids = [m["id"] for m in recs]
    assert 1196 not in rec_ids
    assert 2571 not in rec_ids
    print("  -> Passed: Excluded movies strictly omitted from recommended list.")

    print("\n" + "=" * 60)
    print("SUCCESS: ALL PHASE 6 FLOW VERIFICATIONS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase6_manual_flow()
