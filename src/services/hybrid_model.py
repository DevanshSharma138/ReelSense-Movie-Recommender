"""
ReelSense - Hybrid Recommender (Phase 3)
  content      : TF-IDF + cosine over genres/tags/overview/director/cast
  collaborative: TruncatedSVD (matrix factorization) on MovieLens ratings, new users folded in
  hybrid       : score = ALPHA * content + (1 - ALPHA) * collaborative
  cold start   : fewer than MIN_RATINGS ratings -> trending / genre fallback
"""
import re
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data.loader import load_ratings
from src.services.catalog import get_catalog

ALPHA = 0.4
MIN_RATINGS = 3


def _tok(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def _doc(m):
    return " ".join(
        [_tok(g) for g in m["genres"]] * 3
        + [_tok(x) for x in m.get("moods", [])]
        + [_tok(m.get("director", ""))] + [_tok(c) for c in m.get("cast", [])]
        + [m["title"], m.get("tags", ""), m.get("overview", "")]
    )


def _norm(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a, dtype=float)


def _percent(scores, lo=72, hi=99):
    s = np.asarray(scores, dtype=float)
    if len(s) == 0:
        return []
    return [hi if s.max() == s.min() else int(round(lo + (hi - lo) * (x - s.min()) / (s.max() - s.min()))) for x in s]


class HybridModel:
    def __init__(self, alpha=ALPHA, k=50):
        self.alpha = alpha
        self.cat = get_catalog()
        self.ids = [m["id"] for m in self.cat]
        self.pos = {i: p for p, i in enumerate(self.ids)}

        # content
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.X = self.vec.fit_transform([_doc(m) for m in self.cat])
        self.content_sim = cosine_similarity(self.X)

        # collaborative
        r = load_ratings()
        mids = np.sort(r.movieId.unique())
        self.midx = {m: i for i, m in enumerate(mids)}
        uidx = {u: i for i, u in enumerate(r.userId.unique())}
        self.mean = float(r.rating.mean())
        M = csr_matrix((r.rating - self.mean, (r.userId.map(uidx), r.movieId.map(self.midx))),
                       shape=(len(uidx), len(mids)))
        svd = TruncatedSVD(n_components=min(k, min(M.shape) - 1), random_state=42).fit(M)
        self.V = svd.components_                                   # k x n_all
        cols = [self.midx[i] for i in self.ids]
        self.Vcat = self.V[:, cols]                                # k x n_catalog
        Vn = self.Vcat.T / (np.linalg.norm(self.Vcat.T, axis=1, keepdims=True) + 1e-9)
        self.item_sim = Vn @ Vn.T

    # ---------------------------------------------------------------- helpers
    def _out(self, p, pct, sim, why):
        m = dict(self.cat[p])
        m.update(vector_match=pct, similarity=round(float(sim), 3), why_recommended=why, is_recommended=True)
        return m

    def cold_start(self, genres=None, n=12, exclude=()):
        order = sorted(range(len(self.cat)),
                       key=lambda p: (self.cat[p]["trending_rank"] or 99, -self.cat[p]["popularity"]))
        order = [p for p in order if self.ids[p] not in set(exclude)]
        if genres:
            g = set(genres)
            order = [p for p in order if g & set(self.cat[p]["genres"])] or order
        order = order[:n]
        pcts = _percent([self.cat[p]["popularity"] for p in order])
        return [self._out(p, pc, self.cat[p]["popularity"] / 5,
                          ["Trending with the community right now" if self.cat[p]["trending_rank"]
                           else "Highly rated by thousands of viewers",
                           "Rate 3 films to unlock personalised picks"]) for p, pc in zip(order, pcts)]

    # ---------------------------------------------------------------- public
    def recommend(self, ratings, n=12, genres=None, exclude=()):
        """ratings: {movieId: stars 0.5-5}. Returns (list[movie], mode)."""
        r = {int(k): float(v) for k, v in (ratings or {}).items() if int(k) in self.pos}
        if len(r) < MIN_RATINGS:
            return self.cold_start(genres, n, exclude), "cold_start"

        ids = list(r)
        pos = np.array([self.pos[i] for i in ids])
        vals = np.array([r[i] for i in ids])

        w = np.clip(vals - 2.5, 0, None)                          # only liked films shape taste
        if w.sum() > 0:
            prof = np.asarray(self.X[pos].T @ w).ravel()
            prof /= (np.linalg.norm(prof) or 1.0)
            s_content = np.asarray(self.X @ prof).ravel()
        else:
            s_content = np.zeros(len(self.ids))

        u = np.zeros(self.V.shape[1])
        u[[self.midx[i] for i in ids]] = vals - self.mean
        s_collab = (u @ self.V.T) @ self.Vcat

        score = self.alpha * _norm(s_content) + (1 - self.alpha) * _norm(s_collab)
        banned = set(ids) | set(exclude)
        mask = np.array([i in banned for i in self.ids])
        if genres:
            g = set(genres)
            mask |= np.array([not (g & set(m["genres"])) for m in self.cat])
        score[mask] = -1
        top = [p for p in np.argsort(-score)[:n] if score[p] >= 0]
        pcts = _percent([score[p] for p in top])

        liked = [(self.pos[i], r[i]) for i in ids if r[i] >= 4] or [(self.pos[i], r[i]) for i in ids]
        out = []
        for p, pc in zip(top, pcts):
            src_p, src_r = max(liked, key=lambda x: self.content_sim[p, x[0]])
            why = [f"Because you rated {self.cat[src_p]['title']} {src_r:g}\u2605"]
            shared = set(self.cat[p]["genres"]) & set(self.cat[src_p]["genres"])
            if shared:
                why.append("Shared genres: " + ", ".join(sorted(shared)))
            if _norm(s_collab)[p] > 0.6:
                why.append("Viewers with similar taste rated it highly")
            why.append(f"Hybrid score {score[p]:.2f} (content {_norm(s_content)[p]:.2f}, collaborative {_norm(s_collab)[p]:.2f})")
            out.append(self._out(p, pc, score[p], why))
        return out, "hybrid"

    def similar(self, movie_id, limit=6):
        p = self.pos.get(movie_id)
        if p is None:
            return []
        sim = self.alpha * self.content_sim[p] + (1 - self.alpha) * self.item_sim[p]
        order = [j for j in np.argsort(-sim) if j != p][:limit]
        pcts = _percent([sim[j] for j in order])
        return [self._out(j, pc, sim[j], [f"Similar to {self.cat[p]['title']}",
                                           f"Content {self.content_sim[p, j]:.2f} \u00b7 audience {self.item_sim[p, j]:.2f}"])
                for j, pc in zip(order, pcts)]

    def query(self, text, limit=6):
        q = self.vec.transform([re.sub(r"[-/]", "_", str(text).lower())])
        s = cosine_similarity(q, self.X).ravel()
        order = [j for j in np.argsort(-s)[:limit] if s[j] > 0]
        pcts = _percent([s[j] for j in order])
        return [self._out(j, pc, s[j], ["Matches your search on plot, genre and mood"]) for j, pc in zip(order, pcts)]

    def get_breakdown_signals(self, movie_id, ratings):
        """
        Computes mathematically grounded signals for a specific movie given user ratings.
        Returns a dict containing exact normalized scores, contributions, and reference movies.
        """
        p = self.pos.get(movie_id)
        if p is None:
            return {"in_catalog": False}

        target_movie = self.cat[p]
        raw_r = ratings or {}
        # Ensure ratings are on 0.5-5.0 scale (if old 10-scale passed, divide by 2)
        if any(float(v) > 5.0 for v in raw_r.values()):
            r = {int(k): float(v) / 2.0 for k, v in raw_r.items() if int(k) in self.pos}
            orig_ratings = {int(k): float(v) / 2.0 for k, v in raw_r.items() if int(k) in self.pos}
        else:
            r = {int(k): float(v) for k, v in raw_r.items() if int(k) in self.pos}
            orig_ratings = {int(k): float(v) for k, v in raw_r.items() if int(k) in self.pos}

        # Check cold-start threshold
        if len(r) < MIN_RATINGS:
            ref_movies = []
            if len(r) > 0:
                for rid, rval in r.items():
                    rp = self.pos[rid]
                    sim_val = float(self.content_sim[p, rp])
                    ref_m = self.cat[rp]
                    shared_g = sorted(list(set(target_movie.get("genres", [])) & set(ref_m.get("genres", []))))
                    shared_m = sorted(list(set(target_movie.get("moods", [])) & set(ref_m.get("moods", []))))
                    ref_movies.append({
                        "id": rid,
                        "title": ref_m["title"],
                        "user_rating": orig_ratings.get(rid, rval),
                        "similarity": round(sim_val, 2),
                        "shared_genres": shared_g,
                        "shared_moods": shared_m,
                    })
                ref_movies.sort(key=lambda x: x["similarity"], reverse=True)

            return {
                "in_catalog": True,
                "is_cold_start": True,
                "movie_id": movie_id,
                "title": target_movie["title"],
                "content_score": None,
                "collab_score": None,
                "hybrid_score": None,
                "content_contrib": None,
                "collab_contrib": None,
                "reference_movies": ref_movies,
                "popularity": float(target_movie.get("popularity", 0.0)),
                "community_rating": float(target_movie.get("rating", 0.0)),
                "n_ratings": int(target_movie.get("n_ratings", 0)),
                "trending_rank": target_movie.get("trending_rank"),
                "is_hidden_gem": bool(target_movie.get("is_hidden_gem", False)),
            }

        # Hybrid model computation
        ids = list(r)
        pos = np.array([self.pos[i] for i in ids])
        vals = np.array([r[i] for i in ids])

        w = np.clip(vals - 2.5, 0, None)
        if w.sum() > 0:
            prof = np.asarray(self.X[pos].T @ w).ravel()
            prof /= (np.linalg.norm(prof) or 1.0)
            s_content = np.asarray(self.X @ prof).ravel()
        else:
            s_content = np.zeros(len(self.ids))

        u = np.zeros(self.V.shape[1])
        u[[self.midx[i] for i in ids]] = vals - self.mean
        s_collab = (u @ self.V.T) @ self.Vcat

        norm_c = _norm(s_content)
        norm_cl = _norm(s_collab)

        content_val = float(norm_c[p])
        collab_val = float(norm_cl[p])
        hybrid_val = float(self.alpha * content_val + (1.0 - self.alpha) * collab_val)

        # Reference movies among positively rated (stars >= 3.5 or all rated)
        liked_ids = [i for i in ids if r[i] >= 3.5] or ids
        ref_movies = []
        for rid in liked_ids:
            rp = self.pos[rid]
            sim_val = float(self.content_sim[p, rp])
            ref_m = self.cat[rp]
            shared_g = sorted(list(set(target_movie.get("genres", [])) & set(ref_m.get("genres", []))))
            shared_m = sorted(list(set(target_movie.get("moods", [])) & set(ref_m.get("moods", []))))
            ref_movies.append({
                "id": rid,
                "title": ref_m["title"],
                "user_rating": orig_ratings.get(rid, r[rid]),
                "similarity": round(sim_val, 2),
                "shared_genres": shared_g,
                "shared_moods": shared_m,
            })
        ref_movies.sort(key=lambda x: x["similarity"], reverse=True)
        ref_movies = ref_movies[:3]

        return {
            "in_catalog": True,
            "is_cold_start": False,
            "movie_id": movie_id,
            "title": target_movie["title"],
            "content_score": round(content_val, 3),
            "collab_score": round(collab_val, 3),
            "hybrid_score": round(hybrid_val, 3),
            "content_contrib": round(self.alpha * content_val, 3),
            "collab_contrib": round((1.0 - self.alpha) * collab_val, 3),
            "reference_movies": ref_movies,
            "popularity": float(target_movie.get("popularity", 0.0)),
            "community_rating": float(target_movie.get("rating", 0.0)),
            "n_ratings": int(target_movie.get("n_ratings", 0)),
            "trending_rank": target_movie.get("trending_rank"),
            "is_hidden_gem": bool(target_movie.get("is_hidden_gem", False)),
        }


_model = None
def get_model():
    global _model
    if _model is None:
        _model = HybridModel()
    return _model
