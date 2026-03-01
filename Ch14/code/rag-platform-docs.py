#!/usr/bin/env python3
"""
RAG Platform Documentation System.

Implements Retrieval-Augmented Generation for platform documentation:
- Indexes markdown documentation into a searchable format
- Retrieves relevant context for user queries
- Optionally augments responses with LLM summarization

This demo uses TF-IDF for retrieval. Production systems would use embeddings
(OpenAI, local BERT, etc.) for semantic similarity.
"""

import os
import json
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import Counter
import re


@dataclass
class Document:
    """Represents a documentation page or section."""
    id: str
    title: str
    content: str
    section: str
    tags: List[str]


class SimpleTokenizer:
    """Basic tokenizer for TF-IDF."""

    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may',
        'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where'
    }

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize text into words."""
        # Convert to lowercase and split on non-alphanumeric
        words = re.findall(r'\b\w+\b', text.lower())

        # Remove stop words and short words
        tokens = [
            w for w in words
            if w not in SimpleTokenizer.STOP_WORDS and len(w) > 2
        ]

        return tokens


class TFIDFRetriever:
    """Simple TF-IDF based document retriever."""

    def __init__(self):
        """Initialize retriever."""
        self.documents: Dict[str, Document] = {}
        self.tf_vectors: Dict[str, Dict[str, float]] = {}
        self.idf: Dict[str, float] = {}
        self.vocab: set = set()

    def add_document(self, document: Document) -> None:
        """Add a document to the index."""
        self.documents[document.id] = document

        # Tokenize and compute TF
        tokens = SimpleTokenizer.tokenize(document.content)
        token_freq = Counter(tokens)

        # Normalize TF
        total = sum(token_freq.values())
        tf_vector = {}
        for token, freq in token_freq.items():
            tf_vector[token] = freq / total if total > 0 else 0
            self.vocab.add(token)

        self.tf_vectors[document.id] = tf_vector

    def compute_idf(self) -> None:
        """Compute IDF values."""
        doc_count = len(self.documents)

        # Count documents containing each term
        term_docs = {}
        for doc_id, tf_vec in self.tf_vectors.items():
            for token in tf_vec.keys():
                term_docs[token] = term_docs.get(token, 0) + 1

        # Compute IDF
        for token in self.vocab:
            doc_freq = term_docs.get(token, 1)
            self.idf[token] = math.log(doc_count / doc_freq) if doc_freq > 0 else 0

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """
        Retrieve top-k documents for a query.

        Args:
            query: User query
            k: Number of documents to retrieve

        Returns:
            List of (document, relevance_score) tuples
        """
        if not self.documents:
            return []

        # Compute query vector
        query_tokens = SimpleTokenizer.tokenize(query)
        query_freq = Counter(query_tokens)

        total = sum(query_freq.values())
        query_tf = {}
        for token, freq in query_freq.items():
            query_tf[token] = freq / total if total > 0 else 0

        query_tfidf = {}
        for token, tf in query_tf.items():
            idf = self.idf.get(token, 0)
            query_tfidf[token] = tf * idf

        # Compute similarity to each document
        scores = []
        for doc_id, doc in self.documents.items():
            doc_tfidf = self.tf_vectors[doc_id]

            # Cosine similarity
            dot_product = 0
            for token, q_val in query_tfidf.items():
                if token in doc_tfidf:
                    dot_product += q_val * doc_tfidf[token]

            # Compute norms
            query_norm = math.sqrt(sum(v**2 for v in query_tfidf.values()))
            doc_norm = math.sqrt(sum(v**2 for v in doc_tfidf.values()))

            if query_norm > 0 and doc_norm > 0:
                similarity = dot_product / (query_norm * doc_norm)
            else:
                similarity = 0

            scores.append((doc, similarity))

        # Sort by similarity and return top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class RAGSystem:
    """RAG system combining retrieval and augmentation."""

    def __init__(self):
        """Initialize RAG system."""
        self.retriever = TFIDFRetriever()
        self.queries: List[Dict] = []

    def add_documentation(self, documents: List[Document]) -> None:
        """
        Add documentation to the system.

        Args:
            documents: List of documents to index
        """
        for doc in documents:
            self.retriever.add_document(doc)

        self.retriever.compute_idf()

    def query(self, question: str, k: int = 3) -> Dict:
        """
        Query the documentation system.

        Args:
            question: User question
            k: Number of documents to retrieve

        Returns:
            Result dict with context and answer
        """
        # Retrieve relevant documents
        results = self.retriever.retrieve(question, k=k)

        context = "\n\n".join([
            f"[{doc.title}]\n{doc.content[:500]}..."
            for doc, score in results
        ])

        answer = self._generate_answer(question, context)

        query_result = {
            'question': question,
            'context_documents': len(results),
            'retrieved_docs': [
                {
                    'title': doc.title,
                    'section': doc.section,
                    'score': float(score)
                }
                for doc, score in results
            ],
            'answer': answer
        }

        self.queries.append(query_result)
        return query_result

    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer based on context.

        In production, this would call an LLM. For demo, use heuristics.
        """
        # Try LLM first
        llm_answer = self._try_llm_answer(question, context)
        if llm_answer:
            return llm_answer

        # Fallback to template-based answer
        return self._template_answer(question, context)

    def _try_llm_answer(self, question: str, context: str) -> Optional[str]:
        """Try to get answer from LLM if available."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None

        try:
            import json as json_module
            # Mock LLM call for demo
            return None
        except:
            return None

    def _template_answer(self, question: str, context: str) -> str:
        """Generate answer using templates."""
        # Simple heuristics for common questions
        q_lower = question.lower()

        if 'how' in q_lower and 'deploy' in q_lower:
            return (
                "To deploy to the platform: "
                "1. Push your code to the main branch "
                "2. Wait for CI/CD pipeline to complete "
                "3. Rollout is automatic or manual based on service config. "
                "See deployment docs for more details."
            )
        elif 'error' in q_lower or 'fix' in q_lower:
            return (
                "Check the relevant section for troubleshooting steps. "
                "Common issues include configuration errors and dependency conflicts. "
                "See logs for specific error messages."
            )
        elif 'monitor' in q_lower or 'alert' in q_lower:
            return (
                "The platform provides built-in monitoring and alerting. "
                "Configure dashboards in your service definition. "
                "Set thresholds for metrics you want to track."
            )
        else:
            return (
                f"Based on the documentation, {context[:200]}... "
                "For more details, consult the full documentation sections provided."
            )


def create_sample_docs() -> List[Document]:
    """Create sample platform documentation."""
    return [
        Document(
            id="deploy-guide",
            title="Deployment Guide",
            section="Getting Started",
            content="""
            Deploying applications to the platform is straightforward.

            1. Prepare your application with a Dockerfile and service definition.
            2. Push to the main branch - our CI/CD automatically builds and tests.
            3. Deployment is automatic based on your service configuration.
            4. Monitor health through dashboards and set up alerts.

            For canary deployments, specify canary_percentage in config.
            For blue-green deployments, use the deployment strategy field.
            Rollbacks are automatic on health check failures.
            """,
            tags=["deployment", "ci-cd", "getting-started"]
        ),
        Document(
            id="monitoring-guide",
            title="Monitoring and Observability",
            section="Operations",
            content="""
            The platform provides comprehensive monitoring capabilities.

            Key components:
            - Metrics collection via Prometheus exporters
            - Log aggregation using ELK stack
            - Distributed tracing with Jaeger
            - Custom dashboards in Grafana

            Define metrics in your service config. Alert rules are auto-generated.
            Set thresholds for CPU, memory, latency, and error rate.
            Use annotations to add context to dashboards.

            Common metrics: request_duration, error_rate, cpu_percent, memory_mb.
            Query metrics using Prometheus QL (PromQL).
            """,
            tags=["monitoring", "observability", "metrics", "alerts"]
        ),
        Document(
            id="troubleshoot",
            title="Troubleshooting Common Issues",
            section="Operations",
            content="""
            Common problems and solutions:

            High CPU Usage: Check for infinite loops or unbounded growth.
            Review metrics in dashboard. Profile if needed.

            Memory Leaks: Monitor heap size. Use profiling tools.
            Java: Enable JVM flags for garbage collection logs.

            Service Won't Start: Check logs. Verify environment variables.
            Ensure ports aren't in use. Check permission issues.

            Slow Queries: Enable query logging. Check indexes.
            Use explain plan. Consider caching.

            Network Issues: Check security group rules. Verify DNS resolution.
            Review proxy configuration.
            """,
            tags=["troubleshooting", "debugging", "operations"]
        ),
        Document(
            id="scaling-guide",
            title="Scaling and Performance",
            section="Advanced",
            content="""
            Scale your application horizontally or vertically.

            Horizontal Scaling:
            - Increase replica count for your service
            - Load balancer automatically distributes traffic
            - Recommended for stateless services

            Vertical Scaling:
            - Increase CPU and memory per replica
            - For stateful services or batch jobs

            Auto-scaling:
            - Set min/max replicas
            - Scale based on CPU, memory, or custom metrics
            - Cooldown period prevents thrashing

            Performance best practices:
            - Use caching (Redis) for frequently accessed data
            - Implement connection pooling
            - Batch database operations
            - Enable compression for large responses
            """,
            tags=["scaling", "performance", "advanced"]
        ),
        Document(
            id="security",
            title="Security and Access Control",
            section="Operations",
            content="""
            Platform security features:

            Authentication: OIDC integration with your identity provider.
            Authorization: RBAC with fine-grained permissions.
            Network: Service mesh with mTLS between services.
            Secrets: Encrypted at rest, rotated automatically.

            Best practices:
            - Never commit secrets to version control
            - Use secrets manager for sensitive data
            - Enable audit logging
            - Regular security scans on dependencies
            - Keep images updated

            Compliance: HIPAA, SOC2, PCI-DSS certified platform.
            """,
            tags=["security", "compliance", "authentication"]
        ),
    ]


def main():
    """Demonstrate RAG system."""
    print("=" * 70)
    print("RAG Platform Documentation System Demo")
    print("=" * 70)

    # Create and initialize system
    rag = RAGSystem()
    docs = create_sample_docs()

    print(f"\nIndexing {len(docs)} documentation pages...")
    rag.add_documentation(docs)
    print("Ready for queries.\n")

    # Sample queries
    queries = [
        "How do I deploy my application?",
        "What monitoring tools are available?",
        "My service has high CPU usage, how do I fix it?",
        "How do I scale my application?",
        "What security features does the platform have?",
    ]

    print("-" * 70)
    print("Sample Queries and Responses:")
    print("-" * 70)

    for question in queries:
        result = rag.query(question)

        print(f"\nQ: {question}")
        print(f"A: {result['answer']}")
        print(f"   (Retrieved {len(result['retrieved_docs'])} docs)")

        for doc in result['retrieved_docs']:
            print(f"     - {doc['title']} ({doc['score']:.2f})")

    print("\n" + "-" * 70)
    print("Statistics:")
    print(f"  Total queries: {len(rag.queries)}")
    print(f"  Avg docs per query: {sum(len(q['retrieved_docs']) for q in rag.queries) / len(rag.queries):.1f}")


if __name__ == "__main__":
    main()
