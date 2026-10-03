"""
Transactional email templates & senders for the app, sent over SMTP.

Each `*_email_html` function returns a self-contained HTML string for a
specific email. Each `send_*_email` function sends that email through
Django's SMTP backend (configured by the EMAIL_* settings).
"""
import logging
import re
from html import unescape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)

LOGO_URL = f"{settings.SITE_URL}/static/images/SanterdeTrust.png?v=3"


def _email_shell(preheader, body_html):
    """Wrap inner body HTML in the shared Santerde Trust email layout."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Santerde Trust</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
  <span style="display:none;font-size:1px;color:#f4f4f5;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
    {preheader}
  </span>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:24px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#ffffff;border:1px solid #e4e4e7;">

          <!-- Logo header -->
          <tr>
            <td align="center" style="padding:28px 32px 20px 32px;border-bottom:1px solid #e4e4e7;">
              <img src="{LOGO_URL}" alt="Santerde Trust" width="104" style="display:block;max-width:104px;height:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:28px 32px;">
              {body_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #e4e4e7;">
              <p style="margin:0 0 6px 0;font-size:12px;line-height:1.6;color:#71717a;text-align:center;">
                This is an automated message from Santerde Trust. Please do not reply to this email.
              </p>
              <p style="margin:0;font-size:12px;line-height:1.6;color:#71717a;text-align:center;">
                Need help? Contact us at
                <a href="mailto:support@santerdetrust.com" style="color:#2563eb;text-decoration:none;">support@santerdetrust.com</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _html_to_text(html):
    """Rough plain-text version of an email, for clients that don't render HTML."""
    body = re.sub(r'(?is)<(head|style|title)[^>]*>.*?</\1>', '', html)
    body = re.sub(r'(?is)<span style="display:none.*?</span>', '', body)   # preheader
    body = re.sub(r'(?i)<br\s*/?>|</(p|h1|tr|td)>', '\n', body)
    body = unescape(re.sub(r'<[^>]+>', '', body))
    lines = [' '.join(line.split()) for line in body.splitlines()]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()


def _send(to, subject, html, kind):
    """
    Send one HTML email over SMTP. Returns True on success, False if the
    email was skipped (SMTP not configured) or failed to send.
    """
    if not settings.EMAIL_HOST_PASSWORD:
        logger.warning("HOSTINGER_EMAIL_PASSWORD is not configured; skipping %s email to %s", kind, to)
        return False

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=_html_to_text(html),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
        )
        message.attach_alternative(html, "text/html")
        message.send()
        return True
    except Exception:
        logger.exception("Failed to send %s email to %s", kind, to)
        return False


def tac_email_html(user, tac_code):
    """Build the HTML body for the Transfer Authorization Code email."""
    first_name = (user.first_name or 'there').strip()
    body_html = f"""\
      <h1 style="margin:0 0 12px 0;font-size:18px;font-weight:600;color:#18181b;">
        Your Transfer Authorization Code
      </h1>
      <p style="margin:0 0 20px 0;font-size:14px;line-height:1.6;color:#3f3f46;">
        Hi {first_name}, use the code below to authorize your transaction. Do not share this code with anyone.
      </p>

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
        <tr>
          <td align="center" style="padding:16px;background-color:#f4f4f5;border:1px solid #e4e4e7;">
            <span style="font-family:'Courier New',monospace;font-size:28px;font-weight:700;letter-spacing:0.2em;color:#18181b;">
              {tac_code}
            </span>
          </td>
        </tr>
      </table>

"""
    return _email_shell(
        preheader=f"Your Transfer Authorization Code is {tac_code}",
        body_html=body_html,
    )


def otp_email_html(user, otp_code, minutes_valid):
    """Build the HTML body for the two-factor sign-in code email."""
    first_name = (user.first_name or 'there').strip()
    body_html = f"""\
      <h1 style="margin:0 0 12px 0;font-size:18px;font-weight:600;color:#18181b;">
        Your sign-in verification code
      </h1>
      <p style="margin:0 0 20px 0;font-size:14px;line-height:1.6;color:#3f3f46;">
        Hi {first_name}, enter the code below to finish signing in to Santerde Trust.
        It expires in {minutes_valid} minutes.
      </p>

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
        <tr>
          <td align="center" style="padding:16px;background-color:#f4f4f5;border:1px solid #e4e4e7;">
            <span style="font-family:'Courier New',monospace;font-size:28px;font-weight:700;letter-spacing:0.2em;color:#18181b;">
              {otp_code}
            </span>
          </td>
        </tr>
      </table>

      <p style="margin:0;font-size:13px;line-height:1.6;color:#71717a;">
        <strong style="color:#3f3f46;">Didn't try to sign in?</strong>
        Someone may know your password. Change it right away and contact support.
        Santerde Trust staff will never ask for this code.
      </p>
"""
    return _email_shell(
        preheader=f"Your Santerde Trust verification code is {otp_code}",
        body_html=body_html,
    )


