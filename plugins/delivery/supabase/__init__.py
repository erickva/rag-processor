"""
Supabase Delivery Plugin for RAG Document Processor.

This plugin provides integration with Supabase's pgvector extension for storing
document chunks with embeddings in a PostgreSQL database.

Features:
- Automatic embedding generation using OpenAI
- Batch uploads for performance
- Configurable table schemas
- Built-in retry logic and error handling
- Vector similarity search optimization

Requirements:
- Supabase project with pgvector extension enabled
- OpenAI API key for embedding generation
- Supabase URL and anon/service key

Installation:
    pip install supabase openai

Usage:
    rag-processor upload document.rag --to supabase --table products

Environment Variables:
    OPENAI_API_KEY: OpenAI API key for embeddings
    SUPABASE_URL: Your Supabase project URL
    SUPABASE_KEY: Supabase anon or service role key
"""

from .supabase_provider import SupabaseProvider
from .openai_embeddings import OpenAIEmbeddingProvider
from .base import DeliveryProvider, DeliveryResult, EmbeddingProvider

__all__ = [
    "SupabaseProvider",
    "OpenAIEmbeddingProvider", 
    "DeliveryProvider",
    "DeliveryResult",
    "EmbeddingProvider",
]

__version__ = "0.1.0"
__plugin_type__ = "delivery"
__plugin_name__ = "supabase"