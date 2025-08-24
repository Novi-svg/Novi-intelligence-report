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
            self.send_error_notification(e)
            raise
    
    def collect_all_data(self):
        """Collect data from all sources with error handling"""
        data = {
            'date': self.current_time.strftime('%B %d, %Y'),
            'day': self.current_time.strftime('%A'),
            'time': self.current_time.strftime('%I:%M %p IST'),
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
    
    def generate_html_report(self, data):
        """Generate HTML email content using Jinja2 template"""
        try:
            from jinja2 import Environment, FileSystemLoader
            
            # Load template
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template('email_template.html')
            
            # Add some helper functions to template context
            data['has_market_data'] = bool(data.get('stocks') and data['stocks'].get('large_cap'))
            data['has_jobs'] = bool(data.get('jobs'))
            data['has_sap_data'] = bool(data.get('sap'))
            data['has_career_data'] = bool(data.get('career'))
            
            # Render template with data
            html_content = template.render(**data)
            
            logger.info(f"✅ HTML report generated ({len(html_content)} characters)")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ HTML generation failed: {e}")
            # Return a simple fallback HTML
            return self._generate_fallback_html(data)
    
    def _generate_fallback_html(self, data):
        """Generate simple fallback HTML if template fails"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Novi's Intelligence Report - {data['date']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #4facfe; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }}
                .error {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Novi's Intelligence Report</h1>
                <p>{data['date']} • {data['day']}</p>
            </div>
            
            <div class="section">
                <p class="error">⚠️ Report template error occurred. Basic report generated.</p>
                <p><strong>Time:</strong> {data['time']}</p>
                <p><strong>News Items:</strong> {len(data.get('news', {}).get('global', []))}</p>
                <p><strong>Jobs Found:</strong> {len(data.get('jobs', []))}</p>
                <p><strong>Status:</strong> System is working, template needs attention</p>
            </div>
            
            <div class="section">
                <h3>📰 Latest News</h3>
                {''.join([f'<p>• {item.get("title", "")}</p>' for item in data.get('news', {}).get('global', [])[:5]])}
            </div>
            
            <div class="section">
                <h3>💼 Job Opportunities</h3>
                {''.join([f'<p>• {job.get("title", "")} at {job.get("company", "")}</p>' for job in data.get('jobs', [])[:5]])}
            </div>
        </body>
        </html>
        """
        return html
    
    def send_error_notification(self, error):
        """Send error notification email"""
        try:
            error_details = {
                'error_message': str(error),
                'error_type': type(error).__name__,
                'timestamp': self.current_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'traceback': traceback.format_exc()
            }
            
            self.email_sender.send_error_notification(
                error_details['traceback'], 
                error_details['error_type']
            )
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
    
    def log_success_metrics(self, report_data):
        """Log success metrics for monitoring"""
        try:
            metrics = {
                'news_count': len(report_data.get('news', {}).get('global', [])),
                'jobs_count': len(report_data.get('jobs', [])),
                'stocks_count': len(report_data.get('stocks', {}).get('large_cap', [])),
                'generation_time': self.current_time.isoformat(),
                'report_type': self._get_report_type()
            }
            
            logger.info("📈 Success Metrics:")
            for key, value in metrics.items():
                logger.info(f"  {key}: {value}")
                
        except Exception as e:
            logger.warning(f"Could not log metrics: {e}")
    
    def _get_report_type(self):
        """Determine the type of report being generated"""
        report_types = []
        
        if self.current_day != 6:  # Not Sunday
            report_types.append("Markets")
        
        if self.current_day == 5:  # Saturday
            report_types.append("SAP-Weekly")
        
        if self.current_day in [0, 5]:  # Monday or Saturday
            report_types.append("Career-Analysis")
        
        report_types.append("Daily")
        
        return "+".join(report_types)

def main():
    """Main execution function with enhanced error handling"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 NOVI'S INTELLIGENCE REPORT SYSTEM")
        logger.info("=" * 50)
        
        # Create report generator
        generator = ReportGenerator()
        
        # Generate and send report
        generator.generate_report()
        
        logger.info("=" * 50)
        logger.info("✅ REPORT GENERATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("⏹️  Report generation interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ FATAL ERROR IN REPORT GENERATION")
        logger.error("=" * 50)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Type: {type(e).__name__}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
