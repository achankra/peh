"""
RAG Pipeline: Retrieval-Augmented Generation for AI-powered platform documentation.

This module implements a production-grade RAG system that:
1. Loads markdown documentation
2. Creates semantic embeddings (OpenAI or local)
3. Stores vectors in ChromaDB or Pinecone
4. Retrieves relevant context for user queries
5. Generates answers using LLM
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from langchain.document_loaders import DirectoryLoader, TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings.openai import OpenAIEmbeddings
    from langchain.embeddings.huggingface import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma, Pinecone
    from langchain.chains import RetrievalQA
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    import chromadb
except ImportError:
    chromadb = None


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class RetrievalResult:
    """Result from vector store retrieval."""
    query: str
    context_documents: List[str]
    confidence_scores: List[float]
    answer: str
    source_citations: List[str]
    retrieval_time_ms: float


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline for platform documentation.

    Supports multiple vector databases and embedding models.
    """

    def __init__(
        self,
        vector_db: str = "chromadb",
        embedding_model: str = "openai",
        collection_name: str = "platform_docs",
        similarity_threshold: float = 0.6,
    ):
        """
        Initialize RAG pipeline.

        Args:
            vector_db: "chromadb" or "pinecone"
            embedding_model: "openai" or "huggingface"
            collection_name: Vector store collection name
            similarity_threshold: Minimum similarity score for retrieval
        """
        self.vector_db_type = vector_db
        self.collection_name = collection_name
        self.similarity_threshold = similarity_threshold
        self.documents_indexed = 0

        # Initialize embeddings
        self.embeddings = self._init_embeddings(embedding_model)

        # Initialize vector store
        self.vector_store = self._init_vector_store()

        # Initialize LLM
        self.llm = self._init_llm()

    def _init_embeddings(self, model: str):
        """Initialize embedding model."""
        if model == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning(
                    "OPENAI_API_KEY not set. Using mock embeddings for demo."
                )
                return MockEmbeddings()
            return OpenAIEmbeddings(model="text-embedding-3-small")
        elif model == "huggingface":
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        else:
            return MockEmbeddings()

    def _init_vector_store(self):
        """Initialize vector store."""
        if self.vector_db_type == "chromadb":
            return ChromaDBStore(
                embeddings=self.embeddings,
                collection_name=self.collection_name
            )
        elif self.vector_db_type == "pinecone":
            return PineconeStore(
                embeddings=self.embeddings,
                collection_name=self.collection_name
            )
        else:
            return MockVectorStore(embeddings=self.embeddings)

    def _init_llm(self):
        """Initialize language model."""
        if os.getenv("OPENAI_API_KEY"):
            return ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=1000
            )
        return MockLLM()

    def index_documents(self, doc_paths: List[str] | str, chunk_size: int = 1024):
        """
        Index documents from filesystem.

        Args:
            doc_paths: Single path or list of paths to documents
            chunk_size: Chunk size for text splitting
        """
        if isinstance(doc_paths, str):
            doc_paths = [doc_paths]

        documents = []
        for doc_path in doc_paths:
            path = Path(doc_path)
            if path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        'content': content,
                        'source': str(path),
                        'type': 'file'
                    })
            elif path.is_dir():
                # Load all markdown and text files
                for file in path.rglob('*.md'):
                    with open(file, 'r', encoding='utf-8') as f:
                        documents.append({
                            'content': f.read(),
                            'source': str(file),
                            'type': 'file'
                        })

        # Split documents into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = []
        for doc in documents:
            texts = splitter.split_text(doc['content'])
            for text in texts:
                chunks.append({
                    'content': text,
                    'source': doc['source'],
                    'type': doc['type']
                })

        # Add to vector store
        self.vector_store.add_documents(chunks)
        self.documents_indexed = len(chunks)

        logger.info(f"Indexed {len(chunks)} document chunks from {len(documents)} files")
        return len(chunks)

    def index_json_data(self, data: List[Dict]):
        """
        Index structured data from JSON.

        Args:
            data: List of document dictionaries with 'content' and 'title' keys
        """
        chunks = []
        for item in data:
            content = item.get('content', '')
            title = item.get('title', 'Unknown')

            # Create structured chunks
            chunks.append({
                'content': f"Title: {title}\n\n{content}",
                'source': title,
                'type': 'json',
                'metadata': item.get('metadata', {})
            })

        self.vector_store.add_documents(chunks)
        logger.info(f"Indexed {len(chunks)} JSON documents")
        return len(chunks)

    def query(
        self,
        query: str,
        top_k: int = 3,
        include_confidence: bool = True
    ) -> RetrievalResult:
        """
        Query the RAG system.

        Args:
            query: User query string
            top_k: Number of relevant documents to retrieve
            include_confidence: Include similarity confidence scores

        Returns:
            RetrievalResult with context, answer, and citations
        """
        import time
        start_time = time.time()

        # Retrieve relevant documents
        retrieved_docs, scores = self.vector_store.retrieve(
            query=query,
            top_k=top_k
        )

        # Filter by similarity threshold
        filtered_docs = []
        filtered_scores = []
        for doc, score in zip(retrieved_docs, scores):
            if score >= self.similarity_threshold:
                filtered_docs.append(doc)
                filtered_scores.append(score)

        # Build context from retrieved documents
        context = "\n\n---\n\n".join(filtered_docs)
        sources = self._extract_sources(filtered_docs)

        # Generate answer using LLM
        answer = self._generate_answer(query, context)

        retrieval_time = (time.time() - start_time) * 1000

        return RetrievalResult(
            query=query,
            context_documents=filtered_docs,
            confidence_scores=filtered_scores,
            answer=answer,
            source_citations=sources,
            retrieval_time_ms=retrieval_time
        )

    def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with context."""
        prompt = f"""Based on the following context, answer the user's question.
