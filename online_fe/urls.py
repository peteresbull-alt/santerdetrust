"""
URL configuration for online_fe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from app import views as app_views


admin.site.site_header = "Santerde Trust Administration"
admin.site.site_title = "Santerde Trust Admin Portal"
admin.site.index_title = "Welcome to Santerde Trust Admin Portal"



urlpatterns = [
    # Shows Django's 'Forgotten your password?' link on the admin login page
    path('admin/password-reset/', app_views.PasswordResetRequestView.as_view(), name='admin_password_reset'),
    # Staff sign in through the site login so two-factor authentication applies to the admin too
    path('admin/login/', app_views.admin_login_redirect, name='admin_login_2fa'),
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



