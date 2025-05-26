import datetime
import time
from django.http import JsonResponse
import uuid
import random
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from django.conf import settings
from urllib.parse import urlparse
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    ProfileUpdateForm,
    DeleteAccountForm,
    AvatarUpdateForm,
    CustomPasswordChangeForm
)
from .models import PasswordResetToken, EmailVerificationToken
from .serializers import CustomTokenObtainPairSerializer
import logging
from django.views.decorators.csrf import csrf_exempt


from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited
from django.contrib.auth import update_session_auth_hash




logger = logging.getLogger(__name__)

User = get_user_model()




# @ratelimit(key='ip', rate='5/h', method='POST', block=True)
# accounts/views.py
from django.core.mail import send_mail, EmailMessage  # Added EmailMessage import
from django.conf import settings
import logging
from django.utils.html import escape

logger = logging.getLogger(__name__)

@csrf_exempt
def signup_view(request):
    """View for user registration with proper error handling"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.avatar = f'avatar{random.randint(1, 30)}.webp'
            
            try:
                user.save()
            except Exception as e:
                logger.error(f"User creation failed: {str(e)}")
                messages.error(request, 'Registration failed. Please try again.')
                return redirect('accounts:signup')

            try:
                # Create verification token
                token = EmailVerificationToken.objects.create(
                    user=user,
                    expires_at=timezone.now() + datetime.timedelta(hours=24)
                )
                
                verification_url = request.build_absolute_uri(
                    reverse('accounts:verify_email', args=[str(token.token)])
                )

                # Send email using proper HTML template
                subject = 'Verify Your Email Address'
                html_message = render_to_string('accounts/email_verification.html', {
                    'user': user,
                    'verification_url': verification_url,
                    'expiry_time': '24 hours'
                })
                plain_message = f"Please verify your email: {verification_url}"

                # Use EmailMessage for better control
                email = EmailMessage(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                email.content_subtype = "html"  # Main content is HTML
                email.body = html_message
                email.send(fail_silently=False)

                request.session['verification_email'] = user.email
                messages.success(request, 'Registration successful! Check your email for verification.')
                return redirect('accounts:email_sent')

            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                user.delete()  # Rollback user creation
                messages.error(request, 'Failed to send verification email. Please contact support.')
                return redirect('accounts:signup')

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})




def email_sent_view(request):
    """View to show after email verification is sent"""
    email = request.session.get('verification_email')
    if not email:
        return redirect('accounts:signup')
        
    return render(request, 'accounts/email_sent.html', {'email': email})



def verify_email_view(request, token):
    """View to verify email"""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if not verification_token.is_valid():
            messages.error(request, 'The verification link has expired.')
            request.session['verification_email'] = verification_token.user.email
            return redirect('accounts:email_sent')
            
        user = verification_token.user
        user.is_active = True
        user.email_verified = True
        user.save()
        
        EmailVerificationToken.objects.filter(user=user).delete()
        
        messages.success(request, 'Email verified successfully!')
        return redirect('accounts:login')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:email_sent')



#@ratelimit(key='ip', rate='2/h', method='POST', block=True)
# def resend_verification_view(request):
#     """View to resend verification email"""
#     if request.method == 'POST':
#         email = request.POST.get('email')
        
#         try:
#             user = User.objects.get(email=email)
            
#             if user.email_verified:
#                 messages.info(request, 'Email is already verified. You can login now.')
#                 return redirect('accounts:login')
                
#             # Delete any existing tokens
#             EmailVerificationToken.objects.filter(user=user).delete()
            
#             # Create new token
#             token = EmailVerificationToken.objects.create(
#                 user=user,
#                 expires_at=timezone.now() + datetime.timedelta(hours=24)
#             )
            
#             # Build verification URL
#             verification_url = request.build_absolute_uri(
#                 reverse('accounts:verify_email', kwargs={'token': str(token.token)})
#             )

#             # Render the email content
#             subject = 'Verify Your Email Address'
#             message = render_to_string('accounts/email_verification.html', {
#                 'user': user,
#                 'verification_url': verification_url, 
#                 'expiry_time': '24 hours'
#             })
            
#             # Send verification email
#             send_mail(
#                 subject=subject,
#                 message='',  # Empty message since we're using HTML
#                 html_message=message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[user.email],
#                 fail_silently=False
#             )

#             messages.success(request, 'Verification email has been resent. Please check your inbox.')
#             return render(request, 'accounts/email_sent.html', {'email': user.email})
            
#         except User.DoesNotExist:
#             messages.error(request, 'No account found with this email address.')
    
#     return render(request, 'accounts/resend_verification.html')


def resend_verification_view(request):
    """View to resend verification email"""
    initial = {}
    if 'verification_email' in request.session:
        initial['email'] = request.session['verification_email']

        
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Check session if email not provided
        if not email:
            email = request.session.get('verification_email')
        
        if not email:
            error_msg = 'Email address is required.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'accounts/resend_verification.html')
        
        try:
            user = User.objects.get(email=email)
            
            if user.email_verified:
                msg = 'Email is already verified. You can login now.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': msg})
                messages.info(request, msg)
                return redirect('accounts:login')
                
            # Delete existing tokens
            EmailVerificationToken.objects.filter(user=user).delete()
            
            # Create new token
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + datetime.timedelta(hours=24)
            )
            
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': token.token})
            )

            # Send email
            subject = 'Verify Your Email Address'
            message = render_to_string('accounts/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'expiry_time': '24 hours'
            })
            
            send_mail(
                subject=subject,
                message='',
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )

            # Handle AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                request.session['verification_email'] = user.email
                messages.success(request, 'Verification email has been resent.')
                return redirect('accounts:email_sent')
            
        except User.DoesNotExist:
            error_msg = 'No account found with this email address.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'accounts/resend_verification.html')
    
    # GET request handling
    email = request.session.get('verification_email')
    if email:
        return render(request, 'accounts/email_sent.html', {'email': email})
    return render(request, 'accounts/resend_verification.html')



# @ratelimit(key='ip', rate='5/h', method='POST', block=True)
def login_view(request):
    """View for authenticating users with rate limiting"""
    redirect_uri = request.GET.get('redirect_uri')
    
    # Validate redirect_uri
    allowed_domains = settings.ALLOWED_REDIRECT_DOMAINS
    if redirect_uri:
        domain = urlparse(redirect_uri).netloc.split(':')[0]
        if domain not in allowed_domains:
            logger.error(f"Invalid redirect_uri: {redirect_uri}")
            return HttpResponse("Invalid redirect URI", status=400)
    
    if request.user.is_authenticated:
        if redirect_uri:
            # Generate tokens and send via POST
            serializer = CustomTokenObtainPairSerializer()
            token_data = serializer.get_token(request.user)
            access_token = str(token_data.access_token)
            refresh_token = str(token_data)
            return render(request, 'accounts/token_redirect.html', {
                'redirect_uri': redirect_uri,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_id': request.user.id
            })
        else:
            return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if not user.is_superuser and not user.email_verified:
                logout(request)
                # Store email in session and redirect
                request.session['verification_email'] = user.email
                messages.error(request, 'Email not verified. Please check your email or resend the verification link.')
                return redirect('accounts:email_sent')  
                  
            if redirect_uri:
                # Generate tokens and send via POST
                serializer = CustomTokenObtainPairSerializer()
                token_data = serializer.get_token(user)
                access_token = str(token_data.access_token)
                refresh_token = str(token_data)
                return render(request, 'accounts/token_redirect.html', {
                    'redirect_uri': redirect_uri,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user_id': user.id
                })
            else:
                messages.success(request, 'Login successful!')
                return redirect('accounts:profile')
        else:
            if hasattr(form, 'unverified_email') and form.unverified_email:
                request.session['verification_email'] = form.unverified_email
                messages.error(request, 'Email not verified. Please check your email or resend the verification link.')

                return redirect('accounts:resend_verification')
            
            # messages.error(request, 'Invalid email/username or password.')

    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form, 'redirect_uri': redirect_uri})



class BlacklistRefreshToken(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.debug(f"Refresh token blacklisted: {refresh_token}")
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



def password_reset_email_sent_view(request):
    """View to show after password reset email is sent"""
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:password_reset_request')
        
    return render(request, 'accounts/password_reset_email_sent.html', {'email': email})






from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

@login_required
def logout_view(request):
    """Centralized auth-server logout supporting multiple clients."""
    # 1. Log the user out of Django session
    logout(request)

    # 2. Success message (optional)
    messages.success(request, 'You have been logged out successfully.')

    # 3. Determine where to send them next:
    #    - honor a ?next=... param if it’s on the allow-list
    #    - otherwise fall back to a default client URL
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_CLIENT_HOSTS):
        redirect_to = next_url
    else:
        redirect_to = settings.CLIENT_LOGOUT_URL  # your default
    
    # 4. Attach flag so client knows it came from the auth server
    sep = '&' if '?' in redirect_to else '?'
    client_logout_url = f"{redirect_to}{sep}{urlencode({'from_auth_server': 'true'})}"

    logger.debug(f"Redirecting to client logout: {client_logout_url}")
    return redirect(client_logout_url)






@login_required
def profile_view(request):
    """View for user profile"""
    logger.debug(f"Profile accessed for user: {request.user.id}")
    return render(request, 'accounts/profile/profile.html')
# def login_view(request):
    """Modified login view that returns tokens to client"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            print("Form is valid")
            user = form.get_user()
            login(request, user)  # Traditional session login
            
            # Generate tokens (same as your API does)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Get the client's redirect URL from params
            client_redirect_url = request.GET.get('redirect_uri')
            if not client_redirect_url:
                messages.success(request, 'Login successful!')
                return redirect('accounts:profile')
            
            # Redirect back to client with tokens
            print(f"Redirecting to {client_redirect_url} with tokens")
            print(f"Access Token: {access_token}")
            print(f"Refresh Token: {str(refresh)}")
            messages.success(request, 'Login successful! Redirecting to client application.')
            return redirect(
                f"{client_redirect_url}?"
                f"access_token={access_token}&"
                f"refresh_token={str(refresh)}&"
                f"user_id={user.id}"
            )
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


