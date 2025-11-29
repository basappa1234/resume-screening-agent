"""
Vector Database for Semantic Similarity Matching
Uses FAISS and Sentence Transformers for efficient similarity search
Now with hybrid search combining keyword matching and vector similarity
"""
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import json
import os
import re
from collections import Counter

class VectorDatabase:
    """Vector database for semantic similarity matching of resumes and job descriptions"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the vector database
        
        Args:
            model_name: Sentence transformer model to use for embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.documents = []  # Store document metadata
        self.doc_ids = []    # Store document IDs
        
    def add_documents(self, documents: List[Dict]) -> None:
        """
        Add documents to the vector database
        
        Args:
            documents: List of document dictionaries with 'id', 'content', and metadata
        """
        texts = [doc['content'] for doc in documents]
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype(np.float32))
        
        # Store metadata
        for doc in documents:
            self.documents.append(doc)
            self.doc_ids.append(doc['id'])
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype(np.float32), k)
        
        # Return results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.documents):  # Check bounds
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def get_document_count(self) -> int:
        """Get the number of documents in the database"""
        return len(self.documents)
    
    def clear(self) -> None:
        """Clear the database"""
        self.index.reset()
        self.documents = []
        self.doc_ids = []

class HybridSearchEngine:
    """Hybrid search engine combining keyword matching and vector similarity"""
    
    def __init__(self):
        """Initialize the hybrid search engine"""
        self.vector_db = VectorDatabase()
        self.keyword_index = {}  # Simple inverted index for keyword search
        self.documents = {}      # Store all documents by ID
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text (simple approach)
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - can be enhanced with NLP techniques
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords
    
    def _build_keyword_index(self, doc_id: str, content: str) -> None:
        """
        Build keyword index for a document
        
        Args:
            doc_id: Document ID
            content: Document content
        """
        keywords = self._extract_keywords(content)
        keyword_counts = Counter(keywords)
        
        # Add to inverted index
        for keyword, count in keyword_counts.items():
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = {}
            self.keyword_index[keyword][doc_id] = count
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> None:
        """
        Add a document to the hybrid search engine
        
        Args:
            doc_id: Document ID
            content: Document content
            metadata: Additional metadata
        """
        # Store document
        document = {
            'id': doc_id,
            'content': content,
            'metadata': metadata or {}
        }
        self.documents[doc_id] = document
        
        # Build keyword index
        self._build_keyword_index(doc_id, content)
        
        # Add to vector database
        self.vector_db.add_documents([document])
    
    def keyword_search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Perform keyword search
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document_id, score) tuples
        """
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []
        
        # Calculate scores for each document
        doc_scores = {}
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for doc_id, count in self.keyword_index[keyword].items():
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0
                    doc_scores[doc_id] += count
        
        # Sort by score and return top k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_docs[:k]
    
    def hybrid_search(self, query: str, k: int = 10, keyword_weight: float = 0.3, vector_weight: float = 0.7) -> List[Tuple[Dict, float]]:
        """
        Perform hybrid search combining keyword and vector similarity
        
        Args:
            query: Search query
            k: Number of results to return
            keyword_weight: Weight for keyword matching (0.0 to 1.0)
            vector_weight: Weight for vector similarity (0.0 to 1.0)
            
        Returns:
            List of (document, combined_score) tuples
        """
        # Get keyword search results
        keyword_results = self.keyword_search(query, k * 2)  # Get more candidates
        keyword_scores = dict(keyword_results)
        
        # Get vector search results
        vector_results = self.vector_db.search(query, k * 2)  # Get more candidates
        vector_scores = {doc['id']: score for doc, score in vector_results}
        
        print(f"Keyword search returned {len(keyword_results)} results")
        print(f"Vector search returned {len(vector_results)} results")
        
        # Combine scores using weighted average
        all_doc_ids = set(list(keyword_scores.keys()) + list(vector_scores.keys()))
        combined_scores = {}
        
        # Get max scores for normalization (avoid division by zero)
        max_keyword_score = max(keyword_scores.values()) if keyword_scores else 1
        max_vector_score = max(vector_scores.values()) if vector_scores else 1
        
        # Ensure we don't divide by zero
        if max_keyword_score == 0:
            max_keyword_score = 1
        if max_vector_score == 0:
            max_vector_score = 1
        
        for doc_id in all_doc_ids:
            # Normalize scores (0-1 range)
            norm_keyword = keyword_scores.get(doc_id, 0) / max_keyword_score
            norm_vector = vector_scores.get(doc_id, 0) / max_vector_score
            
            # Calculate weighted combined score
            combined_score = (keyword_weight * norm_keyword) + (vector_weight * norm_vector)
            combined_scores[doc_id] = combined_score
        
        # Sort by combined score and return top k
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Combined search returned {len(sorted_docs)} results, returning top {min(k, len(sorted_docs))}")
        
        # Get document details
        results = []
        for doc_id, score in sorted_docs[:k]:
            if doc_id in self.documents:
                results.append((self.documents[doc_id], score))
        
        return results
    
    def get_document_count(self) -> int:
        """Get the number of documents in the database"""
        return len(self.documents)

