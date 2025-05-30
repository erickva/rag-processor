"""
Legal processing strategy.

Specialized for legal documents with paragraph-based chunking that preserves
legal structure, article numbering, and clause relationships.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import LEGAL_CHUNK_OVERLAP


class LegalStrategy(ProcessingStrategy):
    """
    Legal document processing strategy.
    
    Chunks at paragraph boundaries while preserving legal structure,
    article numbering, and maintaining clause relationships.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "legal/paragraph-based"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "Legal document chunking at paragraph boundaries with structure preservation"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for legal paragraph boundaries."""
        return r'\n\n+'  # Double newlines indicate paragraph breaks
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return LEGAL_CHUNK_OVERLAP
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process legal content into paragraph-based chunks.
        
        Args:
            content (str): Raw legal document text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of legal chunks with metadata
        """
        chunker = TextChunker()
        overlap = self.get_overlap(directive)
        
        # Use specialized legal chunking
        chunks = self._chunk_by_legal_structure(content, overlap, client_config)
        
        if not chunks:
            # Fallback to paragraph-based chunking
            return chunker.chunk_by_pattern(content, r'\n\s*\n', overlap)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for legal strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for legal document indicators
        legal_indicators = [
            r'Article\s+\d+|Artigo\s+\d+',
            r'Section\s+\d+|Seção\s+\d+',
            r'whereas|considerando',
            r'hereby|pelo\s+presente',
            r'Terms\s+and\s+Conditions',
            r'Privacy\s+Policy',
            r'Agreement|Acordo',
            r'Contract|Contrato',
            r'shall|deve|deverá',
            r'party|parte',
            r'clause|cláusula',
        ]
        
        indicator_matches = 0
        for pattern in legal_indicators:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            indicator_matches += matches
        
        if indicator_matches < 3:
            issues.append("Content doesn't appear to be legal document format")
        
        # Check paragraph structure
        paragraph_count = len(re.split(r'\n\s*\n', content))
        if paragraph_count < 5:
            issues.append("Very few paragraphs detected - may not be suitable for paragraph-based chunking")
        
        # Check for numbered sections/articles
        numbered_sections = len(re.findall(r'^\s*\d+\.', content, re.MULTILINE))
        if numbered_sections == 0:
            issues.append("No numbered sections detected - legal structure may be unclear")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for legal documents.
        
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
            "#!strategy: legal/paragraph-based",
            f"#!validation: {client_config.name}/legal-document",
            "#!chunk-pattern: \\n\\n+",
        ]
        
        # Add metadata
        metadata = {
            "type": "legal-document",
            "version": "1.0",
            "structure": "legal",
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
            "# Legal Document Template",
            "",
            "## Article 1 - Definitions",
            "",
            "For the purposes of this agreement, the following terms shall have the meanings set forth below:",
            "",
            "1.1 \"Party\" means each individual or entity that is a signatory to this agreement.",
            "",
            "1.2 \"Services\" means the services to be provided under this agreement as described herein.",
            "",
            "## Article 2 - Scope of Agreement",
            "",
            "This agreement governs the relationship between the parties with respect to the subject matter described herein. The parties agree to be bound by the terms and conditions set forth in this document.",
            "",
            "## Article 3 - Obligations",
            "",
            "3.1 Each party shall perform its obligations under this agreement in good faith and in accordance with applicable law.",
            "",
            "3.2 The parties acknowledge that time is of the essence in the performance of their respective obligations.",
            "",
            "## Article 4 - Term and Termination",
            "",
            "4.1 This agreement shall commence on the date of execution and shall continue for a period of one (1) year unless terminated earlier in accordance with the provisions hereof.",
            "",
            "4.2 Either party may terminate this agreement upon thirty (30) days written notice to the other party.",
            "",
            "# Continue adding articles and clauses following proper legal document structure.",
        ])
        
        return '\n'.join(template_parts)
    
    def _chunk_by_legal_structure(self, content: str, overlap: int, client_config: ClientConfig) -> List[ChunkMetadata]:
        """
        Chunk legal content preserving legal structure.
        
        Args:
            content (str): Legal document content
            overlap (int): Character overlap between chunks
            client_config (ClientConfig): Client configuration
            
        Returns:
            List[ChunkMetadata]: List of legal structure chunks
        """
        chunks = []
        
        # Try to identify legal sections/articles first
        legal_sections = self._extract_legal_sections(content)
        
        if legal_sections:
            chunks = self._process_legal_sections(legal_sections, overlap)
        else:
            # Fallback to paragraph processing
            chunks = self._process_paragraphs(content, overlap)
        
        return chunks
    
    def _extract_legal_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract legal sections/articles from content."""
        sections = []
        
        # Patterns for legal sections
        section_patterns = [
            r'^(Article\s+\d+|Artigo\s+\d+)[:\-\s]*(.*)$',
            r'^(Section\s+\d+|Seção\s+\d+)[:\-\s]*(.*)$',
            r'^(\d+\.\d*)[:\-\s]*(.*)$',
            r'^([A-Z][A-Z\s]{5,30})\s*$',  # ALL CAPS section headers
        ]
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
            
            if matches:
                for i, match in enumerate(matches):
                    section_start = match.start()
                    
                    # Find section end (next section or end of document)
                    if i < len(matches) - 1:
                        section_end = matches[i + 1].start()
                    else:
                        section_end = len(content)
                    
                    section_text = content[section_start:section_end].strip()
                    
                    if len(section_text) > 100:  # Only include substantial sections
                        sections.append({
                            "text": section_text,
                            "title": match.group(1).strip(),
                            "subtitle": match.group(2).strip() if len(match.groups()) > 1 else "",
                            "start_pos": section_start,
                            "end_pos": section_end,
                            "section_type": self._classify_legal_section(section_text),
                        })
                
                break  # Use first pattern that finds sections
        
        return sections
    
    def _process_legal_sections(self, sections: List[Dict], overlap: int) -> List[ChunkMetadata]:
        """Process legal sections into chunks."""
        chunks = []
        
        for i, section in enumerate(sections):
            section_text = section["text"]
            
            # For large sections, split into subsections
            if len(section_text) > 2000:
                sub_chunks = self._split_large_legal_section(section, overlap)
                chunks.extend(sub_chunks)
            else:
                # Create single chunk for section
                legal_metadata = self._analyze_legal_content(section_text, section)
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "section_title": section["title"],
                    "section_subtitle": section["subtitle"],
                    "section_type": section["section_type"],
                    "chunking_method": "legal-section",
                    **legal_metadata
                }
                
                chunk = ChunkMetadata(
                    text=section_text,
                    metadata=chunk_metadata,
                    start_position=section["start_pos"],
                    end_position=section["end_pos"]
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _process_paragraphs(self, content: str, overlap: int) -> List[ChunkMetadata]:
        """Process content as paragraphs when no legal structure is found."""
        chunks = []
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk_paras = []
        current_size = 0
        target_size = 1500
        position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            para_size = len(paragraph)
            
            # Check if adding paragraph exceeds target size
            if current_chunk_paras and current_size + para_size > target_size:
                # Create chunk from current paragraphs
                chunk_text = "\n\n".join(current_chunk_paras)
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "paragraph_count": len(current_chunk_paras),
                    "chunking_method": "paragraph-based",
                    **self._analyze_legal_content(chunk_text)
                }
                
                chunk = ChunkMetadata(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    start_position=position - current_size,
                    end_position=position
                )
                
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_paras = []
                current_size = 0
            
            current_chunk_paras.append(paragraph)
            current_size += para_size
            position += para_size + 2  # +2 for paragraph separator
        
        # Add final chunk
        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "paragraph_count": len(current_chunk_paras),
                "chunking_method": "paragraph-based",
                **self._analyze_legal_content(chunk_text)
            }
            
            chunk = ChunkMetadata(
                text=chunk_text,
                metadata=chunk_metadata,
                start_position=position - current_size,
                end_position=position
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_legal_section(self, section: Dict, overlap: int) -> List[ChunkMetadata]:
        """Split large legal sections into smaller chunks."""
        text = section["text"]
        chunks = []
        
        # Try to split by subsections first
        subsection_pattern = r'^\s*\d+\.\d+\s+'
        subsections = re.split(subsection_pattern, text, flags=re.MULTILINE)
        
        if len(subsections) > 1:
            # Process as subsections
            position = section["start_pos"]
            for i, subsection_text in enumerate(subsections):
                if not subsection_text.strip():
                    continue
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "section_title": section["title"],
                    "subsection_index": i,
                    "is_subsection": True,
                    "chunking_method": "legal-subsection",
                    **self._analyze_legal_content(subsection_text, section)
                }
                
                chunk = ChunkMetadata(
                    text=subsection_text.strip(),
                    metadata=chunk_metadata,
                    start_position=position,
                    end_position=position + len(subsection_text)
                )
                
                chunks.append(chunk)
                position += len(subsection_text)
        else:
            # Split by paragraphs within section
            paragraphs = text.split('\n\n')
            current_chunk = []
            current_size = 0
            
            for paragraph in paragraphs:
                if current_size + len(paragraph) > 1500 and current_chunk:
                    # Create chunk
                    chunk_text = '\n\n'.join(current_chunk)
                    
                    chunk_metadata = {
                        "strategy": self.name,
                        "chunk_index": len(chunks),
                        "section_title": section["title"],
                        "section_part": f"Part {len(chunks) + 1}",
                        "chunking_method": "legal-section-split",
                        **self._analyze_legal_content(chunk_text, section)
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
                
                current_chunk.append(paragraph)
                current_size += len(paragraph)
            
            # Add final chunk
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                
                chunk_metadata = {
                    "strategy": self.name,
                    "chunk_index": len(chunks),
                    "section_title": section["title"],
                    "section_part": f"Part {len(chunks) + 1}",
                    "chunking_method": "legal-section-split",
                    **self._analyze_legal_content(chunk_text, section)
                }
                
                chunk = ChunkMetadata(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    start_position=section["start_pos"],
                    end_position=section["end_pos"]
                )
                
                chunks.append(chunk)
        
        return chunks
    
    def _classify_legal_section(self, text: str) -> str:
        """Classify the type of legal section."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["definition", "definição", "meaning"]):
            return "definitions"
        elif any(word in text_lower for word in ["obligation", "obrigação", "duty", "dever"]):
            return "obligations"
        elif any(word in text_lower for word in ["termination", "rescisão", "end"]):
            return "termination"
        elif any(word in text_lower for word in ["payment", "pagamento", "fee", "taxa"]):
            return "payment"
        elif any(word in text_lower for word in ["liability", "responsabilidade", "damage"]):
            return "liability"
        elif any(word in text_lower for word in ["dispute", "disputa", "arbitration"]):
            return "dispute_resolution"
        elif any(word in text_lower for word in ["governing", "applicable", "law"]):
            return "governing_law"
        else:
            return "general"
    
    def _analyze_legal_content(self, text: str, section: Dict = None) -> Dict[str, Any]:
        """Analyze legal content for metadata."""
        analysis = {}
        
        # Count legal terms
        legal_terms = ["shall", "may", "must", "hereby", "whereas", "therefore", "party", "agreement"]
        analysis["legal_term_count"] = sum(len(re.findall(f'\\b{term}\\b', text, re.IGNORECASE)) for term in legal_terms)
        
        # Detect references
        analysis["has_cross_references"] = bool(re.search(r'Section\s+\d+|Article\s+\d+|paragraph\s+\d+', text, re.IGNORECASE))
        analysis["has_definitions"] = bool(re.search(r'means|shall mean|defined as', text, re.IGNORECASE))
        analysis["has_obligations"] = bool(re.search(r'shall|must|required to', text, re.IGNORECASE))
        
        # Detect dates and numbers
        analysis["has_dates"] = bool(re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', text))
        analysis["has_monetary_amounts"] = bool(re.search(r'\$[\d,]+|\d+\s*(?:dollars?|euros?|reais?)', text, re.IGNORECASE))
        
        # Section classification
        if section:
            analysis["section_type"] = section.get("section_type", "general")
        
        return analysis