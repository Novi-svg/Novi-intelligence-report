#!/usr/bin/env python3
"""
Novi's Daily Intelligence Report Generator
Runs daily at 5:00 AM IST via GitHub Actions
"""

import sys
import os
from datetime import datetime, timedelta
import logging

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
    format='%(asctime)s - %(levelname)s - %(message)s'
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
        
    def generate_report(self):
        """Generate and send the daily intelligence report"""
        try:
            logger.info("🚀 Starting Novi's Intelligence Report generation...")
            
            # Check if we should skip today
            if should_skip_today():
                logger.info("📅 Skipping report - excluded day")
                return
            
            # Collect data
            logger.info("📊 Collecting data...")
            report_data = self.collect_all_data()
            
            # Generate HTML report
            logger.info("📝 Generating HTML report...")
            html_content = self.generate_html_report(report_data)
            
            # Send email
            logger.info("📧 Sending email report...")
            subject = f"📊 Novi's Intelligence Report - {self.current_time.strftime('%B %d, %Y')}"
            self.email_sender.send_email(subject, html_content)
            
            logger.info("✅ Report sent successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error generating report: {str(e)}")
            self.send_error_notification(e)
            raise
    
    def collect_all_data(self):
        """Collect data from all sources"""
        data = {
            'date': self.current_time.strftime('%B %d, %Y'),
            'day': self.current_time.strftime('%A'),
            'time': self.current_time.strftime('%I:%M %p IST')
        }
        
        # News (Daily)
        logger.info("📰 Collecting news...")
        data['news'] = self.news_collector.get_all_news()
        
        # Stocks & Mutual Funds (Skip Sunday)
        if self.current_day != 6:  # Not Sunday
            logger.info("📈 Collecting stock data...")
            data['stocks'] = self.stock_collector.get_stock_data()
            data['mutual_funds'] = self.stock_collector.get_mutual_funds()
            data['investment_analysis'] = self.stock_collector.get_investment_analysis()
        
        # Jobs (Daily)
        logger.info("💼 Collecting job data...")
        data['jobs'] = self.jobs_collector.get_jobs()
        
        # SAP Data (Saturday only)
        if self.current_day == 5:  # Saturday
            logger.info("🔧 Collecting SAP data...")
            data['sap'] = self.sap_collector.get_sap_data()
        
        # Career Analysis (Bi-weekly: Saturday & Monday)
        if self.current_day in [0, 5]:  # Monday or Saturday
            logger.info("📊 Collecting career analysis...")
            data['career'] = self.sap_collector.get_career_analysis()
        
        return data
    
    def generate_html_report(self, data):
        """Generate HTML email content"""
        from jinja2 import Environment, FileSystemLoader
        
        # Load template
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('email_template.html')
        
        # Render template with data
        html_content = template.render(**data)
        return html_content
    
    def send_error_notification(self, error):
        """Send error notification email"""
        try:
            subject = "⚠️ Novi Intelligence Report - Error Alert"
            body = f"""
            <h2 style="color: #dc3545;">Error in Report Generation</h2>
            <p><strong>Time:</strong> {self.current_time}</p>
            <p><strong>Error:</strong> {str(error)}</p>
            <p><strong>Type:</strong> {type(error).__name__}</p>
            <hr>
            <p><em>The system will attempt to run again tomorrow.</em></p>
            """
            
            self.email_sender.send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")

def main():
    """Main execution function"""
    try:
        generator = ReportGenerator()
        generator.generate_report()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
