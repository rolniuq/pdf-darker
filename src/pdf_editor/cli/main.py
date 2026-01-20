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
from ..operations.ocr_operations import (
    OCRExtractTextOperation, OCREditTextOperation, OCRSearchOperation
)
from ..operations.batch_operations import (
    BatchProcessOperation, BatchTemplateOperation, BatchReportOperation
)
from ..operations.compression_operations import (
    CompressPDFOperation, OptimizeImagesOperation, CleanupPDFOperation, AnalyzePDFOperation
)
from ..operations.advanced_export_operations import (
    ExportToWordOperation, ExportToExcelOperation, ExportToPowerPointOperation
)
from ..operations.cloud_operations import (
    CloudUploadOperation, CloudDownloadOperation, CloudListOperation
)
from ..operations.email_web_operations import (
    EmailPDFOperation, FlaskWebService, PrintPDFOperation
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


# Phase 4: Advanced Processing Commands

@cli.command()
@click.option('--pages', '-p', type=str, help='Pages to process (comma-separated, e.g., "0,1,2")')
@click.option('--language', '-l', type=str, default='eng', help='OCR language code')
@click.option('--dpi', '-d', type=int, default=300, help='DPI for OCR processing')
@click.option('--confidence', '-c', type=float, default=60.0, help='Confidence threshold (0-100)')
@click.option('--output', '-o', type=str, default='ocr_output.json', help='Output JSON file')
@click.argument('input_file')
@click.pass_context
def ocr_extract(ctx, pages: str, language: str, dpi: int, confidence: float, output: str, input_file: str):
    """Extract text from PDF using OCR."""
    
    editor = ctx.obj['editor']
    
    # Parse pages
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(',')]
        except ValueError:
            console.print("[red]Error: Invalid page format. Use comma-separated numbers.[/red]")
            sys.exit(1)
    
    with console.status("[bold green]Extracting text with OCR..."):
        editor.load_document(input_file)
        
        operation = OCRExtractTextOperation(
            pages=page_list,
            language=language,
            dpi=dpi,
            confidence_threshold=confidence
        )
        editor.add_operation(operation)
        
        result = editor.execute_operations()
        
        # Save results to JSON file
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
    
    console.print(Panel.fit(
        f"[green]✓[/green] OCR extraction completed\\n"
        f"[blue]Pages processed:[/blue] {len(result['results'])}\\n"
        f"[blue]Language:[/blue] {language}\\n"
        f"[blue]Output file:[/blue] {output}",
        title="OCR Text Extraction"
    ))


@cli.command()
@click.option('--find', '-f', type=str, required=True, help='Text to find')
@click.option('--replace', '-r', type=str, required=True, help='Text to replace with')
@click.option('--pages', '-p', type=str, help='Pages to process')
@click.option('--language', '-l', type=str, default='eng', help='OCR language')
@click.option('--confidence', '-c', type=float, default=70.0, help='Confidence threshold')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def ocr_edit(ctx, find: str, replace: str, pages: str, language: str, confidence: float, input_file: str, output_file: str):
    """Edit text in PDF using OCR."""
    
    editor = ctx.obj['editor']
    
    # Parse pages
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(',')]
        except ValueError:
            console.print("[red]Error: Invalid page format[/red]")
            sys.exit(1)
    
    with console.status(f"[bold green]Replacing text: '{find}' -> '{replace}'..."):
        editor.load_document(input_file)
        
        operation = OCREditTextOperation(
            find_text=find,
            replace_text=replace,
            pages=page_list,
            language=language,
            confidence_threshold=confidence
        )
        editor.add_operation(operation)
        
        editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] OCR text editing completed\\n"
        f"[blue]Find:[/blue] {find}\\n"
        f"[blue]Replace:[/blue] {replace}\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="OCR Text Editing"
    ))


