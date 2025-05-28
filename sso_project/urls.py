"""
URL Configuration for sso_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
# from accounts.views import trigger_400, trigger_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # path('trigger-400/', trigger_400, name='trigger_400'),
    # path('trigger-500/', trigger_500, name='trigger_500'),

]











# ---------------------------------------------
# Custom Error Handlers for Django Application
# Supports 400, 403, 404, and 500 error pages
# ---------------------------------------------

from django.conf.urls import handler400, handler403, handler404, handler500
from django.shortcuts import render

# 400 - Bad Request
def custom_400_view(request, exception):
    return render(request, 'errors/400.html', status=400)

# 403 - Forbidden
def custom_403_view(request, exception):
    return render(request, 'errors/403.html', status=403)

# 404 - Not Found
def custom_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)

# 500 - Internal Server Error
def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)

# Assigning the custom handlers
handler400 = custom_400_view
handler403 = custom_403_view
handler404 = custom_404_view
handler500 = custom_500_view
