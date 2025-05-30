"""
RAG Document Processor CLI entry point.

Command-line interface for the RAG Document Processing System.
Supports analyze, validate, create-template, and process commands.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

from .core.processor import RAGDocumentProcessor
from .core.analyzer import DocumentType
from .core.validator import ValidationLevel
from config.constants import (
    DEFAULT_OUTPUT_FORMAT, TEMPLATE_OUTPUT_DIR, ANALYSIS_OUTPUT_DIR,
    SUCCESS_DOCUMENT_PROCESSED, SUCCESS_VALIDATION_PASSED, SUCCESS_TEMPLATE_CREATED,
    DEFAULT_EMBEDDING_MODEL
)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        prog="rag-processor",
        description="RAG Document Processing System - Intelligent document chunking for optimal RAG performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rag-processor analyze document.txt
  rag-processor validate document.rag
  rag-processor process document.rag --output chunks.json
  rag-processor create-template product-catalog --output catalog.rag
  
For more information, visit: https://github.com/rag-processor/rag-processor
        """
    )
    
    # Global options
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml", "text"],
        default=DEFAULT_OUTPUT_FORMAT,
        help=f"Output format (default: {DEFAULT_OUTPUT_FORMAT})"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze document to determine type and processing recommendations"
    )
    analyze_parser.add_argument(
        "file",
        help="Path to document file to analyze"
    )
    analyze_parser.add_argument(
        "--output", "-o",
        help="Output file for analysis results"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate .rag document against processing strategy"
    )
    validate_parser.add_argument(
        "file",
        help="Path to .rag document file to validate"
    )
    validate_parser.add_argument(
        "--report", "-r",
        help="Output file for validation report"
    )
    
    # Process command
    process_parser = subparsers.add_parser(
        "process",
        help="Process .rag document into chunks"
    )
    process_parser.add_argument(
        "file",
        help="Path to .rag document file to process"
    )
    process_parser.add_argument(
        "--output", "-o",
        help="Output file for processed chunks"
    )
    process_parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include full metadata in output"
    )
    
    # Create template command
    template_parser = subparsers.add_parser(
        "create-template",
        help="Create .rag template for document type"
    )
    template_parser.add_argument(
        "document_type",
        choices=[
            "product-catalog", "user-manual", "faq", 
            "article", "legal-document", "code-documentation"
        ],
        help="Type of document template to create"
    )
    template_parser.add_argument(
        "--output", "-o",
        help="Output file for template (default: template.rag)"
    )
    
    # Upload command (the real value!)
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload document directly to vector database with chunking and embeddings"
    )
    upload_parser.add_argument(
        "file",
        help="Path to document file to upload"
    )
    upload_parser.add_argument(
        "--to",
        required=True,
        choices=["supabase", "pinecone", "weaviate"],
        help="Vector database destination"
    )
    upload_parser.add_argument(
        "--table",
        required=True,
        help="Database table/collection name"
    )
    upload_parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"OpenAI embedding model (default: {DEFAULT_EMBEDDING_MODEL})"
    )
    upload_parser.add_argument(
        "--metadata",
        help="Additional metadata as JSON string"
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available strategies and document types"
    )
    list_parser.add_argument(
        "type",
        choices=["strategies", "document-types"],
        help="What to list"
    )
    
    return parser


