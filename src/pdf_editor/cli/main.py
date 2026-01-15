"""Main CLI interface for PDF Editor."""

import click
import sys
import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.editor import PDFEditor
from ..operations.text_operations import (
    AddTextOperation
)
from ..operations.page_operations import (
    RotatePageOperation,
    DeletePageOperation
)
from ..operations.image_operations import (
    AddImageOperation,
    ReplaceImageOperation
)
from ..operations.form_operations import (
    CreateFormFieldOperation, FillFormFieldOperation,
    ValidateFormOperation, ExportFormDataOperation
)
from ..operations.annotation_operations import (
    AddAnnotationOperation, AddCommentOperation,
    AddDrawingOperation, AddFreehandOperation
)
from ..operations.security_operations import (
    SetPasswordOperation, AddSignatureOperation,
    EditMetadataOperation, AddSecurityWatermarkOperation, ExportMetadataOperation
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


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--dpi', type=int, default=300, help='DPI for conversion (higher = sharper text)')
@click.option('--quality', type=int, default=95, help='JPEG quality (1-100)')
@click.option('--preserve-text/--no-preserve-text', default=True, help='Preserve text layer and links (default: True)')
@click.option('--legacy', is_flag=True, help='Use legacy image-based conversion (loses text layer)')
@click.option('--verbose', '-v', is_flag=True, default=True, help='Show detailed progress')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing output file')
@click.pass_context
@handle_cli_errors
def dark_mode(ctx, input_file: str, output_file: str, dpi: int, quality: int, preserve_text: bool, legacy: bool, verbose: bool, force: bool):
    """Convert PDF to dark mode (black background, white text) with text preservation."""
    
    # Display mode information
    if not legacy and preserve_text:
        console.print("[green]✅ Enhanced Dark Mode[/green]: Preserves text layer, links, and form fields")
    elif legacy:
        console.print("[yellow]⚠️  Legacy Dark Mode[/yellow]: Converts to images (text layer lost)")
    else:
        console.print("[yellow]⚠️  Image-based Dark Mode[/yellow]: Text layer and links will be lost")
    
    output_path = Path(output_file)
    if output_path.exists() and not force:
        console.print(f"[red]Output file already exists: {output_file}[/red]")
        console.print("Use --force to overwrite")
        sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Converting PDF to enhanced dark mode..."):
        # Load document
        editor.load_document(input_file)
        
        # Add dark mode operation
        operation = DarkModeOperation(
            dpi=dpi, 
            quality=quality, 
            verbose=verbose,
            preserve_text=preserve_text and not legacy,
            preserve_forms=preserve_text and not legacy,
            preserve_links=preserve_text and not legacy,
            use_enhanced=not legacy
        )
        editor.add_operation(operation)
        
        # Execute operations
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Converting to enhanced dark mode...", total=None)
            
            editor.execute_operations()
            progress.update(task, description="Saving document...")
            
            # Save document
            editor.save_document(output_file)
    
    # Show results
    mode_text = "Enhanced (text preserved)" if not legacy else "Legacy (image-based)"
    console.print(Panel.fit(
        f"[green]✓[/green] Successfully converted to {mode_text} dark mode\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}\\n"
        f"[blue]Mode:[/blue] {mode_text}\\n"
        f"[blue]Text Layer:[/blue] {'Preserved ✓' if not legacy else 'Lost ✗'}\\n"
        f"[blue]Links:[/blue] {'Active ✓' if not legacy else 'Lost ✗'}\\n"
        f"[blue]Forms:[/blue] {'Functional ✓' if not legacy else 'Lost ✗'}",
        title="Dark Mode Conversion"
    ))


@cli.command()
@click.option('--page', '-p', type=int, required=True, help='Page number')
@click.option('--type', '-t', type=click.Choice(['text', 'checkbox', 'radio', 'list', 'dropdown', 'signature']), 
              required=True, help='Field type')
@click.option('--rect', '-r', type=str, required=True, help='Rectangle coordinates (x0,y0,x1,y1)')
@click.option('--name', '-n', type=str, required=True, help='Field name')
@click.option('--value', '-v', type=str, help='Default value')
@click.option('--options', type=str, help='Options for list/dropdown fields (comma-separated)')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def create_field(ctx, page: int, type: str, rect: str, name: str, value: str, options: str, input_file: str, output_file: str):
    """Create a form field in PDF."""
    
    editor = ctx.obj['editor']
    
    # Parse rectangle
    try:
        rect_tuple = tuple(map(float, rect.split(',')))
    except ValueError:
        console.print("[red]Error: Rectangle must be comma-separated numbers (x0,y0,x1,y1)[/red]")
        sys.exit(1)
    
    # Parse options
    options_list = options.split(',') if options else []
    
    with console.status(f"[bold green]Creating {type} field '{name}' on page {page}..."):
        editor.load_document(input_file)
        
        operation = CreateFormFieldOperation(page, type, rect_tuple, name, value, options_list)
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Form field created successfully\\n"
        f"[blue]Type:[/blue] {type}\\n"
        f"[blue]Name:[/blue] {name}\\n"
        f"[blue]Page:[/blue] {page}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Form Field Created"
    ))


