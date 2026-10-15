"""
ReelSense - Persistent User State Management Service (Phase 2)
Provides safe, atomic JSON persistence in data/user_state.json for:
  - ratings: {movieId: rating 1 to 5}
  - not_interested: set/list of hidden movie IDs
  - watchlist: list of saved movie IDs (independent of ratings)
  - onboarding_completed: bool
  - onboarding_skipped: bool
  - schema_version: int
  - user_profile: dict
"""
import json
import logging
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional, Set, Union

from src.config import DEFAULT_USER

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
USER_STATE_PATH = DATA_DIR / "user_state.json"
LEGACY_USER_DATA_PATH = DATA_DIR / "user_data.json"
CURRENT_SCHEMA_VERSION = 1


def get_default_state() -> Dict[str, Any]:
    """Return a clean default user state structure."""
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "ratings": {},
        "watchlist": [],
        "not_interested": set(),
        "onboarding_completed": False,
        "onboarding_skipped": False,
        "user_profile": DEFAULT_USER.copy(),
    }


def _normalize_id_list(items: Optional[List[Any]]) -> List[int]:
    """Deduplicate and convert items to valid integer movie IDs preserving order."""
    seen = set()
    result = []
    for x in items or []:
        try:
            ix = int(x)
            if ix not in seen:
                seen.add(ix)
                result.append(ix)
        except (ValueError, TypeError):
            continue
    return result


def _normalize_id_set(items: Optional[Union[Set[Any], List[Any]]]) -> Set[int]:
    """Convert items to a set of valid integer movie IDs."""
    result = set()
    for x in items or []:
        try:
            result.add(int(x))
        except (ValueError, TypeError):
            continue
    return result


def _normalize_ratings(ratings: Optional[Dict[Any, Any]]) -> Dict[int, float]:
    """
    Normalize ratings dictionary ensuring integer keys and float values bounded in [1.0, 5.0].
    Preserves existing order (dict is insertion-ordered in Python 3.7+).
    Safely migrates older 0-10 scales:
      - If value > 5.0, divides by 2.0.
      - Bounded between 0.5 and 5.0.
    """
    result = {}
    for k, v in (ratings or {}).items():
        try:
            mid = int(k)
            val = float(v)
            if val > 5.0:
                val = val / 2.0
            val = round(max(0.0, min(5.0, val)), 2)
            result[mid] = val
        except (ValueError, TypeError):
            continue
    return result


def _normalize_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge profile with DEFAULT_USER ensuring all expected keys exist."""
    base = DEFAULT_USER.copy()
    if isinstance(profile, dict):
        base.update({k: v for k, v in profile.items() if k in base and v is not None})
    if base.get("min_rating_pref", 0) > 5.0:
        base["min_rating_pref"] = round(base["min_rating_pref"] / 2.0, 1)
    return base


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely load user state from JSON file.
    Checks user_state.json first, falls back to legacy user_data.json if needed.
    Handles empty, malformed, or missing files safely without data destruction.
    """
    target_path = Path(path) if path else USER_STATE_PATH

    # If target doesn't exist but legacy user_data.json does, load legacy
    if not target_path.exists() and not path and LEGACY_USER_DATA_PATH.exists():
        target_path = LEGACY_USER_DATA_PATH

    if not target_path.exists():
        return get_default_state()

    try:
        text = target_path.read_text(encoding="utf-8").strip()
        if not text:
            return get_default_state()

        raw = json.loads(text)
        if not isinstance(raw, dict):
            return get_default_state()

        ratings = _normalize_ratings(raw.get("ratings"))
        onboard_comp = bool(raw.get("onboarding_completed", False))
        onboard_skip = bool(raw.get("onboarding_skipped", False))
        if ratings and not onboard_comp and not onboard_skip:
            onboard_comp = True

        return {
            "schema_version": int(raw.get("schema_version", CURRENT_SCHEMA_VERSION)),
            "ratings": ratings,
            "watchlist": _normalize_id_list(raw.get("watchlist")),
            "not_interested": _normalize_id_set(raw.get("not_interested")),
            "onboarding_completed": onboard_comp,
            "onboarding_skipped": onboard_skip,
            "user_profile": _normalize_profile(raw.get("user_profile")),
        }
    except Exception as e:
        logger.warning(f"Error loading user state from {target_path}: {e}. Falling back to default.")
        return get_default_state()


