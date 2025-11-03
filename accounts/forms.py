from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import password_validation
from .models import CustomUser, PasswordResetRequest
import re


class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'company_branch', 'company_role', 'section', 'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'company_branch': forms.Select(attrs={'class': 'form-control'}),
            'company_role': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            phone_regex = r'^\+?1?\d{9,15}$'
            if not re.match(phone_regex, phone_number):
                raise forms.ValidationError('Enter a valid phone number.')
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email


class CustomUserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'company_role', 'section']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company_role': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True, request_user=None):
        user = super().save(commit=False)

        # Check if changes require approval
        approval_required = False
        if request_user and not request_user.is_administrator():
            # Regular users need approval for role/section changes
            original_user = CustomUser.objects.get(pk=user.pk)
            if (original_user.company_role != user.company_role or
                    original_user.section != user.section):
                approval_required = True

        if approval_required:
            # Store pending changes
            pending_data = {}
            for field in self.Meta.fields:
                if getattr(original_user, field) != getattr(user, field):
                    pending_data[field] = getattr(user, field)

            user.pending_profile_data = pending_data
            user.profile_update_pending = True

            # Don't apply changes immediately
            for field, value in pending_data.items():
                setattr(user, field, getattr(original_user, field))

        if commit:
            user.save()

            # Log the action
            if request_user:
                action_type = 'PROFILE_UPDATE'
                if approval_required:
                    action_type += '_REQUEST'
                user.log_action(
                    action_type,
                    'Profile updated' + (' (pending approval)' if approval_required else ''),
                    request=None  # You can pass request if available
                )

        return user, approval_required


class DeleteAccountForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I understand that this action cannot be undone",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Tell us why you are leaving...',
            'rows': 3
        })
    )


class PasswordResetRequestForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True),
        empty_label="Select User",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Explain why this password reset is needed...',
            'rows': 4
        }),
        help_text="Provide a detailed reason for the password reset request"
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request and self.request.user.is_authenticated:
            if not self.request.user.is_administrator():
                # Regular users can only request for themselves
                self.fields['user'].queryset = CustomUser.objects.filter(id=self.request.user.id)
                self.fields['user'].initial = self.request.user
                self.fields['user'].widget.attrs['readonly'] = True
        else:
            # For non-authenticated users, don't show user selection
            self.fields['user'].widget = forms.HiddenInput()


class AdminPasswordResetReviewForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('APPROVED', 'Approve Reset'),
            ('REJECTED', 'Reject Request'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add notes for the user (optional)...',
            'rows': 3
        }),
        help_text="These notes will be visible to the user"
    )


class AdminPasswordSetForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        password_validation.validate_password(password2)
        return password2
