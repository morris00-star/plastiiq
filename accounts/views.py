import os
from django.views.decorators.cache import never_cache
import json
import logging
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail

from .forms import (
    AdminCreateUserForm, BulkUserUploadForm,
    CustomUserCreationForm,
    CustomUserLoginForm,
    UserProfileForm,
    DeleteAccountForm,
    PasswordResetRequestForm,
    AdminPasswordResetReviewForm,
    AdminPasswordSetForm
)

from .models import CustomUser, PasswordResetRequest, UserActionLog

logger = logging.getLogger(__name__)


def log_user_action(action_type, description_field='username'):
    """Decorator to log user actions."""

    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            if request.user.is_authenticated:
                description = f"{action_type}"
                if description_field in kwargs:
                    description += f" for {kwargs[description_field]}"

                request.user.log_action(
                    action_type,
                    description,
                    request
                )

            return response

        return wrapped_view

    return decorator


def is_admin(user):
    """Check if user has admin privileges."""
    return user.is_staff or user.is_superuser


def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.is_approved = False
            user.save()

            request.session['just_registered_user_id'] = user.id
            return redirect('accounts:registration_received')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def registration_received_view(request):
    """Landing page shown right after registration."""
    user_id = request.session.pop('just_registered_user_id', None)
    context = {}

    if user_id:
        try:
            context['registered_user'] = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            pass

    return render(request, 'accounts/registration_received.html', context)


@never_cache
def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_approved:
                    login(request, user)
                    if user.password_change_required:
                        return redirect('accounts:force_password_change')
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')

                    next_page = request.GET.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect('home')
                else:
                    messages.warning(
                        request,
                        'Your account is pending approval. '
                        'Please wait for admin approval before logging in.'
                    )
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view with approval-required editing."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user, approval_required = form.save(commit=True, request_user=request.user)

            if approval_required:
                messages.info(
                    request,
                    'Your profile changes have been submitted for admin approval. '
                    'You will be notified once they are approved.'
                )
            else:
                messages.success(request, 'Profile updated successfully!')

            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'form': form,
        'profile_update_pending': request.user.profile_update_pending,
    }
    return render(request, 'accounts/profile.html', context)


def forgot_password_view(request):
    """Handle forgot password requests from non-authenticated users."""
    if request.user.is_authenticated:
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        username = request.POST.get('username')
        reason = request.POST.get('reason')

        try:
            user = CustomUser.objects.get(username=username, is_active=True)

            PasswordResetRequest.objects.create(
                user=user,
                requested_by=user,
                reason=reason,
                status='PENDING'
            )

            user.log_action(
                'PASSWORD_RESET_REQUEST',
                f'Password reset requested via forgot password. Reason: {reason}',
                request
            )

            messages.success(
                request,
                'Your password reset request has been submitted successfully. '
                'An administrator will review your request shortly.'
            )
            return redirect('accounts:login')

        except CustomUser.DoesNotExist:
            messages.error(request, 'Username not found or account is inactive.')
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')

    return render(request, 'accounts/forgot_password.html')


