import datetime
import uuid
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
    CustomSetPasswordForm
)
from .models import PasswordResetToken, EmailVerificationToken
from .serializers import CustomTokenObtainPairSerializer
import logging
from django.views.decorators.csrf import csrf_exempt


from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited




logger = logging.getLogger(__name__)

User = get_user_model()

# def signup_view(request):
#     """View for user registration"""
#     if request.user.is_authenticated:
#         return redirect('accounts:profile')
        
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             messages.success(request, 'Registration successful! Welcome to our platform.')
#             return redirect('accounts:profile')
#     else:
#         form = CustomUserCreationForm()
    
#     return render(request, 'accounts/signup.html', {'form': form})



@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def signup_view(request):
    """View for user registration with rate limiting"""
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User inactive until email verification
            user.save()
            
            # Create email verification token
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + datetime.timedelta(hours=24)
            )
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', args=[str(token.token)])
            )
            
            # Send verification email
            subject = 'Verify Your Email Address'
            message = render_to_string('accounts/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'expiry_time': '24 hours'
            })
            
            send_mail(subject, message, None, [user.email])
            
            # Store email in session for the email sent page
            request.session['verification_email'] = user.email
            
            messages.success(request, 'Registration successful! Please check your email for verification link.')
            return redirect('accounts:email_sent')
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
            return redirect('accounts:resend_verification')
            
        user = verification_token.user
        user.is_active = True
        user.email_verified = True
        user.save()
        
        # Delete all verification tokens for this user
        EmailVerificationToken.objects.filter(user=user).delete()
        
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('accounts:login')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:resend_verification')



@ratelimit(key='ip', rate='2/h', method='POST', block=True)
def resend_verification_view(request):
    """View to resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            if user.email_verified:
                messages.info(request, 'Email is already verified. You can login now.')
                return redirect('accounts:login')
                
            # Delete any existing tokens
            EmailVerificationToken.objects.filter(user=user).delete()
            
            # Create new token
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + datetime.timedelta(hours=24)
            )
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': str(token.token)})
            )

            # Render the email content
            subject = 'Verify Your Email Address'
            message = render_to_string('accounts/email_verification.html', {
                'user': user,
                'verification_url': verification_url, 
                'expiry_time': '24 hours'
            })
            
            # Send verification email
            send_mail(
                subject=subject,
                message='',  # Empty message since we're using HTML
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )

            messages.success(request, 'Verification email has been resent. Please check your inbox.')
            return render(request, 'accounts/email_sent.html', {'email': user.email})
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/resend_verification.html')





# def login_view(request):
#     """Modified login view that sends tokens to client via POST"""
#     redirect_uri = request.GET.get('redirect_uri')
    
#     # Validate redirect_uri
#     allowed_domains = settings.ALLOWED_REDIRECT_DOMAINS
#     if redirect_uri:
#         domain = urlparse(redirect_uri).netloc.split(':')[0]
#         if domain not in allowed_domains:
#             logger.error(f"Invalid redirect_uri: {redirect_uri}")
#             return HttpResponse("Invalid redirect URI", status=400)
    
#     logger.debug(f"User authenticated: {request.user.is_authenticated}, redirect_uri: {redirect_uri}")
    
#     if request.user.is_authenticated:
#         if redirect_uri:
#             # User is already logged in, generate tokens and send via POST
#             serializer = CustomTokenObtainPairSerializer()
#             token_data = serializer.get_token(request.user)
#             access_token = str(token_data.access_token)
#             refresh_token = str(token_data)
#             logger.debug(f"User already authenticated, rendering POST form to {redirect_uri}")
#             return render(request, 'accounts/token_redirect.html', {
#                 'redirect_uri': redirect_uri,
#                 'access_token': access_token,
#                 'refresh_token': refresh_token,
#                 'user_id': request.user.id
#             })
#         else:
#             logger.debug("User already authenticated, redirecting to profile")
#             return redirect('accounts:profile')
        
#     if request.method == 'POST':
#         form = CustomAuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             logger.debug("Form is valid")
#             user = form.get_user()
#             login(request, user)  # Traditional session login
            
#             # Generate tokens using custom serializer
#             serializer = CustomTokenObtainPairSerializer()
#             token_data = serializer.get_token(user)
#             access_token = str(token_data.access_token)
#             refresh_token = str(token_data)
            
#             if not redirect_uri:
#                 logger.debug("No redirect_uri, redirecting to profile")
#                 messages.success(request, 'Login successful!')
#                 return redirect('accounts:profile')
            
#             # Send tokens via POST
#             logger.debug(f"Rendering POST form to {redirect_uri}")
#             messages.success(request, 'Login successful! Redirecting to client application.')
#             return render(request, 'accounts/token_redirect.html', {
#                 'redirect_uri': redirect_uri,
#                 'access_token': access_token,
#                 'refresh_token': refresh_token,
#                 'user_id': user.id
#             })
#     else:
#         form = CustomAuthenticationForm()
    
#     logger.debug(f"Rendering login page with redirect_uri: {redirect_uri}")
#     return render(request, 'accounts/login.html', {'form': form})





@ratelimit(key='ip', rate='5/h', method='POST', block=True)
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
            
            if not user.email_verified:
                logout(request)
                messages.error(request, 'Email not verified. Please check your email or resend the verification link.')
                return redirect('accounts:resend_verification')
            
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



@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def password_reset_request(request):
    """View to request a password reset with rate limiting"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                if not user.email_verified:
                    messages.error(request, 'Email not verified. Please verify your email first.')
                    return redirect('accounts:password_reset_request')
                
                # Generate unique token
                token = str(uuid.uuid4())
                expires_at = timezone.now() + datetime.timedelta(hours=1)  # 1 hour expiry
                
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
                    'expiry_time': '1 hour'
                })
                
                send_mail(subject, message, None, [user.email])
                
                # Store email in session for the email sent page
                request.session['reset_email'] = user.email
                
                return redirect('accounts:password_reset_email_sent')
                
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'accounts/password_reset_form.html', {'form': form})


