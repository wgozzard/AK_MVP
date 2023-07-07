"""krow_bar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('chatbot/', views.chatbot, name='home'),
    path('register/', views.register_view, name='register'),
    path('upload-inventory/', views.upload_inventory, name='upload_inventory'),
    path('upload-preview/', views.upload_preview, name='upload_preview'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('clear-inventory/', views.clear_inventory, name='clear_inventory'),
    #path('delete-inventory/', views.delete_inventory, name='delete_inventory'),
    path('403/', TemplateView.as_view(template_name='403.html'), name='403'),
    path('save-inventory/', views.save_inventory, name='save_inventory'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

