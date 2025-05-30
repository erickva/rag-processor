"""
Unit tests for ValidationEngine.

Tests document validation, client-specific rules, and quality assessment.
"""

import pytest
from rag_processor.core.validator import (
    ValidationEngine, ValidationResult, ValidationIssue, ValidationLevel
)
from rag_processor.strategies.products import ProductsStrategy
from rag_processor.utils.directive_parser import ProcessingDirective


class TestValidationEngine:
    """Test cases for ValidationEngine class."""
    
    def test_validate_valid_content(self, validator, sample_product_catalog, scg_config):
        """Test validation of valid content."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective(
            strategy="products/semantic-boundary",
            validation="studio-camila-golin/product-catalog"
        )
        
        result = validator.validate(sample_product_catalog, strategy, scg_config, directive)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert result.score > 0.5
        assert result.error_count == 0
    
    def test_validate_empty_content(self, validator, default_config):
        """Test validation of empty content."""
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        result = validator.validate("", strategy, default_config, directive)
        
        assert not result.is_valid
        assert result.error_count > 0
        assert any("empty" in issue.message.lower() for issue in result.issues)
    
    def test_validate_short_content(self, validator, default_config):
        """Test validation of content that's too short."""
        short_content = "Too short"
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        result = validator.validate(short_content, strategy, default_config, directive)
        
        assert not result.is_valid
        assert result.error_count > 0
        assert any("too short" in issue.message.lower() for issue in result.issues)
    
    def test_validate_encoding_issues(self, validator, default_config):
        """Test validation detects encoding issues."""
        # Content with potential encoding artifacts
        problematic_content = "Content with replacement character: \ufffd and smart quote: \u2019" * 10
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        result = validator.validate(problematic_content, strategy, default_config, directive)
        
        # Should detect encoding artifacts as warnings
        encoding_warnings = [
            issue for issue in result.issues 
            if issue.level == ValidationLevel.WARNING and "encoding" in issue.message.lower()
        ]
        assert len(encoding_warnings) > 0
    
    def test_validate_client_specific_rules(self, validator, scg_config):
        """Test client-specific validation rules."""
        # Content missing required fields for SCG
        incomplete_content = """
        Nome: Produto Incompleto
        Preço: R$ 50,00
        """ * 5  # Make it long enough
        
        strategy = ProductsStrategy()
        directive = ProcessingDirective(
            validation="studio-camila-golin/product-catalog",
            metadata={"type": "product_catalog"}
        )
        
        result = validator.validate(incomplete_content, strategy, scg_config, directive)
        
        # Should find missing required fields
        field_errors = [
            issue for issue in result.issues 
            if "required field" in issue.message.lower()
        ]
        assert len(field_errors) > 0
    
    def test_validate_directive_format(self, validator):
        """Test directive validation."""
        # Invalid strategy format
        invalid_directive = ProcessingDirective(
            strategy="invalid-format",  # Should be category/method
            validation="also-invalid",   # Should be client/rules
            chunk_pattern="[invalid regex"  # Invalid regex
        )
        
        result = validator.validate_directive_only(invalid_directive)
        
        assert not result.is_valid
        assert result.error_count >= 3  # Three format errors
    
    def test_validate_directive_valid(self, validator, sample_directive):
        """Test validation of valid directive."""
        result = validator.validate_directive_only(sample_directive)
        
        assert result.is_valid
        assert result.error_count == 0
    
    def test_quality_assessment(self, validator, default_config):
        """Test content quality assessment."""
        # High quality content
        high_quality = """
        This is a well-structured document with multiple paragraphs.
        Each paragraph contains several sentences with proper punctuation.
        
        The content is organized logically and flows naturally from one idea to the next.
        There are no obvious formatting issues or encoding problems.
        
        The length is appropriate for chunking and the structure is clear.
        This should receive a high quality score from the validator.
        """ * 3
        
        # Low quality content
        low_quality = "vry shrt n prlmt frmttng no punc or structure"
        
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        high_result = validator.validate(high_quality, strategy, default_config, directive)
        low_result = validator.validate(low_quality, strategy, default_config, directive)
        
        assert high_result.score > low_result.score
        assert high_result.score > 0.6
    
    def test_validation_levels(self, validator):
        """Test different validation issue levels."""
        # Create issues of different levels
        error_issue = ValidationIssue(
            level=ValidationLevel.ERROR,
            message="Critical error"
        )
        warning_issue = ValidationIssue(
            level=ValidationLevel.WARNING,
            message="Warning message"
        )
        info_issue = ValidationIssue(
            level=ValidationLevel.INFO,
            message="Info message"
        )
        
        result = ValidationResult(
            is_valid=False,
            issues=[error_issue, warning_issue, info_issue],
            score=0.5,
            metadata={}
        )
        
        assert result.error_count == 1
        assert result.warning_count == 1
        assert result.info_count == 1
    
    def test_generate_validation_report(self, validator, mock_validation_result):
        """Test validation report generation."""
        report = validator.generate_validation_report(mock_validation_result)
        
        assert isinstance(report, str)
        assert "Document Validation Report" in report
        assert "VALID" in report
        assert str(mock_validation_result.score) in report
    
    def test_structure_validation(self, validator, default_config):
        """Test document structure validation."""
        # Content with very long lines
        long_line_content = "A" * 600 + "\n" + "Normal line\n" * 5
        
        # Content without paragraph breaks
        no_paragraphs = "Line 1\nLine 2\nLine 3\n" * 100
        
        strategy = ProductsStrategy()
        directive = ProcessingDirective()
        
        long_result = validator.validate(long_line_content, strategy, default_config, directive)
        no_para_result = validator.validate(no_paragraphs, strategy, default_config, directive)
        
        # Should detect structural issues
        long_warnings = [
            issue for issue in long_result.issues
            if "long lines" in issue.message.lower()
        ]
        para_warnings = [
            issue for issue in no_para_result.issues
            if "paragraph" in issue.message.lower()
        ]
        
        assert len(long_warnings) > 0
        assert len(para_warnings) > 0


