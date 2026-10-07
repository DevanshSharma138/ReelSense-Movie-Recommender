"""
ReelSense - User State Persistence Service (Phase 2)
Provides safe, atomic JSON persistence for:
  - user ratings ({movieId: rating})
  - user watchlist ([movieId, ...])
  - not_interested exclusions (set/list of movieId)
  - user curator profile preferences (dict)
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

# Primary storage path: data/user_data.json
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_STORE_PATH = DATA_DIR / "user_data.json"


def get_default_state() -> Dict[str, Any]:
    """Return a clean, uncorrupted default user state."""
    return {
        "ratings": {},
        "watchlist": [],
        "not_interested": set(),
        "user_profile": DEFAULT_USER.copy(),
    }


def _normalize_id_list(items: Optional[List[Any]]) -> List[int]:
    """Deduplicate and convert items to valid integer MovieLens IDs preserving order."""
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
    """Convert items to a set of valid integer MovieLens IDs."""
    result = set()
    for x in items or []:
        try:
            result.add(int(x))
        except (ValueError, TypeError):
            continue
    return result


def _normalize_ratings(ratings: Optional[Dict[Any, Any]]) -> Dict[int, float]:
    """
    Normalize ratings dictionary ensuring integer keys and float values.
    Implements safe, deterministic migration from old 0-10 scale to 0-5 scale:
    Values > 5.0 are divided by 2.0 and bounded to [0.0, 5.0].
    """
    result = {}
    for k, v in (ratings or {}).items():
        try:
            mid = int(k)
            val = float(v)
            if val > 5.0:
                val = round(val / 2.0, 2)
            val = max(0.0, min(5.0, val))
            result[mid] = val
        except (ValueError, TypeError):
            continue
    return result


def _normalize_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge profile with DEFAULT_USER to guarantee all expected fields exist, migrating 0-10 preferences."""
    base = DEFAULT_USER.copy()
    if isinstance(profile, dict):
        base.update({k: v for k, v in profile.items() if k in base and v is not None})
    if base.get("min_rating_pref", 0) > 5.0:
        base["min_rating_pref"] = round(base["min_rating_pref"] / 2.0, 1)
    return base


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely load user state from JSON file.
    Falls back to clean default state if file is missing, empty, or malformed.
    """
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    if not target_path.exists():
        return get_default_state()

    try:
        text = target_path.read_text(encoding="utf-8").strip()
        if not text:
            return get_default_state()

        raw = json.loads(text)
        if not isinstance(raw, dict):
            return get_default_state()

        return {
            "ratings": _normalize_ratings(raw.get("ratings")),
            "watchlist": _normalize_id_list(raw.get("watchlist")),
            "not_interested": _normalize_id_set(raw.get("not_interested")),
            "user_profile": _normalize_profile(raw.get("user_profile")),
        }
    except Exception as e:
        logger.warning(f"Error loading user store from {target_path}: {e}. Falling back to defaults.")
        return get_default_state()


def save(data: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """
    Atomically save user state to JSON file.
    Uses write-temp-file -> os.replace with retries and direct write fallback
    to prevent partial/corrupt writes and Windows WinError 32 file-locking issues.
    """
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    serialized = {
        "ratings": {str(k): float(v) for k, v in _normalize_ratings(data.get("ratings")).items()},
        "watchlist": _normalize_id_list(data.get("watchlist")),
        "not_interested": sorted(list(_normalize_id_set(data.get("not_interested")))),
        "user_profile": _normalize_profile(data.get("user_profile")),
    }

    temp_path = None
    try:
        # Atomic write: create temp file in the same directory, flush, close, then replace
        with tempfile.NamedTemporaryFile("w", dir=target_path.parent, delete=False, encoding="utf-8") as f:
            temp_path = Path(f.name)
            json.dump(serialized, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # Attempt atomic replace with retries to withstand transient Windows file locks
        replaced = False
        for attempt in range(5):
            try:
                os.replace(temp_path, target_path)
                replaced = True
                break
            except (PermissionError, OSError):
                time.sleep(0.05 * (attempt + 1))

        if not replaced:
            # Fallback: direct write if os.replace is blocked by Windows file watchers
            with open(target_path, "w", encoding="utf-8") as dst:
                json.dump(serialized, dst, indent=2, ensure_ascii=False)
            try:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass

        return True
    except Exception as e:
        logger.error(f"Error saving user store to {target_path}: {e}")
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        return False


# ---------------------------------------------------------
# Granular Helper Getters / Savers
# ---------------------------------------------------------

def get_ratings(path: Optional[Path] = None) -> Dict[int, float]:
    """Retrieve persisted ratings {movieId: rating}."""
    return load(path).get("ratings", {})


def save_ratings(ratings: Dict[int, float], path: Optional[Path] = None) -> bool:
    """Update and persist ratings, preserving other user state."""
    current = load(path)
    current["ratings"] = ratings
    return save(current, path)


def get_watchlist(path: Optional[Path] = None) -> List[int]:
    """Retrieve persisted watchlist [movieId, ...]."""
    return load(path).get("watchlist", [])


def save_watchlist(watchlist: List[int], path: Optional[Path] = None) -> bool:
    """Update and persist watchlist, preserving other user state."""
    current = load(path)
    current["watchlist"] = watchlist
    return save(current, path)


def get_not_interested(path: Optional[Path] = None) -> Set[int]:
    """Retrieve persisted not_interested exclusions set(movieId, ...)."""
    return load(path).get("not_interested", set())


def save_not_interested(not_interested: Union[Set[int], List[int]], path: Optional[Path] = None) -> bool:
    """Update and persist not_interested exclusions, preserving other user state."""
    current = load(path)
    current["not_interested"] = not_interested
    return save(current, path)


def get_profile(path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve persisted user profile dictionary."""
    return load(path).get("user_profile", DEFAULT_USER.copy())


def save_profile(profile: Dict[str, Any], path: Optional[Path] = None) -> bool:
    """Update and persist user profile, preserving other user state."""
    current = load(path)
    current["user_profile"] = profile
    return save(current, path)


def migrate_to_5_point_scale(path: Optional[Path] = None) -> bool:
    """Safely migrate any stored ratings to the 0.0-5.0 scale."""
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    if not target_path.exists():
        return False
    current = load(target_path)
    return save(current, target_path)
