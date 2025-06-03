from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import api_views

app_name = 'accounts'

urlpatterns = [
    # Web views
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('terms/', views.terms_view, name='terms'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
   
    # Email verification
    path('email-sent/', views.email_sent_view, name='email_sent'),
    path('verify-email/<uuid:token>/', views.verify_email_view, name='verify_email'),
    path('verify-email-change/<uuid:token>/', views.verify_email_change, name='verify_email_change'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
    
    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/email-sent/', views.password_reset_email_sent_view, name='password_reset_email_sent'),
    path('password-reset/confirm/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-change/', views.password_change_view, name='password_change'),
    
    # API endpoints
    path('api/avatar/image/', api_views.AvatarImageView.as_view(), name='user-avatar-image'),
    path('api/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('api/token/', api_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
   # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/user/', api_views.UserAPIView.as_view(), name='api_user'),
    path('api/token/refresh/', api_views.CustomTokenRefreshView.as_view(), name='token_refresh'),
]