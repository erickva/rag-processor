# RAG Processor Setup Guide

Complete setup instructions to get the RAG Document Processor working end-to-end with real vector databases.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install openai supabase

# Or install from requirements
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required environment variables:
- `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- `SUPABASE_URL` - Get from [Supabase Dashboard](https://app.supabase.com/)
- `SUPABASE_KEY` - Get from Supabase Dashboard (anon/public key)

### 3. Set Up Supabase Table

In your Supabase SQL editor, run:

```sql
-- Enable vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create products table
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    start_position INTEGER,
    end_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector similarity search index
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Optional: Enable Row Level Security
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Optional: Create policies for authenticated access
CREATE POLICY "Enable read access for authenticated users" ON products
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON products  
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

### 4. Test the Complete Workflow

```bash
# 1. Create a .rag file
cat > test-catalog.rag << 'EOF'
#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!source-url: https://example.com/products/catalog.pdf
#!metadata: {"business": "test-store", "type": "product-catalog"}

Name: Premium Coffee Mug
Description: Handcrafted ceramic mug perfect for your morning coffee
Price: $24.99
Category: Kitchen

Name: Wireless Earbuds
Description: High-quality wireless earbuds with noise cancellation
Price: $89.99
Category: Electronics

Name: Yoga Mat
Description: Non-slip yoga mat for comfortable practice
Price: $34.99
Category: Fitness
EOF

# 2. Upload to Supabase (the real value!)
rag-processor upload test-catalog.rag --to supabase --table products --verbose

# Expected output:
# 🚀 Uploading test-catalog.rag to supabase/products
# 🔌 Connecting to vector database...
# ✅ Connected successfully
# 📄 Processing .rag file into chunks...
# 📦 Generated 3 chunks using structured-blocks/empty-line-separated
# ⬆️  Uploading chunks with embeddings...
# ✅ Successfully uploaded 3 chunks to supabase://products
```

### 5. Verify Upload in Supabase

Check your Supabase dashboard:

```sql
-- View uploaded data
SELECT id, content, metadata, created_at FROM products;

-- Test similarity search (requires a query embedding)
SELECT content, metadata, 
       1 - (embedding <=> '[your-query-embedding-vector]') as similarity
FROM products
ORDER BY embedding <=> '[your-query-embedding-vector]'
LIMIT 5;
```

## 🔧 Advanced Configuration

### Custom Embedding Models

```bash
# Use different OpenAI embedding model
rag-processor upload catalog.rag --to supabase --table products --embedding-model text-embedding-3-large
```

### Batch Size and Performance

Set environment variables in `.env`:

```bash
# Larger batches for faster uploads (default: 100)
RAG_UPLOAD_BATCH_SIZE=200

# Longer timeout for large uploads (default: 300 seconds)
RAG_UPLOAD_TIMEOUT=600
```

### Additional Metadata

```bash
# Add extra metadata to all chunks
rag-processor upload catalog.rag --to supabase --table products \
  --metadata '{"version": "2024-01", "source": "import-batch-1"}'
```

## 🧪 Testing Without Real Services

For development/testing without API keys:

```bash
# Just process and validate (no upload)
rag-processor process catalog.rag

# Analyze document type
rag-processor analyze catalog.rag

# Validate .rag file format
rag-processor validate catalog.rag
```

## 💰 Cost Estimation

### OpenAI Embedding Costs
- **text-embedding-ada-002**: ~$0.0001 per 1K tokens
- Average product: ~50 tokens = $0.000005 per product
- **1000 products ≈ $0.005** (half a cent)

### Supabase Costs
- **Free tier**: 500MB database + 2GB bandwidth
- **Pro tier**: $25/month for larger usage
- Vector storage: ~6KB per product (1536 dimensions)
- **1000 products ≈ 6MB storage**

## 🐛 Troubleshooting

### Common Issues

**"OpenAI package required"**
```bash
pip install openai
```

**"Supabase package required"**
```bash
pip install supabase
```

**"API key required"**
- Check your `.env` file has correct API keys
- Verify environment variables are loaded: `echo $OPENAI_API_KEY`

**"Failed to connect to supabase"**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check Supabase project is active
- Ensure anon key has proper permissions

**"Table 'products' doesn't exist"**
- Run the table creation SQL in Supabase dashboard
- Verify vector extension is enabled: `CREATE EXTENSION vector;`

**"Upload requires .rag files"**
- Convert your text file to .rag format with directives
- Use: `rag-processor create-template product-catalog > catalog.rag`

### Debug Mode

Enable verbose logging:

```bash
# Add to .env
RAG_DEBUG=true

# Or use verbose flag
rag-processor upload catalog.rag --to supabase --table products --verbose
```

## 🎯 Next Steps

1. **Scale Up**: Process larger catalogs and documents
2. **Search Integration**: Build search interface using similarity queries
3. **Multiple Tables**: Organize different document types in separate tables
4. **Batch Processing**: Automate uploads with scripts
5. **Plugin Development**: Add support for PDF/DOCX input formats

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/rag-processor/rag-processor/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/rag-processor/rag-processor/discussions)
- 📖 **Documentation**: [Full Documentation](https://docs.rag-processor.org)

---

**Ready to revolutionize your RAG document processing!** 🚀