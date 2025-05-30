"""
Manual processing strategy.

Specialized for user manuals and documentation with section-based chunking
that preserves hierarchical structure and context.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import MANUAL_CHUNK_OVERLAP


class ManualStrategy(ProcessingStrategy):
    """
    User manual processing strategy.
    
    Chunks at section boundaries while preserving hierarchical structure
    and maintaining context between related sections.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "manual/section-based"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "User manual chunking at section boundaries with hierarchy preservation"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for section boundaries."""
        return r'^#{1,6}\s+(.+)$'  # Markdown headers (# to ######)
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return MANUAL_CHUNK_OVERLAP
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process manual content into section-based chunks.
        
        Args:
            content (str): Raw manual text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of section chunks with metadata
        """
        chunker = TextChunker()
        pattern = self.get_chunk_pattern(directive)
        overlap = self.get_overlap(directive)
        
        # Find all section headers
        header_matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if not header_matches:
            # Try alternative patterns for different header styles
            alternative_patterns = [
                r'^\d+\.\s+(.+)$',           # Numbered sections (1. Introduction)
                r'^[A-Z][A-Z\s]{3,30}$',     # ALL CAPS headers
                r'Chapter\s+\d+[:\s]+(.+)',   # Chapter headers
                r'Section\s+\d+[:\s]+(.+)',   # Section headers
            ]
            
            for alt_pattern in alternative_patterns:
                header_matches = list(re.finditer(alt_pattern, content, re.MULTILINE))
                if header_matches:
                    pattern = alt_pattern
                    break
        
        if not header_matches:
            # No section patterns found - use fallback chunking
            return chunker.chunk_by_size(content, 1500, overlap)
        
        chunks = []
        
        for i, match in enumerate(header_matches):
            # Determine section boundaries
            start_pos = match.start()
            
            if i < len(header_matches) - 1:
                end_pos = header_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract section text
            section_text = content[start_pos:end_pos].strip()
            
            # Skip very short sections
            if len(section_text) < 100:
                continue
            
            # Analyze section structure
            section_metadata = self._analyze_section(section_text, match, content)
            
            # Add overlap from previous section if needed
            if overlap > 0 and i > 0:
                overlap_start = max(0, start_pos - overlap)
                overlap_text = content[overlap_start:start_pos]
                section_text = overlap_text + section_text
                start_pos = overlap_start
            
            # Create chunk with section metadata
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "section_title": section_metadata.get("title", "Unknown Section"),
                "section_level": section_metadata.get("level", 1),
                "section_number": section_metadata.get("number"),
                "parent_section": section_metadata.get("parent"),
                "subsection_count": section_metadata.get("subsection_count", 0),
                "has_code_examples": section_metadata.get("has_code", False),
                "has_lists": section_metadata.get("has_lists", False),
                "chunking_method": "section-based",
                "boundary_pattern": match.group(),
            }
            
            chunk = ChunkMetadata(
                text=section_text,
                metadata=chunk_metadata,
                start_position=start_pos,
                end_position=end_pos
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for manual strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        pattern = self.get_chunk_pattern(directive)
        header_matches = re.findall(pattern, content, re.MULTILINE)
        
        if not header_matches:
            issues.append("No section headers found using pattern")
        elif len(header_matches) < 3:
            issues.append("Very few sections detected - consider different strategy")
        
        # Check for proper hierarchical structure
        lines = content.split('\n')
        header_lines = [line for line in lines if re.match(pattern, line)]
        
        if len(header_lines) < len(header_matches) * 0.8:
            issues.append("Inconsistent header formatting detected")
        
        # Look for manual-specific indicators
        manual_indicators = ["step", "instruction", "procedure", "how to", "tutorial"]
        indicator_count = sum(len(re.findall(indicator, content, re.IGNORECASE)) for indicator in manual_indicators)
        
        if indicator_count == 0:
            issues.append("Content doesn't appear to be instructional/manual format")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for user manuals.
        
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
            "#!strategy: manual/section-based",
            f"#!validation: {client_config.name}/user-manual",
            "#!chunk-pattern: ^#{1,6}\\s+(.+)$",
        ]
        
        # Add metadata
        metadata = {
            "type": "user-manual",
            "version": "1.0",
            "structure": "hierarchical",
        }
        metadata.update(client_metadata)
        
        import json
        template_parts.append(f"#!metadata: {json.dumps(metadata, separators=(',', ':'))}")
        
        # Add custom rules
        custom_rules = client_config.customize_strategy_config(self.name)
        if custom_rules:
            template_parts.append(f"#!custom-rules: {json.dumps(custom_rules, separators=(',', ':'))}")
        
        # Add example content
        template_parts.extend([
            "",
            "# User Manual Template",
            "",
            "## 1. Introduction",
            "",
            "Welcome to the user manual. This section provides an overview of the system.",
            "",
            "### 1.1 Getting Started",
            "",
            "Follow these initial setup steps:",
            "",
            "1. First step description",
            "2. Second step description", 
            "3. Third step description",
            "",
            "## 2. Basic Operations",
            "",
            "This section covers the fundamental operations you can perform.",
            "",
            "### 2.1 Creating New Items",
            "",
            "To create a new item, follow these instructions...",
            "",
            "### 2.2 Editing Existing Items",
            "",
            "To modify an existing item...",
            "",
            "## 3. Advanced Features",
            "",
            "Advanced functionality for experienced users.",
            "",
            "# Continue adding sections following the same hierarchical structure.",
        ])
        
        return '\n'.join(template_parts)
    
    def _analyze_section(self, section_text: str, header_match: re.Match, full_content: str) -> Dict[str, Any]:
        """
        Analyze section structure and content.
        
        Args:
            section_text (str): Section text content
            header_match (re.Match): Regex match for section header
            full_content (str): Full document content for context
            
        Returns:
            Dict[str, Any]: Section analysis metadata
        """
        metadata = {}
        
        # Extract section title
        if len(header_match.groups()) > 0:
            metadata["title"] = header_match.group(1).strip()
        else:
            metadata["title"] = header_match.group().strip()
        
        # Determine section level from header pattern
        header_text = header_match.group()
        if header_text.startswith('#'):
            metadata["level"] = len(header_text) - len(header_text.lstrip('#'))
        elif re.match(r'^\d+\.', header_text):
            # Count dots for numbering depth (1.2.3 = level 3)
            metadata["level"] = header_text.count('.') + 1
        else:
            metadata["level"] = 1
        
        # Extract section number if present
        number_match = re.search(r'^(\d+(?:\.\d+)*)', metadata["title"])
        if number_match:
            metadata["number"] = number_match.group(1)
        
        # Count subsections within this section
        subsection_pattern = r'^#{' + str(metadata["level"] + 1) + r',6}\s+'
        subsection_count = len(re.findall(subsection_pattern, section_text, re.MULTILINE))
        metadata["subsection_count"] = subsection_count
        
        # Detect content types
        metadata["has_code"] = bool(re.search(r'```|`[^`]+`', section_text))
        metadata["has_lists"] = bool(re.search(r'^\s*[\-\*\+]\s+|^\s*\d+\.\s+', section_text, re.MULTILINE))
        metadata["has_tables"] = bool(re.search(r'\|.*\|', section_text))
        metadata["has_images"] = bool(re.search(r'!\[.*\]|<img\s+', section_text))
        
        # Find parent section if this is a subsection
        if metadata["level"] > 1:
            # Look backwards in content for parent header
            before_section = full_content[:header_match.start()]
            parent_pattern = r'^#{' + str(metadata["level"] - 1) + r'}\s+(.+)$'
            parent_matches = list(re.finditer(parent_pattern, before_section, re.MULTILINE))
            if parent_matches:
                last_parent = parent_matches[-1]
                metadata["parent"] = last_parent.group(1).strip()
        
        return metadata