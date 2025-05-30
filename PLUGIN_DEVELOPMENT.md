# RAG Processor Plugin Development Guide

Complete guide for developing plugins for the RAG Document Processor. Plugins extend functionality for input formats and output destinations.

## 🏗️ Plugin Architecture

The RAG Processor supports two types of plugins:

1. **Input Plugins**: Convert various formats (PDF, DOCX, CSV, etc.) to `.rag` files
2. **Delivery Plugins**: Upload processed chunks to vector databases (Supabase, Pinecone, etc.)

## 📁 Plugin Structure

```
plugins/
├── input/
│   ├── csv/                    # CSV to .rag converter
│   ├── pdf/                    # PDF extraction (future)
│   └── docx/                   # Word document extraction (future)
├── delivery/
│   ├── supabase/               # Supabase vector database
│   ├── pinecone/               # Pinecone vector database (future)
│   └── weaviate/               # Weaviate vector database (future)
└── PLUGIN_DEVELOPMENT.md       # This file
```

Each plugin is **self-contained** with its own:
- Dependencies (`requirements.txt`)
- Documentation (`README.md`)
- Tests (`tests/`)

**Note:** Environment configuration uses the centralized `.env.example` file at the project root to avoid duplication of API keys and settings.

## 🚀 Creating a Delivery Plugin

Delivery plugins upload processed chunks with embeddings to vector databases.

### 1. Plugin Structure

```
plugins/delivery/your-plugin/
├── __init__.py                 # Plugin entry point
├── your_provider.py           # Main provider implementation
├── requirements.txt           # Plugin dependencies  
├── .env.example              # Environment configuration
├── README.md                 # Plugin documentation
└── tests/                    # Plugin tests
    ├── __init__.py
    ├── test_provider.py
    └── test_integration.py
```

### 2. Implement DeliveryProvider Interface

```python
# your_provider.py
from typing import List, Dict, Any, Optional
from rag_processor.delivery.base import DeliveryProvider, DeliveryResult, EmbeddingProvider
from rag_processor.utils.text_utils import ChunkMetadata

class YourDeliveryProvider(DeliveryProvider):
    """Your vector database delivery provider."""
    
    def __init__(self, embedding_provider: EmbeddingProvider, **kwargs):
        """Initialize with embedding provider and custom config."""
        super().__init__(embedding_provider)
        # Initialize your database client
        self.client = None
    
    @property
    def name(self) -> str:
        """Provider name (e.g., 'pinecone', 'weaviate')."""
        return "your-provider"
    
    def connect(self, **kwargs) -> bool:
        """Establish connection to your vector database."""
        try:
            # Initialize your database client
            # self.client = YourDatabaseClient(...)
            return self.test_connection()
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test if connection is working."""
        try:
            # Test your database connection
            # self.client.ping() or similar
            return True
        except Exception:
            return False
    
    def upload_chunks(
        self, 
        chunks: List[ChunkMetadata], 
        table_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """Upload chunks with embeddings to your database."""
        try:
            # Prepare chunks with embeddings
            prepared_chunks = self.prepare_chunk_data(chunks, metadata)
            
            # Upload to your database
            uploaded_count = 0
            errors = []
            
            for chunk_data in prepared_chunks:
                try:
                    # Upload single chunk to your database
                    # self.client.insert(table_name, chunk_data)
                    uploaded_count += 1
                except Exception as e:
                    errors.append(f"Chunk upload failed: {e}")
            
            return DeliveryResult(
                success=uploaded_count > 0,
                chunks_uploaded=uploaded_count,
                errors=errors,
                provider=self.name,
                destination=f"{self.name}://{table_name}",
                metadata={
                    "embedding_model": self.embedding_provider.model,
                    "embedding_dimension": self.embedding_provider.dimension,
                    "total_chunks": len(chunks),
                }
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                chunks_uploaded=0,
                errors=[f"Upload failed: {e}"],
                provider=self.name,
                destination=f"{self.name}://{table_name}",
                metadata={}
            )
```

