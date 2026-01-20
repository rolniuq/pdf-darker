"""Batch operations for processing multiple PDF files."""

import os
import glob
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass

from ..core.base import BaseOperation, ProcessingError, ValidationError
from ..core.editor import PDFEditor
from ..utils.logging import get_logger

logger = get_logger("operations.batch")


@dataclass
class BatchTask:
    """Represents a single batch processing task."""
    input_file: Path
    output_file: Path
    operations: List[Dict]
    metadata: Dict[str, Any]


@dataclass
class BatchResult:
    """Represents the result of a batch task."""
    task: BatchTask
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0
    output_size: Optional[int] = None


class BatchProcessOperation(BaseOperation):
    """Process multiple PDF files with specified operations."""
    
    def __init__(self, input_pattern: str, output_dir: str, 
                 operations: List[Dict], max_workers: int = 4,
                 continue_on_error: bool = True, preserve_structure: bool = True):
        super().__init__()
        self.input_pattern = input_pattern
        self.output_dir = Path(output_dir)
        self.operations = operations
        self.max_workers = max_workers
        self.continue_on_error = continue_on_error
        self.preserve_structure = preserve_structure
    
    def validate(self, document) -> None:
        """Validate batch operation parameters."""
        if not self.input_pattern:
            raise ValidationError("Input pattern cannot be empty")
        
        if not self.output_dir:
            raise ValidationError("Output directory cannot be empty")
        
        if not self.operations:
            raise ValidationError("At least one operation must be specified")
        
        if self.max_workers < 1:
            raise ValidationError("Max workers must be at least 1")
        
        # Test if input pattern finds files
        input_files = glob.glob(self.input_pattern)
        if not input_files:
            raise ValidationError(f"No files found matching pattern: {self.input_pattern}")
    
    def execute(self, document) -> Dict:
        """Execute batch processing."""
        try:
            logger.info(f"Starting batch processing for pattern: {self.input_pattern}")
            start_time = time.time()
            
            # Find input files
            input_files = [Path(f) for f in glob.glob(self.input_pattern)]
            logger.info(f"Found {len(input_files)} files to process")
            
            # Create batch tasks
            tasks = self._create_batch_tasks(input_files)
            logger.info(f"Created {len(tasks)} batch tasks")
            
            # Execute batch tasks
            results = self._execute_batch_tasks(tasks)
            
            # Calculate statistics
            successful_tasks = [r for r in results if r.success]
            failed_tasks = [r for r in results if not r.success]
            
            total_time = time.time() - start_time
            total_input_size = sum(task.input_file.stat().st_size for task in tasks)
            total_output_size = sum(r.output_size for r in successful_tasks if r.output_size)
            
            logger.info(f"Batch processing completed in {total_time:.2f}s")
            logger.info(f"Successful: {len(successful_tasks)}, Failed: {len(failed_tasks)}")
            
            return {
                'operation': 'batch_process',
                'total_files': len(tasks),
                'successful': len(successful_tasks),
                'failed': len(failed_tasks),
                'total_time': total_time,
                'total_input_size': total_input_size,
                'total_output_size': total_output_size,
                'results': results,
                'output_directory': str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise ProcessingError(f"Batch processing failed: {e}")
    
    def _create_batch_tasks(self, input_files: List[Path]) -> List[BatchTask]:
        """Create batch tasks from input files."""
        tasks = []
        
        for input_file in input_files:
            try:
                # Determine output file path
                if self.preserve_structure:
                    # Preserve directory structure
                    relative_path = input_file.name  # Simplified for now
                    output_file = self.output_dir / relative_path
                else:
                    # Flatten structure
                    output_file = self.output_dir / input_file.name
                
                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                task = BatchTask(
                    input_file=input_file,
                    output_file=output_file,
                    operations=self.operations.copy(),
                    metadata={
                        'original_size': input_file.stat().st_size,
                        'created_time': time.time()
                    }
                )
                tasks.append(task)
                
            except Exception as e:
                logger.error(f"Failed to create task for {input_file}: {e}")
                if not self.continue_on_error:
                    raise
        
        return tasks
    
    def _execute_batch_tasks(self, tasks: List[BatchTask]) -> List[BatchResult]:
        """Execute batch tasks using thread pool."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._process_single_file, task): task
                for task in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        logger.info(f"✓ Processed: {task.input_file.name}")
                    else:
                        logger.error(f"✗ Failed: {task.input_file.name} - {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"Exception processing {task.input_file.name}: {e}")
                    results.append(BatchResult(
                        task=task,
                        success=False,
                        error_message=str(e)
                    ))
                    
                    if not self.continue_on_error:
                        # Cancel remaining tasks
                        for remaining_future in future_to_task:
                            remaining_future.cancel()
                        break
        
        return results
    
    def _process_single_file(self, task: BatchTask) -> BatchResult:
        """Process a single file."""
        start_time = time.time()
        
        try:
            # Create PDF editor for this task
            editor = PDFEditor()
            
            # Load document
            editor.load_document(str(task.input_file))
            
            # Apply operations
            for op_config in task.operations:
                operation = self._create_operation_from_config(op_config)
                editor.add_operation(operation)
            
            # Execute operations
            editor.execute_operations()
            
            # Save document
            editor.save_document(str(task.output_file))
            
            # Calculate result
            processing_time = time.time() - start_time
            output_size = task.output_file.stat().st_size if task.output_file.exists() else None
            
            return BatchResult(
                task=task,
                success=True,
                processing_time=processing_time,
                output_size=output_size
            )
            
        except Exception as e:
            return BatchResult(
                task=task,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _create_operation_from_config(self, op_config: Dict) -> BaseOperation:
        """Create operation object from configuration."""
        # Import all operation classes
        from .dark_mode import DarkModeOperation
        from .form_operations import CreateFormFieldOperation, FillFormFieldOperation
        from .annotation_operations import AddAnnotationOperation
        from .security_operations import SetPasswordOperation, EditMetadataOperation
        from .ocr_operations import OCRExtractTextOperation, OCREditTextOperation
        
        # Operation type mapping
        operation_classes = {
            'dark_mode': DarkModeOperation,
            'create_field': CreateFormFieldOperation,
            'fill_field': FillFormFieldOperation,
            'add_annotation': AddAnnotationOperation,
            'set_password': SetPasswordOperation,
            'edit_metadata': EditMetadataOperation,
            'ocr_extract_text': OCRExtractTextOperation,
            'ocr_edit_text': OCREditTextOperation
        }
        
        op_type = op_config.get('type')
        if op_type not in operation_classes:
            raise ValidationError(f"Unknown operation type: {op_type}")
        
        op_class = operation_classes[op_type]
        params = op_config.get('parameters', {})
        
        return op_class(**params)


class BatchTemplateOperation(BaseOperation):
    """Apply a predefined template to multiple PDF files."""
    
    def __init__(self, input_pattern: str, output_dir: str, template_name: str,
                 template_params: Optional[Dict] = None, max_workers: int = 4):
        super().__init__()
        self.input_pattern = input_pattern
        self.output_dir = Path(output_dir)
        self.template_name = template_name
        self.template_params = template_params or {}
        self.max_workers = max_workers
    
    def validate(self, document) -> None:
        """Validate template operation parameters."""
        if not self.template_name:
            raise ValidationError("Template name cannot be empty")
        
        # Load template to validate it exists
        template = self._load_template()
        if not template:
            raise ValidationError(f"Template not found: {self.template_name}")
    
    def execute(self, document) -> Dict:
        """Execute template-based batch processing."""
        try:
            # Load template
            template = self._load_template()
            
            # Apply template parameters
            operations = self._apply_template_params(template['operations'], self.template_params)
            
            # Create and execute batch operation
            batch_op = BatchProcessOperation(
                input_pattern=self.input_pattern,
                output_dir=str(self.output_dir),
                operations=operations,
                max_workers=self.max_workers
            )
            
            return batch_op.execute(document)
            
        except Exception as e:
            logger.error(f"Template batch processing failed: {e}")
            raise ProcessingError(f"Template batch processing failed: {e}")
    
    def _load_template(self) -> Optional[Dict]:
        """Load template from file."""
        templates_dir = Path(__file__).parent.parent.parent / "templates"
        template_file = templates_dir / f"{self.template_name}.json"
        
        if template_file.exists():
            with open(template_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def _apply_template_params(self, operations: List[Dict], params: Dict) -> List[Dict]:
        """Apply template parameters to operations."""
        applied_operations = []
        
        for op in operations:
            applied_op = op.copy()
            
            # Replace parameter placeholders
            if 'parameters' in applied_op:
                for param_name, param_value in applied_op['parameters'].items():
                    if isinstance(param_value, str) and param_value.startswith('${') and param_value.endswith('}'):
                        param_key = param_value[2:-1]  # Remove ${ and }
                        if param_key in params:
                            applied_op['parameters'][param_name] = params[param_key]
            
            applied_operations.append(applied_op)
        
        return applied_operations


class BatchReportOperation(BaseOperation):
    """Generate a report from batch processing results."""
    
    def __init__(self, results_file: str, report_format: str = 'json',
                 output_file: Optional[str] = None):
        super().__init__()
        self.results_file = Path(results_file)
        self.report_format = report_format.lower()
        self.output_file = output_file
    
    def validate(self, document) -> None:
        """Validate report operation parameters."""
        if not self.results_file.exists():
            raise ValidationError(f"Results file not found: {self.results_file}")
        
        if self.report_format not in ['json', 'csv', 'html']:
            raise ValidationError("Report format must be 'json', 'csv', or 'html'")
    
    def execute(self, document) -> Dict:
        """Generate batch processing report."""
        try:
            # Load results
            with open(self.results_file, 'r') as f:
                results_data = json.load(f)
            
            # Generate report based on format
            if self.report_format == 'json':
                report_content = self._generate_json_report(results_data)
            elif self.report_format == 'csv':
                report_content = self._generate_csv_report(results_data)
            elif self.report_format == 'html':
                report_content = self._generate_html_report(results_data)
            
            # Save report
            if self.output_file:
                with open(self.output_file, 'w') as f:
                    f.write(report_content)
            
            return {
                'operation': 'batch_report',
                'format': self.report_format,
                'output_file': self.output_file,
                'results_processed': len(results_data.get('results', []))
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ProcessingError(f"Report generation failed: {e}")
    
    def _generate_json_report(self, results_data: Dict) -> str:
        """Generate JSON format report."""
        return json.dumps(results_data, indent=2)
    
    def _generate_csv_report(self, results_data: Dict) -> str:
        """Generate CSV format report."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'File Name', 'Status', 'Processing Time', 'Original Size', 
            'Output Size', 'Size Reduction', 'Error Message'
        ])
        
        # Write results
        for result in results_data.get('results', []):
            task = result['task']
            original_size = task['metadata']['original_size']
            output_size = result.get('output_size', 0)
            size_reduction = ((original_size - output_size) / original_size * 100) if original_size > 0 else 0
            
            writer.writerow([
                task['input_file'],
                'Success' if result['success'] else 'Failed',
                f"{result.get('processing_time', 0):.2f}s",
                original_size,
                output_size,
                f"{size_reduction:.1f}%",
                result.get('error_message', '')
            ])
        
        return output.getvalue()
    
    def _generate_html_report(self, results_data: Dict) -> str:
        """Generate HTML format report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Batch Processing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .success { color: green; }
        .failure { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .status-success { background-color: #d4edda; }
        .status-failure { background-color: #f8d7da; }
    </style>
</head>
<body>
    <h1>Batch Processing Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Files: {total_files}</p>
        <p class="success">Successful: {successful}</p>
        <p class="failure">Failed: {failed}</p>
        <p>Total Time: {total_time:.2f} seconds</p>
        <p>Input Size: {input_size:,} bytes</p>
        <p>Output Size: {output_size:,} bytes</p>
    </div>
    
    <h2>Details</h2>
    <table>
        <thead>
            <tr>
                <th>File Name</th>
                <th>Status</th>
                <th>Processing Time</th>
                <th>Original Size</th>
                <th>Output Size</th>
                <th>Size Reduction</th>
                <th>Error Message</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
        """
        
        # Generate table rows
        table_rows = []
        for result in results_data.get('results', []):
            task = result['task']
            status_class = 'status-success' if result['success'] else 'status-failure'
            status_text = 'Success' if result['success'] else 'Failed'
            
            original_size = task['metadata']['original_size']
            output_size = result.get('output_size', 0)
            size_reduction = ((original_size - output_size) / original_size * 100) if original_size > 0 else 0
            
            table_rows.append(f"""
            <tr class="{status_class}">
                <td>{task['input_file']}</td>
                <td>{status_text}</td>
                <td>{result.get('processing_time', 0):.2f}s</td>
                <td>{original_size:,}</td>
                <td>{output_size:,}</td>
                <td>{size_reduction:.1f}%</td>
                <td>{result.get('error_message', '')}</td>
            </tr>
            """)
        
        return html_template.format(
            total_files=results_data.get('total_files', 0),
            successful=results_data.get('successful', 0),
            failed=results_data.get('failed', 0),
            total_time=results_data.get('total_time', 0),
            input_size=results_data.get('total_input_size', 0),
            output_size=results_data.get('total_output_size', 0),
            table_rows=''.join(table_rows)
        )