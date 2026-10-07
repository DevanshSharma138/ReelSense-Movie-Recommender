"""
ReelSense - TMDB API Client, Caching & Live Metadata Service (Phase 6.5)

Core Architecture:
    MovieLens (authoritative movie identity)
            ↓
    links.csv (authoritative MovieLens -> TMDB mapping)
            ↓
    TMDBService (in-memory deduplication + persistent cache data/tmdb_metadata.json)
            ↓
    MetadataValidator (cross-source title, year, image validation)
            ↓
    4-Tier Image Fallback Hierarchy:
        Tier 1: Verified TMDB Poster (w500)
        Tier 2: Verified TMDB Backdrop (w780)
        Tier 3: Local Dynamic SVG Data URI
        Tier 4: Safe External Placeholder

Security:
    Zero secret printing, zero secret logging, zero secret exposure in UI.
"""

import json
import logging
import os
import re
import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import tomllib
except ImportError:
    import toml as tomllib  # Fallback for Python < 3.11

import requests

from data.loader import DATA_DIR
from src.utils.metadata_validator import (
    TMDB_CDN_BASE,
    is_valid_tmdb_path,
    resolve_movie_images,
    validate_tmdb_mapping,
)

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"
CACHE_FILE = DATA_DIR / "tmdb_metadata.json"
LINKS_FILE = DATA_DIR / "links.csv"
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30-day freshness policy

LANGUAGE_MAP = {
    "en": "English", "ja": "Japanese", "ko": "Korean", "fr": "French",
    "it": "Italian", "es": "Spanish", "de": "German", "hi": "Hindi",
    "zh": "Chinese", "ru": "Russian", "sv": "Swedish", "da": "Danish",
    "pt": "Portuguese",
}


