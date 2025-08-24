import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.config = Config()
    
    def send_email(self, subject, html_content, to_email=None, attachments=None):
        """Send HTML email via Gmail SMTP"""
        try:
            # Email configuration
            from_email = self.config.EMAIL_FROM
            password = self.config.EMAIL_PASSWORD
            to_email = to_email or self.config.EMAIL_TO
            
            if not all([from_email, password, to_email]):
                raise ValueError("Missing email configuration. Check environment variables.")
            
            logger.info(f"Preparing email from {from_email} to {to_email}")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Add plain text fallback
            plain_text = self._html_to_text(html_content)
            text_part = MIMEText(plain_text, "plain", "utf-8")
            message.attach(text_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Send email using Gmail SMTP
            logger.info("Connecting to Gmail SMTP server...")
            
            # Create secure context
            context = ssl.create_default_context()
            
            # Connect to Gmail SMTP server
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.set_debuglevel(0)  # Set to 1 for debugging
                
                # Enable starttls for security
                server.starttls(context=context)
                logger.info("Started TLS connection")
                
                # Login to the server
                server.login(from_email, password)
                logger.info("Successfully logged in to Gmail")
                
                # Send email
                text = message.as_string()
                server.sendmail(from_email, to_email, text)
                logger.info(f"✅ Email sent successfully to {to_email}")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {str(e)}")
            logger.error("Please check:")
            logger.error("1. Gmail app password is correct")
            logger.error("2. 2-Factor Authentication is enabled")
            logger.error("3. App password was generated recently")
            raise
            
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"❌ Recipient email refused: {str(e)}")
            logger.error("Please check the recipient email address")
            raise
            
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error occurred: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}")
            raise
    
    def send_test_email(self):
        """Send a test email to verify configuration"""
        try:
            subject = "🧪 Novi Intelligence Report - Test Email"
            html_content = self._get_test_email_content()
            
            result = self.send_email(subject, html_content)
            
            if result:
                logger.info("✅ Test email sent successfully!")
                return True
            else:
                logger.error("❌ Test email failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test email failed: {str(e)}")
            return False
    
    def _get_test_email_content(self):
        """Generate test email content"""
        current_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .content {{ background: #f8f9fa; padding: 30px; margin: 20px 0; border-radius: 10px; }}
                .success {{ color: #28a745; font-size: 18px; font-weight: bold; }}
                .info {{ color: #6c757d; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Test Email Successful</h1>
                    <p>Novi's Intelligence Report System</p>
                </div>
                <div class="content">
                    <p class="success">✅ Email configuration is working correctly!</p>
                    <p class="info">📅 <strong>Test Date:</strong> {current_time}</p>
                    <p class="info">📧 <strong>From:</strong> {self.config.EMAIL_FROM}</p>
                    <p class="info">📬 <strong>To:</strong> {self.config.EMAIL_TO}</p>
                    
                    <h3>Next Steps:</h3>
                    <ul>
                        <li>Your email configuration is working properly</li>
                        <li>Daily reports will be sent at 5:00 AM IST</li>
                        <li>Check GitHub Actions logs for any issues</li>
                    </ul>
                    
                    <h3>System Status:</h3>
                    <ul>
                        <li>✅ Gmail SMTP connection: Working</li>
                        <li>✅ Authentication: Successful</li>
                        <li>✅ HTML email rendering: Working</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _html_to_text(self, html_content):
        """Convert HTML content to plain text for email fallback"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.warning(f"Could not convert HTML to text: {e}")
            return "Novi's Intelligence Report - Please view HTML version for full content."
    
    def _add_attachment(self, message, attachment_path):
        """Add attachment to email"""
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment_path.split("/")[-1]}',
            )
            
            message.attach(part)
            
        except Exception as e:
            logger.warning(f"Could not add attachment {attachment_path}: {e}")
    
    def send_error_notification(self, error_message, error_type="General Error"):
        """Send error notification email"""
        try:
            subject = "🚨 Novi Intelligence Report - System Error"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
                    .content {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #dc3545; }}
                    .error {{ color: #dc3545; font-weight: bold; }}
                    .timestamp {{ color: #6c757d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 System Error Alert</h1>
                        <p>Novi's Intelligence Report</p>
                    </div>
                    <div class="content">
                        <p class="error">Error Type: {error_type}</p>
                        <p><strong>Error Message:</strong></p>
                        <pre style="background: #f1f3f4; padding: 10px; border-radius: 5px; overflow-x: auto;">{error_message}</pre>
                        <p class="timestamp">Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
                        
                        <h3>Recommended Actions:</h3>
                        <ul>
                            <li>Check GitHub Actions logs for detailed error information</li>
                            <li>Verify all environment variables are set correctly</li>
                            <li>Check API quotas and rate limits</li>
                            <li>System will retry automatically tomorrow</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.send_email(subject, html_content)
            logger.info("Error notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def validate_configuration(self):
    """Validate email configuration"""
    config_issues = []
    
    if not self.config.EMAIL_FROM:
        config_issues.append("EMAIL_FROM environment variable not set")
    
    if not self.config.EMAIL_PASSWORD:
        config_issues.append("EMAIL_PASSWORD environment variable not set")
    
    if not self.config.EMAIL_TO:
        config_issues.append("EMAIL_TO environment variable not set")
    
    if self.config.EMAIL_FROM and '@gmail.com' not in self.config.EMAIL_FROM:
        config_issues.append("EMAIL_FROM must be a Gmail address")
    
    # Fix: Handle Gmail app password with or without spaces
    if self.config.EMAIL_PASSWORD:
        # Remove spaces and check if it's 16 characters
        clean_password = self.config.EMAIL_PASSWORD.replace(' ', '')
        if len(clean_password) != 16:
            config_issues.append("EMAIL_PASSWORD should be a 16-character Gmail app password (spaces will be ignored)")
    
    return config_issues
