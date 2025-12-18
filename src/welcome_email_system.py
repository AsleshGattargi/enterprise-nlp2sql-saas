"""
Welcome Email and Documentation System
Provides automated welcome emails and documentation generation for newly onboarded tenants.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import pdfkit
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from tenant_onboarding_models import (
    OnboardingWorkflow, TenantConfiguration, IndustryType,
    OnboardingNotification, TenantInfo
)
from industry_schema_templates import IndustrySchemaTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailConfiguration:
    """Email server configuration."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@nlp2sql-platform.com")
        self.from_name = os.getenv("FROM_NAME", "NLP2SQL Platform")
        self.reply_to = os.getenv("REPLY_TO_EMAIL", "support@nlp2sql-platform.com")


class DocumentationGenerator:
    """Generates tenant-specific documentation and setup guides."""

    def __init__(self, template_manager: IndustrySchemaTemplateManager):
        self.template_manager = template_manager
        self.templates_dir = Path("templates/documentation")
        self.output_dir = Path("generated_docs")
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

    def generate_welcome_guide(self, workflow: OnboardingWorkflow) -> Dict[str, str]:
        """Generate tenant-specific welcome guide."""
        try:
            # Get industry template for context
            industry_template = self.template_manager.get_template(
                workflow.registration_data.industry
            )

            # Prepare template variables
            template_vars = {
                "tenant_id": workflow.tenant_id,
                "org_name": workflow.registration_data.org_name,
                "admin_name": workflow.registration_data.admin_name,
                "admin_email": workflow.registration_data.admin_email,
                "industry": workflow.registration_data.industry.value,
                "database_type": workflow.registration_data.database_type.value,
                "data_region": workflow.registration_data.data_region.value,
                "compliance_frameworks": [cf.value for cf in workflow.registration_data.compliance_requirements],
                "tenant_config": workflow.tenant_config.dict() if workflow.tenant_config else {},
                "industry_template": industry_template.dict(),
                "setup_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "platform_url": "https://app.nlp2sql-platform.com",
                "api_base_url": "https://api.nlp2sql-platform.com",
                "support_email": "support@nlp2sql-platform.com",
                "documentation_url": "https://docs.nlp2sql-platform.com"
            }

            # Generate different formats
            html_content = self._generate_html_guide(template_vars)
            markdown_content = self._generate_markdown_guide(template_vars)
            pdf_path = self._generate_pdf_guide(template_vars)

            return {
                "html": html_content,
                "markdown": markdown_content,
                "pdf_path": pdf_path
            }

        except Exception as e:
            logger.error(f"Failed to generate welcome guide: {str(e)}")
            return {"html": "", "markdown": "", "pdf_path": ""}

    def generate_api_documentation(self, workflow: OnboardingWorkflow) -> str:
        """Generate tenant-specific API documentation."""
        try:
            template_vars = {
                "tenant_id": workflow.tenant_id,
                "org_name": workflow.registration_data.org_name,
                "api_base_url": f"https://api.nlp2sql-platform.com/v1/tenant/{workflow.tenant_id}",
                "database_type": workflow.registration_data.database_type.value,
                "compliance_frameworks": [cf.value for cf in workflow.registration_data.compliance_requirements],
                "example_queries": self._get_industry_example_queries(workflow.registration_data.industry)
            }

            # Generate API documentation
            api_template = self.jinja_env.get_template("api_guide.md.j2")
            api_content = api_template.render(**template_vars)

            # Save to file
            api_file_path = self.output_dir / f"{workflow.tenant_id}_api_guide.md"
            with open(api_file_path, 'w', encoding='utf-8') as f:
                f.write(api_content)

            return str(api_file_path)

        except Exception as e:
            logger.error(f"Failed to generate API documentation: {str(e)}")
            return ""

    def generate_compliance_checklist(self, workflow: OnboardingWorkflow) -> str:
        """Generate compliance checklist for the tenant's industry."""
        try:
            industry_template = self.template_manager.get_template(
                workflow.registration_data.industry
            )

            template_vars = {
                "tenant_id": workflow.tenant_id,
                "org_name": workflow.registration_data.org_name,
                "industry": workflow.registration_data.industry.value,
                "compliance_frameworks": [cf.value for cf in workflow.registration_data.compliance_requirements],
                "compliance_checklist": industry_template.compliance_checklist,
                "security_requirements": industry_template.security_requirements,
                "audit_requirements": industry_template.audit_requirements,
                "data_retention_policies": industry_template.data_retention_policies
            }

            # Generate compliance checklist
            compliance_template = self.jinja_env.get_template("compliance_checklist.md.j2")
            compliance_content = compliance_template.render(**template_vars)

            # Save to file
            compliance_file_path = self.output_dir / f"{workflow.tenant_id}_compliance_checklist.md"
            with open(compliance_file_path, 'w', encoding='utf-8') as f:
                f.write(compliance_content)

            return str(compliance_file_path)

        except Exception as e:
            logger.error(f"Failed to generate compliance checklist: {str(e)}")
            return ""

    def _generate_html_guide(self, template_vars: Dict[str, Any]) -> str:
        """Generate HTML welcome guide."""
        try:
            template = self.jinja_env.get_template("welcome_guide.html.j2")
            return template.render(**template_vars)
        except Exception as e:
            logger.error(f"Failed to generate HTML guide: {str(e)}")
            return self._get_fallback_html_guide(template_vars)

    def _generate_markdown_guide(self, template_vars: Dict[str, Any]) -> str:
        """Generate Markdown welcome guide."""
        try:
            template = self.jinja_env.get_template("welcome_guide.md.j2")
            return template.render(**template_vars)
        except Exception as e:
            logger.error(f"Failed to generate Markdown guide: {str(e)}")
            return self._get_fallback_markdown_guide(template_vars)

    def _generate_pdf_guide(self, template_vars: Dict[str, Any]) -> str:
        """Generate PDF welcome guide."""
        try:
            # Generate HTML first
            html_content = self._generate_html_guide(template_vars)

            # Convert to PDF
            pdf_filename = f"{template_vars['tenant_id']}_welcome_guide.pdf"
            pdf_path = self.output_dir / pdf_filename

            # PDF generation options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }

            pdfkit.from_string(html_content, str(pdf_path), options=options)
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Failed to generate PDF guide: {str(e)}")
            return ""

    def _get_industry_example_queries(self, industry: IndustryType) -> List[str]:
        """Get industry-specific example queries."""
        examples = {
            IndustryType.HEALTHCARE: [
                "Show me patient visits from last month",
                "What is the average length of stay by department?",
                "List all patients with pending lab results"
            ],
            IndustryType.FINANCE: [
                "Show me transaction volumes by account type",
                "What are the top performing investment products?",
                "List all high-risk transactions from today"
            ],
            IndustryType.EDUCATION: [
                "Show me student enrollment by program",
                "What is the average GPA by department?",
                "List all students with outstanding fees"
            ],
            IndustryType.RETAIL: [
                "Show me sales by product category",
                "What are the top selling items this month?",
                "List all customers with recent returns"
            ],
            IndustryType.TECHNOLOGY: [
                "Show me API usage by endpoint",
                "What are the most active user sessions?",
                "List all failed deployments from this week"
            ]
        }
        return examples.get(industry, [
            "Show me all users",
            "What is the total record count?",
            "List recent activity"
        ])

    def _get_fallback_html_guide(self, template_vars: Dict[str, Any]) -> str:
        """Fallback HTML guide when template fails."""
        return f"""
        <html>
        <head><title>Welcome to NLP2SQL Platform</title></head>
        <body>
            <h1>Welcome to NLP2SQL Platform, {template_vars['org_name']}!</h1>
            <p>Your tenant ID: {template_vars['tenant_id']}</p>
            <p>Database Type: {template_vars['database_type']}</p>
            <p>Industry: {template_vars['industry']}</p>
            <p>Setup Date: {template_vars['setup_date']}</p>

            <h2>Getting Started</h2>
            <p>Visit <a href="{template_vars['platform_url']}">{template_vars['platform_url']}</a> to access your tenant.</p>

            <h2>Support</h2>
            <p>Contact us at {template_vars['support_email']} for assistance.</p>
        </body>
        </html>
        """

    def _get_fallback_markdown_guide(self, template_vars: Dict[str, Any]) -> str:
        """Fallback Markdown guide when template fails."""
        return f"""
# Welcome to NLP2SQL Platform, {template_vars['org_name']}!

## Tenant Information
- **Tenant ID**: {template_vars['tenant_id']}
- **Database Type**: {template_vars['database_type']}
- **Industry**: {template_vars['industry']}
- **Setup Date**: {template_vars['setup_date']}

## Getting Started
Visit [{template_vars['platform_url']}]({template_vars['platform_url']}) to access your tenant.

## Support
Contact us at {template_vars['support_email']} for assistance.
        """


