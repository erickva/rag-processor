"""
Products processing strategy.

Specialized for product catalogs with semantic boundary chunking
to preserve product integrity. Based on proven success with
Studio Camila Golin's product catalog.
"""

import re
from typing import List, Dict, Any

from .base import ProcessingStrategy
from ..utils.directive_parser import ProcessingDirective
from ..utils.text_utils import ChunkMetadata, TextChunker
from ..clients.base import ClientConfig
from config.constants import PRODUCTS_CHUNK_OVERLAP


class ProductsStrategy(ProcessingStrategy):
    """
    Product catalog processing strategy.
    
    Chunks at semantic boundaries to keep complete products together,
    preventing the fragmentation issues that cause poor RAG performance.
    """
    
    @property
    def name(self) -> str:
        """Strategy name in format 'category/method'."""
        return "products/semantic-boundary"
    
    @property
    def description(self) -> str:
        """Human-readable description of the strategy."""
        return "Product catalog chunking at semantic boundaries to preserve product integrity"
    
    @property
    def default_chunk_pattern(self) -> str:
        """Default regex pattern for product boundaries."""
        return r'(?i)Name:\s*([^\n]*)'  # Matches "Name: Product Name" (case insensitive, allows empty)
    
    @property
    def default_overlap(self) -> int:
        """Default character overlap between chunks."""
        return PRODUCTS_CHUNK_OVERLAP  # No overlap for semantic boundaries
    
    def process(
        self, 
        content: str, 
        directive: ProcessingDirective, 
        client_config: ClientConfig
    ) -> List[ChunkMetadata]:
        """
        Process product catalog content into semantic chunks.
        
        Args:
            content (str): Raw product catalog text content
            directive (ProcessingDirective): Processing directives from document
            client_config (ClientConfig): Client-specific configuration
            
        Returns:
            List[ChunkMetadata]: List of product chunks with metadata
        """
        chunker = TextChunker()
        pattern = self.get_chunk_pattern(directive)
        overlap = self.get_overlap(directive)
        
        # Use intelligent boundary detection - try multiple core patterns
        product_matches = self._find_product_boundaries(content, pattern)
        
        if not product_matches:
            # Fallback to alternative detection methods
            product_matches = self._fallback_boundary_detection(content)
        
        if not product_matches:
            # No product patterns found - use fallback chunking
            return chunker.chunk_by_size(content, 1000, overlap)
        
        chunks = []
        
        for i, match in enumerate(product_matches):
            # Determine chunk boundaries
            start_pos = match.start()
            
            if i < len(product_matches) - 1:
                end_pos = product_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract product text
            product_text = content[start_pos:end_pos].strip()
            
            # Skip empty or very short products
            if len(product_text) < 50:
                continue
            
            # Extract product metadata
            product_metadata = self._extract_product_metadata(product_text, match)
            
            # Validate product completeness if client requires it
            validation_issues = []
            if hasattr(client_config, 'validate_product_completeness'):
                validation_issues = client_config.validate_product_completeness(product_text)
            
            # Create chunk with rich metadata
            chunk_metadata = {
                "strategy": self.name,
                "chunk_index": len(chunks),
                "product_name": product_metadata.get("name", "Unknown"),
                "product_category": product_metadata.get("category"),
                "has_price": product_metadata.get("has_price", False),
                "validation_issues": validation_issues,
                "product_fields": product_metadata.get("fields", []),
                "chunking_method": "semantic-boundary",
                "boundary_pattern": match.group(),
            }
            
            chunk = ChunkMetadata(
                text=product_text,
                metadata=chunk_metadata,
                start_position=start_pos,
                end_position=end_pos
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def validate_content(self, content: str, directive: ProcessingDirective) -> List[str]:
        """
        Validate that content is suitable for product strategy.
        
        Args:
            content (str): Document content to validate
            directive (ProcessingDirective): Processing directives
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        pattern = self.get_chunk_pattern(directive)
        product_matches = re.findall(pattern, content, re.MULTILINE)
        
        if not product_matches:
            issues.append("No product boundaries found using pattern")
        elif len(product_matches) < 2:
            issues.append("Very few products detected - consider different strategy")
        
        # Check for incomplete products
        product_indicators = ["Nome:", "Produto:", "Item:", "Categoria:", "Preço:", "Descrição:"]
        indicator_count = sum(len(re.findall(indicator, content, re.IGNORECASE)) for indicator in product_indicators)
        
        if indicator_count < len(product_matches) * 2:
            issues.append("Products appear incomplete - missing key fields")
        
        return issues
    
    def create_template(self, client_config: ClientConfig) -> str:
        """
        Create a .rag template for product catalogs.
        
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
            "#!strategy: products/semantic-boundary",
            f"#!validation: {client_config.name}/product-catalog",
            "#!chunk-pattern: Nome:\\s*([^\\n]+)",
        ]
        
        # Add metadata
        metadata = {
            "business": client_config.name,
            "type": "product-catalog",
            "version": "1.0",
        }
        metadata.update(client_metadata)
        
        import json
        template_parts.append(f"#!metadata: {json.dumps(metadata, separators=(',', ':'))}")
        
        # Add custom rules if client provides them
        custom_rules = client_config.customize_strategy_config(self.name)
        if custom_rules:
            template_parts.append(f"#!custom-rules: {json.dumps(custom_rules, separators=(',', ':'))}")
        
        # Add example content
        template_parts.extend([
            "",
            "# Product Catalog Template",
            "",
            "Nome: Exemplo de Produto 1",
            "Categoria: Categoria Exemplo",
            "Descrição: Descrição detalhada do produto com características principais.",
            "Preço: R$ 99,99",
            "",
            "Nome: Exemplo de Produto 2", 
            "Categoria: Categoria Exemplo",
            "Descrição: Outra descrição de produto com detalhes específicos.",
            "Preço: R$ 149,90",
            "",
            "# Add your products following the same structure above.",
            "# Each product should start with 'Nome:' followed by the product details.",
        ])
        
        return '\n'.join(template_parts)
    
    def _extract_product_metadata(self, product_text: str, name_match: re.Match) -> Dict[str, Any]:
        """
        Extract metadata from product text.
        
        Args:
            product_text (str): Product text content
            name_match (re.Match): Regex match for product name
            
        Returns:
            Dict[str, Any]: Product metadata
        """
        metadata = {
            "name": name_match.group(1).strip() if len(name_match.groups()) > 0 else "Unknown",
            "fields": [],
            "has_price": False,
        }
        
        # Extract common product fields
        field_patterns = {
            "categoria": r'Categoria:\s*([^\n]+)',
            "description": r'Descrição:\s*([^\n]+)',
            "price": r'(?:Preço|Valor):\s*([^\n]+)',
            "brand": r'Marca:\s*([^\n]+)',
            "model": r'Modelo:\s*([^\n]+)',
        }
        
        for field_name, pattern in field_patterns.items():
            match = re.search(pattern, product_text, re.IGNORECASE)
            if match:
                metadata["fields"].append(field_name)
                if field_name == "categoria":
                    metadata["category"] = match.group(1).strip()
                elif field_name == "price":
                    metadata["has_price"] = True
                    metadata["price"] = match.group(1).strip()
        
        return metadata
    
    def _find_product_boundaries(self, content: str, primary_pattern: str) -> List[re.Match]:
        """
        Find product boundaries using flexible pattern matching.
        
        Tries multiple core patterns to detect product boundaries.
        """
        # Core English patterns (case insensitive, allows empty values)
        core_patterns = [
            primary_pattern,                           # Usually Name: pattern
            r'(?i)Description:\s*([^\n]*)',           # Description field
            r'(?i)Price:\s*([^\n]*)',                 # Price field
            r'(?i)Product:\s*([^\n]*)',               # Alternative product field
            r'(?i)Item:\s*([^\n]*)',                  # Item field
        ]
        
        best_matches = []
        best_count = 0
        
        for pattern in core_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            if len(matches) > best_count:
                best_matches = matches
                best_count = len(matches)
        
        return best_matches
    
    def _fallback_boundary_detection(self, content: str) -> List[re.Match]:
        """
        Fallback boundary detection using empty lines and field repetition.
        """
        # Split by empty lines and find which sections have product-like patterns
        sections = re.split(r'\n\s*\n', content)
        boundaries = []
        
        # Pattern to detect any field: value structure
        field_pattern = r'(?i)^([a-zA-Z][a-zA-Z\s]*?):\s*([^\n]*)'
        
        current_pos = 0
        for section in sections:
            section = section.strip()
            if not section:
                current_pos += 2  # Account for the newlines
                continue
            
            # Check if section has field: value patterns
            field_matches = re.findall(field_pattern, section, re.MULTILINE)
            
            if len(field_matches) >= 1:  # At least one field found
                # Create a fake match at the start of this section
                section_start = content.find(section, current_pos)
                if section_start >= 0:
                    # Create a match object-like tuple
                    match = type('Match', (), {
                        'start': lambda: section_start,
                        'end': lambda: section_start + len(section),
                        'group': lambda x=0: section[:50] if x == 0 else section[:50]
                    })()
                    boundaries.append(match)
            
            current_pos += len(section) + 2
        
        return boundaries