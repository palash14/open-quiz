import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.app.core.config import settings
from src.app.core.logger import create_logger

mail_logger = create_logger("mail_logger", "utils_email.log")

smtp_server = settings.SMTP_HOST
smtp_port = settings.SMTP_PORT
smtp_username = settings.SMTP_USERNAME
smtp_password = settings.SMTP_PASSWORD
smtp_encryption = (settings.SMTP_ENCRYPTION or "").lower()  # '', 'starttls', 'ssl'
sender_email = settings.SENDER_EMAIL


def send_email(email: str, subject: str, plain_text_body: str, html_body: str):
    """Send an email with given subject and body content."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = email
        msg["Subject"] = subject
        # Attach plain text part
        part1 = MIMEText(plain_text_body, "plain")

        # Attach HTML part
        part2 = MIMEText(html_body, "html")

        # Attach both parts to the message. Plain text first, then HTML.
        msg.attach(part1)
        msg.attach(part2)

        # Send the email
        if smtp_encryption == "ssl":
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                _login_if_needed(server)
                server.sendmail(sender_email, email, msg.as_string())

        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.ehlo()
                if smtp_encryption == "starttls":
                    if server.has_extn("STARTTLS"):
                        server.starttls()
                        server.ehlo()
                    else:
                        raise RuntimeError(
                            "STARTTLS requested but not supported by server"
                        )
                _login_if_needed(server)
                server.sendmail(sender_email, email, msg.as_string())

    except Exception as e:
        mail_logger.error(f"Error sending email to {email}: {str(e)}")
        raise e

def _login_if_needed(server: smtplib.SMTP):
    """Helper to conditionally perform login."""
    if smtp_username and smtp_password and smtp_username.lower() != "null":
        server.login(smtp_username, smtp_password)


def send_verification_email(email: str, otp: str):
    subject = "Please verify your email address"
    plain_text_body = f"This is your Verification Email OTP: {otp}"

    # HTML version
    html_body = f"""
        <html>
            <body>
                <h1>Verify your email address</h1>
                <p>This is your Verification Email OTP: {otp}</p> 
            </body>
        </html>
        """
    send_email(email, subject, plain_text_body, html_body)


def send_forgot_email(email: str, otp: str):
    subject = "Forgot Password"
    # Plain text version
    plain_text_body = f"This is your reset password email OTP: {otp}"

    # HTML version
    html_body = f"""
        <html>
            <body>
                <h1>Forgot Your Password?</h1>
                <p>This is your reset password email OTP: {otp}</p>
            </body>
        </html>
        """
    send_email(email, subject, plain_text_body, html_body)


def send_custom_email(mail_to: str, mail_subject: str, mail_message: str):
    # Plain text version
    plain_text_body = mail_message

    # HTML version
    html_body = f"""
            <html>
                <body>
                    {mail_message}
                </body>
            </html>
            """
    send_email(mail_to, mail_subject, plain_text_body, html_body)


if __name__ == "__main__":
    try:
        send_custom_email("palash14@gmail.com", "Test Message", "Test Mail Message")

    except Exception as e:
        mail_logger.error(f"Error sending email to: {str(e)}")
        raise e