class ResumeRetriever:
    """Retrieval system for resume screening using hybrid search"""
    
    def __init__(self):
        """Initialize the retriever with hybrid search engine"""
        self.search_engine = HybridSearchEngine()
        self.job_descriptions = {}  # Store job descriptions by ID
    
    def index_resume(self, resume: Dict) -> None:
        """
        Index a single resume in the search engine
        
        Args:
            resume: Resume dictionary
        """
        # Create a comprehensive text representation
        content = self._create_resume_content(resume)
        
        # Ensure we have a valid document ID
        doc_id = resume.get('id') or f"resume_{len(self.search_engine.documents)}"
        
        # Add to search engine
        self.search_engine.add_document(
            doc_id=doc_id,
            content=content,
            metadata={'type': 'resume', 'resume_data': resume}
        )
    
    def index_resumes(self, resumes: List[Dict]) -> None:
        """
        Index resumes in the search engine
        
        Args:
            resumes: List of resume dictionaries
        """
        resume_count = 0
        for resume in resumes:
            self.index_resume(resume)
            resume_count += 1
        
        print(f"Indexed {resume_count} resumes in hybrid search engine")
        print(f"Total documents in search engine: {len(self.search_engine.documents)}")
    
    def index_job_description(self, job_desc: Dict) -> str:
        """
        Index a job description
        
        Args:
            job_desc: Job description dictionary
            
        Returns:
            Job description ID
        """
        # Create a comprehensive text representation
        content = self._create_job_description_content(job_desc)
        
        # Store job description
        job_id = f"job_{len(self.job_descriptions)}"
        self.job_descriptions[job_id] = job_desc
        
        # Index in search engine
        self.search_engine.add_document(
            doc_id=job_id,
            content=content,
            metadata={'type': 'job_description', 'job_data': job_desc}
        )
        
        print(f"Indexed job description: {job_desc.get('title', 'Unknown')}")
        return job_id
    
    def retrieve_candidates(self, job_desc: Dict, top_k: int = 20) -> List[Dict]:
        """
        Retrieve candidates using hybrid search
        
        Args:
            job_desc: Job description dictionary
            top_k: Number of candidates to retrieve
            
        Returns:
            List of candidate resumes
        """
        # Create job description content
        query_content = self._create_job_description_content(job_desc)
        
        # Perform hybrid search
        results = self.search_engine.hybrid_search(query_content, top_k)
        
        print(f"Hybrid search returned {len(results)} total results")
        
        # Extract resume metadata
        candidates = []
        for doc, score in results:
            if doc['metadata'].get('type') == 'resume':
                resume = doc['metadata']['resume_data'].copy()
                resume['hybrid_score'] = score
                candidates.append(resume)
        
        print(f"Retrieved {len(candidates)} candidates using hybrid search")
        return candidates
    
    def _create_resume_content(self, resume: Dict) -> str:
        """
        Create a comprehensive text representation of a resume
        
        Args:
            resume: Resume dictionary
            
        Returns:
            Comprehensive text content
        """
        content_parts = []
        
        # Add basic info
        if resume.get('name'):
            content_parts.append(f"Name: {resume.get('name')}")
        
        if resume.get('summary'):
            content_parts.append(f"Summary: {resume.get('summary')}")
        
        # Add skills
        if resume.get('skills'):
            skills = ', '.join(resume.get('skills', []))
            content_parts.append(f"Skills: {skills}")
        
        # Add experience
        if resume.get('experience'):
            exp_texts = []
            for exp in resume.get('experience', []):
                exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get('description'):
                    exp_text += f" - {exp.get('description')}"
                exp_texts.append(exp_text)
            content_parts.append(f"Experience: {'; '.join(exp_texts)}")
        
        # Add education
        if resume.get('education'):
            edu_texts = []
            for edu in resume.get('education', []):
                edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}"
                edu_texts.append(edu_text)
            content_parts.append(f"Education: {'; '.join(edu_texts)}")
        
        return '. '.join(content_parts)
    
    def _create_job_description_content(self, job_desc: Dict) -> str:
        """
        Create a comprehensive text representation of a job description
        
        Args:
            job_desc: Job description dictionary
            
        Returns:
            Comprehensive text content
        """
        content_parts = []
        
        # Add basic info
        if job_desc.get('title'):
            content_parts.append(f"Job Title: {job_desc.get('title')}")
        
        if job_desc.get('company'):
            content_parts.append(f"Company: {job_desc.get('company')}")
        
        if job_desc.get('description'):
            content_parts.append(f"Description: {job_desc.get('description')}")
        
        # Add required skills
        if job_desc.get('required_skills'):
            skills = ', '.join(job_desc.get('required_skills', []))
            content_parts.append(f"Required Skills: {skills}")
        
        # Add preferred skills
        if job_desc.get('preferred_skills'):
            skills = ', '.join(job_desc.get('preferred_skills', []))
            content_parts.append(f"Preferred Skills: {skills}")
        
        # Add responsibilities
        if job_desc.get('responsibilities'):
            resp = '; '.join(job_desc.get('responsibilities', []))
            content_parts.append(f"Responsibilities: {resp}")
        
        # Add qualifications
        if job_desc.get('qualifications'):
            qual = '; '.join(job_desc.get('qualifications', []))
            content_parts.append(f"Qualifications: {qual}")
        
        return '. '.join(content_parts)