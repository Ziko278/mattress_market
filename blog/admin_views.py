from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import BlogPostModel, BlogCategoryModel, BlogTagModel, BlogCommentModel
from .serializers import (
    BlogPostDetailSerializer, BlogCategorySerializer,
    BlogTagSerializer, BlogCommentSerializer
)


# ==================== BLOG CATEGORY MANAGEMENT ====================

class AdminBlogCategoryListCreateView(APIView):
    """
    Admin: List all blog categories or create new category
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        categories = BlogCategoryModel.objects.all()
        serializer = BlogCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BlogCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBlogCategoryDetailView(APIView):
    """
    Admin: Update or delete blog category
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            category = BlogCategoryModel.objects.get(pk=pk)
            serializer = BlogCategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BlogCategoryModel.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            category = BlogCategoryModel.objects.get(pk=pk)
            category.delete()
            return Response({"message": "Category deleted"}, status=status.HTTP_200_OK)
        except BlogCategoryModel.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== BLOG TAG MANAGEMENT ====================

class AdminBlogTagListCreateView(APIView):
    """
    Admin: List all tags or create new tag
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        tags = BlogTagModel.objects.all()
        serializer = BlogTagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BlogTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBlogTagDetailView(APIView):
    """
    Admin: Update or delete tag
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            tag = BlogTagModel.objects.get(pk=pk)
            serializer = BlogTagSerializer(tag, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BlogTagModel.DoesNotExist:
            return Response({"error": "Tag not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            tag = BlogTagModel.objects.get(pk=pk)
            tag.delete()
            return Response({"message": "Tag deleted"}, status=status.HTTP_200_OK)
        except BlogTagModel.DoesNotExist:
            return Response({"error": "Tag not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== BLOG POST MANAGEMENT ====================

class AdminBlogPostListCreateView(APIView):
    """
    Admin: List all blog posts or create new post
    Includes both active and inactive posts
    Search: ?search=keyword
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        posts = BlogPostModel.objects.all().order_by('-created_at')

        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            posts = posts.filter(title__icontains=search_query)

        serializer = BlogPostDetailSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BlogPostDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBlogPostDetailView(APIView):
    """
    Admin: Get, update, or delete a blog post
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            post = BlogPostModel.objects.get(pk=pk)
            serializer = BlogPostDetailSerializer(post)
            return Response(serializer.data)
        except BlogPostModel.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            post = BlogPostModel.objects.get(pk=pk)
            serializer = BlogPostDetailSerializer(post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BlogPostModel.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            post = BlogPostModel.objects.get(pk=pk)
            post.delete()
            return Response({"message": "Blog post deleted"}, status=status.HTTP_200_OK)
        except BlogPostModel.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== COMMENT MANAGEMENT ====================

class AdminCommentListView(APIView):
    """
    Admin: Get all comments with filter
    Filter: ?status=active or ?status=inactive
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        comments = BlogCommentModel.objects.all().order_by('-created_at')

        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            comments = comments.filter(status=status_filter)

        serializer = BlogCommentSerializer(comments, many=True)
        return Response(serializer.data)


class AdminCommentApproveView(APIView):
    """
    Admin: Approve a comment (set status to active)
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            comment = BlogCommentModel.objects.get(pk=pk)
            comment.status = 'active'
            comment.save()
            return Response({"message": "Comment approved"})
        except BlogCommentModel.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminCommentDeleteView(APIView):
    """
    Admin: Delete a comment
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            comment = BlogCommentModel.objects.get(pk=pk)
            comment.delete()
            return Response({"message": "Comment deleted"}, status=status.HTTP_200_OK)
        except BlogCommentModel.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        