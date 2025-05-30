"""
Test suite for the current simplified RAG Processor system.

Covers the core functionality with the new simplified directive format
and structured-blocks strategies.
"""

import pytest
import tempfile
import os
from pathlib import Path

from rag_processor.core.processor import RAGDocumentProcessor
from rag_processor.core.analyzer import DocumentAnalyzer, DocumentType
from rag_processor.utils.directive_parser import DirectiveParser, ProcessingDirective
from rag_processor.strategies.structured_blocks import (
    EmptyLineSeparatedStrategy, HeadingSeparatedStrategy, NumberedSeparatedStrategy
)


class TestSimplifiedDirectiveParser:
    """Test the simplified directive parser."""
    
    def test_parse_simplified_directives(self):
        """Test parsing simplified .rag file directives."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!source-url: https://example.com/catalog.pdf
#!metadata: {"business": "test", "type": "catalog"}

Name: Test Product
Price: $19.99'''
        
        parser = DirectiveParser()
        directive = parser.parse(content)
        
        assert directive.strategy == "structured-blocks/empty-line-separated"
        assert directive.source_url == "https://example.com/catalog.pdf"
        assert directive.metadata["business"] == "test"
        assert directive.metadata["type"] == "catalog"
    
    def test_extract_content(self):
        """Test extracting content without directives."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!metadata: {"test": true}

Name: Product 1
Description: Test product'''
        
        parser = DirectiveParser()
        extracted = parser.extract_content(content)
        
        assert "Name: Product 1" in extracted
        assert "Description: Test product" in extracted
        assert "#!strategy" not in extracted
        assert "#!/usr/bin/env" not in extracted
    
    def test_create_directive_header(self):
        """Test creating directive headers."""
        directive = ProcessingDirective(
            strategy="structured-blocks/empty-line-separated",
            source_url="https://example.com/doc.pdf",
            metadata={"test": "value"}
        )
        
        parser = DirectiveParser()
        header = parser.create_directive_header(directive)
        
        assert "#!/usr/bin/env rag-processor" in header
        assert "#!strategy: structured-blocks/empty-line-separated" in header
        assert "#!source-url: https://example.com/doc.pdf" in header
        assert '"test":"value"' in header


class TestStructuredBlocksStrategies:
    """Test structured blocks processing strategies."""
    
    def test_empty_line_separated_strategy(self):
        """Test empty line separated processing."""
        content = '''Name: Product 1
Description: First product
Price: $10.00

Name: Product 2
Description: Second product  
Price: $20.00'''
        
        strategy = EmptyLineSeparatedStrategy()
        directive = ProcessingDirective(strategy="structured-blocks/empty-line-separated")
        
        from rag_processor.clients.default import DefaultConfig
        chunks = strategy.process(content, directive, DefaultConfig())
        
        assert len(chunks) == 2
        assert "Product 1" in chunks[0].text
        assert "Product 2" in chunks[1].text
        assert chunks[0].metadata["strategy"] == "structured-blocks/empty-line-separated"
    
    def test_heading_separated_strategy(self):
        """Test heading separated processing."""
        content = '''# Introduction
This is an introduction section.

## Overview  
This is an overview subsection.

# Main Content
This is the main content section.'''
        
        strategy = HeadingSeparatedStrategy()
        directive = ProcessingDirective(strategy="structured-blocks/heading-separated")
        
        from rag_processor.clients.default import DefaultConfig
        chunks = strategy.process(content, directive, DefaultConfig())
        
        assert len(chunks) >= 2  # Should find heading-separated chunks
        # Check that headings are preserved in chunks
        chunk_texts = [chunk.text for chunk in chunks]
        assert any("# Introduction" in text for text in chunk_texts)
        assert any("# Main Content" in text for text in chunk_texts)
    
    def test_numbered_separated_strategy(self):
        """Test numbered list separated processing."""
        content = '''1. First step in the process
   This explains the first step in detail.

2. Second step follows
   This explains the second step.

3. Third and final step
   This completes the process.'''
        
        strategy = NumberedSeparatedStrategy()
        directive = ProcessingDirective(strategy="structured-blocks/numbered-separated")
        
        from rag_processor.clients.default import DefaultConfig
        chunks = strategy.process(content, directive, DefaultConfig())
        
        assert len(chunks) >= 2  # Should find numbered chunks
        # Check that numbers are preserved
        chunk_texts = [chunk.text for chunk in chunks]
        assert any("1. First step" in text for text in chunk_texts)
        assert any("2. Second step" in text for text in chunk_texts)


class TestDocumentAnalyzer:
    """Test document analysis with new strategy recommendations."""
    
    def test_analyze_structured_blocks(self):
        """Test analysis recommends structured-blocks strategies."""
        content = '''Name: Product 1
Description: Test product 1
Price: $19.99

