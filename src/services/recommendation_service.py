from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.services.catalog import get_catalog, get_by_id
from src.services.hybrid_model import get_model


_user_recs_cache = {}


class RecommendationService:
    @staticmethod
    def get_recommended_for_user(user_preferences=None, limit=12, exclude=None):
        """
        user_preferences (all optional):
          ratings:         {movieId: stars}   <- drives the hybrid/content model
          watchlist:       list[int]          <- positive preference & excluded from recs
          favorite_genres: list[str]          <- optional genre filter
          hidden_ids:      list[int]          <- 'Not interested' movies to exclude
        exclude: optional iterable of movie IDs to strictly exclude (along with hidden & rated)
        """
        p = user_preferences or {}
        raw_ratings = p.get("ratings") or {}
        if any(float(v) > 5.0 for v in raw_ratings.values()):
            ratings = {int(k): float(v) / 2.0 for k, v in raw_ratings.items()}
        else:
            ratings = {int(k): float(v) for k, v in raw_ratings.items()}

        raw_wl = p.get("watchlist") or ()
        watchlist = tuple(int(x) for x in raw_wl)

        raw_hidden = p.get("hidden_ids") or ()
        all_excluded = set(int(x) for x in raw_hidden)
        if exclude:
            all_excluded.update(int(x) for x in exclude)
        hidden_ids = tuple(sorted(all_excluded))

        fav_genres = tuple(p.get("favorite_genres") or ())

        # Targeted cache key based directly on user preference state
        cache_key = (
            tuple(sorted(ratings.items())),
            tuple(sorted(watchlist)),
            hidden_ids,
            fav_genres,
            int(limit),
        )
        if cache_key in _user_recs_cache:
            return [dict(m) for m in _user_recs_cache[cache_key]]

        items, _mode = get_model().recommend(
            ratings=ratings,
            n=limit,
            genres=list(fav_genres) if fav_genres else None,
            exclude=hidden_ids,
            watchlist=watchlist,
        )

        # Guarantee no duplicates and strict exclusion of rated/hidden
        banned = set(ratings.keys()) | set(hidden_ids)
        deduped = []
        seen = set()
        for m in items:
            mid = m["id"]
            if mid not in banned and mid not in seen:
                seen.add(mid)
                deduped.append(m)

        _user_recs_cache[cache_key] = deduped
        return [dict(m) for m in deduped]

    @staticmethod
    def get_onboarding_picks(n=24) -> List[Dict[str, Any]]:
        """
        Selects ~24 diverse, recognizable, high-popularity films drawn from the actual catalog,
        balanced across major cinematic genres with available posters.
        """
        cat = get_catalog()
        genre_order = [
            "Drama", "Sci-Fi", "Action", "Comedy", "Crime",
            "Animation", "Thriller", "Adventure", "Romance", "Mystery"
        ]
        selected = []
        selected_ids = set()

        by_genre = {g: [] for g in genre_order}
        for m in sorted(cat, key=lambda x: (-(x.get("n_ratings") or 0), -x.get("popularity", 0))):
            for g in m.get("genres", []):
                if g in by_genre:
                    by_genre[g].append(m)

        # Round-robin selection across genre priorities
        for _ in range(6):
            for g in genre_order:
                for candidate in by_genre[g]:
                    if candidate["id"] not in selected_ids and len(selected) < n:
                        selected.append(dict(candidate))
                        selected_ids.add(candidate["id"])
                        break
            if len(selected) >= n:
                break

        # Refill to n if needed
        if len(selected) < n:
            for m in sorted(cat, key=lambda x: -x.get("popularity", 0)):
                if m["id"] not in selected_ids:
                    selected.append(dict(m))
                    selected_ids.add(m["id"])
                    if len(selected) >= n:
                        break

        return selected[:n]

    @staticmethod
    def get_because_you_liked(movie_id: int, limit: int = 6, exclude: Any = ()) -> List[Dict[str, Any]]:
        """
        Returns up to `limit` movies similar to `movie_id` using content and collaborative similarity,
        strictly excluding movies in `exclude` (rated, hidden, and already displayed IDs).
        """
        model = get_model()
        banned = set(int(x) for x in (exclude or ()))
        banned.add(int(movie_id))

        target_movie = get_by_id().get(int(movie_id))
        target_title = target_movie["title"] if target_movie else f"Movie #{movie_id}"
        target_genres = set(target_movie.get("genres", [])) if target_movie else set()

        candidates = model.similar(int(movie_id), limit=limit + len(banned) + 10)
        results = []
        seen = set()

        for cand in candidates:
            mid = cand["id"]
            if mid not in banned and mid not in seen:
                shared = target_genres & set(cand.get("genres", []))
                m_copy = dict(cand)
                m_copy["why_recommended"] = [
                    f"Because you liked '{target_title}'",
                    f"Shared genres: {', '.join(sorted(shared))}" if shared else "Similar critical acclaim and aesthetic pacing"
                ]
                seen.add(mid)
                results.append(m_copy)
                if len(results) >= limit:
                    break

        # Refill if fewer than limit
        if len(results) < limit:
            cat = get_catalog()
            for cand in cat:
                mid = cand["id"]
                if mid not in banned and mid not in seen and (target_genres & set(cand.get("genres", []))):
                    shared = target_genres & set(cand.get("genres", []))
                    m_copy = dict(cand)
                    m_copy["vector_match"] = 85
                    m_copy["why_recommended"] = [
                        f"Because you liked '{target_title}'",
                        f"Shared genres: {', '.join(sorted(shared))}"
                    ]
                    seen.add(mid)
                    results.append(m_copy)
                    if len(results) >= limit:
                        break

        return results[:limit]

    @staticmethod
    def get_top_genre_picks(ratings=None, limit=6, exclude=()) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Determines user's most-liked genre based on ratings:
          Weighted score for genre = sum(rating) for movies rated >= 3.0 containing genre.
        Returns (top_genre_name, list_of_movies).
        If no positive ratings exist, returns (None, general_curated_movies).
        """
        r = ratings or {}
        cat_by_id = get_by_id()
        genre_scores = {}

        for raw_mid, raw_score in r.items():
            score = float(raw_score)
            if score >= 3.0:
                movie = cat_by_id.get(int(raw_mid))
                if movie:
                    for g in movie.get("genres", []):
                        genre_scores[g] = genre_scores.get(g, 0.0) + score

        banned = set(int(x) for x in (exclude or ())) | set(int(k) for k in r.keys())

        if genre_scores:
            top_genre = max(genre_scores.items(), key=lambda x: x[1])[0]
            rec_prefs = {
                "ratings": r,
                "favorite_genres": [top_genre],
                "hidden_ids": list(banned),
            }
            recs = RecommendationService.get_recommended_for_user(rec_prefs, limit=limit + 6, exclude=banned)
            valid_recs = [m for m in recs if top_genre in m.get("genres", []) and m["id"] not in banned]

            if len(valid_recs) < limit:
                cat = get_catalog()
                existing_ids = set(m["id"] for m in valid_recs)
                for cand in cat:
                    mid = cand["id"]
                    if mid not in banned and mid not in existing_ids and top_genre in cand.get("genres", []):
                        m_copy = dict(cand)
                        m_copy["vector_match"] = 88
                        m_copy["why_recommended"] = [f"Curated title in your favorite genre '{top_genre}'"]
                        valid_recs.append(m_copy)
                        existing_ids.add(mid)
                        if len(valid_recs) >= limit:
                            break

            return top_genre, valid_recs[:limit]
        else:
            # Fallback when no rating preference exists
            rec_prefs = {"ratings": {}, "hidden_ids": list(banned)}
            recs = RecommendationService.get_recommended_for_user(rec_prefs, limit=limit, exclude=banned)
            return None, recs[:limit]

    @staticmethod
    def get_user_recommendation_diagnostics(user_preferences=None):
        """Telemetry on user taste profile & recommendation strategy."""
        p = user_preferences or {}
        raw_ratings = p.get("ratings") or {}
        if any(float(v) > 5.0 for v in raw_ratings.values()):
            ratings = {int(k): float(v) / 2.0 for k, v in raw_ratings.items()}
        else:
            ratings = {int(k): float(v) for k, v in raw_ratings.items()}
        watchlist = p.get("watchlist") or ()
        hidden_ids = p.get("hidden_ids") or ()

        n_pos = sum(1 for v in ratings.values() if v >= 3.5)
        n_neg = sum(1 for v in ratings.values() if v < 3.0)
        n_neu = sum(1 for v in ratings.values() if 3.0 <= v < 3.5)

        if len(ratings) >= 3:
            strategy = "hybrid_personalized"
        elif len(ratings) > 0 or len(watchlist) > 0:
            strategy = "content_personalized"
        else:
            strategy = "cold_start_generic"

        recs = RecommendationService.get_recommended_for_user(user_preferences, limit=6)

        return {
            "n_ratings": len(ratings),
            "ratings_count": len(ratings),
            "n_positive": n_pos,
            "positive_count": n_pos,
            "n_negative": n_neg,
            "negative_count": n_neg,
            "n_neutral": n_neu,
            "n_watchlist": len(watchlist),
            "watchlist_count": len(watchlist),
            "n_excluded": len(hidden_ids),
            "has_taste_profile": (len(ratings) > 0 or len(watchlist) > 0),
            "strategy": strategy,
            "mode": RecommendationService.get_recommendation_mode(user_preferences),
            "recommendations_count": len(recs),
            "top_movie_ids": [m["id"] for m in recs[:3]],
            "top_titles": [m["title"] for m in recs[:3]],
            "top_scores": [m.get("similarity") for m in recs[:3]],
        }

    @staticmethod
    def get_recommendation_mode(user_preferences=None):
        """'hybrid' or 'cold_start'."""
        n = len((user_preferences or {}).get("ratings") or {})
        return "hybrid" if n >= 3 else "cold_start"

    @staticmethod
    def get_trending_movies(limit=6, exclude=None):
        """Return trending movies excluding rated/hidden/displayed IDs."""
        banned = set(int(x) for x in (exclude or ()))
        t = [dict(m) for m in get_catalog() if m["is_trending"] and m["id"] not in banned]
        t.sort(key=lambda x: (x["trending_rank"] or 99, -x["rating"]))
        if len(t) < limit:
            # Refill with catalog top popularity
            for m in get_catalog():
                if m["id"] not in banned and m["id"] not in [x["id"] for x in t]:
                    t.append(dict(m))
                    if len(t) >= limit:
                        break
        return t[:limit]

    @staticmethod
    @lru_cache(maxsize=1)
    def get_movies_by_rank():
        r = [dict(m) for m in get_catalog() if m["trending_rank"] is not None]
        r.sort(key=lambda x: x["trending_rank"])
        return r[:5]

    @staticmethod
    @lru_cache(maxsize=16)
    def get_hidden_gems(limit=6):
        g = [dict(m) for m in get_catalog() if m["is_hidden_gem"]]
        g.sort(key=lambda x: -x["rating"])
        return g[:limit]

    @staticmethod
    def get_movies_by_mood(mood_id, limit=8, exclude=None):
        banned = set(int(x) for x in (exclude or ()))
        m = [dict(x) for x in get_catalog() if mood_id in x["moods"] and x["id"] not in banned]
        m.sort(key=lambda x: -x["popularity"])
        if len(m) < limit:
            for x in get_catalog():
                if x["id"] not in banned and x["id"] not in [item["id"] for item in m]:
                    m.append(dict(x))
                    if len(m) >= limit:
                        break
        return m[:limit]

    @staticmethod
    def search_by_prompt(prompt, limit=6):
        if not prompt or not prompt.strip():
            return RecommendationService.get_trending_movies(limit)
        return get_model().query(prompt, limit) or RecommendationService.get_trending_movies(limit)

    @staticmethod
    def get_similar_movies(movie, limit=6):
        if not movie:
            return RecommendationService.get_trending_movies(limit)
        return get_model().similar(movie.get("id"), limit)

    @staticmethod
    def get_recommendation_explanation(movie, user_ratings=None):
        if not movie:
            return []
        if movie.get("why_recommended"):
            return movie["why_recommended"]

        reasons = []
        ratings = user_ratings or {}
        cat_by_id = get_by_id()

        if ratings:
            high_rated_ids = [int(k) for k, v in ratings.items() if float(v) >= 3.5]
            shared_found = False
            for hid in high_rated_ids:
                hm = cat_by_id.get(hid)
                if hm and hm["id"] != movie.get("id"):
                    shared = set(movie.get("genres", [])) & set(hm.get("genres", []))
                    if shared:
                        reasons.append(f"Because you rated '{hm['title']}' highly (Shared genres: {', '.join(sorted(shared))})")
                        shared_found = True
                        break
            if not shared_found and high_rated_ids:
                hm = cat_by_id.get(high_rated_ids[0])
                if hm:
                    reasons.append(f"Calibrated with your preference for '{hm['title']}'")

        if movie.get("is_trending") and movie.get("trending_rank"):
            reasons.append(f"Trending #{movie['trending_rank']} among active community viewers")
        elif movie.get("is_hidden_gem"):
            reasons.append("Curator Hidden Gem with exceptional review scores")

        if movie.get("n_ratings", 0) > 0:
            reasons.append(f"Rated ⭐ {movie.get('rating', 0)/2:.1f}/5 across {movie.get('n_ratings')} viewers")
        elif movie.get("genres"):
            reasons.append(f"Strong genre affinity in {', '.join(movie['genres'][:2])}")

        return reasons or ["Curated title from the MovieLens master library"]

    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_mood_counts():
        cat = get_catalog()
        counts = {}
        for m in cat:
            for mood in m.get("moods", []):
                counts[mood] = counts.get(mood, 0) + 1
        return counts

    @staticmethod
    def get_mood_count(mood_id):
        return RecommendationService.get_all_mood_counts().get(mood_id, 0)

    @staticmethod
    def get_recommendation_breakdown(movie, user_ratings=None):
        from src.services.taste_service import TasteService
        return TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)
