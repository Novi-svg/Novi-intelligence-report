pythonimport smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.config = Config()
    
    def send_email(self, subject, html_content, to_email=None):
        """Send HTML email via Gmail SMTP"""
        try:
            # Email configuration
            from_email = self.config.EMAIL_FROM
            password = self.config.EMAIL_PASSWORD
            to_email = to_email or self.config.EMAIL_TO
            
            if not all([from_email, password, to_email]):
                raise ValueError("Missing email configuration. Check environment variables.")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email
            
            # Create HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(from_email, password)
                server.sendmail(from_email, to_email, message.as_string())
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            raise


