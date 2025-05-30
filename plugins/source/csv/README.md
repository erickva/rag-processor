# CSV Input Plugin

Convert CSV files to structured .rag format for processing by the RAG Document Processor.

## 🚀 Quick Start

### 1. Basic Conversion

```bash
# Convert CSV to .rag format
rag-processor convert products.csv --format csv

# Specify output file
rag-processor convert products.csv --format csv --output catalog.rag

# Use specific processing strategy
rag-processor convert products.csv --format csv --strategy structured-blocks/empty-line-separated
```

### 2. Example Input/Output

**Input CSV (`products.csv`):**
```csv
Name,Description,Price,Category
Premium Fan,Handcrafted premium fan with golden details,45.90,Home Decor
Wedding Menu,Elegant wedding menu with classic design,12.50,Stationery
Vintage Invitation,Vintage floral invitation for special events,8.75,Invitations
```

**Output .rag (`products.rag`):**
```bash
#!/usr/bin/env rag-processor
#!strategy: structured-blocks/empty-line-separated
#!metadata: {"source_file":"products.csv","source_format":"csv","rows_processed":3,"converted_by":"csv-input-plugin","delimiter":","}

Name: Premium Fan
Description: Handcrafted premium fan with golden details
Price: 45.90
Category: Home Decor

Name: Wedding Menu
Description: Elegant wedding menu with classic design
Price: 12.50
Category: Stationery

Name: Vintage Invitation
Description: Vintage floral invitation for special events
Price: 8.75
Category: Invitations
```

## 📋 Features

- ✅ **Automatic Field Mapping**: CSV columns become field: value pairs
- ✅ **Empty Line Separation**: Each CSV row becomes a separate block
- ✅ **Column Filtering**: Include/exclude specific columns
- ✅ **Data Cleaning**: Automatic cleanup of field names and values
- ✅ **Dialect Detection**: Handles different CSV formats automatically
- ✅ **Validation**: Built-in CSV validation and error reporting
- ✅ **Metadata Preservation**: Tracks conversion details in .rag file

## ⚙️ Advanced Usage

### Column Filtering

```python
from plugins.input.csv import CSVConverter

# Include only specific columns
converter = CSVConverter(include_columns=['Name', 'Price', 'Category'])
converter.convert('products.csv', 'filtered.rag')

# Exclude specific columns
converter = CSVConverter(exclude_columns=['Internal_ID', 'Notes'])
converter.convert('products.csv', 'clean.rag')
```

### Custom Delimiters

```python
# Handle tab-separated values
converter = CSVConverter(delimiter='\t')
converter.convert('data.tsv', 'data.rag')

# Handle semicolon-separated values
converter = CSVConverter(delimiter=';')
converter.convert('european.csv', 'european.rag')
```

### Programmatic Usage

```python
from plugins.input.csv import CSVConverter

# Basic conversion
converter = CSVConverter()
output_file = converter.convert(
    csv_file='products.csv',
    output_file='products.rag',
    strategy='structured-blocks/empty-line-separated',
    source_url='https://example.com/products.csv',
    metadata={'version': '2024-01', 'department': 'sales'}
)

print(f"Converted to: {output_file}")

# Validate CSV before conversion
issues = converter.validate_csv('products.csv')
if issues:
    print("CSV validation issues:")
    for issue in issues:
        print(f"  • {issue}")
else:
    print("✅ CSV is valid")
```

## 🔧 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `delimiter` | str | `,` | CSV delimiter character |
| `skip_empty` | bool | `True` | Skip rows with all empty values |
| `include_columns` | List[str] | None | Only include these columns |
| `exclude_columns` | List[str] | [] | Exclude these columns |

## 📊 Supported Formats

### CSV Dialects
- **Standard CSV**: Comma-separated values
- **TSV**: Tab-separated values
- **European CSV**: Semicolon-separated values
- **Custom delimiters**: Any single character

### Data Types
The plugin handles all data as text, but preserves structure for:
- **Product catalogs**: Name, Description, Price, Category
- **Contact lists**: Name, Email, Phone, Address
- **Inventory**: SKU, Name, Quantity, Location
- **Any structured data**: Flexible field mapping

## ✅ Validation

The plugin validates CSV files for:

```python
converter = CSVConverter()
issues = converter.validate_csv('data.csv')

# Common validation checks:
# - File exists and is readable
# - Valid CSV format
# - Has column headers
# - Contains data rows
# - Not all rows are empty
# - UTF-8 encoding
```

## 🧪 Testing

### Test CSV File

Create a test CSV file:

```bash
cat > test-products.csv << 'EOF'
Name,Description,Price,Category
Test Product 1,A sample product for testing,19.99,Electronics
Test Product 2,Another test product,29.99,Home & Garden
Test Product 3,Final test product,39.99,Sports
EOF
```

### Convert and Process

```bash
# Convert CSV to .rag
rag-processor convert test-products.csv --format csv

# Process the .rag file
rag-processor process test-products.rag

# Upload to vector database
rag-processor upload test-products.rag --to supabase --table test_products
```

## 🐛 Troubleshooting

### Common Issues

**"Invalid CSV format"**
- Check file has proper CSV structure
- Verify delimiter is correct
- Ensure quotes are properly escaped

**"No column headers found"**
- CSV file must have header row
- Check first line contains column names

**"File encoding issue"**
- Ensure CSV file is UTF-8 encoded
- Convert with: `iconv -f ISO-8859-1 -t UTF-8 file.csv > file_utf8.csv`

**"All rows are empty"**
- Check CSV has data beyond headers
- Verify not all cells are empty

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

converter = CSVConverter()
converter.convert('problematic.csv', 'output.rag')
```

## 📈 Performance

### File Size Limits
- **Small files** (< 1MB): Instant conversion
- **Medium files** (1-100MB): Seconds to convert
- **Large files** (100MB+): Minutes, consider splitting

### Memory Usage
- Plugin loads entire CSV into memory
- For very large files, consider splitting first:

```bash
# Split large CSV into smaller files
split -l 10000 large.csv split_
# Convert each split file separately
```

### Optimization Tips

```python
# Skip empty rows for faster processing
converter = CSVConverter(skip_empty=True)

# Filter columns to reduce size
converter = CSVConverter(include_columns=['Name', 'Description', 'Price'])

# Use appropriate strategy for your data
converter.convert('data.csv', strategy='structured-blocks/empty-line-separated')
```

## 🔄 Integration with Core System

After conversion, use standard RAG Processor commands:

```bash
# 1. Convert CSV to .rag
rag-processor convert products.csv --format csv

# 2. Analyze the .rag file
rag-processor analyze products.rag

# 3. Validate the conversion
rag-processor validate products.rag

# 4. Process into chunks
rag-processor process products.rag

# 5. Upload to vector database
rag-processor upload products.rag --to supabase --table products
```

## 📚 Plugin Development

This plugin demonstrates the input plugin interface. Key components:

- **Converter Class**: Handles format-specific conversion logic
- **Validation**: Ensures input quality before conversion
- **Configuration**: Flexible options for different use cases
- **Integration**: Seamless integration with core CLI

See [Plugin Development Guide](../../PLUGIN_DEVELOPMENT.md) for creating similar plugins.

## 📞 Support

- 🐛 **Issues**: File with `[csv-plugin]` tag
- 💬 **Questions**: GitHub Discussions
- 📖 **CSV Format**: [RFC 4180](https://tools.ietf.org/html/rfc4180)
- 🔧 **Python CSV**: [csv module docs](https://docs.python.org/3/library/csv.html)

---

**Transform your CSV data into RAG-ready format!** 📊