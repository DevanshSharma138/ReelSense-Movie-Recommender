"""
ReelSense - Movie Data & Search Service
Phase 3: reads the real MovieLens-based catalog instead of SAMPLE_MOVIES.
"""
from src.services.catalog import get_catalog, get_by_id, search_movies


class MovieService:
    @staticmethod
    def get_all_movies():
        return get_catalog()

    @staticmethod
    def search_movies(query="", limit=None):
        return search_movies(query=query, limit=limit)

    @staticmethod
    def get_movie_by_id(movie_id):
        try:
            m = get_by_id().get(int(movie_id))
        except (ValueError, TypeError):
            return None

        if m and ("data:image/svg" in m.get("poster_url", "") or not m.get("backdrop_url")):
            try:
                from src.services.tmdb_service import get_tmdb_service
                from src.utils.metadata_validator import resolve_movie_images
                svc = get_tmdb_service()
                if svc.is_available():
                    cached = svc.get_cached_metadata(m["id"])
                    if not cached:
                        res = svc.enrich_movie(m["id"], m["title"], m.get("release_year"))
                        cached = res.get("metadata")
                    if cached:
                        poster, backdrop, _ = resolve_movie_images(
                            m["title"],
                            m.get("release_year"),
                            m["genres"][0] if m.get("genres") else "Cinema",
                            tmdb_meta=cached,
                            expected_tmdb_id=cached.get("tmdb_id"),
                        )
                        m["poster_url"] = poster
                        m["backdrop_url"] = backdrop
                        if cached.get("overview"):
                            m["overview"] = cached["overview"]
                        if cached.get("runtime"):
                            m["runtime"] = f"{cached['runtime']} MIN"
                        if cached.get("director"):
                            m["director"] = cached["director"]
                        if cached.get("cast"):
                            m["cast"] = cached["cast"]
                        if cached.get("language"):
                            m["language"] = cached["language"]
            except Exception:
                pass
        return m

    @staticmethod
    def get_all_genres():
        genres = set()
        for m in get_catalog():
            genres.update(m.get("genres", []))
        return sorted(genres)

    @staticmethod
    def get_all_languages():
        return sorted(set(m.get("language", "English") for m in get_catalog()))

    @staticmethod
    def filter_movies(query="", selected_genres=None, year_range=(1930, 2026),
                      min_rating=0.0, language="All", sort_by="Rating (High to Low)"):
        results = list(get_catalog())

        if query:
            q = query.lower().strip()
            results = [
                m for m in results
                if q in m["title"].lower() or q in m["overview"].lower()
                or q in m.get("director", "").lower()
                or any(q in a.lower() for a in m.get("cast", []))
                or any(q in g.lower() for g in m.get("genres", []))
            ]
        if selected_genres:
            results = [m for m in results if any(g in m["genres"] for g in selected_genres)]
        if year_range:
            results = [m for m in results if year_range[0] <= m.get("release_year", 2000) <= year_range[1]]
        if min_rating > 0:
            results = [m for m in results if m.get("rating", 0) >= min_rating]
        if language and language != "All":
            results = [m for m in results if m.get("language") == language]

        if sort_by == "Rating (High to Low)":
            results.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_by == "Release Year (Newest First)":
            results.sort(key=lambda x: x.get("release_year", 0), reverse=True)
        elif sort_by == "Release Year (Oldest First)":
            results.sort(key=lambda x: x.get("release_year", 0))
        elif sort_by == "Title (A-Z)":
            results.sort(key=lambda x: x.get("title", ""))
        return results
