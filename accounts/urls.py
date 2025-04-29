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
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # API endpoints
    path('api/register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('api/token/', api_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', api_views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/user/', api_views.UserAPIView.as_view(), name='api_user'),
]