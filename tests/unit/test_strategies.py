"""
Unit tests for processing strategies.

Tests all 6 core processing strategies for proper chunking behavior.
"""

import pytest
from rag_processor.strategies import (
    ProductsStrategy, ManualStrategy, FAQStrategy, 
    ArticleStrategy, LegalStrategy, CodeStrategy
)
from rag_processor.utils.directive_parser import ProcessingDirective
from tests.conftest import assert_chunk_quality, assert_metadata_complete


class TestProductsStrategy:
    """Test cases for ProductsStrategy."""
    
    def test_products_strategy_basic(self, sample_product_catalog, scg_config):
        """Test basic products strategy processing."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(sample_product_catalog, directive, scg_config)
        
        assert_chunk_quality(chunks, min_chunks=2)
        
        # Each chunk should represent a complete product
        for chunk in chunks:
            assert "Nome:" in chunk.text
            assert_metadata_complete(chunk.metadata, ["strategy", "product_name", "chunking_method"])
    
    def test_products_strategy_custom_pattern(self, scg_config):
        """Test products strategy with custom pattern."""
        content = """
        Produto: Item A
        Categoria: Teste
        Valor: R$ 100
        
        Produto: Item B
        Categoria: Teste
        Valor: R$ 200
        """
        
        strategy = ProductsStrategy()
        directive = ProcessingDirective(chunk_pattern=r"Produto:\s*([^\n]+)")
        
        chunks = strategy.process(content, directive, scg_config)
        
        assert len(chunks) == 2
        assert all("Produto:" in chunk.text for chunk in chunks)
    
    def test_products_strategy_metadata_extraction(self, sample_product_catalog, scg_config):
        """Test product metadata extraction."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(sample_product_catalog, directive, scg_config)
        
        # Check metadata extraction
        for chunk in chunks:
            metadata = chunk.metadata
            assert "product_name" in metadata
            assert "has_price" in metadata
            assert "product_fields" in metadata
            
            # Should detect price in products
            if "Preço:" in chunk.text:
                assert metadata["has_price"] is True


class TestManualStrategy:
    """Test cases for ManualStrategy."""
    
    def test_manual_strategy_basic(self, sample_user_manual, default_config):
        """Test basic manual strategy processing."""
        strategy = ManualStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(sample_user_manual, directive, default_config)
        
        assert_chunk_quality(chunks, min_chunks=2)
        
        # Each chunk should contain section content
        for chunk in chunks:
            assert_metadata_complete(chunk.metadata, ["strategy", "section_title", "section_level"])
    
    def test_manual_strategy_hierarchy(self, default_config):
        """Test manual strategy preserves section hierarchy."""
        content = """
        # Main Title
        
        Content for main section.
        
        ## Subsection 1
        
        Content for subsection 1.
        
        ### Sub-subsection
        
        Nested content here.
        
        ## Subsection 2
        
        Content for subsection 2.
        """
        
        strategy = ManualStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        # Should detect different section levels
        levels = [chunk.metadata["section_level"] for chunk in chunks]
        assert min(levels) == 1  # Main section
        assert max(levels) >= 2  # Subsections


class TestFAQStrategy:
    """Test cases for FAQStrategy."""
    
    def test_faq_strategy_basic(self, sample_faq, default_config):
        """Test basic FAQ strategy processing."""
        strategy = FAQStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(sample_faq, directive, default_config)
        
        assert_chunk_quality(chunks, min_chunks=2)
        
        # Each chunk should contain Q&A pair
        for chunk in chunks:
            assert_metadata_complete(chunk.metadata, ["strategy", "question", "question_type"])
    
    def test_faq_strategy_question_types(self, default_config):
        """Test FAQ strategy question type classification."""
        content = """
        Q: What is this product?
        A: This is a test product.
        
        Q: How do I install it?
        A: Follow these steps to install.
        
        Q: Why should I use this?
        A: Because it's the best solution.
        
        Q: When will it be available?
        A: It's available now.
        """
        
        strategy = FAQStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        question_types = [chunk.metadata["question_type"] for chunk in chunks]
        
        # Should classify different question types
        assert "definition" in question_types  # What questions
        assert "procedure" in question_types   # How questions
        assert "explanation" in question_types # Why questions
        assert "timing" in question_types      # When questions


class TestArticleStrategy:
    """Test cases for ArticleStrategy."""
    
    def test_article_strategy_basic(self, default_config):
        """Test basic article strategy processing."""
        content = """
        This is the introduction paragraph of an article. It provides context and sets up the main topic.
        
        The second paragraph develops the main ideas further. It contains multiple sentences that flow naturally.
        Each sentence contributes to the overall narrative and maintains coherence.
        
        The third paragraph continues the discussion. It provides additional details and examples to support the main points.
        This helps readers understand the topic more deeply.
        
        Finally, the conclusion paragraph summarizes the key points. It ties everything together and provides closure.
        """
        
        strategy = ArticleStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        assert_chunk_quality(chunks, min_chunks=1)
        
        for chunk in chunks:
            assert_metadata_complete(chunk.metadata, ["strategy", "sentence_count", "paragraph_count"])
    
    def test_article_strategy_sentence_boundaries(self, default_config):
        """Test article strategy respects sentence boundaries."""
        content = """
        First sentence here. Second sentence follows. Third sentence completes the thought.
        
        Another paragraph with more sentences. This one is longer and more detailed. 
        It should be handled properly by the chunking algorithm.
        """ * 5  # Repeat to ensure chunking
        
        strategy = ArticleStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        # Chunks should end at sentence boundaries
        for chunk in chunks:
            text = chunk.text.strip()
            # Should end with sentence terminator
            assert text.endswith('.') or text.endswith('!') or text.endswith('?')


