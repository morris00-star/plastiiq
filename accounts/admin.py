from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser

    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'company_role', 'company_branch', 'section',
        'is_approved', 'is_active', 'date_joined'
    ]

    list_filter = [
        'is_approved', 'is_active', 'is_staff', 'company_branch',
        'company_role', 'section', 'date_joined'
    ]

    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'phone_number'
    ]

    fieldsets = UserAdmin.fieldsets + (
        ('Company Information', {
            'fields': (
                'phone_number', 'company_branch', 'company_role',
                'section', 'is_approved', 'approved_by'
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Company Information', {
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'company_branch', 'company_role', 'section'
            )
        }),
    )

    readonly_fields = ['date_joined']

    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_date=timezone.now()
        )
        self.message_user(request, f'{updated} users approved successfully.')

    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        updated = queryset.update(
            is_approved=False,
            approved_by=None,
            approved_date=None
        )
        self.message_user(request, f'{updated} users rejected.')

    reject_users.short_description = "Reject selected users"
