#!/usr/bin/env python3
"""
PDF Report Generator for Novi's Intelligence System
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from config import Config

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.config = Config()
        self.template_dir = Path(__file__).parent.parent / 'templates'
        
        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
    def generate_pdf_report(self, report_data: dict, output_path: str) -> str:
        """Generate PDF from report data using WeasyPrint."""
        try:
            logger.info("📄 Loading PDF template...")
            template = self.jinja_env.get_template('pdf_report_template.html')
            
            # Add current timestamp to data if not present
            if 'date' not in report_data:
                current_time = datetime.now(self.config.IST)
                report_data.update({
                    'date': current_time.strftime('%B %d, %Y'),
                    'day': current_time.strftime('%A'),
                    'time': current_time.strftime('%I:%M %p'),
                    'timezone': 'IST'
                })
            
            logger.info("🔄 Rendering HTML content...")
            html_content = template.render(**report_data)
            
            logger.info("📑 Converting HTML to PDF...")
            html_doc = HTML(string=html_content, base_url=str(self.template_dir))
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate PDF
            html_doc.write_pdf(output_path)
            logger.info(f"✅ PDF generated successfully: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error generating PDF: {str(e)}")
            raise
            
    def get_pdf_size_mb(self, pdf_path: str) -> float:
        """Get PDF file size in MB."""
        try:
            size_bytes = os.path.getsize(pdf_path)
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
