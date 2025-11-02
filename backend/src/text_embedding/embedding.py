import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
import json
from langchain_openai import OpenAIEmbeddings
import numpy as np

class Embedding:
    def __init__(self):
        self._embeddings = None  # Lazy initialization
    
    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return self._embeddings

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