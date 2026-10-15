"""
ReelSense - Taste & Recommendation Intelligence Service (Phase 6)
Provides mathematically grounded explanations and taste evolution analytics.
No LLM, no fake numbers, strictly derived from real model signals and user state.
"""
from typing import Any, Dict, List, Optional, Tuple
from src.services.catalog import get_catalog
from src.services.hybrid_model import get_model
from src.services.movie_service import MovieService


class TasteService:
    @staticmethod
    def get_recommendation_breakdown(movie_or_id: Any, user_ratings: Optional[Dict[Any, Any]] = None) -> Dict[str, Any]:
        """
        Computes a transparent, mathematically grounded recommendation breakdown for a movie.
        Returns:
            - is_cold_start (bool)
            - content_score, collab_score, hybrid_score (floats 0.0-1.0 or None)
            - content_contrib, collab_contrib (floats or None)
            - content_match_pct, collab_match_pct, taste_match_pct (ints 0-100 or None)
            - strength_label (str)
            - positive_references (list of dicts with title, rating, similarity)
            - matched_genres (list of str)
            - matched_moods (list of str)
            - narrative (list of str)
        """
        # Resolve movie dict and ID
        if isinstance(movie_or_id, dict):
            movie_id = movie_or_id.get("id")
            if "title" in movie_or_id:
                movie = movie_or_id
            else:
                movie = MovieService.get_movie_by_id(movie_id)
        else:
            try:
                movie_id = int(movie_or_id)
                movie = MovieService.get_movie_by_id(movie_id)
            except (ValueError, TypeError):
                return {"in_catalog": False}

        if not movie or movie_id is None:
            return {"in_catalog": False}

        raw_ratings = user_ratings or {}
        model = get_model()
        signals = model.get_breakdown_signals(movie_id, raw_ratings)

        if not signals.get("in_catalog"):
            return {"in_catalog": False}

        # Calculate user's overall genre weights from ratings
        cat_by_id = MovieService.get_movie_by_id(movie_id)  # warm check
        from src.services.catalog import get_by_id
        cat_by_id = get_by_id()
        user_genre_weights = {}
        for mid, score in raw_ratings.items():
            try:
                m_item = cat_by_id.get(int(mid))
                if m_item:
                    for g in m_item.get("genres", []):
                        user_genre_weights[g] = user_genre_weights.get(g, 0.0) + float(score)
            except (ValueError, TypeError):
                continue

        movie_genres = movie.get("genres", [])
        movie_moods = movie.get("moods", [])

        # Taste match calculation (alignment between movie's genres and user's weighted genre favorites)
        taste_match_pct = None
        if user_genre_weights and movie_genres:
            max_gw = max(user_genre_weights.values()) if user_genre_weights else 1.0
            total_possible = len(movie_genres) * max_gw
            actual_gw = sum(user_genre_weights.get(g, 0.0) for g in movie_genres)
            if total_possible > 0:
                taste_match_pct = int(round(min(1.0, actual_gw / total_possible) * 100))

        # Identify strong genre and mood matches
        top_user_genres = sorted(user_genre_weights.keys(), key=lambda g: user_genre_weights[g], reverse=True)[:3]
        matched_genres = [g for g in movie_genres if g in top_user_genres] or movie_genres[:2]
        matched_moods = movie_moods[:2]

        is_cold_start = signals.get("is_cold_start", True)
        narrative = []

        if is_cold_start:
            n_rated = len([k for k in raw_ratings if int(k) in model.pos])
            # Determine qualitative strength for cold-start
            if movie.get("trending_rank") and movie["trending_rank"] <= 10:
                strength_label = "Trending High"
            elif movie.get("is_hidden_gem"):
                strength_label = "Curator Highlight"
            elif float(movie.get("rating", 0.0)) >= 8.0:
                strength_label = "Critical Acclaim"
            else:
                strength_label = "Community Curated"

            if n_rated == 0:
                narrative.append("Taste profile uninitialized. React to (like/dislike) 3 films to activate personalized hybrid recommendations.")
            else:
                narrative.append(f"Profile developing ({n_rated}/3 reactions recorded). Collaborative filtering unlocks at 3 reactions.")

            if signals.get("reference_movies"):
                top_ref = signals["reference_movies"][0]
                narrative.append(
                    f"Content overlap with '{top_ref['title']}' (rated {top_ref['user_rating']:g}/5, cosine similarity {top_ref['similarity']:.2f})."
                )

            if movie.get("trending_rank"):
                narrative.append(f"Trending #{movie['trending_rank']} among active community viewers.")
            elif movie.get("is_hidden_gem"):
                narrative.append("Curator Hidden Gem with exceptional review scores.")

            if movie.get("n_ratings", 0) > 0:
                narrative.append(f"Rated ⭐ {movie.get('rating', 0):.1f}/10 across {movie.get('n_ratings')} MovieLens reviews.")

            return {
                "in_catalog": True,
                "is_cold_start": True,
                "movie_id": movie_id,
                "title": movie["title"],
                "content_score": None,
                "collab_score": None,
                "hybrid_score": None,
                "content_contrib": None,
                "collab_contrib": None,
                "content_match_pct": None,
                "collab_match_pct": None,
                "taste_match_pct": taste_match_pct,
                "strength_label": strength_label,
                "positive_references": signals.get("reference_movies", []),
                "matched_genres": matched_genres,
                "matched_moods": matched_moods,
                "popularity": signals.get("popularity", 0.0),
                "community_rating": signals.get("community_rating", 0.0),
                "n_ratings": signals.get("n_ratings", 0),
                "narrative": narrative,
            }

        # Personalized Hybrid Breakdown (>= 3 ratings)
        content_score = signals["content_score"]
        collab_score = signals["collab_score"]
        hybrid_score = signals["hybrid_score"]
        content_contrib = signals["content_contrib"]
        collab_contrib = signals["collab_contrib"]

        content_match_pct = int(round(content_score * 100))
        collab_match_pct = int(round(collab_score * 100))
        if taste_match_pct is None:
            taste_match_pct = int(round(content_score * 100))

        # Qualitative strength label from actual hybrid score
        if hybrid_score >= 0.75:
            strength_label = "Very Strong"
        elif hybrid_score >= 0.60:
            strength_label = "Strong"
        elif hybrid_score >= 0.45:
            strength_label = "Moderate"
        else:
            strength_label = "Developing"

        # Build transparent narrative from real signals
        refs = signals.get("reference_movies", [])
        if refs:
            top_ref = refs[0]
            shared_info = f" (Shared genres: {', '.join(top_ref['shared_genres'])})" if top_ref.get("shared_genres") else ""
            narrative.append(
                f"Because you rated '{top_ref['title']}' highly ({top_ref['user_rating']:g}/5){shared_info}."
            )
            narrative.append(
                f"TF-IDF content cosine similarity with your favorites is {top_ref['similarity']:.2f}."
            )

        if collab_score >= 0.60:
            narrative.append("Strong collaborative signal: viewers with similar rating profiles gave this high marks.")
        elif collab_score >= 0.40:
            narrative.append("Moderate collaborative alignment with comparable viewer patterns.")
        else:
            narrative.append("Exploratory collaborative signal across community clusters.")

        narrative.append(
            f"Final Hybrid Score: {hybrid_score:.2f} (Content contribution {content_contrib:.2f} + Collaborative contribution {collab_contrib:.2f})."
        )

        return {
            "in_catalog": True,
            "is_cold_start": False,
            "movie_id": movie_id,
            "title": movie["title"],
            "content_score": content_score,
            "collab_score": collab_score,
            "hybrid_score": hybrid_score,
            "content_contrib": content_contrib,
            "collab_contrib": collab_contrib,
            "content_match_pct": content_match_pct,
            "collab_match_pct": collab_match_pct,
            "taste_match_pct": taste_match_pct,
            "strength_label": strength_label,
            "positive_references": refs,
            "matched_genres": matched_genres,
            "matched_moods": matched_moods,
            "popularity": signals.get("popularity", 0.0),
            "community_rating": signals.get("community_rating", 0.0),
            "n_ratings": signals.get("n_ratings", 0),
            "narrative": narrative,
        }

    @staticmethod
    def get_taste_evolution(ratings: Optional[Dict[Any, Any]]) -> Dict[str, Any]:
        """
        Reconstructs the evolution of user genre preferences across cumulative rating milestones.
        Reuses the exact rating-weighted genre strength logic from the Taste Profile.
        Does not invent fake timestamps; uses rating-count stages (1st, 3rd, 5th, 10th, Current).
        """
        raw = ratings or {}
        from src.services.catalog import get_by_id
        catalog_by_id = get_by_id()
        valid_items: List[Tuple[int, float]] = []
        for k, v in raw.items():
            try:
                mid = int(k)
                score = float(v)
                if mid in catalog_by_id:
                    valid_items.append((mid, score))
            except (ValueError, TypeError):
                continue

        total_rated = len(valid_items)
        if total_rated == 0:
            return {
                "is_empty": True,
                "is_minimal": False,
                "total_rated": 0,
                "milestones": [],
                "top_genres": [],
                "evolution_matrix": {},
                "taste_shifts": [],
                "insights": {
                    "emerging": None,
                    "consistent": None,
                    "biggest_change": None,
                    "summary": "Rate movies across the catalog to begin tracking your taste evolution.",
                },
            }

        # Determine dynamic milestones strictly <= total_rated
        # Milestones: 1st rating, 3rd (hybrid threshold), 5th, 10th, 20th, 50th, and Current
        candidate_cutoffs = [1, 3, 5, 10, 20, 50]
        selected_cutoffs = [c for c in candidate_cutoffs if c < total_rated]
        if total_rated not in selected_cutoffs:
            selected_cutoffs.append(total_rated)
        selected_cutoffs.sort()

        milestones = []
        for cutoff in selected_cutoffs:
            slice_items = valid_items[:cutoff]
            # Exact Taste Profile weighting logic: genre_weights[g] += float(score)
            genre_weights: Dict[str, float] = {}
            genre_counts: Dict[str, int] = {}
            slice_scores = [score for _, score in slice_items]
            avg_score = sum(slice_scores) / len(slice_scores)

            for mid, score in slice_items:
                m = catalog_by_id.get(mid)
                if m:
                    for g in m.get("genres", []):
                        genre_weights[g] = genre_weights.get(g, 0.0) + float(score)
                        genre_counts[g] = genre_counts.get(g, 0) + 1

            total_pts = sum(genre_weights.values()) or 1.0
            # Calculate genre share % (percentage of user's genre points)
            genre_shares = {
                g: round((w / total_pts) * 100.0, 1) for g, w in genre_weights.items()
            }
            dominant_genre = max(genre_weights.keys(), key=lambda g: genre_weights[g]) if genre_weights else "Diverse"

            if cutoff == 1:
                label = "1st Rating"
            elif cutoff == 3:
                label = "3rd Rating (Hybrid Unlocked)"
            elif cutoff == 5:
                label = "5th Rating"
            elif cutoff == 10:
                label = "10th Rating"
            elif cutoff == 20:
                label = "20th Rating"
            elif cutoff == total_rated:
                label = f"Current ({total_rated} Ratings)"
            else:
                label = f"{cutoff}th Rating"

            milestones.append({
                "cutoff": cutoff,
                "label": label,
                "dominant_genre": dominant_genre,
                "avg_rating": round(avg_score, 2),
                "genre_weights": genre_weights,
                "genre_counts": genre_counts,
                "genre_shares": genre_shares,
                "total_points": round(total_pts, 1),
            })

        # Identify top 6 overall genres at current milestone
        current_m = milestones[-1]
        top_genres = sorted(
            current_m["genre_weights"].keys(),
            key=lambda g: current_m["genre_weights"][g],
            reverse=True,
        )[:6]

        # Build evolution matrix: {genre: [share_at_m0, share_at_m1, ...]}
        evolution_matrix: Dict[str, List[float]] = {}
        for g in top_genres:
            evolution_matrix[g] = [
                m["genre_shares"].get(g, 0.0) for m in milestones
            ]

        # Calculate taste shifts if at least 2 milestones exist
        taste_shifts = []
        emerging_genre = None
        consistent_genre = None
        biggest_change_genre = None
        biggest_delta = 0.0

        if len(milestones) >= 2:
            first_m = milestones[0]
            first_shares = first_m["genre_shares"]
            curr_shares = current_m["genre_shares"]

            # Initial top 2 genres at milestone 1
            first_top_2 = sorted(
                first_shares.keys(), key=lambda g: first_shares[g], reverse=True
            )[:2]

            genre_deltas = {}
            for g in top_genres:
                delta = round(curr_shares.get(g, 0.0) - first_shares.get(g, 0.0), 1)
                genre_deltas[g] = delta

                if abs(delta) > abs(biggest_delta):
                    biggest_delta = delta
                    biggest_change_genre = g

                if delta >= 4.0:
                    taste_shifts.append({
                        "genre": g,
                        "direction": "up",
                        "delta": delta,
                        "label": f"↑ {g} (+{delta:.1f}%)",
                    })
                elif delta <= -4.0:
                    taste_shifts.append({
                        "genre": g,
                        "direction": "down",
                        "delta": delta,
                        "label": f"↓ {g} ({delta:.1f}%)",
                    })

            # Emerging genre: grew significantly and was not initial #1 or #2
            candidates_emerging = [
                g for g in top_genres
                if g not in first_top_2 and genre_deltas.get(g, 0.0) >= 3.0
            ]
            if candidates_emerging:
                emerging_genre = max(candidates_emerging, key=lambda g: genre_deltas[g])
            elif taste_shifts:
                pos_shifts = [s for s in taste_shifts if s["direction"] == "up"]
                if pos_shifts:
                    emerging_genre = pos_shifts[0]["genre"]

            # Most consistent genre: present across all milestones with lowest variance
            candidate_consistent = []
            for g in top_genres:
                shares = evolution_matrix[g]
                if all(s > 0 for s in shares):
                    spread = max(shares) - min(shares)
                    candidate_consistent.append((g, spread))
            if candidate_consistent:
                candidate_consistent.sort(key=lambda x: x[1])
                consistent_genre = candidate_consistent[0][0]

        # Generate truthful summary insight
        if total_rated < 3:
            summary = (
                f"You have evaluated {total_rated} title{'s' if total_rated != 1 else ''}. "
                "Taste profile is currently forming; like or dislike 3 or more films to unlock milestone comparisons and hybrid recommendations."
            )
        elif taste_shifts:
            up_genres = [s["genre"] for s in taste_shifts if s["direction"] == "up"]
            if up_genres:
                summary = (
                    f"Your taste has progressively expanded toward {', '.join(up_genres)}, "
                    f"while maintaining steady affinity for {current_m['dominant_genre']}."
                )
            else:
                summary = f"Your genre preference remains anchored in {current_m['dominant_genre']}."
        else:
            summary = (
                f"Your genre distribution has remained balanced across your {total_rated} rated titles, "
                f"with {current_m['dominant_genre']} as your top preference."
            )

        return {
            "is_empty": False,
            "is_minimal": total_rated < 3,
            "total_rated": total_rated,
            "milestones": milestones,
            "top_genres": top_genres,
            "evolution_matrix": evolution_matrix,
            "taste_shifts": taste_shifts,
            "insights": {
                "emerging": emerging_genre,
                "consistent": consistent_genre,
                "biggest_change": (
                    f"{biggest_change_genre} ({'+' if biggest_delta > 0 else ''}{biggest_delta:.1f}%)"
                    if biggest_change_genre and abs(biggest_delta) >= 3.0
                    else None
                ),
                "summary": summary,
            },
        }
