"""
ReelSense - Unified Movie Catalog (Phase 3)
MovieLens (real movies, ratings) + optional TMDB metadata (posters, overview, cast)
-> list of dicts with the SAME fields the UI already uses.
"""
import json, re, urllib.parse
from functools import lru_cache
import numpy as np
import pandas as pd

from data.loader import load_movies, load_ratings, DATA_DIR
from src.utils.metadata_validator import resolve_movie_images, audit_catalog_integrity

CATALOG_SIZE = 2000                     # Expanded active catalog size (Phase 5.5)
META_FILE = DATA_DIR / "tmdb_metadata.json"
LINKS_FILE = DATA_DIR / "links.csv"
TMDB = "https://image.tmdb.org/t/p/"

GENRE_MOODS = {
    "Happy": {"Comedy", "Animation", "Children", "Musical", "Fantasy"},
    "Relaxed": {"Romance", "Documentary", "Animation", "Musical"},
    "Mind-blown": {"Sci-Fi", "Mystery", "Thriller"},
    "Thrilling": {"Action", "Thriller", "Adventure", "Crime"},
    "Adrenaline": {"Action", "Adventure", "War"},
    "Emotional": {"Drama", "Romance", "War"},
    "Romantic": {"Romance"},
    "Dark": {"Crime", "Horror", "Film-Noir", "Thriller", "War"},
    "Melancholic": {"Drama", "War"},
}


def _clean_title(t):
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t).strip()
    m = re.match(r"^(.*), (The|A|An)( \(.*\))?$", t)
    return f"{m.group(2)} {m.group(1)}" if m else t


def _placeholder(title, size="600x900"):
    return f"https://placehold.co/{size}/1c1b1e/f2ca50?text=" + urllib.parse.quote(title)


def _meta():
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}
    except (OSError, ValueError):
        return {}


def _links_map():
    if not LINKS_FILE.exists():
        return {}
    try:
        df = pd.read_csv(LINKS_FILE).dropna(subset=["tmdbId"])
        return dict(zip(df["movieId"].astype(int), df["tmdbId"].astype(int)))
    except Exception:
        return {}


def _tags():
    p = DATA_DIR / "tags.csv"
    if not p.exists():
        return {}
    t = pd.read_csv(p).dropna(subset=["tag"])
    return t.groupby("movieId").tag.apply(lambda s: " ".join(s.astype(str).str.lower())).to_dict()


@lru_cache(maxsize=1)
def get_catalog():
    movies = load_movies().set_index("movieId")
    ratings = load_ratings()
    stats = ratings.groupby("movieId").rating.agg(["mean", "count"])
    gm, m_min = stats["mean"].mean(), stats["count"].quantile(0.6)
    stats["bayes"] = (stats["count"] * stats["mean"] + m_min * gm) / (stats["count"] + m_min)

    cut = ratings.timestamp.max() - 365 * 24 * 3600
    recent = ratings[ratings.timestamp >= cut].groupby("movieId").size()
    ids = [i for i in stats["count"].nlargest(CATALOG_SIZE).index if i in movies.index]
    trend_ids = recent.reindex(ids).fillna(0).nlargest(10).index.tolist()
    median_cnt = stats.loc[ids, "count"].median()

    meta, tags, links_map, out = _meta(), _tags(), _links_map(), []
    for i in ids:
        row, st, md = movies.loc[i], stats.loc[i], meta.get(str(i), {})
        title = _clean_title(row.title)
        genres = [g for g in row.genres.split("|") if g]
        moods = [m for m, gs in GENRE_MOODS.items() if gs & set(genres)] or ["Emotional"]
        primary_genre = genres[0] if genres else "Cinema"
        rel_year = int(row.year) if pd.notna(row.year) else None
        expected_tmdb = links_map.get(int(i))

        # Verified 4-tier image hierarchy & metadata cross-validation
        poster, backdrop, audit = resolve_movie_images(
            movie_title=row.title,
            release_year=rel_year,
            genre=primary_genre,
            tmdb_meta=md if md else None,
            expected_tmdb_id=expected_tmdb,
        )

        # Overview and crew from TMDB only if cross-source validation passed
        if audit["is_valid"] and md:
            overview = md.get("overview") or f"A {', '.join(genres[:3]).lower() or 'feature'} film from {int(row.year) if pd.notna(row.year) else 'unknown year'}."
            runtime = f"{md['runtime']} MIN" if md.get("runtime") else "N/A"
            director = md.get("director", "")
            cast = md.get("cast", [])
            language = md.get("language", "English")
        else:
            overview = f"A {', '.join(genres[:3]).lower() or 'feature'} film from {int(row.year) if pd.notna(row.year) else 'unknown year'}."
            runtime = "N/A"
            director = ""
            cast = []
            language = "English"

        rank = trend_ids.index(i) + 1 if i in trend_ids else None
        out.append({
            "id": int(i), "title": title,
            "release_year": int(row.year) if pd.notna(row.year) else 0,
            "genres": genres,
            "rating": round(float(st["mean"]) * 2, 1),          # 0-10 scale like the UI
            "n_ratings": int(st["count"]),
            "popularity": float(st["bayes"]),
            "vector_match": 0,
            "overview": overview,
            "runtime": runtime,
            "director": director,
            "cast": cast,
            "language": language,
            "poster_url": poster, "backdrop_url": backdrop,
            "moods": moods,
            "tags": tags.get(i, ""),
            "is_trending": rank is not None,
            "is_hidden_gem": bool(st["mean"] >= 4.1 and st["count"] <= median_cnt),
            "is_recommended": False,
            "trending_rank": rank,
            "trending_growth": f"{int(recent.get(i, 0))} ratings this year" if rank else "",
            "why_recommended": [],
        })
    return out


def get_by_id():
    return {m["id"]: m for m in get_catalog()}
