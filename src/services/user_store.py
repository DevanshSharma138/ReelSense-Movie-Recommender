"""
ReelSense - User State Persistence Bridge (Phase 2)
Maintains full backward compatibility with user_store while delegating
to the robust user_state service and respecting DEFAULT_STORE_PATH monkeypatching in tests.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.services import user_state

DATA_DIR = user_state.DATA_DIR
DEFAULT_STORE_PATH = user_state.USER_STATE_PATH


def get_default_state() -> Dict[str, Any]:
    return user_state.get_default_state()


def load(path: Optional[Path] = None) -> Dict[str, Any]:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.load(target_path)


def save(data: Dict[str, Any], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.save(data, target_path)


def get_ratings(path: Optional[Path] = None) -> Dict[int, float]:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.get_ratings(target_path)


def save_ratings(ratings: Dict[Any, Any], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.save_ratings(ratings, target_path)


def rate_movie(movie_id: int, rating: Union[int, float], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.rate_movie(movie_id, rating, target_path)


def like_movie(movie_id: int, path: Optional[Path] = None) -> bool:
    """Convenience helper to record a positive Like reaction (5.0 rating)."""
    return rate_movie(movie_id, 5.0, path)


def dislike_movie(movie_id: int, path: Optional[Path] = None) -> bool:
    """Convenience helper to record a negative Dislike reaction (1.0 rating)."""
    return rate_movie(movie_id, 1.0, path)


def remove_rating(movie_id: int, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.remove_rating(movie_id, target_path)


def get_watchlist(path: Optional[Path] = None) -> List[int]:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.get_watchlist(target_path)


def save_watchlist(watchlist: List[int], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.save_watchlist(watchlist, target_path)


def add_to_watchlist(movie_id: int, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.add_to_watchlist(movie_id, target_path)


def remove_from_watchlist(movie_id: int, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.remove_from_watchlist(movie_id, target_path)


def get_not_interested(path: Optional[Path] = None) -> Set[int]:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.get_not_interested(target_path)


def save_not_interested(not_interested: Union[Set[int], List[int]], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.save_not_interested(not_interested, target_path)


def mark_not_interested(movie_id: int, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.mark_not_interested(movie_id, target_path)


def unmark_not_interested(movie_id: int, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.unmark_not_interested(movie_id, target_path)


def get_profile(path: Optional[Path] = None) -> Dict[str, Any]:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.get_profile(target_path)


def save_profile(profile: Dict[str, Any], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.save_profile(profile, target_path)


def is_onboarding_completed(path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.is_onboarding_completed(target_path)


def is_onboarding_skipped(path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.is_onboarding_skipped(target_path)


def is_onboarding_done(path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.is_onboarding_done(target_path)


def complete_onboarding(selected_movie_ids: List[int], path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.complete_onboarding(selected_movie_ids, target_path)


def skip_onboarding(path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.skip_onboarding(target_path)


def reset_onboarding(clear_ratings: bool = True, path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    return user_state.reset_onboarding(clear_ratings, target_path)


def migrate_to_5_point_scale(path: Optional[Path] = None) -> bool:
    target_path = Path(path) if path else DEFAULT_STORE_PATH
    current = load(target_path)
    return save(current, target_path)
