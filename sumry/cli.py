import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import warnings
import os

from sumry.readers import (
    read_csv,
    read_excel,
    read_geojson,
    read_shapefile,
    detect_file_type
)

app = typer.Typer(
    name="sumry",
    help="Summarize various data sources (CSV, Excel, GeoJSON, Shapefiles)",
    add_completion=False
)

console = Console()


@app.command()
def main(
    file_path: Path = typer.Argument(
        ...,
        help="Path to the file to summarize",
        exists=True
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v",
        help="Show detailed information"
    ),
    select: Optional[str] = typer.Option(
        None,
        "--select",
        "-s",
        help="Select specific components (e.g., sheet names for Excel, separated by commas)"
    ),
    count: Optional[int] = typer.Option(
        None,
        "--count",
        "-n",
        help="Display N sample records in table format (default: 5)"
    )
):
    """
    Summarize a data file (CSV, Excel, GeoJSON, or Shapefile).
    """
    
    # Suppress warnings and verbose output in non-verbose mode
    if not verbose:
        warnings.filterwarnings('ignore')
        os.environ['PYOGRIO_USE_ARROW'] = '0'  # Suppress pyogrio Arrow warnings
    
    if not file_path.exists():
        console.print(f"[bold red]Error:[/bold red] File {file_path} does not exist")
        raise typer.Exit(1)
    
    file_type = detect_file_type(file_path)
    
    if not file_type:
        console.print(f"[bold red]Error:[/bold red] Unsupported file type for {file_path}")
        raise typer.Exit(1)
    
    try:
        # Set default count to 5 if count option is used without value
        sample_count = 5 if count is not None and count <= 0 else count
        
        if file_type == "CSV":
            summary = read_csv(file_path, verbose, sample_count)
        elif file_type == "Excel":
            summary = read_excel(file_path, verbose, select, sample_count)
        elif file_type == "GeoJSON":
            summary = read_geojson(file_path, verbose, sample_count)
        elif file_type == "Shapefile":
            summary = read_shapefile(file_path, verbose, sample_count)
        else:
            console.print(f"[bold red]Error:[/bold red] Handler not implemented for {file_type}")
            raise typer.Exit(1)
            
        display_summary(summary, file_type, verbose, sample_count)
        
    except Exception as e:
        console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
        raise typer.Exit(1)


def display_summary(summary: dict, file_type: str, verbose: bool, sample_count: Optional[int] = None):
    """Display the file summary using Rich formatting."""
    
    panel = Panel.fit(
        f"[bold green]{file_type} File Summary[/bold green]",
        border_style="cyan"
    )
    console.print(panel)
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    for key, value in summary.get("basic_info", {}).items():
        if isinstance(value, (list, dict)):
            value_str = str(value)
        else:
            value_str = str(value)
        table.add_row(key, value_str)
    
    console.print(table)
    
    # Handle multiple sheets if present
    if "sheets" in summary:
        for sheet_name, sheet_summary in summary["sheets"].items():
            console.print(f"\n[bold cyan]Sheet: {sheet_name}[/bold cyan]")
            _display_sheet_summary(sheet_summary, verbose, sample_count)
        return
    
    # Single sheet/file display
    _display_sheet_summary(summary, verbose, sample_count)


def _display_sheet_summary(summary: dict, verbose: bool, sample_count: Optional[int] = None):
    """Display summary for a single sheet or file."""
    if "columns" in summary and summary["columns"]:
        console.print("\n[bold cyan]Columns/Fields:[/bold cyan]")
        col_table = Table(show_header=True, box=None)
        col_table.add_column("Name", style="green")
        col_table.add_column("Type", style="yellow")
        
        if verbose and "sample_values" in summary:
            col_table.add_column("Sample Values", style="white")
            
        for col_info in summary["columns"]:
            if verbose and "sample_values" in summary:
                sample = summary["sample_values"].get(col_info["name"], [])
                sample_str = ", ".join(str(v) for v in sample[:3])
                col_table.add_row(col_info["name"], col_info["type"], sample_str)
            else:
                col_table.add_row(col_info["name"], col_info["type"])
        
        console.print(col_table)
    
    if verbose and "statistics" in summary:
        console.print("\n[bold cyan]Statistics:[/bold cyan]")
        stats_table = Table(show_header=True, box=None)
        stats_table.add_column("Column", style="green")
        stats_table.add_column("Min", style="yellow")
        stats_table.add_column("Max", style="yellow")
        stats_table.add_column("Mean", style="yellow")
        stats_table.add_column("Unique", style="yellow")
        
        for col_name, stats in summary["statistics"].items():
            stats_table.add_row(
                col_name,
                str(stats.get("min", "N/A")),
                str(stats.get("max", "N/A")),
                str(stats.get("mean", "N/A")),
                str(stats.get("unique", "N/A"))
            )
        
        console.print(stats_table)
    
    if "geometry_info" in summary:
        console.print("\n[bold cyan]Geometry Information:[/bold cyan]")
        geo_table = Table(show_header=False, box=None, padding=(0, 2))
        geo_table.add_column("Property", style="cyan", no_wrap=True)
        geo_table.add_column("Value", style="white")
        
        for key, value in summary["geometry_info"].items():
            geo_table.add_row(key, str(value))
        
        console.print(geo_table)
    
    # Display sample data if count option is used
    if sample_count is not None and "sample_data" in summary:
        console.print(f"\n[bold cyan]Sample Records (showing {sample_count}):[/bold cyan]")
        sample_table = Table(show_header=True, box=None)
        
        # Add columns based on the data
        if summary["sample_data"]:
            # Get column names from first row
            columns = list(summary["sample_data"][0].keys())
            for col in columns:
                sample_table.add_column(col, style="white", no_wrap=False)
            
            # Add data rows
            for row in summary["sample_data"]:
                sample_table.add_row(*[str(row.get(col, "")) for col in columns])
        
        console.print(sample_table)


if __name__ == "__main__":
    app()