import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json
from langchain_openai import OpenAIEmbeddings

load_dotenv()
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")

class Embedding:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()

    def embed_text(self, text: str) -> List[float]:
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            raise e

if __name__ == "__main__":
    emb = Embedding()
    text = "Graph Neural Networks in Healthcare"
    print(f"Embedding: {emb.embed_text(text)}")