@cli.command()
@click.option('--pattern', '-p', type=str, required=True, help='File pattern (e.g., "*.pdf")')
@click.option('--output-dir', '-o', type=str, required=True, help='Output directory')
@click.option('--operations', type=str, required=True, help='Operations JSON file')
@click.option('--workers', '-w', type=int, default=4, help='Number of parallel workers')
@click.option('--continue-on-error', is_flag=True, default=True, help='Continue processing on errors')
@click.pass_context
def batch_process(ctx, pattern: str, output_dir: str, operations: str, workers: int, continue_on_error: bool):
    """Process multiple PDF files with specified operations."""
    
    # Load operations from JSON file
    try:
        with open(operations, 'r') as f:
            ops_config = json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading operations file: {e}[/red]")
        sys.exit(1)
    
    with console.status(f"[bold green]Processing files: {pattern}..."):
        # Create a temporary document for validation
        editor = ctx.obj['editor']
        
        operation = BatchProcessOperation(
            input_pattern=pattern,
            output_dir=output_dir,
            operations=ops_config,
            max_workers=workers,
            continue_on_error=continue_on_error
        )
        
        result = operation.execute(editor)  # Pass editor for validation
        
        # Save batch results
        results_file = Path(output_dir) / 'batch_results.json'
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Batch processing completed\\n"
        f"[blue]Total files:[/blue] {result['total_files']}\\n"
        f"[blue]Successful:[/blue] {result['successful']}\\n"
        f"[blue]Failed:[/blue] {result['failed']}\\n"
        f"[blue]Total time:[/blue] {result['total_time']:.2f}s\\n"
        f"[blue]Results file:[/blue] {results_file}",
        title="Batch Processing"
    ))


@cli.command()
@click.option('--quality', '-q', type=int, default=70, help='Compression quality (0-100)')
@click.option('--image-quality', '-i', type=int, default=75, help='Image quality (0-100)')
@click.option('--compress-images', is_flag=True, default=True, help='Compress images')
@click.option('--remove-metadata', is_flag=True, default=False, help='Remove metadata')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def compress_pdf(ctx, quality: int, image_quality: int, compress_images: bool, remove_metadata: bool, input_file: str, output_file: str):
    """Compress PDF to reduce file size."""
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Compressing PDF..."):
        editor.load_document(input_file)
        
        operation = CompressPDFOperation(
            quality=quality,
            image_quality=image_quality,
            compress_images=compress_images,
            remove_metadata=remove_metadata
        )
        editor.add_operation(operation)
        
        result = editor.execute_operations()
        editor.save_document(output_file)
    
    console.print(Panel.fit(
        f"[green]✓[/green] PDF compression completed\\n"
        f"[blue]Original size:[/blue] {result['original_size']:,} bytes\\n"
        f"[blue]Compressed size:[/blue] {result['compressed_size']:,} bytes\\n"
        f"[blue]Reduction:[/blue] {result['compression_ratio']:.1f}%\\n"
        f"[blue]Input:[/blue] {input_file}\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="PDF Compression"
    ))


# Phase 5: Advanced Export Commands

@cli.command()
@click.option('--preserve-formatting', is_flag=True, default=True, help='Preserve text formatting')
@click.option('--extract-images', is_flag=True, default=True, help='Extract images')
@click.option('--page-breaks', is_flag=True, default=True, help='Add page breaks')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def export_word(ctx, preserve_formatting: bool, extract_images: bool, page_breaks: bool, input_file: str, output_file: str):
    """Export PDF to Word document."""
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Exporting to Word..."):
        editor.load_document(input_file)
        
        operation = ExportToWordOperation(
            output_path=output_file,
            preserve_formatting=preserve_formatting,
            extract_images=extract_images,
            page_breaks=page_breaks
        )
        editor.add_operation(operation)
        
        result = editor.execute_operations()
    
    console.print(Panel.fit(
        f"[green]✓[/green] Word export completed\\n"
        f"[blue]Pages processed:[/blue] {result['pages_processed']}\\n"
        f"[blue]Images extracted:[/blue] {result['images_extracted']}\\n"
        f"[blue]File size:[/blue] {result['file_size']:,} bytes\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Word Export"
    ))


@cli.command()
@click.option('--type', '-t', type=click.Choice(['form_data', 'table_data', 'text_blocks']), 
               default='form_data', help='Export type')
@click.option('--include-metadata', is_flag=True, default=True, help='Include metadata')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def export_excel(ctx, type: str, include_metadata: bool, input_file: str, output_file: str):
    """Export PDF form data or content to Excel."""
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Exporting to Excel..."):
        editor.load_document(input_file)
        
        operation = ExportToExcelOperation(
            output_path=output_file,
            export_type=type,
            include_metadata=include_metadata
        )
        editor.add_operation(operation)
        
        result = editor.execute_operations()
    
    console.print(Panel.fit(
        f"[green]✓[/green] Excel export completed\\n"
        f"[blue]Export type:[/blue] {type}\\n"
        f"[blue]File size:[/blue] {result['file_size']:,} bytes\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="Excel Export"
    ))


