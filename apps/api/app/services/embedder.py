import math
import hashlib
import numpy as np
from typing import List
from app.config import settings

class BaseEmbedder:
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]

class LocalVectorEmbedder(BaseEmbedder):
    """
    Deterministic feature vectorizer utilizing character n-grams and hashing trick.
    Guarantees zero-dependency, reproducible 384-dimensional embeddings offline.
    """
    def __init__(self, dimension: int = settings.EMBEDDING_DIMENSION):
        self.dimension = dimension

    def _hash_token(self, token: str) -> int:
        return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % self.dimension

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().split()
            if not words:
                embeddings.append(vec.tolist())
                continue
                
            for word in words:
                # Unigram feature
                idx = self._hash_token(word)
                vec[idx] += 1.0
                # Bigram features
                for i in range(len(word) - 2):
                    sub = word[i:i+3]
                    idx_sub = self._hash_token(sub)
                    vec[idx_sub] += 0.5
                    
            # L2 Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings

class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, api_key: str = settings.OPENAI_API_KEY, model: str = settings.EMBEDDING_MODEL):
        self.api_key = api_key
        self.model = model
        self.local_fallback = LocalVectorEmbedder()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            return self.local_fallback.embed_texts(texts)
        try:
            import requests
            resp = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": texts, "model": self.model},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
        except Exception:
            return self.local_fallback.embed_texts(texts)

def get_embedder() -> BaseEmbedder:
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbedder()
    return LocalVectorEmbedder()