If the context doesn't contain relevant information, say so clearly.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

        try:
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Unable to generate answer. Please try again."

    def _extract_sources(self, documents: List[str]) -> List[str]:
        """Extract source citations from documents."""
        sources = set()
        for doc in documents:
            # Try to extract metadata or filename from document
            lines = doc.split('\n')
            if lines and lines[0].startswith('File:'):
                sources.add(lines[0].replace('File:', '').strip())
        return list(sources)

    def batch_query(self, queries: List[str]) -> List[RetrievalResult]:
        """Process multiple queries efficiently."""
        return [self.query(q) for q in queries]

    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        return {
            'documents_indexed': self.documents_indexed,
            'vector_db_type': self.vector_db_type,
            'embedding_model': self.embeddings.__class__.__name__,
            'similarity_threshold': self.similarity_threshold,
            'timestamp': datetime.now().isoformat()
        }


class ChromaDBStore:
    """Wrapper for ChromaDB vector store."""

    def __init__(self, embeddings, collection_name: str):
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.client = chromadb.Client() if chromadb else None
        self.collection = None

    def add_documents(self, documents: List[Dict]):
        """Add documents to collection."""
        if not self.client:
            logger.warning("ChromaDB not available")
            return

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        for i, doc in enumerate(documents):
            embedding = self.embeddings.embed_query(doc['content'])
            self.collection.add(
                ids=[f"doc_{i}"],
                embeddings=[embedding],
                metadatas=[{
                    'source': doc.get('source', ''),
                    'type': doc.get('type', '')
                }],
                documents=[doc['content']]
            )

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[str], List[float]]:
        """Retrieve similar documents."""
        if not self.collection:
            return [], []

        try:
            embedding = self.embeddings.embed_query(query)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k
            )

            documents = results.get('documents', [[]])[0]
            distances = results.get('distances', [[]])[0]

            # Convert distances to similarity scores (1 - distance for cosine)
            scores = [1 - d for d in distances]

            return documents, scores
        except Exception as e:
            logger.error(f"Error retrieving from ChromaDB: {e}")
            return [], []


