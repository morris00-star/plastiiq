from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import CustomUserCreationForm, CustomUserLoginForm, UserProfileForm, DeleteAccountForm, \
    PasswordResetRequestForm, AdminPasswordResetReviewForm, AdminPasswordSetForm
from .models import CustomUser, PasswordResetRequest, UserActionLog


def log_user_action(action_type, description_field='username'):
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
    return user.is_staff or user.is_superuser


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User is active but not approved
            user.is_approved = False  # Needs admin approval
            user.save()

            messages.success(
                request,
                'Registration successful! Your account is pending admin approval. '
                'You will be notified once your account is approved.'
            )
            return redirect('accounts:login')  # Fixed: use namespaced URL
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Try to authenticate with username
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_approved:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')

                    # Redirect to next page if specified
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
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view with approval-required editing"""
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
    """Handle forgot password requests from non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        username = request.POST.get('username')
        reason = request.POST.get('reason')

        try:
            user = CustomUser.objects.get(username=username, is_active=True)

            # Create password reset request
            PasswordResetRequest.objects.create(
                user=user,
                requested_by=user,  # User requesting for themselves
                reason=reason,
                status='PENDING'
            )

            # Log the action
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
    """Allow users to request password reset (requires admin approval)"""
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
    """Admin view for pending password reset requests"""
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
    """Admin review and approve/reject password reset request"""
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

            # Log the action
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
    """Admin set new password for approved reset request"""
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

            # Update reset request status
            reset_request.status = 'COMPLETED'
            reset_request.save()

            # Log the action
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
    """View detailed user activity logs"""
    user = get_object_or_404(CustomUser, id=user_id)
    action_logs = user.action_logs.all()[:50]  # Last 50 actions

    # Get statistics
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
    """View system-wide activity logs"""
    # Get filter parameters
    action_type = request.GET.get('action_type', '')
    user_id = request.GET.get('user_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Build query
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

    # Get available users for filter
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
    """Allow users to delete their own account"""
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            # Soft delete the user account
            request.user.is_active = False
            request.user.save()

            # Logout the user
            logout(request)

            messages.success(
                request,
                'Your account has been successfully deleted. '
                'We\'re sorry to see you go!'
            )
            return redirect('home')
    else:
        form = DeleteAccountForm()

    return render(request, 'accounts/delete_account.html', {'form': form})


@login_required
def dashboard_view(request):
    """Main dashboard - different views for admins and regular users"""
    user = request.user

    if user.is_administrator():
        return admin_dashboard(request)
    else:
        return user_dashboard(request)


def admin_dashboard(request):
    """Admin dashboard with user management and analytics"""
    # User statistics
    total_users = CustomUser.objects.count()
    pending_approvals = CustomUser.objects.filter(is_approved=False, is_active=True).count()
    approved_users = CustomUser.objects.filter(is_approved=True).count()
    pending_password_resets = PasswordResetRequest.objects.filter(status='PENDING').count()

    # User role distribution
    role_distribution = CustomUser.objects.filter(is_approved=True).values(
        'company_role'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # Section distribution
    section_distribution = CustomUser.objects.filter(is_approved=True).values(
        'section'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent registrations (last 7 days)
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    recent_registrations = CustomUser.objects.filter(
        date_joined__gte=one_week_ago
    ).order_by('-date_joined')[:10]

    # Recent activity (you can expand this with actual activity data)
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
    """Regular user dashboard with personal stats and quick actions"""
    user = request.user

    # Get user's calculation statistics (you'll need to implement these)
    total_calculations = 0
    recent_calculations = []

    # Try to get calculation stats from different apps
    try:
        from extrusion.models import ExtrusionCalculation
        user_extrusion_calcs = ExtrusionCalculation.objects.filter(user=user)
        total_calculations += user_extrusion_calcs.count()
        recent_calculations.extend(list(user_extrusion_calcs.order_by('-timestamp')[:5]))
    except:
        pass

    try:
        from calculator.models import DensityCalculation
        user_density_calcs = DensityCalculation.objects.filter(user=user)
        total_calculations += user_density_calcs.count()
        recent_calculations.extend(list(user_density_calcs.order_by('-timestamp')[:5]))
    except:
        pass

    # Sort recent calculations by timestamp
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
    """Admin view for pending profile updates"""
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
    """Admin view to see pending user approvals"""
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
    """Approve a user account"""
    user_to_approve = get_object_or_404(CustomUser, id=user_id, is_approved=False)

    if request.method == 'POST':
        user_to_approve.is_approved = True
        user_to_approve.approved_by = request.user
        user_to_approve.approved_date = timezone.now()
        user_to_approve.save()

        messages.success(request, f'User {user_to_approve.username} has been approved successfully.')
        return redirect('accounts:admin_user_approval_list')  # Fixed URL name

    context = {'user': user_to_approve}
    return render(request, 'accounts/admin_approve_user_confirm.html', context)


@login_required
@user_passes_test(is_admin)
def admin_reject_user(request, user_id):
    """Reject a user account (deactivate)"""
    user_to_reject = get_object_or_404(CustomUser, id=user_id, is_approved=False)

    if request.method == 'POST':
        user_to_reject.is_active = False
        user_to_reject.save()

        messages.warning(request, f'User {user_to_reject.username} has been rejected and deactivated.')
        return redirect('accounts:admin_user_approval_list')  # Fixed URL name

    context = {'user': user_to_reject}
    return render(request, 'accounts/admin_reject_user_confirm.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_management(request):
    """Complete user management for admins"""
    all_users = CustomUser.objects.all().order_by('-date_joined')

    # Filter users
    status_filter = request.GET.get('status', 'all')
    role_filter = request.GET.get('role', 'all')
    section_filter = request.GET.get('section', 'all')

    if status_filter == 'pending':
        all_users = all_users.filter(is_approved=False, is_active=True)
    elif status_filter == 'approved':
        all_users = all_users.filter(is_approved=True, is_active=True)
    elif status_filter == 'inactive':
        all_users = all_users.filter(is_active=False)

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
    """Approve a user's profile update"""
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
    """Reject a user's profile update"""
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
    """Admin delete user account"""
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
    """Admin activate deactivated user account"""
    user_to_activate = get_object_or_404(CustomUser, id=user_id, is_active=False)

    if request.method == 'POST':
        user_to_activate.is_active = True
        user_to_activate.save()

        messages.success(request, f'User account {user_to_activate.username} has been activated.')
        return redirect('accounts:admin_user_management')

    context = {'user': user_to_activate}
    return render(request, 'accounts/admin_activate_user.html', context)

