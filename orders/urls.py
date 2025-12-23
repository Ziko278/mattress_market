from django.urls import path
from .views import (
    OrderCreateView, OrderTrackView, UserOrderListView, OrderDetailView,
    WishlistView, WishlistAddView, WishlistRemoveView,
    AddressListView, AddressCreateView, AddressUpdateView, AddressDeleteView,
    PaymentCallbackView
)
from .admin_views import (
    AdminOrderListView, AdminOrderDetailView, AdminOrderUpdateStatusView,
    AdminOrderDeleteView, AdminDashboardStatsView
)

urlpatterns = [
    # Public endpoints
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('payment/callback/', PaymentCallbackView.as_view(), name='payment-callback'),
    path('track/', OrderTrackView.as_view(), name='order-track'),
    path('my-orders/', UserOrderListView.as_view(), name='user-orders'),
    path('<str:order_id>/', OrderDetailView.as_view(), name='order-detail'),

    # Wishlist
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/', WishlistAddView.as_view(), name='wishlist-add'),
    path('wishlist/<int:wishlist_id>/', WishlistRemoveView.as_view(), name='wishlist-remove'),

    # Addresses
    path('addresses/', AddressListView.as_view(), name='addresses'),
    path('addresses/create/', AddressCreateView.as_view(), name='address-create'),
    path('addresses/<int:address_id>/', AddressUpdateView.as_view(), name='address-update'),
    path('addresses/<int:address_id>/delete/', AddressDeleteView.as_view(), name='address-delete'),

    # Admin endpoints
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:pk>/status/', AdminOrderUpdateStatusView.as_view(), name='admin-order-status'),
    path('admin/orders/<int:pk>/delete/', AdminOrderDeleteView.as_view(), name='admin-order-delete'),
    path('admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin-dashboard'),
]