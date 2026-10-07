"""
ReelSense - TMDB Metadata & Image Enrichment Script (Phase 6.5)

Enriches the MovieLens catalog with verified TMDB metadata (posters, backdrops,
overviews, runtime, director, principal cast, language).

Security & Integrity Guarantees:
  - Zero hardcoded keys; reads securely via TMDBService (Streamlit secrets -> secrets.toml -> env)
  - Never logs or prints the API key
  - Respects MovieLens as the authoritative source
  - Validates cross-source title similarity and year divergence
  - Skips already-valid cached records (fully resumable)
  - Controlled pacing to respect TMDB rate limits
  - Atomic persistence to data/tmdb_metadata.json

Usage:
  python data/enrich_tmdb.py                 # Enrich active catalog (default 2000)
  python data/enrich_tmdb.py --sample 20      # Controlled audit / test on 20 movies
  python data/enrich_tmdb.py --limit 100      # Enrich up to 100 movies
"""

import argparse
import logging
import re
import sys
import time
from pathlib import Path

# Add project root to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from data.loader import DATA_DIR, load_movies, load_ratings
from src.services.tmdb_service import TMDBService, get_tmdb_service
from src.utils.metadata_validator import is_valid_tmdb_path, validate_tmdb_mapping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("enrich_tmdb")


def parse_args():
    parser = argparse.ArgumentParser(description="ReelSense TMDB Catalog Enrichment")
    parser.add_argument(
        "--catalog-size",
        type=int,
        default=2000,
        help="Target number of top MovieLens movies to consider (default: 2000)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Run on a representative sample of N movies for verification",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of network requests performed in this run",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetching even if valid cached metadata exists",
    )
    return parser.parse_args()


def run_enrichment():
    args = parse_args()
    service = get_tmdb_service()

    if not service.is_available():
        print("\n" + "=" * 60)
        print("TMDB API Key Not Configured")
        print("=" * 60)
        print("To enable live TMDB enrichment, configure your key in either:")
        print("  1. .streamlit/secrets.toml  (TMDB_API_KEY = \"your_key\")")
        print("  2. Environment variable: $env:TMDB_API_KEY=\"your_key\"")
        print("\nReelSense will continue to operate normally with procedural SVG fallbacks.\n")
        sys.exit(1)

    links_path = DATA_DIR / "links.csv"
    if not links_path.exists():
        sys.exit(f"Error: {links_path} not found.")

    print("\n" + "=" * 60)
    print("ReelSense TMDB Metadata Enrichment Engine (Phase 6.5)")
    print("=" * 60)

    # Load MovieLens catalog
    movies_df = load_movies().set_index("movieId")
    ratings_df = load_ratings()
    links_df = pd.read_csv(links_path).dropna(subset=["tmdbId"])
    links_map = dict(zip(links_df["movieId"].astype(int), links_df["tmdbId"].astype(int)))

    # Select top movies by rating count
    top_ids = ratings_df.groupby("movieId").size().nlargest(args.catalog_size).index.tolist()
    active_ids = [m_id for m_id in top_ids if m_id in movies_df.index]

    if args.sample:
        active_ids = active_ids[: args.sample]
        print(f"Running controlled verification sample on {len(active_ids)} movies.")
    else:
        print(f"Target active catalog: {len(active_ids)} movies.")

    # Inspect current cache
    cache = service.get_all_cached_metadata()
    valid_cached = 0
    needs_enrichment = []

    for m_id in active_ids:
        row = movies_df.loc[m_id]
        ml_title = row.title
        ml_year = int(row.year) if pd.notna(row.year) else None
        expected_tmdb = links_map.get(int(m_id))

        cached_meta = cache.get(str(m_id))
        if cached_meta and not args.force:
            audit = validate_tmdb_mapping(
                movie_id=m_id,
                ml_title=ml_title,
                ml_year=ml_year,
                tmdb_meta=cached_meta,
                expected_tmdb_id=expected_tmdb,
            )
            if audit["is_valid"]:
                valid_cached += 1
                continue
        needs_enrichment.append(m_id)

    print(f"Already verified in cache: {valid_cached} / {len(active_ids)}")
    print(f"Pending enrichment: {len(needs_enrichment)}")

    if not needs_enrichment:
        print("All target movies already have verified metadata cached. Nothing to do!")
        return

    to_process = needs_enrichment
    if args.limit:
        to_process = to_process[: args.limit]
        print(f"Limiting execution to {len(to_process)} movies as requested.")

    success_count = 0
    rejected_count = 0
    skipped_count = 0

    print("\nStarting rate-controlled enrichment...\n")

    for idx, m_id in enumerate(to_process, 1):
        row = movies_df.loc[m_id]
        ml_title = row.title
        ml_year = int(row.year) if pd.notna(row.year) else None
        expected_tmdb = links_map.get(int(m_id))

        if not expected_tmdb:
            skipped_count += 1
            print(f"[{idx}/{len(to_process)}] SKIPPED (No TMDB ID in links.csv): movieId={m_id} '{ml_title}'")
            continue

        result = service.enrich_movie(
            movie_id=m_id,
            ml_title=ml_title,
            ml_year=ml_year,
            expected_tmdb_id=expected_tmdb,
            force_refresh=args.force,
        )

        if result["is_enriched"]:
            success_count += 1
            meta = result["metadata"]
            poster_tag = "[POSTER]" if is_valid_tmdb_path(meta.get("poster")) else "[NO POSTER]"
            backdrop_tag = "[BACKDROP]" if is_valid_tmdb_path(meta.get("backdrop")) else ""
            print(f"[{idx}/{len(to_process)}] OK: movieId={m_id} -> TMDB {meta.get('tmdb_id')} | '{meta.get('title')}' {poster_tag} {backdrop_tag}")
        else:
            rejected_count += 1
            audit_reason = result.get("audit", {}).get("reason", "Unknown")
            print(f"[{idx}/{len(to_process)}] REJECTED / FALLBACK: movieId={m_id} '{ml_title}' -> {audit_reason}")

        # Controlled pacing: 350ms delay between requests to stay well within TMDB rate limits (approx 3 req/sec)
        time.sleep(0.35)

    print("\n" + "=" * 60)
    print("Enrichment Run Summary")
    print("=" * 60)
    print(f"Successfully enriched: {success_count}")
    print(f"Validation rejected / fallback: {rejected_count}")
    print(f"Skipped (missing mapping): {skipped_count}")

    stats = service.get_cache_stats()
    print(f"Total cached movies in vault: {stats['total_cached']}")
    print(f"Movies with verified TMDB poster: {stats['with_poster']}")
    print(f"Movies with verified TMDB backdrop: {stats['with_backdrop']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_enrichment()
