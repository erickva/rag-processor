"""
Unit tests for DirectiveParser.

Tests parsing of .rag file headers and processing directives.
"""

import pytest
import json
from rag_processor.utils.directive_parser import DirectiveParser, ProcessingDirective


class TestDirectiveParser:
    """Test cases for DirectiveParser class."""
    
    def test_parse_empty_content(self, directive_parser):
        """Test parsing content with no directives."""
        content = "Just plain text content with no directives."
        
        directive = directive_parser.parse(content)
        
        assert directive.strategy is None
        assert directive.validation is None
        assert directive.chunk_pattern is None
        assert directive.metadata == {}
        assert directive.custom_rules == {}
    
    def test_parse_complete_directive(self, directive_parser):
        """Test parsing complete directive with all fields."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary
#!validation: studio-camila-golin/product-catalog
#!chunk-pattern: Nome:\\s*([^\\n]+)
#!metadata: {"business": "studio-camila-golin", "type": "product-catalog", "version": "1.0"}
#!custom-rules: {"overlap": 0, "preserve_integrity": true}

Content starts here.
'''
        
        directive = directive_parser.parse(content)
        
        assert directive.strategy == "products/semantic-boundary"
        assert directive.validation == "studio-camila-golin/product-catalog"
        assert directive.chunk_pattern == r"Nome:\s*([^\n]+)"
        assert directive.metadata["business"] == "studio-camila-golin"
        assert directive.metadata["type"] == "product-catalog"
        assert directive.custom_rules["overlap"] == 0
        assert directive.custom_rules["preserve_integrity"] is True
    
    def test_parse_partial_directive(self, directive_parser):
        """Test parsing directive with only some fields."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: manual/section-based
#!metadata: {"type": "user-manual"}

