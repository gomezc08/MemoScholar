# src/jaccard_coefficient/jaccard_videos.py
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import numpy as np

from src.db.connector import Connector
from src.db.db_crud.select_db import DBSelect
from src.text_embedding.embedding import Embedding
from src.jaccard_coefficient.features import Features

@dataclass
class ScoredItem:
    youtube_id: int
    title: str
    url: Optional[str]
    score: float

class JaccardVideoRecommender:
    """
    Recommender using weighted semantic similarity-based jaccard coefficient.
    
    J^+(P, i) = α_sem * |P^+_sem ∩ I_sem| / |P^+_sem ∪ I_sem|
              + α_len * |P^+_len ∩ I_len| / |P^+_len ∪ I_len|
              + α_fresh * |P^+_fresh ∩ I_fresh| / |P^+_fresh ∪ I_fresh|
              + α_pop * |P^+_pop ∩ I_pop| / |P^+_pop ∪ I_pop|
              + α_type * |P^+_type ∩ I_type| / |P^+_type ∪ I_type|
              + α_tok * |P^+_tok ∩ I_tok| / |P^+_tok ∪ I_tok|
    
    S(P, i) = J^+(P, i) - λ * J^-(P, i)
    
    Public API:
      - update_features(project_id: Optional[int] = None) -> None
      - recommend(project_id: int, topk: int = 5, include_likes: bool = True) -> List[Dict]
      - restage_candidates(project_id: int, candidates: List[Dict]) -> None
      - promote_topk_and_clear(project_id: int, topk: int = 5) -> None
    """
    
    # Feature category weights (alpha values)
    WEIGHTS = {
        'emb': 0.4,   # semantic similarity
        'tok': 0.3,   # text tokens
        'dur': 0.1,   # duration
        'fresh': 0.1, # freshness
        'pop': 0.05,  # popularity
        'type': 0.05  # type
    }
    
    def __init__(self, connector: Connector):
        self.cx = connector
        self.features = Features()
        self.db_select = DBSelect()
        self.embedding = Embedding()
        if self.cx.cursor is None:
            self.cx.open_connection()

    def weighted_jaccard(self, features_A: Dict[str, Set[str]], features_B: Dict[str, Set[str]]) -> float:
        """
        Calculate weighted jaccard coefficient across feature categories.
        
        Args:
            features_A: Dict mapping category -> Set of feature values
            features_B: Dict mapping category -> Set of feature values
        
        Returns:
            Weighted jaccard score
        """
        total_score = 0.0
        
        for category, weight in self.WEIGHTS.items():
            A_cat = features_A.get(category, set())
            B_cat = features_B.get(category, set())
            
            # Jaccard for this category
            intersection = len(A_cat & B_cat)
            union = len(A_cat | B_cat)
            
            if union > 0:
                jaccard = intersection / union
                total_score += weight * jaccard
        
        return total_score

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

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True, lambda_dislike: float = 0.5) -> List[Dict]:
        """
        Score current staged candidates in `youtube_current_recs`, update their score/rank,
        and return the top-k.
        """
        # Load project features (liked items + project text)
        proj_features = self._load_project_features(project_id, include_likes=include_likes)
        
        # Load disliked features
        disliked_features = self._load_disliked_features(project_id)
        
        # Fetch candidate videos
        cand_rows = self._fetch_current_recs(project_id)
        
        scored: List[Tuple[int, str, Optional[str], float]] = []
        for r in cand_rows:
            # Extract features from candidate row
            cand_features = self._extract_features_from_rec_row(r)
            
            # Calculate J^+ (positive jaccard)
            pos_score = self.weighted_jaccard(proj_features, cand_features)
            
            # Calculate J^- (negative jaccard)
            neg_score = self.weighted_jaccard(disliked_features, cand_features) if disliked_features else 0.0
            
            # Calculate final score: S(P, i) = J^+(P, i) - λ * J^-(P, i)
            final_score = max(0.0, pos_score - lambda_dislike * neg_score)
            
            # r[0] = rec_id, r[1] = video_title, r[4] = video_url
            scored.append((r[0], r[1], r[4], final_score))
        
        # Persist scores and ranks
        scored_sorted = sorted(scored, key=lambda x: x[3], reverse=True)
        self._update_rec_scores_and_ranks(project_id, scored_sorted)
        
        # Return full YouTube video details with score
        result: List[Dict] = []
        for rec_id, title, url, s in scored_sorted[:topk]:
            video_details = self.db_select.get_youtube_video_from_youtube_current_recs(rec_id)
            if video_details:
                video_details['calculated_score'] = s
                result.append(video_details)
        return result

    def promote_topk_and_clear(self, project_id: int, topk: int = 5) -> None:
        """
        Insert the top-k ranked current recommendations into `youtube` as the shown items,
        then clear all `youtube_current_recs` for the project.
        """
        cur = self.cx.cursor
        # Select top-k by rank
        cur.execute(
            """
            SELECT rec_id, video_title, video_description, video_duration, video_url, video_views, video_likes, video_embedding
            FROM youtube_current_recs
            WHERE project_id=%s
            ORDER BY rank_position ASC NULLS LAST, score DESC
            LIMIT %s
            """,
            (project_id, topk),
        )
        top_rows = cur.fetchall()
        if top_rows:
            cur.executemany(
                """
                INSERT INTO youtube(project_id, video_title, video_description, video_duration, video_url, video_views, video_likes, video_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, STRING_TO_VECTOR(%s))
                """,
                [
                    (
                        project_id,
                        r[1],  # video_title
                        r[2],  # video_description
                        r[3],  # video_duration
                        r[4],  # video_url
                        r[5],  # video_views
                        r[6],  # video_likes
                        str(r[7]) if r[7] else None  # video_embedding
                    )
                    for r in top_rows
                ],
            )
        
        # Clear staging
        cur.execute("DELETE FROM youtube_current_recs WHERE project_id=%s", (project_id,))
        
        # Clean up orphaned likes
        cleanup_query = """
            DELETE FROM likes 
            WHERE project_id = %s 
            AND target_type = 'youtube' 
            AND target_id NOT IN (
                SELECT youtube_id FROM youtube 
                WHERE project_id = %s
            )
        """
        cur.execute(cleanup_query, (project_id, project_id))
        
        self.cx.cnx.commit()

    def restage_candidates(self, project_id: int, candidates: List[Dict]) -> None:
        """
        Replace current staged candidates for the project with the provided candidates.
        Also computes and stores features in youtube_current_recs_features.
        """
        cur = self.cx.cursor
        cur.execute("DELETE FROM youtube_current_recs WHERE project_id=%s", (project_id,))
        cur.execute("DELETE FROM youtube_current_recs_features WHERE rec_id IN (SELECT rec_id FROM youtube_current_recs WHERE project_id=%s)", (project_id,))
        
        # Clean up orphaned likes
        cleanup_query = """
            DELETE FROM likes 
            WHERE project_id = %s 
            AND target_type = 'youtube' 
            AND target_id NOT IN (
                SELECT youtube_id FROM youtube 
                WHERE project_id = %s
            )
        """
        cur.execute(cleanup_query, (project_id, project_id))

        def _secs_to_time(secs: Optional[int]) -> Optional[str]:
            if secs is None:
                return None
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

        rows = []
        for c in candidates:
            title = c.get("title")
            if not title:
                continue
            desc = c.get("description", "")
            url = c.get("url")
            views = c.get("views", 0)
            likes = c.get("likes", 0)
            embedding = c.get("embedding")
            
            if "duration_time" in c and c.get("duration_time") is not None:
                dur_time = c.get("duration_time")
            else:
                dur_time = _secs_to_time(c.get("duration_seconds"))
            
            # Convert embedding to string if it's a list
            embedding_str = None
            if embedding is not None:
                if isinstance(embedding, list):
                    import json
                    embedding_str = json.dumps(embedding)
                else:
                    embedding_str = str(embedding)
            
            rows.append((project_id, title, desc, dur_time, url, views, likes, embedding_str))

        if rows:
            cur.executemany(
                """
                INSERT INTO youtube_current_recs(project_id, video_title, video_description, video_duration, video_url, video_views, video_likes, video_embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s, STRING_TO_VECTOR(%s))
                """,
                rows,
            )
            self.cx.cnx.commit()
            
            # Now compute features for each inserted candidate
            cur.execute("SELECT rec_id, TIME_TO_SEC(video_duration) AS video_duration_sec, video_views, video_likes, video_title, video_description FROM youtube_current_recs WHERE project_id=%s", (project_id,))
            recs = cur.fetchall()
            
            for rec_row in recs:
                rec_id = rec_row[0]
                duration_sec = rec_row[1]
                views = rec_row[2]
                likes = rec_row[3]
                title = rec_row[4]
                description = rec_row[5]
                
                # Generate features
                text_content = f"{title or ''} {description or ''}"
                features_list = self.features.video_features(
                    seconds=duration_sec,
                    published_at=None,
                    views=views,
                    sem_score=None,
                    text_content=text_content
                )
                
                # Insert features
                if features_list:
                    cur.executemany(
                        "INSERT INTO youtube_current_recs_features(rec_id, category, feature) VALUES (%s, %s, %s)",
                        [(rec_id, cat, feat) for cat, feat in features_list]
                    )
            
            self.cx.cnx.commit()

    # ---------------- Private helpers ---------------- 
    
    def _load_project_features(self, project_id: int, include_likes: bool) -> Dict[str, Set[str]]:
        """
        Load project features grouped by category.
        Returns Dict mapping category -> Set of feature values.
        """
        cur = self.cx.cursor
        
        # Get project information
        cur.execute("""
            SELECT p.project_id, p.topic, p.objective, p.guidelines, p.embedding,
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
        
        proj_row = cur.fetchone()
        if not proj_row:
            return {cat: set() for cat in self.WEIGHTS.keys()}
        
        # Extract features using the new Features class
        topic = proj_row[1]
        objective = proj_row[2]
        guidelines = proj_row[3]
        embedding = proj_row[4]
        queries_text = proj_row[5]
        special_instructions = proj_row[6]
        
        # Calculate semantic similarity score if embedding exists
        sem_score = None
        if embedding is not None:
            # Embedding calculation would go here
            # For now, we'll use a placeholder
            sem_score = 0.5  # Placeholder, should calculate actual similarity
        
        features_list = self.features.project_features(
            topic, objective, guidelines, queries_text, special_instructions, sem_score
        )
        
        # Organize by category
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for category, feature_value in features_list:
            features_by_category[category].add(feature_value)
        
        # Add liked videos' features
        if include_likes:
            cur.execute("""
                SELECT target_id
                FROM likes
                WHERE project_id=%s AND target_type='youtube' AND isLiked = TRUE
            """, (project_id,))
            
            for (target_id,) in cur.fetchall():
                video_features = self._get_youtube_features(target_id)
                for category, feature_set in video_features.items():
                    features_by_category[category] |= feature_set
        
        return features_by_category

    def _load_disliked_features(self, project_id: int) -> Optional[Dict[str, Set[str]]]:
        """Load features from disliked videos."""
        cur = self.cx.cursor
        cur.execute("""
            SELECT target_id
            FROM likes
            WHERE project_id=%s AND target_type='youtube' AND isLiked = FALSE
        """, (project_id,))
        
        disliked_ids = [r[0] for r in cur.fetchall()]
        if not disliked_ids:
            return None
        
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for target_id in disliked_ids:
            video_features = self._get_youtube_features(target_id)
            for category, feature_set in video_features.items():
                features_by_category[category] |= feature_set
        
        return features_by_category

    def _get_youtube_features(self, youtube_id: int) -> Dict[str, Set[str]]:
        """Get features for a youtube video from youtube_features table."""
        cur = self.cx.cursor
        cur.execute("""
            SELECT category, feature
            FROM youtube_features
            WHERE youtube_id = %s
        """, (youtube_id,))
        
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for category, feature_value in cur.fetchall():
            features_by_category[category].add(feature_value)
        
        return features_by_category

    def _extract_features_from_rec_row(self, row: Tuple) -> Dict[str, Set[str]]:
        """
        Extract features from a youtube_current_recs row.
        row format: (rec_id, video_title, video_description, video_duration_sec, video_url, video_views, video_likes, embedding)
        """
        # Fetch features from youtube_current_recs_features table
        rec_id = row[0]
        cur = self.cx.cursor
        cur.execute("""
            SELECT category, feature
            FROM youtube_current_recs_features
            WHERE rec_id = %s
        """, (rec_id,))
        
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for category, feature_value in cur.fetchall():
            features_by_category[category].add(feature_value)
        
        return features_by_category

    def _project_row_with_latest_query(self, project_id: int) -> Optional[Tuple]:
        cur = self.cx.cursor
        cur.execute("""
            SELECT p.project_id, p.topic, p.objective, p.guidelines, p.embedding,
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

    def _upsert_project_features(self, project_id: int) -> None:
        """Update project features in the database."""
        # For now, we'll store project features in a different way
        # Since the schema doesn't have a project_features table with category
        # We'll skip this for now and compute features on-the-fly
        pass

    def _upsert_all_project_features(self) -> None:
        """Update features for all projects."""
        # Similar to _upsert_project_features
        pass

    def _upsert_youtube_features(self, project_id: Optional[int] = None) -> None:
        """
        Update features for YouTube videos in the youtube_features table.
        """
        cur = self.cx.cursor
        if project_id is None:
            cur.execute("""
                SELECT youtube_id, TIME_TO_SEC(video_duration) AS video_duration_sec,
                       video_views, video_likes, video_title, video_description
                FROM youtube
            """)
        else:
            cur.execute("""
                SELECT youtube_id, TIME_TO_SEC(video_duration) AS video_duration_sec,
                       video_views, video_likes, video_title, video_description
                FROM youtube
                WHERE project_id = %s
            """, (project_id,))
        
        rows = cur.fetchall()
        for row in rows:
            youtube_id = row[0]
            duration_sec = row[1]
            views = row[2]
            likes = row[3]
            title = row[4]
            description = row[5]
            
            # Clear existing features
            cur.execute("DELETE FROM youtube_features WHERE youtube_id = %s", (youtube_id,))
            
            # Generate features
            text_content = f"{title or ''} {description or ''}"
            features_list = self.features.video_features(
                seconds=duration_sec,
                published_at=None,  # Not available in current data
                views=views,
                sem_score=None,  # Would need to calculate from embedding
                text_content=text_content
            )
            
            # Insert features
            if features_list:
                cur.executemany(
                    "INSERT INTO youtube_features(youtube_id, category, feature) VALUES (%s, %s, %s)",
                    [(youtube_id, cat, feat) for cat, feat in features_list]
                )
        
        self.cx.cnx.commit()

    def _fetch_current_recs(self, project_id: int) -> List[Tuple]:
        """Fetch staged candidates."""
        cur = self.cx.cursor
        cur.execute("""
            SELECT
                rec_id,
                video_title,
                video_description,
                TIME_TO_SEC(video_duration) AS video_duration_sec,
                video_url,
                video_views,
                video_likes,
                video_embedding
            FROM youtube_current_recs
            WHERE project_id=%s
        """, (project_id,))
        results = cur.fetchall()
        return results

    def _update_rec_scores_and_ranks(self, project_id: int, scored_sorted: List[Tuple[int, str, Optional[str], float]]) -> None:
        """Persist scores and ranks for current staged candidates."""
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
