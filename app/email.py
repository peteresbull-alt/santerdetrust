"""
Transactional email templates & senders for the app, powered by Resend.

Each `*_email_html` function returns a self-contained HTML string for a
specific email. Each `send_*_email` function sends that email via Resend.
"""
import logging

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_KEY

LOGO_URL = f"{settings.SITE_URL}/static/images/SanterdeTrust.png?v=2"


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
              <img src="{LOGO_URL}" alt="Santerde Trust" width="120" style="display:block;max-width:120px;height:auto;">
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
    Email a new user a welcome message after they register. Returns the
    Resend response dict, or None if the email was skipped or failed to send.
    """
    if not user.email:
        return None

    if not settings.RESEND_KEY:
        logger.warning("RESEND_KEY is not configured; skipping welcome email to %s", user.email)
        return None

    try:
        return resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [user.email],
            "subject": "Welcome to Santerde Trust",
            "html": welcome_email_html(user),
        })
    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)
        return None


def send_tac_email(user, tac_code):
    """
    Email the user their Transfer Authorization Code, if they have opted in
    via `user.can_receive_tac_mail`. Returns the Resend response dict, or
    None if the email was skipped or failed to send.
    """
    if not user.can_receive_tac_mail or not user.email:
        return None

    if not settings.RESEND_KEY:
        logger.warning("RESEND_KEY is not configured; skipping TAC email to %s", user.email)
        return None

    try:
        return resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [user.email],
            "subject": "Your Transfer Authorization Code",
            "html": tac_email_html(user, tac_code),
        })
    except Exception:
        logger.exception("Failed to send TAC email to %s", user.email)
        return None