class WelcomeEmailSender:
    """Handles sending welcome emails to newly onboarded tenants."""

    def __init__(self, email_config: EmailConfiguration):
        self.email_config = email_config
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def send_welcome_email(
        self,
        workflow: OnboardingWorkflow,
        documentation_paths: Dict[str, str]
    ) -> OnboardingNotification:
        """Send welcome email to newly onboarded tenant."""
        try:
            # Prepare email content
            email_content = self._prepare_welcome_email_content(workflow, documentation_paths)

            # Create notification record
            notification = OnboardingNotification(
                tenant_id=workflow.tenant_id,
                notification_type="welcome",
                recipient_emails=[workflow.registration_data.admin_email],
                cc_emails=workflow.registration_data.notification_emails,
                subject=f"Welcome to NLP2SQL Platform - {workflow.registration_data.org_name}",
                template_name="welcome_email",
                template_variables=email_content["variables"]
            )

            # Send email asynchronously
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                notification,
                email_content["html"],
                email_content["attachments"]
            )

            if success:
                notification.sent_at = datetime.utcnow()
                notification.delivery_status = "sent"
                logger.info(f"Welcome email sent successfully to {workflow.tenant_id}")
            else:
                notification.delivery_status = "failed"
                logger.error(f"Failed to send welcome email to {workflow.tenant_id}")

            return notification

        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            # Return failed notification
            return OnboardingNotification(
                tenant_id=workflow.tenant_id,
                notification_type="welcome",
                recipient_emails=[workflow.registration_data.admin_email],
                subject="Welcome Email Failed",
                template_name="welcome_email",
                delivery_status="failed"
            )

    async def send_status_update_email(
        self,
        workflow: OnboardingWorkflow,
        status_message: str,
        is_error: bool = False
    ) -> OnboardingNotification:
        """Send status update email during onboarding process."""
        try:
            notification_type = "error" if is_error else "status_update"
            subject_prefix = "Onboarding Error" if is_error else "Onboarding Update"

            # Prepare email content
            template_vars = {
                "tenant_id": workflow.tenant_id,
                "org_name": workflow.registration_data.org_name,
                "admin_name": workflow.registration_data.admin_name,
                "status_message": status_message,
                "current_status": workflow.current_status.value,
                "is_error": is_error,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }

            # Create notification
            notification = OnboardingNotification(
                tenant_id=workflow.tenant_id,
                notification_type=notification_type,
                recipient_emails=[workflow.registration_data.admin_email],
                cc_emails=workflow.registration_data.notification_emails,
                subject=f"{subject_prefix} - {workflow.registration_data.org_name}",
                template_name="status_update_email",
                template_variables=template_vars
            )

            # Generate email content
            email_html = self._generate_status_email_html(template_vars)

            # Send email
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                notification,
                email_html,
                []
            )

            if success:
                notification.sent_at = datetime.utcnow()
                notification.delivery_status = "sent"
            else:
                notification.delivery_status = "failed"

            return notification

        except Exception as e:
            logger.error(f"Error sending status update email: {str(e)}")
            return OnboardingNotification(
                tenant_id=workflow.tenant_id,
                notification_type="error",
                recipient_emails=[workflow.registration_data.admin_email],
                subject="Status Update Failed",
                template_name="status_update_email",
                delivery_status="failed"
            )

    def _prepare_welcome_email_content(
        self,
        workflow: OnboardingWorkflow,
        documentation_paths: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare welcome email content and variables."""
        # Get access URLs
        tenant_url = f"https://app.nlp2sql-platform.com/tenant/{workflow.tenant_id}"
        api_url = f"https://api.nlp2sql-platform.com/v1/tenant/{workflow.tenant_id}"

        # Prepare template variables
        template_vars = {
            "tenant_id": workflow.tenant_id,
            "org_name": workflow.registration_data.org_name,
            "admin_name": workflow.registration_data.admin_name,
            "admin_email": workflow.registration_data.admin_email,
            "industry": workflow.registration_data.industry.value,
            "database_type": workflow.registration_data.database_type.value,
            "tenant_url": tenant_url,
            "api_url": api_url,
            "support_email": "support@nlp2sql-platform.com",
            "documentation_url": "https://docs.nlp2sql-platform.com",
            "setup_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "admin_username": workflow.tenant_config.admin_user_id if workflow.tenant_config else "admin",
            "initial_password_info": "Check your separate email for login credentials"
        }

        # Generate HTML content
        html_content = self._generate_welcome_email_html(template_vars)

        # Prepare attachments
        attachments = []
        for doc_type, path in documentation_paths.items():
            if path and os.path.exists(path):
                attachments.append({
                    "filename": os.path.basename(path),
                    "path": path,
                    "content_type": self._get_content_type(path)
                })

        return {
            "html": html_content,
            "variables": template_vars,
            "attachments": attachments
        }

    def _generate_welcome_email_html(self, template_vars: Dict[str, Any]) -> str:
        """Generate HTML content for welcome email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to NLP2SQL Platform</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3B82F6; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; background-color: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .info-box {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid #3B82F6; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to NLP2SQL Platform!</h1>
                    <p>Your tenant has been successfully provisioned</p>
                </div>

                <div class="content">
                    <h2>Hello {template_vars['admin_name']},</h2>

                    <p>Congratulations! Your NLP2SQL Platform tenant for <strong>{template_vars['org_name']}</strong> has been successfully set up and is ready to use.</p>

                    <div class="info-box">
                        <h3>Your Tenant Information</h3>
                        <ul>
                            <li><strong>Tenant ID:</strong> {template_vars['tenant_id']}</li>
                            <li><strong>Industry:</strong> {template_vars['industry']}</li>
                            <li><strong>Database Type:</strong> {template_vars['database_type']}</li>
                            <li><strong>Setup Date:</strong> {template_vars['setup_date']}</li>
                        </ul>
                    </div>

                    <h3>Getting Started</h3>
                    <p>You can access your tenant using the following links:</p>
                    <ul>
                        <li><strong>Web Application:</strong> <a href="{template_vars['tenant_url']}">{template_vars['tenant_url']}</a></li>
                        <li><strong>API Endpoint:</strong> <a href="{template_vars['api_url']}">{template_vars['api_url']}</a></li>
                    </ul>

                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{template_vars['tenant_url']}" class="button">Access Your Tenant</a>
                    </p>

                    <h3>Next Steps</h3>
                    <ol>
                        <li>Log in using your admin credentials (sent in a separate email)</li>
                        <li>Review the attached documentation and setup guides</li>
                        <li>Configure additional users and permissions</li>
                        <li>Start exploring with natural language queries</li>
                    </ol>

                    <h3>Support & Resources</h3>
                    <ul>
                        <li><strong>Documentation:</strong> <a href="{template_vars['documentation_url']}">{template_vars['documentation_url']}</a></li>
                        <li><strong>Support Email:</strong> <a href="mailto:{template_vars['support_email']}">{template_vars['support_email']}</a></li>
                        <li><strong>Support Portal:</strong> <a href="https://support.nlp2sql-platform.com">https://support.nlp2sql-platform.com</a></li>
                    </ul>
                </div>

                <div class="footer">
                    <p>This email was sent to {template_vars['admin_email']} for tenant {template_vars['tenant_id']}</p>
                    <p>&copy; 2024 NLP2SQL Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_status_email_html(self, template_vars: Dict[str, Any]) -> str:
        """Generate HTML content for status update email."""
        color = "#EF4444" if template_vars["is_error"] else "#3B82F6"
        status_icon = "❌" if template_vars["is_error"] else "✅"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Onboarding Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .status-box {{ background-color: #e7f3ff; padding: 15px; border-left: 4px solid {color}; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{status_icon} Onboarding Status Update</h1>
                </div>

                <div class="content">
                    <h2>Hello {template_vars['admin_name']},</h2>

                    <p>We have an update on the onboarding process for <strong>{template_vars['org_name']}</strong>.</p>

                    <div class="status-box">
                        <h3>Status Information</h3>
                        <ul>
                            <li><strong>Tenant ID:</strong> {template_vars['tenant_id']}</li>
                            <li><strong>Current Status:</strong> {template_vars['current_status']}</li>
                            <li><strong>Timestamp:</strong> {template_vars['timestamp']}</li>
                        </ul>
                        <p><strong>Message:</strong> {template_vars['status_message']}</p>
                    </div>

                    <p>If you have any questions or concerns, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _send_email_sync(
        self,
        notification: OnboardingNotification,
        html_content: str,
        attachments: List[Dict[str, str]]
    ) -> bool:
        """Send email synchronously (called by executor)."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.subject
            msg['From'] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
            msg['To'] = ", ".join(notification.recipient_emails)
            msg['Reply-To'] = self.email_config.reply_to

            if notification.cc_emails:
                msg['Cc'] = ", ".join(notification.cc_emails)

            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Add attachments
            for attachment in attachments:
                if os.path.exists(attachment["path"]):
                    with open(attachment["path"], "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)

            # Send email
            context = ssl.create_default_context()

            with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
                if self.email_config.smtp_use_tls:
                    server.starttls(context=context)

                if self.email_config.smtp_username and self.email_config.smtp_password:
                    server.login(self.email_config.smtp_username, self.email_config.smtp_password)

                # Send to all recipients
                all_recipients = notification.recipient_emails + notification.cc_emails
                server.sendmail(self.email_config.from_email, all_recipients, msg.as_string())

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def _get_content_type(self, file_path: str) -> str:
        """Get MIME content type for file."""
        extension = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.md': 'text/markdown',
            '.html': 'text/html',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
        return content_types.get(extension, 'application/octet-stream')


class WelcomeEmailOrchestrator:
    """Orchestrates the complete welcome email and documentation process."""

    def __init__(self, template_manager: IndustrySchemaTemplateManager):
        self.template_manager = template_manager
        self.email_config = EmailConfiguration()
        self.doc_generator = DocumentationGenerator(template_manager)
        self.email_sender = WelcomeEmailSender(self.email_config)

    async def send_welcome_package(self, workflow: OnboardingWorkflow) -> List[OnboardingNotification]:
        """Send complete welcome package including emails and documentation."""
        notifications = []

        try:
            logger.info(f"Starting welcome package generation for tenant {workflow.tenant_id}")

            # Generate documentation
            welcome_guide = self.doc_generator.generate_welcome_guide(workflow)
            api_docs = self.doc_generator.generate_api_documentation(workflow)
            compliance_checklist = self.doc_generator.generate_compliance_checklist(workflow)

            documentation_paths = {
                "welcome_guide_pdf": welcome_guide.get("pdf_path", ""),
                "api_documentation": api_docs,
                "compliance_checklist": compliance_checklist
            }

            # Send welcome email
            welcome_notification = await self.email_sender.send_welcome_email(
                workflow, documentation_paths
            )
            notifications.append(welcome_notification)

            logger.info(f"Welcome package sent successfully for tenant {workflow.tenant_id}")

        except Exception as e:
            logger.error(f"Failed to send welcome package: {str(e)}")
            # Send error notification
            error_notification = await self.email_sender.send_status_update_email(
                workflow,
                f"Failed to send welcome package: {str(e)}",
                is_error=True
            )
            notifications.append(error_notification)

        return notifications

    async def send_onboarding_status_update(
        self,
        workflow: OnboardingWorkflow,
        status_message: str,
        is_error: bool = False
    ) -> OnboardingNotification:
        """Send onboarding status update email."""
        return await self.email_sender.send_status_update_email(
            workflow, status_message, is_error
        )


# Template creation functions (these would create the actual Jinja2 templates)

def create_email_templates():
    """Create email template files if they don't exist."""
    templates_dir = Path("templates/documentation")
    templates_dir.mkdir(exist_ok=True)

    # Welcome guide HTML template
    welcome_html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ org_name }} - NLP2SQL Platform Welcome Guide</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        .header { text-align: center; border-bottom: 2px solid #3B82F6; padding-bottom: 20px; }
        .section { margin: 30px 0; }
        .info-box { background-color: #f0f9ff; padding: 15px; border-left: 4px solid #3B82F6; }
        .code { background-color: #f4f4f4; padding: 10px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to NLP2SQL Platform</h1>
        <h2>{{ org_name }}</h2>
        <p>Setup Date: {{ setup_date }}</p>
    </div>

    <div class="section">
        <h2>Tenant Information</h2>
        <div class="info-box">
            <ul>
                <li><strong>Tenant ID:</strong> {{ tenant_id }}</li>
                <li><strong>Industry:</strong> {{ industry }}</li>
                <li><strong>Database Type:</strong> {{ database_type }}</li>
                <li><strong>Data Region:</strong> {{ data_region }}</li>
                {% if compliance_frameworks %}
                <li><strong>Compliance:</strong> {{ compliance_frameworks|join(', ') }}</li>
                {% endif %}
            </ul>
        </div>
    </div>

    <div class="section">
        <h2>Access Information</h2>
        <ul>
            <li><strong>Platform URL:</strong> <a href="{{ platform_url }}">{{ platform_url }}</a></li>
            <li><strong>API Base URL:</strong> <code>{{ api_base_url }}</code></li>
        </ul>
    </div>

    <div class="section">
        <h2>Getting Started</h2>
        <ol>
            <li>Log in to the platform using your admin credentials</li>
            <li>Explore the dashboard and available features</li>
            <li>Try natural language queries with your data</li>
            <li>Configure additional users and permissions</li>
        </ol>
    </div>

    <div class="section">
        <h2>Support</h2>
        <p>Contact our support team at <a href="mailto:{{ support_email }}">{{ support_email }}</a></p>
        <p>Documentation: <a href="{{ documentation_url }}">{{ documentation_url }}</a></p>
    </div>
</body>
</html>
    """

    # Write template file
    with open(templates_dir / "welcome_guide.html.j2", "w", encoding="utf-8") as f:
        f.write(welcome_html_template)

    logger.info("Email templates created successfully")


# Initialize templates on module import
create_email_templates()

# Export main classes
__all__ = [
    "WelcomeEmailOrchestrator",
    "DocumentationGenerator",
    "WelcomeEmailSender",
    "EmailConfiguration"
]