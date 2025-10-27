from typing import Optional, List
from datetime import datetime, timezone

def _dur_bucket(seconds: Optional[int]) -> Optional[str]:
    """Bucket duration into short/medium/long"""
    if seconds is None: return None
    if seconds <= 5 * 60:     return "dur:s"   # 0–5 min
    if seconds <= 30 * 60:    return "dur:m"   # 5–30 min
    return "dur:l"                             # 30+ min

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
    """Bucket popularity based on view count"""
    if views is None: return None
    if views >= 1_000_000:  return "pop:high"   # ≥ 1e6
    if views >= 10_000:     return "pop:mid"    # 1e4–1e6
    return "pop:low"                            # < 1e4

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
        """Bucket semantic similarity score"""
        if score is None: return None
        if score > 0.90:        return "sem:high"
        if score > 0.75:        return "sem:mid"
        return "sem:low"
    
    @staticmethod
    def video_features(
        seconds: Optional[int],
        published_at: Optional[datetime],
        views: Optional[int],
        sem_score: Optional[float]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a video.
        Returns list of (category, feature) tuples.
        Focuses on non-text features and semantic similarity.
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
        
        # Popularity feature
        pop = _pop_bucket(views)
        if pop:
            features.append(('pop', pop))
        
        # Type feature (always youtube)
        features.append(('type', 'youtube'))
        
        # Semantic similarity feature (from embedding similarity)
        # If no score provided, use a default bucket to ensure comparison is possible
        if sem_score is None:
            sem = "sem:mid"  # Default to mid when no semantic score available
        else:
            sem = Features.sem_bucket(sem_score)
        
        # Always add emb feature
        if sem:
            features.append(('emb', sem))
        else:
            # Fallback if somehow sem is still None
            features.append(('emb', 'sem:mid'))
        
        return features
    
    @staticmethod
    def project_features(
        sem_score: Optional[float]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a project.
        Returns list of (category, feature) tuples.
        Projects only need semantic similarity feature from their embedding.
        """
        features = []
        
        # Semantic similarity feature (from embedding)
        # If no score provided, use a default bucket
        if sem_score is None:
            sem = "sem:mid"  # Default to mid when no semantic score available
        else:
            sem = Features.sem_bucket(sem_score)
        
        if sem:
            features.append(('emb', sem))
        
        return features
