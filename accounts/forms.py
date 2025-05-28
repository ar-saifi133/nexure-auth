import datetime
from django.utils import timezone
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
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from .models import EmailChangeRequest
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib import messages
import uuid



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



class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users with username, full name, email and password.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Base input class
        base_input_class = (
            "  peer block bg-transparent  placeholder-transparent transition-colors duration-200 form-control w-full h-11 rounded-[10px] border border-[color:#8C8C8C] px-5 "
            "focus:ring-0 focus:outline-none focus:border-accent-grey "
            "text-[12px] font-medium placeholder:text-[12px] placeholder:font-light"
        )

        # Apply default classes and keep placeholders
        for field_name, field in self.fields.items():
            widget = field.widget

            # Skip if it's a checkbox or other non-text input
            if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                existing_attrs = widget.attrs
                existing = widget.attrs.get('class', '')
                placeholder = existing_attrs.get('placeholder', f"{field.label}*")
                widget.attrs.update({
                    'class': f"{base_input_class} {existing}",
                    'placeholder': placeholder
                })
    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control w-full h-11 rounded-[10px] border border-[color: #8C8C8C] pl-5', 'placeholder': 'Username*'}),
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
        widget=forms.TextInput(attrs={'class': 'form-control  w-full h-11 rounded-[10px] border border-[color: #8C8C8C] pl-5', 'placeholder': ''}),
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
        widget=forms.EmailInput(attrs={  'class': 'form-control text-sm font-medium w-full h-11 rounded-[10px] border border-accent-grey pl-5  focus:ring-0 focus:outline-none focus:border-accent-grey placeholder:text-sm placeholder:font-light', 'placeholder': 'Email*'}),
        validators=[validate_temp_email]
    )
    
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={ "id": "id_password1", 'class': ' form-control pr-10', 'placeholder': 'Password*'}),
        help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
        validators=[validate_password_complexity]
    )
    
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={ "id": "id_password2", 'class': 'form-control pr-10', 'placeholder': 'Confirm Password'})
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




# forms.py  (excerpt)

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "id": "reset-email",
                "class": (
                    "peer block w-[470px] h-[44px] rounded-[10px] border-[1px] border-gray-400 "
                    "bg-transparent px-7 pt-1.5 pb-2 text-[12px] text-[#FFFFFF] "
                    "placeholder-transparent focus:border-[#8c8c8c] focus:outline-none "
                    "transition-colors duration-200"
                ),
                "placeholder": " ",          # <-- literally one space
            }
        ),
    )

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # Base input class
        base_input_class = (
            "  peer block bg-transparent  placeholder-transparent transition-colors duration-200 form-control w-full h-11 rounded-[10px] border border-[color:#8C8C8C] pl-5 "
            "focus:ring-0 focus:outline-none focus:border-accent-grey "
            "text-[12px] font-medium placeholder:text-[12px ] placeholder:font-light"
        )


        # Apply default classes and keep placeholders
        for field_name, field in self.fields.items():
            widget = field.widget


            # Skip if it's a checkbox or other non-text input
            if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                existing_attrs = widget.attrs
                placeholder = existing_attrs.get('placeholder', f"{field.label}*")
                widget.attrs.update({
                    'class': base_input_class,
                    'placeholder': placeholder
                })
    """Login form that accepts both username and email"""
    username = forms.CharField(
        label=_("Email or Username"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        })
    )
   
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "id": "id_password1",
            'class': 'form-control',
            'placeholder': 'Password* '
        })
    )


    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        self.unverified_email = None  # Add this line


        if username and password:
            # First try standard authentication
            user = authenticate(
                request=self.request,
                username=username,
                password=password
            )

            # If authentication failed, check username/email manually
            if user is None:
                try:
                    user = User.objects.get(
                        Q(email__iexact=username) | Q(username=username)
                    )
                except User.DoesNotExist:
                    user = None

                # Validate password if user exists
                if user and not user.check_password(password):
                    user = None

            # If we have a valid user at this point
            if user:
                self.user_cache = user  # Critical: Set user_cache
                
                # Check if user is allowed to login
                self.confirm_login_allowed(user)  # Handles is_active check
                
                # Custom email verification check
                if not user.email_verified:
                    self.unverified_email = user.email
                    raise ValidationError("Account not verified. Please check your email.")
            else:
                raise ValidationError("Invalid email/username or password.")

            return self.cleaned_data

        raise ValidationError("Both username and password are required.")








class CustomSetPasswordForm(SetPasswordForm):
    """
    A form for setting a new password for a user.
    """
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
        attrs={
        "id": "first-password",
                "class": (
                    "peer block w-[470px] h-[44px] rounded-[10px] border-[1px] border-gray-400 "
                    "bg-transparent px-7 pt-1.5 pb-2 text-[12px] text-[#FFFFFF] "
                    "placeholder-transparent focus:border-[#8c8c8c] focus:outline-none "
                    "transition-colors duration-200"
                ),
                "placeholder": " ",
        }
        ),
        help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
        validators=[validate_password_complexity]
    )
    
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(
        attrs={
            "id": "second-password",
                "class": (
                    "peer block w-[470px] h-[44px] rounded-[10px] border-[1px] border-gray-400 "
                    "bg-transparent px-7 pt-1.5 pb-2 text-[12px] text-[#FFFFFF] "
                    "placeholder-transparent focus:border-[#8c8c8c] focus:outline-none "
                    "transition-colors duration-200"
                ),
                "placeholder": " ",
        }
        )
    )

    def clean_new_password1(self):
        old_password = self.user.password
        new_password = self.cleaned_data.get('new_password1')
        
        if self.user.check_password(new_password):
            raise ValidationError(_("New password cannot be same as current password."))
            
        return new_password




