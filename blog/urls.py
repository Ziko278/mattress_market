from django.urls import path
from .views import (
    BlogCategoryListView, BlogPostListView, BlogPostDetailView,
    BlogCommentCreateView, RecentBlogPostsView
)
from .admin_views import (
    AdminBlogCategoryListCreateView, AdminBlogCategoryDetailView,
    AdminBlogTagListCreateView, AdminBlogTagDetailView,
    AdminBlogPostListCreateView, AdminBlogPostDetailView,
    AdminCommentListView, AdminCommentApproveView, AdminCommentDeleteView
)

urlpatterns = [
    # Public endpoints
    path('categories/', BlogCategoryListView.as_view(), name='blog-categories'),
    path('posts/', BlogPostListView.as_view(), name='blog-posts'),
    path('posts/<slug:slug>/', BlogPostDetailView.as_view(), name='blog-post-detail'),
    path('comments/create/', BlogCommentCreateView.as_view(), name='blog-comment-create'),
    path('recent/', RecentBlogPostsView.as_view(), name='recent-posts'),

    # Admin endpoints - Categories
    path('admin/categories/', AdminBlogCategoryListCreateView.as_view(), name='admin-blog-categories'),
    path('admin/categories/<int:pk>/', AdminBlogCategoryDetailView.as_view(), name='admin-blog-category-detail'),

    # Admin endpoints - Tags
    path('admin/tags/', AdminBlogTagListCreateView.as_view(), name='admin-blog-tags'),
    path('admin/tags/<int:pk>/', AdminBlogTagDetailView.as_view(), name='admin-blog-tag-detail'),

    # Admin endpoints - Posts
    path('admin/posts/', AdminBlogPostListCreateView.as_view(), name='admin-blog-posts'),
    path('admin/posts/<int:pk>/', AdminBlogPostDetailView.as_view(), name='admin-blog-post-detail'),

    # Admin endpoints - Comments
    path('admin/comments/', AdminCommentListView.as_view(), name='admin-comments'),
    path('admin/comments/<int:pk>/approve/', AdminCommentApproveView.as_view(), name='admin-comment-approve'),
    path('admin/comments/<int:pk>/', AdminCommentDeleteView.as_view(), name='admin-comment-delete'),
]