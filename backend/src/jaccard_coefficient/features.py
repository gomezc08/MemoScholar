from typing import Optional, Set
from datetime import datetime, timezone

class Features:
    @staticmethod
    def dur_bucket(seconds: Optional[int]) -> Optional[str]:
        if seconds is None: return None
        if seconds <= 5 * 60:     return "dur:s"   # 0–5 min
        if seconds <= 30 * 60:    return "dur:m"   # 5–30 min
        return "dur:l"                             # 30+ min

    @staticmethod
    def fresh_bucket(published_at: Optional[datetime]) -> Optional[str]:
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

    @staticmethod
    def sem_bucket(score: Optional[float]) -> Optional[str]:
        if score is None: return None
        if score > 0.90:        return "sem:high"
        if score > 0.75:        return "sem:mid"
        return "sem:low"

    @staticmethod
    def pop_bucket(views: Optional[int]) -> Optional[str]:
        if views is None: return None
        if views >= 1_000_000:  return "pop:high"   # ≥ 1e6
        if views >= 10_000:     return "pop:mid"    # 1e4–1e6
        return "pop:low"                               # < 1e4

    @classmethod
    def video_features(cls,
                       seconds: Optional[int],
                       published_at: Optional[datetime.datetime],
                       views: Optional[int],
                       sem_score: Optional[float],
                       category: Optional[str]) -> Set[str]:
        feats = {
            cls.dur_bucket(seconds),
            cls.fresh_bucket(published_at),
            cls.pop_bucket(views),
            cls.sem_bucket(sem_score),
        }
        return {f for f in feats if f is not None}
