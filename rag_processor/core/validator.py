"""
Document validation engine.

Validates documents against processing strategies and client-specific rules
to ensure quality and suitability for RAG processing.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.directive_parser import ProcessingDirective
from ..strategies.base import ProcessingStrategy
from ..clients.base import ClientConfig
from config.constants import (
    MINIMUM_DOCUMENT_LENGTH, UTF8_ENCODING, ERROR_INVALID_ENCODING,
    ERROR_DOCUMENT_TOO_SHORT, ERROR_VALIDATION_FAILED
)


class ValidationLevel(Enum):
    """Validation severity levels."""
    
    ERROR = "error"         # Critical issues that prevent processing
    WARNING = "warning"     # Issues that may affect quality
    INFO = "info"          # Informational notes


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    
    level: ValidationLevel
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation results."""
    
    is_valid: bool
    issues: List[ValidationIssue]
    score: float  # 0.0 to 1.0 quality score
    metadata: Dict[str, Any]
    
    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return len([issue for issue in self.issues if issue.level == ValidationLevel.ERROR])
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return len([issue for issue in self.issues if issue.level == ValidationLevel.WARNING])
    
    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return len([issue for issue in self.issues if issue.level == ValidationLevel.INFO])


class ValidationEngine:
    """
    Document validation engine.
    
    Performs comprehensive validation of documents against processing strategies
    and client-specific rules to ensure optimal RAG performance.
    """
    
    def __init__(self):
        """Initialize validation engine."""
        pass
    
    def validate(
        self,
        content: str,
        strategy: ProcessingStrategy,
        client_config: ClientConfig,
        directive: ProcessingDirective
    ) -> ValidationResult:
        """
        Validate document content comprehensively.
        
        Args:
            content (str): Document text content to validate
            strategy (ProcessingStrategy): Processing strategy to validate against
            client_config (ClientConfig): Client configuration for specific rules
            directive (ProcessingDirective): Processing directives from document
            
        Returns:
            ValidationResult: Complete validation results
        """
        issues = []
        metadata = {}
        
        # Universal validation checks
        issues.extend(self._validate_basic_requirements(content))
        issues.extend(self._validate_encoding(content))
        issues.extend(self._validate_structure(content))
        
        # Strategy-specific validation
        strategy_issues = strategy.validate_content(content, directive)
        for issue_msg in strategy_issues:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=issue_msg,
                location="strategy_validation"
            ))
        
        # Client-specific validation
        issues.extend(self._validate_client_rules(content, client_config, directive))
        
        # Directive validation
        issues.extend(self._validate_directive(directive))
        
        # Content quality assessment
        quality_issues, quality_score = self._assess_content_quality(content, strategy, client_config)
        issues.extend(quality_issues)
        
        # Calculate overall validation status
        error_count = len([issue for issue in issues if issue.level == ValidationLevel.ERROR])
        is_valid = error_count == 0
        
        # Build metadata
        metadata.update({
            "content_length": len(content),
            "strategy_name": strategy.name,
            "client_name": client_config.name,
            "validation_timestamp": self._get_timestamp(),
            "total_issues": len(issues),
            "quality_score": quality_score,
        })
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            score=quality_score,
            metadata=metadata
        )
    
    def validate_directive_only(self, directive: ProcessingDirective) -> ValidationResult:
        """
        Validate only the processing directive without content.
        
        Args:
            directive (ProcessingDirective): Processing directive to validate
            
        Returns:
            ValidationResult: Directive validation results
        """
        issues = self._validate_directive(directive)
        
        error_count = len([issue for issue in issues if issue.level == ValidationLevel.ERROR])
        is_valid = error_count == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            score=1.0 if is_valid else 0.5,
            metadata={"validation_type": "directive_only"}
        )
    
    def _validate_basic_requirements(self, content: str) -> List[ValidationIssue]:
        """Validate basic document requirements."""
        issues = []
        
        # Minimum length check
        if len(content) < MINIMUM_DOCUMENT_LENGTH:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"{ERROR_DOCUMENT_TOO_SHORT}: {len(content)} characters (minimum: {MINIMUM_DOCUMENT_LENGTH})",
                suggestion=f"Add more content to reach minimum {MINIMUM_DOCUMENT_LENGTH} characters"
            ))
        
        # Empty or whitespace-only content
        if not content.strip():
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message="Document is empty or contains only whitespace",
                suggestion="Add meaningful content to the document"
            ))
        
        # Very short lines might indicate formatting issues
        lines = content.split('\n')
        short_lines = [line for line in lines if 0 < len(line.strip()) < 10]
        if len(short_lines) > len(lines) * 0.3:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Many very short lines detected - possible formatting issues",
                suggestion="Check document formatting and line breaks"
            ))
        
        return issues
    
    def _validate_encoding(self, content: str) -> List[ValidationIssue]:
        """Validate document encoding."""
        issues = []
        
        try:
            # Test encoding by attempting to encode/decode
            content.encode(UTF8_ENCODING).decode(UTF8_ENCODING)
        except UnicodeError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"{ERROR_INVALID_ENCODING}: {str(e)}",
                suggestion="Ensure document is saved in UTF-8 encoding"
            ))
        
        # Check for common encoding artifacts
        encoding_artifacts = [
            '\ufffd',  # Replacement character
            '\xa0',    # Non-breaking space
            '\u2019',  # Smart quote (common in copy-paste from Word)
        ]
        
        for artifact in encoding_artifacts:
            if artifact in content:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Encoding artifact detected: {repr(artifact)}",
                    suggestion="Clean up special characters or encoding issues"
                ))
        
        return issues
    
    def _validate_structure(self, content: str) -> List[ValidationIssue]:
        """Validate document structure."""
        issues = []
        
        lines = content.split('\n')
        
        # Check for reasonable line length distribution
        very_long_lines = [line for line in lines if len(line) > 500]
        if very_long_lines:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"{len(very_long_lines)} very long lines detected (>500 chars)",
                suggestion="Consider breaking long lines for better readability"
            ))
        
        # Check for paragraph structure
        paragraph_breaks = len(re.findall(r'\n\s*\n', content))
        if paragraph_breaks == 0 and len(content) > 1000:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="No paragraph breaks detected in long document",
                suggestion="Add paragraph breaks to improve structure"
            ))
        
        # Check for potential OCR errors (common patterns)
        ocr_patterns = [
            r'\b[a-z]\s[a-z]\s[a-z]\b',  # Scattered letters
            r'\b\d\s\d\s\d\b',          # Scattered numbers
            r'[Il1|]{3,}',               # Common OCR confusion characters
        ]
        
        for pattern in ocr_patterns:
            matches = re.findall(pattern, content)
            if len(matches) > 5:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Possible OCR artifacts detected: {len(matches)} matches for pattern {pattern}",
                    suggestion="Review content for OCR scanning errors"
                ))
        
        return issues
    
    def _validate_client_rules(
        self,
        content: str,
        client_config: ClientConfig,
        directive: ProcessingDirective
    ) -> List[ValidationIssue]:
        """Validate against client-specific rules."""
        issues = []
        
        validation_rules = client_config.get_validation_rules()
        
        # Check minimum content length (client-specific)
        min_length = validation_rules.get("minimum_content_length", MINIMUM_DOCUMENT_LENGTH)
        if len(content) < min_length:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                message=f"Content too short for {client_config.name}: {len(content)} < {min_length} chars",
                suggestion=f"Add more content to meet {client_config.name} requirements"
            ))
        
        # Check required fields based on document type
        if directive.metadata and "type" in directive.metadata:
            doc_type = directive.metadata["type"]
            required_fields = client_config.get_required_fields(doc_type)
            
            for field in required_fields:
                if field not in content:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Required field missing: {field}",
                        location=f"client_validation/{client_config.name}",
                        suggestion=f"Add '{field}' field to document"
                    ))
        
        # Validate field formats
        field_patterns = client_config.get_field_patterns()
        for field_name, pattern in field_patterns.items():
            # Look for field in content
            field_regex = f'{re.escape(field_name)}:\s*([^\n]+)'
            field_matches = re.finditer(field_regex, content, re.IGNORECASE)
            
            for match in field_matches:
                field_value = match.group(1).strip()
                if not client_config.validate_field_format(field_name, field_value):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Field '{field_name}' format doesn't match expected pattern: {field_value}",
                        location=f"line_containing:{field_value[:30]}",
                        suggestion=f"Ensure {field_name} follows expected format"
                    ))
        
        # Client-specific content validation
        if hasattr(client_config, 'validate_product_completeness') and 'product' in content.lower():
            # Special validation for product catalogs
            validation_issues = client_config.validate_product_completeness(content)
            for issue_msg in validation_issues:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=issue_msg,
                    location="product_validation"
                ))
        
        return issues
    
    def _validate_directive(self, directive: ProcessingDirective) -> List[ValidationIssue]:
        """Validate processing directive."""
        issues = []
        
        # Validate strategy format
        if directive.strategy:
            if '/' not in directive.strategy:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Strategy must be in format 'category/method'",
                    location="directive.strategy",
                    suggestion="Use format like 'products/semantic-boundary'"
                ))
        
        # Validate source URL format
        if directive.source_url:
            if not (directive.source_url.startswith('http://') or directive.source_url.startswith('https://')):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="Source URL should be a valid HTTP/HTTPS URL",
                    location="directive.source_url",
                    suggestion="Use format like 'https://example.com/document.pdf'"
                ))
        
        # Validate metadata structure
        if directive.metadata:
            if not isinstance(directive.metadata, dict):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message="Metadata must be a JSON object",
                    location="directive.metadata"
                ))
            else:
                # Check for required metadata fields
                recommended_fields = ["type", "version"]
                for field in recommended_fields:
                    if field not in directive.metadata:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.INFO,
                            message=f"Recommended metadata field missing: {field}",
                            location="directive.metadata",
                            suggestion=f"Consider adding '{field}' to metadata"
                        ))
        
        return issues
    
    def _assess_content_quality(
        self,
        content: str,
        strategy: ProcessingStrategy,
        client_config: ClientConfig
    ) -> tuple[List[ValidationIssue], float]:
        """Assess overall content quality and provide score."""
        issues = []
        quality_factors = {}
        
        # Content length quality
        length = len(content)
        if length < 500:
            quality_factors["length"] = 0.3
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Content is quite short - may limit chunking effectiveness",
                suggestion="Consider adding more content for better RAG performance"
            ))
        elif length > 10000:
            quality_factors["length"] = 0.9
        else:
            quality_factors["length"] = min(0.8, length / 5000)
        
        # Structure quality
        paragraph_count = len(re.split(r'\n\s*\n', content))
        if paragraph_count < 3:
            quality_factors["structure"] = 0.4
        elif paragraph_count > 20:
            quality_factors["structure"] = 0.9
        else:
            quality_factors["structure"] = min(0.8, paragraph_count / 10)
        
        # Language quality (basic assessment)
        sentence_count = len(re.findall(r'[.!?]+', content))
        word_count = len(content.split())
        
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
            if 10 <= avg_sentence_length <= 30:
                quality_factors["language"] = 0.8
            elif 5 <= avg_sentence_length <= 50:
                quality_factors["language"] = 0.6
            else:
                quality_factors["language"] = 0.4
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Average sentence length unusual: {avg_sentence_length:.1f} words",
                    suggestion="Review sentence structure for optimal readability"
                ))
        else:
            quality_factors["language"] = 0.2
        
        # Strategy compatibility
        strategy_issues = strategy.validate_content(content, ProcessingDirective())
        if not strategy_issues:
            quality_factors["strategy_fit"] = 0.9
        elif len(strategy_issues) <= 2:
            quality_factors["strategy_fit"] = 0.7
        else:
            quality_factors["strategy_fit"] = 0.4
        
        # Calculate weighted quality score
        weights = {
            "length": 0.2,
            "structure": 0.3,
            "language": 0.2,
            "strategy_fit": 0.3,
        }
        
        quality_score = sum(
            quality_factors.get(factor, 0.5) * weight
            for factor, weight in weights.items()
        )
        
        # Quality score assessment
        if quality_score < 0.4:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Low content quality score: {quality_score:.2f}",
                suggestion="Consider improving content structure and clarity"
            ))
        elif quality_score > 0.8:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"High quality content detected: {quality_score:.2f}",
                suggestion="Content is well-structured for RAG processing"
            ))
        
        return issues, quality_score
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for validation metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            result (ValidationResult): Validation results to report
            
        Returns:
            str: Formatted validation report
        """
        lines = []
        
        # Header
        lines.append("# Document Validation Report")
        lines.append(f"**Status**: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
        lines.append(f"**Quality Score**: {result.score:.2f}/1.0")
        lines.append(f"**Total Issues**: {len(result.issues)}")
        lines.append("")
        
        # Summary
        if result.error_count > 0:
            lines.append(f"🔴 **Errors**: {result.error_count} (must be fixed)")
        if result.warning_count > 0:
            lines.append(f"🟡 **Warnings**: {result.warning_count} (should be reviewed)")
        if result.info_count > 0:
            lines.append(f"🔵 **Info**: {result.info_count} (informational)")
        lines.append("")
        
        # Issues by category
        if result.issues:
            lines.append("## Issues Found")
            lines.append("")
            
            for level in [ValidationLevel.ERROR, ValidationLevel.WARNING, ValidationLevel.INFO]:
                level_issues = [issue for issue in result.issues if issue.level == level]
                if level_issues:
                    level_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}[level.value]
                    lines.append(f"### {level_icon} {level.value.title()} Issues")
                    lines.append("")
                    
                    for i, issue in enumerate(level_issues, 1):
                        lines.append(f"{i}. **{issue.message}**")
                        if issue.location:
                            lines.append(f"   - Location: {issue.location}")
                        if issue.suggestion:
                            lines.append(f"   - Suggestion: {issue.suggestion}")
                        lines.append("")
        else:
            lines.append("## ✅ No Issues Found")
            lines.append("Document passed all validation checks!")
            lines.append("")
        
        # Metadata
        lines.append("## Validation Details")
        lines.append("")
        for key, value in result.metadata.items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        return '\n'.join(lines)