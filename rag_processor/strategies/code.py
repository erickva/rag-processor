"""
Code processing strategy.

Specialized for code documentation with function/class-based chunking
that preserves code structure and documentation relationships.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import CODE_CHUNK_OVERLAP


class CodeStrategy(ProcessingStrategy):
    """
    Code documentation processing strategy.
    
    Chunks at function/class boundaries while preserving code structure,
    documentation blocks, and maintaining API relationships.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "code/function-based"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "Code documentation chunking at function/class boundaries with structure preservation"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for code boundaries."""
        return r'(def\s+\w+\(|function\s+\w+\(|class\s+\w+|##\s+[A-Z])'
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return CODE_CHUNK_OVERLAP
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process code documentation into function/class-based chunks.
        
        Args:
            content (str): Raw code documentation text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of code chunks with metadata
        """
        chunker = TextChunker()
        overlap = self.get_overlap(directive)
        
        # Use specialized code documentation chunking
        chunks = self._chunk_by_code_structure(content, overlap, client_config)
        
        if not chunks:
            # Fallback to pattern-based chunking
            pattern = self.get_chunk_pattern(directive)
            return chunker.chunk_by_pattern(content, pattern, overlap)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for code strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for code documentation indicators
        code_indicators = [
            r'def\s+\w+\(',
            r'function\s+\w+\(',
            r'class\s+\w+',
            r'API|api',
            r'```[\w]*\n',
            r'@param|@return',
            r'import\s+\w+',
            r'##\s+[A-Z]',
            r'""".*?"""',
            r'/\*\*.*?\*/',
            r'//.*',
        ]
        
        indicator_matches = 0
        for pattern in code_indicators:
            matches = len(re.findall(pattern, content, re.IGNORECASE | re.DOTALL))
            indicator_matches += matches
        
        if indicator_matches < 3:
            issues.append("Content doesn't appear to be code documentation format")
        
        # Check for function/class definitions
        function_count = len(re.findall(r'def\s+\w+\(|function\s+\w+\(', content))
        class_count = len(re.findall(r'class\s+\w+', content))
        
        if function_count == 0 and class_count == 0:
            issues.append("No function or class definitions detected")
        
        # Check for code blocks
        code_block_count = len(re.findall(r'```', content))
        if code_block_count < 2:
            issues.append("Very few code blocks detected - may not be code documentation")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for code documentation.
        
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
            "#!strategy: code/function-based",
            f"#!validation: {client_config.name}/code-documentation",
            "#!chunk-pattern: (def\\s+\\w+\\(|function\\s+\\w+\\(|class\\s+\\w+|##\\s+[A-Z])",
        ]
        
        # Add metadata
        metadata = {
            "type": "code-documentation",
            "version": "1.0",
            "structure": "functional",
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
            "# Code Documentation Template",
            "",
            "## Overview",
            "",
            "This document provides comprehensive documentation for the API functions and classes.",
            "",
            "## Authentication",
            "",
            "All API calls require authentication using the following method:",
            "",
            "```python",
            "import requests",
            "",
            "headers = {",
            '    "Authorization": "Bearer YOUR_API_KEY"',
            "}",
            "```",
            "",
            "## Core Functions",
            "",
            "### def create_user(name, email)",
            "",
            "Creates a new user in the system.",
            "",
            "**Parameters:**",
            "- `name` (str): The user's full name",
            "- `email` (str): The user's email address",
            "",
            "**Returns:**",
            "- `dict`: User object with id, name, and email",
            "",
            "**Example:**",
            "```python",
            'user = create_user("John Doe", "john@example.com")',
            "print(user['id'])  # Output: 12345",
            "```",
            "",
            "### def get_user(user_id)",
            "",
            "Retrieves a user by their ID.",
            "",
            "**Parameters:**",
            "- `user_id` (int): The unique identifier for the user",
            "",
            "**Returns:**",
            "- `dict`: User object if found, None otherwise",
            "",
            "**Example:**",
            "```python",
            "user = get_user(12345)",
            "if user:",
            '    print(f"User name: {user[\'name\']}")',
            "```",
            "",
            "## Data Classes",
            "",
            "### class UserManager",
            "",
            "Manages user-related operations and data persistence.",
            "",
            "**Attributes:**",
            "- `database_url` (str): Connection string for the database",
            "- `cache_enabled` (bool): Whether caching is enabled",
            "",
            "**Methods:**",
            "- `connect()`: Establishes database connection",
            "- `disconnect()`: Closes database connection",
            "- `create_user(data)`: Creates a new user record",
            "",
            "# Continue adding functions, classes, and API endpoints following the same structure.",
        ])
        
        return '\n'.join(template_parts)
    
    def _chunk_by_code_structure(self, content: str, overlap: int, client_config: ClientConfig) -> List[ChunkMetadata]:
        """
        Chunk code documentation by function/class structure.
        
        Args:
            content (str): Code documentation content
            overlap (int): Character overlap between chunks
            client_config (ClientConfig): Client configuration
            
        Returns:
            List[ChunkMetadata]: List of code structure chunks
        """
        chunks = []
        
        # Extract code sections (functions, classes, API endpoints)
        code_sections = self._extract_code_sections(content)
        
        if code_sections:
            chunks = self._process_code_sections(code_sections, overlap)
        else:
            # Fallback to header-based processing
            chunks = self._process_by_headers(content, overlap)
        
        return chunks
    
    def _extract_code_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract code sections (functions, classes, etc.) from content."""
        sections = []
        
        # Patterns for different code elements
        code_patterns = [
            (r'###?\s+(def\s+\w+\([^)]*\))', 'function', r'def\s+(\w+)\('),
            (r'###?\s+(function\s+\w+\([^)]*\))', 'function', r'function\s+(\w+)\('),
            (r'###?\s+(class\s+\w+)', 'class', r'class\s+(\w+)'),
            (r'##\s+([A-Z][A-Za-z\s]+)', 'section', None),
            (r'###\s+([A-Z][A-Za-z\s]+)', 'subsection', None),
        ]
        
        for pattern, section_type, name_pattern in code_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            
            for i, match in enumerate(matches):
                section_start = match.start()
                
                # Find section end (next section or end of document)
                next_match_start = len(content)
                for other_pattern, _, _ in code_patterns:
                    other_matches = list(re.finditer(other_pattern, content[section_start + 1:], re.MULTILINE))
                    if other_matches:
                        candidate_end = section_start + 1 + other_matches[0].start()
                        if candidate_end < next_match_start:
                            next_match_start = candidate_end
                
                section_text = content[section_start:next_match_start].strip()
                
                if len(section_text) > 50:  # Only include substantial sections
                    # Extract name
                    name = match.group(1)
                    if name_pattern:
                        name_match = re.search(name_pattern, name)
                        if name_match:
                            name = name_match.group(1)
                    
                    sections.append({
                        "text": section_text,
                        "name": name,
                        "type": section_type,
                        "start_pos": section_start,
                        "end_pos": next_match_start,
                        "language": self._detect_language(section_text),
                    })
        
        # Sort by position to maintain order
        sections.sort(key=lambda x: x["start_pos"])
        
        return sections
    
    def _process_code_sections(self, sections: List[Dict], overlap: int) -> List[ChunkMetadata]:
        """Process code sections into chunks."""
        chunks = []
        
        for section in sections:
            section_text = section["text"]
            
            # For large sections, consider splitting
            if len(section_text) > 2500:
                sub_chunks = self._split_large_code_section(section, overlap)
                chunks.extend(sub_chunks)
            else:
                # Create single chunk for section
                code_metadata = self._analyze_code_content(section_text, section)
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "code_element_name": section["name"],
                    "code_element_type": section["type"],
                    "programming_language": section["language"],
                    "chunking_method": "code-structure",
                    **code_metadata
                }
                
                chunk = ChunkMetadata(
                    text=section_text,
                    metadata=chunk_metadata,
                    start_position=section["start_pos"],
                    end_position=section["end_pos"]
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _process_by_headers(self, content: str, overlap: int) -> List[ChunkMetadata]:
        """Process content by headers when no code structure is found."""
        chunks = []
        
        # Use markdown-style headers
        header_pattern = r'^#{1,6}\s+(.+)$'
        header_matches = list(re.finditer(header_pattern, content, re.MULTILINE))
        
        if not header_matches:
            # Final fallback to size-based chunking
            chunker = TextChunker()
            return chunker.chunk_by_size(content, 1500, overlap)
        
        for i, match in enumerate(header_matches):
            section_start = match.start()
            
            if i < len(header_matches) - 1:
                section_end = header_matches[i + 1].start()
            else:
                section_end = len(content)
            
            section_text = content[section_start:section_end].strip()
            
            if len(section_text) > 100:
                header_level = len(match.group().split()[0])  # Count # characters
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "section_title": match.group(1).strip(),
                    "header_level": header_level,
                    "chunking_method": "header-based",
                    **self._analyze_code_content(section_text)
                }
                
                chunk = ChunkMetadata(
                    text=section_text,
                    metadata=chunk_metadata,
                    start_position=section_start,
                    end_position=section_end
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _split_large_code_section(self, section: Dict, overlap: int) -> List[ChunkMetadata]:
        """Split large code sections into smaller chunks."""
        text = section["text"]
        chunks = []
        
        # Try to split by subsections or paragraphs
        split_pattern = r'\n\s*\n'
        parts = re.split(split_pattern, text)
        
        current_chunk = []
        current_size = 0
        target_size = 1500
        
        for part in parts:
            part_size = len(part)
            
            if current_size + part_size > target_size and current_chunk:
                # Create chunk
                chunk_text = '\n\n'.join(current_chunk)
                
                code_metadata = self._analyze_code_content(chunk_text, section)
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "code_element_name": section["name"],
                    "code_element_type": section["type"],
                    "section_part": f"Part {len(chunks) + 1}",
                    "programming_language": section["language"],
                    "chunking_method": "code-section-split",
                    **code_metadata
                }
                
                chunk = ChunkMetadata(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    start_position=section["start_pos"],
                    end_position=section["start_pos"] + len(chunk_text)
                )
                
                chunks.append(chunk)
                current_chunk = []
                current_size = 0
            
            current_chunk.append(part)
            current_size += part_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            
            code_metadata = self._analyze_code_content(chunk_text, section)
            
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "code_element_name": section["name"],
                "code_element_type": section["type"],
                "section_part": f"Part {len(chunks) + 1}",
                "programming_language": section["language"],
                "chunking_method": "code-section-split",
                **code_metadata
            }
            
            chunk = ChunkMetadata(
                text=chunk_text,
                metadata=chunk_metadata,
                start_position=section["start_pos"],
                end_position=section["end_pos"]
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _detect_language(self, text: str) -> str:
        """Detect programming language from code content."""
        language_indicators = {
            'python': [r'def\s+\w+\(', r'import\s+\w+', r'from\s+\w+\s+import', r'""".*?"""'],
            'javascript': [r'function\s+\w+\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'=>'],
            'java': [r'public\s+class', r'private\s+\w+', r'public\s+static', r'@Override'],
            'c': [r'#include\s*<', r'int\s+main\(', r'printf\(', r'malloc\('],
            'cpp': [r'#include\s*<', r'std::', r'class\s+\w+', r'namespace\s+\w+'],
            'go': [r'func\s+\w+\(', r'package\s+\w+', r'import\s*\(', r'type\s+\w+\s+struct'],
            'rust': [r'fn\s+\w+\(', r'use\s+\w+', r'struct\s+\w+', r'impl\s+\w+'],
        }
        
        text_lower = text.lower()
        
        for language, patterns in language_indicators.items():
            score = sum(len(re.findall(pattern, text_lower)) for pattern in patterns)
            if score > 0:
                return language
        
        # Check for code blocks with language hints
        code_block_match = re.search(r'```(\w+)', text)
        if code_block_match:
            return code_block_match.group(1).lower()
        
        return "unknown"
    
    def _analyze_code_content(self, text: str, section: Dict = None) -> Dict[str, Any]:
        """Analyze code content for metadata."""
        analysis = {}
        
        # Count code blocks
        analysis["code_block_count"] = len(re.findall(r'```', text))
        
        # Detect documentation elements
        analysis["has_parameters"] = bool(re.search(r'@param|Parameters?:', text, re.IGNORECASE))
        analysis["has_returns"] = bool(re.search(r'@return|Returns?:', text, re.IGNORECASE))
        analysis["has_examples"] = bool(re.search(r'Example:|```', text, re.IGNORECASE))
        analysis["has_links"] = bool(re.search(r'https?://|www\.', text))
        
        # Count function/method definitions
        analysis["function_count"] = len(re.findall(r'def\s+\w+\(|function\s+\w+\(', text))
        analysis["class_count"] = len(re.findall(r'class\s+\w+', text))
        
        # Detect API-related content
        analysis["is_api_doc"] = bool(re.search(r'API|endpoint|request|response', text, re.IGNORECASE))
        analysis["has_http_methods"] = bool(re.search(r'GET|POST|PUT|DELETE|PATCH', text))
        
        # Complexity indicators
        if section and section.get("type") == "function":
            # Count parameters for functions
            param_match = re.search(r'\(([^)]*)\)', section.get("name", ""))
            if param_match:
                params = [p.strip() for p in param_match.group(1).split(',') if p.strip()]
                analysis["parameter_count"] = len(params)
                analysis["complexity"] = "high" if len(params) > 5 else "medium" if len(params) > 2 else "low"
        
        return analysis