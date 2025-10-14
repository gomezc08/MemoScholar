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
        """
        Refresh derived features for projects and persisted youtube items.
        Does not compute features for `youtube_current_recs` (computed ad-hoc when scoring).
        """
        if project_id is None:
            self._upsert_all_project_features()
            self._upsert_youtube_features(None)
        else:
            self._upsert_project_features(project_id)
            self._upsert_youtube_features(project_id)

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True, dislike_weight: float = 0.5) -> List[ScoredItem]:
        """
        Score current staged candidates in `youtube_current_recs`, update their score/rank,
        and return the top-k as `ScoredItem`s. Expects up to 15 candidates pre-staged per project.
        """
        proj_feats = self._load_project_feature_set(project_id, include_likes=include_likes)
        proj_feats = self._normalize_project_features_for_video(proj_feats)
        disliked_feats = self._load_disliked_feature_set(project_id)
        cand_rows = self._fetch_current_recs(project_id)

        scored: List[Tuple[int, str, Optional[str], float]] = []
        for r in cand_rows:
            # r format: (rec_id, video_title, video_description, video_duration_sec, video_url, video_views, video_likes)
            feats = self._youtube_features_from_rec_row(r)
            pos = _jaccard(proj_feats, feats)
            neg = _jaccard(disliked_feats, feats) if disliked_feats else 0.0
            s = max(0.0, pos - dislike_weight * neg)
            scored.append((r[0], r[1], r[4], s))

        # Persist scores and ranks
        scored_sorted = sorted(scored, key=lambda x: x[3], reverse=True)
        self._update_rec_scores_and_ranks(project_id, scored_sorted)

        # Return ScoredItem list
        result: List[ScoredItem] = []
        for rec_id, title, url, s in scored_sorted[:topk]:
            result.append(ScoredItem(youtube_id=rec_id, title=title, url=url, score=s))
        return result

    def _normalize_project_features_for_video(self, feats: Set[str]) -> Set[str]:
        """
        Map project-side text tokens (qtok:*) into the same namespace as item tokens (tok:*).
        This ensures text overlap is measured even before any likes.
        """
        norm: Set[str] = set()
        for f in feats:
            if f.startswith("qtok:"):
                norm.add("tok:" + f[len("qtok:"):])
            else:
                norm.add(f)
        return norm

    def _load_disliked_feature_set(self, project_id: int) -> Set[str]:
        """
        Aggregate features from all disliked youtube items for this project.
        """
        cur = self.cx.cursor
        cur.execute(
            """
            SELECT target_id
            FROM likes
            WHERE project_id=%s AND target_type='youtube' AND isLiked = FALSE
            """,
            (project_id,),
        )
        disliked_ids = [r[0] for r in cur.fetchall()]
        if not disliked_ids:
            return set()
        feats: Set[str] = set()
        for tid in disliked_ids:
            cur.execute(
                """
                SELECT feature FROM item_features
                WHERE target_type='youtube' AND target_id=%s
                """,
                (tid,),
            )
            feats |= {r[0] for r in cur.fetchall()}
        return feats

    def promote_topk_and_clear(self, project_id: int, topk: int = 5) -> None:
        """
        Insert the top-k ranked current recommendations into `youtube` as the shown items,
        then clear all `youtube_current_recs` for the project.
        """
        cur = self.cx.cursor
        # Select top-k by rank (computed by recommend)
        cur.execute(
            """
            SELECT rec_id, video_title, video_description, video_duration, video_url, video_views, video_likes
            FROM youtube_current_recs
            WHERE project_id=%s
            ORDER BY rank ASC NULLS LAST, score DESC
            LIMIT %s
            """,
            (project_id, topk),
        )
        top_rows = cur.fetchall()
        if top_rows:
            cur.executemany(
                """
                INSERT INTO youtube(project_id, query_id, video_title, video_description, video_duration, video_url, video_views, video_likes)
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        project_id,
                        r[1],  # title
                        r[2],  # description
                        r[3],  # duration (TIME)
                        r[4],  # url
                        r[5],  # views
                        r[6],  # likes
                    )
                    for r in top_rows
                ],
            )
        # Clear staging
        cur.execute("DELETE FROM youtube_current_recs WHERE project_id=%s", (project_id,))
        self.cx.cnx.commit()

    def restage_candidates(self, project_id: int, candidates: List[Dict]) -> None:
        """
        Replace current staged candidates for the project with the provided 15 candidates.
        Each candidate dict may contain: title, description, duration_seconds or duration_time,
        url, views, likes. Duration can be provided in seconds; it will be converted to TIME.
        """
        cur = self.cx.cursor
        cur.execute("DELETE FROM youtube_current_recs WHERE project_id=%s", (project_id,))

        def _secs_to_time(secs: Optional[int]) -> Optional[str]:
            if secs is None:
                return None
            # Format HH:MM:SS
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

        rows = []
        for c in candidates:
            title = c.get("title")
            if not title:
                # Skip invalid entries silently
                continue
            desc = c.get("description")
            url = c.get("url")
            views = c.get("views", 0)
            likes = c.get("likes", 0)
            if "duration_time" in c and c.get("duration_time") is not None:
                dur_time = c.get("duration_time")
            else:
                dur_time = _secs_to_time(c.get("duration_seconds"))
            rows.append((project_id, title, desc, dur_time, url, views, likes))

        if rows:
            cur.executemany(
                """
                INSERT INTO youtube_current_recs(project_id, video_title, video_description, video_duration, video_url, video_views, video_likes)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                rows,
            )
        self.cx.cnx.commit()

    # ---------------- Private helpers ----------------
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

    def _youtube_features_from_rec_row(self, row: Tuple) -> Set[str]:
        """
        Compute features from a `youtube_current_recs` row.
        row format: (rec_id, video_title, video_description, video_duration_sec, video_url, video_views, video_likes)
        """
        feats = set()
        text = f"{row[1] or ''} {row[2] or ''}"  # title + description
        feats |= {f"tok:{t}" for t in _tokenize(text)}
        db = _dur_bucket(row[3])  # duration seconds
        if db: feats.add(db)
        vb = _log_bucket(row[5], "popv")
        lb = _log_bucket(row[6], "popl")
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
        # Legacy: fetch existing persisted youtube items as candidates
        cur = self.cx.cursor
        cur.execute(
            """
            SELECT youtube_id, video_title, video_url
            FROM youtube
            WHERE project_id = %s
            """,
            (project_id,),
        )
        return cur.fetchall()

    def _fetch_current_recs(self, project_id: int) -> List[Tuple]:
        """
        Fetch staged candidates with duration converted to seconds for feature bucketing.
        """
        cur = self.cx.cursor
        cur.execute(
            """
            SELECT
                rec_id,
                video_title,
                video_description,
                TIME_TO_SEC(video_duration) AS video_duration_sec,
                video_url,
                video_views,
                video_likes
            FROM youtube_current_recs
            WHERE project_id=%s
            """,
            (project_id,),
        )
        return cur.fetchall()

    def _update_rec_scores_and_ranks(self, project_id: int, scored_sorted: List[Tuple[int, str, Optional[str], float]]) -> None:
        """
        Persist score and rank for current staged candidates.
        """
        cur = self.cx.cursor
        # Update score
        for rec_id, _title, _url, score in scored_sorted:
            cur.execute(
                "UPDATE youtube_current_recs SET score=%s WHERE rec_id=%s",
                (score, rec_id),
            )
        # Update rank
        for rank, (rec_id, _title, _url, _score) in enumerate(scored_sorted, start=1):
            cur.execute(
                "UPDATE youtube_current_recs SET rank_position=%s WHERE rec_id=%s",
                (rank, rec_id),
            )
        self.cx.cnx.commit()