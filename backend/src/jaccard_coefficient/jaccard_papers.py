# src/recs/jaccard_papers.py
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

def _normalize_author(name: str) -> Optional[str]:
    if not name: return None
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("_")
    return name or None

def _year_2yr_bucket(year: Optional[int]) -> Optional[str]:
    if not year: return None
    start = year - (year % 2)
    end = start + 1
    return f"year:{start}-{end}"

def _jaccard(A: Set[str], B: Set[str]) -> float:
    if not A or not B: return 0.0
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0

@dataclass
class ScoredItem:
    paper_id: int
    title: str
    url: Optional[str]
    score: float

class JaccardPaperRecommender:
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
            self._upsert_all_paper_features()
        else:
            self._upsert_project_features(project_id)
            self._upsert_paper_features(project_id)

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True) -> List[ScoredItem]:
        proj_feats = self._load_project_feature_set(project_id, include_likes=include_likes)
        pp_rows = self._fetch_paper_candidates(project_id)

        scored: List[ScoredItem] = []
        for p in pp_rows:
            # p format: (paper_id, paper_title, pdf_link)
            feats = self._load_item_feature_set("paper", p[0])  # p[0] is paper_id
            s = _jaccard(proj_feats, feats)
            scored.append(ScoredItem(paper_id=p[0], title=p[1], url=p[2], score=s))  # p[1] is paper_title, p[2] is pdf_link

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

    def _paper_features_from_row(self, row: Tuple, authors: List[str]) -> Set[str]:
        # row format: (paper_id, project_id, paper_title, paper_summary, published_year, pdf_link)
        feats = set()
        text = f"{row[2] or ''} {row[3] or ''}"  # paper_title, paper_summary
        feats |= {f"tok:{t}" for t in _tokenize(text)}
        for a in authors:
            na = _normalize_author(a)
            if na: feats.add(f"author:{na}")
        yb = _year_2yr_bucket(row[4])  # published_year
        if yb: feats.add(yb)
        feats.add("type:paper")
        return feats

    def _upsert_paper_features(self, project_id: Optional[int] = None) -> None:
        cur = self.cx.cursor
        if project_id is None:
            cur.execute("""
                SELECT paper_id, project_id, paper_title, paper_summary, published_year, pdf_link
                FROM papers
            """)
        else:
            cur.execute("""
                SELECT paper_id, project_id, paper_title, paper_summary, published_year, pdf_link
                FROM papers
                WHERE project_id = %s
            """, (project_id,))
        rows = cur.fetchall()
        for r in rows:
            cur.execute("""
                SELECT a.name
                FROM paperauthors pa
                JOIN authors a ON a.author_id = pa.author_id
                WHERE pa.paper_id = %s
            """, (r[0],))  # r[0] is paper_id
            authors = [row[0] for row in cur.fetchall()]  # row[0] is name
            feats = self._paper_features_from_row(r, authors)

            cur.execute("DELETE FROM item_features WHERE target_type='paper' AND target_id=%s", (r[0],))  # r[0] is paper_id
            if feats:
                cur.executemany(
                    "INSERT INTO item_features(target_type, target_id, feature) VALUES (%s,%s,%s)",
                    [("paper", r[0], f) for f in feats]  # r[0] is paper_id
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
                if lk[0] != "paper":  # lk[0] is target_type, papers recommender uses only paper likes
                    continue
                cur.execute("""
                    SELECT feature FROM item_features
                    WHERE target_type='paper' AND target_id=%s
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

    def _fetch_paper_candidates(self, project_id: int) -> List[Tuple]:
        cur = self.cx.cursor
        cur.execute("""
            SELECT paper_id, paper_title, pdf_link
            FROM papers
            WHERE project_id = %s
        """, (project_id,))
        return cur.fetchall()
