"""Memory Retrieval Module

Handles embedding generation and vector search.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
import json

from memory import Memory, MemoryManager


class EmbeddingProvider:
    """Handles text embedding generation"""
    
    def __init__(self, model_name: str = "sentence-transformers/bge-small-zh-v1.5"):
        """Initialize embedding provider
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return [e.tolist() for e in embeddings]


class VectorStore:
    """Vector database wrapper using Chroma"""
    
    def __init__(self, persist_dir: str = "./data/chroma_db", embedding_provider: Optional[EmbeddingProvider] = None):
        """Initialize vector store
        
        Args:
            persist_dir: Directory to persist vector database
            embedding_provider: Custom embedding provider
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb not installed. Install with: pip install chroma-db")
        
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedding_provider = embedding_provider or EmbeddingProvider()
        
        # Initialize Chroma client using new PersistentClient API
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name="novel_memories",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_memory(self, memory: Memory) -> None:
        """Add memory to vector store
        
        Args:
            memory: Memory object to add
        """
        embedding = self.embedding_provider.embed(memory.content)
        metadata = {
            "type": memory.type,
            "created_at": memory.created_at,
            "memory_id": memory.id,
        }
        if memory.name:
            metadata["name"] = memory.name
        
        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            documents=[memory.content],
            metadatas=[metadata]
        )
    
    def update_memory(self, memory: Memory) -> None:
        """Update memory in vector store
        
        Args:
            memory: Updated memory object
        """
        self.delete_memory(memory.id)
        self.add_memory(memory)
    
    def delete_memory(self, memory_id: str) -> None:
        """Delete memory from vector store
        
        Args:
            memory_id: ID of memory to delete
        """
        try:
            self.collection.delete(ids=[memory_id])
        except Exception as e:
            print(f"Warning: Could not delete memory {memory_id}: {e}")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for memories by semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant memories with metadata
        """
        query_embedding = self.embedding_provider.embed(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        memories = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None,
                })
        
        return memories
    
    def search_by_type(self, query: str, memory_type: str, n_results: int = 5) -> List[Dict]:
        """Search for memories by type
        
        Args:
            query: Search query
            memory_type: Type filter (character, plot, callback)
            n_results: Number of results to return
            
        Returns:
            List of relevant memories of specified type
        """
        query_embedding = self.embedding_provider.embed(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            where={"type": memory_type},
            n_results=n_results
        )
        
        memories = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None,
                })
        
        return memories
    
    def persist(self) -> None:
        """Persist vector database to disk"""
        # PersistentClient automatically persists, so this is now a no-op
        # but kept for API compatibility
        pass


class MemoryRetriever:
    """High-level memory retrieval interface"""
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        """Initialize retriever
        
        Args:
            memory_manager: MemoryManager instance
            vector_store: VectorStore instance
        """
        self.memory_manager = memory_manager or MemoryManager()
        self.vector_store = vector_store or VectorStore()
    
    def search_memories(self, query: str, n_results: int = 5) -> List[Memory]:
        """Search for memories
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of Memory objects
        """
        search_results = self.vector_store.search(query, n_results=n_results)
        
        memories = []
        for result in search_results:
            memory = self.memory_manager.get_memory(result['id'])
            if memory:
                memories.append(memory)
        
        return memories
    
    def search_by_character(self, query: str, character_name: str, n_results: int = 5) -> List[Memory]:
        """Search memories for a specific character
        
        Args:
            query: Search query
            character_name: Character name filter
            n_results: Number of results
            
        Returns:
            List of Memory objects related to character
        """
        all_memories = self.memory_manager.get_memories_by_character(character_name)
        if not all_memories:
            return []
        
        # Combine character info with query
        enhanced_query = f"{character_name}: {query}"
        search_results = self.vector_store.search(enhanced_query, n_results=n_results)
        
        memories = []
        for result in search_results:
            memory = self.memory_manager.get_memory(result['id'])
            if memory and memory.type == "character" and memory.name == character_name:
                memories.append(memory)
        
        return memories
    
    def search_by_type(self, query: str, memory_type: str, n_results: int = 5) -> List[Memory]:
        """Search memories by type
        
        Args:
            query: Search query
            memory_type: Type filter (character, plot, callback)
            n_results: Number of results
            
        Returns:
            List of Memory objects
        """
        search_results = self.vector_store.search_by_type(query, memory_type, n_results=n_results)
        
        memories = []
        for result in search_results:
            memory = self.memory_manager.get_memory(result['id'])
            if memory:
                memories.append(memory)
        
        return memories
    
    def sync_memories_to_vector_db(self) -> None:
        """Sync all memories from manager to vector database"""
        all_memories = self.memory_manager.get_all_memories()
        for memory in all_memories:
            self.vector_store.add_memory(memory)
        self.vector_store.persist()
