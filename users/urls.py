from django.urls import path
from .views import (
    UserRegisterView, UserLoginView, UserLogoutView,
    UserProfileView, UserProfileUpdateView, PasswordChangeView
)
from .admin_views import (
    AdminUserListView, AdminUserDetailView,
    AdminUserToggleActiveView, AdminUserDeleteView
)

urlpatterns = [
    # Public endpoints
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),

    # Admin endpoints
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:pk>/toggle/', AdminUserToggleActiveView.as_view(), name='admin-user-toggle'),
    path('admin/users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='admin-user-delete'),
]