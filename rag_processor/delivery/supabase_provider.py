"""
Supabase vector database delivery provider.

Uploads chunks with embeddings to Supabase's pgvector extension.
"""

import os
from typing import List, Dict, Any, Optional
import json

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

from .base import DeliveryProvider, DeliveryResult, EmbeddingProvider
from ..utils.text_utils import ChunkMetadata
from config.constants import (
    DEFAULT_BATCH_SIZE, ERROR_MISSING_API_KEY, ERROR_CONNECTION_FAILED,
    DEFAULT_SUPABASE_TABLE_SCHEMA
)


class SupabaseProvider(DeliveryProvider):
    """Supabase vector database delivery provider."""
    
    def __init__(
        self, 
        embedding_provider: EmbeddingProvider,
        url: Optional[str] = None,
        key: Optional[str] = None
    ):
        """
        Initialize Supabase provider.
        
        Args:
            embedding_provider: Provider for generating embeddings
            url: Supabase project URL (if not provided, reads from SUPABASE_URL env var)
            key: Supabase anon key (if not provided, reads from SUPABASE_KEY env var)
        """
        if not HAS_SUPABASE:
            raise ImportError("supabase package required. Install with: pip install supabase")
        
        super().__init__(embedding_provider)
        
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url:
            raise ValueError(ERROR_MISSING_API_KEY.format(env_var="SUPABASE_URL"))
        if not self.key:
            raise ValueError(ERROR_MISSING_API_KEY.format(env_var="SUPABASE_KEY"))
        
        self.client: Optional[Client] = None
    
    @property
    def name(self) -> str:
        """Provider name."""
        return "supabase"
    
    def connect(self, **kwargs) -> bool:
        """Establish connection to Supabase."""
        try:
            self.client = create_client(self.url, self.key)
            return self.test_connection()
        except Exception as e:
            print(f"Failed to connect to Supabase: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test if connection is working."""
        if not self.client:
            return False
        
        try:
            # Simple test query
            response = self.client.table("_supabase_migrations").select("*").limit(1).execute()
            return True
        except Exception:
            # Table might not exist, try a basic auth check
            try:
                self.client.auth.get_session()
                return True
            except Exception:
                return False
    
    def upload_chunks(
        self, 
        chunks: List[ChunkMetadata], 
        table_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """
        Upload chunks with embeddings to Supabase table.
        
        Args:
            chunks: List of text chunks with metadata
            table_name: Supabase table name
            metadata: Additional metadata to attach to all chunks
            
        Returns:
            DeliveryResult with upload status and statistics
        """
        if not self.client:
            if not self.connect():
                return DeliveryResult(
                    success=False,
                    chunks_uploaded=0,
                    errors=["Failed to connect to Supabase"],
                    provider=self.name,
                    destination=f"{self.url}/{table_name}",
                    metadata={}
                )
        
        try:
            # Prepare chunks with embeddings
            prepared_chunks = self.prepare_chunk_data(chunks, metadata)
            
            # Format for Supabase insertion
            supabase_rows = []
            for chunk_data in prepared_chunks:
                row = {
                    "content": chunk_data["text"],
                    "embedding": chunk_data["embedding"],
                    "metadata": json.dumps(chunk_data["metadata"]),
                    "start_position": chunk_data["start_position"],
                    "end_position": chunk_data["end_position"],
                }
                supabase_rows.append(row)
            
            # Upload in batches to avoid hitting size limits
            batch_size = DEFAULT_BATCH_SIZE
            total_uploaded = 0
            errors = []
            
            for i in range(0, len(supabase_rows), batch_size):
                batch = supabase_rows[i:i + batch_size]
                
                try:
                    response = self.client.table(table_name).insert(batch).execute()
                    total_uploaded += len(batch)
                except Exception as e:
                    errors.append(f"Batch {i//batch_size + 1}: {str(e)}")
            
            success = total_uploaded > 0
            
            return DeliveryResult(
                success=success,
                chunks_uploaded=total_uploaded,
                errors=errors,
                provider=self.name,
                destination=f"{self.url}/{table_name}",
                metadata={
                    "embedding_model": getattr(self.embedding_provider, 'model', 'unknown'),
                    "embedding_dimension": self.embedding_provider.dimension,
                    "total_chunks": len(chunks),
                    "batches_processed": (len(supabase_rows) + batch_size - 1) // batch_size,
                }
            )
            
        except Exception as e:
            return DeliveryResult(
                success=False,
                chunks_uploaded=0,
                errors=[f"Upload failed: {str(e)}"],
                provider=self.name,
                destination=f"{self.url}/{table_name}",
                metadata={}
            )
    
    def create_table_if_not_exists(self, table_name: str) -> bool:
        """
        Create table with proper schema if it doesn't exist.
        
        Note: This requires database admin permissions. In production,
        tables should be created via Supabase dashboard or migrations.
        """
        if not self.client:
            return False
        
        try:
            # Check if table exists by trying to query it
            self.client.table(table_name).select("*").limit(1).execute()
            return True  # Table exists
        except Exception:
            # Table doesn't exist, but we can't create it via client
            # This would need to be done via SQL migrations
            print(f"Table '{table_name}' doesn't exist. Create it manually in Supabase with schema:")
            print(f"""
CREATE TABLE {table_name} (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR({self.embedding_provider.dimension}),
    metadata JSONB,
    start_position INTEGER,
    end_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON {table_name} USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
            """)
            return False