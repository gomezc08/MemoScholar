import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db.connector import Connector
from src.jaccard_coefficient.jaccard_videos import JaccardVideoRecommender
from src.jaccard_coefficient.jaccard_papers import JaccardPaperRecommender

def run_demo(project_id: int = 1):
    cx = Connector()
    cx.open_connection()
    try:
        vids = JaccardVideoRecommender(cx)
        papers = JaccardPaperRecommender(cx)

        # Refresh features after you’ve inserted new items for this project
        vids.update_features(project_id)
        papers.update_features(project_id)

        top_vids = vids.recommend(project_id, topk=5, include_likes=True)
        top_paps = papers.recommend(project_id, topk=5, include_likes=True)

        print("\nTop videos:")
        for i, r in enumerate(top_vids, 1):
            print(f"{i:>2}. {r.title}  (score={r.score:.4f})  {r.url or ''}")

        print("\nTop papers:")
        for i, r in enumerate(top_paps, 1):
            print(f"{i:>2}. {r.title}  (score={r.score:.4f})  {r.url or ''}")
    finally:
        cx.close_connection()

if __name__ == "__main__":
    run_demo(project_id=1)