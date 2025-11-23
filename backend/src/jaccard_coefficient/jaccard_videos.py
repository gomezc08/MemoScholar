# src/jaccard_coefficient/jaccard_videos.py
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import logging

from src.db.connector import Connector
from src.db.db_crud.select_db import DBSelect
from src.db.db_crud.insert import DBInsert
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
    Recommender using weighted feature-based Jaccard coefficient with semantic embeddings.

    The system uses a hybrid content-based + collaborative filtering approach:

    1. **Feature Extraction**: Each video is represented by multiple feature categories:
       - emb: Semantic similarity (computed via cosine similarity of embeddings)
       - dur: Video duration (bucketed: xs, s, m, l, xl)
       - pop: Popularity (view count - bucketed: niche, low, mid, high, viral)
       - engage: Engagement (like ratio - bucketed: low, mid, high)
       - fresh: Freshness (publication date - bucketed: 1y, 3y, old)
       - type: Content type (always 'youtube')

    2. **Positive Profile Construction (P^+)**: Built from liked videos' features
       - Aggregates features from all videos the user has liked
       - Represents user preferences

    3. **Negative Profile Construction (P^-)**: Built from disliked videos' features
       - Aggregates features from all videos the user has disliked
       - Represents content to avoid

    4. **Scoring Formula**:
       J^+(P, i) = Σ_category α_category * |P^+_category ∩ I_category| / |P^+_category ∪ I_category|

       S(P, i) = J^+(P, i) - λ * J^-(P, i)

       Where:
       - P^+ = positive profile (liked items)
       - P^- = negative profile (disliked items)
       - i = candidate item
       - α_category = weight for each feature category
       - λ = discount factor for negative signal (default 0.5)

    5. **Key Innovation**: Semantic similarity via embeddings
       - Project embedding captures research topic/objective
       - Video embeddings capture content semantics
       - Cosine similarity bucketed into discrete features
       - Enables content-based recommendations even without user history

    Public API:
      - update_features(project_id: Optional[int] = None) -> None
      - recommend(project_id: int, topk: int = 5, include_likes: bool = True) -> List[Dict]
      - add_candidates(project_id: int, candidates: List[Dict]) -> List[int]
    """
    
    # Feature category weights (alpha values)
    WEIGHTS = {
        'emb': 0.55,     # semantic similarity (primary - most important)
        'dur': 0.15,     # duration (user preference for video length)
        'pop': 0.10,     # popularity (social proof)
        'engage': 0.10,  # engagement (like ratio - quality signal)
        'fresh': 0.05,   # freshness (recency preference)
        'type': 0.05     # type (content type matching)
    }
    
    def __init__(self, connector: Connector):
        self.cx = connector
        self.features = Features()
        # Create DB instances but they'll use the shared connector
        self.db_select = DBSelect()
        self.db_insert = DBInsert()
        self.embedding = Embedding()
        
        # Share the open connection with DBSelect and DBInsert
        self.db_select.connector = self.cx
        self.db_insert.connector = self.cx
        # Disable connection management for shared connection
        self.db_select.manage_connection = False
        self.db_insert.manage_connection = False

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

        Args:
            project_id: The project ID
            topk: Number of recommendations to return
            include_likes: Whether to include liked videos in the positive profile
            lambda_dislike: Weight for negative signal from disliked items

        Returns:
            List of top-k recommended videos with scores
        """
        self._ensure_connection()
        logger.info(f"Starting recommendation for project_id={project_id}, topk={topk}, include_likes={include_likes}")

        # Load project features (liked items + project text)
        proj_features = self._load_project_features(project_id, include_likes=include_likes)
        logger.info(f"Loaded project features: {[(cat, len(feats)) for cat, feats in proj_features.items()]}")

        # Load disliked features
        disliked_features = self._load_disliked_features(project_id)
        if disliked_features:
            logger.info(f"Loaded disliked features: {[(cat, len(feats)) for cat, feats in disliked_features.items()]}")

        # Fetch candidate videos (videos that haven't been recommended)
        cand_rows = self._fetch_unrecommended_videos(project_id)
        logger.info(f"Found {len(cand_rows)} unrecommended candidate videos")

        scored: List[Tuple[int, str, Optional[str], float]] = []
        for idx, r in enumerate(cand_rows):
            # Extract features from candidate row
            cand_features = self._extract_features_from_youtube_row(r)

            # Debug: log features for first few videos
            if idx < 3:
                logger.info(f"Video {idx+1} '{r[1][:50]}' features: {[(cat, list(feats)) for cat, feats in cand_features.items()]}")

            # Calculate J^+ (positive jaccard)
            pos_score = self.weighted_jaccard(proj_features, cand_features)

            # Calculate J^- (negative jaccard)
            neg_score = self.weighted_jaccard(disliked_features, cand_features) if disliked_features else 0.0

            # Calculate final score: S(P, i) = J^+(P, i) - λ * J^-(P, i)
            final_score = max(0.0, pos_score - lambda_dislike * neg_score)

            if idx < 3:
                logger.info(f"Video {idx+1} scores: pos={pos_score:.4f}, neg={neg_score:.4f}, final={final_score:.4f}")

            # r[0] = youtube_id, r[1] = video_title, r[4] = video_url
            scored.append((r[0], r[1], r[4], final_score))

        # Sort by score
        scored_sorted = sorted(scored, key=lambda x: x[3], reverse=True)
        logger.info(f"Top 5 scores: {[f'{s[1][:30]}={s[3]:.4f}' for s in scored_sorted[:5]]}")

        # Mark top-k as recommended
        self._mark_topk_as_recommended(project_id, scored_sorted[:topk])

        # Return full YouTube video details with score
        result: List[Dict] = []
        for youtube_id, title, url, s in scored_sorted[:topk]:
            video_details = self.db_select.get_youtube_video(youtube_id)
            if video_details:
                video_details['calculated_score'] = s
                result.append(video_details)

        logger.info(f"Returning {len(result)} recommendations")
        return result

    def add_candidates(self, project_id: int, candidates: List[Dict]) -> List[int]:
        """
        Add new candidate videos to the youtube table (if they don't exist).
        Returns list of youtube_ids that were added.
        """
        logger.info(f"add_candidates called with {len(candidates)} candidates for project {project_id}")
        self._ensure_connection()
        cur = self.cx.cursor
        
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
            cur.execute("""
                SELECT youtube_id FROM youtube 
                WHERE project_id=%s AND video_title=%s
            """, (project_id, title))
            
            if cur.fetchone():
                continue  # Skip if already exists
            
            # Insert video
            cur.execute(
                """
                INSERT INTO youtube(project_id, video_title, video_description, video_duration, video_url, video_views, video_likes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (project_id, title, desc, dur_time, url, views, likes)
            )
            youtube_id = cur.lastrowid
            added_ids.append(youtube_id)
            
            # Generate and insert features
            duration_sec = None
            if dur_time:
                parts = dur_time.split(':')
                duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

            # CRITICAL: Compute actual semantic similarity
            sem_score = self._compute_semantic_similarity(project_id, youtube_id, title, desc)

            features_list = self.features.video_features(
                seconds=duration_sec,
                published_at=None,
                views=views,
                sem_score=sem_score,
                likes=likes
            )

            # Insert features using db_crud
            sem_display = sem_score if sem_score is not None else 0.0
            logger.info(f"Inserting features for youtube_id {youtube_id} (sem_score={sem_display:.4f})")
            self.db_insert.insert_youtube_features(youtube_id, features_list)
            logger.info(f"Successfully inserted features for youtube_id {youtube_id}")
        
        logger.info(f"Committing {len(added_ids)} added videos")
        self.cx.cnx.commit()
        logger.info(f"add_candidates complete, returning {len(added_ids)} added IDs")
        return added_ids

    # ---------------- Private helpers ---------------- 
    
    def _load_project_features(self, project_id: int, include_likes: bool) -> Dict[str, Set[str]]:
        """
        Load project features grouped by category.
        Returns Dict mapping category -> Set of feature values.

        Note: Project features come from liked videos only, not from project embedding directly.
        The project embedding is used to compute semantic similarity scores for candidate videos.
        """
        self._ensure_connection()
        cur = self.cx.cursor

        # Initialize feature categories
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}

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
        self._ensure_connection()
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
        self._ensure_connection()
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

    def _extract_features_from_youtube_row(self, row: Tuple) -> Dict[str, Set[str]]:
        """
        Extract features from a youtube table row.
        row format: (youtube_id, video_title, video_description, video_duration_sec, video_url, video_views, video_likes)
        """
        # Fetch features from youtube_features table
        youtube_id = row[0]
        self._ensure_connection()
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

    def _compute_semantic_similarity(self, project_id: int, youtube_id: int, video_title: str, video_description: str) -> Optional[float]:
        """
        Compute semantic similarity between project and video using embeddings.
        Uses cached video embeddings to avoid redundant API calls.

        Args:
            project_id: The project ID
            youtube_id: The YouTube video ID (for caching)
            video_title: Video title
            video_description: Video description

        Returns:
            Cosine similarity score between 0 and 1, or None if embeddings unavailable
        """
        try:
            # Get project embedding
            project_embedding = self.db_select.get_project_embedding(project_id)
            if not project_embedding:
                logger.warning(f"No project embedding found for project_id={project_id}")
                return None

            # Check cache for video embedding
            video_embedding = self.db_select.get_youtube_video_embedding(youtube_id)

            if video_embedding is None:
                # Cache miss - generate and cache embedding
                video_text = f"{video_title}; {video_description}"
                video_embedding = self.embedding.embed_text(video_text)

                # Cache the embedding for future use
                self.db_insert.upsert_youtube_video_embedding(youtube_id, video_embedding)
                logger.info(f"Generated and cached new embedding for youtube_id={youtube_id}")
            else:
                logger.info(f"Using cached embedding for youtube_id={youtube_id}")

            # Compute cosine similarity
            similarity = self.embedding.cosine_similarity(project_embedding, video_embedding)

            # Cosine similarity is already in [-1, 1] range, but typically positive for related content
            # For text embeddings, similarity is usually in [0, 1] range naturally
            # We clamp to [0, 1] to handle any edge cases
            clamped_similarity = max(0.0, min(1.0, similarity))

            logger.debug(f"Computed semantic similarity: raw={similarity:.4f}, clamped={clamped_similarity:.4f}")
            return clamped_similarity

        except Exception as e:
            logger.error(f"Error computing semantic similarity: {e}")
            return None

    def _upsert_youtube_features(self, project_id: Optional[int] = None) -> None:
        """
        Update features for YouTube videos in the youtube_features table.
        Uses db_crud functions instead of direct cursor operations.

        CRITICAL CHANGE: Now computes actual semantic similarity using embeddings.
        """
        self._ensure_connection()
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
        for row in rows:
            youtube_id = row[0]
            vid_project_id = row[1]
            video_title = row[2]
            video_description = row[3]
            duration_sec = row[4]
            views = row[5]
            likes = row[6]

            # CRITICAL: Compute actual semantic similarity
            sem_score = self._compute_semantic_similarity(vid_project_id, youtube_id, video_title, video_description)

            # Generate features with actual semantic score
            features_list = self.features.video_features(
                seconds=duration_sec,
                published_at=None,  # TODO: Add published_at to youtube table
                views=views,
                sem_score=sem_score,
                likes=likes
            )

            # Insert features using db_crud
            self.db_insert.insert_youtube_features(youtube_id, features_list)

    def _fetch_unrecommended_videos(self, project_id: int) -> List[Tuple]:
        """Fetch videos that haven't been recommended yet."""
        self._ensure_connection()
        cur = self.cx.cursor
        cur.execute("""
            SELECT
                y.youtube_id,
                y.video_title,
                y.video_description,
                TIME_TO_SEC(y.video_duration) AS video_duration_sec,
                y.video_url,
                y.video_views,
                y.video_likes
            FROM youtube y
            WHERE y.project_id=%s
            AND NOT EXISTS (
                SELECT 1 FROM youtube_has_rec yhr
                WHERE yhr.youtube_id = y.youtube_id 
                AND yhr.hasBeenRecommended = TRUE
            )
        """, (project_id,))
        results = cur.fetchall()
        return results

    def _mark_topk_as_recommended(self, project_id: int, top_videos: List[Tuple[int, str, Optional[str], float]]) -> None:
        """Mark top-k videos as recommended in youtube_has_rec."""
        cur = self.cx.cursor
        for youtube_id, _title, _url, _score in top_videos:
            # Check if entry already exists
            cur.execute("SELECT youtube_has_rec_id FROM youtube_has_rec WHERE youtube_id=%s", (youtube_id,))
            if cur.fetchone():
                # Update existing entry
                cur.execute(
                    "UPDATE youtube_has_rec SET hasBeenRecommended=TRUE WHERE youtube_id=%s",
                    (youtube_id,)
                )
            else:
                # Insert new entry
                cur.execute(
                    "INSERT INTO youtube_has_rec(youtube_id, hasBeenRecommended) VALUES (%s, TRUE)",
                    (youtube_id,)
                )
        self.cx.cnx.commit()
