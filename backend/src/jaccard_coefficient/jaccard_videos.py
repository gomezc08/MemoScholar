# src/recs/jaccard_videos.py
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple

from src.db.connector import Connector

_STOP = {
    "a","an","the","and","or","but","if","then","else","for","to","of","in","on","by","with",
    "from","into","at","is","are","was","were","be","been","being","as","it","this","that",
    "these","those","we","you","they","he","she","i","me","my","our","your","their","them",
    "about","over","under","between","within","without","than","so","do","does","did","done",
    "can","could","should","would","may","might","will","just","not","no","yes"
}
_WORD_RE = re.compile(r"[a-z0-9]+")

def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    toks = _WORD_RE.findall(text)
    return [t for t in toks if len(t) > 2 and t not in _STOP]

def _dur_bucket(seconds: Optional[int]) -> Optional[str]:
    if seconds is None: return None
    if seconds <  5*60: return "dur:xs"
    if seconds < 10*60: return "dur:s"
    if seconds < 20*60: return "dur:m"
    if seconds < 40*60: return "dur:l"
    return "dur:xl"

def _log_bucket(n: Optional[int], prefix: str) -> Optional[str]:
    if n is None: return None
    if n >= 10_000_000: return f"{prefix}:1e7+"
    if n >=  1_000_000: return f"{prefix}:1e6+"
    if n >=    100_000: return f"{prefix}:1e5+"
    if n >=     10_000: return f"{prefix}:1e4+"
    if n >=      1_000: return f"{prefix}:1e3+"
    return None

def _jaccard(A: Set[str], B: Set[str]) -> float:
    if not A or not B: return 0.0
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0

@dataclass
class ScoredItem:
    youtube_id: int
    title: str
    url: Optional[str]
    score: float

