# Supabase Delivery Plugin

Upload RAG document chunks with embeddings to Supabase's pgvector database.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install supabase openai
# or
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# From the project root directory:
cp .env.example .env
# Edit .env with your OpenAI and Supabase credentials
```

**Required Environment Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key for embeddings
- `SUPABASE_URL` - Your Supabase project URL  
- `SUPABASE_KEY` - Your Supabase anon key

### 3. Create Supabase Table

In your Supabase SQL editor:

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    start_position INTEGER,
    end_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector index
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 4. Upload Documents

```bash
rag-processor upload catalog.rag --to supabase --table products
```

## 📋 Features

- ✅ **Automatic Embeddings**: Uses OpenAI to generate embeddings
- ✅ **Batch Processing**: Efficient uploads with configurable batch sizes
- ✅ **Error Handling**: Robust retry logic and detailed error reporting
- ✅ **Vector Search**: Optimized for similarity queries
- ✅ **Metadata Support**: Rich metadata storage with JSONB
- ✅ **Connection Pooling**: Efficient database connections
- ✅ **Schema Validation**: Automatic table schema verification

## ⚙️ Configuration

Environment variables in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon or service key |
| `SUPABASE_BATCH_SIZE` | No | Upload batch size (default: 100) |
| `SUPABASE_UPLOAD_TIMEOUT` | No | Timeout in seconds (default: 300) |
| `SUPABASE_MAX_RETRIES` | No | Max retry attempts (default: 3) |

## 🔍 Vector Search Examples

After uploading, query your data:

```sql
-- Simple similarity search
SELECT content, metadata, 
       1 - (embedding <=> query_embedding) as similarity
FROM products
ORDER BY embedding <=> query_embedding
LIMIT 10;

-- Filter by metadata with similarity
SELECT content, metadata, 
       1 - (embedding <=> query_embedding) as similarity
FROM products
WHERE metadata->>'category' = 'electronics'
ORDER BY embedding <=> query_embedding
LIMIT 5;

-- Hybrid search with text + vector
SELECT content, metadata,
       1 - (embedding <=> query_embedding) as similarity
FROM products
WHERE content ILIKE '%wireless%'
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

## 💰 Cost Estimation

### OpenAI Embeddings
- **text-embedding-ada-002**: $0.0001 per 1K tokens
- Average product: ~50 tokens = $0.000005
- **1000 products ≈ $0.005**

### Supabase Storage
- **Free tier**: 500MB database
- **Pro tier**: $25/month unlimited
- Vector storage: ~6KB per product
- **1000 products ≈ 6MB**

## 🧪 Testing

Test without uploading:

```bash
# Validate environment
python -c "
import os
from plugins.delivery.supabase import SupabaseProvider, OpenAIEmbeddingProvider
embedding_provider = OpenAIEmbeddingProvider()
provider = SupabaseProvider(embedding_provider)
print('✅ Configuration valid')
"

# Test connection
python -c "
from plugins.delivery.supabase import SupabaseProvider, OpenAIEmbeddingProvider
embedding_provider = OpenAIEmbeddingProvider()
provider = SupabaseProvider(embedding_provider)
if provider.connect():
    print('✅ Supabase connection successful')
else:
    print('❌ Supabase connection failed')
"
```

## 🐛 Troubleshooting

### Common Issues

**"Failed to connect to Supabase"**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check Supabase project status
- Ensure anon key has proper permissions

**"Table does not exist"**
- Run table creation SQL
- Check table name in command matches database

**"Vector extension not found"**
- Enable vector extension: `CREATE EXTENSION vector;`
- May require database admin privileges

**"Embedding dimension mismatch"**
- Ensure table VECTOR dimension matches embedding model
- ada-002: 1536, text-embedding-3-large: 3072

### Debug Mode

Enable verbose logging:

```bash
rag-processor upload catalog.rag --to supabase --table products --verbose
```

## 🔧 Advanced Usage

### Custom Table Schema

```sql
-- Custom table with additional fields
CREATE TABLE custom_docs (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    start_position INTEGER,
    end_position INTEGER,
    document_title TEXT,
    document_url TEXT,
    processing_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Bulk Operations

```bash
# Process multiple files
for file in *.rag; do
    rag-processor upload "$file" --to supabase --table products
done

# With additional metadata per file
rag-processor upload catalog.rag --to supabase --table products \
  --metadata '{"batch": "2024-01", "source": "catalog.rag"}'
```

### Performance Optimization

```bash
# Larger batches for faster uploads
export SUPABASE_BATCH_SIZE=200

# Longer timeout for large documents  
export SUPABASE_UPLOAD_TIMEOUT=600

# Upload with high-performance model
rag-processor upload catalog.rag --to supabase --table products \
  --embedding-model text-embedding-3-large
```

## 📚 Plugin Development

This plugin demonstrates the delivery plugin interface. See [Plugin Development Guide](../../PLUGIN_DEVELOPMENT.md) for creating your own plugins.

## 📞 Support

- 🐛 **Plugin Issues**: File issues with `[supabase-plugin]` tag
- 💬 **Questions**: Use GitHub Discussions
- 📖 **Supabase Docs**: https://supabase.com/docs
- 📖 **OpenAI Docs**: https://platform.openai.com/docs