def main():
    """Main CLI entry point."""
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        processor = RAGDocumentProcessor()
        
        if args.command == "analyze":
            handle_analyze(processor, args)
        elif args.command == "validate":
            handle_validate(processor, args)
        elif args.command == "process":
            handle_process(processor, args)
        elif args.command == "create-template":
            handle_create_template(processor, args)
        elif args.command == "upload":
            handle_upload(processor, args)
        elif args.command == "list":
            handle_list(processor, args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_analyze(processor: RAGDocumentProcessor, args):
    """Handle analyze command."""
    
    if args.verbose:
        print(f"Analyzing document: {args.file}")
    
    analysis = processor.analyze_document(args.file)
    
    # Prepare output
    output_data = {
        "document_type": analysis.document_type.value,
        "confidence": analysis.confidence,
        "recommended_strategy": analysis.recommended_strategy,
        "detected_patterns": analysis.detected_patterns,
        "analysis_details": analysis.analysis_details,
    }
    
    # Format and output
    if args.format == "json":
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif args.format == "yaml":
        import yaml
        output_text = yaml.dump(output_data, default_flow_style=False)
    else:  # text format
        output_text = format_analysis_text(analysis)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        if args.verbose:
            print(f"Analysis saved to: {args.output}")
    else:
        print(output_text)


def handle_validate(processor: RAGDocumentProcessor, args):
    """Handle validate command."""
    
    if args.verbose:
        print(f"Validating document: {args.file}")
    
    validation = processor.validate_document(args.file)
    
    # Generate report
    if args.format == "text" or args.report:
        report_text = processor.validator.generate_validation_report(validation)
    
    if args.format == "json":
        output_data = {
            "is_valid": validation.is_valid,
            "score": validation.score,
            "error_count": validation.error_count,
            "warning_count": validation.warning_count,
            "info_count": validation.info_count,
            "issues": [
                {
                    "level": issue.level.value,
                    "message": issue.message,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in validation.issues
            ],
            "metadata": validation.metadata,
        }
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif args.format == "yaml":
        import yaml
        output_data = {
            "is_valid": validation.is_valid,
            "score": validation.score,
            "issues": [
                {
                    "level": issue.level.value,
                    "message": issue.message,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in validation.issues
            ]
        }
        output_text = yaml.dump(output_data, default_flow_style=False)
    else:  # text format
        output_text = report_text
    
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report_text)
        if args.verbose:
            print(f"Validation report saved to: {args.report}")
    
    if not args.report or args.verbose:
        print(output_text)
    
    # Exit with error code if validation failed
    if not validation.is_valid:
        print(f"\n❌ Validation failed with {validation.error_count} errors", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ {SUCCESS_VALIDATION_PASSED}")


def handle_process(processor: RAGDocumentProcessor, args):
    """Handle process command."""
    
    if args.verbose:
        print(f"Processing document: {args.file}")
    
    result = processor.process_file(args.file)
    
    # Prepare output
    if args.include_metadata:
        output_data = {
            "chunks": [
                {
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                }
                for chunk in result.chunks
            ],
            "processing_info": {
                "strategy_used": result.strategy_used,
                "processing_time": result.processing_time,
                "analysis": {
                    "document_type": result.analysis.document_type.value,
                    "confidence": result.analysis.confidence,
                },
                "validation": {
                    "is_valid": result.validation.is_valid,
                    "score": result.validation.score,
                    "error_count": result.validation.error_count,
                },
                "metadata": result.metadata,
            }
        }
    else:
        output_data = {
            "chunks": [chunk.text for chunk in result.chunks],
            "total_chunks": len(result.chunks),
            "strategy_used": result.strategy_used,
        }
    
    # Format output
    if args.format == "json":
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif args.format == "yaml":
        import yaml
        output_text = yaml.dump(output_data, default_flow_style=False)
    else:  # text format
        output_text = format_processing_text(result, args.include_metadata)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        if args.verbose:
            print(f"Processing results saved to: {args.output}")
    else:
        print(output_text)
    
    if args.verbose:
        print(f"\n✅ {SUCCESS_DOCUMENT_PROCESSED}")
        print(f"Generated {len(result.chunks)} chunks using {result.strategy_used} strategy")
        print(f"Processing time: {result.processing_time:.2f} seconds")


def handle_create_template(processor: RAGDocumentProcessor, args):
    """Handle create-template command."""
    
    # Map command line types to enum values
    type_mapping = {
        "product-catalog": DocumentType.PRODUCT_CATALOG,
        "user-manual": DocumentType.USER_MANUAL,
        "faq": DocumentType.FAQ,
        "article": DocumentType.ARTICLE,
        "legal-document": DocumentType.LEGAL_DOCUMENT,
        "code-documentation": DocumentType.CODE_DOCUMENTATION,
    }
    
    document_type = type_mapping[args.document_type]
    
    if args.verbose:
        print(f"Creating {args.document_type} template")
    
    template_content = processor.create_template(document_type)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = f"{args.document_type}.rag"
    
    # Write template
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✅ {SUCCESS_TEMPLATE_CREATED}: {output_file}")
    
    if args.verbose:
        print(f"Template type: {args.document_type}")
        print(f"Client config: {args.client}")
        print(f"File size: {len(template_content)} characters")


def handle_upload(processor: RAGDocumentProcessor, args):
    """Handle upload command - the real value!"""
    
    # Require .rag files with embedded directives
    if not args.file.endswith('.rag'):
        print("❌ Upload requires .rag files with embedded directives", file=sys.stderr)
        print("💡 Create a .rag file first or use: rag-processor create-template", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        print(f"🚀 Uploading {args.file} to {args.to}/{args.table}")
        print(f"Embedding model: {args.embedding_model}")
    
    # Import delivery components
    from .delivery.openai_embeddings import OpenAIEmbeddingProvider
    from .delivery.supabase_provider import SupabaseProvider
    
    try:
        # Initialize embedding provider
        embedding_provider = OpenAIEmbeddingProvider(model=args.embedding_model)
        
        # Initialize delivery provider
        if args.to == "supabase":
            delivery_provider = SupabaseProvider(embedding_provider)
        else:
            raise ValueError(f"Delivery provider '{args.to}' not yet implemented")
        
        # Connect to provider
        if args.verbose:
            print("🔌 Connecting to vector database...")
        
        if not delivery_provider.connect():
            print(f"❌ Failed to connect to {args.to}", file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print("✅ Connected successfully")
        
        # Process .rag file (strategy is embedded in the file)
        if args.verbose:
            print("📄 Processing .rag file into chunks...")
        
        result = processor.process_file(args.file)
        
        if args.verbose:
            print(f"📦 Generated {len(result.chunks)} chunks using {result.strategy_used}")
            print(f"📊 Document type: {result.analysis.document_type.value} ({result.analysis.confidence:.2f} confidence)")
        
        # Parse additional metadata if provided
        additional_metadata = {}
        if args.metadata:
            import json
            additional_metadata = json.loads(args.metadata)
        
        # Upload to vector database
        if args.verbose:
            print("⬆️  Uploading chunks with embeddings...")
        
        delivery_result = delivery_provider.upload_chunks(
            result.chunks,
            args.table,
            additional_metadata
        )
        
        # Report results
        if delivery_result.success:
            print(f"✅ Successfully uploaded {delivery_result.chunks_uploaded} chunks to {args.to}://{args.table}")
            
            if args.verbose:
                print(f"📈 Embedding model: {delivery_result.metadata.get('embedding_model', 'unknown')}")
                print(f"📐 Embedding dimension: {delivery_result.metadata.get('embedding_dimension', 'unknown')}")
                print(f"🔄 Batches processed: {delivery_result.metadata.get('batches_processed', 'unknown')}")
                
                # Show source URL if available
                from .utils.directive_parser import DirectiveParser
                parser = DirectiveParser()
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
                directive = parser.parse(content)
                if directive.source_url:
                    print(f"🔗 Source document: {directive.source_url}")
            
            if delivery_result.errors:
                print(f"⚠️  {len(delivery_result.errors)} warnings:")
                for error in delivery_result.errors:
                    print(f"  • {error}")
        else:
            print(f"❌ Upload failed to {args.to}://{args.table}", file=sys.stderr)
            for error in delivery_result.errors:
                print(f"  • {error}", file=sys.stderr)
            sys.exit(1)
    
    except ImportError as e:
        if "openai" in str(e):
            print("❌ OpenAI package required. Install with: pip install openai", file=sys.stderr)
        elif "supabase" in str(e):
            print("❌ Supabase package required. Install with: pip install supabase", file=sys.stderr)
        else:
            print(f"❌ Missing dependency: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Upload failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def handle_list(processor: RAGDocumentProcessor, args):
    """Handle list command."""
    
    if args.type == "strategies":
        strategies = processor.get_available_strategies()
        print("Available Processing Strategies:")
        print("=" * 35)
        for strategy in strategies:
            strategy_obj = processor.strategies[strategy]
            print(f"• {strategy}")
            print(f"  Description: {strategy_obj.description}")
            print(f"  Pattern: {strategy_obj.default_chunk_pattern}")
            print(f"  Overlap: {strategy_obj.default_overlap} chars")
            print()
    
    elif args.type == "clients":
        clients = processor.get_available_clients()
        print("Available Client Configurations:")
        print("=" * 35)
        for client in clients:
            client_obj = processor.client_configs[client]
            print(f"• {client}")
            print(f"  Description: {client_obj.description}")
            print()
    
    elif args.type == "document-types":
        print("Supported Document Types:")
        print("=" * 25)
        type_descriptions = {
            "product-catalog": "Product catalogs with semantic boundaries",
            "user-manual": "User manuals with section-based structure",
            "faq": "FAQ documents with Q&A pairs",
            "article": "Articles with sentence-based chunking",
            "legal-document": "Legal documents with paragraph structure",
            "code-documentation": "Code documentation with function boundaries",
        }
        
        for doc_type, description in type_descriptions.items():
            print(f"• {doc_type}")
            print(f"  {description}")
            print()


def format_analysis_text(analysis) -> str:
    """Format analysis results as readable text."""
    
    lines = []
    lines.append("# Document Analysis Results")
    lines.append("=" * 30)
    lines.append(f"Document Type: {analysis.document_type.value}")
    lines.append(f"Confidence: {analysis.confidence:.3f}")
    lines.append(f"Recommended Strategy: {analysis.recommended_strategy}")
    lines.append("")
    
    if analysis.detected_patterns:
        lines.append("Detected Patterns:")
        for pattern, count in analysis.detected_patterns.items():
            lines.append(f"  • {pattern}: {count} matches")
        lines.append("")
    
    lines.append("Analysis Details:")
    for key, value in analysis.analysis_details.items():
        if isinstance(value, dict):
            lines.append(f"  {key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"    {sub_key}: {sub_value}")
        else:
            lines.append(f"  {key}: {value}")
    
    return '\n'.join(lines)


def format_processing_text(result, include_metadata: bool) -> str:
    """Format processing results as readable text."""
    
    lines = []
    lines.append("# Document Processing Results")
    lines.append("=" * 30)
    lines.append(f"Strategy Used: {result.strategy_used}")
    lines.append(f"Total Chunks: {len(result.chunks)}")
    lines.append(f"Processing Time: {result.processing_time:.2f} seconds")
    lines.append("")
    
    if include_metadata:
        lines.append("Processing Details:")
        lines.append(f"  Document Type: {result.analysis.document_type.value}")
        lines.append(f"  Analysis Confidence: {result.analysis.confidence:.3f}")
        lines.append(f"  Validation Valid: {result.validation.is_valid}")
        lines.append(f"  Validation Score: {result.validation.score:.2f}")
        lines.append("")
    
    lines.append("Chunks:")
    lines.append("-" * 10)
    
    for i, chunk in enumerate(result.chunks):
        lines.append(f"\n[Chunk {i + 1}]")
        if include_metadata:
            lines.append(f"Length: {len(chunk.text)} chars")
            lines.append(f"Position: {chunk.start_position}-{chunk.end_position}")
        
        # Show first 200 characters of chunk
        preview = chunk.text[:200]
        if len(chunk.text) > 200:
            preview += "..."
        lines.append(f"Content: {preview}")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    main()