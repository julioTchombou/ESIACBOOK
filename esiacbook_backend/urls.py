"""
URL configuration for esiackbook_backend project.

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
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, StudentProfileViewSet, ProfessorProfileViewSet
from django.conf import settings # Pour les fichiers médias
from django.conf.urls.static import static # Pour les fichiers médias



router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'student-profiles', StudentProfileViewSet, basename='student-profile')
router.register(r'professor-profiles', ProfessorProfileViewSet, basename='professor-profile')
# 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/',include('users.urls')),
    path('api/', include(router.urls)), # Incluez les routes des ViewSets
    path('api-auth/', include('rest_framework.urls')),
    path('api/password-reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/resources/', include('ressources.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
       
   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


