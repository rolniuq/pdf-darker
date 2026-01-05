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
from ..operations.text_operations import (
    AddTextOperation,
    HighlightTextOperation,
    AddAnnotationOperation,
    AddTextBoxOperation,
    ReplaceTextOperation,
    DeleteTextOperation
)
from ..operations.page_operations import (
    RotatePageOperation,
    DeletePageOperation,
    ReorderPagesOperation,
    InsertPageOperation,
    ExtractPagesOperation,
    MergeDocumentsOperation,
    SplitDocumentOperation
)
from ..operations.image_operations import (
    AddImageOperation,
    ResizeImageOperation,
    CropImageOperation,
    ImageFilterOperation,
    AddWatermarkOperation,
    AddImageWatermarkOperation
)
from ..operations.dark_mode import DarkModeOperation
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


# Text Operations Commands

@cli.group()
def text():
    """Text manipulation operations."""
    pass


@text.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--search', '-s', required=True, help='Text to search for')
@click.option('--color', '-c', default='1,1,0', help='Highlight color (RGB, e.g., "1,1,0" for yellow)')
@click.option('--pages', '-p', help='Pages to search (comma-separated, default: all)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def highlight(ctx, input_file: str, output_file: str, search: str, color: str, 
             pages: str, force: bool):
    """Highlight text in PDF pages."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    # Parse color
    try:
        color_tuple = tuple(float(c.strip()) for c in color.split(','))
        if len(color_tuple) != 3:
            raise ValueError("Color must have 3 components")
    except ValueError:
        console.print("[red]Error: Invalid color format. Use RGB values like '1,1,0'[/red]")
        sys.exit(1)
    
    # Parse page numbers
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(',')]
        except ValueError:
            console.print("[red]Error: Invalid page numbers[/red]")
            sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Highlighting text '{search}'..."):
        document = editor.load_document(input_file)
        
        operation = HighlightTextOperation(search, color_tuple, page_list)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully highlighted text\n"
        f"[blue]Search text:[/blue] {search}\n"
        f"[blue]Pages:[/blue] {page_list or 'all'}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Text Highlight Complete"
    ))


@text.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--page', '-p', type=int, required=True, help='Page number (0-based)')
@click.option('--x', type=float, required=True, help='X coordinate')
@click.option('--y', type=float, required=True, help='Y coordinate')
@click.option('--text', '-t', required=True, help='Annotation text')
@click.option('--type', 'annotation_type', type=click.Choice(['note', 'text', 'free_text', 'callout']), 
              default='note', help='Annotation type')
@click.option('--author', default='PDF Editor', help='Annotation author')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def annotate(ctx, input_file: str, output_file: str, page: int, x: float, y: float, 
            text: str, annotation_type: str, author: str, force: bool):
    """Add annotation to a PDF page."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Adding annotation to page {page}..."):
        document = editor.load_document(input_file)
        
        operation = AddAnnotationOperation(page, (x, y), text, annotation_type, author)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully added annotation\n"
        f"[blue]Page:[/blue] {page}\n"
        f"[blue]Position:[/blue] ({x}, {y})\n"
        f"[blue]Type:[/blue] {annotation_type}\n"
        f"[blue]Text:[/blue] {text}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Add Annotation Complete"
    ))


# Page Operations Commands

@cli.group()
def pages():
    """Page manipulation operations."""
    pass


@pages.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--position', type=int, required=True, help='Insert position (0-based)')
@click.option('--width', type=float, help='Page width (for blank page)')
@click.option('--height', type=float, help='Page height (for blank page)')
@click.option('--source', help='Source PDF file to insert page from')
@click.option('--source-page', type=int, help='Page number from source file')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def insert(ctx, input_file: str, output_file: str, position: int, width: float, 
          height: float, source: str, source_page: int, force: bool):
    """Insert a page into PDF."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    if source and not Path(source).exists():
        console.print(f"[red]Error: Source file not found: {source}[/red]")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Inserting page at position {position}..."):
        document = editor.load_document(input_file)
        
        operation = InsertPageOperation(position, width, height, source, source_page)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully inserted page\n"
        f"[blue]Position:[/blue] {position}\n"
        f"[blue]Source:[/blue] {source or 'blank page'}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Insert Page Complete"
    ))


@pages.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--pages', '-p', required=True, help='Pages to extract (comma-separated)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def extract(ctx, input_file: str, output_file: str, pages: str, force: bool):
    """Extract pages from PDF."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
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
    
    with console.status(f"[bold green]Extracting pages {page_list}..."):
        operation = ExtractPagesOperation(page_list, output_file)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully extracted pages\n"
        f"[blue]Pages:[/blue] {page_list}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Extract Pages Complete"
    ))


