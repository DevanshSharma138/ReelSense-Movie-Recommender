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

        # collaborative with graceful fallback
        self.has_collab = False
        try:
            r = load_ratings()
            if r is not None and len(r) >= 50:
                mids = np.sort(r.movieId.unique())
                self.midx = {m: i for i, m in enumerate(mids)}
                uidx = {u: i for i, u in enumerate(r.userId.unique())}
                self.mean = float(r.rating.mean())
                M = csr_matrix((r.rating - self.mean, (r.userId.map(uidx), r.movieId.map(self.midx))),
                               shape=(len(uidx), len(mids)))
                n_comp = min(k, min(M.shape) - 1)
                if n_comp >= 2:
                    svd = TruncatedSVD(n_components=n_comp, random_state=42).fit(M)
                    self.V = svd.components_                                   # k x n_all
                    cols = [self.midx[i] for i in self.ids if i in self.midx]
                    if len(cols) == len(self.ids):
                        self.Vcat = self.V[:, cols]                                # k x n_catalog
                        Vn = self.Vcat.T / (np.linalg.norm(self.Vcat.T, axis=1, keepdims=True) + 1e-9)
                        self.item_sim = Vn @ Vn.T
                        self.has_collab = True
        except Exception:
            self.has_collab = False

        if not self.has_collab:
            self.V = np.zeros((1, len(self.ids)))
            self.Vcat = np.zeros((1, len(self.ids)))
            self.midx = {}
            self.mean = 3.5
            self.item_sim = self.content_sim.copy()

        self._similar_cache = {}
        self._query_cache = {}

    # ---------------------------------------------------------------- helpers
    def _out(self, p, pct, sim, why):
        m = dict(self.cat[p])
        m.update(vector_match=pct, similarity=round(float(sim), 3), why_recommended=why, is_recommended=True)
        return m

    def cold_start(self, genres=None, n=12, exclude=()):
        order = sorted(range(len(self.cat)),
                       key=lambda p: (self.cat[p]["trending_rank"] or 99, -self.cat[p]["popularity"]))
        exclude_set = set(exclude or ())
        order = [p for p in order if self.ids[p] not in exclude_set]
        if genres:
            g = set(genres)
            order = [p for p in order if g & set(self.cat[p]["genres"])] or order
        order = order[:n]
        pcts = _percent([self.cat[p]["popularity"] for p in order])
        return [self._out(p, pc, self.cat[p]["popularity"] / 5,
                          ["Trending with the community right now" if self.cat[p]["trending_rank"]
                           else "Highly rated by thousands of viewers",
                           "Rate films or save titles to unlock personalized picks"]) for p, pc in zip(order, pcts)]

    # ---------------------------------------------------------------- public
    def recommend(self, ratings=None, n=12, genres=None, exclude=(), watchlist=None):
        """
        Personalized Recommendation Pipeline.
        
        Args:
            ratings: Dict[int, float] user movie ratings (0.0 to 5.0 scale).
            n: int number of recommendations to return.
            genres: Optional[list[str]] favorite genres to filter by.
            exclude: Iterable[int] movie IDs to strictly exclude (hidden_ids/not_interested).
            watchlist: Optional[Iterable[int]] movie IDs saved to user's Watchlist/Vault.
            
        Returns:
            Tuple[List[dict], str]: (recommended_movies, mode)
        """
        raw_r = ratings or {}
        # Normalize ratings ensuring 0.0-5.0 scale
        if any(float(v) > 5.0 for v in raw_r.values()):
            r = {int(k): float(v) / 2.0 for k, v in raw_r.items() if int(k) in self.pos}
        else:
            r = {int(k): float(v) for k, v in raw_r.items() if int(k) in self.pos}

        wl = [int(k) for k in (watchlist or ()) if int(k) in self.pos]
        banned = set(int(k) for k in (exclude or ())) | set(r.keys()) | set(wl)

        if len(r) == 0 and len(wl) == 0:
            return self.cold_start(genres, n, banned), "cold_start"

        # -------------------------------------------------------------
        # 1. TASTE PROFILE GENERATION (Explicit Ratings + Watchlist)
        # -------------------------------------------------------------
        # Weight mapping: 5★: +1.0, 4★: +0.5, 3★: 0.0, 2★: -0.5, 0-1★: -1.0
        # Watchlist (unrated): +0.35 (moderate positive intent)
        rated_weights = {}
        for mid, val in r.items():
            rated_weights[mid] = max(-1.0, min(1.0, (val - 3.0) / 2.0))

        # Add watchlist items that have not been explicitly rated
        all_weights = dict(rated_weights)
        for wid in wl:
            if wid not in all_weights:
                all_weights[wid] = 0.35

        pos_items = [(self.pos[mid], w) for mid, w in all_weights.items() if w > 0]
        neg_items = [(self.pos[mid], abs(w)) for mid, w in all_weights.items() if w < 0]

        # A. Positive Content Profile
        if pos_items:
            pos_idx = [p for p, _ in pos_items]
            pos_w = np.array([w for _, w in pos_items], dtype=float)
            pos_vec = np.asarray(self.X[pos_idx].T @ pos_w).ravel()
            p_norm = np.linalg.norm(pos_vec)
            pos_prof = pos_vec / p_norm if p_norm > 0 else np.zeros_like(pos_vec)
        else:
            pos_prof = np.zeros(self.X.shape[1], dtype=float)

        # B. Negative Content Profile (Avoidance Signal)
        if neg_items:
            neg_idx = [p for p, _ in neg_items]
            neg_w = np.array([w for _, w in neg_items], dtype=float)
            neg_vec = np.asarray(self.X[neg_idx].T @ neg_w).ravel()
            n_norm = np.linalg.norm(neg_vec)
            neg_prof = neg_vec / n_norm if n_norm > 0 else np.zeros_like(neg_vec)
        else:
            neg_prof = np.zeros(self.X.shape[1], dtype=float)

        # C. Combined Profile & Content Scoring
        if pos_items:
            user_prof = pos_prof - 0.45 * neg_prof
            u_norm = np.linalg.norm(user_prof)
            user_prof = user_prof / u_norm if u_norm > 0 else pos_prof
            s_content = np.asarray(self.X @ user_prof).ravel()
        else:
            s_content = -np.asarray(self.X @ neg_prof).ravel()

        # D. Direct Item Similarity Penalty for Negatively Rated Titles
        if neg_items:
            neg_idx = [p for p, _ in neg_items]
            neg_w = np.array([w for _, w in neg_items], dtype=float)
            neg_sims = self.content_sim[:, neg_idx] @ (neg_w / (neg_w.sum() or 1.0))
            s_content = s_content - 0.40 * np.maximum(0.0, neg_sims - 0.15)

        # -------------------------------------------------------------
        # 2. COLLABORATIVE SCORING (TruncatedSVD Latent Space)
        # -------------------------------------------------------------
        u = np.zeros(self.V.shape[1], dtype=float)
        valid_rated = [i for i in r if i in self.midx]
        if valid_rated:
            vals = np.array([r[i] for i in valid_rated], dtype=float)
            u[[self.midx[i] for i in valid_rated]] = vals - self.mean
            s_collab = (u @ self.V.T) @ self.Vcat
        else:
            s_collab = np.zeros(len(self.ids), dtype=float)

        # -------------------------------------------------------------
        # 3. HYBRID WEIGHTING & CALIBRATION
        # -------------------------------------------------------------
        if len(r) >= 3:
            alpha = self.alpha  # 0.4 content, 0.6 collab
            score = alpha * _norm(s_content) + (1.0 - alpha) * _norm(s_collab)
            mode = "hybrid"
        elif len(r) >= 1:
            score = 0.85 * _norm(s_content) + 0.15 * _norm(s_collab)
            mode = "cold_start"
        else:
            score = _norm(s_content)
            mode = "cold_start"

        # -------------------------------------------------------------
        # 4. EXCLUSIONS & GENRE FILTERING
        # -------------------------------------------------------------
        mask = np.array([i in banned for i in self.ids], dtype=bool)
        if genres:
            g = set(genres)
            mask |= np.array([not (g & set(m.get("genres", []))) for m in self.cat], dtype=bool)
        score[mask] = -1.0

        top = [p for p in np.argsort(-score)[:n] if score[p] >= 0]
        if len(top) < n:
            candidates = sorted(
                range(len(self.cat)),
                key=lambda p: (self.cat[p]["trending_rank"] or 99, -self.cat[p]["popularity"])
            )
            for p in candidates:
                if p not in top and self.ids[p] not in banned:
                    top.append(p)
                    if len(top) == n:
                        break

        pcts = _percent([score[p] for p in top])

        # -------------------------------------------------------------
        # 5. REASON GENERATION & EXPLANATIONS
        # -------------------------------------------------------------
        liked = [(self.pos[i], r[i]) for i in r if r[i] >= 3.5] or [(self.pos[i], r[i]) for i in r]
        out = []
        for p, pc in zip(top, pcts):
            why = []
            if liked:
                src_p, src_r = max(liked, key=lambda x: self.content_sim[p, x[0]])
                why.append(f"Because you rated {self.cat[src_p]['title']} {src_r:g}\u2605")
                shared = set(self.cat[p]["genres"]) & set(self.cat[src_p]["genres"])
                if shared:
                    why.append("Shared genres: " + ", ".join(sorted(shared)))
            elif wl:
                src_p = max([self.pos[w] for w in wl], key=lambda x: self.content_sim[p, x])
                why.append(f"Based on your saved vault title '{self.cat[src_p]['title']}'")
                shared = set(self.cat[p]["genres"]) & set(self.cat[src_p]["genres"])
                if shared:
                    why.append("Shared genres: " + ", ".join(sorted(shared)))
            else:
                why.append("Curated title based on community favorites")

            if len(r) >= 3 and _norm(s_collab)[p] > 0.6:
                why.append("Viewers with similar taste rated it highly")
            why.append(f"Hybrid score {score[p]:.2f} (content {_norm(s_content)[p]:.2f}, collaborative {_norm(s_collab)[p]:.2f})")
            out.append(self._out(p, pc, score[p], why))
        return out, mode

    def similar(self, movie_id, limit=6):
        cache_key = (movie_id, limit)
        if cache_key in self._similar_cache:
            return self._similar_cache[cache_key]
        p = self.pos.get(movie_id)
        if p is None:
            return []
        sim = self.alpha * self.content_sim[p] + (1 - self.alpha) * self.item_sim[p]
        order = [j for j in np.argsort(-sim) if j != p][:limit]
        pcts = _percent([sim[j] for j in order])
        res = [self._out(j, pc, sim[j], [f"Similar to {self.cat[p]['title']}",
                                           f"Content {self.content_sim[p, j]:.2f} \u00b7 audience {self.item_sim[p, j]:.2f}"])
                for j, pc in zip(order, pcts)]
        self._similar_cache[cache_key] = res
        return res

    def query(self, text, limit=6):
        cache_key = (str(text).strip().lower(), limit)
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        q = self.vec.transform([re.sub(r"[-/]", "_", str(text).lower())])
        s = cosine_similarity(q, self.X).ravel()
        order = [j for j in np.argsort(-s)[:limit] if s[j] > 0]
        pcts = _percent([s[j] for j in order])
        res = [self._out(j, pc, s[j], ["Matches your search on plot, genre and mood"]) for j, pc in zip(order, pcts)]
        self._query_cache[cache_key] = res
        return res

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