@cli.command()
@click.option('--one-slide-per-page', is_flag=True, default=True, help='One slide per page')
@click.option('--slide-size', type=click.Choice(['standard_4_3', 'standard_16_9', 'widescreen', 'a4']), 
               default='standard_4_3', help='Slide size')
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def export_powerpoint(ctx, one_slide_per_page: bool, slide_size: str, input_file: str, output_file: str):
    """Export PDF to PowerPoint presentation."""
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Exporting to PowerPoint..."):
        editor.load_document(input_file)
        
        operation = ExportToPowerPointOperation(
            output_path=output_file,
            one_slide_per_page=one_slide_per_page,
            slide_size=slide_size
        )
        editor.add_operation(operation)
        
        result = editor.execute_operations()
    
    console.print(Panel.fit(
        f"[green]✓[/green] PowerPoint export completed\\n"
        f"[blue]Slides created:[/blue] {result['slides_created']}\\n"
        f"[blue]Images extracted:[/blue] {result['images_extracted']}\\n"
        f"[blue]File size:[/blue] {result['file_size']:,} bytes\\n"
        f"[blue]Output:[/blue] {output_file}",
        title="PowerPoint Export"
    ))


@cli.command()
@click.option('--provider', '-p', type=click.Choice(['google_drive', 'dropbox']), 
               required=True, help='Cloud storage provider')
@click.option('--config', type=str, help='Configuration file for cloud service')
@click.argument('local_file')
@click.argument('cloud_path')
@click.pass_context
def cloud_upload(ctx, provider: str, config: str, local_file: str, cloud_path: str):
    """Upload PDF to cloud storage."""
    
    # Load configuration
    cloud_config = {}
    if config:
        try:
            with open(config, 'r') as f:
                cloud_config = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading config file: {e}[/red]")
            sys.exit(1)
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Uploading to {provider}..."):
        operation = CloudUploadOperation(
            local_path=local_file,
            provider=provider,
            cloud_path=cloud_path,
            config=cloud_config
        )
        
        result = operation.execute(editor)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Upload to {provider} completed\\n"
        f"[blue]Local file:[/blue] {result['local_file']}\\n"
        f"[blue]Cloud path:[/blue] {result['cloud_path']}\\n"
        f"[blue]File size:[/blue] {result['cloud_file']['size']:,} bytes",
        title="Cloud Upload"
    ))


@cli.command()
@click.option('--smtp-server', type=str, required=True, help='SMTP server address')
@click.option('--smtp-port', type=int, default=587, help='SMTP port')
@click.option('--username', type=str, required=True, help='Email username')
@click.option('--password', type=str, required=True, help='Email password or app password')
@click.option('--to', type=str, required=True, help='Recipient email addresses (comma-separated)')
@click.option('--subject', type=str, required=True, help='Email subject')
@click.option('--body', type=str, default='Please find the attached PDF document.', help='Email body')
@click.option('--from', 'from_addr', type=str, help='Sender email address')
@click.option('--use-tls', is_flag=True, default=True, help='Use TLS encryption')
@click.argument('input_file')
@click.pass_context
def email_pdf(ctx, smtp_server: str, smtp_port: int, username: str, password: str, 
               to: str, subject: str, body: str, from_addr: str, use_tls: bool, input_file: str):
    """Send PDF via email."""
    
    # Parse recipient addresses
    to_addresses = [addr.strip() for addr in to.split(',') if addr.strip()]
    
    editor = ctx.obj['editor']
    
    with console.status("[bold green]Sending email..."):
        editor.load_document(input_file)
        
        operation = EmailPDFOperation(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            use_tls=use_tls,
            from_address=from_addr
        )
        
        result = operation.execute(editor)
    
    console.print(Panel.fit(
        f"[green]✓[/green] Email sent successfully\\n"
        f"[blue]To:[/blue] {', '.join(result['to_addresses'])}\\n"
        f"[blue]Subject:[/blue] {result['subject']}\\n"
        f"[blue]From:[/blue] {result['from_address']}\\n"
        f"[blue]Server:[/blue] {result['smtp_server']}:{result['smtp_port']}\\n"
        f"[blue]Attachment size:[/blue] {result['attachment_size']:,} bytes",
        title="Email Sent"
    ))


@cli.command()
@click.option('--printer', '-p', type=str, help='Printer name')
@click.option('--copies', '-c', type=int, default=1, help='Number of copies')
@click.option('--pages', type=str, help='Pages to print (comma-separated)')
@click.option('--color/--no-color', default=True, help='Print in color')
@click.option('--duplex', is_flag=True, default=False, help='Print double-sided')
@click.option('--paper-size', type=click.Choice(['A4', 'A3', 'Letter', 'Legal']), 
               default='A4', help='Paper size')
@click.option('--orientation', type=click.Choice(['portrait', 'landscape']), 
               default='portrait', help='Paper orientation')
