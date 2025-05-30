"""
CSV to .rag converter implementation.

Converts CSV files to structured .rag format with empty-line separated blocks.
"""

import csv
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class CSVConverter:
    """Convert CSV files to structured .rag format."""
    
    def __init__(
        self, 
        delimiter: str = ',',
        skip_empty: bool = True,
        include_columns: Optional[List[str]] = None,
        exclude_columns: Optional[List[str]] = None
    ):
        """
        Initialize CSV converter.
        
        Args:
            delimiter: CSV delimiter character (default: ',')
            skip_empty: Skip rows with all empty values (default: True)
            include_columns: Only include these columns (default: all)
            exclude_columns: Exclude these columns (default: none)
        """
        self.delimiter = delimiter
        self.skip_empty = skip_empty
        self.include_columns = include_columns
        self.exclude_columns = exclude_columns or []
    
    def convert(
        self, 
        csv_file: str, 
        output_file: Optional[str] = None,
        strategy: str = "structured-blocks/empty-line-separated",
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert CSV file to .rag format.
        
        Args:
            csv_file: Path to input CSV file
            output_file: Path to output .rag file (optional)
            strategy: Processing strategy to embed in .rag file
            source_url: Source URL for the original document
            metadata: Additional metadata for .rag file
            
        Returns:
            str: Path to created .rag file
        """
        # Read and process CSV
        rows_data = self._read_csv(csv_file)
        
        if not rows_data:
            raise ValueError(f"No valid data found in CSV file: {csv_file}")
        
        # Convert to structured blocks
        content = self._create_structured_content(rows_data)
        
        # Generate .rag file content
        rag_content = self._create_rag_content(
            content, strategy, source_url, metadata, csv_file, len(rows_data)
        )
        
        # Write .rag file
        if not output_file:
            output_file = Path(csv_file).with_suffix('.rag')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rag_content)
        
        return str(output_file)
    
    def _read_csv(self, csv_file: str) -> List[Dict[str, str]]:
        """Read CSV file and return list of row dictionaries."""
        rows_data = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            # Detect dialect
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=self.delimiter)
            
            reader = csv.DictReader(f, dialect=dialect)
            
            for row_num, row in enumerate(reader, 1):
                # Filter columns if specified
                filtered_row = self._filter_columns(row)
                
                # Skip empty rows if configured
                if self.skip_empty and self._is_empty_row(filtered_row):
                    continue
                
                # Clean up values
                cleaned_row = {k: str(v).strip() for k, v in filtered_row.items() if k}
                
                if cleaned_row:
                    rows_data.append(cleaned_row)
        
        return rows_data
    
    def _filter_columns(self, row: Dict[str, str]) -> Dict[str, str]:
        """Filter columns based on include/exclude lists."""
        filtered = {}
        
        for key, value in row.items():
            # Skip if column should be excluded
            if key in self.exclude_columns:
                continue
            
            # Include only specified columns (if list provided)
            if self.include_columns and key not in self.include_columns:
                continue
            
            filtered[key] = value
        
        return filtered
    
    def _is_empty_row(self, row: Dict[str, str]) -> bool:
        """Check if row has all empty values."""
        return all(not str(value).strip() for value in row.values())
    
    def _create_structured_content(self, rows_data: List[Dict[str, str]]) -> str:
        """Create structured content with empty-line separated blocks."""
        blocks = []
        
        for row in rows_data:
            # Convert each row to field: value format
            block_lines = []
            
            for key, value in row.items():
                if value:  # Only include non-empty values
                    # Clean up field name (remove special characters, capitalize)
                    clean_key = self._clean_field_name(key)
                    block_lines.append(f"{clean_key}: {value}")
            
            if block_lines:
                blocks.append('\n'.join(block_lines))
        
        return '\n\n'.join(blocks)
    
    def _clean_field_name(self, field_name: str) -> str:
        """Clean up field name for .rag format."""
        # Remove special characters, replace underscores with spaces, capitalize
        clean_name = field_name.replace('_', ' ').replace('-', ' ')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c.isspace())
        return clean_name.strip().title()
    
    def _create_rag_content(
        self, 
        content: str, 
        strategy: str, 
        source_url: Optional[str],
        metadata: Optional[Dict[str, Any]], 
        csv_file: str,
        row_count: int
    ) -> str:
        """Create complete .rag file content with directives."""
        header_lines = [
            "#!/usr/bin/env rag-processor",
            f"#!strategy: {strategy}",
        ]
        
        # Add source URL if provided
        if source_url:
            header_lines.append(f"#!source-url: {source_url}")
        
        # Create metadata
        file_metadata = {
            "source_file": str(Path(csv_file).name),
            "source_format": "csv",
            "rows_processed": row_count,
            "converted_by": "csv-input-plugin",
            "delimiter": self.delimiter,
        }
        
        # Add custom metadata
        if metadata:
            file_metadata.update(metadata)
        
        header_lines.append(f"#!metadata: {json.dumps(file_metadata, separators=(',', ':'))}")
        
        # Combine header and content
        return '\n'.join(header_lines) + '\n\n' + content
    
    @property
    def format_name(self) -> str:
        """Name of the input format this converter handles."""
        return "csv"
    
    @property
    def supported_extensions(self) -> List[str]:
        """List of file extensions this converter supports."""
        return [".csv", ".tsv"]
    
    def validate_csv(self, csv_file: str) -> List[str]:
        """
        Validate CSV file and return list of issues.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Check if file is empty
                if not f.read().strip():
                    issues.append("CSV file is empty")
                    return issues
                
                f.seek(0)
                
                # Try to read as CSV
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample, delimiters=self.delimiter)
                except csv.Error as e:
                    issues.append(f"Invalid CSV format: {e}")
                    return issues
                
                reader = csv.DictReader(f, dialect=dialect)
                
                # Check for headers
                if not reader.fieldnames:
                    issues.append("No column headers found")
                    return issues
                
                # Check for data rows
                row_count = 0
                empty_rows = 0
                
                for row in reader:
                    row_count += 1
                    if self._is_empty_row(row):
                        empty_rows += 1
                
                if row_count == 0:
                    issues.append("No data rows found")
                elif empty_rows == row_count:
                    issues.append("All rows are empty")
                elif empty_rows > row_count * 0.5:
                    issues.append(f"Many empty rows found ({empty_rows}/{row_count})")
                
        except FileNotFoundError:
            issues.append(f"File not found: {csv_file}")
        except PermissionError:
            issues.append(f"Permission denied: {csv_file}")
        except UnicodeDecodeError:
            issues.append("File encoding issue - not valid UTF-8")
        except Exception as e:
            issues.append(f"Unexpected error: {e}")
        
        return issues