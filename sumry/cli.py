import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.box import ROUNDED, DOUBLE_EDGE, MINIMAL_DOUBLE_HEAD
from rich.syntax import Syntax
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
import warnings
import os
import json
import sys

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
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results in JSON format"
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
        if json_output:
            print(json.dumps({"error": f"File {file_path} does not exist"}), file=sys.stderr)
        else:
            console.print(f"[bold red]Error:[/bold red] File {file_path} does not exist")
        raise typer.Exit(1)
    
    file_type = detect_file_type(file_path)
    
    if not file_type:
        if json_output:
            print(json.dumps({"error": f"Unsupported file type for {file_path}"}), file=sys.stderr)
        else:
            console.print(f"[bold red]Error:[/bold red] Unsupported file type for {file_path}")
        raise typer.Exit(1)
    
    try:
        # Set default count to 5 if count option is used without value
        sample_count = 5 if count is not None and count <= 0 else count
        
        if json_output:
            # No spinner for JSON output
            if file_type == "CSV":
                summary = read_csv(file_path, verbose, sample_count)
            elif file_type == "Excel":
                summary = read_excel(file_path, verbose, select, sample_count)
            elif file_type == "GeoJSON":
                summary = read_geojson(file_path, verbose, sample_count)
            elif file_type == "Shapefile":
                summary = read_shapefile(file_path, verbose, sample_count)
            else:
                console.print(f"[bold red]Error:[/bold red] Handler not implemented for {file_type}", file=sys.stderr)
                raise typer.Exit(1)
        else:
            # Show loading spinner while reading the file
            with console.status(f"[bold green]📂 Reading {file_type} file...[/bold green]", spinner="dots") as status:
                if file_type == "CSV":
                    summary = read_csv(file_path, verbose, sample_count)
                elif file_type == "Excel":
                    status.update(f"[bold green]📊 Reading Excel file ({select if select else 'default sheet'})...[/bold green]")
                    summary = read_excel(file_path, verbose, select, sample_count)
                elif file_type == "GeoJSON":
                    status.update(f"[bold green]🌍 Reading GeoJSON file...[/bold green]")
                    summary = read_geojson(file_path, verbose, sample_count)
                elif file_type == "Shapefile":
                    status.update(f"[bold green]🗺️ Reading Shapefile...[/bold green]")
                    summary = read_shapefile(file_path, verbose, sample_count)
                else:
                    console.print(f"[bold red]Error:[/bold red] Handler not implemented for {file_type}")
                    raise typer.Exit(1)
        
        # Clear the line after loading (only for non-JSON output)
        if not json_output:
            console.print()
        
        if json_output:
            # Output as JSON
            print(json.dumps(summary, indent=2, default=str))
        else:
            display_summary(summary, file_type, verbose, sample_count)
        
    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Error reading file: {str(e)}"}), file=sys.stderr)
        else:
            console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
        raise typer.Exit(1)


