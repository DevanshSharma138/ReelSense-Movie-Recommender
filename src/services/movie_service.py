from functools import lru_cache
from src.services.catalog import get_catalog, get_by_id, search_movies

_attempted_tmdb_enrichment = set()


class MovieService:
    @staticmethod
    def get_all_movies():
        return get_catalog()

    @staticmethod
    def search_movies(query="", limit=None):
        return list(search_movies(query=query, limit=limit))

    @staticmethod
    def get_movie_by_id(movie_id):
        try:
            m = get_by_id().get(int(movie_id))
        except (ValueError, TypeError):
            return None

        if m and ("data:image/svg" in m.get("poster_url", "") or not m.get("backdrop_url")):
            m_id = m["id"]
            try:
                from src.services.tmdb_service import get_tmdb_service
                from src.utils.metadata_validator import resolve_movie_images
                svc = get_tmdb_service()
                cached = svc.get_cached_metadata(m_id)
                if not cached and svc.is_available() and m_id not in _attempted_tmdb_enrichment:
                    _attempted_tmdb_enrichment.add(m_id)
                    res = svc.enrich_movie(m_id, m["title"], m.get("release_year"))
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
    @lru_cache(maxsize=1)
    def get_all_genres():
        genres = set()
        for m in get_catalog():
            genres.update(m.get("genres", []))
        return sorted(genres)

    @staticmethod
    @lru_cache(maxsize=1)
    def get_all_languages():
        return sorted(set(m.get("language", "English") for m in get_catalog()))

    @staticmethod
    def filter_movies(query="", selected_genres=None, year_range=(1930, 2026),
                      min_rating=0.0, language="All", sort_by="Rating (High to Low)"):
        catalog = get_catalog()
        has_query = bool(query and str(query).strip())
        has_genres = bool(selected_genres)
        has_year = bool(year_range and (year_range[0] > 1930 or year_range[1] < 2026))
        has_rating = bool(min_rating and min_rating > 0.0)
        has_lang = bool(language and language != "All")

        if not (has_query or has_genres or has_year or has_rating or has_lang):
            results = list(catalog)
        else:
            q = str(query).lower().strip() if has_query else ""
            genre_set = set(selected_genres) if has_genres else None
            y_min, y_max = year_range if has_year else (0, 3000)

            results = []
            for m in catalog:
                if has_rating and m.get("rating", 0) < min_rating:
                    continue
                if has_year:
                    ry = m.get("release_year", 2000)
                    if ry < y_min or ry > y_max:
                        continue
                if has_lang and m.get("language") != language:
                    continue
                if has_genres and not genre_set.intersection(m.get("genres", ())):
                    continue
                if has_query:
                    search_blob = m.get("_search_blob")
                    if search_blob is not None:
                        if q not in search_blob:
                            continue
                    else:
                        if not (q in m["title"].lower() or q in m["overview"].lower()
                                or q in m.get("director", "").lower()
                                or any(q in str(a).lower() for a in m.get("cast", []))
                                or any(q in str(g).lower() for g in m.get("genres", []))):
                            continue
                results.append(m)

        if sort_by == "Rating (High to Low)":
            results.sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif sort_by == "Release Year (Newest First)":
            results.sort(key=lambda x: x.get("release_year", 0), reverse=True)
        elif sort_by == "Release Year (Oldest First)":
            results.sort(key=lambda x: x.get("release_year", 0))
        elif sort_by == "Title (A-Z)":
            results.sort(key=lambda x: x.get("title", ""))
        return results
