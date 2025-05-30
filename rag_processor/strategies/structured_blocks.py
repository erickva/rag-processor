"""
Structured blocks processing strategies.

Implements mechanical separation over semantic understanding using various
block separator patterns like empty lines, headings, and numbered lists.
"""

import re
from typing import List, Dict, Any, Optional
from abc import abstractmethod

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import DEFAULT_CHUNK_OVERLAP


class StructuredBlocksStrategy(ProcessingStrategy):
    """
    Base class for structured block processing strategies.
    
    Implements mechanical separation using various block separators
    instead of semantic pattern matching. Each subclass defines
    how to detect block boundaries.
    """
    
    @property
    @abstractmethod
    def separator_type(self) -> str:
        """Type of separator used (e.g., 'empty-line', 'heading', 'numbered')."""
        pass
    
    @property
    @abstractmethod
    def separator_pattern(self) -> str:
        """Regex pattern to detect block separators."""
        pass
    
    @property
    def name(self) -> str:
        """Strategy name in format 'structured-blocks/separator-type'."""
        return f"structured-blocks/{self.separator_type}"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return f"Structured block chunking using {self.separator_type} separators"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default pattern is the separator pattern."""
        return self.separator_pattern
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return 0  # No overlap for block separation
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process content into blocks using mechanical separation.
        
        Args:
            content (str): Raw document text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of block chunks with metadata
        """
        blocks = self._split_into_blocks(content, directive)
        
        if not blocks:
            # Fallback to size-based chunking if no blocks found
            chunker = TextChunker()
            return chunker.chunk_by_size(content, 1000, self.get_overlap(directive))
        
        chunks = []
        current_pos = 0
        
        for i, block in enumerate(blocks):
            block_text = block.strip()
            
            # Skip empty blocks
            if not block_text:
                current_pos += len(block) + len(self._get_separator_text())
                continue
            
            # Apply size limits if specified in directive
            max_lines = self._get_max_lines_per_block(directive)
            min_fields = self._get_min_fields_per_block(directive)
            
            # Validate block according to limits
            if not self._validate_block(block_text, max_lines, min_fields):
                current_pos += len(block) + len(self._get_separator_text())
                continue
            
            # Find actual position in original content
            start_pos = content.find(block_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(block_text)
            
            # Extract block metadata
            block_metadata = self._extract_block_metadata(block_text, i)
            
            # Create chunk with rich metadata
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "block_index": i,
                "separator_type": self.separator_type,
                "chunking_method": "mechanical-separation",
                "line_count": len(block_text.splitlines()),
                "field_count": block_metadata.get("field_count", 0),
                "fields": block_metadata.get("fields", []),
            }
            
            chunk = ChunkMetadata(
                text=block_text,
                metadata=chunk_metadata,
                start_position=start_pos,
                end_position=end_pos
            )
            
            chunks.append(chunk)
            current_pos = end_pos + len(self._get_separator_text())
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for structured block strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        blocks = self._split_into_blocks(content, directive)
        
        if not blocks:
            issues.append(f"No {self.separator_type} separators found in content")
        elif len(blocks) < 2:
            issues.append(f"Very few blocks detected ({len(blocks)}) - consider different strategy")
        
        # Check block quality
        empty_blocks = sum(1 for block in blocks if not block.strip())
        if empty_blocks > len(blocks) * 0.3:  # More than 30% empty blocks
            issues.append("Too many empty blocks - content may not be well-structured")
        
        # Check for minimum content in blocks
        min_content_blocks = sum(1 for block in blocks if len(block.strip()) >= 20)
        if min_content_blocks < len(blocks) * 0.7:  # Less than 70% have meaningful content
            issues.append("Many blocks have insufficient content")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for structured blocks.
        
        Args:
            client_config (ClientConfig): Client configuration for customization
            
        Returns:
            str: Complete .rag template content
        """
        # Get client-specific metadata
        client_metadata = client_config.get_template_metadata()
        
        # Build template header
        template_parts = [
            "#!/usr/bin/env rag-processor",
            f"#!strategy: {self.name}",
            f"#!validation: {client_config.name}/structured-blocks",
        ]
        
        # Add strategy-specific directives
        template_parts.extend(self._get_template_directives())
        
        # Add metadata
        metadata = {
            "business": client_config.name,
            "type": "structured-blocks",
            "separator": self.separator_type,
            "version": "1.0",
        }
        metadata.update(client_metadata)
        
        import json
        template_parts.append(f"#!metadata: {json.dumps(metadata, separators=(',', ':'))}")
        
        # Add example content
        template_parts.extend([
            "",
            f"# Structured Blocks Template ({self.separator_type})",
            "",
        ])
        
        # Add separator-specific examples
        template_parts.extend(self._get_template_examples())
        
        return '\n'.join(template_parts)
    
    def _split_into_blocks(self, content: str, directive: ProcessingDirective) -> List[str]:
        """Split content into blocks using the separator pattern."""
        pattern = self.get_chunk_pattern(directive)
        
        # Use the separator pattern to split content
        if self.separator_type == "empty-line":
            # Split by double newlines (empty lines)
            blocks = re.split(r'\n\s*\n', content)
        else:
            # For other separators, split by the pattern
            blocks = re.split(pattern, content, flags=re.MULTILINE)
        
        return [block for block in blocks if block.strip()]
    
    def _validate_block(self, block_text: str, max_lines: Optional[int], min_fields: Optional[int]) -> bool:
        """Validate a block against size and content requirements."""
        lines = block_text.splitlines()
        
        # Check line count limit
        if max_lines and len(lines) > max_lines:
            return False
        
        # Check minimum fields requirement
        if min_fields:
            field_pattern = r'^([a-zA-Z][a-zA-Z\s]*?):\s*([^\n]*)'
            field_matches = re.findall(field_pattern, block_text, re.MULTILINE)
            if len(field_matches) < min_fields:
                return False
        
        return True
    
    def _extract_block_metadata(self, block_text: str, block_index: int) -> Dict[str, Any]:
        """Extract metadata from a block."""
        metadata = {
            "block_index": block_index,
            "fields": [],
            "field_count": 0,
        }
        
        # Extract field: value patterns
        field_pattern = r'^([a-zA-Z][a-zA-Z\s]*?):\s*([^\n]*)'
        field_matches = re.findall(field_pattern, block_text, re.MULTILINE)
        
        if field_matches:
            metadata["fields"] = [field[0].strip() for field in field_matches]
            metadata["field_count"] = len(field_matches)
        
        return metadata
    
    def _get_max_lines_per_block(self, directive: ProcessingDirective) -> Optional[int]:
        """Get max lines per block (simplified - no limits)."""
        return None  # No limits in simplified format
    
    def _get_min_fields_per_block(self, directive: ProcessingDirective) -> Optional[int]:
        """Get min fields per block (simplified - no requirements)."""
        return None  # No requirements in simplified format
    
    def _get_separator_text(self) -> str:
        """Get the actual separator text (for position calculations)."""
        if self.separator_type == "empty-line":
            return "\n\n"
        return "\n"
    
    @abstractmethod
    def _get_template_directives(self) -> List[str]:
        """Get strategy-specific template directives."""
        pass
    
    @abstractmethod  
    def _get_template_examples(self) -> List[str]:
        """Get strategy-specific template examples."""
        pass


class EmptyLineSeparatedStrategy(StructuredBlocksStrategy):
    """
    Empty line separated blocks strategy.
    
    Splits content into blocks using empty lines as separators.
    Universal and foolproof - works with any structured data.
    """
    
    @property
    def separator_type(self) -> str:
        """Type of separator used."""
        return "empty-line-separated"
    
    @property
    def separator_pattern(self) -> str:
        """Regex pattern to detect empty line separators."""
        return r'\n\s*\n'
    
    def _get_template_directives(self) -> List[str]:
        """Get empty-line specific template directives."""
        return []  # No additional directives in simplified format
    
    def _get_template_examples(self) -> List[str]:
        """Get empty-line specific template examples."""
        return [
            "Name: Example Item 1",
            "Description: First example item with details",
            "Category: Example Category",
            "",
            "Name: Example Item 2", 
            "Description: Second example item with different details",
            "Category: Example Category",
            "",
            "Name: Example Item 3",
            "Description: Third example item to show the pattern",
            "Category: Another Category",
            "",
            "# Add your structured data following the same pattern above.",
            "# Each block should be separated by an empty line.",
            "# Field: Value format is recommended but not required.",
        ]


class HeadingSeparatedStrategy(StructuredBlocksStrategy):
    """
    Heading separated blocks strategy.
    
    Splits content into blocks using markdown-style headings as separators.
    Perfect for documentation and hierarchical content.
    """
    
    @property
    def separator_type(self) -> str:
        """Type of separator used."""
        return "heading-separated"
    
    @property
    def separator_pattern(self) -> str:
        """Regex pattern to detect heading separators."""
        return r'^#{1,6}\s+.+$'
    
    def _split_into_blocks(self, content: str, directive: ProcessingDirective) -> List[str]:
        """Split content by headings, keeping heading with content."""
        pattern = self.get_chunk_pattern(directive)
        
        # Find all heading positions
        heading_matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if not heading_matches:
            return [content]  # No headings found, return whole content
        
        blocks = []
        
        for i, match in enumerate(heading_matches):
            start_pos = match.start()
            
            # Find end position (start of next heading or end of content)
            if i < len(heading_matches) - 1:
                end_pos = heading_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            block = content[start_pos:end_pos].strip()
            if block:
                blocks.append(block)
        
        return blocks
    
    def _get_template_directives(self) -> List[str]:
        """Get heading-specific template directives."""
        return []  # No additional directives in simplified format
    
    def _get_template_examples(self) -> List[str]:
        """Get heading-specific template examples."""
        return [
            "# Main Section 1",
            "",
            "Content for the first main section goes here.",
            "This can include multiple paragraphs and details.",
            "",
            "## Subsection 1.1",
            "",
            "More detailed content for this subsection.",
            "Each heading will create a separate chunk.",
            "",
            "# Main Section 2",
            "",
            "Content for the second main section.",
            "The heading level determines the hierarchy.",
            "",
            "### Subsection 2.1.1",
            "",
            "Even deeper nested content can be handled.",
            "",
            "# Add your content following the same heading structure above.",
            "# Each heading (# ## ### etc.) will start a new chunk.",
        ]


class NumberedSeparatedStrategy(StructuredBlocksStrategy):
    """
    Numbered list separated blocks strategy.
    
    Splits content into blocks using numbered lists as separators.
    Perfect for step-by-step instructions and ordered content.
    """
    
    @property
    def separator_type(self) -> str:
        """Type of separator used."""
        return "numbered-separated"
    
    @property
    def separator_pattern(self) -> str:
        """Regex pattern to detect numbered list separators."""
        return r'^\d+\.\s+'
    
    def _split_into_blocks(self, content: str, directive: ProcessingDirective) -> List[str]:
        """Split content by numbered items, keeping number with content."""
        pattern = self.get_chunk_pattern(directive)
        
        # Find all numbered item positions
        number_matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if not number_matches:
            return [content]  # No numbered items found, return whole content
        
        blocks = []
        
        for i, match in enumerate(number_matches):
            start_pos = match.start()
            
            # Find end position (start of next number or end of content)
            if i < len(number_matches) - 1:
                end_pos = number_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            block = content[start_pos:end_pos].strip()
            if block:
                blocks.append(block)
        
        return blocks
    
    def _get_template_directives(self) -> List[str]:
        """Get numbered-specific template directives."""
        return []  # No additional directives in simplified format
    
    def _get_template_examples(self) -> List[str]:
        """Get numbered-specific template examples."""
        return [
            "1. First step or item in the sequence",
            "   This can include multiple lines of explanation",
            "   and detailed instructions for this step.",
            "",
            "2. Second step follows the same pattern",
            "   Each numbered item will become a separate chunk.",
            "   You can include code, examples, or any content.",
            "",
            "3. Third step continues the sequence",
            "   The numbering helps maintain logical order",
            "   while ensuring each step is properly chunked.",
            "",
            "4. Additional steps can be added as needed",
            "   Perfect for tutorials, procedures, or any",
            "   step-by-step content that needs to be processed.",
            "",
            "# Add your numbered content following the same pattern above.",
            "# Each number (1. 2. 3. etc.) will start a new chunk.",
        ]