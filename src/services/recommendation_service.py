"""
ReelSense - Recommendation Engine Service (Phase 3: hybrid)
Same public methods as before. get_recommended_for_user now takes real ratings.
"""
from src.services.catalog import get_catalog
from src.services.hybrid_model import get_model


class RecommendationService:
    @staticmethod
    def get_recommended_for_user(user_preferences=None, limit=6):
        """
        user_preferences (all optional):
          ratings:         {movieId: stars}   <- drives the hybrid model
          favorite_genres: list[str]          <- optional genre filter
          hidden_ids:      list[int]          <- 'Not interested' movies to exclude
        Under 3 ratings -> trending/genre cold-start fallback.
        """
        p = user_preferences or {}
        raw_ratings = p.get("ratings") or {}
        if any(float(v) > 5.0 for v in raw_ratings.values()):
            ratings = {int(k): float(v) / 2.0 for k, v in raw_ratings.items()}
        else:
            ratings = {int(k): float(v) for k, v in raw_ratings.items()}

        items, _mode = get_model().recommend(ratings, n=limit,
                                             genres=p.get("favorite_genres"),
                                             exclude=p.get("hidden_ids") or ())
        return items

    @staticmethod
    def get_recommendation_mode(user_preferences=None):
        """'hybrid' or 'cold_start' - use for the 'Trending fallback active' badge."""
        n = len((user_preferences or {}).get("ratings") or {})
        return "hybrid" if n >= 3 else "cold_start"

    @staticmethod
    def get_trending_movies(limit=6):
        t = [dict(m) for m in get_catalog() if m["is_trending"]]
        t.sort(key=lambda x: (x["trending_rank"] or 99, -x["rating"]))
        return t[:limit]

    @staticmethod
    def get_movies_by_rank():
        r = [dict(m) for m in get_catalog() if m["trending_rank"] is not None]
        r.sort(key=lambda x: x["trending_rank"])
        return r[:5]

    @staticmethod
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
    def get_recommendation_explanation(movie):
        if not movie:
            return []
        return movie.get("why_recommended") or [f"Rated {movie.get('rating', 0)}/10 by {movie.get('n_ratings', 0)} viewers"]
