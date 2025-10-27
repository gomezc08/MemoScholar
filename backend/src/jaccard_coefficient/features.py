import re
from typing import Optional, Set, List, Dict
from datetime import datetime, timezone

_STOP = {
    "a","an","the","and","or","but","if","then","else","for","to","of","in","on","by","with",
    "from","into","at","is","are","was","were","be","been","being","as","it","this","that",
    "these","those","we","you","they","he","she","i","me","my","our","your","their","them",
    "about","over","under","between","within","without","than","so","do","does","did","done",
    "can","could","should","would","may","might","will","just","not","no","yes"
}
_WORD_RE = re.compile(r"[a-z0-9]+")

def _tokenize(text: str) -> List[str]:
    """Extract meaningful tokens from text for feature generation"""
    if not text:
        return []
    text = text.lower()
    toks = _WORD_RE.findall(text)
    return [t for t in toks if len(t) > 2 and t not in _STOP]

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
    where category is one of: 'dur', 'fresh', 'pop', 'type', 'tok', 'kp', 'emb'
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
    def tokenize(text: str) -> List[str]:
        """Extract tokens for feature generation"""
        return _tokenize(text)
    
    @staticmethod
    def video_features(
        seconds: Optional[int],
        published_at: Optional[datetime],
        views: Optional[int],
        sem_score: Optional[float],
        text_content: Optional[str]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a video.
        Returns list of (category, feature) tuples.
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
        
        # Text tokens feature
        if text_content:
            tokens = _tokenize(text_content)
            for tok in tokens:
                features.append(('tok', tok))
        
        # Semantic similarity feature
        sem = Features.sem_bucket(sem_score)
        if sem:
            features.append(('emb', sem))
        
        return features
    
    @staticmethod
    def project_features(
        topic: Optional[str],
        objective: Optional[str],
        guidelines: Optional[str],
        queries_text: Optional[str],
        special_instructions: Optional[str],
        sem_score: Optional[float]
    ) -> List[tuple[str, str]]:
        """
        Generate features for a project.
        Returns list of (category, feature) tuples.
        """
        features = []
        
        # Combine all text content
        text_content = " ".join([
            topic or "",
            objective or "",
            guidelines or "",
            queries_text or "",
            special_instructions or ""
        ])
        
        # Text tokens
        tokens = _tokenize(text_content)
        for tok in tokens:
            features.append(('tok', tok))
        
        # Semantic similarity feature
        sem = Features.sem_bucket(sem_score)
        if sem:
            features.append(('emb', sem))
        
        return features
