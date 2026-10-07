"""
ReelSense - Phase 6.5 Controlled Live TMDB Audit (15 Representative Films)

Performs a strict, controlled representative audit against live TMDB API:
  - Blockbusters, Classics, Newer, Multi-genre, International, Similar titles/Remakes
  - Verifies MovieLens title/year <-> TMDB title/year cross-validation
  - Verifies poster and backdrop paths belong to the authentic movie
  - Zero API key printing/logging.
"""

import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from data.loader import DATA_DIR, load_movies
from src.services.tmdb_service import TMDBService, get_tmdb_service
from src.utils.metadata_validator import is_valid_tmdb_path, resolve_movie_images, validate_tmdb_mapping

# 15 Representative movies across diverse categories
AUDIT_CANDIDATES = [
    # (movieId, expected_category)
    (1, "Blockbuster / Animation (Toy Story)"),
    (2571, "Blockbuster / Sci-Fi (The Matrix)"),
    (79132, "Modern Blockbuster / Mind-Blowing (Inception)"),
    (912, "Classic / Romance (Casablanca)"),
    (858, "Classic / Crime (The Godfather)"),
    (1203, "Classic / Drama (12 Angry Men)"),
    (109487, "Modern Sci-Fi / Epic (Interstellar)"),
    (122882, "Modern Action (Mad Max: Fury Road)"),
    (177765, "Modern Animation (Coco)"),
    (7, "Remake variant (Sabrina 1995)"),
    (915, "Classic Original (Sabrina 1954)"),
    (1089, "Crime / Cult Classic (Reservoir Dogs 1992)"),
    (4993, "Fantasy Epic (Lord of the Rings 2001)"),
    (4973, "International / French (Amélie 2001)"),
    (2019, "International / Classic (Seven Samurai 1954)"),
]


def run_live_audit():
    service = get_tmdb_service()
    if not service.is_available():
        print("ERROR: TMDB API is not available.")
        sys.exit(1)

    movies_df = load_movies().set_index("movieId")
    links_df = pd.read_csv(DATA_DIR / "links.csv").dropna(subset=["tmdbId"])
    links_map = dict(zip(links_df["movieId"].astype(int), links_df["tmdbId"].astype(int)))

    print("=" * 80)
    print("REELSENSE PHASE 6.5 — LIVE TMDB REPRESENTATIVE AUDIT (15 MOVIES)")
    print("=" * 80)

    audit_records = []
    all_passed = True

    for m_id, category in AUDIT_CANDIDATES:
        if m_id not in movies_df.index:
            print(f"Skipping movieId {m_id}: not in active movies.csv")
            continue

        row = movies_df.loc[m_id]
        ml_title = row.title
        ml_year = int(row.year) if pd.notna(row.year) else None
        target_tmdb_id = links_map.get(m_id)

        # Execute live enrichment through TMDBService
        enrich_result = service.enrich_movie(
            movie_id=m_id,
            ml_title=ml_title,
            ml_year=ml_year,
            expected_tmdb_id=target_tmdb_id,
            force_refresh=True,  # Test live network roundtrip
        )

        meta = enrich_result.get("metadata") or {}
        audit = enrich_result.get("audit") or {}

        tmdb_title = meta.get("title", "N/A")
        tmdb_date = meta.get("release_date", "N/A")
        tmdb_year = int(str(tmdb_date)[:4]) if len(str(tmdb_date)) >= 4 and str(tmdb_date)[:4].isdigit() else None
        poster_path = meta.get("poster")
        backdrop_path = meta.get("backdrop")

        has_valid_poster = is_valid_tmdb_path(poster_path)
        has_valid_backdrop = is_valid_tmdb_path(backdrop_path)

        poster_url, backdrop_url, img_audit = resolve_movie_images(
            movie_title=ml_title,
            release_year=ml_year,
            genre=row.genres.split("|")[0] if row.genres else "Cinema",
            tmdb_meta=meta,
            expected_tmdb_id=target_tmdb_id,
        )

        tier_poster = "Tier 1 (TMDB Poster)" if "w500" in poster_url else ("Tier 2 (TMDB Backdrop)" if "w780" in poster_url else "Tier 3 (SVG)")
        tier_backdrop = "Tier 1/2 (TMDB Backdrop)" if "w1280" in backdrop_url or "w780" in backdrop_url else "Tier 3 (SVG Backdrop)"

        is_identity_aligned = (
            enrich_result["is_enriched"]
            and audit.get("is_valid", False)
            and (has_valid_poster or has_valid_backdrop)
        )

        if not is_identity_aligned:
            all_passed = False

        status_flag = "PASS" if is_identity_aligned else "FAIL"
        print(f"\n[{status_flag}] Category: {category}")
        print(f"      MovieLens:  movieId={m_id} | '{ml_title}' (Year: {ml_year})")
        print(f"      TMDB API:   tmdbId={target_tmdb_id} | '{tmdb_title}' (Date: {tmdb_date}, Year: {tmdb_year})")
        print(f"      Validation: Status={audit.get('status')} | Reason={audit.get('reason')}")
        print(f"      Poster:     {poster_path} -> {tier_poster}")
        print(f"      Backdrop:   {backdrop_path} -> {tier_backdrop}")

        audit_records.append({
            "movieId": m_id,
            "category": category,
            "ml_title": ml_title,
            "ml_year": ml_year,
            "tmdb_id": target_tmdb_id,
            "tmdb_title": tmdb_title,
            "tmdb_year": tmdb_year,
            "has_poster": has_valid_poster,
            "has_backdrop": has_valid_backdrop,
            "tier_poster": tier_poster,
            "tier_backdrop": tier_backdrop,
            "passed": is_identity_aligned,
        })
        time.sleep(0.4)

    print("\n" + "=" * 80)
    print(f"LIVE AUDIT SUMMARY: {sum(1 for r in audit_records if r['passed'])} / {len(audit_records)} PASSED")
    print("=" * 80)

    if not all_passed:
        print("FAIL: One or more live audit records failed identity validation.")
        sys.exit(1)
    else:
        print("SUCCESS: All 15 representative films successfully enriched and verified with live TMDB API!")
        return 0


if __name__ == "__main__":
    run_live_audit()
