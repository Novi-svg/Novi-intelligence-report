#!/usr/bin/env python3
"""
Novi's Daily Intelligence Report Generator (Updated)
- No API dependencies
- Dynamic stock and mutual fund selection
- Enhanced web scraping
- Better error handling
"""

import sys
import os
from datetime import datetime, timedelta
import logging
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, get_ist_time, should_skip_today
from src.data_collectors.news_collector import NewsCollector
from src.data_collectors.stock_collector import StockCollector
from src.data_collectors.jobs_collector import JobsCollector
from src.data_collectors.sap_collector import SAPCollector
from src.utils.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/novi_report.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.config = Config()
        self.current_time = get_ist_time()
        self.current_day = self.current_time.weekday()  # 0=Monday, 6=Sunday
        
        # Initialize collectors
        self.news_collector = NewsCollector()
        self.stock_collector = StockCollector()
        self.jobs_collector = JobsCollector()
        self.sap_collector = SAPCollector()
        self.email_sender = EmailSender()
        
        logger.info(f"🎯 Report Generator initialized for {self.current_time.strftime('%A, %B %d, %Y')}")
        
    def generate_report(self):
        """Generate and send the daily intelligence report"""
        try:
            logger.info("🚀 Starting Novi's Intelligence Report generation...")
            
            # Check if we should skip today
            if should_skip_today():
                logger.info("📅 Skipping report - excluded day")
                return
            
            # Validate email configuration
            config_issues = self.email_sender.validate_configuration()
            if config_issues:
                for issue in config_issues:
                    logger.error(f"❌ Config issue: {issue}")
                raise ValueError("Email configuration is invalid")
            
            # Collect data with progress tracking
            logger.info("📊 Collecting data from all sources...")
            report_data = self.collect_all_data()
            
            # Generate HTML report
            logger.info("📝 Generating HTML report...")
            html_content = self.generate_html_report(report_data)
            
            # Send email
            logger.info("📧 Sending email report...")
            subject = f"📊 Novi's Intelligence Report - {self.current_time.strftime('%B %d, %Y')}"
            success = self.email_sender.send_email(subject, html_content)
            
            if success:
                logger.info("✅ Report sent successfully!")
                self.log_success_metrics(report_data)
            else:
                raise Exception("Email sending failed")
            
        except Exception as e:
            logger.error(f"❌ Error generating report: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.send_error_notification(e
