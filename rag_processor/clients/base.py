"""
Base client configuration interface.

Defines the common interface for client-specific configurations
and validation rules.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ClientConfig(ABC):
    """
    Abstract base class for client-specific configurations.
    
    Each client can define custom validation rules, field requirements,
    and processing preferences.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Client configuration name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of client configuration."""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get client-specific validation rules.
        
        Returns:
            Dict[str, Any]: Validation configuration
        """
        pass
    
    @abstractmethod
    def get_required_fields(self, document_type: str) -> List[str]:
        """
        Get required fields for a document type.
        
        Args:
            document_type (str): Type of document being processed
            
        Returns:
            List[str]: List of required field patterns
        """
        pass
    
    @abstractmethod
    def get_field_patterns(self) -> Dict[str, str]:
        """
        Get regex patterns for field validation.
        
        Returns:
            Dict[str, str]: Field name to regex pattern mapping
        """
        pass
    
    def validate_field_format(self, field_name: str, value: str) -> bool:
        """
        Validate field value against client patterns.
        
        Args:
            field_name (str): Name of field to validate
            value (str): Field value to check
            
        Returns:
            bool: True if value matches expected format
        """
        patterns = self.get_field_patterns()
        if field_name not in patterns:
            return True  # No pattern defined, assume valid
        
        import re
        pattern = patterns[field_name]
        return bool(re.search(pattern, value, re.IGNORECASE))
    
    def get_template_metadata(self) -> Dict[str, Any]:
        """
        Get metadata to include in generated templates.
        
        Returns:
            Dict[str, Any]: Template metadata
        """
        return {
            "client": self.name,
            "description": self.description,
        }
    
    def customize_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Provide client-specific strategy customizations.
        
        Args:
            strategy_name (str): Name of processing strategy
            
        Returns:
            Dict[str, Any]: Strategy customization options
        """
        return {}  # Default: no customizations