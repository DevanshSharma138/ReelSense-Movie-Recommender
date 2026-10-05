"""ReelSense data loader. MovieLens only. Cached so files load once."""
from functools import lru_cache
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
MOVIES_COLS = {"movieId", "title", "genres"}
RATINGS_COLS = {"userId", "movieId", "rating", "timestamp"}


def _read(name: str, required: set) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Download ml-latest-small from "
            "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip "
            f"and copy {name} into the data/ folder."
        )
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
    return df


@lru_cache(maxsize=1)
def load_movies() -> pd.DataFrame:
    df = _read("movies.csv", MOVIES_COLS)
    df = df.dropna(subset=["movieId", "title"]).drop_duplicates("movieId")
    df["genres"] = df["genres"].fillna("").replace("(no genres listed)", "")
    df["movieId"] = df["movieId"].astype(int)
    df["year"] = df["title"].str.extract(r"\((\d{4})\)\s*$")[0]
    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_ratings() -> pd.DataFrame:
    df = _read("ratings.csv", RATINGS_COLS)
    df = df.dropna(subset=["userId", "movieId", "rating"])
    df = df.astype({"userId": int, "movieId": int, "rating": float})
    return df.reset_index(drop=True)


if __name__ == "__main__":
    m, r = load_movies(), load_ratings()
    print("Movies loaded:", len(m), "| Ratings loaded:", len(r))
    print("\nMovies columns:", list(m.columns), "\n", m.head())
    print("\nRatings columns:", list(r.columns), "\n", r.head())