class JaccardVideoRecommender:
    """
    Public API:
      - update_features(project_id: Optional[int] = None) -> None
      - recommend(project_id: int, topk: int = 5, include_likes: bool = True) -> List[ScoredItem]
    """
    def __init__(self, connector: Connector):
        self.cx = connector
        if self.cx.cursor is None:
            self.cx.open_connection()

    # ---------------- Public methods ----------------

    def update_features(self, project_id: Optional[int] = None) -> None:
        self._ensure_tables()
        if project_id is None:
            self._upsert_all_project_features()
            self._upsert_all_youtube_features()
        else:
            self._upsert_project_features(project_id)
            self._upsert_youtube_features(project_id)

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True) -> List[ScoredItem]:
        proj_feats = self._load_project_feature_set(project_id, include_likes=include_likes)
        yt_rows = self._fetch_youtube_candidates(project_id)

        scored: List[ScoredItem] = []
        for y in yt_rows:
            # y format: (youtube_id, video_title, video_url)
            feats = self._load_item_feature_set("youtube", y[0])  # y[0] is youtube_id
            s = _jaccard(proj_feats, feats)
            scored.append(ScoredItem(youtube_id=y[0], title=y[1], url=y[2], score=s))  # y[1] is video_title, y[2] is video_url

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:topk]

    # ---------------- Private helpers ----------------

    def _ensure_tables(self) -> None:
        cur = self.cx.cursor
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS project_features (
                  project_id INT NOT NULL,
                  feature TEXT NOT NULL,
                  FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE
                )
            """)
        except Exception:
            # Table might already exist, ignore the error
            pass
        
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_project_features_project ON project_features(project_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_project_features_feature  ON project_features(feature)")
        except Exception:
            # Older MySQL variants don't support IF NOT EXISTS on CREATE INDEX
            pass

        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS item_features (
                  target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('youtube','paper')),
                  target_id INT NOT NULL,
                  feature TEXT NOT NULL
                )
            """)
        except Exception:
            # Table might already exist, ignore the error
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_item_features_target ON item_features(target_type, target_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_item_features_feature ON item_features(feature)")
        except Exception:
            pass
        self.cx.cnx.commit()

    def _project_row_with_latest_query(self, project_id: int) -> Optional[Tuple]:
        cur = self.cx.cursor
        cur.execute("""
            SELECT p.project_id, p.topic, p.objective, p.guidelines,
                   q.queries_text, q.special_instructions
            FROM project p
            LEFT JOIN (
                SELECT project_id, queries_text, special_instructions
                FROM queries
                WHERE project_id = %s
                ORDER BY query_id DESC
                LIMIT 1
            ) q ON q.project_id = p.project_id
            WHERE p.project_id = %s
        """, (project_id, project_id))
        rows = cur.fetchall()
        return rows[0] if rows else None

    def _project_features_from_row(self, row: Tuple) -> Set[str]:
        # row format: (project_id, topic, objective, guidelines, queries_text, special_instructions)
        txt = " ".join([
            row[1] or "",  # topic
            row[2] or "",  # objective
            row[3] or "",  # guidelines
            row[4] or "",  # queries_text
            row[5] or "",  # special_instructions
        ])
        feats = {f"qtok:{t}" for t in _tokenize(txt)}
        low = txt.lower()
        if re.search(r"\bshort\b", low): feats.add("pref:dur_short")
        if re.search(r"\brecent\b|\bnew\b|\b202[3-9]\b", low): feats.add("pref:rec_new")
        return feats

    def _upsert_project_features(self, project_id: int) -> None:
        row = self._project_row_with_latest_query(project_id)
        if not row:
            return
        feats = self._project_features_from_row(row)
        cur = self.cx.cursor
        cur.execute("DELETE FROM project_features WHERE project_id = %s", (project_id,))
        if feats:
            cur.executemany(
                "INSERT INTO project_features(project_id, feature) VALUES (%s, %s)",
                [(project_id, f) for f in feats]
            )
        self.cx.cnx.commit()

    def _upsert_all_project_features(self) -> None:
        cur = self.cx.cursor
        cur.execute("SELECT project_id FROM project")
        pids = [r[0] for r in cur.fetchall()]  # r[0] is project_id
        for pid in pids:
            self._upsert_project_features(pid)

    def _youtube_features_from_row(self, row: Tuple) -> Set[str]:
        # row format: (youtube_id, project_id, video_title, video_description, video_duration_sec, video_views, video_likes)
        feats = set()
        text = f"{row[2] or ''} {row[3] or ''}"  # video_title, video_description
        feats |= {f"tok:{t}" for t in _tokenize(text)}
        db = _dur_bucket(row[4])  # video_duration_sec
        if db: feats.add(db)
        vb = _log_bucket(row[5], "popv")  # video_views
        lb = _log_bucket(row[6], "popl")  # video_likes
        if vb: feats.add(vb)
        if lb: feats.add(lb)
        feats.add("type:youtube")
        return feats

    def _upsert_youtube_features(self, project_id: Optional[int] = None) -> None:
        cur = self.cx.cursor
        if project_id is None:
            cur.execute("""
                SELECT youtube_id, project_id, video_title, video_description,
                       TIME_TO_SEC(video_duration) AS video_duration_sec,
                       video_views, video_likes
                FROM youtube
            """)
        else:
            cur.execute("""
                SELECT youtube_id, project_id, video_title, video_description,
                       TIME_TO_SEC(video_duration) AS video_duration_sec,
                       video_views, video_likes
                FROM youtube
                WHERE project_id = %s
            """, (project_id,))
        rows = cur.fetchall()
        for r in rows:
            feats = self._youtube_features_from_row(r)
            cur.execute("DELETE FROM item_features WHERE target_type='youtube' AND target_id=%s", (r[0],))  # r[0] is youtube_id
            if feats:
                cur.executemany(
                    "INSERT INTO item_features(target_type, target_id, feature) VALUES (%s,%s,%s)",
                    [("youtube", r[0], f) for f in feats]  # r[0] is youtube_id
                )
        self.cx.cnx.commit()

    def _load_project_feature_set(self, project_id: int, include_likes: bool) -> Set[str]:
        cur = self.cx.cursor
        cur.execute("SELECT feature FROM project_features WHERE project_id=%s", (project_id,))
        feats = {r[0] for r in cur.fetchall()}  # r[0] is feature
        if include_likes:
            cur.execute("""
                SELECT target_type, target_id
                FROM likes
                WHERE project_id=%s AND isLiked = TRUE
            """, (project_id,))
            for lk in cur.fetchall():
                if lk[0] != "youtube":  # lk[0] is target_type, videos recommender uses only video likes
                    continue
                cur.execute("""
                    SELECT feature FROM item_features
                    WHERE target_type='youtube' AND target_id=%s
                """, (lk[1],))  # lk[1] is target_id
                feats |= {r[0] for r in cur.fetchall()}  # r[0] is feature
        return feats

    def _load_item_feature_set(self, target_type: str, target_id: int) -> Set[str]:
        cur = self.cx.cursor
        cur.execute("""
            SELECT feature FROM item_features
            WHERE target_type=%s AND target_id=%s
        """, (target_type, target_id))
        return {r[0] for r in cur.fetchall()}  # r[0] is feature

    def _fetch_youtube_candidates(self, project_id: int) -> List[Tuple]:
        cur = self.cx.cursor
        cur.execute("""
            SELECT youtube_id, video_title, video_url
            FROM youtube
            WHERE project_id = %s
        """, (project_id,))
        return cur.fetchall()