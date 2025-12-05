from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import BlogPostModel, BlogCategoryModel, BlogCommentModel
from .serializers import (
    BlogPostListSerializer, BlogPostDetailSerializer,
    BlogCategorySerializer, BlogCommentCreateSerializer
)


class BlogPagination(PageNumberPagination):
    """
    Pagination for blog posts - 12 per page
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class BlogCategoryListView(APIView):
    def get(self, request):
        categories = BlogCategoryModel.objects.all()
        serializer = BlogCategorySerializer(categories, many=True, context={'request': request})  # Add context
        return Response(serializer.data)


class BlogPostListView(APIView):
    """
    Get all blog posts with filters and search

    Query params:
    - search: Search in title, excerpt, content
    - category: Filter by category ID
    - tag: Filter by tag ID
    """
    pagination_class = BlogPagination

    def get(self, request):
        # Only active posts
        posts = BlogPostModel.objects.filter(status='active')

        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            posts = posts.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )

        # Filter by category
        category_id = request.query_params.get('category', None)
        if category_id:
            posts = posts.filter(category_id=category_id)

        # Filter by tag
        tag_id = request.query_params.get('tag', None)
        if tag_id:
            posts = posts.filter(tags__id=tag_id)

        # Remove duplicates and order by newest
        posts = posts.distinct().order_by('-created_at')

        # Pagination
        paginator = self.pagination_class()
        paginated_posts = paginator.paginate_queryset(posts, request)
        
        serializer = BlogPostListSerializer(paginated_posts, many=True, context={'request': request})  # Add context
        return paginator.get_paginated_response(serializer.data)


class BlogPostDetailView(APIView):
    def get(self, request, slug):
        try:
            post = BlogPostModel.objects.get(slug=slug, status='active')
            
            post.view_count += 1
            post.save()
            
            serializer = BlogPostDetailSerializer(post, context={'request': request})  # Add context
            return Response(serializer.data)
        except BlogPostModel.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)



class BlogCommentCreateView(APIView):
    """
    Create a blog comment (requires moderation - status='inactive' by default)
    """

    def post(self, request):
        serializer = BlogCommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Comment submitted for approval"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecentBlogPostsView(APIView):
    def get(self, request):
        posts = BlogPostModel.objects.filter(status='active').order_by('-created_at')[:5]
        serializer = BlogPostListSerializer(posts, many=True, context={'request': request})  # Add context
        return Response(serializer.data)