@pages.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('sources', nargs=-1, required=True)
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--position', type=int, help='Insert position (default: end)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def merge(ctx, input_file: str, sources: tuple, output: str, position: int, force: bool):
    """Merge multiple PDFs."""
    
    output_path = Path(output)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_path}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    # Validate source files
    source_list = []
    for source in sources:
        if not Path(source).exists():
            console.print(f"[red]Error: Source file not found: {source}[/red]")
            sys.exit(1)
        source_list.append(source)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Merging {len(source_list) + 1} documents..."):
        document = editor.load_document(input_file)
        
        operation = MergeDocumentsOperation(source_list, output, position)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully merged documents\n"
        f"[blue]Sources:[/blue] {len(source_list)} files\n"
        f"[blue]Output:[/blue] {output}",
        title="Merge Documents Complete"
    ))


# Image Operations Commands

@cli.group()
def images():
    """Image manipulation operations."""
    pass


@images.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--page', '-p', type=int, required=True, help='Page number (0-based)')
@click.option('--index', '-i', type=int, required=True, help='Image index (0-based)')
@click.option('--filter', 'filter_type', type=click.Choice(['brightness', 'contrast', 'sharpness', 'blur', 'grayscale']), 
              required=True, help='Filter type')
@click.option('--intensity', type=float, default=1.0, help='Filter intensity (0-2)')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def filter(ctx, input_file: str, output_file: str, page: int, index: int, 
          filter_type: str, intensity: float, force: bool):
    """Apply filter to an image in PDF."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_path}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Applying {filter_type} filter..."):
        document = editor.load_document(input_file)
        
        operation = ImageFilterOperation(page, index, filter_type, intensity)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully applied filter\n"
        f"[blue]Page:[/blue] {page}\n"
        f"[blue]Image index:[/blue] {index}\n"
        f"[blue]Filter:[/blue] {filter_type}\n"
        f"[blue]Intensity:[/blue] {intensity}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Image Filter Complete"
    ))


@images.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--text', '-t', required=True, help='Watermark text')
@click.option('--pages', '-p', help='Pages to watermark (comma-separated, default: all)')
@click.option('--size', type=int, default=48, help='Font size')
@click.option('--opacity', type=float, default=0.3, help='Opacity (0-1)')
@click.option('--rotation', type=int, default=45, help='Rotation angle')
@click.option('--color', default='0.5,0.5,0.5', help='Color (RGB)')
@click.option('--position', type=click.Choice(['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right']), 
              default='center', help='Position')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def watermark(ctx, input_file: str, output_file: str, text: str, pages: str, size: int, 
             opacity: float, rotation: int, color: str, position: str, force: bool):
    """Add text watermark to PDF."""
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_path}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    # Parse color
    try:
        color_tuple = tuple(float(c.strip()) for c in color.split(','))
        if len(color_tuple) != 3:
            raise ValueError("Color must have 3 components")
    except ValueError:
        console.print("[red]Error: Invalid color format. Use RGB values like '0.5,0.5,0.5'[/red]")
        sys.exit(1)
    
    # Parse page numbers
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(',')]
        except ValueError:
            console.print("[red]Error: Invalid page numbers[/red]")
            sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Adding watermark '{text}'..."):
        document = editor.load_document(input_file)
        
        operation = AddWatermarkOperation(text, page_list, size, opacity, rotation, color_tuple, position)
        editor.add_operation(operation)
        
        results = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully added watermark\n"
        f"[blue]Text:[/blue] {text}\n"
        f"[blue]Pages:[/blue] {page_list or 'all'}\n"
        f"[blue]Position:[/blue] {position}\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Watermark Complete"
    ))


if __name__ == '__main__':
    cli()