def display_summary(summary: dict, file_type: str, verbose: bool, sample_count: Optional[int] = None):
    """Display the file summary using Rich formatting."""
    
    title_text = Text(f"📊 {file_type} File Summary", style="bold magenta")
    panel = Panel(
        title_text,
        border_style="bright_cyan",
        box=DOUBLE_EDGE,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()
    
    table = Table(
        show_header=False, 
        box=MINIMAL_DOUBLE_HEAD, 
        padding=(0, 2),
        title="[bold cyan]📋 File Information[/bold cyan]",
        title_style="bold",
        border_style="bright_blue"
    )
    table.add_column("Property", style="bright_cyan", no_wrap=True)
    table.add_column("Value", style="bright_white")
    
    for key, value in summary.get("basic_info", {}).items():
        if isinstance(value, (list, dict)):
            value_str = str(value)
        else:
            value_str = str(value)
        
        # Style different value types
        if isinstance(value, (int, float)):
            value_text = Text(value_str, style="bold yellow")
        elif isinstance(value, bool):
            value_text = Text(value_str, style="bold green" if value else "bold red")
        else:
            value_text = Text(value_str, style="bright_white")
        
        key_text = Text(key, style="bright_cyan")
        table.add_row(key_text, value_text)
    
    console.print(table)
    
    # Handle multiple sheets if present
    if "sheets" in summary:
        console.print(Rule("[bold bright_magenta]📑 Sheets[/bold bright_magenta]", style="bright_magenta"))
        for sheet_name, sheet_summary in summary["sheets"].items():
            sheet_panel = Panel(
                f"[bold bright_yellow]📄 {sheet_name}[/bold bright_yellow]",
                border_style="yellow",
                box=ROUNDED,
                expand=False
            )
            console.print(sheet_panel)
            _display_sheet_summary(sheet_summary, verbose, sample_count)
        return
    
    # Single sheet/file display
    _display_sheet_summary(summary, verbose, sample_count)


def _display_sheet_summary(summary: dict, verbose: bool, sample_count: Optional[int] = None):
    """Display summary for a single sheet or file."""
    if "columns" in summary and summary["columns"]:
        console.print(Rule("[bold bright_cyan]🔤 Columns/Fields[/bold bright_cyan]", style="bright_cyan"))
        col_table = Table(
            show_header=True, 
            box=ROUNDED,
            border_style="bright_green",
            header_style="bold white"
        )
        col_table.add_column("#", style="dim white", width=4)
        col_table.add_column("Name", style="bold green")
        col_table.add_column("Type", style="bold yellow")
        
        if verbose and "sample_values" in summary:
            col_table.add_column("Sample Values", style="bright_white", overflow="fold")
            
        for idx, col_info in enumerate(summary["columns"], 1):
            if verbose and "sample_values" in summary:
                sample = summary["sample_values"].get(col_info["name"], [])
                sample_str = " | ".join(f"[italic]{str(v)}[/italic]" for v in sample[:3])
                col_table.add_row(
                    str(idx),
                    Text(col_info["name"], style="bold green"),
                    Text(col_info["type"], style="yellow"),
                    sample_str
                )
            else:
                col_table.add_row(
                    str(idx),
                    Text(col_info["name"], style="bold green"),
                    Text(col_info["type"], style="yellow")
                )
        
        console.print(col_table)
    
    if verbose and "statistics" in summary:
        console.print(Rule("[bold bright_magenta]📈 Statistics[/bold bright_magenta]", style="bright_magenta"))
        stats_table = Table(
            show_header=True,
            box=ROUNDED,
            border_style="bright_magenta",
            header_style="bold"
        )
        stats_table.add_column("Column", style="bold green")
        stats_table.add_column("Min", style="cyan")
        stats_table.add_column("Max", style="cyan")
        stats_table.add_column("Mean", style="yellow")
        stats_table.add_column("Unique", style="bright_magenta")
        
        for col_name, stats in summary["statistics"].items():
            min_val = str(stats.get("min", "N/A"))
            max_val = str(stats.get("max", "N/A"))
            mean_val = str(stats.get("mean", "N/A"))
            unique_val = str(stats.get("unique", "N/A"))
            
            # Format numbers nicely
            if mean_val != "N/A" and "." in mean_val:
                try:
                    mean_val = f"{float(mean_val):.2f}"
                except:
                    pass
            
            stats_table.add_row(
                Text(col_name, style="bold green"),
                Text(min_val, style="cyan"),
                Text(max_val, style="cyan"),
                Text(mean_val, style="yellow"),
                Text(unique_val, style="bright_magenta")
            )
        
        console.print(stats_table)
    
    if "geometry_info" in summary:
        console.print(Rule("[bold bright_blue]🌍 Geometry Information[/bold bright_blue]", style="bright_blue"))
        geo_table = Table(
            show_header=False,
            box=ROUNDED,
            padding=(0, 2),
            border_style="bright_blue"
        )
        geo_table.add_column("Property", style="bold cyan", no_wrap=True)
        geo_table.add_column("Value", style="bright_white")
        
        for key, value in summary["geometry_info"].items():
            key_text = Text(key, style="bold cyan")
            value_text = Text(str(value), style="bright_yellow" if isinstance(value, (int, float)) else "bright_white")
            geo_table.add_row(key_text, value_text)
        
        console.print(geo_table)
    
    # Display sample data if count option is used
    if sample_count is not None and "sample_data" in summary:
        console.print(Rule(f"[bold bright_yellow]📝 Sample Records (showing {sample_count})[/bold bright_yellow]", style="bright_yellow"))
        sample_table = Table(
            show_header=True,
            box=ROUNDED,
            border_style="bright_yellow",
            header_style="bold yellow",
            show_lines=True,
            row_styles=["none", "dim"]
        )
        
        # Add columns based on the data
        if summary["sample_data"]:
            # Get column names from first row
            columns = list(summary["sample_data"][0].keys())
            for col in columns:
                sample_table.add_column(col, style="bright_white", no_wrap=False, overflow="ellipsis")
            
            # Add data rows
            for row in summary["sample_data"]:
                row_data = []
                for col in columns:
                    val = row.get(col, "")
                    val_str = str(val) if val != "" else "[dim]—[/dim]"
                    
                    # Add syntax highlighting for different data types
                    if isinstance(val, bool):
                        val_str = f"[bold green]{val}[/bold green]" if val else f"[bold red]{val}[/bold red]"
                    elif isinstance(val, (int, float)):
                        val_str = f"[bold yellow]{val}[/bold yellow]"
                    elif val == "":
                        val_str = "[dim italic]null[/dim italic]"
                    
                    row_data.append(val_str)
                sample_table.add_row(*row_data)
        
        console.print(sample_table)


if __name__ == "__main__":
    app()