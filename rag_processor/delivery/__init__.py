"""
Delivery system for uploading chunks to vector databases.

This is where the real value lives - taking chunked content and actually
delivering it to production vector databases where it can be searched.
"""

from .base import DeliveryProvider, DeliveryResult, EmbeddingProvider
from .supabase_provider import SupabaseProvider

__all__ = [
    "DeliveryProvider",
    "DeliveryResult", 
    "EmbeddingProvider",
    "SupabaseProvider",
]