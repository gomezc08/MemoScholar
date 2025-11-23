"""
Advanced Collaborative Filtering Approaches for Sparse Data

1. Item-based CF: Find similar items instead of similar users
2. BPR (Bayesian Personalized Ranking): Optimized for implicit feedback
3. Hybrid: Combine multiple approaches

For extremely sparse data like CiteULike where user-based CF fails
"""

import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import time
import random
import os


class ItemBasedCF:
    """
    Item-based Collaborative Filtering

    Key idea: Instead of finding similar users, find similar items
    Works better when:
    - Few users but many interactions per user
    - User-user overlap is low
    - Item-item overlap is higher
    """

    def __init__(self, k_neighbors=20):
        """
        Initialize item-based CF

        Parameters:
        -----------
        k_neighbors : int
            Number of similar items to consider
        """
        self.k_neighbors = k_neighbors
        self.item_similarity = None
        self.user_item_matrix = None
        self.n_users = 0
        self.n_items = 0

    def fit(self, user_item_matrix):
        """
        Compute item-item similarity matrix

        Parameters:
        -----------
        user_item_matrix : scipy.sparse matrix (n_users x n_items)
            User-item interaction matrix
        """
        print(f"   Training item-based CF (k={self.k_neighbors})...")

        self.user_item_matrix = user_item_matrix
        self.n_users, self.n_items = user_item_matrix.shape

        # Transpose to get item-user matrix
        item_user_matrix = user_item_matrix.T.tocsr()

        # Compute item-item similarity using cosine similarity
        print(f"   Computing item-item similarity...")
        start = time.time()

        # For large matrices, compute in batches
        batch_size = 1000
        self.item_similarity = lil_matrix((self.n_items, self.n_items), dtype=np.float32)

        for i in range(0, self.n_items, batch_size):
            end_i = min(i + batch_size, self.n_items)
            batch = item_user_matrix[i:end_i].toarray()

            # Compute similarity with all items
            sim = cosine_similarity(batch, item_user_matrix.toarray())

            # Keep only top-k similar items per item
            for j, item_idx in enumerate(range(i, end_i)):
                # Get top-k neighbors (excluding self)
                sim_scores = sim[j]
                sim_scores[item_idx] = 0  # Exclude self

                top_k_indices = np.argsort(sim_scores)[::-1][:self.k_neighbors]

                for idx in top_k_indices:
                    if sim_scores[idx] > 0:
                        self.item_similarity[item_idx, idx] = sim_scores[idx]

        self.item_similarity = self.item_similarity.tocsr()

        print(f"   Similarity computed in {time.time() - start:.1f}s")
        print(f"   Avg neighbors per item: {self.item_similarity.nnz / self.n_items:.1f}")

        return self

    def predict(self, user_idx, item_idx):
        """
        Predict rating for user-item pair

        Score = weighted sum of user's ratings on similar items
        """
        # Get items user has interacted with
        user_items = self.user_item_matrix[user_idx].nonzero()[1]

        if len(user_items) == 0:
            return 0.0

        # Get similarities between target item and user's items
        similarities = self.item_similarity[item_idx, user_items].toarray().flatten()

        # Weighted average
        if similarities.sum() == 0:
            return 0.0

        # User's ratings on those items
        ratings = self.user_item_matrix[user_idx, user_items].toarray().flatten()

        score = (similarities * ratings).sum() / similarities.sum()
        return score

    def recommend(self, user_idx, n_recommendations=10, exclude_items=None):
        """
        Generate recommendations for a user

        For each candidate item:
          Score = sum of similarities to items user has interacted with
        """
        # Get items user has interacted with
        user_items = self.user_item_matrix[user_idx].nonzero()[1]

        if len(user_items) == 0:
            return []

        # Get all items similar to user's items
        # Score for item j = sum of similarity(j, i) for all i in user's items
        scores = np.zeros(self.n_items)

        for user_item in user_items:
            # Get similar items and their similarities
            similar_items = self.item_similarity[user_item].nonzero()[1]
            similarities = self.item_similarity[user_item, similar_items].toarray().flatten()

            # Add to scores
            scores[similar_items] += similarities

        # Exclude items user has already interacted with
        if exclude_items is not None:
            scores[exclude_items] = -np.inf

        # Get top-N items
        top_items = np.argsort(scores)[::-1][:n_recommendations]

        return [(int(item_idx), float(scores[item_idx])) for item_idx in top_items]