class TestValidationIssue:
    """Test cases for ValidationIssue class."""
    
    def test_validation_issue_creation(self):
        """Test ValidationIssue creation."""
        issue = ValidationIssue(
            level=ValidationLevel.WARNING,
            message="Test message",
            location="test_location",
            suggestion="Test suggestion"
        )
        
        assert issue.level == ValidationLevel.WARNING
        assert issue.message == "Test message"
        assert issue.location == "test_location"
        assert issue.suggestion == "Test suggestion"
    
    def test_validation_issue_minimal(self):
        """Test ValidationIssue with minimal fields."""
        issue = ValidationIssue(
            level=ValidationLevel.ERROR,
            message="Error message"
        )
        
        assert issue.level == ValidationLevel.ERROR
        assert issue.message == "Error message"
        assert issue.location is None
        assert issue.suggestion is None


class TestValidationResult:
    """Test cases for ValidationResult class."""
    
    def test_validation_result_properties(self):
        """Test ValidationResult computed properties."""
        issues = [
            ValidationIssue(ValidationLevel.ERROR, "Error 1"),
            ValidationIssue(ValidationLevel.ERROR, "Error 2"),
            ValidationIssue(ValidationLevel.WARNING, "Warning 1"),
            ValidationIssue(ValidationLevel.INFO, "Info 1"),
        ]
        
        result = ValidationResult(
            is_valid=False,
            issues=issues,
            score=0.3,
            metadata={}
        )
        
        assert result.error_count == 2
        assert result.warning_count == 1
        assert result.info_count == 1
    
    def test_validation_result_empty_issues(self):
        """Test ValidationResult with no issues."""
        result = ValidationResult(
            is_valid=True,
            issues=[],
            score=1.0,
            metadata={}
        )
        
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.info_count == 0