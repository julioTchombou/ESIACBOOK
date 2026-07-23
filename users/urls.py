from django.urls import path
from .views import (
    RegisterUserView, UserProfileView, UserListView,ChangePasswordView,AdminUserUpdateView,UserDetailView,MyTokenObtainPairView,
    UserMeView, ProfessorListView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('usersList/', UserListView.as_view(), name='user-list'),
    path('login/',MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('token/refresh/',TokenRefreshView.as_view(), name="token_refresh"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('update/<int:pk>/', AdminUserUpdateView.as_view(), name='admin-user-update'),
    path('delete/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('professors/', ProfessorListView.as_view(), name='professor-list'),
]