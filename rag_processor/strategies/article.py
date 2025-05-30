"""
Article processing strategy.

Specialized for articles and narrative content with sentence-based chunking
that preserves paragraph structure and narrative flow.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import ARTICLE_CHUNK_OVERLAP


class ArticleStrategy(ProcessingStrategy):
    """
    Article processing strategy.
    
    Chunks at sentence boundaries while preserving paragraph structure
    and maintaining narrative flow with appropriate overlap.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "article/sentence-based"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "Article chunking at sentence boundaries with paragraph structure preservation"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for sentence boundaries."""
        return r'[.!?]+\s+'
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return ARTICLE_CHUNK_OVERLAP
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process article content into sentence-based chunks.
        
        Args:
            content (str): Raw article text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of article chunks with metadata
        """
        chunker = TextChunker()
        overlap = self.get_overlap(directive)
        
        # Use intelligent sentence-aware chunking
        chunks = self._chunk_by_sentences(content, overlap, client_config)
        
        if not chunks:
            # Fallback to size-based chunking
            return chunker.chunk_by_size(content, 1200, overlap)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for article strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        # Check sentence structure
        sentence_count = len(re.findall(r'[.!?]+', content))
        if sentence_count < 10:
            issues.append("Very few sentences detected - may not be suitable for sentence-based chunking")
        
        # Check paragraph structure
        paragraph_count = len(re.split(r'\n\s*\n', content))
        if paragraph_count < 3:
            issues.append("Very few paragraphs detected - content may be too short")
        
        # Check for article-like structure
        article_indicators = ["introduction", "conclusion", "paragraph", "section", "chapter"]
        indicator_count = sum(len(re.findall(indicator, content, re.IGNORECASE)) for indicator in article_indicators)
        
        if indicator_count == 0:
            issues.append("Content doesn't appear to have typical article structure")
        
        # Check average sentence length
        if sentence_count > 0:
            avg_sentence_length = len(content) / sentence_count
            if avg_sentence_length < 20:
                issues.append("Average sentence length is very short - may not be article content")
            elif avg_sentence_length > 200:
                issues.append("Average sentence length is very long - may need different chunking strategy")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for articles.
        
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
            "#!strategy: article/sentence-based",
            f"#!validation: {client_config.name}/article",
            "#!chunk-pattern: [.!?]+\\s+",
        ]
        
        # Add metadata
        metadata = {
            "type": "article",
            "version": "1.0",
            "structure": "narrative",
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
            "# Article Template",
            "",
            "## Introduction",
            "",
            "This is the introduction paragraph of your article. It should provide context and overview of the topic you'll be discussing. The introduction sets the tone and gives readers an idea of what to expect.",
            "",
            "## Main Content",
            "",
            "Here you can develop your main ideas. Each paragraph should focus on a specific point or aspect of your topic. Use clear, concise sentences that flow naturally from one to the next.",
            "",
            "For example, you might want to explain a concept in detail. Then you could provide evidence or examples to support your points. This creates a logical progression that readers can easily follow.",
            "",
            "## Supporting Details",
            "",
            "Add supporting information, examples, or case studies here. This section can include:",
            "",
            "- Bullet points for key information",
            "- Numbered lists for sequential processes",
            "- Quotes or references to other sources",
            "- Statistical data or research findings",
            "",
            "## Conclusion",
            "",
            "Summarize the main points of your article and provide any final thoughts or recommendations. The conclusion should tie everything together and leave readers with a clear understanding of the topic.",
            "",
            "# Continue adding content following proper article structure with clear paragraphs and sentences.",
        ])
        
        return '\n'.join(template_parts)
    
    def _chunk_by_sentences(self, content: str, overlap: int, client_config: ClientConfig) -> List[ChunkMetadata]:
        """
        Chunk content by sentences while preserving paragraph structure.
        
        Args:
            content (str): Article content to chunk
            overlap (int): Character overlap between chunks
            client_config (ClientConfig): Client configuration
            
        Returns:
            List[ChunkMetadata]: List of sentence-based chunks
        """
        chunks = []
        
        # Split into sentences while preserving paragraph boundaries
        sentences = self._extract_sentences_with_boundaries(content)
        
        if not sentences:
            return chunks
        
        current_chunk_sentences = []
        current_chunk_size = 0
        target_chunk_size = 1000  # Target size in characters
        max_chunk_size = 1500     # Maximum size before forced split
        
        for sentence_data in sentences:
            sentence_text = sentence_data["text"]
            sentence_size = len(sentence_text)
            
            # Check if adding this sentence would exceed limits
            would_exceed_target = current_chunk_size + sentence_size > target_chunk_size
            would_exceed_max = current_chunk_size + sentence_size > max_chunk_size
            
            # Create chunk if we have content and hit limits
            if current_chunk_sentences and (would_exceed_max or (would_exceed_target and current_chunk_size > 500)):
                chunk = self._create_sentence_chunk(
                    current_chunk_sentences, 
                    len(chunks), 
                    overlap if chunks else 0
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap sentences if needed
                if overlap > 0:
                    overlap_sentences = self._get_overlap_sentences(current_chunk_sentences, overlap)
                    current_chunk_sentences = overlap_sentences
                    current_chunk_size = sum(len(s["text"]) for s in overlap_sentences)
                else:
                    current_chunk_sentences = []
                    current_chunk_size = 0
            
            # Add current sentence
            current_chunk_sentences.append(sentence_data)
            current_chunk_size += sentence_size
        
        # Add final chunk if there's remaining content
        if current_chunk_sentences:
            chunk = self._create_sentence_chunk(
                current_chunk_sentences,
                len(chunks),
                0  # No overlap for final chunk
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_sentences_with_boundaries(self, content: str) -> List[Dict[str, Any]]:
        """Extract sentences with paragraph boundary information."""
        sentences = []
        
        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', content)
        position = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            # Find paragraph position in original content
            para_start = content.find(paragraph.strip(), position)
            position = para_start + len(paragraph)
            
            # Split paragraph into sentences
            sentence_pattern = r'([.!?]+)\s*'
            sentence_boundaries = list(re.finditer(sentence_pattern, paragraph))
            
            sentence_start = 0
            for boundary in sentence_boundaries:
                sentence_end = boundary.end()
                sentence_text = paragraph[sentence_start:sentence_end].strip()
                
                if sentence_text:
                    sentences.append({
                        "text": sentence_text,
                        "paragraph_index": para_idx,
                        "is_paragraph_start": sentence_start == 0,
                        "is_paragraph_end": sentence_end >= len(paragraph.strip()),
                        "absolute_position": para_start + sentence_start,
                    })
                
                sentence_start = sentence_end
            
            # Handle paragraph with no sentence boundaries
            if not sentence_boundaries and paragraph.strip():
                sentences.append({
                    "text": paragraph.strip(),
                    "paragraph_index": para_idx,
                    "is_paragraph_start": True,
                    "is_paragraph_end": True,
                    "absolute_position": para_start,
                })
        
        return sentences
    
    def _create_sentence_chunk(self, sentence_list: List[Dict], chunk_index: int, overlap: int) -> ChunkMetadata:
        """Create a chunk from a list of sentences."""
        if not sentence_list:
            return None
        
        # Combine sentence texts
        chunk_text = " ".join(s["text"] for s in sentence_list)
        
        # Calculate positions
        start_pos = sentence_list[0]["absolute_position"]
        end_pos = start_pos + len(chunk_text)
        
        # Analyze chunk content
        chunk_analysis = self._analyze_chunk_content(chunk_text, sentence_list)
        
        # Create metadata
        chunk_metadata = {
            "strategy": self.name,
            "chunk_index": chunk_index,
            "sentence_count": len(sentence_list),
            "paragraph_count": len(set(s["paragraph_index"] for s in sentence_list)),
            "starts_paragraph": sentence_list[0]["is_paragraph_start"],
            "ends_paragraph": sentence_list[-1]["is_paragraph_end"],
            "chunking_method": "sentence-based",
            "content_type": chunk_analysis.get("content_type", "narrative"),
            "has_dialogue": chunk_analysis.get("has_dialogue", False),
            "has_lists": chunk_analysis.get("has_lists", False),
            "readability_score": chunk_analysis.get("readability", "medium"),
        }
        
        return ChunkMetadata(
            text=chunk_text,
            metadata=chunk_metadata,
            start_position=start_pos,
            end_position=end_pos
        )
    
    def _get_overlap_sentences(self, sentences: List[Dict], overlap_chars: int) -> List[Dict]:
        """Get sentences for overlap based on character count."""
        if not sentences:
            return []
        
        overlap_sentences = []
        char_count = 0
        
        # Work backwards from end to get overlap
        for sentence in reversed(sentences):
            sentence_length = len(sentence["text"])
            if char_count + sentence_length <= overlap_chars:
                overlap_sentences.insert(0, sentence)
                char_count += sentence_length
            else:
                break
        
        return overlap_sentences
    
    def _analyze_chunk_content(self, chunk_text: str, sentences: List[Dict]) -> Dict[str, Any]:
        """Analyze chunk content for additional metadata."""
        analysis = {}
        
        # Determine content type
        if re.search(r'"[^"]*"', chunk_text):
            analysis["content_type"] = "dialogue"
            analysis["has_dialogue"] = True
        elif re.search(r'^\s*[-*+]\s+', chunk_text, re.MULTILINE):
            analysis["content_type"] = "list"
            analysis["has_lists"] = True
        elif len(sentences) == 1:
            analysis["content_type"] = "single_sentence"
        else:
            analysis["content_type"] = "narrative"
        
        # Simple readability assessment
        avg_sentence_length = len(chunk_text) / len(sentences) if sentences else 0
        if avg_sentence_length < 50:
            analysis["readability"] = "easy"
        elif avg_sentence_length > 120:
            analysis["readability"] = "complex"
        else:
            analysis["readability"] = "medium"
        
        # Check for special features
        analysis["has_numbers"] = bool(re.search(r'\d+', chunk_text))
        analysis["has_questions"] = bool(re.search(r'\?', chunk_text))
        analysis["has_exclamations"] = bool(re.search(r'!', chunk_text))
        
        return analysis