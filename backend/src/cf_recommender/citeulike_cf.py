"""
Final Hybrid Recommendation System

Combines Item-based CF and Content-based models using a Switched ensemble strategy.
Self-contained implementation that only requires the data-cite dataset.
"""

import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from collections import Counter
import random
import time
import pickle
import os


model_directory = r"backend\src\cf_recommender\data-cite"
models_directory = r"backend\src\cf_recommender\models"

class ItemBasedCF:
    """
    Item-based Collaborative Filtering

    Finds similar items based on user interactions and recommends
    items similar to those the user has already interacted with.
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
        self.user_item_matrix = user_item_matrix
        self.n_users, self.n_items = user_item_matrix.shape

        # Transpose to get item-user matrix
        item_user_matrix = user_item_matrix.T.tocsr()

        # Compute item-item similarity using cosine similarity
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

        return self

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


class ContentBased:
    """
    Content-based Recommender using item features

    Recommends items similar to those the user has previously liked
    based on item content features.
    """

    def __init__(self):
        self.item_features = None
        self.item_features_normalized = None
        self.idx_to_item = None

    def load_item_features(self, mult_file, idx_to_item, n_items):
        """
        Load features with proper index mapping

        Parameters:
        -----------
        mult_file : str
            Path to mult.dat
        idx_to_item : dict
            Mapping from our indices to original item IDs
        n_items : int
            Number of items in our filtered dataset
        """
        self.idx_to_item = idx_to_item

        # Read mult.dat - each line is one item in order (0, 1, 2, ...)
        mult_features = {}

        with open(mult_file, 'r') as f:
            for original_item_id, line in enumerate(f):
                parts = line.strip().split()
                if len(parts) < 1:
                    continue

                num_words = int(parts[0])
                features = {}

                for i in range(1, len(parts)):
                    word_id, count = parts[i].split(':')
                    features[int(word_id)] = int(count)

                mult_features[original_item_id] = features

        # Create feature matrix for our items
        max_word_id = max(
            max(features.keys()) if features else 0
            for features in mult_features.values() if features
        )
        n_features = max_word_id + 1

        self.item_features = lil_matrix((n_items, n_features), dtype=np.float32)

        items_with_features = 0
        for our_idx in range(n_items):
            original_item_id = idx_to_item[our_idx]

            if original_item_id in mult_features:
                features = mult_features[original_item_id]
                for word_id, count in features.items():
                    self.item_features[our_idx, word_id] = count
                items_with_features += 1

        self.item_features = self.item_features.tocsr()
        self.item_features_normalized = normalize(self.item_features, norm='l2', axis=1)

        return self

    def get_user_profile(self, user_items):
        """Create user profile from items"""
        if len(user_items) == 0:
            return np.zeros(self.item_features_normalized.shape[1])

        user_profile = self.item_features_normalized[user_items].mean(axis=0)
        return np.asarray(user_profile).flatten()

    def recommend(self, user_items, n_recommendations=10, exclude_items=None):
        """Generate content-based recommendations"""
        if len(user_items) == 0:
            return []

        user_profile = self.get_user_profile(user_items)
        scores = self.item_features_normalized.dot(user_profile)

        if exclude_items is not None:
            scores[exclude_items] = -np.inf

        top_items = np.argsort(scores)[::-1][:n_recommendations]
        return [(int(item_idx), float(scores[item_idx])) for item_idx in top_items]


class SwitchedEnsemble:
    """
    Switched Ensemble Recommender

    Combines multiple recommenders using weighted score aggregation.
    Each model's scores are normalized and weighted, then combined.
    """

    def __init__(self, item_cf_model=None, content_model=None,
                 cf_weight=0.7, content_weight=0.3):
        """
        Initialize switched ensemble

        Parameters:
        -----------
        item_cf_model : ItemBasedCF
            Item-based collaborative filtering model
        content_model : ContentBased
            Content-based model
        cf_weight : float
            Weight for collaborative filtering (default: 0.7)
        content_weight : float
            Weight for content-based (default: 0.3)
        """
        self.item_cf = item_cf_model
        self.content = content_model
        self.cf_weight = cf_weight
        self.content_weight = content_weight

    def recommend(self, user_idx, user_items, n_recommendations=10, exclude_items=None):
        """
        Generate recommendations using weighted score combination

        Parameters:
        -----------
        user_idx : int
            User index for CF model
        user_items : list
            List of items user has interacted with (for CB model)
        n_recommendations : int
            Number of recommendations to return
        exclude_items : list
            Items to exclude from recommendations

        Returns:
        --------
        List of (item_id, score) tuples
        """
        all_scores = {}

        # Get CF recommendations
        try:
            cf_recs = self.item_cf.recommend(user_idx, n_recommendations * 3, exclude_items)

            for item, score in cf_recs:
                # Normalize scores to 0-1 range
                normalized_score = score / (abs(score) + 1) if score != 0 else 0
                all_scores[item] = self.cf_weight * normalized_score
        except Exception as e:
            pass

        # Get CB recommendations
        try:
            cb_recs = self.content.recommend(user_items, n_recommendations * 3, exclude_items)

            for item, score in cb_recs:
                # Normalize scores to 0-1 range
                normalized_score = score / (abs(score) + 1) if score != 0 else 0

                if item not in all_scores:
                    all_scores[item] = 0.0
                all_scores[item] += self.content_weight * normalized_score
        except Exception as e:
            pass

        # Sort by combined score
        sorted_items = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_items[:n_recommendations]


def load_and_filter_data(data_dir=model_directory, min_user_items=10, min_item_users=5):
    """
    Load and filter data

    Parameters:
    -----------
    data_dir : str
        Path to data directory
    min_user_items : int
        Minimum items per user
    min_item_users : int
        Minimum users per item

    Returns:
    --------
    interactions : list of lists
        User-item interactions
    item_to_idx : dict
        Mapping from original item IDs to our indices
    idx_to_item : dict
        Mapping from our indices to original item IDs
    """
    users_file = f"{data_dir}/users.dat"

    # Load all data
    interactions = []
    with open(users_file, 'r') as f:
        for line in f:
            items = [int(x) for x in line.strip().split()]
            interactions.append(items)

    original_users = len(interactions)

    # Filter users
    filtered_interactions = [items for items in interactions if len(items) >= min_user_items]

    # Count item frequencies
    item_counts = Counter(item for items in filtered_interactions for item in items)

    # Filter items
    valid_items = {item for item, count in item_counts.items() if count >= min_item_users}

    # Re-filter users
    final_interactions = []
    for items in filtered_interactions:
        filtered_items = [item for item in items if item in valid_items]
        if len(filtered_items) >= min_user_items:
            final_interactions.append(filtered_items)

    # Create mappings
    all_items = sorted(valid_items)
    item_to_idx = {item_id: idx for idx, item_id in enumerate(all_items)}
    idx_to_item = {idx: item_id for item_id, idx in item_to_idx.items()}

    # Convert to indices
    interactions_idx = []
    for items in final_interactions:
        interactions_idx.append([item_to_idx[item] for item in items])

    return interactions_idx, item_to_idx, idx_to_item


def create_train_test_split(interactions, test_ratio=0.2):
    """
    Create train/test split

    Parameters:
    -----------
    interactions : list of lists
        User-item interactions
    test_ratio : float
        Ratio of interactions to put in test

    Returns:
    --------
    train_interactions : list of lists
    test_interactions : list of lists
    """
    random.seed(42)

    train_interactions = []
    test_interactions = []

    total_train = 0
    total_test = 0

    for user_idx, items in enumerate(interactions):
        # Shuffle items
        items_shuffled = items.copy()
        random.shuffle(items_shuffled)

        # Randomly assign each item to train or test
        train_items = []
        test_items = []

        for item in items_shuffled:
            if random.random() < test_ratio:
                test_items.append(item)
            else:
                train_items.append(item)

        # Ensure at least 1 item in each set
        if len(train_items) == 0:
            train_items = [test_items.pop()]
        if len(test_items) == 0 and len(train_items) > 1:
            test_items = [train_items.pop()]

        train_interactions.append(train_items)
        test_interactions.append(test_items)

        total_train += len(train_items)
        total_test += len(test_items)

    return train_interactions, test_interactions


def evaluate_model(model, test_interactions, train_interactions, name='Model', k=10, is_ensemble=False):
    """
    Evaluate a recommendation model

    Parameters:
    -----------
    model : Recommender model
        Model to evaluate
    test_interactions : list of lists
        Test interactions
    train_interactions : list of lists
        Training interactions
    name : str
        Model name for display
    k : int
        Number of recommendations
    is_ensemble : bool
        Whether the model is an ensemble (needs user_items parameter)

    Returns:
    --------
    dict : Evaluation metrics
    """
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
            if is_ensemble:
                recs = model.recommend(user_idx, train_items, k, exclude_items=train_items)
            else:
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
        'hit_rate': hit_rate
    }


def evaluate_content_model(model, test_interactions, train_interactions, name='Content-based', k=10):
    """
    Evaluate content-based model (needs user_items instead of user_idx)
    """
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
            # Get recommendations using train_items
            recs = model.recommend(train_items, k, exclude_items=train_items)
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
        'hit_rate': hit_rate
    }


def main():
    """
    Main function to train and evaluate the hybrid recommendation system
    """
    # 1. Load data
    interactions, item_to_idx, idx_to_item = load_and_filter_data(
        data_dir=model_directory,
        min_user_items=10,
        min_item_users=5
    )

    n_users = len(interactions)
    n_items = len(item_to_idx)

    # 2. Train/test split
    train_interactions, test_interactions = create_train_test_split(
        interactions, test_ratio=0.2
    )

    # 3. Create user-item matrix
    train_matrix = lil_matrix((n_users, n_items), dtype=np.float32)
    for user_idx, items in enumerate(train_interactions):
        for item_idx in items:
            train_matrix[user_idx, item_idx] = 1.0
    train_matrix = train_matrix.tocsr()

    # 4. Train models
    # Train Item-based CF
    item_cf = ItemBasedCF(k_neighbors=20)
    item_cf.fit(train_matrix)

    # Train Content-based
    cb_model = ContentBased()
    cb_model.load_item_features(model_directory + '/mult.dat', idx_to_item, n_items)

    # Create Switched Ensemble
    switched_ensemble = SwitchedEnsemble(
        item_cf_model=item_cf,
        content_model=cb_model,
        cf_weight=0.7,
        content_weight=0.3
    )

    # 5. Evaluate
    item_cf_metrics = evaluate_model(
        item_cf, test_interactions, train_interactions,
        'Item-based CF', k=10
    )

    cb_metrics = evaluate_content_model(
        cb_model, test_interactions, train_interactions,
        'Content-based', k=10
    )

    switched_metrics = evaluate_model(
        switched_ensemble, test_interactions, train_interactions,
        'Switched Ensemble', k=10, is_ensemble=True
    )

    # 6. Print results
    print("="*70)
    print("RESULTS")
    print("="*70)
    print(f"\n{'Model':<25} {'NDCG@10':<12} {'Precision@10':<15} {'Recall@10':<12} {'Hit Rate@10':<12}")
    print("-"*70)
    print("Individual Models:")
    print(f"{'  Item-based CF':<25} {item_cf_metrics['ndcg@k']:<12.4f} {item_cf_metrics['precision@k']:<15.4f} {item_cf_metrics['recall@k']:<12.4f} {item_cf_metrics['hit_rate']:<12.4f}")
    print(f"{'  Content-based':<25} {cb_metrics['ndcg@k']:<12.4f} {cb_metrics['precision@k']:<15.4f} {cb_metrics['recall@k']:<12.4f} {cb_metrics['hit_rate']:<12.4f}")
    print()
    print("Ensembles:")
    print(f"{'  Switched':<25} {switched_metrics['ndcg@k']:<12.4f} {switched_metrics['precision@k']:<15.4f} {switched_metrics['recall@k']:<12.4f} {switched_metrics['hit_rate']:<12.4f}")
    print("="*70)

    # 7. Save the switched model
    # Ensure models directory exists
    os.makedirs(models_directory, exist_ok=True)

    # Save the model
    model_path = os.path.join(models_directory, 'switched_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(switched_ensemble, f)

    # Save metadata for later use
    metadata = {
        'item_to_idx': item_to_idx,
        'idx_to_item': idx_to_item,
        'n_users': n_users,
        'n_items': n_items,
        'metrics': {
            'item_cf': item_cf_metrics,
            'content_based': cb_metrics,
            'switched': switched_metrics
        }
    }

    metadata_path = os.path.join(models_directory, 'switched_model_metadata.pkl')
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)


def load_and_use_model(user_items_example=None):
    """
    Example function showing how to load and use the saved model

    Parameters:
    -----------
    user_items_example : list, optional
        Example list of item indices the user has interacted with
    """
    # Load the model
    model_path = os.path.join(models_directory, 'switched_model.pkl')
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Load metadata
    metadata_path = os.path.join(models_directory, 'switched_model_metadata.pkl')
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)

    # Example usage
    if user_items_example is not None:
        recs = model.recommend(
            user_idx=0,  # Dummy user index
            user_items=user_items_example,
            n_recommendations=10,
            exclude_items=user_items_example
        )

    return model, metadata


if __name__ == "__main__":
    main()

    # Uncomment to see example of loading and using the model:
    # load_and_use_model(user_items_example=[0, 1, 2, 3, 4])