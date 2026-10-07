"""
ReelSense - Movie Metadata & Poster Integrity Validator (Phase 5.5)

Establishes and verifies the MovieLens -> TMDB -> Poster/Backdrop identity chain:
    MovieLens movieId
            ↓
    MovieLens title/year
            ↓
    MovieLens links.csv
            ↓
    TMDB movie ID
            ↓
    TMDB metadata
            ↓
    poster / backdrop

Validates cross-source title normalization, year divergence thresholds,
safe TMDB CDN path regex patterns, and enforces the deterministic 4-tier image hierarchy:
    Tier 1: Verified TMDB poster
    Tier 2: Verified TMDB backdrop
    Tier 3: Local dynamic SVG poster/backdrop
    Tier 4: Safe external placeholder (resilient against unexpected generation failures)
"""

import difflib
import html
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.utils.image_utils import (
    FALLBACK_UNSPLASH,
    generate_fallback_backdrop,
    generate_fallback_poster,
)

TMDB_CDN_BASE = "https://image.tmdb.org/t/p/"
VALID_PATH_PATTERN = re.compile(r"^/[a-zA-Z0-9_\-\.]+\.(jpg|jpeg|png|webp)$", re.IGNORECASE)


def normalize_title(title: str) -> str:
    """Normalize movie titles for robust cross-catalog matching.
    
    Strips trailing years '(YYYY)', removes leading/trailing articles ('The', 'A', 'An'),
    removes punctuation, and lowercases.
    """
    if not title:
        return ""
    t = str(title).strip()
    # Strip trailing year in parens: "Toy Story (1995)" -> "Toy Story"
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t).strip()
    # Handle inverted articles: "Godfather, The" -> "The Godfather" -> "Godfather"
    inv_match = re.match(r"^(.*),\s*(The|A|An)(?:\s*\(.*\))?$", t, re.IGNORECASE)
    if inv_match:
        t = inv_match.group(1).strip()
    else:
        # Strip leading article: "The Matrix" -> "Matrix"
        t = re.sub(r"^(The|A|An)\s+", "", t, flags=re.IGNORECASE).strip()
    # Remove subtitles or parenthetical notes: "Movie Title (Special Edition)"
    t = re.sub(r"\(.*?\)", "", t).strip()
    # Remove punctuation
    t = re.sub(r"[^\w\s]", "", t).lower().strip()
    return " ".join(t.split())


def extract_year_from_title(title: str) -> Optional[int]:
    """Extract release year from MovieLens title format 'Title (YYYY)'."""
    if not title:
        return None
    match = re.search(r"\((\d{4})\)\s*$", str(title))
    return int(match.group(1)) if match else None


def is_valid_tmdb_path(path: Any) -> bool:
    """Verify that a TMDB image path is a valid relative path from TMDB API."""
    if not path or not isinstance(path, str):
        return False
    path = path.strip()
    if len(path) < 5 or len(path) > 120:
        return False
    return bool(VALID_PATH_PATTERN.match(path))


def calculate_title_similarity(title_a: str, title_b: str) -> float:
    """Compute token-aware similarity between two normalized titles."""
    norm_a = normalize_title(title_a)
    norm_b = normalize_title(title_b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    # Token overlap ratio
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    overlap = len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)

    # Sequence matcher ratio
    seq_ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()

    # If all tokens of the shorter title are contained in the longer title (e.g. subtitles)
    if tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a):
        return max(0.85, seq_ratio)

    return max(overlap, seq_ratio)


