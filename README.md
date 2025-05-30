# RAG Document Processor (in development)

**Intelligent document chunking for optimal RAG performance**

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

## 🚀 Overview

The RAG Document Processor is a revolutionary approach to RAG document processing focused on **mechanical separation over semantic understanding**. It solves fundamental chunking problems through simple, reliable block-separation techniques.

**Core Philosophy:**
- 🔧 **Mechanical Separation**: Reliable empty-line block separation instead of complex semantic analysis
- 📝 **Text-First Focus**: Excellent text chunking with plugin extensibility for other formats
- 🎯 **Declarative Processing**: Documents embed their own processing instructions
- ✅ **Quality Assurance**: Built-in validation prevents poor RAG performance
- 🔌 **Plugin Ecosystem**: Community-extensible for specialized input formats

## 🔧 Installation

```bash
pip install rag-processor
```

For development installation:
```bash
pip install rag-processor[dev]
```

For CLI features:
```bash
pip install rag-processor[cli]
```

## 🎯 Quick Start

### 1. Create a .rag Document

```bash
#!/usr/bin/env rag-processor
@strategy: structured-blocks/empty-line-separated
@max-lines-per-block: 10
@metadata: {"type": "product-catalog", "business": "my-store"}

Name: Premium Fan
Description: Handcrafted premium fan with golden details
Price: $45.90
Category: Home Decor

Name: Wedding Menu
Description: Elegant wedding menu with classic design
Price: $12.50
Category: Stationery

Name: Vintage Invitation
Description: Vintage floral invitation for special events
Price: $8.75
Category: Invitations
```

### 2. Process the Document

```bash
# Analyze document type and get recommendations
rag-processor analyze document.rag

# Validate document against strategy
rag-processor validate document.rag

# Process into optimized chunks
rag-processor process document.rag --output chunks.json
```

### 3. Use Programmatically

```python
from rag_processor import RAGDocumentProcessor

processor = RAGDocumentProcessor()

# Process a .rag file
result = processor.process_file("document.rag")

print(f"Generated {len(result.chunks)} chunks")
print(f"Strategy used: {result.strategy_used}")
print(f"Quality score: {result.validation.score:.2f}")

# Access individual chunks
for chunk in result.chunks:
    print(f"Chunk: {chunk.text[:100]}...")
    print(f"Metadata: {chunk.metadata}")
```

## 📋 Supported Processing Strategies

| Strategy | Best For | Description |
|----------|----------|-------------|
| **`structured-blocks/empty-line-separated`** | Products, Contacts, Records | Blocks separated by empty lines |
| **`structured-blocks/heading-separated`** | Documents, Manuals | Blocks separated by headings |
| **`manual/section-based`** | Documentation | Hierarchical section processing |
| **`faq/qa-pairs`** | Support, Q&A | Question-answer pair processing |
| **`article/sentence-based`** | Articles, Blogs | Sentence boundary processing |
| **`legal/paragraph-based`** | Contracts, Legal | Legal paragraph processing |

## 🔌 Bidirectional Plugin Ecosystem (Future)**

The core system focuses on excellent text processing, with community plugins for both source formats AND delivery destinations:

```bash
# SOURCE PLUGINS: Various formats → .rag files
rag-processor-pdf extract document.pdf --output document.rag
rag-processor-docx extract document.docx --output document.rag
rag-processor-web scrape https://example.com --output document.rag

# CORE PROCESSING: .rag files → optimized chunks  
rag-processor process document.rag --output chunks.json

# DELIVERY PLUGINS: chunks → vector databases
rag-processor-supabase upload chunks.json --table embeddings
rag-processor-pinecone upload chunks.json --index products
rag-processor-firestore upload chunks.json --collection docs
```

**Complete Plugin Ecosystem:**
```bash
# Core system
pip install rag-processor              # Core text processing

# Source plugins (format extraction)
pip install rag-processor-pdf          # PDF extraction
pip install rag-processor-docx         # Word documents
pip install rag-processor-ocr          # OCR for images
pip install rag-processor-web          # Web scraping
pip install rag-processor-confluence   # Confluence integration
pip install rag-processor-notion       # Notion export

# Output plugins (vector database delivery)
pip install rag-processor-supabase     # Supabase vector store
pip install rag-processor-pinecone     # Pinecone delivery
pip install rag-processor-firestore    # Firestore upload
pip install rag-processor-weaviate     # Weaviate integration
pip install rag-processor-chroma       # ChromaDB support
pip install rag-processor-qdrant       # Qdrant upload
```

**Plugin Architecture Benefits:**
- ✅ Lightweight core system
- ✅ Optional complexity
- ✅ Community-driven innovation
- ✅ End-to-end workflow support
- ✅ Specialized format & destination support