@login_required
def password_reset_request_view(request):
    """Allow users to request password reset (requires admin approval)."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST, request=request)
        if form.is_valid():
            user_to_reset = form.cleaned_data['user']
            reason = form.cleaned_data['reason']

            try:
                user_to_reset.request_password_reset(request.user, reason)

                messages.success(
                    request,
                    'Password reset request submitted successfully. '
                    'An administrator will review your request shortly.'
                )
                return redirect('accounts:dashboard')
            except PermissionError as e:
                messages.error(request, str(e))
    else:
        form = PasswordResetRequestForm(request=request)

    context = {
        'form': form,
        'user_can_request_others': request.user.is_administrator(),
    }
    return render(request, 'accounts/password_reset_request.html', context)


@login_required
@user_passes_test(is_admin)
def admin_password_reset_list(request):
    """Admin view for pending password reset requests."""
    pending_resets = PasswordResetRequest.objects.filter(status='PENDING').order_by('-created_at')
    approved_resets = PasswordResetRequest.objects.filter(status='APPROVED').order_by('-created_at')[:10]
    rejected_resets = PasswordResetRequest.objects.filter(status='REJECTED').order_by('-created_at')[:10]

    context = {
        'pending_resets': pending_resets,
        'approved_resets': approved_resets,
        'rejected_resets': rejected_resets,
        'total_pending': pending_resets.count(),
    }
    return render(request, 'accounts/admin_password_reset_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_review_password_reset(request, request_id):
    """Admin review and approve/reject password reset request."""
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id, status='PENDING')

    if request.method == 'POST':
        form = AdminPasswordResetReviewForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']

            reset_request.status = status
            reset_request.admin_notes = admin_notes
            reset_request.reviewed_by = request.user
            reset_request.reviewed_at = timezone.now()
            reset_request.save()

            reset_request.user.log_action(
                'PASSWORD_CHANGE',
                f'Password reset request {status.lower()} by administrator',
                request
            )

            if status == 'APPROVED':
                messages.success(request, f'Password reset for {reset_request.user.username} has been approved.')
            else:
                messages.warning(request, f'Password reset for {reset_request.user.username} has been rejected.')

            return redirect('accounts:admin_password_reset_list')
    else:
        form = AdminPasswordResetReviewForm()

    context = {
        'reset_request': reset_request,
        'form': form,
    }
    return render(request, 'accounts/admin_review_password_reset.html', context)


@login_required
@user_passes_test(is_admin)
def admin_set_password(request, request_id):
    """Admin set new password for approved reset request."""
    reset_request = get_object_or_404(
        PasswordResetRequest,
        id=request_id,
        status='APPROVED'
    )

    if request.method == 'POST':
        form = AdminPasswordSetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            reset_request.user.set_password(new_password)
            reset_request.user.last_password_change = timezone.now()
            reset_request.user.save()

            reset_request.status = 'COMPLETED'
            reset_request.save()

            reset_request.user.log_action(
                'PASSWORD_CHANGE',
                'Password reset completed by administrator',
                request
            )

            messages.success(
                request,
                f'Password for {reset_request.user.username} has been reset successfully.'
            )
            return redirect('accounts:admin_password_reset_list')
    else:
        form = AdminPasswordSetForm()

    context = {
        'reset_request': reset_request,
        'form': form,
    }
    return render(request, 'accounts/admin_set_password.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_activity(request, user_id):
    """View detailed user activity logs."""
    user = get_object_or_404(CustomUser, id=user_id)
    action_logs = user.action_logs.all()[:50]

    action_stats = user.action_logs.values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'target_user': user,
        'action_logs': action_logs,
        'action_stats': action_stats,
        'total_actions': user.action_logs.count(),
    }
    return render(request, 'accounts/admin_user_activity.html', context)


@login_required
@user_passes_test(is_admin)
def admin_system_activity(request):
    """View system-wide activity logs."""
    action_type = request.GET.get('action_type', '')
    user_id = request.GET.get('user_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    action_logs = UserActionLog.objects.all()

    if action_type:
        action_logs = action_logs.filter(action_type=action_type)

    if user_id:
        action_logs = action_logs.filter(user_id=user_id)

    if date_from:
        action_logs = action_logs.filter(timestamp__gte=date_from)

    if date_to:
        action_logs = action_logs.filter(timestamp__lte=date_to)

    action_logs = action_logs.select_related('user').order_by('-timestamp')[:100]

    active_users = CustomUser.objects.filter(is_active=True)

    context = {
        'action_logs': action_logs,
        'active_users': active_users,
        'action_types': UserActionLog.ACTION_TYPES,
        'filters': {
            'action_type': action_type,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'accounts/admin_system_activity.html', context)


@login_required
def delete_account_view(request):
    """Allow users to delete their own account."""
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            deleted_user = request.user

            deleted_user.is_active = False
            deleted_user.save()

            logout(request)

            messages.success(
                request,
                'Your account has been successfully deleted. '
                "We're sorry to see you go!"
            )
            return redirect('home')
    else:
        form = DeleteAccountForm()

    return render(request, 'accounts/delete_account.html', {'form': form})


@login_required
def dashboard_view(request):
    """Main dashboard - different views for admins and regular users."""
    user = request.user

    if user.is_administrator():
        return admin_dashboard(request)
    else:
        return user_dashboard(request)


def admin_dashboard(request):
    """Admin dashboard with user management and analytics."""
    total_users = CustomUser.objects.count()
    pending_approvals = CustomUser.objects.filter(is_approved=False, is_active=True).count()
    approved_users = CustomUser.objects.filter(is_approved=True).count()
    pending_password_resets = PasswordResetRequest.objects.filter(status='PENDING').count()

    role_distribution = CustomUser.objects.filter(is_approved=True).values(
        'company_role'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    section_distribution = CustomUser.objects.filter(is_approved=True).values(
        'section'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    recent_registrations = CustomUser.objects.filter(
        date_joined__gte=one_week_ago
    ).order_by('-date_joined')[:10]

    context = {
        'dashboard_type': 'admin',
        'total_users': total_users,
        'pending_approvals': pending_approvals,
        'approved_users': approved_users,
        'role_distribution': role_distribution,
        'pending_password_resets': pending_password_resets,
        'section_distribution': section_distribution,
        'recent_registrations': recent_registrations,
    }

    return render(request, 'accounts/admin_dashboard.html', context)


def user_dashboard(request):
    """Regular user dashboard with personal stats and quick actions."""
    user = request.user

    total_calculations = 0
    recent_calculations = []

    try:
        from extrusion.models import ExtrusionCalculation
        user_extrusion_calcs = ExtrusionCalculation.objects.filter(user=user)
        total_calculations += user_extrusion_calcs.count()
        recent_calculations.extend(list(user_extrusion_calcs.order_by('-timestamp')[:5]))
    except ImportError:
        pass

    try:
        from calculator.models import DensityCalculation
        user_density_calcs = DensityCalculation.objects.filter(user=user)
        total_calculations += user_density_calcs.count()
        recent_calculations.extend(list(user_density_calcs.order_by('-timestamp')[:5]))
    except ImportError:
        pass

    recent_calculations.sort(key=lambda x: x.timestamp, reverse=True)
    recent_calculations = recent_calculations[:5]

    context = {
        'dashboard_type': 'user',
        'user': user,
        'total_calculations': total_calculations,
        'recent_calculations': recent_calculations,
        'is_approved': user.is_approved,
    }

    return render(request, 'accounts/user_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_profile_approval_list(request):
    """Admin view for pending profile updates."""
    pending_updates = CustomUser.objects.filter(
        profile_update_pending=True,
        is_active=True
    ).order_by('date_joined')

    context = {
        'pending_updates': pending_updates,
        'total_pending': pending_updates.count(),
    }
    return render(request, 'accounts/admin_profile_approval_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_approval_list(request):
    """Admin view to see pending user approvals."""
    pending_users = CustomUser.objects.filter(is_approved=False, is_active=True).order_by('date_joined')
    approved_users = CustomUser.objects.filter(is_approved=True, is_active=True).order_by('-approved_date')

    context = {
        'pending_users': pending_users,
        'approved_users': approved_users,
        'total_pending': pending_users.count(),
        'total_approved': approved_users.count(),
    }
    return render(request, 'accounts/admin_user_approval_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_approve_user(request, user_id):
    """Approve a user account."""
    user_to_approve = get_object_or_404(CustomUser, id=user_id, is_approved=False)

    if request.method == 'POST':
        user_to_approve.is_approved = True
        user_to_approve.approved_by = request.user
        user_to_approve.approved_date = timezone.now()
        user_to_approve.save()

        messages.success(request, f'User {user_to_approve.username} has been approved successfully.')
        return redirect('accounts:admin_user_approval_list')

    context = {'user': user_to_approve}
    return render(request, 'accounts/admin_approve_user_confirm.html', context)


@login_required
@user_passes_test(is_admin)
def admin_reject_user(request, user_id):
    """Reject a user account (deactivate)."""
    user_to_reject = get_object_or_404(CustomUser, id=user_id, is_approved=False)

    if request.method == 'POST':
        user_to_reject.is_active = False
        user_to_reject.save()

        messages.warning(request, f'User {user_to_reject.username} has been rejected and deactivated.')
        return redirect('accounts:admin_user_approval_list')

    context = {'user': user_to_reject}
    return render(request, 'accounts/admin_reject_user_confirm.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_management(request):
    """Complete user management for admins."""
    all_users = CustomUser.objects.all().order_by('-date_joined')

    status_filter = request.GET.get('status', 'all')
    role_filter = request.GET.get('role', 'all')
    section_filter = request.GET.get('section', 'all')

    if status_filter == 'pending':
        all_users = all_users.filter(is_approved=False, is_active=True)
    elif status_filter == 'approved':
        all_users = all_users.filter(is_approved=True, is_active=True)
    elif status_filter == 'inactive':
        all_users = all_users.filter(is_active=False)
    else:
        all_users = all_users.filter(is_active=True)

    if role_filter != 'all':
        all_users = all_users.filter(company_role=role_filter)

    if section_filter != 'all':
        all_users = all_users.filter(section=section_filter)

    context = {
        'users': all_users,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'section_filter': section_filter,
        'total_users': all_users.count(),
        'role_choices': CustomUser.ROLE_CHOICES,
        'section_choices': CustomUser.SECTION_CHOICES,
    }
    return render(request, 'accounts/admin_user_management.html', context)


@login_required
@user_passes_test(is_admin)
def admin_approve_profile_update(request, user_id):
    """Approve a user's profile update."""
    user_to_approve = get_object_or_404(CustomUser, id=user_id, profile_update_pending=True)

    if request.method == 'POST':
        user_to_approve.approve_profile_update(request.user)

        messages.success(request, f'Profile update for {user_to_approve.username} has been approved.')
        return redirect('accounts:admin_profile_approval_list')

    context = {
        'user': user_to_approve,
        'pending_data': user_to_approve.pending_profile_data or {},
    }
    return render(request, 'accounts/admin_approve_profile_update.html', context)


