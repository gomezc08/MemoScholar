# src/jaccard_coefficient/jaccard_videos.py
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import logging

from src.db.connector import Connector
from src.db.db_crud.select_db import DBSelect
from src.db.db_crud.insert import DBInsert
from src.db.db_crud.change import DBChange
from src.text_embedding.embedding import Embedding
from src.jaccard_coefficient.features import Features

logger = logging.getLogger(__name__)

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
      - add_candidates(project_id: int, candidates: List[Dict]) -> List[int]
    """
    
    # Feature category weights (alpha values)
    WEIGHTS = {
        'emb': 0.6,   # semantic similarity (primary)
        'dur': 0.15,  # duration
        'fresh': 0.1, # freshness
        'pop': 0.1,   # popularity
        'type': 0.05  # type
    }
    
    def __init__(self, connector: Connector):
        self.cx = connector
        self.features = Features()
        # Create DB instances but they'll use the shared connector
        self.db_select = DBSelect()
        self.db_insert = DBInsert()
        self.db_change = DBChange()
        self.embedding = Embedding()
        
        # Share the open connection with DBSelect, DBInsert, and DBChange
        self.db_select.connector = self.cx
        self.db_insert.connector = self.cx
        self.db_change.connector = self.cx
        # Disable connection management for shared connection
        self.db_select.manage_connection = False
        self.db_insert.manage_connection = False
        self.db_change.manage_connection = False

    def _ensure_connection(self) -> None:
        if self.cx.cursor is None or self.cx.cnx is None or not self.cx.cnx.is_connected():
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
        Refresh derived features for persisted YouTube videos.
        Note: Project features are computed on-the-fly and don't need updating.
        """
        self._ensure_connection()
        self._upsert_youtube_features(project_id)

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True, lambda_dislike: float = 0.5) -> List[Dict]:
        """
        Score all videos that haven't been recommended yet, update their recommendation status,
        and return the top-k.
        """
        self._ensure_connection()
        # Load project features (liked items + project text)
        proj_features = self._load_project_features(project_id, include_likes=include_likes)
        
        # Load disliked features
        disliked_features = self._load_disliked_features(project_id)
        
        # Fetch candidate videos (videos that haven't been recommended)
        cand_rows = self._fetch_unrecommended_videos(project_id)
        
        scored: List[Tuple[int, str, Optional[str], float]] = []
        for r in cand_rows:
            # Extract features from candidate row
            cand_features = self._extract_features_from_youtube_row(r)
            
            # Debug: log features for first video only
            if len(scored) == 0:
                logger.info(f"DEBUG: Project features by category: {proj_features}")
                logger.info(f"DEBUG: First candidate features by category: {cand_features}")
            
            # Calculate J^+ (positive jaccard)
            pos_score = self.weighted_jaccard(proj_features, cand_features)
            
            # Calculate J^- (negative jaccard)
            neg_score = self.weighted_jaccard(disliked_features, cand_features) if disliked_features else 0.0
            
            # Calculate final score: S(P, i) = J^+(P, i) - λ * J^-(P, i)
            final_score = max(0.0, pos_score - lambda_dislike * neg_score)
            
            # r[0] = youtube_id, r[1] = video_title, r[4] = video_url
            scored.append((r[0], r[1], r[4], final_score))
        
        # Sort by score
        scored_sorted = sorted(scored, key=lambda x: x[3], reverse=True)
        
        # Mark top-k as recommended
        self._mark_topk_as_recommended(project_id, scored_sorted[:topk])
        
        # Return full YouTube video details with score
        result: List[Dict] = []
        for youtube_id, title, url, s in scored_sorted[:topk]:
            video_details = self.db_select.get_youtube_video(youtube_id)
            if video_details:
                video_details['calculated_score'] = s
                result.append(video_details)
        return result

    def add_candidates(self, project_id: int, candidates: List[Dict]) -> List[int]:
        """
        Add new candidate videos to the youtube table (if they don't exist).
        Returns list of youtube_ids that were added.
        """
        logger.info(f"add_candidates called with {len(candidates)} candidates for project {project_id}")
        self._ensure_connection()
        
        def _secs_to_time(secs: Optional[int]) -> Optional[str]:
            if secs is None:
                return None
            h = secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

        added_ids = []
        for idx, c in enumerate(candidates):
            logger.info(f"Processing candidate {idx+1}/{len(candidates)}: {c.get('title', 'Unknown')[:50]}")
            title = c.get("title")
            if not title:
                continue
            desc = c.get("description", "")
            url = c.get("url")
            views = int(c.get("views", 0) or 0)
            likes = int(c.get("likes", 0) or 0)
            
            if "duration_time" in c and c.get("duration_time") is not None:
                dur_time = c.get("duration_time")
            else:
                dur_time = _secs_to_time(c.get("duration_seconds"))
            
            # Check if video already exists
            if self.db_select.check_youtube_video_exists(project_id, title):
                continue  # Skip if already exists
            
            # Insert video using db_crud (query_id can be None)
            youtube_id = self.db_insert.create_youtube(
                project_id=project_id,
                query_id=None,
                video_title=title,
                video_description=desc,
                video_duration=dur_time,
                video_url=url,
                video_views=views,
                video_likes=likes
            )
            
            if youtube_id is None:
                logger.warning(f"Failed to insert video: {title}")
                continue
                
            added_ids.append(youtube_id)
            
            # Generate and insert features
            duration_sec = None
            if dur_time:
                parts = dur_time.split(':')
                duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            
            features_list = self.features.video_features(
                seconds=duration_sec,
                published_at=None,
                views=views,
                sem_score=None
            )
            
            # Insert features using db_crud
            logger.info(f"Inserting features for youtube_id {youtube_id}")
            self.db_insert.insert_youtube_features(youtube_id, features_list)
            logger.info(f"Successfully inserted features for youtube_id {youtube_id}")
        
        logger.info(f"Committing {len(added_ids)} added videos")
        self.cx.cnx.commit()
        logger.info(f"add_candidates complete, returning {len(added_ids)} added IDs")
        return added_ids

    
    def _load_project_features(self, project_id: int, include_likes: bool) -> Dict[str, Set[str]]:
        """
        Load project features grouped by category.
        Returns Dict mapping category -> Set of feature values.
        """
        self._ensure_connection()
        
        # Fetch project embedding from project_embeddings (if needed for sem_score in future)
        project_embedding = self.db_select.get_project_embedding(project_id)
        if project_embedding is None:
            return {cat: set() for cat in self.WEIGHTS.keys()}
        
        # For now, we don't compute actual similarity; use None and rely on bucketed features
        sem_score = None
        
        features_list = self.features.project_features(sem_score)
        
        # Organize by category
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for category, feature_value in features_list:
            features_by_category[category].add(feature_value)
        
        # Add liked videos' features
        if include_likes:
            liked_ids = self.db_select.get_liked_youtube_ids(project_id)
            for target_id in liked_ids:
                video_features = self._get_youtube_features(target_id)
                for category, feature_set in video_features.items():
                    features_by_category[category] |= feature_set
        
        return features_by_category

    def _load_disliked_features(self, project_id: int) -> Optional[Dict[str, Set[str]]]:
        """Load features from disliked videos."""
        self._ensure_connection()
        
        disliked_ids = self.db_select.get_disliked_youtube_ids(project_id)
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
        self._ensure_connection()
        
        features_by_category = self.db_select.get_youtube_features_by_category(youtube_id)
        # Ensure all categories exist in the result (even if empty)
        for cat in self.WEIGHTS.keys():
            if cat not in features_by_category:
                features_by_category[cat] = set()
        
        return features_by_category

    def _extract_features_from_youtube_row(self, row: Tuple) -> Dict[str, Set[str]]:
        """
        Extract features from a youtube table row.
        row format: (youtube_id, video_title, video_description, video_duration_sec, video_url, video_views, video_likes)
        """
        # Fetch features from youtube_features table
        youtube_id = row[0]
        self._ensure_connection()
        
        features_by_category = self.db_select.get_youtube_features_by_category(youtube_id)
        # Ensure all categories exist in the result (even if empty)
        for cat in self.WEIGHTS.keys():
            if cat not in features_by_category:
                features_by_category[cat] = set()
        
        return features_by_category

    def _upsert_youtube_features(self, project_id: Optional[int] = None) -> None:
        """
        Update features for YouTube videos in the youtube_features table.
        Uses db_crud functions instead of direct cursor operations.
        """
        self._ensure_connection()
        
        rows = self.db_select.get_youtube_videos_for_feature_update(project_id)
        for row in rows:
            youtube_id = row[0]
            duration_sec = row[1]
            views = row[2]
            likes = row[3]
            
            # Generate features
            # sem_score=None will default to "sem:mid" in the features function
            features_list = self.features.video_features(
                seconds=duration_sec,
                published_at=None,
                views=views,
                sem_score=None
            )
            
            # Insert features using db_crud
            self.db_insert.insert_youtube_features(youtube_id, features_list)

    def _fetch_unrecommended_videos(self, project_id: int) -> List[Tuple]:
        """Fetch videos that haven't been recommended yet."""
        self._ensure_connection()
        return self.db_select.get_unrecommended_youtube_videos(project_id)

    def _mark_topk_as_recommended(self, project_id: int, top_videos: List[Tuple[int, str, Optional[str], float]]) -> None:
        """Mark top-k videos as recommended in youtube_has_rec."""
        self._ensure_connection()
        youtube_ids = [youtube_id for youtube_id, _title, _url, _score in top_videos]
        self.db_change.mark_youtube_videos_as_recommended(youtube_ids)
        self.cx.cnx.commit()
