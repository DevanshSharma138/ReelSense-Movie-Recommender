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
    def get_recommendation_explanation(movie, user_ratings=None):
        if not movie:
            return []
        if movie.get("why_recommended"):
            return movie["why_recommended"]

        # Build dynamic signals from real data
        reasons = []
        ratings = user_ratings or {}
        cat_by_id = {m["id"]: m for m in get_catalog()}

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
    def get_mood_count(mood_id):
        return sum(1 for m in get_catalog() if mood_id in m.get("moods", []))

    @staticmethod
    def get_all_mood_counts():
        cat = get_catalog()
        counts = {}
        for m in cat:
            for mood in m.get("moods", []):
                counts[mood] = counts.get(mood, 0) + 1
        return counts
