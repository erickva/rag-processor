"""
Integration tests for CLI interface.

Tests command-line interface functionality and output formats.
"""

import pytest
import json
import subprocess
import sys
from pathlib import Path


class TestCLIInterface:
    """Integration test cases for CLI interface."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "RAG Document Processing System" in result.stdout
        assert "analyze" in result.stdout
        assert "validate" in result.stdout
        assert "process" in result.stdout
        assert "create-template" in result.stdout
    
    def test_cli_version(self):
        """Test CLI version output."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "0.1.0" in result.stdout
    
    def test_cli_analyze_command(self, create_temp_file, sample_product_catalog):
        """Test CLI analyze command."""
        test_file = create_temp_file(sample_product_catalog)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "analyze", str(test_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            assert "Document Type:" in result.stdout
            assert "Confidence:" in result.stdout
            assert "Recommended Strategy:" in result.stdout
        
        finally:
            test_file.unlink()
    
    def test_cli_analyze_json_output(self, create_temp_file, sample_product_catalog):
        """Test CLI analyze command with JSON output."""
        test_file = create_temp_file(sample_product_catalog)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "analyze", str(test_file), "--format", "json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            
            # Should be valid JSON
            output_data = json.loads(result.stdout)
            assert "document_type" in output_data
            assert "confidence" in output_data
            assert "recommended_strategy" in output_data
        
        finally:
            test_file.unlink()
    
    def test_cli_validate_command(self, create_temp_file, sample_rag_file):
        """Test CLI validate command."""
        test_file = create_temp_file(sample_rag_file, suffix=".rag")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "validate", str(test_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            assert "Document Validation Report" in result.stdout
            assert "VALID" in result.stdout
        
        finally:
            test_file.unlink()
    
    def test_cli_process_command(self, create_temp_file, sample_rag_file):
        """Test CLI process command."""
        test_file = create_temp_file(sample_rag_file, suffix=".rag")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "process", str(test_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            assert "Document Processing Results" in result.stdout
            assert "Strategy Used:" in result.stdout
            assert "Total Chunks:" in result.stdout
        
        finally:
            test_file.unlink()
    
    def test_cli_process_json_output(self, create_temp_file, sample_rag_file):
        """Test CLI process command with JSON output."""
        test_file = create_temp_file(sample_rag_file, suffix=".rag")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "process", str(test_file), "--format", "json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            
            # Should be valid JSON
            output_data = json.loads(result.stdout)
            assert "chunks" in output_data
            assert "total_chunks" in output_data
            assert "strategy_used" in output_data
            assert len(output_data["chunks"]) > 0
        
        finally:
            test_file.unlink()
    
    def test_cli_create_template_command(self, temp_dir):
        """Test CLI create-template command."""
        output_file = temp_dir / "test_template.rag"
        
        result = subprocess.run(
            [
                sys.executable, "-m", "rag_processor", 
                "create-template", "product-catalog",
                "--client", "studio-camila-golin",
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Template created successfully" in result.stdout
        assert output_file.exists()
        
        # Check template content
        template_content = output_file.read_text()
        assert template_content.startswith("#!/usr/bin/env rag-processor")
        assert "#!strategy: products/semantic-boundary" in template_content
        assert "Nome: Exemplo de Produto" in template_content
    
    def test_cli_list_strategies(self):
        """Test CLI list strategies command."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "list", "strategies"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Available Processing Strategies" in result.stdout
        assert "products/semantic-boundary" in result.stdout
        assert "manual/section-based" in result.stdout
        assert "faq/qa-pairs" in result.stdout
    
    def test_cli_list_clients(self):
        """Test CLI list clients command."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "list", "clients"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Available Client Configurations" in result.stdout
        assert "default" in result.stdout
        assert "studio-camila-golin" in result.stdout
    
    def test_cli_list_document_types(self):
        """Test CLI list document-types command."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "list", "document-types"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Supported Document Types" in result.stdout
        assert "product-catalog" in result.stdout
        assert "user-manual" in result.stdout
        assert "faq" in result.stdout
    
    def test_cli_error_handling_file_not_found(self):
        """Test CLI error handling for non-existent file."""
        result = subprocess.run(
            [sys.executable, "-m", "rag_processor", "analyze", "non_existent_file.txt"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 1
        assert "File not found" in result.stderr
    
    def test_cli_verbose_mode(self, create_temp_file, sample_product_catalog):
        """Test CLI verbose mode."""
        test_file = create_temp_file(sample_product_catalog)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "--verbose", "analyze", str(test_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            assert "Analyzing document:" in result.stdout
        
        finally:
            test_file.unlink()
    
    def test_cli_output_to_file(self, create_temp_file, sample_product_catalog, temp_dir):
        """Test CLI output to file."""
        test_file = create_temp_file(sample_product_catalog)
        output_file = temp_dir / "analysis_output.json"
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "rag_processor", 
                    "analyze", str(test_file),
                    "--format", "json",
                    "--output", str(output_file)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0
            assert output_file.exists()
            
            # Check output file content
            output_data = json.loads(output_file.read_text())
            assert "document_type" in output_data
            assert "confidence" in output_data
        
        finally:
            test_file.unlink()


class TestCLIValidation:
    """Test CLI validation scenarios."""
    
    def test_cli_validate_invalid_document(self, create_temp_file):
        """Test CLI validation of invalid document."""
        invalid_rag = '''#!/usr/bin/env rag-processor
#!strategy: invalid-format
#!chunk-pattern: [invalid regex

Too short content.
'''
        
        test_file = create_temp_file(invalid_rag, suffix=".rag")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "rag_processor", "validate", str(test_file)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 1  # Should fail validation
            assert "Validation failed" in result.stderr
        
        finally:
            test_file.unlink()
    
    def test_cli_validation_report_output(self, create_temp_file, temp_dir):
        """Test CLI validation with report output."""
        invalid_rag = '''#!/usr/bin/env rag-processor
#!strategy: products/semantic-boundary

Very short content that will fail validation.
'''
        
        test_file = create_temp_file(invalid_rag, suffix=".rag")
        report_file = temp_dir / "validation_report.txt"
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "rag_processor", 
                    "validate", str(test_file),
                    "--report", str(report_file)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 1
            assert report_file.exists()
            
            # Check report content
            report_content = report_file.read_text()
            assert "Document Validation Report" in report_content
            assert "INVALID" in report_content
        
        finally:
            test_file.unlink()


class TestCLIWorkflows:
    """Test complete CLI workflows."""
    
    def test_template_to_processing_workflow(self, temp_dir):
        """Test complete workflow from template creation to processing."""
        template_file = temp_dir / "workflow_test.rag"
        
        # Step 1: Create template
        result1 = subprocess.run(
            [
                sys.executable, "-m", "rag_processor",
                "create-template", "product-catalog",
                "--client", "studio-camila-golin",
                "--output", str(template_file)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result1.returncode == 0
        assert template_file.exists()
        
        # Step 2: Modify template with real content
        template_content = template_file.read_text()
        real_content = template_content.replace(
            "Nome: Exemplo de Produto 1",
            "Nome: Produto Real de Teste"
        ).replace(
            "Nome: Exemplo de Produto 2",
            "Nome: Segundo Produto Real"
        )
        template_file.write_text(real_content)
        
        # Step 3: Validate the modified file
        result2 = subprocess.run(
            [sys.executable, "-m", "rag_processor", "validate", str(template_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result2.returncode == 0
        
        # Step 4: Process the file
        result3 = subprocess.run(
            [
                sys.executable, "-m", "rag_processor", 
                "process", str(template_file),
                "--format", "json"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result3.returncode == 0
        
        # Check final output
        output_data = json.loads(result3.stdout)
        assert "chunks" in output_data
        assert len(output_data["chunks"]) >= 2
        assert output_data["strategy_used"] == "products/semantic-boundary"