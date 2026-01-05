"""Main CLI interface for PDF Editor."""

import click
import sys
from pathlib import Path
from typing import Optional, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from ..core.editor import PDFEditor
from ..operations import (
    DarkModeOperation,
    AddTextOperation,
    RotatePageOperation,
    DeletePageOperation,
    ReorderPagesOperation,
    AddImageOperation
)
from ..config.manager import config_manager
from ..utils.logging import get_logger, setup_logging
from ..utils.validation import ValidationError, ProcessingError

console = Console()
logger = get_logger("cli")


def handle_cli_errors(func):
    """Decorator to handle CLI errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            console.print(f"[red]Validation Error:[/red] {e}")
            sys.exit(1)
        except ProcessingError as e:
            console.print(f"[red]Processing Error:[/red] {e}")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected Error:[/red] {e}")
            logger.exception("Unexpected error in CLI")
            sys.exit(1)
    
    return wrapper


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool, log_file: Optional[str]):
    """PDF Editor - A comprehensive PDF editing tool."""
    
    # Setup logging
    if verbose:
        setup_logging(level="DEBUG", log_file=log_file)
    elif log_file:
        setup_logging(level="INFO", log_file=log_file)
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['editor'] = PDFEditor(config_file=config)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--dpi', type=int, default=300, help='DPI for image conversion (higher = sharper text)')
@click.option('--quality', type=int, default=95, help='JPEG quality (1-100)')
@click.option('--verbose', '-v', is_flag=True, default=True, help='Show detailed progress')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def dark_mode(ctx, input_file: str, output_file: str, dpi: int, quality: int, verbose: bool, force: bool):
    """Convert PDF to dark mode (black background, white text)."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    verbose = ctx.obj['verbose']
    
    with console.status("[bold green]Converting PDF to dark mode..."):
        # Load document
        document = editor.load_document(input_file)
        
        # Add dark mode operation
        operation = DarkModeOperation(dpi=dpi, quality=quality, verbose=verbose)
        editor.add_operation(operation)
        
        # Execute operations
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Converting to dark mode...", total=None)
            
            results = editor.execute_operations()
            progress.update(task, description="Saving document...")
            
            # Save document
            editor.save_document(output_file)
    
    # Show results
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully converted to dark mode\n"
        f"[blue]Input:[/blue] {input_file}\n"
        f"[blue]Output:[/blue] {output_file}\n"
        f"[blue]Operations:[/blue] {results['successful']}/{results['total']} successful",
        title="Dark Mode Conversion Complete"
    ))


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--page', '-p', type=int, required=True, help='Page number (0-based)')
@click.option('--angle', '-a', type=click.Choice(['90', '180', '270']), required=True, help='Rotation angle')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def rotate(ctx, input_file: str, output_file: str, page: int, angle: str, force: bool):
    """Rotate a PDF page."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Rotating page {page} by {angle} degrees..."):
        document = editor.load_document(input_file)
        
        operation = RotatePageOperation(page, int(angle))
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully rotated page {page}\n"
        f"[blue]Angle:[/blue] {angle}°\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Page Rotation Complete"
    ))


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.pass_context
@handle_cli_errors
def info(ctx, input_file: str):
    """Display information about a PDF file."""
    
    editor = ctx.obj['editor']
    document = editor.load_document(input_file)
    
    info_data = editor.get_document_info()
    
    # Create info table
    table = Table(title="PDF Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("File Path", str(info_data['file_path']))
    table.add_row("Page Count", str(info_data['page_count']))
    table.add_row("File Size", f"{info_data['metadata'].get('file_size', 0):,} bytes")
    table.add_row("Title", info_data['metadata'].get('title', 'N/A'))
    table.add_row("Author", info_data['metadata'].get('author', 'N/A'))
    table.add_row("Creator", info_data['metadata'].get('creator', 'N/A'))
    table.add_row("Modified", info_data['metadata'].get('modified_time', 'N/A'))
    
    console.print(table)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--page', '-p', type=int, required=True, help='Page number (0-based)')
@click.option('--text', '-t', required=True, help='Text to add')
@click.option('--x', type=float, required=True, help='X coordinate')
@click.option('--y', type=float, required=True, help='Y coordinate')
@click.option('--font', default='helv', help='Font name')
@click.option('--size', type=float, default=11, help='Font size')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def add_text(ctx, input_file: str, output_file: str, page: int, text: str, 
             x: float, y: float, font: str, size: float, force: bool):
    """Add text to a PDF page."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Adding text to page {page}..."):
        document = editor.load_document(input_file)
        
        operation = AddTextOperation(page, text, (x, y), fontname=font, fontsize=size)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully added text\n"
        f"[blue]Page:[/blue] {page}\n"
        f"[blue]Text:[/blue] {text}\n"
        f"[blue]Position:[/blue] ({x}, {y})\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Add Text Complete"
    ))


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--pages', '-p', help='Pages to delete (comma-separated, e.g., "0,2,5")')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def delete_pages(ctx, input_file: str, output_file: str, pages: str, force: bool):
    """Delete pages from a PDF."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    if not pages:
        console.print("[red]Error: --pages option is required[/red]")
        sys.exit(1)
    
    # Parse page numbers
    try:
        page_list = [int(p.strip()) for p in pages.split(',')]
    except ValueError:
        console.print("[red]Error: Invalid page numbers[/red]")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    document = editor.load_document(input_file)
    
    # Validate page numbers
    for page_num in page_list:
        if page_num < 0 or page_num >= document.page_count:
            console.print(f"[red]Error: Page number {page_num} out of range[/red]")
            sys.exit(1)
    
    with console.status(f"[bold green]Deleting pages {page_list}..."):
        # Sort in descending order to avoid index shifting
        page_list.sort(reverse=True)
        
        for page_num in page_list:
            operation = DeletePageOperation(page_num)
            editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully deleted pages\n"
        f"[blue]Pages:[/blue] {page_list}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Delete Pages Complete"
    ))


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    
    console.print(Panel.fit(
        "Current Configuration",
        title="Configuration"
    ))
    
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    # Display all configuration values
    config_dict = config_manager.config.__dict__
    for key, value in config_dict.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)


@cli.command()
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key: str, value: str):
    """Set a configuration value."""
    
    try:
        # Try to convert to appropriate type
        if value.lower() in ['true', 'false']:
            value_bool = value.lower() == 'true'
            config_manager.set(key, value_bool)
        elif value.isdigit():
            config_manager.set(key, int(value))
        else:
            config_manager.set(key, value)
        
        console.print(f"[green]✓[/green] Set {key} = {value}")
        
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()