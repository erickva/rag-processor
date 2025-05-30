"""
Processing Directive Parser.

Parses .rag file headers to extract processing instructions and metadata.
"""

import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config.constants import ERROR_INVALID_DIRECTIVE


@dataclass
class ProcessingDirective:
    """Parsed processing directive from .rag file header."""
    
    strategy: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize empty dict if None."""
        if self.metadata is None:
            self.metadata = {}


class DirectiveParser:
    """
    Parses processing directives from .rag file headers.
    
    Handles shebang-style directive parsing and JSON metadata extraction.
    """
    
    def __init__(self):
        """Initialize parser with core directive patterns."""
        self.directive_patterns = {
            'strategy': r'@strategy:\s*(.+)',
            'source_url': r'@source-url:\s*(.+)',
            'metadata': r'@metadata:\s*(.+)',
        }
    
    def parse(self, content: str) -> ProcessingDirective:
        """
        Parse processing directives from document content.
        
        Args:
            content (str): Full .rag document content
            
        Returns:
            ProcessingDirective: Parsed directive configuration
            
        Raises:
            ValueError: If JSON metadata is malformed
        """
        lines = content.split('\n')
        directive = ProcessingDirective()
        
        for line in lines:
            line = line.strip()
            
            # Skip shebang line
            if line.startswith('#!/'):
                continue
                
            # Stop at first non-directive line
            if not line.startswith('@'):
                break
            
            # Parse each directive type
            for directive_type, pattern in self.directive_patterns.items():
                match = re.match(pattern, line)
                if match:
                    value = match.group(1).strip()
                    
                    # Handle JSON metadata field
                    if directive_type == 'metadata':
                        try:
                            parsed_value = json.loads(value)
                            setattr(directive, directive_type, parsed_value)
                        except json.JSONDecodeError as e:
                            raise ValueError(
                                f"{ERROR_INVALID_DIRECTIVE}: Invalid JSON in {directive_type}: {e}"
                            )
                    else:
                        setattr(directive, directive_type, value)
                    break
        
        return directive
    
    def extract_content(self, content: str) -> str:
        """
        Extract document content without directive headers.
        
        Args:
            content (str): Full .rag document content
            
        Returns:
            str: Document content without directive headers
        """
        lines = content.split('\n')
        content_lines = []
        in_content = False
        
        for line in lines:
            # Skip shebang and directive lines
            if line.startswith('#!/') or line.startswith('@'):
                continue
            
            # Start collecting content after directives
            in_content = True
            content_lines.append(line)
        
        return '\n'.join(content_lines).strip()
    
    def create_directive_header(self, directive: ProcessingDirective) -> str:
        """
        Create directive header string from ProcessingDirective object.
        
        Args:
            directive (ProcessingDirective): Directive configuration
            
        Returns:
            str: Complete directive header for .rag file
        """
        lines = ['#!/usr/bin/env rag-processor']
        
        if directive.strategy:
            lines.append(f'@strategy: {directive.strategy}')
        
        if directive.source_url:
            lines.append(f'@source-url: {directive.source_url}')
        
        if directive.metadata:
            metadata_json = json.dumps(directive.metadata, separators=(',', ':'))
            lines.append(f'@metadata: {metadata_json}')
        
        return '\n'.join(lines) + '\n\n'
    
    def validate_directive(self, directive: ProcessingDirective) -> List[str]:
        """
        Validate processing directive for common issues.
        
        Args:
            directive (ProcessingDirective): Directive to validate
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate strategy format
        if directive.strategy:
            if '/' not in directive.strategy:
                issues.append("Strategy must be in format 'category/method'")
        
        # Validate source URL format
        if directive.source_url:
            if not (directive.source_url.startswith('http://') or directive.source_url.startswith('https://')):
                issues.append("Source URL must be a valid HTTP/HTTPS URL")
        
        # Validate metadata structure
        if directive.metadata:
            if not isinstance(directive.metadata, dict):
                issues.append("Metadata must be a JSON object")
        
        return issues