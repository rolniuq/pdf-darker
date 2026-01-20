"""Email and web service operations."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional
import json
import tempfile
import shutil

from ..core.base import BaseOperation, ProcessingError, ValidationError
from ..utils.logging import get_logger

logger = get_logger("operations.email_web")


class EmailPDFOperation(BaseOperation):
    """Send PDF via email."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, to_addresses: List[str], subject: str,
                 body: str, use_tls: bool = True, from_address: Optional[str] = None):
        super().__init__()
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to_addresses = to_addresses
        self.subject = subject
        self.body = body
        self.use_tls = use_tls
        self.from_address = from_address or username
    
    def validate(self, document) -> None:
        """Validate email operation parameters."""
        if not self.smtp_server:
            raise ValidationError("SMTP server is required")
        
        if not self.smtp_port or self.smtp_port < 1 or self.smtp_port > 65535:
            raise ValidationError("Valid SMTP port is required")
        
        if not self.username or not self.password:
            raise ValidationError("Email username and password are required")
        
        if not self.to_addresses:
            raise ValidationError("At least one recipient address is required")
        
        # Basic email validation
        for addr in self.to_addresses:
            if '@' not in addr or '.' not in addr.split('@')[1]:
                raise ValidationError(f"Invalid email address: {addr}")
        
        if not self.subject:
            raise ValidationError("Email subject is required")
    
    def execute(self, document) -> Dict:
        """Execute email sending."""
        try:
            logger.info(f"Sending PDF to {len(self.to_addresses)} recipients")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(self.to_addresses)
            msg['Subject'] = self.subject
            
            # Add body
            msg.attach(MIMEText(self.body, 'plain'))
            
            # Add PDF as attachment
            self._add_pdf_attachment(msg, document)
            
            # Send email
            self._send_email(msg)
            
            logger.info("Email sent successfully")
            
            return {
                'operation': 'email_pdf',
                'to_addresses': self.to_addresses,
                'subject': self.subject,
                'from_address': self.from_address,
                'smtp_server': self.smtp_server,
                'attachment_size': len(document.tobytes())
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise ProcessingError(f"Email sending failed: {e}")
    
    def _add_pdf_attachment(self, msg: MIMEMultipart, document):
        """Add PDF as email attachment."""
        try:
            # Get PDF bytes
            pdf_data = document.tobytes()
            
            # Create attachment
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename='document.pdf')
            
            msg.attach(attachment)
            
        except Exception as e:
            logger.error(f"Failed to attach PDF: {e}")
            raise ProcessingError(f"Failed to attach PDF to email: {e}")
    
    def _send_email(self, msg: MIMEMultipart):
        """Send email using SMTP."""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            # Upgrade to secure connection if using TLS
            if self.use_tls:
                server.starttls()
            
            # Login
            server.login(self.username, self.password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.from_address, self.to_addresses, text)
            
            # Close connection
            server.quit()
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise ProcessingError(f"Failed to send email: {e}")


# Web service operations would use frameworks like Flask or FastAPI
# Here's a framework for future implementation

class WebAPIServer:
    """Base class for PDF processing web API server."""
    
    def __init__(self, host: str = 'localhost', port: int = 8000):
        self.host = host
        self.port = port
        self.app = None
    
    def setup_routes(self):
        """Setup API routes."""
        pass
    
    def run(self):
        """Run the web server."""
        pass


