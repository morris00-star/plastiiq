from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re
from django.utils import timezone


class UserActionLog(models.Model):
    ACTION_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('CALCULATION', 'Calculation Performed'),
        ('ACCOUNT_CREATE', 'Account Created'),
        ('ACCOUNT_DELETE', 'Account Deleted'),
        ('PASSWORD_RESET_REQUEST', 'Password Reset Requested'),
    ]

    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='action_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"


class PasswordResetRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='password_reset_requests')
    requested_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='requested_resets')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_resets')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Password reset for {self.user.username} - {self.status}"


class CustomUser(AbstractUser):
    BRANCH_CHOICES = [('kawempe', 'Kawempe')]
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('supervisor', 'Supervisor'),
        ('operator', 'Operator'),
        ('qc_technician', 'QC Technician'),
        ('sales_representative', 'Sales Representative'),
        ('engineer', 'Engineer'),
        ('other', 'Other'),
    ]
    SECTION_CHOICES = [
        ('extrusion', 'Extrusion'),
        ('printing', 'Printing'),
        ('lamination', 'Lamination'),
        ('slitting', 'Slitting'),
        ('bag_making', 'Bag Making'),
        ('quality_control', 'Quality Control'),
        ('maintenance', 'Maintenance'),
        ('sales', 'Sales'),
        ('other', 'Other'),
    ]

    phone_number = models.CharField(max_length=15, blank=True, default='')
    company_branch = models.CharField(max_length=20, choices=BRANCH_CHOICES, default='kawempe')
    company_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='other')
    is_approved = models.BooleanField(default=False)

    # Profile editing approval system
    profile_update_pending = models.BooleanField(default=False)
    pending_profile_data = models.JSONField(blank=True, null=True)

    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Password reset tracking
    last_password_change = models.DateTimeField(null=True, blank=True)
    password_change_required = models.BooleanField(default=False)

    def clean(self):
        super().clean()

        if self.phone_number and self.phone_number.strip():
            phone_regex = r'^\+?1?\d{9,15}$'
            if not re.match(phone_regex, self.phone_number):
                raise ValidationError({'phone_number': 'Enter a valid phone number.'})

    def save(self, *args, **kwargs):
        if self.is_staff or self.is_superuser or self.company_role == 'admin':
            self.is_approved = True
            self.is_staff = True

        super().save(*args, **kwargs)

    def is_administrator(self):
        return self.company_role == 'admin' or self.is_superuser or self.is_staff

    def can_approve_users(self):
        return self.is_administrator()

    def get_role_display_name(self):
        return dict(self.ROLE_CHOICES).get(self.company_role, self.company_role)

    def get_section_display_name(self):
        return dict(self.SECTION_CHOICES).get(self.section, self.section)

    @property
    def pending_approvals_count(self):
        if self.is_administrator():
            return CustomUser.objects.filter(is_approved=False, is_active=True).count()
        return 0

    @property
    def pending_profile_updates_count(self):
        if self.is_administrator():
            return CustomUser.objects.filter(profile_update_pending=True, is_active=True).count()
        return 0

    @property
    def pending_password_resets_count(self):
        if self.is_administrator():
            return PasswordResetRequest.objects.filter(status='PENDING').count()
        return 0

    def log_action(self, action_type, description, request=None):
        """Log user action with optional request context"""
        ip_address = None
        user_agent = ""

        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        UserActionLog.objects.create(
            user=self,
            action_type=action_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def request_password_reset(self, requested_by, reason):
        """Request password reset that requires admin approval"""
        if requested_by != self and not requested_by.is_administrator():
            raise PermissionError("Only administrators can request password resets for other users")

        PasswordResetRequest.objects.create(
            user=self,
            requested_by=requested_by,
            reason=reason,
            status='PENDING'
        )

        # Log the action
        self.log_action(
            'PASSWORD_RESET_REQUEST',
            f'Password reset requested by {requested_by.username}. Reason: {reason}'
        )

    def approve_profile_update(self, approved_by):
        """Approve pending profile update"""
        if self.pending_profile_data and self.profile_update_pending:
            for field, value in self.pending_profile_data.items():
                if hasattr(self, field) and field not in ['username', 'email', 'password']:
                    setattr(self, field, value)

            self.pending_profile_data = None
            self.profile_update_pending = False
            self.approved_by = approved_by
            self.approved_date = timezone.now()
            self.save()

            self.log_action(
                'PROFILE_UPDATE',
                'Profile update approved by administrator'
            )

    def reject_profile_update(self):
        """Reject pending profile update"""
        self.pending_profile_data = None
        self.profile_update_pending = False
        self.save()

        self.log_action(
            'PROFILE_UPDATE',
            'Profile update rejected by administrator'
        )

    def delete_account(self):
        """Soft delete user account"""
        self.is_active = False
        self.save()

        self.log_action(
            'ACCOUNT_DELETE',
            'Account deactivated'
        )

    def get_recent_actions(self, limit=10):
        """Get recent user actions"""
        return self.action_logs.all()[:limit]

    def __str__(self):
        return f"{self.username} - {self.get_role_display_name()}"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