class BPR_MF:
    """
    Bayesian Personalized Ranking Matrix Factorization

    Optimized for implicit feedback (clicks, views, etc.)
    Instead of predicting ratings, learns to RANK items correctly

    Key idea: For each user, items they interacted with should rank
              higher than items they didn't interact with
    """

    def __init__(self, n_factors=50, learning_rate=0.01, reg=0.01, n_iterations=50):
        """
        Initialize BPR-MF model

        Parameters:
        -----------
        n_factors : int
            Number of latent factors
        learning_rate : float
            Learning rate for SGD
        reg : float
            Regularization parameter
        n_iterations : int
            Number of training iterations
        """
        self.n_factors = n_factors
        self.learning_rate = learning_rate
        self.reg = reg
        self.n_iterations = n_iterations

        self.user_factors = None
        self.item_factors = None
        self.n_users = 0
        self.n_items = 0

    def fit(self, user_item_matrix):
        """
        Train BPR model using stochastic gradient descent

        Parameters:
        -----------
        user_item_matrix : scipy.sparse matrix
            User-item interaction matrix (binary: 1=interacted, 0=not)
        """
        print(f"   Training BPR (factors={self.n_factors}, iters={self.n_iterations})...")

        self.n_users, self.n_items = user_item_matrix.shape

        # Initialize factors
        self.user_factors = np.random.normal(0, 0.01, (self.n_users, self.n_factors)).astype(np.float32)
        self.item_factors = np.random.normal(0, 0.01, (self.n_items, self.n_factors)).astype(np.float32)

        # Convert to LIL for efficient access
        user_item_lil = user_item_matrix.tolil()

        # Create user -> positive items mapping
        user_positive_items = {}
        for user_idx in range(self.n_users):
            positive_items = user_item_lil.rows[user_idx]
            if len(positive_items) > 0:
                user_positive_items[user_idx] = set(positive_items)

        all_items = set(range(self.n_items))

        # Training
        start = time.time()

        for iteration in range(self.n_iterations):
            # Sample triplets (user, positive_item, negative_item)
            losses = []

            for _ in range(len(user_positive_items) * 10):  # Sample 10x number of users
                # Random user with interactions
                user_idx = random.choice(list(user_positive_items.keys()))

                # Random positive item for this user
                pos_item = random.choice(list(user_positive_items[user_idx]))

                # Random negative item (not in user's interactions)
                negative_items = all_items - user_positive_items[user_idx]
                if len(negative_items) == 0:
                    continue
                neg_item = random.choice(list(negative_items))

                # Compute scores
                pos_score = np.dot(self.user_factors[user_idx], self.item_factors[pos_item])
                neg_score = np.dot(self.user_factors[user_idx], self.item_factors[neg_item])

                # BPR loss: want pos_score > neg_score
                # Loss = -ln(sigmoid(pos_score - neg_score))
                diff = pos_score - neg_score
                sigmoid = 1.0 / (1.0 + np.exp(-diff))
                loss = -np.log(sigmoid + 1e-10)
                losses.append(loss)

                # Gradients
                grad_factor = (1 - sigmoid)

                # Update user factors
                user_grad = grad_factor * (self.item_factors[pos_item] - self.item_factors[neg_item]) - self.reg * self.user_factors[user_idx]
                self.user_factors[user_idx] += self.learning_rate * user_grad

                # Update positive item factors
                pos_item_grad = grad_factor * self.user_factors[user_idx] - self.reg * self.item_factors[pos_item]
                self.item_factors[pos_item] += self.learning_rate * pos_item_grad

                # Update negative item factors
                neg_item_grad = -grad_factor * self.user_factors[user_idx] - self.reg * self.item_factors[neg_item]
                self.item_factors[neg_item] += self.learning_rate * neg_item_grad

            if (iteration + 1) % 10 == 0:
                avg_loss = np.mean(losses)
                print(f"   Iteration {iteration + 1}/{self.n_iterations}, Loss: {avg_loss:.4f}")

        print(f"   Training completed in {time.time() - start:.1f}s")

        return self

    def predict(self, user_idx, item_idx):
        """Predict score for user-item pair"""
        score = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        return float(score)

    def recommend(self, user_idx, n_recommendations=10, exclude_items=None):
        """Generate top-N recommendations"""
        # Compute scores for all items
        scores = self.user_factors[user_idx].dot(self.item_factors.T)

        # Exclude already consumed items
        if exclude_items is not None:
            scores[exclude_items] = -np.inf

        # Get top-N items
        top_items = np.argsort(scores)[::-1][:n_recommendations]

        return [(int(item_idx), float(scores[item_idx])) for item_idx in top_items]


