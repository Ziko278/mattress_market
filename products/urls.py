from django.urls import path
from .views import (
    BrandListView, CategoryListView, ProductListView, ProductDetailView,
    FeaturedProductsView, NewArrivalsView, RelatedProductsView, ProductReviewCreateView,
    WeightListView
)
from .admin_views import (
    AdminBrandListCreateView, AdminBrandDetailView,
    AdminCategoryListCreateView, AdminCategoryDetailView,
    AdminSizeListCreateView, AdminWeightListCreateView,
    AdminProductListCreateView, AdminProductDetailView,
    AdminVariantCreateView, AdminVariantDetailView,
    AdminProductImageUploadView, AdminProductImageDeleteView,
    AdminReviewListView, AdminReviewApproveView, AdminReviewDeleteView
)

urlpatterns = [
    # Public endpoints
    path('brands/', BrandListView.as_view(), name='brands'),
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('weights/', WeightListView.as_view(), name='weights'),
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
    path('new-arrivals/', NewArrivalsView.as_view(), name='new-arrivals'),
    
    path('', ProductListView.as_view(), name='products'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    
    path('<int:product_id>/related/', RelatedProductsView.as_view(), name='related-products'),
    path('reviews/create/', ProductReviewCreateView.as_view(), name='review-create'),
    
    

    # Admin endpoints - Brands
    path('admin/brands/', AdminBrandListCreateView.as_view(), name='admin-brands'),
    path('admin/brands/<int:pk>/', AdminBrandDetailView.as_view(), name='admin-brand-detail'),

    # Admin endpoints - Categories
    path('admin/categories/', AdminCategoryListCreateView.as_view(), name='admin-categories'),
    path('admin/categories/<int:pk>/', AdminCategoryDetailView.as_view(), name='admin-category-detail'),

    # Admin endpoints - Sizes & Weights
    path('admin/sizes/', AdminSizeListCreateView.as_view(), name='admin-sizes'),
    path('admin/weights/', AdminWeightListCreateView.as_view(), name='admin-weights'),

    # Admin endpoints - Products
    path('admin/products/', AdminProductListCreateView.as_view(), name='admin-products'),
    path('admin/products/<int:pk>/', AdminProductDetailView.as_view(), name='admin-product-detail'),

    # Admin endpoints - Variants
    path('admin/variants/', AdminVariantCreateView.as_view(), name='admin-variant-create'),
    path('admin/variants/<int:pk>/', AdminVariantDetailView.as_view(), name='admin-variant-detail'),

    # Admin endpoints - Images
    path('admin/images/', AdminProductImageUploadView.as_view(), name='admin-image-upload'),
    path('admin/images/<int:pk>/', AdminProductImageDeleteView.as_view(), name='admin-image-delete'),

    # Admin endpoints - Reviews
    path('admin/reviews/', AdminReviewListView.as_view(), name='admin-reviews'),
    path('admin/reviews/<int:pk>/approve/', AdminReviewApproveView.as_view(), name='admin-review-approve'),
    path('admin/reviews/<int:pk>/', AdminReviewDeleteView.as_view(), name='admin-review-delete'),
]