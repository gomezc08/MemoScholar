"""
CF Paper Recommender

Uses content-based similarity (embeddings) to score and recommend papers.
Similar to JaccardVideoRecommender but adapted for papers.
"""

import pickle
import os
from typing import List, Dict, Optional, Tuple
from ..db.connector import Connector
from ..db.db_crud.select_db import DBSelect
from ..db.db_crud.insert import DBInsert
from ..text_embedding.embedding import Embedding
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

models_directory = r"backend\src\cf_recommender\models"


class CFPaperRecommender:
    """
    Content-based paper recommender using embeddings.
    
    Scores papers based on semantic similarity to the project using embeddings.
    Returns top-k recommendations with scores.
    """
    
    def __init__(self, connector: Connector):
        self.connector = connector
        self.db_select = DBSelect()
        self.db_insert = DBInsert()
        self.embedding = Embedding()
    
    def add_candidates(self, project_id: int, candidates: List[Dict]) -> List[int]:
        """
        Add candidate papers to database (papers should already be added by paper_generator).
        This method is kept for API compatibility but doesn't need to do anything
        since papers are already in the database.
        
        Returns list of paper_ids that were added.
        """
        logger.info(f"add_candidates called with {len(candidates)} candidates for project {project_id}")
        # Papers are already added by paper_generator, so we just return the IDs
        # This method exists for API compatibility
        added_ids = []
        
        for candidate in candidates:
            # Papers should already be in database from paper_generator
            # We could check here, but for now just log
            logger.debug(f"Candidate: {candidate.get('title', 'Unknown')[:50]}")
        
        logger.info(f"add_candidates complete, returning {len(added_ids)} IDs")
        return added_ids
    
    def recommend(self, project_id: int, topk: int = 5) -> List[Dict]:
        """
        Score all unrecommended papers for a project and return top-k.
        
        Args:
            project_id: The project ID
            topk: Number of recommendations to return (default: 5)
        
        Returns:
            List of top-k recommended papers with scores
        """
        logger.info(f"Starting recommendation for project_id={project_id}, topk={topk}")
        
        # Get project embedding
        project_embedding = self.db_select.get_project_embedding(project_id)
        if not project_embedding:
            logger.warning(f"No project embedding found for project_id={project_id}")
            # Fallback: return papers without scoring
            return self._get_papers_without_scoring(project_id, topk)
        
        # Get all papers for this project that haven't been recommended yet
        # For now, we'll score all papers in the project
        papers = self._get_unrecommended_papers(project_id)
        logger.info(f"Found {len(papers)} papers to score")
        
        if len(papers) == 0:
            logger.warning(f"No papers found for project {project_id}")
            return []
        
        # Score each paper
        scored_papers = []
        for paper in papers:
            try:
                paper_id = paper['paper_id']
                paper_title = paper.get('paper_title', '')
                paper_summary = paper.get('paper_summary', '')
                
                # Get or create paper embedding
                paper_embedding = self.db_select.get_paper_embedding(paper_id)
                
                if paper_embedding is None:
                    # Generate and cache embedding
                    paper_text = f"{paper_title}; {paper_summary}"
                    paper_embedding = self.embedding.embed_text(paper_text)
                    self.db_insert.upsert_paper_embedding(paper_id, paper_embedding)
                    logger.info(f"Generated and cached embedding for paper_id={paper_id}")
                
                # Compute cosine similarity
                similarity = self.embedding.cosine_similarity(project_embedding, paper_embedding)
                score = max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
                
                scored_papers.append({
                    'paper': paper,
                    'score': score
                })
                
            except Exception as e:
                logger.error(f"Error scoring paper {paper.get('paper_id')}: {str(e)}", exc_info=True)
                continue
        
        # Sort by score (descending)
        scored_papers.sort(key=lambda x: x['score'], reverse=True)
        
        # Get top-k
        top_papers = scored_papers[:topk]
        
        # Log top scores
        top_scores_list = []
        for p in top_papers:
            paper_title = p['paper'].get('paper_title', 'Unknown')[:30]
            score = p['score']
            top_scores_list.append(f"{paper_title}={score:.4f}")
        logger.info(f"Top {len(top_papers)} scores: {', '.join(top_scores_list)}")
        
        # Format results
        result = []
        for item in top_papers:
            paper = item['paper']
            score = item['score']
            
            # Get authors
            paper_with_authors = self.db_select.get_paper_with_authors(paper['paper_id'])
            authors = []
            if paper_with_authors and paper_with_authors.get('authors'):
                authors = [a.get('name', '') if isinstance(a, dict) else a for a in paper_with_authors['authors']]
            
            # Generate ArXiv abstract link from PDF link
            pdf_link = paper.get('pdf_link', '')
            arxiv_link = ''
            if pdf_link and pdf_link != 'No PDF':
                if '/pdf/' in pdf_link:
                    arxiv_link = pdf_link.replace('/pdf/', '/abs/').replace('.pdf', '')
                else:
                    arxiv_link = pdf_link
            
            result.append({
                'paper_id': paper['paper_id'],
                'paper_title': paper.get('paper_title', ''),
                'link': arxiv_link,  # ArXiv abstract page link
                'pdf_link': pdf_link,
                'paper_summary': paper.get('paper_summary', ''),
                'published_year': paper.get('published_year'),
                'authors': authors,
                'calculated_score': score
            })
        
        logger.info(f"Returning {len(result)} recommendations")
        return result
    
    def _get_unrecommended_papers(self, project_id: int) -> List[Dict]:
        """
        Get all papers for a project.
        In the future, we could add a 'recommended' flag to filter.
        """
        self.connector.open_connection()
        try:
            query = """
                SELECT paper_id, project_id, query_id, paper_title, 
                       paper_summary, published_year, pdf_link
                FROM papers
                WHERE project_id = %s
                ORDER BY paper_id DESC
            """
            self.connector.cursor.execute(query, (project_id,))
            results = self.connector.cursor.fetchall()
            
            papers = []
            for row in results:
                papers.append({
                    'paper_id': row[0],
                    'project_id': row[1],
                    'query_id': row[2],
                    'paper_title': row[3],
                    'paper_summary': row[4],
                    'published_year': row[5],
                    'pdf_link': row[6]
                })
            
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}", exc_info=True)
            return []
        finally:
            self.connector.close_connection()
    
    def _get_papers_without_scoring(self, project_id: int, topk: int) -> List[Dict]:
        """
        Fallback: return papers without scoring when project embedding is missing.
        """
        papers = self._get_unrecommended_papers(project_id)
        
        result = []
        for paper in papers[:topk]:
            paper_with_authors = self.db_select.get_paper_with_authors(paper['paper_id'])
            authors = []
            if paper_with_authors and paper_with_authors.get('authors'):
                authors = [a.get('name', '') if isinstance(a, dict) else a for a in paper_with_authors['authors']]
            
            result.append({
                'paper_id': paper['paper_id'],
                'paper_title': paper.get('paper_title', ''),
                'pdf_link': paper.get('pdf_link'),
                'paper_summary': paper.get('paper_summary', ''),
                'published_year': paper.get('published_year'),
                'authors': authors,
                'calculated_score': 0.0  # No score available
            })
        
        return result