@cli.command()
@click.option('--page', '-p', type=int, help='Page number (optional, applies to all pages if not specified)')
@click.option('--data', '-d', type=str, required=True, help='Field data as JSON string (e.g., \\"{\'field1\':\'value1\'}\\")')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def fill_field(ctx, page: int, data: str, input_file: str, output_file: str):
    """Fill form fields with data."""
    
    editor = ctx.obj['editor']
    
    # Parse field data
    try:
        field_data = json.loads(data)
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format for field data[/red]")
        sys.exit(1)
    
    with console.status("[bold green]Filling form fields..."):
        editor.load_document(input_file)
        
        operation = FillFormFieldOperation(field_data, page)
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Form fields filled successfully\\n"
        f"[blue]Fields:[/blue] {len(field_data)}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Form Fields Filled"
    ))


@cli.command()
@click.option('--page', '-p', type=int, required=True, help='Page number')
@click.option('--rect', '-r', type=str, required=True, help='Rectangle coordinates (x0,y0,x1,y1)')
@click.option('--type', '-t', type=click.Choice(['text', 'highlight', 'underline', 'strikeout', 'note', 'rectangle', 'circle']), 
              required=True, help='Annotation type')
@click.option('--content', '-c', type=str, help='Annotation content')
@click.option('--author', '-a', type=str, help='Author name')
@click.option('--color', type=str, default='red', help='Color (default: red)')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def add_annotation(ctx, page: int, rect: str, type: str, content: str, author: str, color: str, input_file: str, output_file: str):
    """Add annotation to PDF."""
    
    editor = ctx.obj['editor']
    
    # Parse rectangle
    try:
        rect_tuple = tuple(map(float, rect.split(',')))
    except ValueError:
        console.print("[red]Error: Rectangle must be comma-separated numbers (x0,y0,x1,y1)[/red]")
        sys.exit(1)
    
    # Convert color string to tuple
    color_map = {
        'red': (1, 0, 0),
        'green': (0, 1, 0),
        'blue': (0, 0, 1),
        'yellow': (1, 1, 0),
        'purple': (1, 0, 1),
        'cyan': (0, 1, 1),
        'black': (0, 0, 0)
    }
    color_tuple = color_map.get(color.lower(), (1, 0, 0))
    
    with console.status(f"[bold green]Adding {type} annotation..."):
        editor.load_document(input_file)
        
        operation = AddAnnotationOperation(page, rect_tuple, type, content, author, color_tuple)
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Annotation added successfully\\n"
        f"[blue]Type:[/blue] {type}\\n"
        f"[blue]Page:[/blue] {page}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Annotation Added"
    ))


@cli.command()
@click.option('--user-password', type=str, help='User password for opening')
@click.option('--owner-password', type=str, help='Owner password for permissions')
@click.option('--encryption', type=click.Choice(['40', '128', '256']), default='128', help='Encryption strength')
@click.option('--permissions', type=str, help='Permissions JSON string')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def set_password(ctx, user_password: str, owner_password: str, encryption: str, permissions: str, input_file: str, output_file: str):
    """Set password protection for PDF."""
    
    editor = ctx.obj['editor']
    
    # Parse permissions
    perms = {}
    if permissions:
        try:
            perms = json.loads(permissions)
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON format for permissions[/red]")
            sys.exit(1)
    
    with console.status("[bold green]Setting password protection..."):
        editor.load_document(input_file)
        
        operation = SetPasswordOperation(user_password, owner_password, perms, int(encryption))
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Password protection set\\n"
        f"[blue]Encryption:[/blue] {encryption}-bit\\n"
        f"[blue]User Password:[/blue] {'Yes' if user_password else 'No'}\\n"
        f"[blue]Owner Password:[/blue] {'Yes' if owner_password else 'No'}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Password Protection Added"
    ))


@cli.command()
@click.option('--title', type=str, help='Document title')
@click.option('--author', type=str, help='Document author')
@click.option('--subject', type=str, help='Document subject')
@click.option('--keywords', type=str, help='Document keywords')
@click.option('--creator', type=str, help='Document creator')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def edit_metadata(ctx, title: str, author: str, subject: str, keywords: str, creator: str, input_file: str, output_file: str):
    """Edit PDF metadata."""
    
    editor = ctx.obj['editor']
    
    # Build metadata dictionary
    metadata = {}
    if title:
        metadata['title'] = title
    if author:
        metadata['author'] = author
    if subject:
        metadata['subject'] = subject
    if keywords:
        metadata['keywords'] = keywords
    if creator:
        metadata['creator'] = creator
    
    if not metadata:
        console.print("[red]Error: At least one metadata field must be specified[/red]")
        sys.exit(1)
    
    with console.status("[bold green]Editing metadata..."):
        editor.load_document(input_file)
        
        operation = EditMetadataOperation(metadata)
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Metadata updated successfully\\n"
        f"[blue]Fields:[/blue] {len(metadata)}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Metadata Updated"
    ))


@cli.command()
@click.argument('input_file')
@click.argument('output_file')
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


@cli.command()
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def wrapper(ctx, input_file: str, output_file: str):
    """Wrapper operation for basic PDF operations."""
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Processing document..."):
        editor.load_document(input_file)
        
        # For now, this is a placeholder for additional operations
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Document processed\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Document Processed"
    ))


@cli.command()
@click.pass_context
def cli(ctx):
    """PDF Editor CLI."""
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['editor'] = PDFEditor(config_file=config)
    ctx.obj['verbose'] = verbose if 'verbose' in ctx.params else True


if __name__ == '__main__':
    cli()