Name: Product 2
Description: Test product 2
Price: $29.99'''
        
        analyzer = DocumentAnalyzer()
        analysis = analyzer.analyze(content)
        
        # Should detect structured blocks with high confidence
        assert analysis.document_type == DocumentType.STRUCTURED_BLOCKS
        assert analysis.confidence > 0.8
        assert "structured-blocks" in analysis.recommended_strategy
    
    def test_analyze_empty_content(self):
        """Test analysis of empty content."""
        analyzer = DocumentAnalyzer()
        analysis = analyzer.analyze("")
        
        assert analysis.confidence == 0.0
        # Empty content may still get assigned a type (just with 0 confidence)


class TestRAGDocumentProcessor:
    """Test the main processor with simplified system."""
    
    def test_process_rag_file(self):
        """Test processing a complete .rag file."""
        rag_content = '''#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!source-url: https://example.com/test.pdf
#!metadata: {"business": "test", "type": "catalog"}

Name: Product A
Description: First test product
Price: $15.00
Category: Electronics

Name: Product B
Description: Second test product
Price: $25.00
Category: Books'''
        
        # Create temporary .rag file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rag', delete=False) as f:
            f.write(rag_content)
            temp_path = f.name
        
        try:
            processor = RAGDocumentProcessor()
            result = processor.process_file(temp_path)
            
            # Verify processing results
            assert len(result.chunks) == 2
            assert result.strategy_used == "structured-blocks/empty-line-separated"
            assert result.analysis.document_type == DocumentType.STRUCTURED_BLOCKS
            assert result.validation.is_valid
            
            # Verify chunk content
            assert "Product A" in result.chunks[0].text
            assert "Product B" in result.chunks[1].text
            
        finally:
            os.unlink(temp_path)
    
    def test_analyze_document(self):
        """Test document analysis functionality."""
        # Create temporary text file
        content = '''Name: Test Item
Description: Sample description
Price: $10.00

Name: Another Item
Description: Another description
Price: $20.00'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            processor = RAGDocumentProcessor()
            analysis = processor.analyze_document(temp_path)
            
            assert analysis.document_type == DocumentType.STRUCTURED_BLOCKS
            assert analysis.confidence > 0.7
            assert "structured-blocks" in analysis.recommended_strategy
            
        finally:
            os.unlink(temp_path)


class TestCSVPlugin:
    """Test CSV input plugin functionality."""
    
    def test_csv_conversion(self):
        """Test CSV to .rag conversion."""
        from plugins.input.csv import CSVConverter
        
        # Create test CSV
        csv_content = '''Name,Description,Price,Category
Product 1,Test product 1,19.99,Electronics
Product 2,Test product 2,29.99,Books'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            converter = CSVConverter()
            rag_path = converter.convert(csv_path)
            
            # Verify .rag file was created
            assert os.path.exists(rag_path)
            
            # Verify .rag content
            with open(rag_path, 'r') as f:
                rag_content = f.read()
            
            assert "#!/usr/bin/env rag-processor" in rag_content
            assert "#!strategy: structured-blocks/empty-line-separated" in rag_content
            assert "Name: Product 1" in rag_content
            assert "Description: Test product 1" in rag_content
            
            # Clean up
            os.unlink(rag_path)
            
        finally:
            os.unlink(csv_path)
    
    def test_csv_validation(self):
        """Test CSV validation functionality."""
        from plugins.input.csv import CSVConverter
        
        # Create valid CSV
        csv_content = '''Name,Price
Product 1,19.99
Product 2,29.99'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            converter = CSVConverter()
            issues = converter.validate_csv(csv_path)
            
            # Should have no validation issues
            assert len(issues) == 0
            
        finally:
            os.unlink(csv_path)


class TestDeliverySystem:
    """Test delivery system interfaces."""
    
    def test_delivery_provider_interface(self):
        """Test delivery provider base interface."""
        from rag_processor.delivery.base import EmbeddingProvider, DeliveryProvider
        from unittest.mock import Mock
        
        # Create mock embedding provider
        embedding_provider = Mock(spec=EmbeddingProvider)
        embedding_provider.dimension = 1536
        
        # Test that we can't instantiate abstract base class
        with pytest.raises(TypeError):
            DeliveryProvider(embedding_provider)
    
    def test_openai_embedding_provider_interface(self):
        """Test OpenAI embedding provider interface (without API key)."""
        from rag_processor.delivery.openai_embeddings import OpenAIEmbeddingProvider
        
        # Should fail without API key (or with ImportError if openai not available)
        with pytest.raises((ValueError, ImportError, AttributeError)):
            OpenAIEmbeddingProvider()


# Integration test that exercises the complete workflow
class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_csv_to_rag_to_chunks_workflow(self):
        """Test complete CSV → .rag → chunks workflow."""
        from plugins.input.csv import CSVConverter
        
        # 1. Create test CSV
        csv_content = '''Name,Description,Price
Coffee Mug,Premium ceramic mug,24.99
Notebook,Leather-bound notebook,15.50'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            # 2. Convert CSV to .rag
            converter = CSVConverter()
            rag_path = converter.convert(csv_path)
            
            # 3. Process .rag file into chunks
            processor = RAGDocumentProcessor()
            result = processor.process_file(rag_path)
            
            # 4. Verify complete workflow
            assert len(result.chunks) == 2
            assert result.strategy_used == "structured-blocks/empty-line-separated"
            assert "Coffee Mug" in result.chunks[0].text
            assert "Notebook" in result.chunks[1].text
            
            # Clean up
            os.unlink(rag_path)
            
        finally:
            os.unlink(csv_path)