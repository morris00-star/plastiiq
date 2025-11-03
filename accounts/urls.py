from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('delete-account/', views.delete_account_view, name='delete_account'),

    # Admin URLs
    path('admin/approval-list/', views.admin_user_approval_list, name='admin_user_approval_list'),
    path('admin/approve-user/<int:user_id>/', views.admin_approve_user, name='admin_approve_user'),
    path('admin/reject-user/<int:user_id>/', views.admin_reject_user, name='admin_reject_user'),
    path('admin/user-management/', views.admin_user_management, name='admin_user_management'),
    path('admin/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin/activate-user/<int:user_id>/', views.admin_activate_user, name='admin_activate_user'),

    # Profile approval URLs
    path('admin/profile-approvals/', views.admin_profile_approval_list, name='admin_profile_approval_list'),
    path('admin/approve-profile/<int:user_id>/', views.admin_approve_profile_update,
         name='admin_approve_profile_update'),
    path('admin/reject-profile/<int:user_id>/', views.admin_reject_profile_update, name='admin_reject_profile_update'),

    # Password reset requests
    path('password-reset-request/', views.password_reset_request_view, name='password_reset_request'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # Password reset management
    path('admin/password-resets/', views.admin_password_reset_list, name='admin_password_reset_list'),
    path('admin/review-password-reset/<int:request_id>/', views.admin_review_password_reset, name='admin_review_password_reset'),
    path('admin/set-password/<int:request_id>/', views.admin_set_password, name='admin_set_password'),

    # Activity monitoring
    path('admin/user-activity/<int:user_id>/', views.admin_user_activity, name='admin_user_activity'),
    path('admin/system-activity/', views.admin_system_activity, name='admin_system_activity'),
]