### 3. Plugin Entry Point

```python
# __init__.py
"""
Your Delivery Plugin for RAG Document Processor.

Description of what your plugin does and key features.

Requirements:
- List your requirements here
- API keys or credentials needed

Usage:
    rag-processor upload document.rag --to your-provider --table products
"""

from .your_provider import YourDeliveryProvider

__all__ = ["YourDeliveryProvider"]
__version__ = "0.1.0"
__plugin_type__ = "delivery"
__plugin_name__ = "your-provider"
```

### 4. Configuration Template

```bash
# .env.example
# Your Plugin Configuration
# Copy this file to .env and fill in your credentials

# Your API credentials
YOUR_API_KEY=your-api-key-here
YOUR_API_URL=https://api.yourservice.com

# OpenAI for embeddings
OPENAI_API_KEY=sk-your-openai-api-key-here

# Performance tuning
YOUR_BATCH_SIZE=100
YOUR_TIMEOUT=300

# Usage examples and setup instructions...
```

### 5. Register Plugin

Update the main CLI to recognize your plugin:

```python
# In rag_processor/__main__.py, update handle_upload()
if args.to == "your-provider":
    from plugins.delivery.your_provider import YourDeliveryProvider
    delivery_provider = YourDeliveryProvider(embedding_provider)
```

## 📥 Creating an Input Plugin

Input plugins convert various file formats into `.rag` files.

### 1. Plugin Structure

```
plugins/input/your-format/
├── __init__.py                 # Plugin entry point
├── converter.py               # Main conversion logic
├── requirements.txt           # Plugin dependencies
├── .env.example              # Configuration (if needed)
├── README.md                 # Plugin documentation
└── tests/                    # Plugin tests
```

### 2. Implement Converter Interface

```python
# converter.py
from typing import Optional, Dict, Any
from pathlib import Path

class YourFormatConverter:
    """Convert your format to .rag files."""
    
    def __init__(self, **config):
        """Initialize converter with configuration."""
        self.config = config
    
    def convert(
        self, 
        input_file: str, 
        output_file: Optional[str] = None,
        strategy: str = "structured-blocks/empty-line-separated",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert input file to .rag format.
        
        Args:
            input_file: Path to input file
            output_file: Path to output .rag file (optional)
            strategy: Processing strategy to embed in .rag file
            metadata: Additional metadata for .rag file
            
        Returns:
            str: Path to created .rag file
        """
        # Read and process your input format
        content = self._extract_content(input_file)
        
        # Generate .rag file content
        rag_content = self._create_rag_content(
            content, strategy, metadata, input_file
        )
        
        # Write .rag file
        if not output_file:
            output_file = Path(input_file).with_suffix('.rag')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rag_content)
        
        return str(output_file)
    
    def _extract_content(self, input_file: str) -> str:
        """Extract text content from your input format."""
        # Implement format-specific extraction
        # For CSV: read and format as structured blocks
        # For PDF: extract text and preserve structure  
        # For DOCX: extract text and headings
        pass
    
    def _create_rag_content(
        self, 
        content: str, 
        strategy: str, 
        metadata: Dict[str, Any], 
        source_file: str
    ) -> str:
        """Create complete .rag file content with directives."""
        header_lines = [
            "#!/usr/bin/env rag-processor",
            f"#!strategy: {strategy}",
        ]
        
        # Add source URL if available
        if 'source_url' in metadata:
            header_lines.append(f"#!source-url: {metadata['source_url']}")
        
        # Add metadata
        import json
        file_metadata = {
            "source_file": source_file,
            "converted_by": f"{self.__class__.__name__}",
            "format": self.format_name,
        }
        if metadata:
            file_metadata.update(metadata)
        
        header_lines.append(f"#!metadata: {json.dumps(file_metadata)}")
        
        # Combine header and content
        return '\n'.join(header_lines) + '\n\n' + content
    
    @property
    def format_name(self) -> str:
        """Name of the input format this converter handles."""
        return "your-format"
    
    @property
    def supported_extensions(self) -> List[str]:
        """List of file extensions this converter supports."""
        return [".your-ext"]
```

