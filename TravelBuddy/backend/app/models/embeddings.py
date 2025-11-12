"""Embedding generation service"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import logging

logger = logging.getLogger(_name_)

class EmbeddingService:
    """Handles text embedding generation"""
    
    def _init_(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
        
        Returns:
            Numpy array of embeddings
        """
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            raise
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text"""
        return self.encode(text)[0] if isinstance(text, str) else self.encode(text)
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score between -1 and 1
        """
        from numpy.linalg import norm
        
        return np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
    
    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate similarity between query and multiple embeddings
        
        Args:
            query_embedding: Query embedding (1D array)
            embeddings: Matrix of embeddings (2D array)
        
        Returns:
            Array of similarity scores
        """
        from numpy.linalg import norm
        
        # Normalize if not already normalized
        query_norm = query_embedding / norm(query_embedding)
        embeddings_norm = embeddings / norm(embeddings, axis=1, keepdims=True)
        
        # Calculate dot products
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities
    
    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar texts to query
        
        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return
        
        Returns:
            List of (index, text, similarity_score) tuples
        """
        # Encode all texts
        query_embedding = self.encode_single(query)
        candidate_embeddings = self.encode(candidates)
        
        # Calculate similarities
        similarities = self.batch_similarity(query_embedding, candidate_embeddings)
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return results
        results = [
            (idx, candidates[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        return results
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.model.get_sentence_embedding_dimension()
    
    def encode_for_storage(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Encode texts and convert to list format for storage
        
        Args:
            texts: Single text or list of texts
        
        Returns:
            List of embedding vectors as lists
        """
        embeddings = self.encode(texts)
        
        if embeddings.ndim == 1:
            return [embeddings.tolist()]
        else:
            return embeddings.tolist()