def validate_tmdb_mapping(
    movie_id: int,
    ml_title: str,
    ml_year: Optional[int],
    tmdb_meta: Optional[Dict[str, Any]],
    expected_tmdb_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Audit a single MovieLens ↔ TMDB metadata mapping.
    
    Returns:
        dict containing:
            is_valid: bool (True if metadata safely matches the movie)
            status: str code
            reason: str explanation
            poster_path: str or None
            backdrop_path: str or None
            tier_poster: int (1-4)
            tier_backdrop: int (1-4)
    """
    result = {
        "movie_id": movie_id,
        "ml_title": ml_title,
        "ml_year": ml_year,
        "is_valid": False,
        "status": "MISSING_TMDB",
        "reason": "No TMDB metadata available",
        "poster_path": None,
        "backdrop_path": None,
        "tmdb_id": None,
        "tmdb_title": None,
        "tmdb_year": None,
    }

    if not tmdb_meta or not isinstance(tmdb_meta, dict):
        return result

    # 1. ID verification if both provided
    tmdb_id = tmdb_meta.get("tmdb_id")
    result["tmdb_id"] = tmdb_id
    if expected_tmdb_id is not None and tmdb_id is not None:
        if int(expected_tmdb_id) != int(tmdb_id):
            result["status"] = "MISMATCH_ID"
            result["reason"] = f"Expected TMDB ID {expected_tmdb_id} but found {tmdb_id}"
            return result

    # 2. Title verification if TMDB title recorded
    tmdb_title = tmdb_meta.get("title") or tmdb_meta.get("original_title")
    result["tmdb_title"] = tmdb_title
    if tmdb_title:
        similarity = calculate_title_similarity(ml_title, tmdb_title)
        if similarity < 0.45:
            result["status"] = "MISMATCH_TITLE"
            result["reason"] = f"Title similarity too low: '{ml_title}' vs '{tmdb_title}' ({similarity:.2f})"
            return result

    # 3. Year verification if TMDB release date recorded
    release_date = tmdb_meta.get("release_date") or ""
    tmdb_year = None
    if release_date and len(str(release_date)) >= 4 and str(release_date)[:4].isdigit():
        tmdb_year = int(str(release_date)[:4])
        result["tmdb_year"] = tmdb_year
        if ml_year is not None:
            year_diff = abs(ml_year - tmdb_year)
            # Legitimate festival/foreign release dates can differ by up to 2 years.
            # Differences > 4 years indicate a remake, sequel, or different production.
            if year_diff > 4 or (year_diff > 2 and tmdb_title and calculate_title_similarity(ml_title, tmdb_title) < 0.85):
                result["status"] = "MISMATCH_YEAR"
                result["reason"] = f"Year divergence ({ml_year} vs {tmdb_year})"
                return result

    # 4. Image paths validation
    raw_poster = tmdb_meta.get("poster") or tmdb_meta.get("poster_path")
    raw_backdrop = tmdb_meta.get("backdrop") or tmdb_meta.get("backdrop_path")

    valid_poster = raw_poster if is_valid_tmdb_path(raw_poster) else None
    valid_backdrop = raw_backdrop if is_valid_tmdb_path(raw_backdrop) else None

    result["poster_path"] = valid_poster
    result["backdrop_path"] = valid_backdrop
    result["is_valid"] = True
    result["status"] = "VALID_TMDB"
    result["reason"] = "TMDB metadata verified"
    return result


def resolve_movie_images(
    movie_title: str,
    release_year: Optional[int],
    genre: Optional[str],
    tmdb_meta: Optional[Dict[str, Any]] = None,
    expected_tmdb_id: Optional[int] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    """Resolve poster and backdrop URLs strictly following the 4-tier hierarchy.
    
    Tier 1: Validated TMDB poster (w500)
    Tier 2: Validated TMDB backdrop (w780)
    Tier 3: Procedural local SVG data URI
    Tier 4: Safe external placeholder fallback
    
    Returns:
        tuple (poster_url, backdrop_url, audit_info)
    """
    clean_title = re.sub(r"\s*\(\d{4}\)\s*$", "", movie_title).strip()
    inv = re.match(r"^(.*),\s*(The|A|An)(?:\s*\(.*\))?$", clean_title, re.IGNORECASE)
    display_title = f"{inv.group(2)} {inv.group(1)}" if inv else clean_title
    primary_genre = genre or "Cinema"

    audit = validate_tmdb_mapping(
        movie_id=0,
        ml_title=movie_title,
        ml_year=release_year,
        tmdb_meta=tmdb_meta,
        expected_tmdb_id=expected_tmdb_id,
    )

    poster_url = None
    backdrop_url = None
    tier_poster = 4
    tier_backdrop = 4

    # --- POSTER RESOLUTION ---
    if audit["is_valid"] and audit["poster_path"]:
        # Tier 1: Real TMDB poster
        poster_url = f"{TMDB_CDN_BASE}w500{audit['poster_path']}"
        tier_poster = 1
    elif audit["is_valid"] and audit["backdrop_path"]:
        # Tier 2: Real TMDB backdrop as poster
        poster_url = f"{TMDB_CDN_BASE}w780{audit['backdrop_path']}"
        tier_poster = 2
    else:
        # Tier 3: Local SVG Fallback
        try:
            poster_url = generate_fallback_poster(display_title, year=release_year, genre=primary_genre)
            tier_poster = 3
        except Exception:
            # Tier 4: Emergency placeholder fallback
            safe_param = urllib.parse.quote(display_title)
            poster_url = f"https://placehold.co/600x900/1c1b1e/f2ca50?text={safe_param}"
            tier_poster = 4

    # --- BACKDROP RESOLUTION ---
    if audit["is_valid"] and audit["backdrop_path"]:
        # Tier 1: Real TMDB backdrop
        backdrop_url = f"{TMDB_CDN_BASE}w1280{audit['backdrop_path']}"
        tier_backdrop = 1
    elif audit["is_valid"] and audit["poster_path"]:
        # Tier 2: Real TMDB poster as backdrop
        backdrop_url = f"{TMDB_CDN_BASE}w780{audit['poster_path']}"
        tier_backdrop = 2
    else:
        # Tier 3: Local SVG Fallback
        try:
            backdrop_url = generate_fallback_backdrop(display_title, year=release_year, genre=primary_genre)
            tier_backdrop = 3
        except Exception:
            # Tier 4: Emergency placeholder fallback
            safe_param = urllib.parse.quote(display_title)
            backdrop_url = f"https://placehold.co/1600x900/141316/f2ca50?text={safe_param}"
            tier_backdrop = 4

    audit["tier_poster"] = tier_poster
    audit["tier_backdrop"] = tier_backdrop
    return poster_url, backdrop_url, audit


def audit_catalog_integrity(
    catalog: List[Dict[str, Any]],
    links_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Execute a comprehensive metadata and visual asset audit across the active catalog."""
    total = len(catalog)
    unique_ids = len(set(m["id"] for m in catalog))
    unique_titles = len(set(m["title"] for m in catalog))

    tier_counts = {
        "tier_1_tmdb_poster": 0,
        "tier_2_tmdb_backdrop": 0,
        "tier_3_svg_fallback": 0,
        "tier_4_placeholder": 0,
    }

    missing_years = 0
    missing_genres = 0
    duplicate_posters = 0
    seen_posters: Dict[str, str] = {}
    suspicious_mappings: List[Dict[str, Any]] = []

    links_map = {}
    if links_df is not None and not links_df.empty:
        links_map = dict(zip(links_df["movieId"].astype(int), links_df["tmdbId"]))

    for m in catalog:
        m_id = m.get("id")
        title = m.get("title", "")
        p_url = m.get("poster_url", "")
        year = m.get("release_year")
        genres = m.get("genres", [])

        if not year or year == 0:
            missing_years += 1
        if not genres:
            missing_genres += 1

        # Classify poster tier
        if "image.tmdb.org" in p_url:
            if "/w500/" in p_url:
                tier_counts["tier_1_tmdb_poster"] += 1
            else:
                tier_counts["tier_2_tmdb_backdrop"] += 1
        elif p_url.startswith("data:image/svg+xml"):
            tier_counts["tier_3_svg_fallback"] += 1
        else:
            tier_counts["tier_4_placeholder"] += 1

        # Check duplicate poster mappings across different titles (excluding SVG data URIs)
        if "image.tmdb.org" in p_url:
            if p_url in seen_posters and seen_posters[p_url] != title:
                duplicate_posters += 1
            else:
                seen_posters[p_url] = title

        # Verify links mapping if available
        if links_map and m_id in links_map:
            expected_tmdb = links_map[m_id]
            if pd.isna(expected_tmdb):
                suspicious_mappings.append({
                    "movieId": m_id,
                    "title": title,
                    "reason": "Missing tmdbId in links.csv",
                })

    return {
        "catalog_size": total,
        "unique_movie_ids": unique_ids,
        "unique_titles": unique_titles,
        "missing_years": missing_years,
        "missing_genres": missing_genres,
        "tier_distribution": tier_counts,
        "duplicate_posters_found": duplicate_posters,
        "suspicious_mappings_count": len(suspicious_mappings),
        "suspicious_mappings": suspicious_mappings[:10],
        "is_healthy": (
            unique_ids == total
            and missing_years == 0
            and missing_genres == 0
            and total > 0
        ),
    }