class FlaskWebService(WebAPIServer):
    """Flask-based web service for PDF processing."""
    
    def __init__(self, host: str = 'localhost', port: int = 8000, 
                 upload_folder: str = 'uploads'):
        super().__init__(host, port)
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
        
        try:
            from flask import Flask, request, jsonify, send_file
            from werkzeug.utils import secure_filename
            
            self.Flask = Flask
            self.request = request
            self.jsonify = jsonify
            self.send_file = send_file
            self.secure_filename = secure_filename
            
            self.app = Flask(__name__)
            self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
            
        except ImportError:
            raise ValidationError("Flask is not installed. Install with: pip install flask")
    
    def setup_routes(self):
        """Setup Flask API routes."""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return self.jsonify({'status': 'healthy', 'service': 'pdf-editor-api'})
        
        @self.app.route('/api/process/dark-mode', methods=['POST'])
        def process_dark_mode():
            return self._handle_pdf_processing('dark_mode')
        
        @self.app.route('/api/process/extract-text', methods=['POST'])
        def extract_text():
            return self._handle_pdf_processing('extract_text')
        
        @self.app.route('/api/process/compress', methods=['POST'])
        def compress_pdf():
            return self._handle_pdf_processing('compress')
        
        @self.app.route('/api/process/batch', methods=['POST'])
        def batch_process():
            return self._handle_batch_processing()
        
        @self.app.route('/api/export/word', methods=['POST'])
        def export_word():
            return self._handle_export('word')
        
        @self.app.route('/api/export/excel', methods=['POST'])
        def export_excel():
            return self._handle_export('excel')
        
        @self.app.route('/api/export/powerpoint', methods=['POST'])
        def export_powerpoint():
            return self._handle_export('powerpoint')
    
    def _handle_pdf_processing(self, operation_type: str):
        """Handle single PDF processing operations."""
        try:
            if 'file' not in self.request.files:
                return self.jsonify({'error': 'No file provided'}), 400
            
            file = self.request.files['file']
            if file.filename == '':
                return self.jsonify({'error': 'No file selected'}), 400
            
            # Save uploaded file
            filename = self.secure_filename(file.filename)
            input_path = self.upload_folder / filename
            file.save(str(input_path))
            
            # Process file
            from ..core.editor import PDFEditor
            from ..operations.dark_mode import DarkModeOperation
            from ..operations.ocr_operations import OCRExtractTextOperation
            from ..operations.compression_operations import CompressPDFOperation
            
            editor = PDFEditor()
            editor.load_document(str(input_path))
            
            # Create operation based on type
            if operation_type == 'dark_mode':
                operation = DarkModeOperation()
            elif operation_type == 'extract_text':
                operation = OCRExtractTextOperation()
            elif operation_type == 'compress':
                operation = CompressPDFOperation()
            else:
                return self.jsonify({'error': 'Unknown operation'}), 400
            
            editor.add_operation(operation)
            result = editor.execute_operations()
            
            # Save output
            output_filename = f"processed_{filename}"
            output_path = self.upload_folder / output_filename
            editor.save_document(str(output_path))
            
            # Return result
            return self.jsonify({
                'success': True,
                'operation': operation_type,
                'result': result,
                'download_url': f'/api/download/{output_filename}'
            })
            
        except Exception as e:
            logger.error(f"API processing error: {e}")
            return self.jsonify({'error': str(e)}), 500
    
    def _handle_export(self, export_type: str):
        """Handle export operations."""
        try:
            if 'file' not in self.request.files:
                return self.jsonify({'error': 'No file provided'}), 400
            
            file = self.request.files['file']
            filename = self.secure_filename(file.filename)
            input_path = self.upload_folder / filename
            file.save(str(input_path))
            
            from ..core.editor import PDFEditor
            from ..operations.advanced_export_operations import (
                ExportToWordOperation, ExportToExcelOperation, ExportToPowerPointOperation
            )
            
            editor = PDFEditor()
            editor.load_document(str(input_path))
            
            # Create export operation
            if export_type == 'word':
                output_filename = filename.replace('.pdf', '.docx')
                output_path = self.upload_folder / output_filename
                operation = ExportToWordOperation(str(output_path))
            elif export_type == 'excel':
                output_filename = filename.replace('.pdf', '.xlsx')
                output_path = self.upload_folder / output_filename
                operation = ExportToExcelOperation(str(output_path))
            elif export_type == 'powerpoint':
                output_filename = filename.replace('.pdf', '.pptx')
                output_path = self.upload_folder / output_filename
                operation = ExportToPowerPointOperation(str(output_path))
            else:
                return self.jsonify({'error': 'Unknown export format'}), 400
            
            editor.add_operation(operation)
            result = editor.execute_operations()
            
            return self.jsonify({
                'success': True,
                'export_type': export_type,
                'result': result,
                'download_url': f'/api/download/{output_filename}'
            })
            
        except Exception as e:
            logger.error(f"API export error: {e}")
            return self.jsonify({'error': str(e)}), 500
    
    def _handle_batch_processing(self):
        """Handle batch processing requests."""
        try:
            # This would handle multiple file uploads and batch operations
            # For now, return a placeholder response
            return self.jsonify({
                'success': False,
                'message': 'Batch processing not yet implemented in web API'
            }), 501
            
        except Exception as e:
            logger.error(f"API batch processing error: {e}")
            return self.jsonify({'error': str(e)}), 500
    
    def run(self):
        """Run Flask web server."""
        self.setup_routes()
        
        # Add download route
        @self.app.route('/api/download/<filename>')
        def download_file(filename):
            try:
                file_path = self.upload_folder / filename
                if file_path.exists():
                    return self.send_file(str(file_path), as_attachment=True)
                else:
                    return self.jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return self.jsonify({'error': str(e)}), 500
        
        logger.info(f"Starting web API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)


class PrintPDFOperation(BaseOperation):
    """Print PDF with advanced options."""
    
    def __init__(self, printer_name: Optional[str] = None, copies: int = 1,
                 pages: Optional[str] = None, color: bool = True,
                 duplex: bool = False, paper_size: str = 'A4',
                 orientation: str = 'portrait'):
        super().__init__()
        self.printer_name = printer_name
        self.copies = copies
        self.pages = pages
        self.color = color
        self.duplex = duplex
        self.paper_size = paper_size
        self.orientation = orientation
    
    def validate(self, document) -> None:
        """Validate print operation parameters."""
        if self.copies < 1 or self.copies > 100:
            raise ValidationError("Number of copies must be between 1 and 100")
        
        valid_orientations = ['portrait', 'landscape']
        if self.orientation not in valid_orientations:
            raise ValidationError(f"Orientation must be one of: {', '.join(valid_orientations)}")
        
        valid_paper_sizes = ['A4', 'A3', 'Letter', 'Legal']
        if self.paper_size not in valid_paper_sizes:
            raise ValidationError(f"Paper size must be one of: {', '.join(valid_paper_sizes)}")
    
    def execute(self, document) -> Dict:
        """Execute PDF printing."""
        try:
            logger.info(f"Printing PDF with {self.copies} copies")
            
            # Save PDF to temporary file for printing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                document.save(str(tmp_file.name))
                tmp_path = tmp_file.name
            
            # Use system print command (platform-dependent)
            success = self._print_pdf(tmp_path)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            if not success:
                raise ProcessingError("Failed to print PDF")
            
            logger.info("PDF printed successfully")
            
            return {
                'operation': 'print_pdf',
                'printer_name': self.printer_name,
                'copies': self.copies,
                'pages': self.pages,
                'color': self.color,
                'duplex': self.duplex,
                'paper_size': self.paper_size,
                'orientation': self.orientation
            }
            
        except Exception as e:
            logger.error(f"PDF printing failed: {e}")
            raise ProcessingError(f"PDF printing failed: {e}")
    
    def _print_pdf(self, pdf_path: str) -> bool:
        """Print PDF using system command."""
        try:
            import platform
            
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows print command
                cmd = f'print /D:"{self.printer_name}" "{pdf_path}"'
            elif system == 'darwin':
                # macOS print command
                options = []
                if not self.color:
                    options.append('-o Color=false')
                if self.duplex:
                    options.append('-o Duplex=DuplexNoTumble')
                if self.copies > 1:
                    options.append(f'-n {self.copies}')
                
                printer_option = f'-p "{self.printer_name}"' if self.printer_name else ''
                cmd = f'lpr {printer_option} {" ".join(options)} "{pdf_path}"'
            else:
                # Linux print command
                options = []
                if not self.color:
                    options.append('-o Color=false')
                if self.duplex:
                    options.append('-o Duplex=DuplexNoTumble')
                if self.copies > 1:
                    options.append(f'-n {self.copies}')
                
                printer_option = f'-P {self.printer_name}' if self.printer_name else ''
                cmd = f'lpr {printer_option} {" ".join(options)} "{pdf_path}"'
            
            # Execute print command
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Print command execution failed: {e}")
            return False