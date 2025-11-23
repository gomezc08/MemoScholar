from typing import Optional, List
from datetime import datetime, timezone
import re

def _dur_bucket(seconds: Optional[int]) -> Optional[str]:
    """Bucket duration into more granular categories"""
    if seconds is None: return None
    if seconds <= 3 * 60:     return "dur:xs"  # 0-3 min (quick clips)
    if seconds <= 10 * 60:    return "dur:s"   # 3-10 min (short)
    if seconds <= 20 * 60:    return "dur:m"   # 10-20 min (medium)
    if seconds <= 45 * 60:    return "dur:l"   # 20-45 min (long)
    return "dur:xl"                            # 45+ min (very long)

def _fresh_bucket(published_at: Optional[datetime]) -> Optional[str]:
    """Bucket freshness based on days since published"""
    if not published_at:
        return None
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    days = (now - published_at).days

    if days <= 365:
        return "fresh:1y"   # 0–1 year
    if days <= 3 * 365:
        return "fresh:3y"   # 1–3 years
    return "fresh:old"      # 3+ years

def _pop_bucket(views: Optional[int]) -> Optional[str]:
    """Bucket popularity based on view count with more granularity"""
    if views is None: return None
    if views >= 10_000_000: return "pop:viral"  # ≥ 10M (viral)
    if views >= 1_000_000:  return "pop:high"   # 1M-10M
    if views >= 100_000:    return "pop:mid"    # 100K-1M
    if views >= 10_000:     return "pop:low"    # 10K-100K
    return "pop:niche"                          # < 10K (niche)

class Features:
    """
    Feature extraction for videos. Each feature is returned as a tuple (category, feature_value)
    where category is one of: 'dur', 'fresh', 'pop', 'type', 'emb'
    
    Note: Token-based features removed to focus on semantic similarity with embeddings.
    """
    
    @staticmethod
    def dur_bucket(seconds: Optional[int]) -> Optional[str]:
        return _dur_bucket(seconds)
    
    @staticmethod
    def fresh_bucket(published_at: Optional[datetime]) -> Optional[str]:
        return _fresh_bucket(published_at)
    
    @staticmethod
    def pop_bucket(views: Optional[int]) -> Optional[str]:
        return _pop_bucket(views)
    
    @staticmethod
    def sem_bucket(score: Optional[float]) -> Optional[str]:
        """Bucket semantic similarity score with finer granularity"""
        if score is None: return None
        if score > 0.95:        return "sem:excellent"  # 0.95-1.0 (highly relevant)
        if score > 0.85:        return "sem:high"       # 0.85-0.95 (very relevant)
        if score > 0.70:        return "sem:mid"        # 0.70-0.85 (relevant)
        if score > 0.50:        return "sem:low"        # 0.50-0.70 (somewhat relevant)
        return "sem:poor"                               # <0.50 (weakly relevant)
    
    @staticmethod
    def video_features(
        seconds: Optional[int],
        published_at: Optional[datetime],
        views: Optional[int],
        sem_score: Optional[float],
        likes: Optional[int] = None
    ) -> List[tuple[str, str]]:
        """
        Generate features for a video.
        Returns list of (category, feature) tuples.
        Focuses on non-text features and semantic similarity.

        Args:
            seconds: Video duration in seconds
            published_at: Publication date
            views: View count
            sem_score: Semantic similarity score (0-1)
            likes: Like count (optional)
        """
        features = []

        # Duration feature
        dur = _dur_bucket(seconds)
        if dur:
            features.append(('dur', dur))

        # Freshness feature
        fresh = _fresh_bucket(published_at)
        if fresh:
            features.append(('fresh', fresh))

        # Popularity feature based on views
        pop = _pop_bucket(views)
        if pop:
            features.append(('pop', pop))

        # Engagement feature based on likes (if available)
        if likes is not None and views is not None and views > 0:
            # Like ratio = likes / views
            like_ratio = likes / views
            if like_ratio > 0.05:       # >5% like ratio (very engaging)
                features.append(('engage', 'engage:high'))
            elif like_ratio > 0.02:     # 2-5% (normal)
                features.append(('engage', 'engage:mid'))
            else:                       # <2% (low engagement)
                features.append(('engage', 'engage:low'))

        # Type feature (always youtube)
        features.append(('type', 'youtube'))

        # Semantic similarity feature (from embedding similarity)
        # CRITICAL: This should be computed by comparing video embedding to project embedding
        if sem_score is not None:
            sem = Features.sem_bucket(sem_score)
            if sem:
                features.append(('emb', sem))
        # Don't add default bucket if no semantic score - forces actual computation

        return features

    @staticmethod
    def project_features(
        sem_score: Optional[float]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a project.
        Returns list of (category, feature) tuples.
        Projects only need semantic similarity feature from their embedding.

        Note: This is used to represent the project's "profile" when comparing
        against candidate videos. The sem_score here would be a similarity score
        comparing the project embedding to a candidate's embedding.
        """
        features = []

        # Semantic similarity feature (from embedding)
        if sem_score is not None:
            sem = Features.sem_bucket(sem_score)
            if sem:
                features.append(('emb', sem))

        return features

    # ============ Paper Feature Extraction ============

    @staticmethod
    def year_bucket(year: Optional[int]) -> Optional[str]:
        """Bucket publication year into ranges"""
        if year is None: return None
        current_year = datetime.now().year

        if year >= current_year - 1:    return "year:2024+"   # Last 1 year
        if year >= current_year - 3:    return "year:2021-23" # 1-3 years ago
        if year >= current_year - 5:    return "year:2019-20" # 3-5 years ago
        if year >= current_year - 10:   return "year:2014-18" # 5-10 years ago
        return "year:old"                                     # 10+ years ago

    @staticmethod
    def normalize_author(name: str) -> Optional[str]:
        """Normalize author name for feature matching"""
        if not name: return None
        # Remove special characters, lowercase, replace spaces with underscores
        name = name.strip().lower()
        name = re.sub(r"[^a-z0-9\s]", "", name)
        name = re.sub(r"\s+", "_", name)
        name = name.strip("_")
        return name if name else None

    @staticmethod
    def paper_features(
        title: str,
        summary: Optional[str],
        year: Optional[int],
        authors: Optional[List[str]],
        sem_score: Optional[float]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a paper.
        Returns list of (category, feature) tuples.

        Args:
            title: Paper title
            summary: Paper summary/abstract
            year: Publication year
            authors: List of author names
            sem_score: Semantic similarity score (0-1) to project
        """
        features = []

        # Year/recency feature
        year_feat = Features.year_bucket(year)
        if year_feat:
            features.append(('year', year_feat))

        # Author features (can have multiple)
        if authors:
            for author in authors:
                norm_author = Features.normalize_author(author)
                if norm_author:
                    features.append(('author', f"author:{norm_author}"))

        # Type feature (always paper)
        features.append(('type', 'paper'))

        # Semantic similarity feature (from embedding similarity)
        if sem_score is not None:
            sem = Features.sem_bucket(sem_score)
            if sem:
                features.append(('emb', sem))

        return features
