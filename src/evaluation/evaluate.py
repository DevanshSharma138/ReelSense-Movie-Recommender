"""
ReelSense - Recommender Offline Evaluation Engine (Phase 4)
Evaluates recommendation models on MovieLens benchmark interactions:
  - Metrics: Precision@K, Recall@K, HitRate@K, Catalog Coverage, Intra-List Diversity
  - Methodology: User-level temporal 80/20 train/test split on real users (>= 20 ratings)
  - Models compared:
      1. Baseline (Bayesian Popularity / Cold-Start)
      2. Content-Based Only (TF-IDF Cosine, alpha=1.0)
      3. Collaborative-Only (TruncatedSVD Matrix Factorization, alpha=0.0)
      4. ReelSense Hybrid Model (alpha=0.4)
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.loader import load_ratings
from src.services.catalog import get_catalog
from src.services.hybrid_model import HybridModel, _norm


def compute_genre_diversity(movies):
    """Compute average pairwise genre dissimilarity within a recommendation list."""
    if len(movies) < 2:
        return 0.0
    dissimilarities = []
    for i in range(len(movies)):
        g_i = set(movies[i].get("genres", []))
        for j in range(i + 1, len(movies)):
            g_j = set(movies[j].get("genres", []))
            union = g_i | g_j
            if not union:
                dissimilarities.append(0.0)
            else:
                jaccard = len(g_i & g_j) / len(union)
                dissimilarities.append(1.0 - jaccard)
    return float(np.mean(dissimilarities)) if dissimilarities else 0.0


def evaluate_models(n_users=50, min_ratings=20, k_list=(5, 10), rel_threshold=3.5):
    """
    Run offline evaluation on MovieLens ratings using temporal train/test split.
    Returns metrics dictionary with comparisons.
    """
    ratings_df = load_ratings()
    catalog = get_catalog()
    catalog_ids = set(m["id"] for m in catalog)

    # Filter to ratings for catalog items
    df_cat = ratings_df[ratings_df["movieId"].isin(catalog_ids)].copy()
    user_counts = df_cat.groupby("userId").size()
    eligible_users = user_counts[user_counts >= min_ratings].index.tolist()

    if not eligible_users:
        eligible_users = user_counts.nlargest(n_users).index.tolist()

    # Sample a reproducible subset of users
    rng = np.random.RandomState(42)
    selected_users = rng.choice(eligible_users, size=min(n_users, len(eligible_users)), replace=False)

    hybrid = HybridModel(alpha=0.4)
    content_model = HybridModel(alpha=1.0)
    collab_model = HybridModel(alpha=0.0)

    models = {
        "Popularity Baseline": None,
        "Content-Based (TF-IDF)": content_model,
        "Collaborative (SVD)": collab_model,
        "ReelSense Hybrid (0.4)": hybrid,
    }

    results = {
        m_name: {
            "p5": [], "p10": [],
            "r5": [], "r10": [],
            "hit10": [],
            "rec_items": set(),
            "diversity10": [],
        }
        for m_name in models
    }

    for uid in selected_users:
        u_ratings = df_cat[df_cat["userId"] == uid].sort_values("timestamp")
        n_u = len(u_ratings)
        n_train = max(3, int(n_u * 0.8))

        train_part = u_ratings.iloc[:n_train]
        test_part = u_ratings.iloc[n_train:]

        train_dict = dict(zip(train_part["movieId"], train_part["rating"]))
        relevant_test_ids = set(test_part[test_part["rating"] >= rel_threshold]["movieId"])

        if not relevant_test_ids:
            continue

        for m_name, model in models.items():
            if model is None:
                # Cold start / Popularity
                recs = hybrid.cold_start(n=10, exclude=set(train_dict.keys()))
            else:
                recs, _ = model.recommend(train_dict, n=10, exclude=set(train_dict.keys()))

            rec_ids_5 = [m["id"] for m in recs[:5]]
            rec_ids_10 = [m["id"] for m in recs[:10]]

            # Precision & Recall @ 5
            hits_5 = len(set(rec_ids_5) & relevant_test_ids)
            results[m_name]["p5"].append(hits_5 / 5.0)
            results[m_name]["r5"].append(hits_5 / len(relevant_test_ids))

            # Precision & Recall @ 10
            hits_10 = len(set(rec_ids_10) & relevant_test_ids)
            results[m_name]["p10"].append(hits_10 / 10.0)
            results[m_name]["r10"].append(hits_10 / len(relevant_test_ids))

            # Hit Rate @ 10
            results[m_name]["hit10"].append(1.0 if hits_10 > 0 else 0.0)

            # Catalog coverage tracking
            results[m_name]["rec_items"].update(rec_ids_10)

            # Intra-list Diversity @ 10
            results[m_name]["diversity10"].append(compute_genre_diversity(recs[:10]))

    # Aggregate metrics
    summary = {}
    for m_name, vals in results.items():
        n_eval = len(vals["p10"])
        if n_eval == 0:
            continue
        summary[m_name] = {
            "Precision@5": float(np.mean(vals["p5"])),
            "Precision@10": float(np.mean(vals["p10"])),
            "Recall@5": float(np.mean(vals["r5"])),
            "Recall@10": float(np.mean(vals["r10"])),
            "HitRate@10": float(np.mean(vals["hit10"])),
            "Coverage (%)": float(len(vals["rec_items"]) / len(catalog) * 100.0),
            "Diversity@10": float(np.mean(vals["diversity10"])),
            "Users Evaluated": n_eval,
        }

    return summary


def run_and_print_evaluation():
    print("=" * 70)
    print("REELSENSE RECOMMENDER OFFLINE EVALUATION (MovieLens ml-latest-small)")
    print("=" * 70)
    print("Evaluating 50 active users with temporal 80/20 train-test splits...")
    print("Ground truth: held-out user ratings >= 3.5/5.0 (>= 7.0/10)")
    print("-" * 70)

    metrics = evaluate_models(n_users=50, min_ratings=20, rel_threshold=3.5)

    headers = ["Model", "P@5", "P@10", "R@5", "R@10", "HitRate@10", "Coverage", "Diversity"]
    print(f"{headers[0]:<25} | {headers[1]:<6} | {headers[2]:<6} | {headers[3]:<6} | {headers[4]:<6} | {headers[5]:<10} | {headers[6]:<9} | {headers[7]:<9}")
    print("-" * 95)

    for m_name, m_data in metrics.items():
        print(
            f"{m_name:<25} | "
            f"{m_data['Precision@5']:.4f} | "
            f"{m_data['Precision@10']:.4f} | "
            f"{m_data['Recall@5']:.4f} | "
            f"{m_data['Recall@10']:.4f} | "
            f"{m_data['HitRate@10']:.4f}     | "
            f"{m_data['Coverage (%)']:.1f}%    | "
            f"{m_data['Diversity@10']:.4f}"
        )
    print("=" * 70)
    return metrics


if __name__ == "__main__":
    run_and_print_evaluation()
