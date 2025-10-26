import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json
from langchain_openai import OpenAIEmbeddings
import numpy as np

load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")

class Embedding:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def embed_text(self, text: str) -> List[float]:
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            raise e
    
    def cosine_similarity(self,vec1, vec2):
        dot_product=np.dot(vec1,vec2)
        norm_a=np.linalg.norm(vec1)
        norm_b=np.linalg.norm(vec2)
        return dot_product/(norm_a * norm_b)

if __name__ == "__main__":
    emb = Embedding()
    text1 = "Graph Neural Networks in Healthcare"
    text2 = "NLP in Medical Research"
    text3 = "Paris is the capital of France"
    emb_1 = emb.embed_text(text1)
    emb_2 = emb.embed_text(text2)
    emb_3 = emb.embed_text(text3)
    print(f"Embedding: {emb.embed_text(text1)}")
    print(f"Cosine similairty (should be similar): {emb.cosine_similarity(emb_1, emb_2)}")
    print(f"Cosine similairty (should be different): {emb.cosine_similarity(emb_1, emb_3)}")