### 3. CLI Integration

```python
# Add CLI command for your converter
# In rag_processor/__main__.py

# Add convert command
convert_parser = subparsers.add_parser(
    "convert",
    help="Convert input files to .rag format"
)
convert_parser.add_argument("input_file", help="Input file to convert")
convert_parser.add_argument("--output", help="Output .rag file path")
convert_parser.add_argument("--format", required=True, 
                          choices=["csv", "pdf", "docx"], 
                          help="Input format")
convert_parser.add_argument("--strategy", 
                          default="structured-blocks/empty-line-separated",
                          help="Processing strategy for .rag file")

def handle_convert(args):
    """Handle convert command."""
    if args.format == "your-format":
        from plugins.input.your_format import YourFormatConverter
        converter = YourFormatConverter()
        output_file = converter.convert(
            args.input_file, 
            args.output,
            args.strategy
        )
        print(f"✅ Converted to: {output_file}")
```

## 🧪 Testing Plugins

### Unit Tests

```python
# tests/test_provider.py
import pytest
from unittest.mock import Mock
from plugins.delivery.your_provider import YourDeliveryProvider

def test_provider_initialization():
    """Test provider can be initialized."""
    embedding_provider = Mock()
    provider = YourDeliveryProvider(embedding_provider)
    assert provider.name == "your-provider"

def test_connection():
    """Test database connection."""
    embedding_provider = Mock()
    provider = YourDeliveryProvider(embedding_provider)
    # Mock your database client
    # Test connection logic
    pass

def test_upload_chunks():
    """Test chunk upload functionality."""
    # Test your upload logic
    pass
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
import os
from plugins.delivery.your_provider import YourDeliveryProvider

@pytest.mark.skipif(
    not os.getenv("YOUR_API_KEY"), 
    reason="API key required for integration tests"
)
def test_end_to_end_upload():
    """Test complete upload workflow with real API."""
    # Test with real credentials (if available)
    pass
```

## 📦 Plugin Distribution

### 1. Package Structure

```
your-rag-plugin/
├── setup.py                   # Package setup
├── README.md                  # Plugin documentation
├── requirements.txt           # Dependencies
├── your_plugin/              # Plugin code
│   ├── __init__.py
│   └── provider.py
└── tests/                     # Tests
```

### 2. Setup Configuration

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="rag-processor-your-plugin",
    version="0.1.0",
    description="Your Plugin for RAG Document Processor",
    packages=find_packages(),
    install_requires=[
        "rag-processor>=0.1.0",
        "your-dependencies>=1.0.0",
    ],
    entry_points={
        "rag_processor.plugins": [
            "your-plugin = your_plugin:YourProvider"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.8",
    ],
)
```

### 3. Distribution

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*

# Install plugin
pip install rag-processor-your-plugin
```

## 🎯 Plugin Examples

### CSV Input Plugin (Simple)

```python
# plugins/input/csv/converter.py
import csv
from pathlib import Path

class CSVConverter:
    """Convert CSV files to structured .rag format."""
    
    def convert(self, csv_file: str, output_file: str = None) -> str:
        """Convert CSV to .rag with empty-line separated blocks."""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            blocks = []
            for row in reader:
                # Convert each row to field: value format
                block_lines = []
                for key, value in row.items():
                    if value:  # Skip empty values
                        block_lines.append(f"{key}: {value}")
                
                if block_lines:
                    blocks.append('\n'.join(block_lines))
            
            content = '\n\n'.join(blocks)
        
        # Create .rag file
        rag_content = f"""#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!source-url: file://{Path(csv_file).absolute()}
#!metadata: {{"source_format": "csv", "rows": {len(blocks)}}}

{content}"""
        
        if not output_file:
            output_file = Path(csv_file).with_suffix('.rag')
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rag_content)
            
        return str(output_file)
```