def evaluate_model(model, test_interactions, train_interactions, model_name='Model', k=10):
    """
    Evaluate a recommendation model
    """
    print(f"\n   Evaluating {model_name}...")

    ndcg_scores = []
    precision_scores = []
    recall_scores = []
    hit_count = 0
    total_count = 0

    for user_idx in range(len(test_interactions)):
        test_items = set(test_interactions[user_idx])
        train_items = train_interactions[user_idx]

        if len(test_items) == 0:
            continue

        total_count += 1

        try:
            # Get recommendations
            recs = model.recommend(user_idx, k, exclude_items=train_items)
            recommended_items = [item for item, score in recs]

            if len(recommended_items) == 0:
                continue

            # Check hits
            hits = len(set(recommended_items) & test_items)
            if hits > 0:
                hit_count += 1

            # NDCG
            dcg = sum(1.0 / np.log2(i + 2) for i, item in enumerate(recommended_items) if item in test_items)
            idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(test_items), k)))
            if idcg > 0:
                ndcg_scores.append(dcg / idcg)

            # Precision & Recall
            precision = hits / k if k > 0 else 0.0
            recall = hits / len(test_items) if len(test_items) > 0 else 0.0
            precision_scores.append(precision)
            recall_scores.append(recall)

        except Exception as e:
            continue

    hit_rate = hit_count / total_count if total_count > 0 else 0.0

    return {
        'ndcg@k': np.mean(ndcg_scores) if ndcg_scores else 0.0,
        'precision@k': np.mean(precision_scores) if precision_scores else 0.0,
        'recall@k': np.mean(recall_scores) if recall_scores else 0.0,
        'hit_rate': hit_rate,
        'n_evaluated': total_count
    }