Content here.
'''
        
        directive = directive_parser.parse(content)
        
        assert directive.strategy == "manual/section-based"
        assert directive.validation is None
        assert directive.chunk_pattern is None
        assert directive.metadata["type"] == "user-manual"
        assert directive.custom_rules == {}
    
    def test_extract_content(self, directive_parser):
        """Test extracting content without directive headers."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary
#!validation: studio-camila-golin/product-catalog

This is the actual content.
It should be extracted without the directives.

Nome: Product 1
Categoria: Test
'''
        
        extracted = directive_parser.extract_content(content)
        
        assert not extracted.startswith("#!")
        assert "This is the actual content." in extracted
        assert "Nome: Product 1" in extracted
        assert extracted.strip().startswith("This is the actual content.")
    
    def test_create_directive_header(self, directive_parser):
        """Test creating directive header from ProcessingDirective."""
        directive = ProcessingDirective(
            strategy="faq/qa-pairs",
            validation="default/faq",
            chunk_pattern=r"(Q:|Question:)",
            metadata={"type": "faq", "version": "1.0"},
            custom_rules={"require_answers": True}
        )
        
        header = directive_parser.create_directive_header(directive)
        
        assert header.startswith("#!/usr/bin/env rag-processor")
        assert "#!strategy: faq/qa-pairs" in header
        assert "#!validation: default/faq" in header
        assert "#!chunk-pattern: (Q:|Question:)" in header
        assert '"type":"faq"' in header
        assert '"require_answers":true' in header
    
    def test_parse_invalid_json_metadata(self, directive_parser):
        """Test parsing directive with invalid JSON metadata."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary
#!metadata: {invalid json here}

Content.
'''
        
        with pytest.raises(ValueError) as exc_info:
            directive_parser.parse(content)
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_parse_invalid_json_custom_rules(self, directive_parser):
        """Test parsing directive with invalid JSON custom rules."""
        content = '''#!/usr/bin/env rag-processor
#!custom-rules: {also invalid json

Content.
'''
        
        with pytest.raises(ValueError) as exc_info:
            directive_parser.parse(content)
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_validate_directive_valid(self, directive_parser):
        """Test validation of valid directive."""
        directive = ProcessingDirective(
            strategy="products/semantic-boundary",
            validation="studio-camila-golin/product-catalog",
            chunk_pattern=r"Nome:\s*([^\n]+)",
            metadata={"type": "product-catalog"},
            custom_rules={"overlap": 0}
        )
        
        issues = directive_parser.validate_directive(directive)
        
        assert len(issues) == 0
    
    def test_validate_directive_invalid_strategy(self, directive_parser):
        """Test validation of directive with invalid strategy format."""
        directive = ProcessingDirective(
            strategy="invalid-format",  # Should be category/method
        )
        
        issues = directive_parser.validate_directive(directive)
        
        assert len(issues) > 0
        assert any("strategy" in issue.lower() and "format" in issue.lower() for issue in issues)
    
    def test_validate_directive_invalid_validation(self, directive_parser):
        """Test validation of directive with invalid validation format."""
        directive = ProcessingDirective(
            validation="invalid-format",  # Should be client/rules
        )
        
        issues = directive_parser.validate_directive(directive)
        
        assert len(issues) > 0
        assert any("validation" in issue.lower() and "format" in issue.lower() for issue in issues)
    
    def test_validate_directive_invalid_regex(self, directive_parser):
        """Test validation of directive with invalid regex pattern."""
        directive = ProcessingDirective(
            chunk_pattern="[invalid regex(",  # Unclosed bracket
        )
        
        issues = directive_parser.validate_directive(directive)
        
        assert len(issues) > 0
        assert any("regex" in issue.lower() or "pattern" in issue.lower() for issue in issues)
    
    def test_validate_directive_invalid_metadata_type(self, directive_parser):
        """Test validation of directive with invalid metadata type."""
        directive = ProcessingDirective(
            metadata="not a dict"  # Should be dict
        )
        
        issues = directive_parser.validate_directive(directive)
        
        assert len(issues) > 0
        assert any("metadata" in issue.lower() and "object" in issue.lower() for issue in issues)
    
    def test_parse_multiline_content(self, directive_parser):
        """Test parsing content with multiple sections."""
        content = '''#!/usr/bin/env rag-processor
#!strategy: manual/section-based

# Introduction

This is the introduction section.

## Getting Started

Step 1: Read the documentation
Step 2: Install the software
Step 3: Configure your settings

## Advanced Features

Advanced functionality is available for experienced users.
'''
        
        directive = directive_parser.parse(content)
        extracted = directive_parser.extract_content(content)
        
        assert directive.strategy == "manual/section-based"
        assert "# Introduction" in extracted
        assert "## Getting Started" in extracted
        assert "## Advanced Features" in extracted
        assert not extracted.startswith("#!")
    
    def test_parse_windows_line_endings(self, directive_parser):
        """Test parsing content with Windows line endings."""
        content = "#!/usr/bin/env rag-processor\r\n#!strategy: products/semantic-boundary\r\n\r\nContent here.\r\n"
        
        directive = directive_parser.parse(content)
        extracted = directive_parser.extract_content(content)
        
        assert directive.strategy == "products/semantic-boundary"
        assert "Content here." in extracted
    
    def test_parse_with_comments(self, directive_parser):
        """Test parsing content with additional comments."""
        content = '''#!/usr/bin/env rag-processor
# This is a comment and should be ignored
#!strategy: faq/qa-pairs
# Another comment
#!validation: default/faq

Q: What is this?
A: This is content.
'''
        
        directive = directive_parser.parse(content)
        extracted = directive_parser.extract_content(content)
        
        assert directive.strategy == "faq/qa-pairs"
        assert directive.validation == "default/faq"
        assert "Q: What is this?" in extracted
        assert "# This is a comment" not in extracted


class TestProcessingDirective:
    """Test cases for ProcessingDirective class."""
    
    def test_processing_directive_defaults(self):
        """Test ProcessingDirective with default values."""
        directive = ProcessingDirective()
        
        assert directive.strategy is None
        assert directive.validation is None
        assert directive.chunk_pattern is None
        assert directive.metadata == {}
        assert directive.custom_rules == {}
    
    def test_processing_directive_initialization(self):
        """Test ProcessingDirective initialization with values."""
        metadata = {"type": "test", "version": "1.0"}
        custom_rules = {"overlap": 100, "preserve": True}
        
        directive = ProcessingDirective(
            strategy="test/strategy",
            validation="test/validation",
            chunk_pattern=r"test:\s*(.+)",
            metadata=metadata,
            custom_rules=custom_rules
        )
        
        assert directive.strategy == "test/strategy"
        assert directive.validation == "test/validation"
        assert directive.chunk_pattern == r"test:\s*(.+)"
        assert directive.metadata == metadata
        assert directive.custom_rules == custom_rules
    
    def test_processing_directive_post_init(self):
        """Test ProcessingDirective __post_init__ method."""
        directive = ProcessingDirective(
            strategy="test/strategy",
            metadata=None,  # Should be converted to {}
            custom_rules=None  # Should be converted to {}
        )
        
        assert directive.metadata == {}
        assert directive.custom_rules == {}