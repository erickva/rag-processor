"""
RAG Processor Plugin System.

This package contains all official and community plugins for the RAG Document Processor.
Plugins extend functionality for input formats and output destinations.

Plugin Types:
- Input Plugins: Convert various formats (PDF, DOCX, CSV, etc.) to .rag files
- Delivery Plugins: Upload processed chunks to vector databases (Supabase, Pinecone, etc.)

Plugin Structure:
- plugins/input/{plugin_name}/
- plugins/delivery/{plugin_name}/

Each plugin is self-contained with its own dependencies, configuration, and documentation.
"""

__version__ = "0.1.0"