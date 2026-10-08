from functools import lru_cache
from src.services.catalog import get_catalog, get_by_id
from src.services.hybrid_model import get_model


_user_recs_cache = {}

class RecommendationService:
    @staticmethod
    def get_recommended_for_user(user_preferences=None, limit=6):
        """
        user_preferences (all optional):
          ratings:         {movieId: stars}   <- drives the hybrid/content model
          watchlist:       list[int]          <- positive preference & excluded from recs
          favorite_genres: list[str]          <- optional genre filter
          hidden_ids:      list[int]          <- 'Not interested' movies to exclude
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
        hidden_ids = tuple(int(x) for x in raw_hidden)

        fav_genres = tuple(p.get("favorite_genres") or ())

        # Targeted cache key based directly on user preference state
        cache_key = (
            tuple(sorted(ratings.items())),
            tuple(sorted(watchlist)),
            tuple(sorted(hidden_ids)),
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
        _user_recs_cache[cache_key] = items
        return [dict(m) for m in items]

    @staticmethod
    def get_user_recommendation_diagnostics(user_preferences=None):
        """Phase 11: Real-time telemetry on user taste profile & recommendation strategy."""
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
        """'hybrid' or 'cold_start' - use for the 'Trending fallback active' badge."""
        n = len((user_preferences or {}).get("ratings") or {})
        return "hybrid" if n >= 3 else "cold_start"

    @staticmethod
    @lru_cache(maxsize=16)
    def get_trending_movies(limit=6):
        t = [dict(m) for m in get_catalog() if m["is_trending"]]
        t.sort(key=lambda x: (x["trending_rank"] or 99, -x["rating"]))
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
    def get_movies_by_mood(mood_id, limit=8):
        m = [dict(x) for x in get_catalog() if mood_id in x["moods"]]
        m.sort(key=lambda x: -x["popularity"])
        return m[:limit] or [dict(x) for x in get_catalog()[:limit]]

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

        # Build dynamic signals from real data
        reasons = []
        ratings = user_ratings or {}
        cat_by_id = get_by_id()

        # 1. Real rating overlap signal
        if ratings:
            high_rated_ids = [int(k) for k, v in ratings.items() if float(v) >= 7.0]
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

        # 2. Trending or Gem signal
        if movie.get("is_trending") and movie.get("trending_rank"):
            reasons.append(f"Trending #{movie['trending_rank']} among active community viewers")
        elif movie.get("is_hidden_gem"):
            reasons.append("Curator Hidden Gem with exceptional review scores")

        # 3. Community rating signal
        if movie.get("n_ratings", 0) > 0:
            reasons.append(f"Rated ⭐ {movie.get('rating', 0)}/10 across {movie.get('n_ratings')} MovieLens viewers")
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
        """Phase 6: Returns comprehensive, mathematically grounded breakdown dictionary."""
        from src.services.taste_service import TasteService
        return TasteService.get_recommendation_breakdown(movie, user_ratings=user_ratings)

