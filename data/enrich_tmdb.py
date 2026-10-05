"""
ReelSense - one-time TMDB enrichment.
Adds real poster, backdrop, overview, runtime, director, cast, language to the catalog movies.
Needs data/links.csv (from ml-latest-small) and a free TMDB API key.

Run once from project root:
    set TMDB_API_KEY=your_key        (Windows PowerShell:  $env:TMDB_API_KEY="your_key")
    python data/enrich_tmdb.py
Resumable: rerun any time, it skips movies already saved.
"""
import json, os, sys, time
from pathlib import Path
import pandas as pd
import requests

DATA = Path(__file__).resolve().parent
OUT = DATA / "tmdb_metadata.json"
CATALOG_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 600   # keep same as catalog.py
KEY = os.environ.get("TMDB_API_KEY", "").strip()
LANG = {"en": "English", "ja": "Japanese", "ko": "Korean", "fr": "French", "it": "Italian",
        "es": "Spanish", "de": "German", "hi": "Hindi", "zh": "Chinese", "ru": "Russian",
        "sv": "Swedish", "da": "Danish", "pt": "Portuguese"}

if not KEY:
    sys.exit("Set TMDB_API_KEY first (free key: themoviedb.org > Settings > API).")
if not (DATA / "links.csv").exists():
    sys.exit("data/links.csv missing. Copy links.csv from the ml-latest-small folder into data/.")

ratings = pd.read_csv(DATA / "ratings.csv")
links = pd.read_csv(DATA / "links.csv").dropna(subset=["tmdbId"])
links["tmdbId"] = links.tmdbId.astype(int)
top = ratings.groupby("movieId").size().nlargest(CATALOG_SIZE).index
todo = links[links.movieId.isin(top)]

meta = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
headers, params = {}, {"append_to_response": "credits"}
if len(KEY) > 40: headers["Authorization"] = f"Bearer {KEY}"
else: params["api_key"] = KEY

done = 0
for r in todo.itertuples():
    if str(r.movieId) in meta:
        continue
    try:
        res = requests.get(f"https://api.themoviedb.org/3/movie/{r.tmdbId}",
                           params=params, headers=headers, timeout=15)
        if res.status_code == 429:
            time.sleep(3); continue
        if res.status_code == 401:
            sys.exit("TMDB rejected the key (401). Check the key, then run again.")
        if res.status_code != 200:
            meta[str(r.movieId)] = {}; continue
        d = res.json()
        crew = d.get("credits", {}).get("crew", [])
        meta[str(r.movieId)] = {
            "overview": d.get("overview") or "",
            "poster": d.get("poster_path"),
            "backdrop": d.get("backdrop_path"),
            "runtime": d.get("runtime"),
            "director": next((c["name"] for c in crew if c.get("job") == "Director"), ""),
            "cast": [c["name"] for c in d.get("credits", {}).get("cast", [])[:4]],
            "language": LANG.get(d.get("original_language"), (d.get("original_language") or "en").upper()),
        }
        done += 1
        if done % 50 == 0:
            OUT.write_text(json.dumps(meta), encoding="utf-8"); print("saved", done)
        time.sleep(0.05)
    except requests.RequestException as e:
        print("network error, rerun later:", e); break

OUT.write_text(json.dumps(meta), encoding="utf-8")
print(f"Done. {len(meta)} movies in {OUT.name}")
print("This product uses the TMDB API but is not endorsed or certified by TMDB.")