# @ratelimit(key='ip', rate='2/h', method='POST', block=True)
def password_reset_request(request):
    """View to request a password reset"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate unique token
                token = str(uuid.uuid4())
                expires_at = timezone.now() + datetime.timedelta(hours=1)
                
                # Save token to database
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Build reset URL
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', args=[token])
                )
                
                # Send email
                subject = 'Password Reset Request'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'expiry_time': '1 hours'
                })
                
                send_mail(subject, message, None, [user.email])
                
                messages.success(
                    request, 
                    'Password reset link has been sent to your email. Please check your inbox.'
                )
                # return redirect('accounts:login')
                return render(request, 'accounts/password_reset_email_sent.html', {'email': email})
                
            except User.DoesNotExist:
                # We don't want to reveal that an email doesn't exist in our system
                messages.error(
                    request, 
                    'Your email does not exists in our system, you will not receive a password reset link.'
                )
                return redirect('accounts:password_reset_request')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'accounts/password_reset_form.html', {'form': form})


def password_reset_confirm(request, token):
    """View to confirm password reset and set new password"""
    # Get the token
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        # Check if token is valid
        if not reset_token.is_valid():
            messages.error(request, 'The password reset link has expired or is invalid.')
            return redirect('accounts:password_reset_request')
            
        user = reset_token.user
        
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                
                # Mark token as used
                reset_token.used = True
                reset_token.save()
                
                messages.success(request, 'Your password has been successfully reset.')
                return redirect('accounts:login')
        else:
            form = CustomSetPasswordForm(user)
            
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'The password reset link is invalid.')
        return redirect('accounts:password_reset_request')







@login_required
def profile_update_view(request):

   user = request.user



   # ――― determine which form was posted ―――
   if request.method == "POST":
       if "profile_submit" in request.POST:
           # username / email / full-name
           profile_form = ProfileUpdateForm(request.POST, instance=user)
           avatar_form  = AvatarUpdateForm(instance=user)  # blank copy
           if profile_form.is_valid():
               profile_form.save()
               messages.success(request, "Profile updated successfully!")
               return redirect("accounts:profile")


       elif "avatar_submit" in request.POST:
           # avatar only
           avatar_form  = AvatarUpdateForm(request.POST, instance=user)
           profile_form = ProfileUpdateForm(instance=user)  # blank copy
           if avatar_form.is_valid():
               avatar_form.save()
               messages.success(request, "Changes saved successfully!")
               return redirect("accounts:profile")


   else:   # ── GET ──
       profile_form = ProfileUpdateForm(instance=user)
       avatar_form  = AvatarUpdateForm(instance=user)


   return render(
       request,
       "accounts/profile/profile_update.html",
       {
           "profile_form": profile_form,
           "avatar_form":  avatar_form,
       },
   )



@login_required
def delete_account_view(request):
    try:
        # Log request headers for debugging
        print("Request headers:", request.headers)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if request.method == 'POST':
            form = DeleteAccountForm(request.POST, user=request.user)
            if form.is_valid():
                user = request.user
                logout(request)
                user.delete()
                messages.success(request, 'Your account has been deleted successfully.')
                return redirect('accounts:login')
            else:
                # Always use partial template for AJAX, full template for non-AJAX
                template = 'accounts/profile/delete_account_form.html' if is_ajax else 'accounts/profile/delete_account.html'
                return render(request, template, {'form': form})
        else:
            form = DeleteAccountForm(user=request.user)
            template = 'accounts/profile/delete_account_form.html' if is_ajax else 'accounts/profile/delete_account.html'
            return render(request, template, {'form': form})
    except Exception as e:
        print(f"Error in delete_account_view: {str(e)}")
        raise

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Keep user logged in
            messages.success(request, 'Password updated successfully!')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'accounts/profile/password_change.html', {'form': form})


























from django.core.mail import send_mail, get_connection

try:
    connection = get_connection()
    connection.open()
    print("✅ SMTP connection established.")
    connection.close()
except Exception as e:
    print("❌ SMTP connection failed:", e)


def terms_view(request):
 
    return render(request, 'accounts/terms.html')