def password_reset_email_html(user, reset_url, minutes_valid):
    """Build the HTML body for the forgot-password email."""
    first_name = (user.first_name or 'there').strip()
    body_html = f"""\
      <h1 style="margin:0 0 12px 0;font-size:18px;font-weight:600;color:#18181b;">
        Reset your password
      </h1>
      <p style="margin:0 0 20px 0;font-size:14px;line-height:1.6;color:#3f3f46;">
        Hi {first_name}, we received a request to reset the password for your Santerde Trust account.
        Click the button below to choose a new one. The link expires in {minutes_valid} minutes and can only be used once.
      </p>

      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
        <tr>
          <td style="background-color:#2563eb;">
            <a href="{reset_url}" style="display:inline-block;padding:11px 24px;color:#ffffff;font-weight:600;font-size:14px;text-decoration:none;">
              Reset Password
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 20px 0;font-size:12px;line-height:1.6;color:#71717a;word-break:break-all;">
        If the button doesn't work, copy this link into your browser:<br>
        <a href="{reset_url}" style="color:#2563eb;text-decoration:none;">{reset_url}</a>
      </p>

      <p style="margin:0;font-size:13px;line-height:1.6;color:#71717a;">
        <strong style="color:#3f3f46;">Didn't ask for this?</strong>
        You can ignore this email; your password won't change. If you keep getting these emails,
        contact support. Santerde Trust staff will never ask for your password.
      </p>
"""
    return _email_shell(
        preheader="Reset your Santerde Trust password",
        body_html=body_html,
    )


def welcome_email_html(user):
    """Build the HTML body for the post-registration welcome email."""
    first_name = (user.first_name or 'there').strip()
    login_url = f"{settings.SITE_URL}/login/"
    body_html = f"""\
      <h1 style="margin:0 0 12px 0;font-size:18px;font-weight:600;color:#18181b;">
        Welcome to Santerde Trust, {first_name}!
      </h1>
      <p style="margin:0 0 20px 0;font-size:14px;line-height:1.6;color:#3f3f46;">
        Your account has been created successfully. We're glad to have you with us.
      </p>

      <p style="margin:0 0 8px 0;font-size:13px;font-weight:600;color:#18181b;">
        Next steps
      </p>
      <p style="margin:0 0 4px 0;font-size:13px;line-height:1.7;color:#3f3f46;">
        &#8226; Log in to your dashboard
      </p>
      <p style="margin:0 0 4px 0;font-size:13px;line-height:1.7;color:#3f3f46;">
        &#8226; Complete your KYC verification to unlock all features
      </p>
      <p style="margin:0 0 20px 0;font-size:13px;line-height:1.7;color:#3f3f46;">
        &#8226; Apply for an account and start banking with us
      </p>

      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 20px 0;">
        <tr>
          <td style="background-color:#2563eb;">
            <a href="{login_url}" style="display:inline-block;padding:11px 24px;color:#ffffff;font-weight:600;font-size:14px;text-decoration:none;">
              Log In to Your Account
            </a>
          </td>
        </tr>
      </table>

      <p style="margin:0;font-size:13px;line-height:1.6;color:#71717a;">
        <strong style="color:#3f3f46;">Keep your account secure.</strong>
        Never share your password or verification codes with anyone. Santerde Trust
        staff will never ask for them.
      </p>
"""
    return _email_shell(
        preheader=f"Welcome to Santerde Trust, {first_name}! Your account is ready.",
        body_html=body_html,
    )


def send_welcome_email(user):
    """
    Email a new user a welcome message after they register. Returns True if
    it was sent, False if it was skipped or failed to send.
    """
    if not user.email:
        return False
    return _send(user.email, "Welcome to Santerde Trust", welcome_email_html(user), "welcome")


def send_tac_email(user, tac_code):
    """
    Email the user their Transfer Authorization Code, if they have opted in
    via `user.can_receive_tac_mail`. Returns True if it was sent, False if it
    was skipped or failed to send.
    """
    if not user.can_receive_tac_mail or not user.email:
        return False
    return _send(user.email, "Your Transfer Authorization Code", tac_email_html(user, tac_code), "TAC")


def send_otp_email(user, otp_code, minutes_valid=10):
    """
    Email the user their two-factor sign-in code. Returns True if it was sent,
    False if it was skipped or failed to send.
    """
    if not user.email:
        return False
    return _send(
        user.email,
        "Your Santerde Trust verification code",
        otp_email_html(user, otp_code, minutes_valid),
        "2FA code",
    )


def send_password_reset_email(user, reset_url, minutes_valid=60):
    """
    Email the user a one-time link to choose a new password. Returns True if
    it was sent, False if it was skipped or failed to send.
    """
    if not user.email:
        return False
    return _send(
        user.email,
        "Reset your Santerde Trust password",
        password_reset_email_html(user, reset_url, minutes_valid),
        "password reset",
    )
