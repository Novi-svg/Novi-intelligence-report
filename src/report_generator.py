#!/usr/bin/env python3
"""
Novi's Daily Intelligence Report Generator with PDF Support
"""

import sys
import os
from datetime import datetime, timedelta
import logging
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, get_ist_time, should_skip_today
from src.data_collectors.news_collector import NewsCollector
from src.data_collectors.stock_collector import StockCollector
from src.data_collectors.jobs_collector import JobsCollector
from src.data_collectors.sap_collector import SAPCollector
from src.utils.email_sender import EmailSender
from src.utils.pdf_generator import PDFGenerator

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
        self.pdf_generator = PDFGenerator()
        
        # Create reports directory
        self.reports_dir = Path('reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        logger.info(f"🎯 Report Generator initialized for {self.current_time.strftime('%A, %B %d, %Y')}")

    def generate_report(self):
        """Generate and send the daily intelligence report as PDF"""
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

            # Generate PDF filename
            filename = f"novi_report_{self.current_time.strftime('%Y%m%d_%H%M')}.pdf"
            pdf_path = self.reports_dir / filename

            # Generate PDF report
            logger.info("📄 Generating PDF report...")
            self.pdf_generator.generate_pdf_report(report_data, str(pdf_path))
            
            # Get PDF file size
            pdf_size_mb = self.pdf_generator.get_pdf_size_mb(str(pdf_path))
            logger.info(f"📊 PDF generated: {pdf_size_mb:.1f} MB")

            # Send email with PDF attachment
            logger.info("📧 Sending email with PDF attachment...")
            subject = f"📊 Novi's Intelligence Report - {self.current_time.strftime('%B %d, %Y')}"
            success = self.email_sender.send_pdf_report(subject, str(pdf_path), pdf_size_mb)

            if success:
                logger.info("✅ PDF Report sent successfully!")
                self.log_success_metrics(report_data, pdf_size_mb)
            else:
                raise Exception("Email sending failed")

        except Exception as e:
            logger.error(f"❌ Error generating report: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.send_error_notification(e)
            raise

    def collect_all_data(self):
        """Collect data from all sources with error handling"""
        data = {
            'date': self.current_time.strftime('%B %d, %Y'),
            'day': self.current_time.strftime('%A'),
            'time': self.current_time.strftime('%I:%M %p'),
            'timezone': 'IST',
            'generation_time': self.current_time.isoformat()
        }

        # News (Daily) - Always collect
        try:
            logger.info("📰 Collecting news data...")
            data['news'] = self.news_collector.get_all_news()
            logger.info(f"✅ News collected: {len(data['news'].get('global', []))} global, {len(data['news'].get('india', []))} India")
        except Exception as e:
            logger.error(f"❌ News collection failed: {e}")
            data['news'] = {'global': [], 'india': [], 'business': [], 'regional': []}

        # Stocks & Mutual Funds (Skip Sunday for market data)
        if self.current_day != 6:  # Not Sunday
            try:
                logger.info("📈 Collecting stock market data...")
                data['stocks'] = self.stock_collector.get_stock_data()
                logger.info(f"✅ Stocks collected: {len(data['stocks'].get('large_cap', []))} large cap, {len(data['stocks'].get('mid_cap', []))} mid cap")
                
                logger.info("🏦 Collecting mutual fund data...")
                data['mutual_funds'] = self.stock_collector.get_mutual_funds()
                logger.info(f"✅ Mutual funds collected: {sum(len(funds) for funds in data['mutual_funds'].values())} total")
                
                logger.info("📊 Generating investment analysis...")
                data['investment_analysis'] = self.stock_collector.get_investment_analysis()
                logger.info("✅ Investment analysis generated")
            except Exception as e:
                logger.error(f"❌ Stock/MF collection failed: {e}")
                data['stocks'] = {'large_cap': [], 'mid_cap': [], 'small_cap': [], 'analysis': {}}
                data['mutual_funds'] = {'large_cap': [], 'mid_cap': [], 'small_cap': [], 'flexi_cap': []}
                data['investment_analysis'] = {}
        else:
            logger.info("📅 Skipping market data (Sunday)")

        # Jobs (Daily) - Always collect
        try:
            logger.info("💼 Collecting job opportunities...")
            data['jobs'] = self.jobs_collector.get_jobs()
            logger.info(f"✅ Jobs collected: {len(data['jobs'])} opportunities")
        except Exception as e:
            logger.error(f"❌ Jobs collection failed: {e}")
            data['jobs'] = []

        # SAP Data (Saturday only)
        if self.current_day == 5:  # Saturday
            try:
                logger.info("🔧 Collecting SAP weekly insights...")
                data['sap'] = self.sap_collector.get_sap_data()
                logger.info("✅ SAP data collected")
            except Exception as e:
                logger.error(f"❌ SAP data collection failed: {e}")
                data['sap'] = {}

        # Career Analysis (Bi-weekly: Monday & Saturday)
        if self.current_day in [0, 5]:  # Monday or Saturday
            try:
                logger.info("📊 Collecting career analysis...")
                data['career'] = self.sap_collector.get_career_analysis()
                logger.info("✅ Career analysis collected")
            except Exception as e:
                logger.error(f"❌ Career analysis failed: {e}")
                data['career'] = {}

        return data

    def log_success_metrics(self, data, pdf_size_mb):
        """Log success metrics"""
        try:
            metrics = {
                'news_items': len(data.get('news', {}).get('global', [])) + len(data.get('news', {}).get('india', [])),
                'stock_items': len(data.get('stocks', {}).get('large_cap', [])) + len(data.get('stocks', {}).get('mid_cap', [])),
                'job_items': len(data.get('jobs', [])),
                'pdf_size_mb': pdf_size_mb,
                'generation_time': data.get('generation_time')
            }
            
            logger.info("📊 Success Metrics:")
            logger.info(f"   📰 News Items: {metrics['news_items']}")
            logger.info(f"   📈 Stock Items: {metrics['stock_items']}")
            logger.info(f"   💼 Job Items: {metrics['job_items']}")
            logger.info(f"   📄 PDF Size: {metrics['pdf_size_mb']:.1f} MB")
            logger.info(f"   ⏱️ Generated: {metrics['generation_time']}")
            
        except Exception as e:
            logger.warning(f"Could not log metrics: {e}")

    def send_error_notification(self, error):
        """Send error notification"""
        try:
            error_msg = f"Report generation failed: {str(error)}"
            self.email_sender.send_error_notification(error_msg, "PDF Report Generation Error")
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

def main():
    """Main function"""
    try:
        generator = ReportGenerator()
        generator.generate_report()
        logger.info("🎉 Report generation completed successfully!")
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
