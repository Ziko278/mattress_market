from django.urls import path
from .views import SiteInfoView, SettingsView, SliderListView
from .admin_views import (
    AdminSiteInfoView, AdminSettingsView,
    AdminSliderListCreateView, AdminSliderDetailView, AdminSliderToggleView
)

urlpatterns = [
    # Public endpoints
    path('site-info/', SiteInfoView.as_view(), name='site-info'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('sliders/', SliderListView.as_view(), name='sliders'),

    # Admin endpoints
    path('admin/site-info/', AdminSiteInfoView.as_view(), name='admin-site-info'),
    path('admin/settings/', AdminSettingsView.as_view(), name='admin-settings'),
    path('admin/sliders/', AdminSliderListCreateView.as_view(), name='admin-sliders-list'),
    path('admin/sliders/<int:pk>/', AdminSliderDetailView.as_view(), name='admin-slider-detail'),
    path('admin/sliders/<int:pk>/toggle/', AdminSliderToggleView.as_view(), name='admin-slider-toggle'),
]