def password_reset_email_sent_view(request):
    """View to show after password reset email is sent"""
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:password_reset_request')
        
    return render(request, 'accounts/password_reset_email_sent.html', {'email': email})





@login_required
def logout_view(request):
    """View for user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully from all applications.')
    client_logout_url = f"{settings.CLIENT_LOGOUT_URL}?from_auth_server=true"
    logger.debug(f"Redirecting to client logout: {client_logout_url}")
    return redirect(client_logout_url)

@login_required
def profile_view(request):
    """View for user profile"""
    logger.debug(f"Profile accessed for user: {request.user.id}")
    return render(request, 'accounts/profile.html')
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
# class BlacklistRefreshToken(APIView):
#     def post(self, request):
#         refresh_token = request.data.get('refresh')
#         # Add token to blacklist (implementation specific)
#         # Example using django-rest-framework-simplejwt:
#         from rest_framework_simplejwt.tokens import RefreshToken
#         try:
#             token = RefreshToken(refresh_token)
#             token.blacklist()
#             return Response(status=status.HTTP_205_RESET_CONTENT)
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
# @login_required
# def logout_view(request):
#     """View for user logout"""
#     logout(request)
#     messages.success(request, 'You have been logged out successfully.')
#     return redirect('accounts:login')

# @login_required
# def profile_view(request):
#     """View for user profile"""
#     return render(request, 'accounts/profile.html')

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
                expires_at = timezone.now() + datetime.timedelta(hours=24)
                
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
                    'expiry_time': '24 hours'
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
                
                messages.success(request, 'Your password has been successfully reset. You can now login with your new password.')
                return redirect('accounts:login')
        else:
            form = CustomSetPasswordForm(user)
            
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'The password reset link is invalid.')
        return redirect('accounts:password_reset_request')