class TestLegalStrategy:
    """Test cases for LegalStrategy."""
    
    def test_legal_strategy_basic(self, default_config):
        """Test basic legal strategy processing."""
        content = """
        Article 1 - Definitions
        
        For the purposes of this agreement, the following terms shall have the meanings set forth below.
        
        Article 2 - Scope
        
        This agreement governs the relationship between the parties with respect to the subject matter described herein.
        
        Article 3 - Obligations
        
        Each party shall perform its obligations under this agreement in good faith and in accordance with applicable law.
        """
        
        strategy = LegalStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        assert_chunk_quality(chunks, min_chunks=2)
        
        for chunk in chunks:
            assert_metadata_complete(chunk.metadata, ["strategy", "chunking_method"])
    
    def test_legal_strategy_article_detection(self, default_config):
        """Test legal strategy detects articles and sections."""
        content = """
        Article 1 - Introduction
        This is the introduction article with detailed text content.
        
        Section 1.1 - Subsection
        This is a subsection with more specific content.
        
        Article 2 - Main Content
        This is the main content article with comprehensive information.
        """
        
        strategy = LegalStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        # Should detect legal structure
        section_titles = [chunk.metadata.get("section_title", "") for chunk in chunks]
        assert any("Article" in title for title in section_titles)


class TestCodeStrategy:
    """Test cases for CodeStrategy."""
    
    def test_code_strategy_basic(self, default_config):
        """Test basic code strategy processing."""
        content = """
        # API Documentation
        
        ## Authentication
        
        All API calls require authentication.
        
        ### def authenticate(api_key)
        
        Authenticates a user with the provided API key.
        
        **Parameters:**
        - api_key (str): The API key to authenticate with
        
        **Returns:**
        - bool: True if authentication successful
        
        **Example:**
        ```python
        result = authenticate("your-api-key")
        ```
        
        ### def get_user(user_id)
        
        Retrieves user information by ID.
        
        **Parameters:**
        - user_id (int): The user ID to retrieve
        
        **Returns:**
        - dict: User information or None if not found
        """
        
        strategy = CodeStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        assert_chunk_quality(chunks, min_chunks=1)
        
        for chunk in chunks:
            assert_metadata_complete(chunk.metadata, ["strategy", "chunking_method"])
    
    def test_code_strategy_function_detection(self, default_config):
        """Test code strategy detects functions and classes."""
        content = """
        ### def process_document(content)
        
        Processes a document with the given content.
        
        ### class DocumentProcessor
        
        Main class for processing documents.
        
        ### function validateInput(data)
        
        JavaScript function to validate input data.
        """
        
        strategy = CodeStrategy()
        directive = ProcessingDirective()
        
        chunks = strategy.process(content, directive, default_config)
        
        # Should detect code elements
        element_types = [chunk.metadata.get("code_element_type", "") for chunk in chunks]
        assert any(element_type in ["function", "class", "section"] for element_type in element_types)


class TestStrategyValidation:
    """Test strategy validation methods."""
    
    def test_products_validation(self, sample_product_catalog):
        """Test products strategy content validation."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        issues = strategy.validate_content(sample_product_catalog, directive)
        
        # Should have no issues with valid product catalog
        assert len(issues) == 0
    
    def test_products_validation_invalid(self):
        """Test products strategy with invalid content."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        invalid_content = "This is not a product catalog at all."
        
        issues = strategy.validate_content(invalid_content, directive)
        
        # Should detect issues
        assert len(issues) > 0
        assert any("product" in issue.lower() for issue in issues)
    
    @pytest.mark.parametrize("strategy_class,valid_content,invalid_content", [
        (ManualStrategy, "# Section 1\nContent here", "No structure here"),
        (FAQStrategy, "Q: Question?\nA: Answer", "No questions here"),
        (ArticleStrategy, "First sentence. Second sentence.", "x"),
        (LegalStrategy, "Article 1\nLegal content", "Not legal"),
        (CodeStrategy, "def function():\n    pass", "No code here"),
    ])
    def test_strategy_validation_patterns(self, strategy_class, valid_content, invalid_content):
        """Test validation for all strategies."""
        strategy = strategy_class()
        directive = ProcessingDirective()
        
        valid_issues = strategy.validate_content(valid_content, directive)
        invalid_issues = strategy.validate_content(invalid_content, directive)
        
        # Valid content should have fewer issues
        assert len(valid_issues) <= len(invalid_issues)