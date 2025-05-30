"""
Integration tests for RAGDocumentProcessor.

Tests the complete processing pipeline from input to output.
"""

import pytest
import json
import tempfile
from pathlib import Path

from rag_processor.core.processor import RAGDocumentProcessor, ProcessingResult
from rag_processor.core.analyzer import DocumentType
from tests.conftest import assert_chunk_quality


class TestRAGDocumentProcessor:
    """Integration test cases for RAGDocumentProcessor."""
    
    def test_process_complete_pipeline(self, processor, sample_rag_file, create_temp_file):
        """Test complete processing pipeline from .rag file to chunks."""
        # Create temporary .rag file
        rag_file = create_temp_file(sample_rag_file, suffix=".rag")
        
        try:
            result = processor.process_file(str(rag_file))
            
            assert isinstance(result, ProcessingResult)
            assert len(result.chunks) > 0
            assert result.strategy_used == "products/semantic-boundary"
            assert result.analysis.document_type == DocumentType.PRODUCT_CATALOG
            assert result.validation.is_valid
            assert result.processing_time > 0
            
            # Check chunk quality
            assert_chunk_quality(result.chunks, min_chunks=2)
            
            # Each chunk should be a complete product
            for chunk in result.chunks:
                assert "Nome:" in chunk.text
                assert chunk.metadata["strategy"] == "products/semantic-boundary"
        
        finally:
            rag_file.unlink()
    
    def test_process_content_directly(self, processor, sample_rag_file):
        """Test processing content directly without file."""
        result = processor.process_content(sample_rag_file)
        
        assert isinstance(result, ProcessingResult)
        assert len(result.chunks) > 0
        assert result.strategy_used == "products/semantic-boundary"
        assert result.analysis.confidence > 0.5
    
    def test_analyze_document(self, processor, create_temp_file, sample_product_catalog):
        """Test document analysis."""
        test_file = create_temp_file(sample_product_catalog)
        
        try:
            analysis = processor.analyze_document(str(test_file))
            
            assert analysis.document_type == DocumentType.PRODUCT_CATALOG
            assert analysis.confidence > 0.5
            assert analysis.recommended_strategy == "products/semantic-boundary"
            assert len(analysis.detected_patterns) > 0
        
        finally:
            test_file.unlink()
    
    def test_validate_document(self, processor, sample_rag_file, create_temp_file):
        """Test document validation."""
        rag_file = create_temp_file(sample_rag_file, suffix=".rag")
        
        try:
            validation = processor.validate_document(str(rag_file))
            
            assert validation.is_valid
            assert validation.score > 0.5
            assert validation.error_count == 0
        
        finally:
            rag_file.unlink()
    
    def test_create_template(self, processor):
        """Test template creation."""
        template = processor.create_template(DocumentType.PRODUCT_CATALOG, "studio-camila-golin")
        
        assert template.startswith("#!/usr/bin/env rag-processor")
        assert "#!strategy: products/semantic-boundary" in template
        assert "#!validation: studio-camila-golin/product-catalog" in template
        assert "Nome: Exemplo de Produto" in template
    
    def test_strategy_registration(self, processor):
        """Test strategy registration and retrieval."""
        strategies = processor.get_available_strategies()
        
        expected_strategies = [
            "products/semantic-boundary",
            "manual/section-based",
            "faq/qa-pairs",
            "article/sentence-based",
            "legal/paragraph-based",
            "code/function-based",
        ]
        
        for strategy in expected_strategies:
            assert strategy in strategies
    
    def test_client_registration(self, processor):
        """Test client configuration registration and retrieval."""
        clients = processor.get_available_clients()
        
        assert "default" in clients
        assert "studio-camila-golin" in clients
    
    def test_process_invalid_file(self, processor):
        """Test processing non-existent file."""
        with pytest.raises(FileNotFoundError):
            processor.process_file("non_existent_file.rag")
    
    def test_process_invalid_extension(self, processor, create_temp_file):
        """Test processing file without .rag extension."""
        test_file = create_temp_file("Content here", suffix=".txt")
        
        try:
            with pytest.raises(ValueError) as exc_info:
                processor.process_file(str(test_file))
            
            assert ".rag extension" in str(exc_info.value)
        
        finally:
            test_file.unlink()
    
    def test_auto_strategy_selection(self, processor):
        """Test automatic strategy selection based on content analysis."""
        # Product catalog content
        product_content = """
        Nome: Produto A
        Categoria: Teste
        Preço: R$ 100,00
        
        Nome: Produto B
        Categoria: Teste
        Preço: R$ 200,00
        """
        
        # Manual content
        manual_content = """
        # User Guide
        
        ## Chapter 1: Introduction
        
        Welcome to the user guide.
        
        ## Chapter 2: Getting Started
        
        Follow these steps to begin.
        """
        
        product_result = processor.process_content(product_content)
        manual_result = processor.process_content(manual_content)
        
        assert product_result.strategy_used == "products/semantic-boundary"
        assert manual_result.strategy_used == "manual/section-based"
    
    def test_client_specific_processing(self, processor):
        """Test client-specific processing rules."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary
#!validation: studio-camila-golin/product-catalog

Nome: Produto SCG
Categoria: Leques
Descrição: Produto específico da Studio Camila Golin
Preço: R$ 75,00
'''
        
        result = processor.process_content(content)
        
        # Should use SCG-specific configuration
        assert result.strategy_used == "products/semantic-boundary"
        assert "studio-camila-golin" in str(result.validation.metadata)
    
    def test_processing_metadata(self, processor, sample_rag_file):
        """Test processing result metadata."""
        result = processor.process_content(sample_rag_file, "test.rag")
        
        metadata = result.metadata
        assert "filename" in metadata
        assert "total_chunks" in metadata
        assert "total_characters" in metadata
        assert metadata["filename"] == "test.rag"
        assert metadata["total_chunks"] == len(result.chunks)
    
    def test_error_handling_invalid_directive(self, processor):
        """Test error handling for invalid processing directive."""
        invalid_content = '''#!/usr/bin/env rag-processor
#!strategy: invalid-strategy-format
#!chunk-pattern: [invalid regex

Content here.
'''
        
        with pytest.raises(ValueError):
            processor.process_content(invalid_content)
    
    def test_fallback_strategy_selection(self, processor):
        """Test fallback to default strategy when analysis fails."""
        # Content that doesn't match any specific pattern strongly
        ambiguous_content = "Some text that doesn't clearly indicate document type."
        
        result = processor.process_content(ambiguous_content)
        
        # Should fall back to article strategy
        assert result.strategy_used == "article/sentence-based"
        assert len(result.chunks) > 0


class TestProcessingPerformance:
    """Performance and scalability tests."""
    
    def test_large_document_processing(self, processor):
        """Test processing of large documents."""
        # Create large product catalog
        large_content = """
        Nome: Produto {i}
        Categoria: Categoria Teste
        Descrição: Descrição detalhada do produto {i} com mais informações.
        Preço: R$ {price},00
        
        """.format(i=1, price=50)
        
        # Repeat for many products
        large_content = "".join(
            large_content.format(i=i, price=50 + i)
            for i in range(1, 101)  # 100 products
        )
        
        result = processor.process_content(large_content)
        
        assert len(result.chunks) >= 50  # Should create many chunks
        assert result.processing_time < 10.0  # Should complete in reasonable time
        
        # All chunks should be valid
        assert_chunk_quality(result.chunks, min_chunks=50, min_size=50)
    
    def test_concurrent_processing(self, processor):
        """Test concurrent processing of multiple documents."""
        import threading
        import time
        
        contents = [
            "Nome: Produto A\nCategoria: Teste\nPreço: R$ 100",
            "# Manual Section\nContent here for manual.",
            "Q: Question?\nA: Answer here for FAQ.",
        ]
        
        results = []
        threads = []
        
        def process_content(content):
            result = processor.process_content(content)
            results.append(result)
        
        start_time = time.time()
        
        # Start concurrent processing
        for content in contents:
            thread = threading.Thread(target=process_content, args=(content,))
            thread.start()
            threads.append(thread)
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        assert len(results) == 3
        assert all(len(result.chunks) > 0 for result in results)
        assert end_time - start_time < 5.0  # Should complete quickly
    
    def test_memory_efficiency(self, processor):
        """Test memory efficiency with multiple processing cycles."""
        import gc
        
        # Process multiple times to check for memory leaks
        for i in range(10):
            content = f"""
            Nome: Produto {i}
            Categoria: Teste {i}
            Descrição: Produto de teste número {i}
            Preço: R$ {100 + i * 10},00
            """
            
            result = processor.process_content(content)
            assert len(result.chunks) > 0
            
            # Force garbage collection
            gc.collect()
        
        # Should complete without memory issues