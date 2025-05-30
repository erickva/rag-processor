"""
FAQ processing strategy.

Specialized for FAQ documents with Q&A pair chunking to maintain
question-answer relationships and optimize for search.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import FAQ_CHUNK_OVERLAP


class FAQStrategy(ProcessingStrategy):
    """
    FAQ processing strategy.
    
    Chunks at Q&A pair boundaries to maintain the integrity of
    question-answer relationships for optimal search performance.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "faq/qa-pairs"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "FAQ chunking at Q&A pair boundaries to preserve question-answer relationships"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for Q&A boundaries."""
        return r'(Q:|Question:|Pergunta:)\s*(.+?)(?=(Q:|Question:|Pergunta:|A:|Answer:|Resposta:))'
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return FAQ_CHUNK_OVERLAP  # No overlap for Q&A pairs
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process FAQ content into Q&A pair chunks.
        
        Args:
            content (str): Raw FAQ text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of Q&A chunks with metadata
        """
        chunker = TextChunker()
        overlap = self.get_overlap(directive)
        
        # Try multiple FAQ patterns
        qa_pairs = self._extract_qa_pairs(content)
        
        if not qa_pairs:
            # Fallback to numbered question pattern
            qa_pairs = self._extract_numbered_questions(content)
        
        if not qa_pairs:
            # Final fallback - use question mark pattern
            qa_pairs = self._extract_question_mark_pairs(content)
        
        if not qa_pairs:
            # No FAQ patterns found - use fallback chunking
            return chunker.chunk_by_size(content, 800, overlap)
        
        chunks = []
        
        for i, (question, answer, start_pos, end_pos) in enumerate(qa_pairs):
            # Combine question and answer
            qa_text = f"{question}\n\n{answer}".strip()
            
            # Skip very short Q&A pairs
            if len(qa_text) < 50:
                continue
            
            # Analyze Q&A content
            qa_metadata = self._analyze_qa_pair(question, answer)
            
            # Create chunk with Q&A metadata
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "question": qa_metadata.get("question_clean"),
                "answer_length": qa_metadata.get("answer_length", 0),
                "question_type": qa_metadata.get("question_type", "general"),
                "topics": qa_metadata.get("topics", []),
                "has_links": qa_metadata.get("has_links", False),
                "has_examples": qa_metadata.get("has_examples", False),
                "difficulty_level": qa_metadata.get("difficulty", "basic"),
                "chunking_method": "qa-pairs",
            }
            
            chunk = ChunkMetadata(
                text=qa_text,
                metadata=chunk_metadata,
                start_position=start_pos,
                end_position=end_pos
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for FAQ strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for FAQ indicators
        faq_indicators = [
            r'(Q:|Question:|Pergunta:)',
            r'(A:|Answer:|Resposta:)',
            r'FAQ|F\.A\.Q\.',
            r'Frequently\s+Asked',
            r'^\d+\.\s*.+\?',
        ]
        
        indicator_matches = 0
        for pattern in faq_indicators:
            matches = len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
            indicator_matches += matches
        
        if indicator_matches < 4:
            issues.append("Content doesn't appear to be FAQ format")
        
        # Count questions vs answers
        question_count = len(re.findall(r'\?', content))
        answer_indicators = len(re.findall(r'(A:|Answer:|Resposta:)', content, re.IGNORECASE))
        
        if question_count < 3:
            issues.append("Very few questions detected")
        
        if answer_indicators > 0 and abs(question_count - answer_indicators) > 2:
            issues.append("Unbalanced question-answer pairs detected")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for FAQ documents.
        
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
            "#!strategy: faq/qa-pairs",
            f"#!validation: {client_config.name}/faq",
            "#!chunk-pattern: (Q:|Question:|Pergunta:)\\s*(.+?)(?=(Q:|Question:|Pergunta:|A:|Answer:|Resposta:))",
        ]
        
        # Add metadata
        metadata = {
            "type": "faq",
            "version": "1.0",
            "structure": "qa-pairs",
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
            "# FAQ Template",
            "",
            "Q: What is this product/service?",
            "A: This is a comprehensive explanation of what the product or service does and its main benefits.",
            "",
            "Q: How do I get started?",
            "A: To get started, follow these simple steps:",
            "1. First step",
            "2. Second step", 
            "3. Third step",
            "",
            "Q: What are the pricing options?",
            "A: We offer several pricing tiers to meet different needs. Please visit our pricing page for detailed information.",
            "",
            "Q: How can I contact support?",
            "A: You can reach our support team through:",
            "- Email: support@example.com",
            "- Phone: (555) 123-4567",
            "- Live chat on our website",
            "",
            "# Continue adding Q&A pairs following the same format.",
        ])
        
        return '\n'.join(template_parts)
    
    def _extract_qa_pairs(self, content: str) -> List[tuple]:
        """Extract Q&A pairs using explicit markers."""
        qa_pairs = []
        
        # Pattern for Q: ... A: ... format
        qa_pattern = r'(Q:|Question:|Pergunta:)\s*([^Q]*?)\s*(A:|Answer:|Resposta:)\s*([^Q]*?)(?=(Q:|Question:|Pergunta:)|$)'
        
        matches = re.finditer(qa_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            question = f"{match.group(1)} {match.group(2).strip()}"
            answer = f"{match.group(3)} {match.group(4).strip()}"
            
            qa_pairs.append((
                question,
                answer, 
                match.start(),
                match.end()
            ))
        
        return qa_pairs
    
    def _extract_numbered_questions(self, content: str) -> List[tuple]:
        """Extract numbered questions and following content as answers."""
        qa_pairs = []
        
        # Find numbered questions
        question_pattern = r'^\d+\.\s*(.+\?)'
        question_matches = list(re.finditer(question_pattern, content, re.MULTILINE))
        
        for i, match in enumerate(question_matches):
            question = match.group()
            
            # Find answer text until next question or end
            answer_start = match.end()
            if i < len(question_matches) - 1:
                answer_end = question_matches[i + 1].start()
            else:
                answer_end = len(content)
            
            answer = content[answer_start:answer_end].strip()
            
            if answer:  # Only include if there's an answer
                qa_pairs.append((
                    question,
                    answer,
                    match.start(),
                    answer_end
                ))
        
        return qa_pairs
    
    def _extract_question_mark_pairs(self, content: str) -> List[tuple]:
        """Extract questions ending with ? and following paragraphs."""
        qa_pairs = []
        
        # Split content into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        for i, paragraph in enumerate(paragraphs):
            # Check if paragraph ends with question mark
            if paragraph.strip().endswith('?'):
                question = paragraph.strip()
                
                # Look for answer in next paragraph(s)
                answer_parts = []
                for j in range(i + 1, min(i + 3, len(paragraphs))):  # Check next 2 paragraphs
                    next_para = paragraphs[j].strip()
                    if next_para and not next_para.endswith('?'):
                        answer_parts.append(next_para)
                    else:
                        break
                
                if answer_parts:
                    answer = '\n\n'.join(answer_parts)
                    
                    # Calculate positions (approximate)
                    question_pos = content.find(question)
                    answer_end = question_pos + len(question) + len(answer) + 10
                    
                    qa_pairs.append((
                        question,
                        answer,
                        question_pos,
                        min(answer_end, len(content))
                    ))
        
        return qa_pairs
    
    def _analyze_qa_pair(self, question: str, answer: str) -> Dict[str, Any]:
        """Analyze Q&A pair for metadata extraction."""
        metadata = {}
        
        # Clean question text
        question_clean = re.sub(r'^(Q:|Question:|Pergunta:)\s*', '', question).strip()
        metadata["question_clean"] = question_clean
        
        # Answer length and complexity
        metadata["answer_length"] = len(answer)
        metadata["answer_word_count"] = len(answer.split())
        
        # Classify question type
        if re.search(r'\b(what|o que)\b', question_clean, re.IGNORECASE):
            metadata["question_type"] = "definition"
        elif re.search(r'\b(how|como)\b', question_clean, re.IGNORECASE):
            metadata["question_type"] = "procedure"
        elif re.search(r'\b(why|por que)\b', question_clean, re.IGNORECASE):
            metadata["question_type"] = "explanation"
        elif re.search(r'\b(when|quando)\b', question_clean, re.IGNORECASE):
            metadata["question_type"] = "timing"
        elif re.search(r'\b(where|onde)\b', question_clean, re.IGNORECASE):
            metadata["question_type"] = "location"
        else:
            metadata["question_type"] = "general"
        
        # Extract topics/keywords
        topics = []
        # Simple keyword extraction from question
        words = re.findall(r'\b[a-zA-Z]{4,}\b', question_clean.lower())
        topics.extend(words[:5])  # Limit to first 5 words
        metadata["topics"] = topics
        
        # Detect content features
        metadata["has_links"] = bool(re.search(r'https?://|www\.', answer))
        metadata["has_examples"] = bool(re.search(r'example|exemplo|for instance', answer, re.IGNORECASE))
        metadata["has_steps"] = bool(re.search(r'\d+\.\s+|\n\s*[-*]\s+', answer))
        
        # Estimate difficulty
        if len(answer.split()) < 20:
            metadata["difficulty"] = "basic"
        elif len(answer.split()) > 100:
            metadata["difficulty"] = "advanced"
        else:
            metadata["difficulty"] = "intermediate"
        
        return metadata