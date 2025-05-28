"""
URL Configuration for sso_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]












# Code for handling errors # This code handles custom error pages for 404, 403, and 500 errors.
# Custom error handlers

from django.conf.urls import handler404, handler500, handler403
from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_403_view(request, exception):
    return render(request, 'errors/403.html', status=403)

def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)

handler404 = custom_404_view
handler403 = custom_403_view
handler500 = custom_500_view
