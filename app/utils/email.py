import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from loguru import logger

from app.core.config.settings import settings

# Onde modificar configurações de Email:
# - As configurações SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`, `EMAILS_ENABLED`)
#   são carregadas do arquivo `.env` e acessíveis via `settings`.
# - Este arquivo (`app/utils/email.py`) contém a lógica para enviar emails.

async def send_email(
    email_to: str,
    subject: str = "",
    html_content: str = "",
    text_content: Optional[str] = None,
) -> bool:
    """
    Sends an email using SMTP.

    Args:
        email_to: The recipient's email address.
        subject: The subject of the email.
        html_content: The HTML content of the email.
        text_content: Optional plain text content (alternative to HTML).

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if not settings.EMAILS_ENABLED:
        logger.info(f"Email sending is disabled. Would have sent to: {email_to}, Subject: {subject}")
        # In a real scenario, you might want to log the email content or handle it differently
        # For testing or development when emails are disabled, this can simulate a successful send.
        return True 

    assert settings.SMTP_HOST, "SMTP_HOST must be configured to send emails"
    assert settings.EMAIL_FROM, "EMAIL_FROM must be configured to send emails"

    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAIL_FROM
    message["To"] = email_to
    message["Subject"] = subject

    # Attach plain text part first, then HTML part
    if text_content:
        message.attach(MIMEText(text_content, "plain"))
    if html_content:
        message.attach(MIMEText(html_content, "html"))
    else:
        # If only text_content is provided, ensure it's attached as the main content
        if text_content and not html_content:
            pass # Already attached
        else: # Should not happen if html_content is required or text_content is its fallback
            logger.error("Email content is missing (html_content or text_content required).")
            return False

    try:
        logger.debug(f"Attempting to send email to {email_to} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        smtp_server = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASS

        server: smtplib.SMTP
        if settings.SMTP_TLS:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Use TLS encryption
        else:
            # For SSL, use smtplib.SMTP_SSL directly if your server requires it
            # server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            # Or if no encryption (not recommended for production)
            server = smtplib.SMTP(smtp_server, smtp_port)

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        
        server.sendmail(settings.EMAIL_FROM, email_to, message.as_string())
        server.quit()
        logger.info(f"Email sent successfully to: {email_to}, Subject: {subject}")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error while sending email to {email_to}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email to {email_to}: {e}")
        return False

async def send_test_email(email_to: str) -> None:
    """Sends a test email."""
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test Email"
    html_content = f"""
    <html>
        <body>
            <h1>Test Email from {project_name}</h1>
            <p>This is a test email to confirm that email sending is configured correctly.</p>
            <p>If you received this, it means the SMTP settings are working.</p>
        </body>
    </html>
    """
    text_content = f"Test Email from {project_name}\n\nThis is a test email..."
    await send_email(email_to=email_to, subject=subject, html_content=html_content, text_content=text_content)

async def send_password_reset_email(email_to: str, token: str) -> None:
    """
    Sends a password reset email with a reset link/token.
    """
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password Reset Request"
    # In a real application, the link_host would be your frontend URL
    link_host = "http://localhost:3000" # Replace with your frontend domain
    reset_link = f"{link_host}/reset-password?token={token}"

    html_content = f"""
    <html>
        <body>
            <h1>Password Reset Request for {project_name}</h1>
            <p>You (or someone else) requested a password reset for your account.</p>
            <p>If this was you, click the link below to reset your password:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>If you did not request this, please ignore this email.</p>
            <p>This link will expire in a short period (e.g., 1 hour).</p>
        </body>
    </html>
    """
    text_content = f"Password Reset for {project_name}\n\nClick here to reset: {reset_link}"
    await send_email(email_to=email_to, subject=subject, html_content=html_content, text_content=text_content)

# Como usar o utilitário de email:
# from app.utils.email import send_password_reset_email, send_test_email
#
# async def some_function():
#     # Para enviar um email de reset de senha:
#     # await send_password_reset_email(email_to="user@example.com", token="some_reset_token")
#     #
#     # Para enviar um email de teste:
#     # await send_test_email(email_to="test@example.com")

