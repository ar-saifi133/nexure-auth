# from django import forms
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
# from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _

# User = get_user_model()

# class CustomUserCreationForm(UserCreationForm):
#     """
#     A form for creating new users with full name, email and password.
#     """
#     full_name = forms.CharField(
#         label=_("Full Name"),
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}
#         validators=[
#             RegexValidator(
#                 regex=r'^[A-Za-z ]+$',
#                 message='Name must contain only alphabets and spaces.',
#                 code='invalid_name'
#             )
#         ])
#     )

#     email = forms.EmailField(
#         label=_("Email"),
#         max_length=254,
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
#     )
#     password1 = forms.CharField(
#         label=_("Password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
#         help_text=_("At least 8 characters with letters, numbers, and symbols.")
#     )
#     password2 = forms.CharField(
#         label=_("Confirm Password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
#     )

#     class Meta:
#         model = User
#         fields = ('full_name', 'email', 'password1', 'password2')

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise ValidationError(_("This email is already in use."))
#         return email

#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#         if password1 and password2 and password1 != password2:
#             raise ValidationError(_("Passwords don't match."))
#         return password2


# class CustomAuthenticationForm(AuthenticationForm):
#     """
#     A form for authenticating users with email and password.
#     """
#     username = forms.EmailField(
#         label=_("Email"),
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
#     )
#     password = forms.CharField(
#         label=_("Password"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
#     )


# class CustomPasswordResetForm(PasswordResetForm):
#     """
#     A form for generating a password reset token for a user.
#     """
#     email = forms.EmailField(
#         label=_("Email"),
#         max_length=254,
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
#     )


# class CustomSetPasswordForm(SetPasswordForm):
#     """
#     A form for setting a new password for a user.
#     """
#     new_password1 = forms.CharField(
#         label=_("New password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
#         help_text=_("At least 8 characters with letters, numbers, and symbols.")
#     )
#     new_password2 = forms.CharField(
#         label=_("Confirm new password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
#     )





from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import re
from django.db import models 
from django.contrib.auth import authenticate
from django.db.models import Q


User = get_user_model()

# List of temporary email domains to block
TEMP_EMAIL_DOMAINS = [
    'mailinator.com', 
    'tempmail.com', 
    '10minutemail.com',
    'guerrillamail.com',
    'trashmail.com',
    'fakeinbox.com',
    'maildrop.cc'
]

def validate_password_complexity(password):
    """
    Validate that the password meets complexity requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("Password must contain at least one special character.")
    
    if errors:
        raise ValidationError(errors)

def validate_temp_email(email):
    """
    Validate that the email is not from a temporary email service
    """
    domain = email.split('@')[-1].lower()
    if domain in TEMP_EMAIL_DOMAINS:
        raise ValidationError("Temporary email addresses are not allowed.")

# class CustomUserCreationForm(UserCreationForm):
#     """
#     A form for creating new users with full name, email and password.
#     """
#     full_name = forms.CharField(
#         label=_("Full Name"),
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
#         validators=[
#             RegexValidator(
#                 regex=r'^[A-Za-z ]+$',
#                 message='Name must contain only alphabets and spaces.',
#                 code='invalid_name'
#             )
#         ]
#     )
    
#     email = forms.EmailField(
#         label=_("Email"),
#         max_length=254,
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
#         validators=[validate_temp_email]
#     )
    
#     password1 = forms.CharField(
#         label=_("Password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
#         help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
#         validators=[validate_password_complexity]
#     )
    
#     password2 = forms.CharField(
#         label=_("Confirm Password"),
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
#     )

#     class Meta:
#         model = User
#         fields = ('full_name', 'email', 'password1', 'password2')

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise ValidationError(_("This email is already in use."))
#         return email

#     def clean(self):
#         cleaned_data = super().clean()
#         password1 = cleaned_data.get('password1')
#         password2 = cleaned_data.get('password2')
        
#         if password1 and password2 and password1 != password2:
#             self.add_error('password2', "Passwords don't match.")
        
#         return cleaned_data




class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users with username, full name, email and password.
    """
    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.'
            )
        ],
        help_text=_('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    
    full_name = forms.CharField(
        label=_("Full Name"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z ]+$',
                message='Name must contain only alphabets and spaces.',
                code='invalid_name'
            )
        ]
    )
    
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        validators=[validate_temp_email]
    )
    
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
        help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
        validators=[validate_password_complexity]
    )
    
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(_("This username is already in use."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("This email is already in use."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords don't match.")
        
        return cleaned_data




class CustomPasswordResetForm(PasswordResetForm):
    """
    A form for generating a password reset token for a user.
    """
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

# class CustomAuthenticationForm(AuthenticationForm):
#     """
#     A form for authenticating users with email and password.
#     """
#     username = forms.EmailField(
#         label=_("Email"),
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
#     )
#     password = forms.CharField(
#         label=_("Password"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
#     )

#     def clean(self):
#         email = self.cleaned_data.get('username')
#         password = self.cleaned_data.get('password')

#         if email and password:
#             try:
#                 user = User.objects.get(email=email)
#                 if not user.is_active:
#                     raise ValidationError(_("This account is not verified. Please check your email for verification link."))
#             except User.DoesNotExist:
#                 raise ValidationError(_("Account not found. Please check your email or sign up."))
                
#         return super().clean()


class CustomAuthenticationForm(AuthenticationForm):
    """Login form that accepts both username and email"""
    username = forms.CharField(
        label=_("Email or Username"),
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your email or username'
        })
    )
    
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Initial authentication attempt using the provided credentials
            user = authenticate(
                request=self.request,
                username=username,
                password=password
            )
            
            # If authentication fails, check if the input is a username
            if user is None:
                try:
                    # Check if the input matches a username
                    user_by_username = User.objects.get(username=username)
                    # Attempt authentication using the user's email (USERNAME_FIELD)
                    user = authenticate(
                        request=self.request,
                        username=user_by_username.email,
                        password=password
                    )
                except User.DoesNotExist:
                    pass

            # If still not authenticated, check if the input is an email (case-insensitive)
            if user is None:
                try:
                    user_by_email = User.objects.get(email__iexact=username)
                    # Attempt authentication with the retrieved email
                    user = authenticate(
                        request=self.request,
                        username=user_by_email.email,
                        password=password
                    )
                except User.DoesNotExist:
                    pass

            if user is None:
                raise ValidationError(_("Invalid email/username or password."))
                
            if not user.email_verified:
                raise ValidationError(_("Account not verified. Please check your email."))
                
            self.user_cache = user
            
        return self.cleaned_data




class CustomSetPasswordForm(SetPasswordForm):
    """
    A form for setting a new password for a user.
    """
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
        validators=[validate_password_complexity]
    )
    
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean_new_password1(self):
        old_password = self.user.password
        new_password = self.cleaned_data.get('new_password1')
        
        if self.user.check_password(new_password):
            raise ValidationError(_("New password cannot be same as current password."))
            
        return new_password