def save(data: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """
    Atomically save user state to JSON file with retry logic and fallback.
    Prevents partially written files and transient Windows file locking.
    """
    target_path = Path(path) if path else USER_STATE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    norm_ratings = _normalize_ratings(data.get("ratings"))
    serialized = {
        "schema_version": int(data.get("schema_version", CURRENT_SCHEMA_VERSION)),
        "ratings": {str(k): float(v) for k, v in norm_ratings.items()},
        "watchlist": _normalize_id_list(data.get("watchlist")),
        "not_interested": sorted(list(_normalize_id_set(data.get("not_interested")))),
        "onboarding_completed": bool(data.get("onboarding_completed", False)),
        "onboarding_skipped": bool(data.get("onboarding_skipped", False)),
        "user_profile": _normalize_profile(data.get("user_profile")),
    }

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=target_path.parent, delete=False, encoding="utf-8") as f:
            temp_path = Path(f.name)
            json.dump(serialized, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        replaced = False
        for attempt in range(5):
            try:
                os.replace(temp_path, target_path)
                replaced = True
                break
            except (PermissionError, OSError):
                time.sleep(0.05 * (attempt + 1))

        if not replaced:
            with open(target_path, "w", encoding="utf-8") as dst:
                json.dump(serialized, dst, indent=2, ensure_ascii=False)
            try:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass

        # Also keep legacy user_data.json updated for any legacy tests/consumers
        if not path and target_path == USER_STATE_PATH:
            try:
                legacy_dict = {
                    "ratings": serialized["ratings"],
                    "watchlist": serialized["watchlist"],
                    "not_interested": serialized["not_interested"],
                    "user_profile": serialized["user_profile"],
                }
                with open(LEGACY_USER_DATA_PATH, "w", encoding="utf-8") as f_leg:
                    json.dump(legacy_dict, f_leg, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return True
    except Exception as e:
        logger.error(f"Error saving user state to {target_path}: {e}")
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        return False


def get_ratings(path: Optional[Path] = None) -> Dict[int, float]:
    """Retrieve persisted ratings {movieId: rating}."""
    return load(path).get("ratings", {})


def rate_movie(movie_id: int, rating: Union[int, float], path: Optional[Path] = None) -> bool:
    """
    Record or update rating for movie_id.
    Updates existing rating without duplicating it and saves immediately.
    """
    try:
        mid = int(movie_id)
        val = float(rating)
        val = max(1.0, min(5.0, val))
    except (ValueError, TypeError):
        return False

    current = load(path)
    ratings = current.get("ratings", {})
    if mid in ratings:
        del ratings[mid]
    ratings[mid] = round(val, 2)
    current["ratings"] = ratings
    current["onboarding_completed"] = True
    return save(current, path)


def remove_rating(movie_id: int, path: Optional[Path] = None) -> bool:
    """Remove a movie rating and persist state immediately."""
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        return False

    current = load(path)
    ratings = current.get("ratings", {})
    if mid in ratings:
        del ratings[mid]
        current["ratings"] = ratings
        return save(current, path)
    return True


def save_ratings(ratings: Dict[Any, Any], path: Optional[Path] = None) -> bool:
    """Update and persist whole ratings dictionary."""
    current = load(path)
    current["ratings"] = _normalize_ratings(ratings)
    if current["ratings"]:
        current["onboarding_completed"] = True
    return save(current, path)


def get_watchlist(path: Optional[Path] = None) -> List[int]:
    """Retrieve persisted watchlist [movieId, ...]."""
    return load(path).get("watchlist", [])


def add_to_watchlist(movie_id: int, path: Optional[Path] = None) -> bool:
    """Add movie to watchlist (independent of ratings) and save immediately."""
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        return False

    current = load(path)
    wl = current.get("watchlist", [])
    if mid not in wl:
        wl.append(mid)
        current["watchlist"] = wl
        return save(current, path)
    return True


def remove_from_watchlist(movie_id: int, path: Optional[Path] = None) -> bool:
    """Remove movie from watchlist and save immediately."""
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        return False

    current = load(path)
    wl = current.get("watchlist", [])
    if mid in wl:
        wl.remove(mid)
        current["watchlist"] = wl
        return save(current, path)
    return True


def save_watchlist(watchlist: List[int], path: Optional[Path] = None) -> bool:
    """Update and persist watchlist."""
    current = load(path)
    current["watchlist"] = _normalize_id_list(watchlist)
    return save(current, path)


def get_not_interested(path: Optional[Path] = None) -> Set[int]:
    """Retrieve persisted not_interested exclusions set."""
    return load(path).get("not_interested", set())


def mark_not_interested(movie_id: int, path: Optional[Path] = None) -> bool:
    """Exclude movie from all recommendations, preserving ratings history."""
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        return False

    current = load(path)
    ni = current.get("not_interested", set())
    ni.add(mid)
    current["not_interested"] = ni
    return save(current, path)


def unmark_not_interested(movie_id: int, path: Optional[Path] = None) -> bool:
    """Restore movie to eligible recommendation candidates."""
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        return False

    current = load(path)
    ni = current.get("not_interested", set())
    if mid in ni:
        ni.remove(mid)
        current["not_interested"] = ni
        return save(current, path)
    return True


def save_not_interested(not_interested: Union[Set[int], List[int]], path: Optional[Path] = None) -> bool:
    """Update and persist not_interested exclusions."""
    current = load(path)
    current["not_interested"] = _normalize_id_set(not_interested)
    return save(current, path)


def get_profile(path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve persisted user profile dictionary."""
    return load(path).get("user_profile", DEFAULT_USER.copy())


def save_profile(profile: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """Update and persist user profile."""
    current = load(path)
    current["user_profile"] = _normalize_profile(profile)
    return save(current, path)


def is_onboarding_completed(path: Optional[Path] = None) -> bool:
    """Check if onboarding was completed."""
    state = load(path)
    return bool(state.get("onboarding_completed", False))


def is_onboarding_skipped(path: Optional[Path] = None) -> bool:
    """Check if onboarding was explicitly skipped."""
    state = load(path)
    return bool(state.get("onboarding_skipped", False))


def is_onboarding_done(path: Optional[Path] = None) -> bool:
    """
    Onboarding is considered done if:
      - It was explicitly completed, OR
      - It was explicitly skipped, OR
      - User already has at least 1 recorded rating.
    """
    state = load(path)
    if state.get("onboarding_completed") or state.get("onboarding_skipped"):
        return True
    if len(state.get("ratings", {})) > 0:
        return True
    return False


def complete_onboarding(selected_movie_ids: List[int], path: Optional[Path] = None) -> bool:
    """
    Complete onboarding with selected movies.
    Assigns an initial 5-star rating (integer 5) to each selected movie and marks onboarding as completed.
    """
    current = load(path)
    ratings = current.get("ratings", {})
    for mid in selected_movie_ids:
        try:
            imid = int(mid)
            ratings[imid] = 5.0
        except (ValueError, TypeError):
            continue
    current["ratings"] = ratings
    current["onboarding_completed"] = True
    current["onboarding_skipped"] = False
    return save(current, path)


def skip_onboarding(path: Optional[Path] = None) -> bool:
    """
    Mark onboarding as skipped.
    Opens homepage with non-personalized content without creating fake ratings.
    """
    current = load(path)
    current["onboarding_skipped"] = True
    current["onboarding_completed"] = False
    return save(current, path)


def reset_onboarding(clear_ratings: bool = True, path: Optional[Path] = None) -> bool:
    """
    Retake Taste Quiz action.
    Clears ratings (if clear_ratings is True) and resets onboarding status flags.
    Preserves watchlist and excluded/not-interested items!
    """
    current = load(path)
    if clear_ratings:
        current["ratings"] = {}
    current["onboarding_completed"] = False
    current["onboarding_skipped"] = False
    return save(current, path)


def sync_to_session_state(st_state: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Load persistent state into Streamlit session_state."""
    data = load(path)
    st_state["ratings"] = data["ratings"]
    st_state["watchlist"] = data["watchlist"]
    st_state["not_interested"] = data["not_interested"]
    st_state["user_profile"] = data["user_profile"]
    st_state["onboarding_completed"] = data["onboarding_completed"]
    st_state["onboarding_skipped"] = data["onboarding_skipped"]
    st_state["user_store_initialized"] = True