@click.argument('input_file')
@click.pass_context
def print_pdf(ctx, printer: str, copies: int, pages: str, color: bool, 
             duplex: bool, paper_size: str, orientation: str, input_file: str):
    """Print PDF with advanced options."""
    
    editor = ctx.obj['editor']
    
    with console.status(f"[bold green]Printing {copies} copies..."):
        editor.load_document(input_file)
        
        operation = PrintPDFOperation(
            printer_name=printer,
            copies=copies,
            pages=pages,
            color=color,
            duplex=duplex,
            paper_size=paper_size,
            orientation=orientation
        )
        
        result = operation.execute(editor)
    
    console.print(Panel.fit(
        f"[green]✓[/green] PDF sent to printer\\n"
        f"[blue]Printer:[/blue] {result['printer_name'] or 'default'}\\n"
        f"[blue]Copies:[/blue] {result['copies']}\\n"
        f"[blue]Pages:[/blue] {result['pages'] or 'all'}\\n"
        f"[blue]Color:[/blue] {'Yes' if result['color'] else 'No'}\\n"
        f"[blue]Duplex:[/blue] {'Yes' if result['duplex'] else 'No'}\\n"
        f"[blue]Paper size:[/blue] {result['paper_size']}\\n"
        f"[blue]Orientation:[/blue] {result['orientation']}",
        title="Print Job Sent"
    ))


@cli.command()
@click.option('--host', type=str, default='localhost', help='Host to bind to')
@click.option('--port', '-p', type=int, default=8000, help='Port to listen on')
@click.option('--upload-folder', type=str, default='uploads', help='Upload folder path')
@click.option('--debug', is_flag=True, default=False, help='Enable debug mode')
def web_api(host: str, port: int, upload_folder: str, debug: bool):
    """Start PDF processing web API server."""
    
    try:
        console.print(f"[green]🚀 Starting PDF Editor Web API[/green]")
        console.print(f"[blue]Host:[/blue] {host}")
        console.print(f"[blue]Port:[/blue] {port}")
        console.print(f"[blue]Upload folder:[/blue] {upload_folder}")
        console.print()
        
        # Create web service
        web_service = FlaskWebService(
            host=host,
            port=port,
            upload_folder=upload_folder
        )
        
        # Print API endpoints
        console.print("[cyan]Available API Endpoints:[/cyan]")
        console.print("• GET  /api/health - Health check")
        console.print("• POST /api/process/dark-mode - Convert to dark mode")
        console.print("• POST /api/process/extract-text - Extract text with OCR")
        console.print("• POST /api/process/compress - Compress PDF")
        console.print("• POST /api/export/word - Export to Word")
        console.print("• POST /api/export/excel - Export to Excel")
        console.print("• POST /api/export/powerpoint - Export to PowerPoint")
        console.print()
        
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")
        
        # Start server
        web_service.run()
        
    except Exception as e:
        console.print(f"[red]Error starting web API: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--gui', '-g', is_flag=True, help='Launch GUI instead of CLI')
@click.argument('input_file', required=False)
@click.argument('output_file', required=False)
@click.pass_context
def main(ctx, gui: bool, input_file: str, output_file: str):
    """PDF Editor with CLI and GUI modes."""
    if gui:
        # Launch GUI mode
        try:
            from ..gui.main_window import main as gui_main
            console.print("[green]🖥️  Launching PDF Editor GUI...[/green]")
            return gui_main()
        except ImportError as e:
            console.print(f"[red]Error: GUI dependencies not installed: {e}[/red]")
            console.print("[yellow]Please install PySide6: pip install PySide6[/yellow]")
            sys.exit(1)
    else:
        # Show available CLI commands
        console.print(Panel.fit(
            "[bold cyan]PDF Editor - CLI Mode[/bold cyan]\\n\\n"
            "Use 'python main.py --help' to see all available commands\\n\\n"
            "[bold]Common Commands:[/bold]\\n"
            "• dark-mode     - Convert PDF to dark mode\\n"
            "• create-field  - Create form fields\\n"
            "• add-annotation - Add annotations\\n"
            "• set-password  - Add password protection\\n"
            "• edit-metadata - Edit document metadata\\n\\n"
            "[bold]GUI Mode:[/bold]\\n"
            "• Use '--gui' flag to launch graphical interface\\n"
            "• Example: python main.py --gui",
            title="PDF Editor"
        ))


@cli.command()
@click.argument('input_file')
@click.argument('output_file')
@click.pass_context
def cli(ctx):
    """PDF Editor CLI."""
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['editor'] = PDFEditor(config_file=config)
    ctx.obj['verbose'] = verbose if 'verbose' in ctx.params else True


if __name__ == '__main__':
    cli()