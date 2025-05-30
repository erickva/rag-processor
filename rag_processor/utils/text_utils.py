"""
Text processing utilities.

Provides text chunking functionality and chunk metadata management.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from config.constants import (
    MINIMUM_CHUNK_SIZE, MAXIMUM_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
)


@dataclass
class ChunkMetadata:
    """Metadata for a processed text chunk."""
    
    text: str
    metadata: Dict[str, Any]
    start_position: int
    end_position: int
    
    @property
    def character_count(self) -> int:
        """Get character count of chunk text."""
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        """Get word count of chunk text."""
        return len(self.text.split())


class TextChunker:
    """
    Advanced text chunking utility with pattern-based boundaries.
    
    Supports semantic chunking at natural boundaries rather than
    arbitrary character limits.
    """
    
    def __init__(self):
        """Initialize chunker with default settings."""
        pass
    
    def chunk_by_pattern(
        self, 
        text: str, 
        pattern: str, 
        overlap: int = 0,
        min_size: int = MINIMUM_CHUNK_SIZE,
        max_size: int = MAXIMUM_CHUNK_SIZE
    ) -> List[ChunkMetadata]:
        """
        Chunk text using regex pattern boundaries.
        
        Args:
            text (str): Text content to chunk
            pattern (str): Regex pattern for chunk boundaries
            overlap (int): Character overlap between chunks
            min_size (int): Minimum chunk size in characters
            max_size (int): Maximum chunk size in characters
            
        Returns:
            List[ChunkMetadata]: List of text chunks with metadata
        """
        chunks = []
        
        # Find all pattern matches for boundaries
        boundaries = list(re.finditer(pattern, text, re.MULTILINE))
        
        if not boundaries:
            # No pattern matches - fallback to size-based chunking
            return self.chunk_by_size(text, max_size, overlap, min_size)
        
        # Create chunks between boundaries
        start_pos = 0
        
        for i, boundary in enumerate(boundaries):
            # Determine chunk end position
            if i < len(boundaries) - 1:
                end_pos = boundaries[i + 1].start()
            else:
                end_pos = len(text)
            
            # Extract chunk text
            chunk_text = text[start_pos:end_pos].strip()
            
            # Skip chunks that are too small
            if len(chunk_text) < min_size:
                continue
            
            # Split large chunks
            if len(chunk_text) > max_size:
                sub_chunks = self._split_large_chunk(
                    chunk_text, max_size, overlap, start_pos
                )
                chunks.extend(sub_chunks)
            else:
                # Create chunk metadata
                chunk = ChunkMetadata(
                    text=chunk_text,
                    metadata={
                        "chunk_index": len(chunks),
                        "boundary_pattern": boundary.group(),
                        "chunking_method": "pattern-based",
                    },
                    start_position=start_pos,
                    end_position=end_pos
                )
                chunks.append(chunk)
            
            # Set next start position with overlap
            start_pos = max(0, end_pos - overlap)
        
        return chunks
    
    def chunk_by_size(
        self, 
        text: str, 
        chunk_size: int = MAXIMUM_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_size: int = MINIMUM_CHUNK_SIZE
    ) -> List[ChunkMetadata]:
        """
        Chunk text by character size with word boundary preservation.
        
        Args:
            text (str): Text content to chunk
            chunk_size (int): Target chunk size in characters
            overlap (int): Character overlap between chunks  
            min_size (int): Minimum chunk size in characters
            
        Returns:
            List[ChunkMetadata]: List of text chunks with metadata
        """
        chunks = []
        start_pos = 0
        
        while start_pos < len(text):
            # Calculate chunk end position
            end_pos = min(start_pos + chunk_size, len(text))
            
            # Adjust to word boundary if not at text end
            if end_pos < len(text):
                # Look for word boundary within last 100 characters
                boundary_search = text[max(end_pos - 100, start_pos):end_pos + 100]
                word_boundaries = list(re.finditer(r'\s+', boundary_search))
                
                if word_boundaries:
                    # Find closest boundary to target position
                    target_offset = min(100, end_pos - max(end_pos - 100, start_pos))
                    closest_boundary = min(
                        word_boundaries,
                        key=lambda b: abs(b.start() - target_offset)
                    )
                    end_pos = max(end_pos - 100, start_pos) + closest_boundary.end()
            
            # Extract chunk text
            chunk_text = text[start_pos:end_pos].strip()
            
            # Skip chunks that are too small (except if it's the last chunk)
            if len(chunk_text) >= min_size or end_pos >= len(text):
                chunk = ChunkMetadata(
                    text=chunk_text,
                    metadata={
                        "chunk_index": len(chunks),
                        "chunking_method": "size-based",
                        "target_size": chunk_size,
                    },
                    start_position=start_pos,
                    end_position=end_pos
                )
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_pos = max(start_pos + 1, end_pos - overlap)
            
            # Prevent infinite loops
            if start_pos >= end_pos and end_pos >= len(text):
                break
        
        return chunks
    
    def chunk_by_semantic_boundaries(
        self, 
        text: str, 
        boundary_patterns: List[str],
        overlap: int = 0
    ) -> List[ChunkMetadata]:
        """
        Chunk text at semantic boundaries like products, sections, etc.
        
        Args:
            text (str): Text content to chunk
            boundary_patterns (List[str]): List of regex patterns for boundaries
            overlap (int): Character overlap between chunks
            
        Returns:
            List[ChunkMetadata]: List of semantically bounded chunks
        """
        # Combine patterns into single regex with capture groups
        combined_pattern = '|'.join(f'({pattern})' for pattern in boundary_patterns)
        
        return self.chunk_by_pattern(text, combined_pattern, overlap)
    
    def _split_large_chunk(
        self, 
        chunk_text: str, 
        max_size: int, 
        overlap: int,
        base_start_pos: int
    ) -> List[ChunkMetadata]:
        """
        Split a chunk that exceeds maximum size.
        
        Args:
            chunk_text (str): Text to split
            max_size (int): Maximum chunk size
            overlap (int): Overlap between sub-chunks
            base_start_pos (int): Starting position in original text
            
        Returns:
            List[ChunkMetadata]: List of sub-chunks
        """
        sub_chunks = []
        start = 0
        
        while start < len(chunk_text):
            end = min(start + max_size, len(chunk_text))
            
            # Adjust to word boundary
            if end < len(chunk_text):
                last_space = chunk_text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            sub_text = chunk_text[start:end].strip()
            
            if sub_text:
                sub_chunk = ChunkMetadata(
                    text=sub_text,
                    metadata={
                        "chunk_index": len(sub_chunks),
                        "chunking_method": "large-chunk-split",
                        "parent_chunk": True,
                    },
                    start_position=base_start_pos + start,
                    end_position=base_start_pos + end
                )
                sub_chunks.append(sub_chunk)
            
            start = max(start + 1, end - overlap)
        
        return sub_chunks
    
    def extract_structure_info(self, text: str) -> Dict[str, Any]:
        """
        Extract structural information from text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, Any]: Structural analysis results
        """
        lines = text.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "average_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0,
            "paragraph_count": len(re.findall(r'\n\s*\n', text)),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "word_count": len(text.split()),
            "character_count": len(text),
        }