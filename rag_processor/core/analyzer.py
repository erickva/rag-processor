"""
Document Analysis Engine.

Analyzes document content to determine document type and processing patterns
through pattern detection and confidence scoring algorithms.
"""

import re
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from config.constants import (
    PATTERN_FREQUENCY_MULTIPLIER, HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD, REQUIRED_FIELD_SCORE_BOOST,
    PRICE_PATTERN_SCORE_BOOST
)


class DocumentType(Enum):
    """Enumeration of supported document types."""
    
    STRUCTURED_BLOCKS = "structured_blocks"
    PRODUCT_CATALOG = "product_catalog"
    USER_MANUAL = "user_manual"
    FAQ = "faq"
    ARTICLE = "article"
    LEGAL_DOCUMENT = "legal_document"
    CODE_DOCUMENTATION = "code_documentation"
    UNKNOWN = "unknown"


@dataclass
class DocumentAnalysis:
    """Results of document analysis with confidence scoring."""
    
    document_type: DocumentType
    confidence: float
    detected_patterns: Dict[str, int]
    recommended_strategy: str
    analysis_details: Dict[str, any]


class DocumentAnalyzer:
    """
    Analyzes documents to determine type and optimal processing strategy.
    
    Uses pattern detection and frequency analysis to build confidence scores
    for different document types.
    """
    
    def __init__(self):
        """Initialize analyzer with detection patterns for each document type."""
        
        # Pattern definitions: (regex_pattern, confidence_weight)
        self.detection_patterns: Dict[DocumentType, List[Tuple[str, float]]] = {
            DocumentType.STRUCTURED_BLOCKS: [
                # Empty line separated blocks (universal pattern)
                (r'\n\s*\n', 4.0),                            # Empty lines (highest weight)
                
                # Field: Value patterns (universal structure)
                (r'(?i)^[A-Za-z][A-Za-z\s]*?:\s*[^\n]*$', 3.5), # Any field: value pattern
                
                # Block structure indicators
                (r'(?i)^(Name|Title|Item):\s*([^\n]*)', 3.0),   # Common block starters
                (r'(?i)^(Description|Details?):\s*([^\n]*)', 2.5), # Description fields
                (r'(?i)^(Price|Cost|Value):\s*([^\n]*)', 2.5),  # Price fields
                (r'(?i)^(Category|Type|Class):\s*([^\n]*)', 2.0), # Category fields
                
                # Multiple blocks indicator (high confidence for block separation)
                (r'(?:\n\s*\n.*?){3,}', 5.0),                # 3+ empty line separations
            ],
            
            DocumentType.PRODUCT_CATALOG: [
                # Core English product fields (flexible - can be empty)
                (r'(?i)Name:\s*([^\n]*)', 3.0),           # Name field (highest weight)
                (r'(?i)Description:\s*([^\n]*)', 2.5),    # Description field
                (r'(?i)Price:\s*([^\n]*)', 2.5),          # Price field (can be empty)
                
                # Additional common product fields
                (r'(?i)Category:\s*([^\n]*)', 1.5),       # Category field
                (r'(?i)Brand:\s*([^\n]*)', 1.5),          # Brand field
                (r'(?i)SKU:\s*([^\n]*)', 1.5),            # SKU field
                (r'(?i)Product:\s*([^\n]*)', 2.0),        # Alternative product field
                (r'(?i)Item:\s*([^\n]*)', 1.8),           # Item field
                
                # Legacy Portuguese support (lower weight for backward compatibility)
                (r'Nome:\s*([^\n]*)', 1.5),               # Portuguese name
                (r'Descrição:\s*([^\n]*)', 1.2),          # Portuguese description
                (r'Preço:\s*([^\n]*)', 1.2),              # Portuguese price
            ],
            
            DocumentType.USER_MANUAL: [
                (r'^#{1,6}\s+', 2.0),               # Markdown headers
                (r'^\d+\.\s+', 1.5),                # Numbered sections
                (r'Chapter\s+\d+', 2.5),            # Chapter markers
                (r'Section\s+\d+', 2.0),            # Section markers
                (r'^\d+\.\d+\s+', 2.0),             # Subsection numbering
                (r'Step\s+\d+', 1.5),               # Step-by-step instructions
                (r'Instructions?:', 1.8),           # Instruction headers
                (r'How\s+to\s+', 1.5),              # How-to patterns
            ],
            
            DocumentType.FAQ: [
                (r'(Q:|Question:|Pergunta:)', 3.0), # Question markers
                (r'(A:|Answer:|Resposta:)', 3.0),   # Answer markers
                (r'^\d+\.\s*(.+\?)', 2.5),          # Numbered questions
                (r'FAQ|F\.A\.Q\.', 2.0),            # FAQ headers
                (r'\?\s*$', 1.5),                   # Lines ending with ?
                (r'Frequently\s+Asked', 2.0),       # FAQ phrase
            ],
            
            DocumentType.ARTICLE: [
                (r'^[A-Z][^.!?]*[.!?]\s*$', 1.0),   # Sentence patterns
                (r'paragraph|parágrafo', 1.2),      # Paragraph references
                (r'introduction|introdução', 1.5),   # Introduction markers
                (r'conclusion|conclusão', 1.5),      # Conclusion markers
                (r'Por\s+exemplo', 1.0),            # Example phrases (PT)
                (r'For\s+example', 1.0),            # Example phrases (EN)
                (r'Therefore|Therefore,', 1.2),      # Transition words
            ],
            
            DocumentType.LEGAL_DOCUMENT: [
                (r'Article\s+\d+|Artigo\s+\d+', 2.5), # Legal articles
                (r'Section\s+\d+|Seção\s+\d+', 2.0),  # Legal sections
                (r'whereas|considerando', 2.0),        # Legal whereas clauses
                (r'hereby|pelo\s+presente', 2.0),      # Legal language
                (r'Terms\s+and\s+Conditions', 2.5),    # T&C headers
                (r'Privacy\s+Policy', 2.5),            # Privacy policy
                (r'Agreement|Acordo', 2.0),            # Agreement documents
                (r'Contract|Contrato', 2.0),           # Contract documents
            ],
            
            DocumentType.CODE_DOCUMENTATION: [
                (r'def\s+\w+\(', 2.5),              # Python functions
                (r'function\s+\w+\(', 2.5),         # JavaScript functions
                (r'class\s+\w+', 2.0),              # Class definitions
                (r'API|api', 2.0),                  # API documentation
                (r'```[\w]*\n', 2.0),               # Code blocks
                (r'@param|@return', 2.0),           # Documentation tags
                (r'import\s+\w+', 1.5),             # Import statements
                (r'##\s+[A-Z]', 1.5),               # API section headers
            ],
        }
    
    def analyze(self, content: str) -> DocumentAnalysis:
        """
        Analyze document content to determine type and confidence.
        
        Args:
            content (str): Document text content to analyze
            
        Returns:
            DocumentAnalysis: Analysis results with confidence scores
        """
        # Calculate pattern scores for each document type
        type_scores: Dict[DocumentType, float] = {}
        all_detected_patterns: Dict[str, int] = {}
        
        for doc_type, patterns in self.detection_patterns.items():
            score, detected = self._calculate_type_score(content, patterns)
            type_scores[doc_type] = score
            
            # Merge detected patterns with prefixed type name
            for pattern, count in detected.items():
                pattern_key = f"{doc_type.value}:{pattern[:30]}..."
                all_detected_patterns[pattern_key] = count
        
        # Find highest scoring type
        best_type = max(type_scores.keys(), key=lambda t: type_scores[t])
        best_score = type_scores[best_type]
        
        # Normalize confidence score (0.0 to 1.0)
        confidence = self._normalize_confidence(best_score, len(content))
        
        # Determine recommended strategy
        recommended_strategy = self._get_recommended_strategy(best_type, content)
        
        # Build analysis details
        analysis_details = {
            "content_length": len(content),
            "type_scores": {t.value: s for t, s in type_scores.items()},
            "normalized_scores": {
                t.value: self._normalize_confidence(s, len(content)) 
                for t, s in type_scores.items()
            },
            "pattern_analysis": self._analyze_patterns(content),
        }
        
        return DocumentAnalysis(
            document_type=best_type,
            confidence=confidence,
            detected_patterns=all_detected_patterns,
            recommended_strategy=recommended_strategy,
            analysis_details=analysis_details
        )
    
    def _calculate_type_score(self, content: str, patterns: List[Tuple[str, float]]) -> Tuple[float, Dict[str, int]]:
        """
        Calculate confidence score for a document type based on pattern matches.
        
        Args:
            content (str): Document content
            patterns (List[Tuple[str, float]]): Patterns with weights
            
        Returns:
            Tuple[float, Dict[str, int]]: Score and detected pattern counts
        """
        total_score = 0.0
        detected_patterns: Dict[str, int] = {}
        
        for pattern, weight in patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            count = len(matches)
            
            if count > 0:
                detected_patterns[pattern] = count
                
                # Apply frequency multiplier for patterns found multiple times
                frequency_boost = min(count * PATTERN_FREQUENCY_MULTIPLIER, 5.0)
                pattern_score = weight * frequency_boost
                total_score += pattern_score
        
        return total_score, detected_patterns
    
    def _normalize_confidence(self, raw_score: float, content_length: int) -> float:
        """
        Normalize raw pattern score to 0.0-1.0 confidence range.
        
        Args:
            raw_score (float): Raw pattern matching score
            content_length (int): Length of document content
            
        Returns:
            float: Normalized confidence score (0.0 to 1.0)
        """
        # Handle empty content
        if content_length == 0:
            return 0.0
        
        # Base normalization considering content length
        length_factor = min(content_length / 1000, 2.0)  # Cap at 2x for very long docs
        adjusted_score = raw_score / (10.0 * length_factor)
        
        # Apply sigmoid-like function to get 0-1 range
        confidence = min(adjusted_score / (1.0 + adjusted_score), 0.95)
        
        return round(confidence, 3)
    
    def _get_recommended_strategy(self, document_type: DocumentType, content: str = "") -> str:
        """
        Get the recommended processing strategy for a document type.
        
        Args:
            document_type (DocumentType): Detected document type
            content (str): Document content for sub-strategy detection
            
        Returns:
            str: Recommended strategy name
        """
        if document_type == DocumentType.STRUCTURED_BLOCKS:
            # Determine best structured-blocks sub-strategy
            return self._get_structured_blocks_strategy(content)
        
        strategy_mapping = {
            DocumentType.PRODUCT_CATALOG: "structured-blocks/empty-line-separated",  # Updated to use structured-blocks
            DocumentType.USER_MANUAL: "structured-blocks/heading-separated",        # Updated to use structured-blocks  
            DocumentType.FAQ: "faq/qa-pairs",
            DocumentType.ARTICLE: "article/sentence-based", 
            DocumentType.LEGAL_DOCUMENT: "legal/paragraph-based",
            DocumentType.CODE_DOCUMENTATION: "code/function-based",
            DocumentType.UNKNOWN: "structured-blocks/empty-line-separated",         # Default to universal strategy
        }
        
        return strategy_mapping.get(document_type, "structured-blocks/empty-line-separated")
    
    def _get_structured_blocks_strategy(self, content: str) -> str:
        """
        Determine the best structured-blocks sub-strategy based on content patterns.
        
        Args:
            content (str): Document content to analyze
            
        Returns:
            str: Best structured-blocks strategy name
        """
        # Count different separator types
        empty_lines = len(re.findall(r'\n\s*\n', content))
        headings = len(re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE))
        numbered_items = len(re.findall(r'^\d+\.\s+', content, re.MULTILINE))
        
        # Determine best strategy based on separator frequency
        if headings >= 3 and headings > empty_lines * 0.5:
            return "structured-blocks/heading-separated"
        elif numbered_items >= 3 and numbered_items > empty_lines * 0.5:
            return "structured-blocks/numbered-separated"
        else:
            # Default to empty-line separation (most universal)
            return "structured-blocks/empty-line-separated"
    
    def _analyze_patterns(self, content: str) -> Dict[str, any]:
        """
        Perform additional pattern analysis for insights.
        
        Args:
            content (str): Document content
            
        Returns:
            Dict[str, any]: Additional analysis insights
        """
        lines = content.split('\n')
        
        return {
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "average_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0,
            "has_headers": bool(re.search(r'^#{1,6}\s+', content, re.MULTILINE)),
            "has_numbering": bool(re.search(r'^\d+\.\s+', content, re.MULTILINE)),
            "has_questions": bool(re.search(r'.+\?\s*$', content, re.MULTILINE)),
            "has_structured_fields": bool(re.search(r'^\w+:\s*[^\n]+', content, re.MULTILINE)),
            "language_indicators": {
                "portuguese": len(re.findall(r'\b(e|o|a|de|do|da|para|com|em|por)\b', content, re.IGNORECASE)),
                "english": len(re.findall(r'\b(the|and|or|of|to|for|with|in|by)\b', content, re.IGNORECASE)),
            }
        }
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Get human-readable confidence level description.
        
        Args:
            confidence (float): Confidence score (0.0 to 1.0)
            
        Returns:
            str: Confidence level description
        """
        if confidence >= HIGH_CONFIDENCE_THRESHOLD:
            return "High"
        elif confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
            return "Medium"
        else:
            return "Low"
    
    def suggest_improvements(self, analysis: DocumentAnalysis) -> List[str]:
        """
        Suggest improvements based on analysis results.
        
        Args:
            analysis (DocumentAnalysis): Document analysis results
            
        Returns:
            List[str]: List of improvement suggestions
        """
        suggestions = []
        
        if analysis.confidence < MEDIUM_CONFIDENCE_THRESHOLD:
            suggestions.append(
                "Consider adding more structured patterns to improve auto-detection"
            )
        
        if analysis.document_type == DocumentType.UNKNOWN:
            suggestions.append(
                "Document type could not be determined - specify strategy explicitly"
            )
        
        content_length = analysis.analysis_details.get("content_length", 0)
        if content_length < 500:
            suggestions.append(
                "Document is quite short - consider combining with related content"
            )
        
        patterns = analysis.detected_patterns
        if not patterns:
            suggestions.append(
                "No clear structural patterns detected - consider manual formatting"
            )
        
        return suggestions