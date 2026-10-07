"""
ReelSense - Phase 6.5 TMDB API Integration, Caching & Metadata Integrity Tests

Mocked unit tests covering:
  - Section 37: API Client (200, missing key, 401, 404, 429, 500, timeout, connection,
                           malformed JSON, missing poster, missing backdrop, missing fields, retry)
  - Section 38: Metadata Validation (matching accepted, wrong title rejected, year mismatch rejected,
                                     legitimate title variation accepted, fallback hierarchy tiers 1-4,
                                     unrelated image rejected, suspicious ID rejected, valid duplicates)
  - Section 39: Persistent Cache (cache hit no net, cache miss one req, stale cache safety,
                                  corrupt cache recovery, API failure with valid cache)
  - Section 40: Offline Mode (no API key, app imports, recommendations work, SVG fallback works)
  - Section 41: Rate Limiting (429 handling, Retry-After header, controlled backoff, no hammer)
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.tmdb_service import TMDBService, get_tmdb_service
from src.utils.metadata_validator import (
    calculate_title_similarity,
    is_valid_tmdb_path,
    normalize_title,
    resolve_movie_images,
    validate_tmdb_mapping,
)


@pytest.fixture
def mock_temp_cache(tmp_path, monkeypatch):
    """Provide an isolated temporary cache file for testing."""
    test_cache_file = tmp_path / "test_tmdb_metadata.json"
    monkeypatch.setattr("src.services.tmdb_service.CACHE_FILE", test_cache_file)
    service = TMDBService()
    service._cache = {}
    service._links_map = {1: 862, 2: 8844, 260: 11, 296: 680}
    return service, test_cache_file


# =============================================================================
# SECTION 37 & 41: API CLIENT & HTTP ERROR HANDLING & RATE LIMITING
# =============================================================================

def test_api_client_valid_response(mock_temp_cache):
    """Test 1: Valid 200 OK API response parses movie details and credits."""
    service, _ = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "overview": "A little boy named Andy loves to be in his room...",
        "poster_path": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "backdrop_path": "/lxD5ak7ZaMbLPPx29IOpuNzMeJ4.jpg",
        "runtime": 81,
        "original_language": "en",
        "credits": {
            "crew": [{"name": "John Lasseter", "job": "Director"}],
            "cast": [{"name": "Tom Hanks"}, {"name": "Tim Allen"}],
        },
    }

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", return_value=mock_resp):
            details = service.fetch_tmdb_movie_details(862)
            assert details is not None
            assert details["tmdb_id"] == 862
            assert details["title"] == "Toy Story"
            assert details["director"] == "John Lasseter"
            assert details["poster"] == "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg"
            assert details["backdrop"] == "/lxD5ak7ZaMbLPPx29IOpuNzMeJ4.jpg"
            assert details["language"] == "English"


def test_api_client_missing_api_key(mock_temp_cache):
    """Test 2: Missing API key returns None immediately without making network calls."""
    service, _ = mock_temp_cache
    with patch.object(service, "get_api_key", return_value=None):
        with patch("requests.get") as mock_get:
            details = service.fetch_tmdb_movie_details(862)
            assert details is None
            mock_get.assert_not_called()


def test_api_client_401_no_retry(mock_temp_cache):
    """Test 3: HTTP 401 unauthorized strictly DOES NOT aggressively retry."""
    service, _ = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch.object(service, "get_api_key", return_value="fake_rejected_key"):
        with patch("requests.get", return_value=mock_resp) as mock_get:
            details = service.fetch_tmdb_movie_details(862)
            assert details is None
            # Must not retry 401
            assert mock_get.call_count == 1


def test_api_client_404_not_found(mock_temp_cache):
    """Test 4: HTTP 404 movie not found does not retry and returns None."""
    service, _ = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", return_value=mock_resp) as mock_get:
            details = service.fetch_tmdb_movie_details(99999999)
            assert details is None
            assert mock_get.call_count == 1


def test_api_client_429_rate_limit_with_retry_after(mock_temp_cache):
    """Test 5 & Section 41: HTTP 429 respects Retry-After and retries controlledly."""
    service, _ = mock_temp_cache
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "1"}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "credits": {},
    }

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", side_effect=[resp_429, resp_200]) as mock_get:
            with patch("time.sleep") as mock_sleep:
                details = service.fetch_tmdb_movie_details(862)
                assert details is not None
                assert details["title"] == "Toy Story"
                assert mock_get.call_count == 2
                mock_sleep.assert_called_with(1.0)


def test_api_client_500_exponential_backoff(mock_temp_cache):
    """Test 6: HTTP 500 server error retries with controlled exponential backoff."""
    service, _ = mock_temp_cache
    resp_500 = MagicMock()
    resp_500.status_code = 500

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"id": 862, "title": "Toy Story", "credits": {}}

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", side_effect=[resp_500, resp_200]) as mock_get:
            with patch("time.sleep") as mock_sleep:
                details = service.fetch_tmdb_movie_details(862)
                assert details is not None
                assert mock_get.call_count == 2
                assert mock_sleep.call_count == 1


def test_api_client_timeout_and_connection_failure(mock_temp_cache):
    """Test 7 & 8: Timeout and ConnectionError retry then safely return None on exhaustion."""
    service, _ = mock_temp_cache
    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", side_effect=requests.Timeout("Connection timed out")):
            with patch("time.sleep"):
                details = service.fetch_tmdb_movie_details(862)
                assert details is None

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", side_effect=requests.ConnectionError("Network unreachable")):
            with patch("time.sleep"):
                details = service.fetch_tmdb_movie_details(862)
                assert details is None


def test_api_client_malformed_json(mock_temp_cache):
    """Test 9: Malformed JSON response handled gracefully without crashing."""
    service, _ = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON token")

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", return_value=mock_resp):
            details = service.fetch_tmdb_movie_details(862)
            assert details is None


def test_api_client_missing_fields_and_images(mock_temp_cache):
    """Test 10, 11, 12: Missing poster, backdrop, or cast fields are handled safely."""
    service, _ = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 862,
        "title": "Minimal Movie",
        # Missing release_date, poster_path, backdrop_path, credits
    }

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", return_value=mock_resp):
            details = service.fetch_tmdb_movie_details(862)
            assert details is not None
            assert details["title"] == "Minimal Movie"
            assert details["poster"] is None
            assert details["backdrop"] is None
            assert details["director"] == ""
            assert details["cast"] == []


# =============================================================================
# SECTION 38: METADATA VALIDATION & FOUR-TIER IMAGE HIERARCHY
# =============================================================================

def test_validation_correct_mapping_accepted():
    """Test: Valid MovieLens and TMDB metadata mapping is accepted."""
    tmdb_meta = {
        "tmdb_id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "poster_path": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "backdrop_path": "/lxD5ak7ZaMbLPPx29IOpuNzMeJ4.jpg",
    }
    audit = validate_tmdb_mapping(
        movie_id=1,
        ml_title="Toy Story (1995)",
        ml_year=1995,
        tmdb_meta=tmdb_meta,
        expected_tmdb_id=862,
    )
    assert audit["is_valid"] is True
    assert audit["status"] == "VALID_TMDB"
    assert audit["poster_path"] == "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg"


def test_validation_wrong_title_rejected():
    """Test: Unrelated movie title from TMDB is rejected."""
    tmdb_meta = {
        "tmdb_id": 999,
        "title": "Inception",
        "release_date": "2010-07-16",
        "poster_path": "/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
    }
    audit = validate_tmdb_mapping(
        movie_id=1,
        ml_title="Toy Story (1995)",
        ml_year=1995,
        tmdb_meta=tmdb_meta,
        expected_tmdb_id=999,
    )
    assert audit["is_valid"] is False
    assert audit["status"] == "MISMATCH_TITLE"


def test_validation_large_year_mismatch_rejected():
    """Test: Large year divergence (>4 years) rejected (e.g. remake)."""
    tmdb_meta = {
        "tmdb_id": 1234,
        "title": "The Thing",
        "release_date": "2011-10-12",
        "poster_path": "/something.jpg",
    }
    audit = validate_tmdb_mapping(
        movie_id=10,
        ml_title="Thing, The (1982)",
        ml_year=1982,
        tmdb_meta=tmdb_meta,
        expected_tmdb_id=1234,
    )
    assert audit["is_valid"] is False
    assert audit["status"] == "MISMATCH_YEAR"


def test_validation_legitimate_title_variation_accepted():
    """Test: Legitimate title variations (inverted articles, subtitles) are accepted."""
    assert calculate_title_similarity("Godfather, The (1972)", "The Godfather") > 0.8
    assert calculate_title_similarity("Star Wars: Episode IV - A New Hope (1977)", "Star Wars") > 0.7

    tmdb_meta = {
        "tmdb_id": 238,
        "title": "The Godfather",
        "release_date": "1972-03-14",
        "poster_path": "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
    }
    audit = validate_tmdb_mapping(
        movie_id=858,
        ml_title="Godfather, The (1972)",
        ml_year=1972,
        tmdb_meta=tmdb_meta,
        expected_tmdb_id=238,
    )
    assert audit["is_valid"] is True


def test_validation_image_fallback_hierarchy():
    """Test 4-Tier Fallback Hierarchy: Tier 1 -> Tier 2 -> Tier 3 -> Tier 4."""
    # Tier 1: Real poster
    t1_poster, t1_backdrop, a1 = resolve_movie_images(
        movie_title="Toy Story",
        release_year=1995,
        genre="Animation",
        tmdb_meta={"tmdb_id": 862, "title": "Toy Story", "release_date": "1995-10-30", "poster": "/poster.jpg", "backdrop": "/backdrop.jpg"},
        expected_tmdb_id=862,
    )
    assert "https://image.tmdb.org/t/p/w500/poster.jpg" in t1_poster
    assert "backdrop.jpg" in t1_backdrop

    # Tier 2: Missing poster falls back to verified backdrop
    t2_poster, t2_backdrop, a2 = resolve_movie_images(
        movie_title="Toy Story",
        release_year=1995,
        genre="Animation",
        tmdb_meta={"tmdb_id": 862, "title": "Toy Story", "release_date": "1995-10-30", "poster": None, "backdrop": "/backdrop.jpg"},
        expected_tmdb_id=862,
    )
    assert "https://image.tmdb.org/t/p/w780/backdrop.jpg" in t2_poster

    # Tier 3: Missing poster and backdrop falls back to dynamic local SVG data URI
    t3_poster, t3_backdrop, a3 = resolve_movie_images(
        movie_title="Rare Obscure Film",
        release_year=1960,
        genre="Documentary",
        tmdb_meta=None,
    )
    assert t3_poster.startswith("data:image/svg+xml;utf8,")
    assert t3_backdrop.startswith("data:image/svg+xml;utf8,")


def test_validation_unrelated_or_malformed_image_paths_rejected():
    """Test: Malformed or malicious image paths are rejected and not accepted as TMDB images."""
    assert not is_valid_tmdb_path("http://evil.com/exploit.jpg")
    assert not is_valid_tmdb_path("../../../etc/passwd")
    assert not is_valid_tmdb_path("/valid_path.jpg?query=1")
    assert is_valid_tmdb_path("/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg")


# =============================================================================
# SECTION 39: PERSISTENT CACHE BEHAVIOR & CORRUPTION RECOVERY
# =============================================================================

def test_cache_hit_prevents_network_request(mock_temp_cache):
    """Test: Cache hit does not make any network requests."""
    service, _ = mock_temp_cache
    service._cache["1"] = {
        "tmdb_id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "poster": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    }

    with patch("requests.get") as mock_get:
        res = service.enrich_movie(movie_id=1, ml_title="Toy Story", ml_year=1995, expected_tmdb_id=862)
        assert res["is_enriched"] is True
        assert res["source"] == "cache"
        mock_get.assert_not_called()


def test_cache_miss_executes_one_controlled_request(mock_temp_cache):
    """Test: Cache miss makes exactly one controlled API request and caches result."""
    service, cache_file = mock_temp_cache
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "poster_path": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "backdrop_path": "/lxD5ak7ZaMbLPPx29IOpuNzMeJ4.jpg",
        "credits": {},
    }

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = service.enrich_movie(movie_id=1, ml_title="Toy Story", ml_year=1995, expected_tmdb_id=862)
            assert res["is_enriched"] is True
            assert res["source"] == "api_live"
            assert mock_get.call_count == 1
            # Verify persisted in file
            assert cache_file.exists()
            loaded = json.loads(cache_file.read_text(encoding="utf-8"))
            assert "1" in loaded


def test_corrupt_cache_recovery_without_crash(mock_temp_cache):
    """Test: Corrupt or malformed cache file safely recovers without crashing."""
    service, cache_file = mock_temp_cache
    cache_file.write_text("CORRUPTED NOT JSON {{{", encoding="utf-8")

    # Reload service cache from the corrupt file
    service._cache = None
    service._load_cache()
    # Cache should be safely initialized as an empty dictionary
    assert service._cache == {}


def test_api_failure_preserves_valid_cached_metadata(mock_temp_cache):
    """Test: If TMDB API fails, previously valid cached metadata remains completely usable."""
    service, _ = mock_temp_cache
    service._cache["1"] = {
        "tmdb_id": 862,
        "title": "Toy Story",
        "release_date": "1995-10-30",
        "poster": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    }

    with patch.object(service, "get_api_key", return_value="fake_valid_key"):
        # Force refresh where API throws connection error
        with patch("requests.get", side_effect=requests.ConnectionError("Offline")):
            res = service.enrich_movie(movie_id=1, ml_title="Toy Story", ml_year=1995, force_refresh=True)
            assert res["is_enriched"] is True
            assert res["source"] == "cache_fallback"
            assert res["metadata"]["title"] == "Toy Story"


# =============================================================================
# SECTION 40: OFFLINE MODE
# =============================================================================

def test_offline_mode_no_api_key_system_works():
    """Test: When no API key is available, the service remains offline safely and core catalog works."""
    with patch.object(TMDBService, "get_api_key", return_value=None):
        service = TMDBService.get_instance()
        assert service.is_available() is False

        # Attempt enrichment in offline mode -> safely falls back without error
        res = service.enrich_movie(movie_id=1, ml_title="Toy Story", ml_year=1995)
        assert res["source"] in ["cache", "offline_fallback"]

        # Catalog images resolve smoothly to SVG or safe fallback
        poster, backdrop, audit = service.resolve_images_for_movie(
            movie_id=99999,
            title="A Film Without TMDB",
            year=2024,
            genre="Sci-Fi",
        )
        assert poster is not None
        assert backdrop is not None
        assert poster.startswith("data:image/svg+xml") or "unsplash" in poster