## 🎨 Core Processing Strategies

### Structured Blocks (Primary Strategy)
Perfect for any structured data separated by empty lines:
```bash
#!strategy: structured-blocks/empty-line-separated
#!max-lines-per-block: 10
```

**Works with any content:**
- Product catalogs
- Contact lists  
- Record databases
- Inventory systems
- Configuration files

### Manual Strategy  
Ideal for hierarchical documentation:
```bash
#!strategy: manual/section-based
#!chunk-pattern: ^#{1,6}\s+(.+)$
```

### FAQ Strategy
Optimized for question-answer pairs:
```bash
#!strategy: faq/qa-pairs
#!chunk-pattern: (Q:|Question:)
```

## 🎯 Universal Processing

### Simple Configuration
The system now uses universal structured-blocks processing:
- **Language agnostic**: Works with any language (English, Portuguese, Spanish, etc.)
- **Business flexible**: Store business context in .rag file metadata  
- **Format flexible**: Input plugins handle different source formats
- **No hardcoded rules**: Mechanical separation over semantic requirements

## 🛠️ CLI Commands

### For Installed Package
```bash
# Get help
rag-processor --help

# Analyze document
rag-processor analyze document.txt
rag-processor analyze document.rag --format json

# Validate .rag file
rag-processor validate document.rag
rag-processor validate document.rag --report validation.txt

# Process document
rag-processor process document.rag
rag-processor process document.rag --output chunks.json --include-metadata

# Create templates
rag-processor create-template product-catalog --output catalog.rag
rag-processor create-template user-manual --output manual.rag

# List available options
rag-processor list strategies
rag-processor list document-types
```

### For Local Development (No Installation Required)
```bash
# Navigate to project directory
cd /path/to/rag-processor

# Get help
python -m rag_processor --help

# Analyze document (what we just tested!)
python -m rag_processor analyze document.txt
python -m rag_processor analyze document.txt --format json
python -m rag_processor analyze document.txt --format yaml

# Validate .rag file
python -m rag_processor validate document.rag

# Process document
python -m rag_processor process document.rag

# Create templates
python -m rag_processor create-template product-catalog --output catalog.rag

# List available options
python -m rag_processor list strategies
python -m rag_processor list document-types
```

### Example Output
```json
{
  "document_type": "product_catalog",
  "confidence": 0.909,
  "recommended_strategy": "products/semantic-boundary",
  "detected_patterns": {
    "product_catalog:Nome:\\s*[^\\n]+...": 3,
    "product_catalog:Preço:\\s*R?\\$?\\s*[\\d,]+...": 3
  }
}
```

## 📊 Proven Results

Based on real-world success with product catalog implementations:

**Before (Broken System):**
- Query: "wireless headphones" → Wrong results at position #10
- Problem: 400-character chunking fragmented products
- Similarity: Negative scores (-0.0382)

**After (Our Solution):**
- Query: "wireless headphones" → Correct results at positions #1 & #2  
- Solution: Block-based chunking preserves product integrity
- Similarity: High scores (0.8228, 0.8217)

## 🧪 Development

### Setup Development Environment

```bash
git clone https://github.com/rag-processor/rag-processor.git
cd rag-processor
pip install -e .[dev]
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rag_processor --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black rag_processor tests
isort rag_processor tests

# Lint code
flake8 rag_processor tests
mypy rag_processor

# Run pre-commit hooks
pre-commit run --all-files
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding New Strategies

1. Create strategy class inheriting from `ProcessingStrategy`
2. Implement required methods: `process()`, `validate_content()`, `create_template()`
3. Register in `RAGDocumentProcessor`
4. Add comprehensive tests
5. Update documentation

### Adding Input Plugins

1. Create plugin in `plugins/input/{format}/`
2. Implement format-specific conversion to .rag
3. Add plugin documentation and tests
4. See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)

## 📖 Documentation

- [Plugin Development Guide](PLUGIN_DEVELOPMENT.md) - Complete guide for creating source and delivery plugins
- [Project Setup Instructions](SETUP.md) - Installation and configuration guide

## 🐛 Issue Reporting

Found a bug? Have a feature request? Please check our [Issue Tracker](https://github.com/rag-processor/rag-processor/issues).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on real-world experience fixing semantic search issues
- Inspired by the need for standardized RAG processing
- Built for the open source community

## 🔗 Links

- **Homepage**: https://rag-processor.org
- **Documentation**: https://docs.rag-processor.org  
- **Repository**: https://github.com/rag-processor/rag-processor
- **Issues**: https://github.com/rag-processor/rag-processor/issues
- **Discussions**: https://github.com/rag-processor/rag-processor/discussions

---

**Ready to revolutionize your RAG document processing!** 🚀