class ProfileUpdateForm(forms.ModelForm):


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)




   class Meta:
       model = User
       fields = ['full_name', 'username', ]
       widgets = {
         'full_name': forms.TextInput(attrs={
               'class': ' text-[#000000] text-[14px] border-[#33ccff] focus:outline-none focus:ring-0 w-[441px] box-border border border-[rgba(140,140,140,0.3)] rounded-[10px] w-[441px] h-[40px] px-5 py-3 focus:border-[rgba(140,140,140,0.3)]'
           }),
           'username': forms.TextInput(attrs={
               'class': ' text-primary-black text-[14px] focus:outline-none focus:ring-0 w-[441px] box-border border border-[rgba(140,140,140,0.3)] rounded-[10px] w-[441px] h-[40px] px-5 py-3'
           }),
           
       }







   # def __init__(self, *args, **kwargs):
   #     super().__init__(*args, **kwargs)
   #     # Initialize avatar selection with current avatar
   #     self.fields['avatar'].initial = self.instance.avatar


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("This email is already in use."))
        return email


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("This username is already in use."))
        return username


    def save(self, commit=True):
        user = super().save(commit=False)
        new_email = self.cleaned_data.get('email')
        
        # Get ORIGINAL email from database, not form data
        current_email = User.objects.get(pk=user.pk).email  # Critical fix
        
        if new_email != current_email:
            # Delete previous requests
            EmailChangeRequest.objects.filter(user=user).delete()
            
            # Create new request
            token = uuid.uuid4()
            expires_at = timezone.now() + datetime.timedelta(hours=24)
            EmailChangeRequest.objects.create(
                user=user,
                new_email=new_email,
                token=token,
                expires_at=expires_at
            )
            
            # Build verification URL
            verification_url = self.request.build_absolute_uri(
                reverse('accounts:verify_email_change', args=[str(token)])
            )
            
            # Send email
            subject = 'Verify Your New Email Address'
            html_message = render_to_string('accounts/profile/email_change_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'expiry_time': '24 hours'
            })
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(self.request, 'Verification link sent to your new email. Please check your inbox. After verification, you can log in with the new email.')
            
            # Revert to original email
            user.email = current_email  # Now correctly uses original email

        if commit:
            user.save()
        return user



class AvatarUpdateForm(forms.ModelForm):
   AVATAR_CHOICES = [
       (f'avatar{i}.webp', f'Avatar {i}') for i in range(1, 31)
   ]


   avatar = forms.ChoiceField(
       choices=AVATAR_CHOICES,
       widget=forms.RadioSelect(attrs={'class': 'hidden group'}),
       required=True,
       label="Profile Picture"
   )


   class Meta:
       model = User
       fields = ['avatar']


   def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self.fields['avatar'].initial = self.instance.avatar



class DeleteAccountForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="All data associated with this account will be deleted",
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'})
    )
    confirm2 = forms.BooleanField(
        required=True,
        label="I agree to this action, knowing it cannot be undone",
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'})
    )
    password = forms.CharField(
        label="Current Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control focus:ring-0 focus:outline-none focus:border-accent-grey border border-accent-grey/30 h-[40px] px-5 w-full rounded-[10px] placeholder:text-[14px] placeholder:font-medium', 'placeholder':'Password*'}),
        required=True
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError(_("The password is incorrect."))
        return password



class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label=_("Current Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': ' focus:outline-none font-medium text-[14px] overflow-hidden border border-accent-grey/30 rounded-[10px] w-[400px] px-[20px] h-10 flex items-center placeholder:text-[12px] placeholder:font-normal', 'placeholder': 'Current Password*'})
    )
    new_password1 = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(attrs={'class': " focus:outline-none font-medium text-[14px] overflow-hidden border border-accent-grey/30 rounded-[10px] w-[400px] px-[20px] h-10 flex items-center placeholder:text-[12px] placeholder:font-normal", 'placeholder': 'New Password*'}),
        help_text=_("Password must be at least 8 characters with uppercase, lowercase, numbers and symbols."),
        validators=[validate_password_complexity]
    )
    new_password2 = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={'class': " focus:outline-none font-medium text-[14px] overflow-hidden border border-accent-grey/30 rounded-[10px] w-[400px] px-[20px] h-10 flex items-center placeholder:text-[12px] placeholder:font-normal", 'placeholder': 'Confirm Password*'})
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_("Your current password was entered incorrectly."))
        return old_password

    def clean_new_password1(self):
        new_password = self.cleaned_data.get('new_password1')
        
        if self.user.check_password(new_password):
            raise ValidationError(
                _("New password cannot be the same as your current password.")
            )
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('new_password1') != cleaned_data.get('new_password2'):
            self.add_error('new_password2', "Passwords don't match.")
        return cleaned_data

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()