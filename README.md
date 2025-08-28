# sumry

A CLI utility tool for summarizing various data sources.

## Features

- **Multi-format support**: CSV, Excel (.xlsx, .xls, .xlsm), GeoJSON, and Shapefiles
- **Beautiful output**: Rich-formatted tables and panels for clear, readable summaries
- **JSON output**: Export summaries as JSON for programmatic use with `--json` flag
- **Verbose mode**: Additional statistics and sample data with `-v` flag
- **Sample records**: Display sample data rows with `--count` option
- **Sheet selection**: Choose specific Excel sheets with `--select` option
- **Fast and lightweight**: Built with performance in mind
- **Clean output**: No unnecessary warnings or library messages in standard mode

## Installation

This project uses UV as the package manager. To install dependencies:

```bash
# Clone the repository
git clone <repository-url>
cd sumry

# Install dependencies with UV
uv sync
```

## Usage

### Basic usage

```bash
# Summarize a CSV file
uv run sumry data.csv

# Summarize a GeoJSON file
uv run sumry locations.geojson

# Summarize an Excel file
uv run sumry spreadsheet.xlsx

# Summarize a Shapefile
uv run sumry boundaries.shp
```

### Command-line Options

```bash
# Verbose mode - show additional statistics and sample values
uv run sumry data.csv --verbose
uv run sumry data.csv -v

# Display sample records (default: 5 rows)
uv run sumry data.csv --count 10
uv run sumry data.csv -n 10

# Select specific Excel sheets
uv run sumry spreadsheet.xlsx --select "Sheet1,Sheet3"
uv run sumry spreadsheet.xlsx -s "Sheet1"

# Output as JSON
uv run sumry data.csv --json
uv run sumry data.csv -j

# Combine options
uv run sumry data.csv -v -n 5 --json
```

## Output Examples

### Standard Output (CSV)
```
mn
 CSV File Summary 
po
  File            sample.csv  
  Rows            10          
  Columns         4           
  Memory Usage    1.44 KB     

Columns/Fields:
 Name    Type   
 name    object 
 age     int64  
 city    object 
 salary  int64
```

### Verbose Output (CSV)
Includes sample values and statistics for each column:
- Numeric columns: min, max, mean, unique count
- Text columns: unique count, most common value
- Sample values: first 3 non-null values

### JSON Output
Export summaries in JSON format for integration with other tools:

```bash
# Output JSON to file
uv run sumry data.csv --json > summary.json

# Pipe to jq for processing
uv run sumry data.csv --json | jq '.columns[] | .name'

# Get just the basic info
uv run sumry data.csv --json | jq '.basic_info'
```

JSON output includes:
- Basic file information (rows, columns, memory usage)
- Column names and types
- Statistics (when using verbose mode)
- Sample data (when using count option)

### GeoJSON/Shapefile Output
Includes additional geometry information:
- Geometry types and counts
- Bounding box coordinates
- Total area (for polygons)
- Total length (for lines)
- Coordinate Reference System (CRS)

## CLI Options Reference

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--verbose` | `-v` | Show detailed statistics and sample values | `sumry data.csv -v` |
| `--count N` | `-n N` | Display N sample records in table format | `sumry data.csv -n 10` |
| `--select` | `-s` | Select specific Excel sheets (comma-separated) | `sumry file.xlsx -s "Sheet1,Sheet2"` |
| `--json` | `-j` | Output results in JSON format | `sumry data.csv -j` |
| `--help` | | Show help message and exit | `sumry --help` |

## Supported Formats

| Format | Extensions | Description |
|--------|------------|-------------|
| CSV | .csv, .tsv | Comma and tab-separated values |
| Excel | .xlsx, .xls, .xlsm | Microsoft Excel spreadsheets |
| GeoJSON | .geojson, .json | Geographic JSON format |
| Shapefile | .shp | ESRI Shapefile format |

## Dependencies

- **typer**: CLI framework
- **rich**: Terminal formatting and styling
- **pandas**: Data processing for CSV and Excel files
- **geopandas**: Geospatial data processing
- **openpyxl**: Excel file support
- **shapely**: Geometric operations
- **pyproj**: Coordinate system transformations

## Development

```bash
# Install in development mode
uv sync

# Run tests (if available)
uv run pytest

# Build the package
uv build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Sparkgeo

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