def main():
    """
    Compare advanced CF approaches
    """
    print("="*70)
    print("Advanced CF: Item-based CF vs BPR-MF")
    print("="*70)

    # Load data (reuse from hybrid_fixed)
    print("\n1. Loading data...")
    from hybrid_fixed import FixedDataLoader

    loader = FixedDataLoader(data_dir='data-cite')
    interactions, item_to_idx, idx_to_item = loader.load_and_filter_data(
        min_user_items=10,
        min_item_users=5
    )

    n_users = len(interactions)
    n_items = len(item_to_idx)

    # Train/test split
    print("\n2. Creating train/test split...")
    train_interactions, test_interactions = loader.create_global_train_test_split(
        interactions, test_ratio=0.2
    )

    # Create interaction matrix (NO negative sampling for item-based and BPR)
    print("\n3. Creating user-item matrix...")
    train_matrix = lil_matrix((n_users, n_items), dtype=np.float32)
    for user_idx, items in enumerate(train_interactions):
        for item_idx in items:
            train_matrix[user_idx, item_idx] = 1.0
    train_matrix = train_matrix.tocsr()

    print(f"   Non-zero interactions: {train_matrix.nnz}")

    # Train models
    print("\n4. Training models...")

    # Item-based CF
    print("\n   a) Item-based CF:")
    item_cf = ItemBasedCF(k_neighbors=20)
    item_cf.fit(train_matrix)

    # BPR-MF
    print("\n   b) BPR-MF:")
    bpr_model = BPR_MF(
        n_factors=50,
        learning_rate=0.05,
        reg=0.01,
        n_iterations=30
    )
    bpr_model.fit(train_matrix)

    # Evaluate
    print("\n5. Evaluating models...")

    item_cf_metrics = evaluate_model(item_cf, test_interactions, train_interactions, 'Item-based CF', k=10)
    bpr_metrics = evaluate_model(bpr_model, test_interactions, train_interactions, 'BPR-MF', k=10)

    # Print results
    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    print(f"\n{'Model':<20} {'NDCG@10':<12} {'Precision@10':<15} {'Recall@10':<12} {'Hit Rate@10':<12}")
    print("-"*70)
    print(f"{'Item-based CF':<20} {item_cf_metrics['ndcg@k']:<12.4f} {item_cf_metrics['precision@k']:<15.4f} {item_cf_metrics['recall@k']:<12.4f} {item_cf_metrics['hit_rate']:<12.4f}")
    print(f"{'BPR-MF':<20} {bpr_metrics['ndcg@k']:<12.4f} {bpr_metrics['precision@k']:<15.4f} {bpr_metrics['recall@k']:<12.4f} {bpr_metrics['hit_rate']:<12.4f}")

    # Previous results for comparison
    print("\n" + "="*70)
    print("COMPARISON WITH PREVIOUS APPROACHES")
    print("="*70)
    print("\nFrom hybrid_fixed.py:")
    print("  User-based CF (ALS): NDCG@10 = 0.0206, Hit Rate = 0.1156")
    print("  Content-based:       NDCG@10 = 0.0516, Hit Rate = 0.2273")
    print("\nCurrent:")
    print(f"  Item-based CF:       NDCG@10 = {item_cf_metrics['ndcg@k']:.4f}, Hit Rate = {item_cf_metrics['hit_rate']:.4f}")
    print(f"  BPR-MF:              NDCG@10 = {bpr_metrics['ndcg@k']:.4f}, Hit Rate = {bpr_metrics['hit_rate']:.4f}")

    # Analysis
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    best_model = 'Item-based CF' if item_cf_metrics['ndcg@k'] > bpr_metrics['ndcg@k'] else 'BPR-MF'
    best_score = max(item_cf_metrics['ndcg@k'], bpr_metrics['ndcg@k'])

    print(f"\n✓ Best performing model: {best_model} (NDCG@10 = {best_score:.4f})")

    if item_cf_metrics['ndcg@k'] > 0.0206:
        improvement = item_cf_metrics['ndcg@k'] / 0.0206
        print(f"✓ Item-based CF beats user-based CF by {improvement:.1f}x!")
        print("  → Item-item similarity works better for this sparse data")

    if bpr_metrics['ndcg@k'] > 0.0206:
        improvement = bpr_metrics['ndcg@k'] / 0.0206
        print(f"✓ BPR-MF beats user-based CF (ALS) by {improvement:.1f}x!")
        print("  → Ranking-optimized loss works better than rating prediction")

    if best_score > 0.0516:
        print(f"✓ {best_model} even beats content-based!")
        print("  → Collaborative signal is now working!")
    else:
        print("✗ Content-based still winning")
        print("  → Consider hybrid: combine content + collaborative")

    if item_cf_metrics['hit_rate'] > 0.2:
        print(f"✓ Item-based CF hit rate = {item_cf_metrics['hit_rate']:.1%}")
        print("  → Getting good recommendations for >20% of users!")

    # Save best model
    print("\n6. Saving best model...")
    import pickle

    # Ensure models directory exists
    models_dir = os.path.join('backend', 'src', 'models')
    os.makedirs(models_dir, exist_ok=True)

    if item_cf_metrics['ndcg@k'] >= bpr_metrics['ndcg@k']:
        model_path = os.path.join(models_dir, 'best_model_item_cf.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(item_cf, f)
        print(f"   Saved: {model_path}")
    else:
        model_path = os.path.join(models_dir, 'best_model_bpr.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(bpr_model, f)
        print(f"   Saved: {model_path}")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()