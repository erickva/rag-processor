"""
Core RAG Document Processor.

Main orchestration class that coordinates document analysis, strategy selection,
validation, and chunking based on processing directives.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

from ..utils.directive_parser import DirectiveParser, ProcessingDirective
from ..utils.text_utils import TextChunker, ChunkMetadata
from .analyzer import DocumentAnalyzer, DocumentType, DocumentAnalysis
from .validator import ValidationEngine, ValidationResult
from ..strategies.base import ProcessingStrategy
from ..strategies import (
    ProductsStrategy, ManualStrategy, FAQStrategy, 
    ArticleStrategy, LegalStrategy, CodeStrategy
)
from ..strategies.structured_blocks import (
    EmptyLineSeparatedStrategy, HeadingSeparatedStrategy, NumberedSeparatedStrategy
)
from ..clients.base import ClientConfig
from ..clients import DefaultConfig
from config.constants import (
    RAG_FILE_EXTENSION, ERROR_FILE_NOT_FOUND, ERROR_INVALID_DIRECTIVE,
    SUCCESS_DOCUMENT_PROCESSED, HIGH_CONFIDENCE_THRESHOLD
)


@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    
    chunks: List[ChunkMetadata]
    analysis: DocumentAnalysis
    validation: ValidationResult
    strategy_used: str
    processing_time: float
    metadata: Dict[str, Any]


class RAGDocumentProcessor:
    """
    Main RAG document processor that orchestrates the complete pipeline.
    
    Handles document analysis, strategy selection, validation, and chunking
    based on embedded processing directives in .rag files.
    """
    
    def __init__(self):
        """Initialize the processor with all available strategies and clients."""
        self.directive_parser = DirectiveParser()
        self.analyzer = DocumentAnalyzer()
        self.validator = ValidationEngine()
        self.chunker = TextChunker()
        
        # Register processing strategies
        self.strategies: Dict[str, ProcessingStrategy] = {
            # Structured blocks strategies (primary - mechanical separation)
            "structured-blocks/empty-line-separated": EmptyLineSeparatedStrategy(),
            "structured-blocks/heading-separated": HeadingSeparatedStrategy(),
            "structured-blocks/numbered-separated": NumberedSeparatedStrategy(),
            
            # Legacy strategies (semantic-based, still supported)
            "products/semantic-boundary": ProductsStrategy(),
            "manual/section-based": ManualStrategy(),
            "faq/qa-pairs": FAQStrategy(),
            "article/sentence-based": ArticleStrategy(),
            "legal/paragraph-based": LegalStrategy(),
            "code/function-based": CodeStrategy(),
        }
        
        # Register client configurations  
        self.client_configs: Dict[str, ClientConfig] = {
            "default": DefaultConfig(),
        }
    
    def process_file(self, file_path: str) -> ProcessingResult:
        """
        Process a .rag file through the complete pipeline.
        
        Args:
            file_path (str): Path to the .rag document file
            
        Returns:
            ProcessingResult: Complete processing results
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If processing directives are invalid
        """
        import time
        start_time = time.time()
        
        # Load and validate file
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"{ERROR_FILE_NOT_FOUND}: {file_path}")
        
        if not file_path.endswith(RAG_FILE_EXTENSION):
            raise ValueError(f"File must have {RAG_FILE_EXTENSION} extension")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.process_content(content, file_path_obj.name, time.time() - start_time)
    
    def process_content(self, content: str, filename: str = "", processing_time: float = 0.0) -> ProcessingResult:
        """
        Process document content through the complete pipeline.
        
        Args:
            content (str): Raw document content with directives
            filename (str): Optional filename for metadata
            processing_time (float): Optional existing processing time
            
        Returns:
            ProcessingResult: Complete processing results
        """
        import time
        if processing_time == 0.0:
            start_time = time.time()
        
        # Parse processing directives
        directive = self.directive_parser.parse(content)
        document_text = self.directive_parser.extract_content(content)
        
        # Analyze document to determine type and patterns
        analysis = self.analyzer.analyze(document_text)
        
        # Select processing strategy
        strategy_name = self._select_strategy(directive, analysis)
        strategy = self.strategies[strategy_name]
        
        # Get client configuration
        client_config = self._get_client_config(directive)
        
        # Validate document
        validation = self.validator.validate(
            document_text, strategy, client_config, directive
        )
        
        # Process chunks using selected strategy
        chunks = strategy.process(document_text, directive, client_config)
        
        # Calculate final processing time
        if processing_time == 0.0:
            processing_time = time.time() - start_time
        
        return ProcessingResult(
            chunks=chunks,
            analysis=analysis,
            validation=validation,
            strategy_used=strategy_name,
            processing_time=processing_time,
            metadata={
                "filename": filename,
                "total_chunks": len(chunks),
                "total_characters": len(document_text),
                "directive_metadata": directive.metadata,
            }
        )
    
    def analyze_document(self, file_path: str) -> DocumentAnalysis:
        """
        Analyze a document to determine its type and processing recommendations.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            DocumentAnalysis: Analysis results with confidence scores
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract content without directives for analysis
        document_text = self.directive_parser.extract_content(content)
        return self.analyzer.analyze(document_text)
    
    def validate_document(self, file_path: str) -> ValidationResult:
        """
        Validate a .rag document against its processing strategy.
        
        Args:
            file_path (str): Path to the .rag document file
            
        Returns:
            ValidationResult: Validation results with any issues found
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        directive = self.directive_parser.parse(content)
        document_text = self.directive_parser.extract_content(content)
        analysis = self.analyzer.analyze(document_text)
        
        strategy_name = self._select_strategy(directive, analysis)
        strategy = self.strategies[strategy_name]
        client_config = self._get_client_config(directive)
        
        return self.validator.validate(document_text, strategy, client_config, directive)
    
    def create_template(self, document_type: DocumentType, client: str = "default") -> str:
        """
        Create a .rag template for a specific document type and client.
        
        Args:
            document_type (DocumentType): Type of document to create template for
            client (str): Client configuration to use
            
        Returns:
            str: Complete .rag template content
        """
        # Map document types to strategies
        type_to_strategy = {
            DocumentType.PRODUCT_CATALOG: "products/semantic-boundary",
            DocumentType.USER_MANUAL: "manual/section-based", 
            DocumentType.FAQ: "faq/qa-pairs",
            DocumentType.ARTICLE: "article/sentence-based",
            DocumentType.LEGAL_DOCUMENT: "legal/paragraph-based",
            DocumentType.CODE_DOCUMENTATION: "code/function-based",
        }
        
        strategy_name = type_to_strategy.get(document_type, "article/sentence-based")
        strategy = self.strategies[strategy_name]
        client_config = self.client_configs.get(client, self.client_configs["default"])
        
        return strategy.create_template(client_config)
    
    def _select_strategy(self, directive: ProcessingDirective, analysis: DocumentAnalysis) -> str:
        """
        Select the best processing strategy based on directive and analysis.
        
        Args:
            directive (ProcessingDirective): Parsed processing directive
            analysis (DocumentAnalysis): Document analysis results
            
        Returns:
            str: Name of the selected strategy
        """
        # Use explicit strategy from directive if provided
        if directive.strategy:
            if directive.strategy in self.strategies:
                return directive.strategy
            else:
                raise ValueError(f"{ERROR_INVALID_DIRECTIVE}: Unknown strategy '{directive.strategy}'")
        
        # Auto-select based on analysis confidence
        if analysis.confidence >= HIGH_CONFIDENCE_THRESHOLD:
            type_to_strategy = {
                DocumentType.PRODUCT_CATALOG: "products/semantic-boundary",
                DocumentType.USER_MANUAL: "manual/section-based",
                DocumentType.FAQ: "faq/qa-pairs", 
                DocumentType.ARTICLE: "article/sentence-based",
                DocumentType.LEGAL_DOCUMENT: "legal/paragraph-based",
                DocumentType.CODE_DOCUMENTATION: "code/function-based",
            }
            return type_to_strategy.get(analysis.document_type, "article/sentence-based")
        
        # Default fallback strategy
        return "article/sentence-based"
    
    def _get_client_config(self, directive: ProcessingDirective) -> ClientConfig:
        """
        Get client configuration (simplified - always use default).
        
        Args:
            directive (ProcessingDirective): Parsed processing directive
            
        Returns:
            ClientConfig: Default client configuration
        """
        # In simplified format, always use default client config
        return self.client_configs["default"]
    
    def get_available_strategies(self) -> List[str]:
        """Get list of all available processing strategies."""
        return list(self.strategies.keys())
    
    def get_available_clients(self) -> List[str]:
        """Get list of all available client configurations.""" 
        return list(self.client_configs.keys())
    
    def register_strategy(self, name: str, strategy: ProcessingStrategy) -> None:
        """
        Register a new processing strategy.
        
        Args:
            name (str): Strategy name (format: category/method)
            strategy (ProcessingStrategy): Strategy implementation
        """
        self.strategies[name] = strategy
    
    def register_client_config(self, name: str, config: ClientConfig) -> None:
        """
        Register a new client configuration.
        
        Args:
            name (str): Client name
            config (ClientConfig): Client configuration
        """
        self.client_configs[name] = config