### Pinecone Delivery Plugin (Advanced)

```python
# plugins/delivery/pinecone/provider.py
import pinecone
from typing import List, Dict, Any, Optional
from rag_processor.delivery.base import DeliveryProvider, DeliveryResult

class PineconeProvider(DeliveryProvider):
    """Pinecone vector database delivery provider."""
    
    def __init__(self, embedding_provider, api_key: str = None, environment: str = None):
        super().__init__(embedding_provider)
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        self.index = None
    
    @property
    def name(self) -> str:
        return "pinecone"
    
    def connect(self, index_name: str) -> bool:
        """Connect to Pinecone index."""
        try:
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.index = pinecone.Index(index_name)
            return True
        except Exception as e:
            print(f"Pinecone connection failed: {e}")
            return False
    
    def upload_chunks(self, chunks: List[ChunkMetadata], index_name: str, **kwargs) -> DeliveryResult:
        """Upload chunks to Pinecone index."""
        if not self.connect(index_name):
            return DeliveryResult(False, 0, ["Connection failed"], self.name, index_name, {})
        
        prepared_chunks = self.prepare_chunk_data(chunks)
        
        # Convert to Pinecone format
        vectors = []
        for i, chunk_data in enumerate(prepared_chunks):
            vectors.append({
                "id": f"chunk_{i}",
                "values": chunk_data["embedding"],
                "metadata": {
                    "content": chunk_data["text"],
                    **chunk_data["metadata"]
                }
            })
        
        # Batch upload to Pinecone
        try:
            self.index.upsert(vectors)
            return DeliveryResult(True, len(vectors), [], self.name, index_name, {})
        except Exception as e:
            return DeliveryResult(False, 0, [str(e)], self.name, index_name, {})
```

## 📋 Plugin Checklist

Before submitting a plugin:

### Code Quality
- [ ] Follows Python PEP 8 style guide
- [ ] Comprehensive error handling
- [ ] Type hints for all public methods
- [ ] Docstrings for all classes and methods

### Testing  
- [ ] Unit tests for core functionality
- [ ] Integration tests (with mocked external services)
- [ ] Test coverage > 80%
- [ ] Tests pass in CI environment

### Documentation
- [ ] Complete README.md with examples
- [ ] .env.example with all configuration options
- [ ] Setup/installation instructions
- [ ] Troubleshooting section
- [ ] Cost estimation (if applicable)

### Structure
- [ ] Self-contained plugin folder
- [ ] requirements.txt with pinned versions
- [ ] Proper __init__.py with plugin metadata
- [ ] Follows naming conventions

### Integration
- [ ] Implements required interface correctly
- [ ] Registers with main CLI properly
- [ ] Handles missing dependencies gracefully
- [ ] Provides helpful error messages

## 🤝 Contributing Plugins

1. **Fork** the repository
2. **Create** your plugin in appropriate folder
3. **Test** thoroughly with unit and integration tests
4. **Document** with README and examples
5. **Submit** pull request with plugin description

### Plugin Naming Convention

- **Delivery plugins**: `plugins/delivery/{service-name}/`
- **Input plugins**: `plugins/input/{format-name}/`
- **Package names**: `rag-processor-{service-name}`

### Review Process

All plugins go through review for:
- Code quality and security
- Documentation completeness  
- Test coverage
- Performance impact
- User experience

## 📞 Support

- 🐛 **Plugin Issues**: Use `[plugin]` tag in GitHub issues
- 💬 **Development Questions**: GitHub Discussions
- 📖 **API Reference**: See core documentation
- 🎯 **Examples**: Check existing plugins in repository

---

**Ready to extend RAG Processor with your plugin?** 🚀