class TMDBService:
    _instance = None
    _cache: Optional[Dict[str, Any]] = None
    _links_map: Optional[Dict[int, int]] = None
    _session_in_flight: set = set()

    def __init__(self):
        self._load_cache()
        self._load_links()

    @classmethod
    def get_instance(cls) -> "TMDBService":
        if cls._instance is None:
            cls._instance = TMDBService()
        return cls._instance

    # -------------------------------------------------------------------------
    # 1. SECURE API KEY RESOLUTION (Never log or print key value)
    # -------------------------------------------------------------------------
    @staticmethod
    def get_api_key() -> Optional[str]:
        """Resolve TMDB API key following security hierarchy.
        
        Hierarchy:
            1. Streamlit secrets (st.secrets["TMDB_API_KEY"])
            2. Direct .streamlit/secrets.toml reading (for scripts/tests outside Streamlit)
            3. Environment variable (os.environ["TMDB_API_KEY"])
            4. None -> Offline mode
        """
        key = None

        # 1. Try Streamlit runtime secrets
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "TMDB_API_KEY" in st.secrets:
                    key = str(st.secrets["TMDB_API_KEY"]).strip()
                elif "tmdb_api_key" in st.secrets:
                    key = str(st.secrets["tmdb_api_key"]).strip()
        except Exception:
            pass

        # 2. Try direct .streamlit/secrets.toml file read
        if not key:
            secrets_path = Path(__file__).resolve().parent.parent.parent / ".streamlit" / "secrets.toml"
            if secrets_path.exists():
                try:
                    with open(secrets_path, "rb") as f:
                        data = tomllib.load(f)
                    if "TMDB_API_KEY" in data:
                        key = str(data["TMDB_API_KEY"]).strip()
                    elif "tmdb_api_key" in data:
                        key = str(data["tmdb_api_key"]).strip()
                except Exception:
                    pass

        # 3. Try environment variable
        if not key:
            env_key = os.environ.get("TMDB_API_KEY", "").strip()
            if env_key:
                key = env_key

        # Discard empty strings or placeholder templates
        if not key or key in ["your_tmdb_api_key_here", "your_key", "your_real_key", "None"]:
            return None

        return key

    @classmethod
    def is_available(cls) -> bool:
        """Check if TMDB API is configured with a valid key."""
        return cls.get_api_key() is not None

    # -------------------------------------------------------------------------
    # 2. CACHE MANAGEMENT (Atomic persistence & corruption resilience)
    # -------------------------------------------------------------------------
    def _load_cache(self) -> None:
        if self._cache is not None:
            return

        if not CACHE_FILE.exists():
            self._cache = {}
            return

        try:
            content = CACHE_FILE.read_text(encoding="utf-8").strip()
            if not content:
                self._cache = {}
                return
            data = json.loads(content)
            self._cache = data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Cache corruption detected in %s; initializing empty cache. Error: %s", CACHE_FILE.name, str(e))
            self._cache = {}

    def _save_cache(self) -> None:
        """Atomically persist cache dictionary using a temporary file."""
        if self._cache is None:
            return

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(DATA_DIR),
                delete=False,
                prefix="tmdb_meta_",
                suffix=".tmp",
            )
            with temp_file as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Atomic swap with retry for transient Windows file locks
            target_path = str(CACHE_FILE)
            temp_path = temp_file.name
            for attempt in range(4):
                try:
                    os.replace(temp_path, target_path)
                    break
                except OSError:
                    if attempt == 3:
                        # Fallback direct write
                        CACHE_FILE.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass
                    time.sleep(0.05 * (attempt + 1))
        except Exception as e:
            logger.warning("Failed to save TMDB metadata cache: %s", str(e))

    def _load_links(self) -> None:
        if self._links_map is not None:
            return
        if not LINKS_FILE.exists():
            self._links_map = {}
            return
        try:
            import pandas as pd
            df = pd.read_csv(LINKS_FILE).dropna(subset=["tmdbId"])
            self._links_map = dict(zip(df["movieId"].astype(int), df["tmdbId"].astype(int)))
        except Exception as e:
            logger.warning("Failed to load links.csv mapping: %s", str(e))
            self._links_map = {}

    def get_tmdb_id_for_movie(self, movie_id: int) -> Optional[int]:
        if self._links_map is None:
            self._load_links()
        return (self._links_map or {}).get(int(movie_id))

    def get_cached_metadata(self, movie_id: int) -> Optional[Dict[str, Any]]:
        self._load_cache()
        return (self._cache or {}).get(str(movie_id))

    def get_all_cached_metadata(self) -> Dict[str, Any]:
        """Return a copy of all cached TMDB metadata."""
        self._load_cache()
        return dict(self._cache or {})

    def save_cached_metadata(self, movie_id: int, meta: Dict[str, Any]) -> None:
        """Save a single movie's metadata into cache and persist atomically."""
        self._load_cache()
        if self._cache is not None:
            self._cache[str(movie_id)] = meta
            self._save_cache()

    def clear_cache(self) -> None:
        """Reset the internal cache (useful for testing and reload)."""
        self._cache = {}
        if CACHE_FILE.exists():
            try:
                CACHE_FILE.unlink()
            except OSError:
                pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return statistics on current cache content."""
        self._load_cache()
        cache = self._cache or {}
        with_poster = sum(
            1 for m in cache.values()
            if isinstance(m, dict) and is_valid_tmdb_path(m.get("poster") or m.get("poster_path"))
        )
        with_backdrop = sum(
            1 for m in cache.values()
            if isinstance(m, dict) and is_valid_tmdb_path(m.get("backdrop") or m.get("backdrop_path"))
        )
        return {
            "total_cached": len(cache),
            "with_poster": with_poster,
            "with_backdrop": with_backdrop,
        }

    # -------------------------------------------------------------------------
    # 3. HTTP REQUEST ENGINE (Bounded timeouts, controlled backoff, 429 protection)
    # -------------------------------------------------------------------------
    def _execute_api_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 8.0,
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """Execute a secure, rate-limit protected request against TMDB API.
        
        Never logs credentials. Never aggressively retries 401 or 404.
        """
        api_key = self.get_api_key()
        if not api_key:
            return None

        url = f"{TMDB_API_BASE}{endpoint}"
        req_params = dict(params or {})
        headers = {
            "Accept": "application/json",
            "User-Agent": "ReelSense-Recommendation-Engine/6.5",
        }

        # Use Bearer token for v4 keys (length > 40), or query param for v3 keys
        if len(api_key) > 40:
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            req_params["api_key"] = api_key

        attempts = 0
        backoff = 0.5

        while attempts <= max_retries:
            attempts += 1
            try:
                response = requests.get(
                    url,
                    params=req_params,
                    headers=headers,
                    timeout=timeout,
                )

                # HTTP 200: Success
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError:
                        return None

                # HTTP 401 / 403: Invalid credentials — strictly DO NOT retry
                if response.status_code in [401, 403]:
                    logger.warning("TMDB API authentication rejected (HTTP %d). Check configured API key.", response.status_code)
                    return None

                # HTTP 404: Not Found — movie doesn't exist in TMDB, DO NOT retry
                if response.status_code == 404:
                    return None

                # HTTP 429: Rate limited — respect Retry-After header
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_time = min(float(retry_after), 5.0) if retry_after and retry_after.isdigit() else 1.5
                    logger.info("TMDB rate limit encountered (HTTP 429); backing off for %.1fs", wait_time)
                    if attempts <= max_retries:
                        time.sleep(wait_time)
                        continue
                    return None

                # HTTP 500-series: Server error — retry with exponential backoff
                if 500 <= response.status_code < 600:
                    if attempts <= max_retries:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return None

                # Other client errors
                return None

            except (requests.Timeout, requests.ConnectionError) as e:
                # Transient network error — retry
                if attempts <= max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return None
            except requests.RequestException:
                return None

        return None

    # -------------------------------------------------------------------------
    # 4. LIVE METADATA ENRICHMENT (MovieLens-anchored identity & validation)
    # -------------------------------------------------------------------------
    def fetch_tmdb_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Fetch raw movie details and credits from TMDB by tmdbId."""
        if not tmdb_id or int(tmdb_id) <= 0:
            return None

        data = self._execute_api_request(
            f"/movie/{int(tmdb_id)}",
            params={"append_to_response": "credits"},
            timeout=8.0,
        )
        if not data or not isinstance(data, dict):
            return None

        crew = data.get("credits", {}).get("crew", [])
        cast = data.get("credits", {}).get("cast", [])
        director = next((c["name"] for c in crew if c.get("job") == "Director"), "")
        cast_names = [c["name"] for c in cast[:4] if c.get("name")]
        orig_lang = data.get("original_language", "en")
        language = LANGUAGE_MAP.get(orig_lang, (orig_lang or "en").upper())

        return {
            "tmdb_id": int(tmdb_id),
            "title": data.get("title") or data.get("original_title") or "",
            "release_date": data.get("release_date") or "",
            "overview": data.get("overview") or "",
            "poster": data.get("poster_path"),
            "backdrop": data.get("backdrop_path"),
            "runtime": data.get("runtime"),
            "director": director,
            "cast": cast_names,
            "language": language,
            "fetched_at": time.time(),
        }

    def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Clean interface to fetch TMDB movie details by tmdb_id."""
        return self.fetch_tmdb_movie_details(tmdb_id)

    def get_movie_images(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Clean interface to fetch TMDB movie images (poster, backdrop) by tmdb_id."""
        details = self.get_movie_details(tmdb_id)
        if not details:
            return None
        return {
            "poster_path": details.get("poster"),
            "backdrop_path": details.get("backdrop"),
        }

    def enrich_movie(
        self,
        movie_id: int,
        ml_title: str,
        ml_year: Optional[int] = None,
        expected_tmdb_id: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetch, validate, and cache TMDB metadata for a MovieLens movie.
        
        Guaranteed behavior:
            - Checks persistent cache first
            - Verifies cross-source title, year, and image integrity via metadata_validator
            - Deduplicates concurrent in-session requests
            - Never crashes if TMDB API is offline or key is missing
        """
        self._load_cache()
        cached = (self._cache or {}).get(str(movie_id))

        target_tmdb_id = expected_tmdb_id or self.get_tmdb_id_for_movie(movie_id)

        # Cache Hit evaluation
        if cached and isinstance(cached, dict) and not force_refresh:
            audit = validate_tmdb_mapping(
                movie_id=movie_id,
                ml_title=ml_title,
                ml_year=ml_year,
                tmdb_meta=cached,
                expected_tmdb_id=target_tmdb_id,
            )
            # If cached data is valid, return immediately
            if audit["is_valid"]:
                return {
                    "is_enriched": True,
                    "metadata": cached,
                    "audit": audit,
                    "source": "cache",
                }

        # If TMDB API is not configured, return safe fallback based on cached data or SVG
        if not self.get_api_key():
            audit = validate_tmdb_mapping(
                movie_id=movie_id,
                ml_title=ml_title,
                ml_year=ml_year,
                tmdb_meta=cached,
                expected_tmdb_id=target_tmdb_id,
            )
            return {
                "is_enriched": audit["is_valid"],
                "metadata": cached if audit["is_valid"] else None,
                "audit": audit,
                "source": "cache" if audit["is_valid"] else "offline_fallback",
            }

        # Request deduplication: prevent hammering TMDB for same ID in one session
        if movie_id in self._session_in_flight:
            audit = validate_tmdb_mapping(
                movie_id=movie_id,
                ml_title=ml_title,
                ml_year=ml_year,
                tmdb_meta=cached,
                expected_tmdb_id=target_tmdb_id,
            )
            return {
                "is_enriched": audit["is_valid"],
                "metadata": cached if audit["is_valid"] else None,
                "audit": audit,
                "source": "cache",
            }

        # Attempt live API fetch
        self._session_in_flight.add(movie_id)
        try:
            if not target_tmdb_id:
                audit = validate_tmdb_mapping(
                    movie_id=movie_id,
                    ml_title=ml_title,
                    ml_year=ml_year,
                    tmdb_meta=None,
                    expected_tmdb_id=None,
                )
                return {"is_enriched": False, "metadata": None, "audit": audit, "source": "no_tmdb_id"}

            fetched = self.fetch_tmdb_movie_details(target_tmdb_id)
            if not fetched:
                # API request failed or returned 404
                audit = validate_tmdb_mapping(
                    movie_id=movie_id,
                    ml_title=ml_title,
                    ml_year=ml_year,
                    tmdb_meta=cached,
                    expected_tmdb_id=target_tmdb_id,
                )
                return {
                    "is_enriched": audit["is_valid"],
                    "metadata": cached if audit["is_valid"] else None,
                    "audit": audit,
                    "source": "cache_fallback" if audit["is_valid"] else "api_failed",
                }

            # Validate the fetched metadata against MovieLens identity
            audit = validate_tmdb_mapping(
                movie_id=movie_id,
                ml_title=ml_title,
                ml_year=ml_year,
                tmdb_meta=fetched,
                expected_tmdb_id=target_tmdb_id,
            )

            if audit["is_valid"]:
                fetched["validation_status"] = "VALID_TMDB"
                if self._cache is not None:
                    self._cache[str(movie_id)] = fetched
                    self._save_cache()
                return {
                    "is_enriched": True,
                    "metadata": fetched,
                    "audit": audit,
                    "source": "api_live",
                }
            else:
                # Reject metadata if validation failed (e.g. wrong movie, large year divergence)
                logger.warning(
                    "Rejected TMDB metadata for movieId=%d ('%s'): %s",
                    movie_id, ml_title, audit["reason"]
                )
                return {
                    "is_enriched": False,
                    "metadata": None,
                    "audit": audit,
                    "source": "validation_rejected",
                }
        finally:
            self._session_in_flight.discard(movie_id)

    # -------------------------------------------------------------------------
    # 5. UNIFIED 4-TIER IMAGE RESOLVER
    # -------------------------------------------------------------------------
    def resolve_images_for_movie(
        self,
        movie_id: int,
        title: str,
        year: Optional[int] = None,
        genre: Optional[str] = None,
        expected_tmdb_id: Optional[int] = None,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Centralized image resolver returning (poster_url, backdrop_url, audit_info).
        
        Enforces 4-tier hierarchy:
            Tier 1: TMDB Poster (w500)
            Tier 2: TMDB Backdrop (w780)
            Tier 3: Local SVG data URI
            Tier 4: Safe external placeholder
        """
        cached = self.get_cached_metadata(movie_id)
        target_tmdb = expected_tmdb_id or self.get_tmdb_id_for_movie(movie_id)

        poster, backdrop, audit = resolve_movie_images(
            movie_title=title,
            release_year=year,
            genre=genre,
            tmdb_meta=cached,
            expected_tmdb_id=target_tmdb,
        )
        return poster, backdrop, audit


# Global singleton access
def get_tmdb_service() -> TMDBService:
    return TMDBService.get_instance()
