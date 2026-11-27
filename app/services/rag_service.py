import os
import pickle
import re
import logging
from typing import List, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
from app.models.document import DocumentChunk, Document
from app.config import settings
from app.services.gemini_service import GeminiClient
from app.utils.helpers import ensure_vector_store_dir

# Try to import faiss, but make it optional
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Gemini-backed retrieval-augmented generation."""

    _embedding_dimension = GeminiClient.embedding_dimensions
    
    def __init__(self):
        self.client = None  # Client will be initialized lazily when needed
        self.vector_store_dir = "vector_store"
        ensure_vector_store_dir(self.vector_store_dir)
    
    def _get_client(self):
        """Get or create Gemini client instance."""
        if self.client is None:
            self.client = GeminiClient()
        return self.client
    
    def get_user_vector_store_path(self, user_id: int) -> str:
        """Get the path to a user's vector store."""
        return os.path.join(self.vector_store_dir, f"user_{user_id}")
    
    def get_user_index_path(self, user_id: int) -> str:
        """Get the path to a user's FAISS index."""
        return os.path.join(self.get_user_vector_store_path(user_id), "index.faiss")
    
    def get_user_metadata_path(self, user_id: int) -> str:
        """Get the path to a user's metadata file."""
        return os.path.join(self.get_user_vector_store_path(user_id), "metadata.pkl")

    def get_user_embedding_model_path(self, user_id: int) -> str:
        return os.path.join(self.get_user_vector_store_path(user_id), "embedding-model.txt")

    def _embedding_signature(self) -> str:
        return f"{settings.GEMINI_EMBEDDING_MODEL}:{self._embedding_dimension}"

    def _has_current_embedding_model(self, user_id: int) -> bool:
        try:
            with open(self.get_user_embedding_model_path(user_id), encoding="utf-8") as marker:
                return marker.read().strip() == self._embedding_signature()
        except FileNotFoundError:
            return False
    
    def create_embedding(self, text: str) -> List[float]:
        """Create a retrieval-query embedding using Gemini."""
        try:
            return self._get_client().embed_contents(
                [text], task_type="RETRIEVAL_QUERY"
            )[0]
        except Exception as e:
            raise Exception(f"Failed to create embedding: {str(e)}")
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create retrieval-document embeddings for multiple texts."""
        try:
            client = self._get_client()
            embeddings = []
            for offset in range(0, len(texts), 100):
                embeddings.extend(
                    client.embed_contents(
                        texts[offset:offset + 100],
                        task_type="RETRIEVAL_DOCUMENT",
                    )
                )
            return embeddings
        except Exception as e:
            raise Exception(f"Failed to create embeddings batch: {str(e)}")
    
    def initialize_user_vector_store(self, user_id: int) -> None:
        """Initialize a vector store for a user."""
        if not FAISS_AVAILABLE:
            return  # Skip vector store initialization if faiss is not available
            
        user_dir = self.get_user_vector_store_path(user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Create empty index and metadata
        index = faiss.IndexFlatL2(self._embedding_dimension)
        
        # Save empty index
        faiss.write_index(index, self.get_user_index_path(user_id))
        
        # Save empty metadata
        with open(self.get_user_metadata_path(user_id), 'wb') as f:
            pickle.dump([], f)
    
    def add_chunks_to_vector_store(
        self,
        user_id: int,
        chunks: List[DocumentChunk]
    ) -> None:
        """Add document chunks to a user's vector store."""
        if not FAISS_AVAILABLE:
            return  # Skip vector store operations if faiss is not available
            
        # Initialize vector store if it doesn't exist
        if not os.path.exists(self.get_user_index_path(user_id)):
            self.initialize_user_vector_store(user_id)
        
        # Load existing index and metadata
        index = faiss.read_index(self.get_user_index_path(user_id))
        
        with open(self.get_user_metadata_path(user_id), 'rb') as f:
            metadata = pickle.load(f)
        
        # Create embeddings for new chunks
        texts = [chunk.chunk_text for chunk in chunks]
        embeddings = self.create_embeddings_batch(texts)
        
        # Add embeddings to index
        embeddings_array = np.array(embeddings).astype('float32')
        index.add(embeddings_array)
        
        # Add metadata
        for chunk in chunks:
            metadata.append({
                'chunk_id': chunk.id,
                'document_id': chunk.document_id,
                'chunk_text': chunk.chunk_text,
                'page_number': chunk.page_number,
                'subject': chunk.subject,
                'topic': chunk.topic,
                'chunk_index': chunk.chunk_index
            })
        
        # Save updated index and metadata
        faiss.write_index(index, self.get_user_index_path(user_id))
        
        with open(self.get_user_metadata_path(user_id), 'wb') as f:
            pickle.dump(metadata, f)
        with open(self.get_user_embedding_model_path(user_id), "w", encoding="utf-8") as marker:
            marker.write(self._embedding_signature())
    
    def search_similar_chunks(
        self,
        user_id: int,
        query: str,
        top_k: int = 5,
        db: Session = None,
        document_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks based on a query."""
        if not settings.ai_configured or not FAISS_AVAILABLE:
            return self._keyword_search(db, user_id, query, top_k, document_id)

        def keyword_fallback() -> List[Dict[str, Any]]:
            return self._keyword_search(db, user_id, query, top_k, document_id)

        if (
            not os.path.exists(self.get_user_index_path(user_id))
            or not self._has_current_embedding_model(user_id)
        ):
            try:
                self._rebuild_user_vector_store(db, user_id)
            except Exception as error:
                logger.warning("Gemini reindex failed; using keyword search: %s", error)
                return keyword_fallback()
            if not os.path.exists(self.get_user_index_path(user_id)):
                return keyword_fallback()

        # Load index and metadata
        index = faiss.read_index(self.get_user_index_path(user_id))

        with open(self.get_user_metadata_path(user_id), 'rb') as f:
            metadata = pickle.load(f)

        if index.ntotal == 0:
            try:
                self._rebuild_user_vector_store(db, user_id)
            except Exception as error:
                logger.warning("Gemini reindex failed; using keyword search: %s", error)
                return keyword_fallback()
            index = faiss.read_index(self.get_user_index_path(user_id))
            if index.ntotal == 0:
                return keyword_fallback()
            with open(self.get_user_metadata_path(user_id), "rb") as metadata_file:
                metadata = pickle.load(metadata_file)

        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            query_array = np.array([query_embedding]).astype('float32')

            # Search
            candidate_count = min(top_k * 5 if document_id is not None else top_k, index.ntotal)
            distances, indices = index.search(query_array, candidate_count)
        except Exception as error:
            logger.warning("Vector search failed; using keyword search: %s", error)
            return keyword_fallback()

        # Get results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadata):
                result = metadata[idx].copy()
                if document_id is not None and result["document_id"] != document_id:
                    continue
                result['similarity_score'] = float(1 / (1 + distances[0][i]))
                results.append(result)
                if len(results) == top_k:
                    break

        return results or keyword_fallback()

    def _keyword_search(
        self,
        db: Session,
        user_id: int,
        query: str,
        top_k: int,
        document_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Fallback to matching document text when embeddings are unavailable."""
        if db is None:
            return []
        chunks = db.query(DocumentChunk).join(Document).filter(
            Document.user_id == user_id
        )
        if document_id is not None:
            chunks = chunks.filter(DocumentChunk.document_id == document_id)
        chunks = chunks.all()
        if not chunks:
            return []
        stop_words = {
            "about", "after", "and", "are", "can", "does", "explain", "for",
            "from", "how", "into", "is", "it", "me", "of", "on", "or", "please",
            "the", "this", "to", "what", "with", "you",
        }
        terms = {
            term for term in re.findall(r"[a-z0-9]+", query.lower())
            if len(term) > 2 and term not in stop_words
        }
        if not terms:
            return []

        ranked = []
        for chunk in chunks:
            chunk_terms = set(re.findall(r"[a-z0-9]+", chunk.chunk_text.lower()))
            matches = len(terms & chunk_terms)
            if matches:
                ranked.append((matches / len(terms), chunk))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_text": chunk.chunk_text,
                "page_number": chunk.page_number,
                "subject": chunk.subject,
                "topic": chunk.topic,
                "chunk_index": chunk.chunk_index,
                "similarity_score": score,
            }
            for score, chunk in ranked[:top_k]
        ]

    def _rebuild_user_vector_store(self, db: Session, user_id: int) -> None:
        """Re-embed legacy or missing user indexes using the configured Gemini model."""
        if db is None or not FAISS_AVAILABLE:
            return
        chunks = (
            db.query(DocumentChunk)
            .join(Document)
            .filter(Document.user_id == user_id)
            .order_by(DocumentChunk.id)
            .all()
        )
        marker_path = self.get_user_embedding_model_path(user_id)
        if os.path.exists(marker_path):
            os.remove(marker_path)
        self.initialize_user_vector_store(user_id)
        if chunks:
            self.add_chunks_to_vector_store(user_id, chunks)
        else:
            with open(marker_path, "w", encoding="utf-8") as marker:
                marker.write(self._embedding_signature())
    
    def delete_document_from_vector_store(
        self,
        user_id: int,
        document_id: int
    ) -> None:
        """Delete all chunks for a document from the vector store."""
        if not FAISS_AVAILABLE:
            return  # Skip vector store operations if faiss is not available
            
        # Load index and metadata
        if not os.path.exists(self.get_user_index_path(user_id)):
            return
        
        index = faiss.read_index(self.get_user_index_path(user_id))
        
        with open(self.get_user_metadata_path(user_id), 'rb') as f:
            metadata = pickle.load(f)
        
        # Filter out chunks for the document
        filtered_metadata = [
            m for m in metadata if m['document_id'] != document_id
        ]
        
        if len(filtered_metadata) == len(metadata):
            # No chunks to remove
            return
        
        # Rebuild index with remaining chunks
        if filtered_metadata:
            texts = [m['chunk_text'] for m in filtered_metadata]
            embeddings = self.create_embeddings_batch(texts)
            
            new_index = faiss.IndexFlatL2(self._embedding_dimension)
            embeddings_array = np.array(embeddings).astype('float32')
            new_index.add(embeddings_array)
            
            faiss.write_index(new_index, self.get_user_index_path(user_id))
        else:
            # Create empty index
            empty_index = faiss.IndexFlatL2(self._embedding_dimension)
            faiss.write_index(empty_index, self.get_user_index_path(user_id))
        
        # Save updated metadata
        with open(self.get_user_metadata_path(user_id), 'wb') as f:
            pickle.dump(filtered_metadata, f)
    
    def process_document_for_rag(
        self,
        db: Session,
        document: Document
    ) -> None:
        """Index a document and migrate any prior vectors to Gemini embeddings."""
        if (
            not os.path.exists(self.get_user_index_path(document.user_id))
            or not self._has_current_embedding_model(document.user_id)
        ):
            self._rebuild_user_vector_store(db, document.user_id)
            return

        # Get all chunks for the document
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).all()
        
        if not chunks:
            return
        
        # Add chunks to vector store
        self.add_chunks_to_vector_store(document.user_id, chunks)


# Global RAG service instance
rag_service = RAGService()
