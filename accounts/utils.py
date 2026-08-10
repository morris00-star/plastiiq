from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


def _abs_url(url_name):
    """Build a full clickable URL for emails."""
    return f"{settings.SITE_URL}{reverse(url_name)}"


def send_otp_email(user, otp):
    """Send a 6-digit verification code to the user's email via SMTP."""
    subject = "Your PlastIQ verification code"

    text_body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your PlastIQ verification code is: {otp.code}\n"
        f"This code expires in {getattr(settings, 'OTP_VALIDITY_MINUTES', 10)} minutes.\n\n"
        f"If you did not request this, you can safely ignore this email."
    )

    html_body = render_to_string('accounts/otp_email.html', {
        'user': user,
        'otp_code': otp.code,
        'expiry_minutes': getattr(settings, 'OTP_VALIDITY_MINUTES', 10),
        'login_url': _abs_url('accounts:login'),
    })

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def send_approval_email(user, otp):
    """Notify a user their account was approved, and give them their verification code."""
    subject = "Your PlastIQ account has been approved!"

    text_body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Good news — your PlastIQ account has been approved by an administrator.\n\n"
        f"To finish activating your login, verify your email with this code: {otp.code}\n"
        f"This code expires in {getattr(settings, 'OTP_VALIDITY_MINUTES', 10)} minutes.\n\n"
        f"Head to the login page, sign in with your username and password, and enter this "
        f"code when prompted."
    )

    html_body = render_to_string('accounts/approval_email.html', {
        'user': user,
        'otp_code': otp.code,
        'expiry_minutes': getattr(settings, 'OTP_VALIDITY_MINUTES', 10),
        'login_url': _abs_url('accounts:login'),
    })

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def get_admin_emails():
    """Every email address that should receive admin-facing notifications:
    real superusers plus approved in-app 'Administrator' users."""
    from django.db.models import Q
    from .models import CustomUser

    qs = (
        CustomUser.objects.filter(Q(is_superuser=True) | Q(company_role='admin', is_approved=True))
        .exclude(email='')
        .exclude(email__isnull=True)
        .values_list('email', flat=True)
        .distinct()
    )
    return list(qs)


def send_notice_email(to_emails, subject, heading, message, badge_text=None, badge_color="#2fd6c6",
                       action_url=None, action_label=None):
    """Generic plain-notice email (no OTP) used for admin/user notifications."""
    if not to_emails:
        return
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    html_body = render_to_string('accounts/notice_email.html', {
        'heading': heading,
        'message': message,
        'badge_text': badge_text,
        'badge_color': badge_color,
        'action_url': action_url,
        'action_label': action_label,
    })
    text_body = f"{heading}\n\n{message}"

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_emails,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def notify_admins_new_registration(user):
    send_notice_email(
        get_admin_emails(),
        subject=f"New registration: {user.username}",
        heading="New registration awaiting approval",
        message=(
            f"{user.get_full_name() or user.username} ({user.username}) just registered for a "
            f"PlastIQ account and is waiting for approval.\n\n"
            f"Email: {user.email}\n"
            f"Role: {user.get_role_display_name()}\n"
            f"Section: {user.get_section_display_name()}\n\n"
            f"Review it from the User Approvals page in the admin dashboard."
        ),
        badge_text="New Registration",
        badge_color="#8f7cf7",
        action_url=_abs_url('accounts:admin_user_approval_list'),
        action_label="Review Registration",
    )


def notify_user_registration_received(user):
    send_notice_email(
        user.email,
        subject="We received your PlastIQ registration",
        heading="Registration received",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"Thanks for registering with PlastIQ. Your account is now waiting for admin approval. "
            f"We'll email you a verification code as soon as it's approved."
        ),
        badge_text="Pending Approval",
        badge_color="#f5ba3e",
    )


def notify_admins_password_reset_request(reset_request):
    user = reset_request.user
    send_notice_email(
        get_admin_emails(),
        subject=f"Password reset requested: {user.username}",
        heading="Password reset requested",
        message=(
            f"{user.get_full_name() or user.username} ({user.username}) has requested a password reset.\n\n"
            f"Reason given: {reset_request.reason or 'No reason provided'}\n\n"
            f"Review it from the Password Resets page in the admin dashboard."
        ),
        badge_text="Password Reset",
        badge_color="#f2578f",
        action_url=_abs_url('accounts:admin_password_reset_list'),
        action_label="Review Request",
    )


def notify_user_password_reset_received(user):
    send_notice_email(
        user.email,
        subject="Your PlastIQ password reset request was received",
        heading="Password reset request received",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"We received your request to reset your password. An administrator will review it shortly "
            f"and set a temporary password for you."
        ),
        badge_text="Under Review",
        badge_color="#f5ba3e",
    )


def notify_admins_account_deletion(user, initiated_by_admin=False):
    who = "An administrator" if initiated_by_admin else "The user"
    send_notice_email(
        get_admin_emails(),
        subject=f"Account deleted: {user.username}",
        heading="Account deleted",
        message=(
            f"{who} deleted the account for {user.get_full_name() or user.username} "
            f"({user.username}, {user.email})."
        ),
        badge_text="Account Deleted",
        badge_color="#ff7a45",
        action_url=_abs_url('accounts:admin_user_management'),
        action_label="Open User Management",
    )


def notify_user_account_deleted(user, deleted_by_admin=False):
    if deleted_by_admin:
        message = (
            f"Hi {user.first_name or user.username},\n\n"
            f"Your PlastIQ account has been deleted by an administrator. If you believe this was a "
            f"mistake, please contact your administrator directly."
        )
    else:
        message = (
            f"Hi {user.first_name or user.username},\n\n"
            f"Your PlastIQ account has been deleted, as requested. We're sorry to see you go — "
            f"you're welcome to register again any time."
        )
    send_notice_email(
        user.email,
        subject="Your PlastIQ account has been deleted",
        heading="Account deleted",
        message=message,
        badge_text="Account Deleted",
        badge_color="#ff7a45",
    )
