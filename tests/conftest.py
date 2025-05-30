"""
Pytest configuration and shared fixtures for RAG Processor tests.

Provides common test fixtures and utilities used across the test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

from rag_processor.core.processor import RAGDocumentProcessor
from rag_processor.core.analyzer import DocumentAnalyzer, DocumentType
from rag_processor.core.validator import ValidationEngine
from rag_processor.utils.directive_parser import DirectiveParser, ProcessingDirective
from rag_processor.clients.default import DefaultConfig


@pytest.fixture
def processor():
    """Create a RAGDocumentProcessor instance for testing."""
    return RAGDocumentProcessor()


@pytest.fixture
def analyzer():
    """Create a DocumentAnalyzer instance for testing."""
    return DocumentAnalyzer()


@pytest.fixture
def validator():
    """Create a ValidationEngine instance for testing."""
    return ValidationEngine()


@pytest.fixture
def directive_parser():
    """Create a DirectiveParser instance for testing."""
    return DirectiveParser()


@pytest.fixture
def default_config():
    """Create a DefaultConfig instance for testing."""
    return DefaultConfig()


@pytest.fixture
def default_config():
    """Create a DefaultConfig instance for testing."""
    return DefaultConfig()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_product_catalog():
    """Sample product catalog content for testing."""
    return """Nome: Leque Personalizado Rosa
Categoria: Leques
Descrição: Leque artesanal personalizado na cor rosa com detalhes em dourado.
Preço: R$ 45,90

Nome: Menu de Casamento Elegante
Categoria: Menus
Descrição: Menu sofisticado para casamentos com design clássico e elegante.
Preço: R$ 12,50

Nome: Convite Floral Vintage
Categoria: Convites
Descrição: Convite com estampa floral vintage, ideal para eventos especiais.
Preço: R$ 8,75"""


@pytest.fixture
def sample_user_manual():
    """Sample user manual content for testing."""
    return """# User Manual

## 1. Introduction

Welcome to the user manual for our application. This guide will help you get started.

### 1.1 Getting Started

Follow these steps to begin:

1. Install the application
2. Create an account
3. Configure your settings

### 1.2 System Requirements

The application requires:
- Python 3.8 or higher
- 2GB of RAM
- 500MB of disk space

## 2. Basic Operations

This section covers fundamental operations.

### 2.1 Creating Documents

To create a new document, click the "New" button in the toolbar."""


@pytest.fixture
def sample_faq():
    """Sample FAQ content for testing."""
    return """# Frequently Asked Questions

Q: What is this product?
A: This is a comprehensive document processing system designed to optimize RAG performance through intelligent chunking.

Q: How do I get started?
A: Simply install the package using pip and follow the quick start guide in the documentation.

Q: What file formats are supported?
A: We support .rag files with embedded processing directives, as well as plain text files for analysis.

Q: Is there a free trial available?
A: Yes, the basic version is open source and available for free. Enterprise features require a license."""


@pytest.fixture
def sample_rag_file():
    """Sample .rag file content for testing."""
    return """#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary
#!validation: studio-camila-golin/product-catalog
#!chunk-pattern: Nome:\\s*([^\\n]+)
#!metadata: {"business": "studio-camila-golin", "type": "product-catalog", "version": "1.0"}

Nome: Produto Teste
Categoria: Categoria Teste
Descrição: Descrição do produto de teste para validação.
Preço: R$ 99,99

Nome: Segundo Produto
Categoria: Categoria Teste
Descrição: Segundo produto para testar múltiplos produtos.
Preço: R$ 149,90"""


@pytest.fixture
def sample_directive():
    """Sample ProcessingDirective for testing."""
    return ProcessingDirective(
        strategy="structured-blocks/empty-line-separated",
        source_url="https://example.com/test-catalog.pdf",
        metadata={"business": "studio-camila-golin", "type": "product-catalog"}
    )


@pytest.fixture  
def sample_rag_content():
    """Sample .rag file content with simplified directives."""
    return '''#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!source-url: https://example.com/test-catalog.pdf
#!metadata: {"business": "test-store", "type": "product-catalog"}

Name: Test Product 1
Description: First test product for validation
Price: $19.99
Category: Electronics

Name: Test Product 2  
Description: Second test product for validation
Price: $29.99
Category: Books'''


@pytest.fixture
def create_temp_file():
    """Factory function to create temporary files with content."""
    def _create_file(content: str, suffix: str = ".txt") -> Path:
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            return Path(path)
        except:
            os.close(fd)
            raise
    return _create_file


@pytest.fixture
def mock_analysis_result():
    """Mock DocumentAnalysis result for testing."""
    from rag_processor.core.analyzer import DocumentAnalysis
    
    return DocumentAnalysis(
        document_type=DocumentType.PRODUCT_CATALOG,
        confidence=0.85,
        detected_patterns={"Nome:": 2, "Categoria:": 2, "Preço:": 2},
        recommended_strategy="products/semantic-boundary",
        analysis_details={
            "content_length": 500,
            "type_scores": {"product_catalog": 8.5, "user_manual": 1.2},
            "pattern_analysis": {"total_lines": 12, "has_structured_fields": True}
        }
    )


@pytest.fixture
def mock_validation_result():
    """Mock ValidationResult for testing."""
    from rag_processor.core.validator import ValidationResult, ValidationIssue, ValidationLevel
    
    return ValidationResult(
        is_valid=True,
        issues=[
            ValidationIssue(
                level=ValidationLevel.INFO,
                message="High quality content detected",
                suggestion="Content is well-structured for RAG processing"
            )
        ],
        score=0.9,
        metadata={"content_length": 500, "strategy_name": "products/semantic-boundary"}
    )


# Test utility functions
def assert_chunk_quality(chunks, min_chunks=1, min_size=50, max_size=2000):
    """Assert chunk quality meets basic requirements."""
    assert len(chunks) >= min_chunks, f"Expected at least {min_chunks} chunks, got {len(chunks)}"
    
    for i, chunk in enumerate(chunks):
        assert hasattr(chunk, 'text'), f"Chunk {i} missing text attribute"
        assert hasattr(chunk, 'metadata'), f"Chunk {i} missing metadata attribute"
        assert min_size <= len(chunk.text) <= max_size, \
            f"Chunk {i} size {len(chunk.text)} outside range {min_size}-{max_size}"
        assert chunk.text.strip(), f"Chunk {i} is empty or whitespace only"


def assert_metadata_complete(metadata, required_fields=None):
    """Assert that chunk metadata contains required fields."""
    if required_fields is None:
        required_fields = ["strategy", "chunk_index", "chunking_method"]
    
    for field in required_fields:
        assert field in metadata, f"Required metadata field missing: {field}"