class PineconeStore:
    """Wrapper for Pinecone vector store."""

    def __init__(self, embeddings, collection_name: str):
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.index = None

        try:
            import pinecone
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                logger.warning("PINECONE_API_KEY not set")
                return

            pinecone.init(api_key=api_key)
            self.index = pinecone.Index(self.collection_name)
        except ImportError:
            logger.warning("Pinecone not installed")

    def add_documents(self, documents: List[Dict]):
        """Add documents to Pinecone."""
        if not self.index:
            logger.warning("Pinecone not configured")
            return

        vectors = []
        for i, doc in enumerate(documents):
            embedding = self.embeddings.embed_query(doc['content'])
            vectors.append((
                f"doc_{i}",
                embedding,
                {
                    'source': doc.get('source', ''),
                    'content': doc['content'][:500]  # Metadata size limit
                }
            ))

        self.index.upsert(vectors=vectors)

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[str], List[float]]:
        """Retrieve similar documents."""
        if not self.index:
            return [], []

        try:
            embedding = self.embeddings.embed_query(query)
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True
            )

            documents = [m['metadata']['content'] for m in results['matches']]
            scores = [m['score'] for m in results['matches']]

            return documents, scores
        except Exception as e:
            logger.error(f"Error retrieving from Pinecone: {e}")
            return [], []


class MockEmbeddings:
    """Mock embeddings for testing without OpenAI."""

    def embed_query(self, text: str) -> List[float]:
        """Return mock embedding."""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        # Generate deterministic embedding based on text hash
        seed = int(hash_obj.hexdigest()[:8], 16)
        import random
        random.seed(seed)
        return [random.random() for _ in range(384)]


class MockVectorStore:
    """Mock vector store for testing."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.documents = []

    def add_documents(self, documents: List[Dict]):
        self.documents.extend(documents)

    def retrieve(self, query: str, top_k: int = 3) -> Tuple[List[str], List[float]]:
        # Return mock results
        if not self.documents:
            return [], []

        results = [
            self.documents[i % len(self.documents)]['content']
            for i in range(min(top_k, len(self.documents)))
        ]
        scores = [0.8 - (i * 0.1) for i in range(len(results))]
        return results, scores


class MockLLM:
    """Mock LLM for testing without OpenAI."""

    def invoke(self, prompt: str) -> str:
        """Return mock response."""
        return "This is a mock answer generated without API access. " \
               "Based on the context provided, this would typically contain " \
               "a comprehensive answer to your question."


if __name__ == "__main__":
    # Example usage
    rag = RAGPipeline(vector_db="chromadb")

    # Index sample documentation
    sample_docs = [
        {
            "title": "Deployment Guide",
            "content": """
            # Deployment Guide

            ## Prerequisites
            - Docker installed
            - Kubernetes cluster access
            - Helm 3.x

            ## Deployment Steps
            1. Build image: docker build -t myapp:1.0 .
            2. Push to registry: docker push registry/myapp:1.0
            3. Deploy with Helm: helm install myapp ./chart

            ## Verification
            - Check pod status: kubectl get pods
            - Check logs: kubectl logs <pod-name>
            """
        },
        {
            "title": "Troubleshooting",
            "content": """
            # Troubleshooting Guide

            ## Common Issues

            ### Pod CrashLoopBackOff
            - Check resource limits
            - Review pod logs
            - Verify image availability

            ### Service Unavailable
            - Check service endpoints
            - Verify network policies
            - Test DNS resolution
            """
        }
    ]

    rag.index_json_data(sample_docs)

    # Query the system
    result = rag.query("How do I deploy to Kubernetes?")
    print(f"Query: {result.query}")
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence_scores}")
    print(f"Sources: {result.source_citations}")
    print(f"Time: {result.retrieval_time_ms}ms")