@login_required
@user_passes_test(is_admin)
def admin_reject_profile_update(request, user_id):
    """Reject a user's profile update."""
    user_to_reject = get_object_or_404(CustomUser, id=user_id, profile_update_pending=True)

    if request.method == 'POST':
        user_to_reject.reject_profile_update()

        messages.warning(request, f'Profile update for {user_to_reject.username} has been rejected.')
        return redirect('accounts:admin_profile_approval_list')

    context = {
        'user': user_to_reject,
        'pending_data': user_to_reject.pending_profile_data or {},
    }
    return render(request, 'accounts/admin_reject_profile_update.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    """Admin delete user account."""
    user_to_delete = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete_account()

        messages.success(request, f'User account {username} has been deleted.')
        return redirect('accounts:admin_user_management')

    context = {'user': user_to_delete}
    return render(request, 'accounts/admin_delete_user.html', context)


@login_required
@user_passes_test(is_admin)
def admin_activate_user(request, user_id):
    """Admin activate deactivated user account."""
    user_to_activate = get_object_or_404(CustomUser, id=user_id, is_active=False)

    if request.method == 'POST':
        user_to_activate.is_active = True
        user_to_activate.save()

        messages.success(request, f'User account {user_to_activate.username} has been activated.')
        return redirect('accounts:admin_user_management')

    context = {'user': user_to_activate}
    return render(request, 'accounts/admin_activate_user.html', context)


def debug_email_test_view(request):
    """Debug view for testing email configuration."""
    import secrets
    import traceback

    try:
        expected_token = os.getenv('DEBUG_EMAIL_TOKEN')
        if not expected_token:
            return HttpResponse('DEBUG_EMAIL_TOKEN not configured', status=503)

        provided_token = request.GET.get('token', '')
        if not secrets.compare_digest(provided_token, expected_token):
            return HttpResponse('Unauthorized', status=403)

        to_email = request.GET.get('to')
        if not to_email:
            return HttpResponse('Missing ?to=email@example.com parameter', status=400)

        try:
            validate_email(to_email)
        except ValidationError:
            return HttpResponse('Invalid email address format', status=400)

        config_lines = [
            f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'NOT SET')}",
            f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NOT SET')}",
            f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NOT SET')}",
            f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')}",
            f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')}",
            f"EMAIL_HOST_PASSWORD set: {bool(getattr(settings, 'EMAIL_HOST_PASSWORD', None))}",
            f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}",
            f"IS_PRODUCTION: {getattr(settings, 'IS_PRODUCTION', 'NOT SET')}",
        ]

        try:
            result = send_mail(
                subject='PlastIQ Render SMTP test',
                message='If you got this, SMTP works from Render.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            response_lines = config_lines + [f"SUCCESS - send_mail returned: {result}"]
        except Exception as e:
            logger.error(f"SMTP test failed for {to_email}", exc_info=True)
            response_lines = config_lines + [
                f"SEND FAILED - {type(e).__name__}: {e}"
            ]

        return HttpResponse("\n".join(response_lines), content_type="text/plain")

    except Exception as outer_e:
        logger.error("Debug view crashed", exc_info=True)
        return HttpResponse(
            f"Internal error: {type(outer_e).__name__}",
            content_type="text/plain",
            status=500
        )


def admin_create_user_view(request):
    """Admin manually creates a single user account — approved immediately."""
    if not (request.user.is_authenticated and request.user.is_administrator()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:login')

    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            plain_password = form.cleaned_data['password']  # capture before it's hashed on save
            user = form.save()
            return render(request, 'accounts/admin_user_created.html', {
                'created_user': user,
                'plain_password': plain_password,
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCreateUserForm()

    return render(request, 'accounts/admin_create_user.html', {'form': form})


def admin_bulk_upload_users_view(request):
    """Admin uploads an Excel file to create many user accounts at once."""
    if not (request.user.is_authenticated and request.user.is_administrator()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:login')

    results = None

    if request.method == 'POST':
        form = BulkUserUploadForm(request.POST, request.FILES)
        if form.is_valid():
            results = _process_bulk_user_excel(request.FILES['excel_file'])
        else:
            messages.error(request, 'Please choose a valid .xlsx file.')
    else:
        form = BulkUserUploadForm()

    return render(request, 'accounts/admin_bulk_upload_users.html', {
        'form': form,
        'results': results,
    })


def _process_bulk_user_excel(excel_file):
    """Parse an uploaded .xlsx and create CustomUser rows. Returns a results dict."""
    import openpyxl

    created, skipped, errors = [], [], []

    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.active
    except Exception as e:
        return {'created': [], 'skipped': [], 'errors': [f'Could not read the file: {e}']}

    headers = []
    for cell in ws[1]:
        headers.append(str(cell.value).strip().lower() if cell.value is not None else '')

    required_cols = {'username', 'email', 'password'}
    if not required_cols.issubset(set(headers)):
        return {
            'created': [], 'skipped': [],
            'errors': [f'Missing required columns. Found: {headers}. Required at minimum: username, email, password.']
        }

    for row_num, row in enumerate(ws.iter_rows(min_row=2), start=2):
        if all(cell.value in (None, '') for cell in row):
            continue

        data = {headers[i]: (row[i].value if i < len(row) else None) for i in range(len(headers))}

        username = str(data.get('username') or '').strip()
        email = str(data.get('email') or '').strip()
        password = str(data.get('password') or '').strip()

        if not username or not email or not password:
            errors.append(f'Row {row_num}: missing username, email, or password.')
            continue

        if CustomUser.objects.filter(username=username).exists():
            skipped.append(f'Row {row_num}: username "{username}" already exists.')
            continue

        try:
            user = CustomUser(
                username=username,
                email=email,
                first_name=str(data.get('first_name') or '').strip(),
                last_name=str(data.get('last_name') or '').strip(),
                phone_number=str(data.get('phone_number') or '').strip(),
                company_role=str(data.get('company_role') or '').strip(),
                section=str(data.get('section') or '').strip(),
                company_branch=str(data.get('company_branch') or '').strip(),
                is_active=True,
                is_approved=True,
            )
            user.password_change_required = True  # Force them to set their own password on first login
            user.set_password(password)
            user.full_clean(exclude=['password'])
            user.save()
            created.append(username)
        except Exception as e:
            errors.append(f'Row {row_num} ("{username}"): {e}')

    return {'created': created, 'skipped': skipped, 'errors': errors}


def admin_bulk_upload_template_view(request):
    """Download a blank Excel template with the correct headers for bulk user upload."""
    import openpyxl
    from django.http import HttpResponse

    if not (request.user.is_authenticated and request.user.is_administrator()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:login')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Users"
    headers = [
        'username', 'email', 'password', 'first_name', 'last_name',
        'phone_number', 'company_role', 'section', 'company_branch',
    ]
    ws.append(headers)
    ws.append([
        'jdoe', 'jdoe@example.com', 'TempPass123', 'John', 'Doe',
        '+256700000000', 'operator', 'extrusion', 'kawempe',
    ])

    # Reference sheet listing every valid value for the choice columns, so admins
    # filling the template don't guess wrong and get a row silently skipped.
    ref_ws = wb.create_sheet("Valid Values")
    ref_ws.append(['company_role', 'section', 'company_branch'])
    role_values = ['admin', 'manager', 'supervisor', 'operator', 'qc_technician', 'sales_representative', 'engineer', 'other']
    section_values = ['extrusion', 'printing', 'lamination', 'slitting', 'bag_making', 'quality_control', 'maintenance', 'sales', 'other']
    branch_values = ['kawempe']
    max_len = max(len(role_values), len(section_values), len(branch_values))
    for i in range(max_len):
        ref_ws.append([
            role_values[i] if i < len(role_values) else '',
            section_values[i] if i < len(section_values) else '',
            branch_values[i] if i < len(branch_values) else '',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plastiq_bulk_user_template.xlsx"'
    wb.save(response)
    return response


@never_cache
def force_password_change_view(request):
    """Shown once to users whose account was created by an admin — they must set
    their own password before doing anything else in the system."""
    from django.contrib.auth.forms import SetPasswordForm
    from django.contrib.auth import update_session_auth_hash

    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if not request.user.password_change_required:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password_change_required = False
            user.save()
            update_session_auth_hash(request, user)  # keeps them logged in after changing password
            messages.success(request, 'Password updated. Welcome to PlastIQ!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordForm(request.user)

    return render(request, 'accounts/force_password_change.html', {'form': form})
