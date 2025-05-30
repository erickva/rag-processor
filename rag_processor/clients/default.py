"""
Default client configuration.

Provides standard validation rules and field patterns that work
for most general use cases.
"""

from typing import Dict, List, Any

from .base import ClientConfig


class DefaultConfig(ClientConfig):
    """
    Default client configuration with general validation rules.
    
    Used as fallback when no specific client configuration is specified.
    """
    
    @property
    def name(self) -> str:
        """Client configuration name."""
        return "default"
    
    @property
    def description(self) -> str:
        """Human-readable description of client configuration."""
        return "Default configuration with standard validation rules"
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get default validation rules.
        
        Returns:
            Dict[str, Any]: Standard validation configuration
        """
        return {
            "minimum_content_length": 100,
            "require_utf8_encoding": True,
            "allow_empty_chunks": False,
            "validate_chunk_coherence": True,
            "max_chunk_size": 2000,
            "min_chunk_size": 50,
        }
    
    def get_required_fields(self, document_type: str) -> List[str]:
        """
        Get required fields for different document types.
        
        Args:
            document_type (str): Type of document being processed
            
        Returns:
            List[str]: List of required field patterns
        """
        field_requirements = {
            "product_catalog": [],  # No strict requirements for default
            "user_manual": [],
            "faq": [],
            "article": [],
            "legal_document": [],
            "code_documentation": [],
        }
        
        return field_requirements.get(document_type, [])
    
    def get_field_patterns(self) -> Dict[str, str]:
        """
        Get regex patterns for field validation.
        
        Returns:
            Dict[str, str]: Field name to regex pattern mapping
        """
        return {
            # General patterns that work across document types
            "title": r'.{3,100}',           # 3-100 characters
            "description": r'.{10,500}',     # 10-500 characters
            "url": r'https?://[^\s]+',       # Basic URL pattern
            "email": r'[^@]+@[^@]+\.[^@]+',  # Basic email pattern
            "phone": r'[\d\s\-\(\)]{10,20}', # Phone number pattern
            "date": r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Date pattern
        }
    
    def customize_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Provide default strategy customizations.
        
        Args:
            strategy_name (str): Name of processing strategy
            
        Returns:
            Dict[str, Any]: Strategy customization options
        """
        customizations = {
            "products/semantic-boundary": {
                "preserve_product_integrity": True,
                "allow_incomplete_products": False,
            },
            "manual/section-based": {
                "preserve_section_hierarchy": True,
                "include_section_numbers": True,
            },
            "faq/qa-pairs": {
                "require_question_answer_pairs": True,
                "allow_standalone_questions": False,
            },
            "article/sentence-based": {
                "preserve_paragraph_structure": True,
                "break_on_sentence_boundaries": True,
            },
            "legal/paragraph-based": {
                "preserve_legal_structure": True,
                "maintain_article_numbering": True,
            },
            "code/function-based": {
                "preserve_function_definitions": True,
                "include_docstrings": True,
            },
        }
        
        return customizations.get(strategy_name, {})