"""
Configuration constants for RAG Document Processing System.

All magic numbers, thresholds, and configurable values are defined here.
"""

# Document Analysis Constants
MINIMUM_DOCUMENT_LENGTH = 100
MINIMUM_CHUNK_SIZE = 50
MAXIMUM_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200

# Pattern Detection Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.7
MEDIUM_CONFIDENCE_THRESHOLD = 0.4
PATTERN_FREQUENCY_MULTIPLIER = 1.5

# Processing Strategy Constants
PRODUCTS_CHUNK_OVERLAP = 0  # No overlap for semantic boundaries
MANUAL_CHUNK_OVERLAP = 150
FAQ_CHUNK_OVERLAP = 0       # No overlap for Q&A pairs  
ARTICLE_CHUNK_OVERLAP = 100
LEGAL_CHUNK_OVERLAP = 250
CODE_CHUNK_OVERLAP = 100

# Validation Constants
UTF8_ENCODING = "utf-8"
REQUIRED_FIELD_SCORE_BOOST = 2.0
PRICE_PATTERN_SCORE_BOOST = 2.5

# File Extension Constants
RAG_FILE_EXTENSION = ".rag"
BACKUP_EXTENSION = ".bak"

# CLI Constants
DEFAULT_OUTPUT_FORMAT = "json"
TEMPLATE_OUTPUT_DIR = "templates"
ANALYSIS_OUTPUT_DIR = "analysis"

# Error Messages
ERROR_INVALID_ENCODING = "Document must be valid UTF-8 encoded text"
ERROR_DOCUMENT_TOO_SHORT = f"Document must be at least {MINIMUM_DOCUMENT_LENGTH} characters"
ERROR_NO_STRATEGY_FOUND = "No suitable processing strategy could be determined"
ERROR_VALIDATION_FAILED = "Document validation failed"
ERROR_FILE_NOT_FOUND = "RAG document file not found"
ERROR_INVALID_DIRECTIVE = "Invalid processing directive format"

# Delivery System Constants
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
DEFAULT_BATCH_SIZE = 100
UPLOAD_TIMEOUT_SECONDS = 300
MAX_RETRY_ATTEMPTS = 3

# OpenAI Constants  
OPENAI_EMBEDDING_DIMENSIONS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

# Supabase Constants
DEFAULT_SUPABASE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR({dimension}),
    metadata JSONB,
    start_position INTEGER,
    end_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
ON {table_name} USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""

# Success Messages  
SUCCESS_DOCUMENT_PROCESSED = "Document processed successfully"
SUCCESS_VALIDATION_PASSED = "Document validation passed"
SUCCESS_TEMPLATE_CREATED = "Template created successfully"
SUCCESS_UPLOAD_COMPLETED = "Chunks uploaded successfully to vector database"

# Delivery Error Messages
ERROR_MISSING_API_KEY = "API key required. Set environment variable: {env_var}"
ERROR_CONNECTION_FAILED = "Failed to connect to {provider}"
ERROR_UPLOAD_FAILED = "Failed to upload chunks to {provider}: {error}"
ERROR_INVALID_PROVIDER = "Unsupported delivery provider: {provider}"