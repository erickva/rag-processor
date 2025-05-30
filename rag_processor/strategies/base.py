"""
Base processing strategy interface.

Defines the common interface that all processing strategies must implement
for consistent document chunking and template generation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata
from ..clients.base import ClientConfig


class ProcessingStrategy(ABC):
    """
    Abstract base class for all document processing strategies.
    
    Each strategy implements document-type-specific chunking logic
    while maintaining a consistent interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the strategy."""
        pass
    
    @property
    @abstractmethod
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for chunk boundaries."""
        pass
    
    @property
    @abstractmethod
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        pass
    
    @abstractmethod
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process document content into chunks using this strategy.
        
        Args:
            content (str): Raw document text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of processed chunks with metadata
        """
        pass
    
    @abstractmethod
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for this strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        pass
    
    @abstractmethod
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for this strategy.
        
        Args:
            client_config (ClientConfig): Client configuration for customization
            
        Returns:
            str: Complete .rag template content
        """
        pass
    
    def get_chunk_pattern(self, directive: ProcessingDirective) -> str:
        """
        Get the chunk pattern from strategy default.
        
        Args:
            directive (ProcessingDirective): Processing directives (unused in simplified format)
            
        Returns:
            str: Regex pattern for chunk boundaries
        """
        return self.default_chunk_pattern
    
    def get_overlap(self, directive: ProcessingDirective) -> int:
        """
        Get the overlap amount from strategy default.
        
        Args:
            directive (ProcessingDirective): Processing directives (unused in simplified format)
            
        Returns:
            int: Character overlap between chunks
        """
        return self.default_overlap
    
    def create_chunk_metadata(
        self, 
        text: str, 
        chunk_index: int, 
        start_pos: int, 
        end_pos: int,
        metadata: Dict[str, Any] = None
    ) -> ChunkMetadata:
        """
        Create standardized chunk metadata.
        
        Args:
            text (str): Chunk text content
            chunk_index (int): Zero-based chunk index
            start_pos (int): Start position in original document
            end_pos (int): End position in original document  
            metadata (Dict[str, Any]): Additional metadata
            
        Returns:
            ChunkMetadata: Complete chunk metadata
        """
        base_metadata = {
            "strategy": self.name,
            "chunk_index": chunk_index,
            "start_position": start_pos,
            "end_position": end_pos,
            "character_count": len(text),
            "word_count": len(text.split()),
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        return ChunkMetadata(
            text=text.strip(),
            metadata=base_metadata,
            start_position=start_pos,
            end_position=end_pos
        )