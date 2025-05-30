"""
CSV Input Plugin for RAG Document Processor.

This plugin converts CSV files into structured .rag files that can be processed
by the core RAG system. Perfect for product catalogs, contact lists, and any
structured data stored in CSV format.

Features:
- Automatic field mapping to structured blocks
- Empty line separation between records
- Configurable column filtering
- Metadata preservation
- Support for different CSV dialects

Requirements:
- No additional dependencies (uses Python stdlib)

Installation:
    No installation required - uses built-in CSV module

Usage:
    rag-processor convert products.csv --format csv --output products.rag

Example CSV Input:
    Name,Description,Price,Category
    Premium Fan,Handcrafted premium fan,45.90,Home Decor
    Wedding Menu,Elegant wedding menu,12.50,Stationery

Example .rag Output:
    #!/usr/bin/env rag-processor
    #!strategy: structured-blocks/empty-line-separated
    #!metadata: {"source_format": "csv", "rows": 2}

    Name: Premium Fan
    Description: Handcrafted premium fan
    Price: 45.90
    Category: Home Decor

    Name: Wedding Menu
    Description: Elegant wedding menu
    Price: 12.50
    Category: Stationery
"""

from .converter import CSVConverter

__all__ = ["CSVConverter"]
__version__ = "0.1.0"
__plugin_type__ = "input"
__plugin_name__ = "csv"