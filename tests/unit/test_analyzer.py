"""
Unit tests for DocumentAnalyzer.

Tests document type detection, pattern matching, and confidence scoring.
"""

import pytest
from rag_processor.core.analyzer import DocumentAnalyzer, DocumentType, DocumentAnalysis


class TestDocumentAnalyzer:
    """Test cases for DocumentAnalyzer class."""
    
    def test_analyze_product_catalog(self, analyzer, sample_product_catalog):
        """Test analysis of product catalog content."""
        analysis = analyzer.analyze(sample_product_catalog)
        
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.document_type == DocumentType.PRODUCT_CATALOG
        assert analysis.confidence > 0.5
        assert analysis.recommended_strategy == "products/semantic-boundary"
        assert "Nome:" in str(analysis.detected_patterns)
    
    def test_analyze_user_manual(self, analyzer, sample_user_manual):
        """Test analysis of user manual content."""
        analysis = analyzer.analyze(sample_user_manual)
        
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.document_type == DocumentType.USER_MANUAL
        assert analysis.confidence > 0.4
        assert analysis.recommended_strategy == "manual/section-based"
    
    def test_analyze_faq(self, analyzer, sample_faq):
        """Test analysis of FAQ content."""
        analysis = analyzer.analyze(sample_faq)
        
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.document_type == DocumentType.FAQ
        assert analysis.confidence > 0.4
        assert analysis.recommended_strategy == "faq/qa-pairs"
    
    def test_analyze_empty_content(self, analyzer):
        """Test analysis of empty content."""
        analysis = analyzer.analyze("")
        
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.document_type == DocumentType.UNKNOWN
        assert analysis.confidence == 0.0
    
    def test_analyze_short_content(self, analyzer):
        """Test analysis of very short content."""
        short_content = "This is a very short text."
        analysis = analyzer.analyze(short_content)
        
        assert isinstance(analysis, DocumentAnalysis)
        assert analysis.confidence < 0.5
        assert analysis.analysis_details["content_length"] == len(short_content)
    
    def test_pattern_detection_product_catalog(self, analyzer):
        """Test specific pattern detection for product catalogs."""
        content = """
        Nome: Produto 1
        Categoria: Teste
        Preço: R$ 100,00
        
        Nome: Produto 2
        Categoria: Teste
        Preço: R$ 200,00
        """
        
        analysis = analyzer.analyze(content)
        patterns = analysis.detected_patterns
        
        # Should detect multiple instances of product patterns
        product_patterns = [key for key in patterns.keys() if "Nome:" in key]
        assert len(product_patterns) > 0
    
    def test_confidence_scoring(self, analyzer):
        """Test confidence scoring algorithm."""
        # High confidence content
        high_conf_content = """
        Nome: Produto A
        Categoria: Categoria A
        Descrição: Descrição detalhada
        Preço: R$ 50,00
        
        Nome: Produto B
        Categoria: Categoria B
        Descrição: Outra descrição
        Preço: R$ 75,00
        """ * 3  # Repeat to increase confidence
        
        # Low confidence content
        low_conf_content = "This is just some random text without clear structure."
        
        high_analysis = analyzer.analyze(high_conf_content)
        low_analysis = analyzer.analyze(low_conf_content)
        
        assert high_analysis.confidence > low_analysis.confidence
        assert high_analysis.confidence > 0.6
        assert low_analysis.confidence < 0.4
    
    def test_get_confidence_level(self, analyzer):
        """Test confidence level classification."""
        assert analyzer.get_confidence_level(0.8) == "High"
        assert analyzer.get_confidence_level(0.5) == "Medium"
        assert analyzer.get_confidence_level(0.2) == "Low"
    
    def test_suggest_improvements(self, analyzer):
        """Test improvement suggestions."""
        # Low confidence analysis
        low_conf_analysis = DocumentAnalysis(
            document_type=DocumentType.UNKNOWN,
            confidence=0.2,
            detected_patterns={},
            recommended_strategy="article/sentence-based",
            analysis_details={"content_length": 100}
        )
        
        suggestions = analyzer.suggest_improvements(low_conf_analysis)
        assert len(suggestions) > 0
        assert any("confidence" in suggestion.lower() for suggestion in suggestions)
    
    def test_analysis_details_structure(self, analyzer, sample_product_catalog):
        """Test that analysis details contain expected fields."""
        analysis = analyzer.analyze(sample_product_catalog)
        
        details = analysis.analysis_details
        assert "content_length" in details
        assert "type_scores" in details
        assert "pattern_analysis" in details
        
        pattern_analysis = details["pattern_analysis"]
        assert "total_lines" in pattern_analysis
        assert "has_structured_fields" in pattern_analysis
        assert "language_indicators" in pattern_analysis
    
    def test_language_detection(self, analyzer):
        """Test language indicator detection."""
        portuguese_content = """
        Nome: Produto em Português
        Descrição: Este é um produto com descrição em português.
        Preço: R$ 100,00
        """
        
        english_content = """
        Name: English Product
        Description: This is a product with English description.
        Price: $100.00
        """
        
        pt_analysis = analyzer.analyze(portuguese_content)
        en_analysis = analyzer.analyze(english_content)
        
        pt_lang = pt_analysis.analysis_details["pattern_analysis"]["language_indicators"]
        en_lang = en_analysis.analysis_details["pattern_analysis"]["language_indicators"]
        
        assert pt_lang["portuguese"] > pt_lang["english"]
        assert en_lang["english"] > en_lang["portuguese"]


class TestDocumentTypeDetection:
    """Test cases for document type detection."""
    
    @pytest.mark.parametrize("content,expected_type", [
        ("Nome: Test\nCategoria: Test\nPreço: R$ 10", DocumentType.PRODUCT_CATALOG),
        ("# Chapter 1\n## Section 1.1\nContent here", DocumentType.USER_MANUAL),
        ("Q: Question?\nA: Answer here", DocumentType.FAQ),
        ("def function():\n    pass\n\nAPI Documentation", DocumentType.CODE_DOCUMENTATION),
        ("Article 1\nwhereas this agreement", DocumentType.LEGAL_DOCUMENT),
    ])
    def test_document_type_detection(self, analyzer, content, expected_type):
        """Test document type detection for various content types."""
        analysis = analyzer.analyze(content)
        assert analysis.document_type == expected_type
    
    def test_ambiguous_content(self, analyzer):
        """Test handling of ambiguous content that could match multiple types."""
        ambiguous_content = """
        # FAQ Section
        
        Q: What is this?
        A: This is a test.
        
        ## Manual Section
        
        Step 1: Do this
        Step 2: Do that
        """
        
        analysis = analyzer.analyze(ambiguous_content)
        # Should pick one type based on strongest indicators
        assert analysis.document_type != DocumentType.UNKNOWN
        assert 0.0 < analysis.confidence < 1.0