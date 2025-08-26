#!/usr/bin/env python3
"""
Enhanced Email Sender with PDF Attachment Support
"""

import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.config = Config()
        
    def validate_configuration(self):
        """Validate email configuration"""
        issues = []
        
        if not self.config.EMAIL_FROM:
            issues.append("EMAIL_FROM environment variable not set")
        if not self.config.EMAIL_PASSWORD:
            issues.append("EMAIL_PASSWORD environment variable not set")
        if not self.config.EMAIL_TO:
            issues.append("EMAIL_TO environment variable not set")
            
        return issues
    
    def send_pdf_report(self, subject: str, pdf_path: str, pdf_size_mb: float) -> bool:
        """Send email with PDF attachment."""
        try:
            logger.info("📧 Preparing email with PDF attachment...")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_FROM
            msg['To'] = self.config.EMAIL_TO
            msg['Subject'] = subject
            
            # Create email body
            body = self._create_notification_email_body(pdf_size_mb)
            msg.attach(MIMEText(body, 'plain'))
            
            # Add PDF attachment
            with open(pdf_path, 'rb') as pdf_file:
                pdf_attachment = MIMEApplication(pdf_file.read(), _subtype='pdf')
                pdf_attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=os.path.basename(pdf_path)
                )
                msg.attach(pdf_attachment)
            
            # Send email
            logger.info("🔗 Connecting to SMTP server...")
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_FROM, self.config.EMAIL_PASSWORD)
            
            logger.info("📤 Sending email...")
            text = msg.as_string()
            server.sendmail(self.config.EMAIL_FROM, self.config.EMAIL_TO, text)
            server.quit()
            
            logger.info("✅ Email sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {str(e)}")
            return False
    
    def _create_notification_email_body(self, pdf_size_mb: float) -> str:
        """Create a simple notification email body."""
        current_time = datetime.now(self.config.IST)
        body = f"""📊 Novi's Intelligence Report - {current_time.strftime('%B %d, %Y')}

Your comprehensive intelligence report is ready! Please find the detailed PDF report attached.

📋 Report Summary:
• Generated: {current_time.strftime('%A, %B %d, %Y at %I:%M %p IST')}
• Format: Professional PDF Document
• Size: {pdf_size_mb:.1f} MB
• Contains: Market Analysis, News Updates, Job Opportunities, Career Insights

📈 What's Inside:
• Real-time stock market analysis with performance indicators
• Latest global and India news updates with priority categorization
• Curated SAP job opportunities matching your profile
• Investment recommendations and market outlook
• Career development insights and future trends

💡 Key Features:
• Visual charts and performance indicators
• Color-coded stock movements and news priorities  
• Professional formatting optimized for reading
• Mobile-friendly design that prints well

🔗 System Details:
• Powered by Novi's Intelligence System
• Automated data collection from multiple sources
• Daily delivery at 5:00 AM IST via GitHub Actions
• All data sources verified and up-to-date

📧 Support:
For any issues or suggestions, please check your GitHub Actions workflow logs or create an issue in your repository.

Best regards,
🤖 Novi's Intelligence System

---
This is an automated message. Please do not reply to this email.
Generated with ❤️ by your personal intelligence system.
        """
        return body.strip()
    
    def send_error_notification(self, error_message: str, error_type: str = "Report Generation Error") -> bool:
        """Send error notification email."""
        try:
            subject = f"🚨 {error_type} - {datetime.now().strftime('%Y-%m-%d %H:%M IST')}"
            
            body = f"""🚨 Novi's Intelligence Report Error Notification

An error occurred while generating your daily intelligence report.

📊 Error Details:
• Time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p IST')}
• Type: {error_type}
• Message: {error_message}

🔧 Next Steps:
1. Check GitHub Actions logs for detailed error information
2. Verify all environment variables are properly set
3. Ensure all required dependencies are installed
4. Check data source availability

📋 System Status:
• The system will automatically retry tomorrow
• Previous reports remain unaffected
• Check repository issues for similar problems

🔗 Troubleshooting:
• Review workflow logs in GitHub Actions tab
• Verify email credentials are still valid
• Check if any data sources have changed their structure

This notification was sent to ensure you're aware of the issue.

Best regards,
🤖 Novi's Intelligence System (Error Handler)
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_FROM
            msg['To'] = self.config.EMAIL_TO
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_FROM, self.config.EMAIL_PASSWORD)
            server.sendmail(self.config.EMAIL_FROM, self.config.EMAIL_TO, msg.as_string())
            server.quit()
            
            logger.info("📧 Error notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send error notification: {str(e)}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration."""
        try:
            current_time = datetime.now(self.config.IST)
            
            subject = f"✅ Novi's Intelligence System - Test Email - {current_time.strftime('%Y-%m-%d %H:%M IST')}"
            
            body = f"""✅ Email Configuration Test Successful!

🎯 Test Results:
• SMTP Connection: ✅ Working
• Authentication: ✅ Successful  
• Email Delivery: ✅ Working

📊 Configuration Details:
• Test Date: {current_time.strftime('%A, %B %d, %Y at %I:%M %p IST')}
• From: {self.config.EMAIL_FROM}
• To: {self.config.EMAIL_TO}
• Server: {self.config.SMTP_SERVER}:{self.config.SMTP_PORT}

🚀 Next Steps:
• Your email configuration is working properly
• Daily PDF reports will be sent at 5:00 AM IST
• Check GitHub Actions logs for any issues
• The system is ready for automated report delivery

📧 System Status:
• ✅ Gmail SMTP connection: Working
• ✅ Authentication: Successful
• ✅ PDF email delivery: Ready

This test confirms your Novi's Intelligence System is properly configured and ready to deliver daily PDF reports.

Best regards,
🤖 Novi's Intelligence System (Test Mode)
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_FROM
            msg['To'] = self.config.EMAIL_TO
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_FROM, self.config.EMAIL_PASSWORD)
            server.sendmail(self.config.EMAIL_FROM, self.config.EMAIL_TO, msg.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test email failed: {str(e)}")
            return False
