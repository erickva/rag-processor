"""
RAG Document Processing System

A revolutionary standardized approach to RAG document processing that solves
fundamental chunking problems through declarative processing instructions.

Based on proven real-world success fixing semantic search issues.
"""

__version__ = "0.1.0"
__author__ = "RAG Processor Contributors"

from .core.processor import RAGDocumentProcessor
from .core.analyzer import DocumentAnalyzer, DocumentType
from .core.validator import ValidationEngine

__all__ = [
    "RAGDocumentProcessor",
    "DocumentAnalyzer", 
    "DocumentType",
    "ValidationEngine",
]