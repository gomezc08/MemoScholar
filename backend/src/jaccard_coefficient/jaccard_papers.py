# src/jaccard_coefficient/jaccard_papers.py
from typing import List, Dict, Set, Optional, Tuple
from src.db.connector import Connector
from src.db.db_crud.select_db import DBSelect
from src.db.db_crud.insert import DBInsert
from src.text_embedding.embedding import Embedding
from src.jaccard_coefficient.features import Features
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class JaccardPaperRecommender:
    """
    Feature-based Jaccard coefficient recommender for academic papers.

    Algorithm:
    ----------
    1. Build positive profile P^+ from liked papers' features
    2. Build negative profile P^- from disliked papers' features (optional)
    3. For each candidate paper i, compute weighted Jaccard similarity:
       J^+(P, i) = Σ α_category × |P^+_category ∩ I_category| / |P^+_category ∪ I_category|
    4. Final score: S(P, i) = J^+(P, i) - λ × J^-(P, i)

    Features:
    ---------
    - emb: Semantic similarity (from embeddings) - HIGH WEIGHT
    - year: Publication year buckets
    - author: Normalized author names
    - type: Content type (paper)

    Public API:
    -----------
    - add_candidates(project_id, candidates) -> List[int]: Add papers and compute features
    - recommend(project_id, topk) -> List[Dict]: Get top-k recommendations
    """

    # Feature weights (must sum to 1.0)
    WEIGHTS = {
        'emb': 0.60,     # Semantic similarity (primary signal)
        'year': 0.20,    # Publication recency
        'author': 0.15,  # Author matching
        'type': 0.05,    # Content type
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
        """Ensure database connection is open"""
        if self.cx.cursor is None or self.cx.cnx is None or not self.cx.cnx.is_connected():
            self.cx.open_connection()

    def weighted_jaccard(self, prof: Dict[str, Set[str]], item: Dict[str, Set[str]]) -> float:
        """
        Compute weighted Jaccard similarity between profile and item.

        Args:
            prof: Profile features Dict[category -> Set[feature_values]]
            item: Item features Dict[category -> Set[feature_values]]

        Returns:
            Weighted Jaccard score in [0, 1]
        """
        if not prof or not item:
            return 0.0

        total_score = 0.0
        for category, weight in self.WEIGHTS.items():
            p_feats = prof.get(category, set())
            i_feats = item.get(category, set())

            if not p_feats and not i_feats:
                continue

            intersection = len(p_feats & i_feats)
            union = len(p_feats | i_feats)

            if union > 0:
                jaccard = intersection / union
                total_score += weight * jaccard

        return total_score

    def add_candidates(self, project_id: int, candidates: List[Dict]) -> List[int]:
        """
        Add paper candidates to database and compute features.

        Args:
            project_id: Project ID
            candidates: List of paper dicts with keys:
                - title: Paper title
                - summary: Paper abstract/summary
                - year: Publication year
                - authors: List of author names
                - pdf_link: PDF URL

        Returns:
            List of paper_ids that were added
        """
        self._ensure_connection()
        cur = self.cx.cursor

        added_ids = []
        for idx, c in enumerate(candidates):
            logger.info(f"Processing paper {idx+1}/{len(candidates)}: {c.get('title', 'Unknown')[:50]}")
            title = c.get("title")
            if not title:
                continue

            summary = c.get("summary", "")
            year = c.get("year")
            pdf_link = c.get("pdf_link")
            authors_list = c.get("authors", [])

            # Check if paper already exists
            cur.execute("""
                SELECT paper_id FROM papers
                WHERE project_id=%s AND paper_title=%s
            """, (project_id, title))

            if cur.fetchone():
                continue  # Skip if already exists

            # Insert paper
            cur.execute(
                """
                INSERT INTO papers(project_id, paper_title, paper_summary, published_year, pdf_link)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (project_id, title, summary, year, pdf_link)
            )
            paper_id = cur.lastrowid
            added_ids.append(paper_id)

            # Insert authors
            for author_name in authors_list:
                if not author_name:
                    continue

                # Check if author exists
                cur.execute("SELECT author_id FROM authors WHERE name=%s", (author_name,))
                author_row = cur.fetchone()

                if author_row:
                    author_id = author_row[0]
                else:
                    # Create new author
                    cur.execute("INSERT INTO authors(name) VALUES (%s)", (author_name,))
                    author_id = cur.lastrowid

                # Link paper to author
                cur.execute(
                    "INSERT INTO paperauthors(paper_id, author_id) VALUES (%s, %s)",
                    (paper_id, author_id)
                )

            # Compute semantic similarity
            sem_score = self._compute_semantic_similarity(project_id, paper_id, title, summary)

            # Generate features
            features_list = self.features.paper_features(
                title=title,
                summary=summary,
                year=year,
                authors=authors_list,
                sem_score=sem_score
            )

            # Insert features
            sem_display = sem_score if sem_score is not None else 0.0
            logger.info(f"Inserting features for paper_id {paper_id} (sem_score={sem_display:.4f})")
            self.db_insert.insert_paper_features(paper_id, features_list)
            logger.info(f"Successfully inserted features for paper_id {paper_id}")

        logger.info(f"Committing {len(added_ids)} added papers")
        self.cx.cnx.commit()
        logger.info(f"add_candidates complete, returning {len(added_ids)} added IDs")
        return added_ids

    def recommend(self, project_id: int, topk: int = 5, include_likes: bool = True, lambda_dislike: float = 0.5) -> List[Dict]:
        """
        Score all papers and return top-k recommendations.

        Args:
            project_id: The project ID
            topk: Number of recommendations to return
            include_likes: Whether to include liked papers in the positive profile
            lambda_dislike: Weight for negative signal from disliked items

        Returns:
            List of top-k recommended papers with scores
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

        # Fetch candidate papers (all papers for now - can add filtering later)
        cand_rows = self._fetch_candidate_papers(project_id)
        logger.info(f"Found {len(cand_rows)} candidate papers")

        scored: List[Tuple[int, str, Optional[str], float]] = []
        for idx, r in enumerate(cand_rows):
            # Extract features from candidate row
            cand_features = self._extract_features_from_paper_row(r)

            # Debug: log features for first few papers
            if idx < 3:
                logger.info(f"Paper {idx+1} '{r[1][:50]}' features: {[(cat, list(feats)) for cat, feats in cand_features.items()]}")

            # Calculate J^+ (positive jaccard)
            pos_score = self.weighted_jaccard(proj_features, cand_features)

            # Calculate J^- (negative jaccard)
            neg_score = self.weighted_jaccard(disliked_features, cand_features) if disliked_features else 0.0

            # Calculate final score: S(P, i) = J^+(P, i) - λ * J^-(P, i)
            final_score = max(0.0, pos_score - lambda_dislike * neg_score)

            if idx < 3:
                logger.info(f"Paper {idx+1} scores: pos={pos_score:.4f}, neg={neg_score:.4f}, final={final_score:.4f}")

            scored.append((r[0], r[1], r[2], final_score))  # paper_id, title, pdf_link, score

        # Sort by score descending
        scored_sorted = sorted(scored, key=lambda x: x[3], reverse=True)

        # Log top scores
        if scored_sorted:
            logger.info(f"Top 5 scores: {[f'{s[1][:30]}={s[3]:.4f}' for s in scored_sorted[:5]]}")

        # Take top-k
        top_k = scored_sorted[:topk]
        logger.info(f"Returning {len(top_k)} recommendations")

        # Format results
        results = []
        for paper_id, title, pdf_link, score in top_k:
            results.append({
                'paper_id': paper_id,
                'paper_title': title,
                'pdf_link': pdf_link,
                'calculated_score': score
            })

        return results

    # ---------------- Private helpers ----------------

    def _load_project_features(self, project_id: int, include_likes: bool) -> Dict[str, Set[str]]:
        """Load project features from liked papers."""
        self._ensure_connection()
        cur = self.cx.cursor

        # Initialize feature categories
        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}

        # Add liked papers' features
        if include_likes:
            cur.execute("""
                SELECT target_id
                FROM likes
                WHERE project_id=%s AND target_type='paper' AND isLiked = TRUE
            """, (project_id,))

            for (target_id,) in cur.fetchall():
                paper_features = self._get_paper_features(target_id)
                for category, feature_set in paper_features.items():
                    features_by_category[category] |= feature_set

        return features_by_category

    def _load_disliked_features(self, project_id: int) -> Optional[Dict[str, Set[str]]]:
        """Load features from disliked papers."""
        self._ensure_connection()
        cur = self.cx.cursor
        cur.execute("""
            SELECT target_id
            FROM likes
            WHERE project_id=%s AND target_type='paper' AND isLiked = FALSE
        """, (project_id,))

        disliked_ids = [r[0] for r in cur.fetchall()]
        if not disliked_ids:
            return None

        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for paper_id in disliked_ids:
            paper_features = self._get_paper_features(paper_id)
            for category, feature_set in paper_features.items():
                features_by_category[category] |= feature_set

        return features_by_category

    def _get_paper_features(self, paper_id: int) -> Dict[str, Set[str]]:
        """Get features for a specific paper from paper_features table."""
        self._ensure_connection()
        cur = self.cx.cursor
        cur.execute("""
            SELECT category, feature
            FROM paper_features
            WHERE paper_id = %s
        """, (paper_id,))

        features_by_category = {cat: set() for cat in self.WEIGHTS.keys()}
        for category, feature_value in cur.fetchall():
            features_by_category[category].add(feature_value)

        return features_by_category

    def _extract_features_from_paper_row(self, row: Tuple) -> Dict[str, Set[str]]:
        """
        Extract features from a papers table row.
        row format: (paper_id, paper_title, pdf_link)
        """
        # Fetch features from paper_features table
        paper_id = row[0]
        return self._get_paper_features(paper_id)

    def _fetch_candidate_papers(self, project_id: int) -> List[Tuple]:
        """Fetch all papers for a project."""
        self._ensure_connection()
        cur = self.cx.cursor
        cur.execute("""
            SELECT paper_id, paper_title, pdf_link
            FROM papers
            WHERE project_id = %s
        """, (project_id,))
        return cur.fetchall()

    def _compute_semantic_similarity(self, project_id: int, paper_id: int, title: str, summary: Optional[str]) -> Optional[float]:
        """
        Compute semantic similarity between project and paper using embeddings.
        Uses cached paper embeddings to avoid redundant API calls.

        Args:
            project_id: The project ID
            paper_id: The paper ID (for caching)
            title: Paper title
            summary: Paper summary/abstract

        Returns:
            Cosine similarity score between 0 and 1, or None if embeddings unavailable
        """
        try:
            # Get project embedding
            project_embedding = self.db_select.get_project_embedding(project_id)
            if not project_embedding:
                logger.warning(f"No project embedding found for project_id={project_id}")
                return None

            # Check cache for paper embedding
            paper_embedding = self.db_select.get_paper_embedding(paper_id)

            if paper_embedding is None:
                # Cache miss - generate and cache embedding
                paper_text = f"{title}; {summary or ''}"
                paper_embedding = self.embedding.embed_text(paper_text)

                # Cache the embedding for future use
                self.db_insert.upsert_paper_embedding(paper_id, paper_embedding)
                logger.info(f"Generated and cached new embedding for paper_id={paper_id}")
            else:
                logger.info(f"Using cached embedding for paper_id={paper_id}")

            # Compute cosine similarity
            similarity = self.embedding.cosine_similarity(project_embedding, paper_embedding)

            # Clamp to [0, 1]
            clamped_similarity = max(0.0, min(1.0, similarity))
            logger.info(f"Computed semantic similarity: raw={similarity:.4f}, clamped={clamped_similarity:.4f}")

            return clamped_similarity

        except Exception as e:
            logger.error(f"Error computing semantic similarity: {e}")
            return None
