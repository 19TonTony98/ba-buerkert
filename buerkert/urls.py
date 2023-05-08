"""
URL configuration for buerkert project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", include("buerkert_app.urls")),
    path('admin/', admin.site.urls),
]

# Add URL maps to redirect the base URL to the application
urlpatterns += [
    path('favicon.ico',
         RedirectView.as_view(url=staticfiles_storage.url('buerkert_app/img/hswt-logo.ico'), permanent=True)),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
]