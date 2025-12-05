from rest_framework import serializers
from .models import BlogPostModel, BlogCategoryModel, BlogTagModel, BlogCommentModel


class BlogCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BlogCategoryModel
        fields = ['id', 'title', 'slug', 'post_count']


class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTagModel
        fields = ['id', 'title']


class BlogPostListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.title', read_only=True)
    featured_image = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPostModel
        fields = ['id', 'title', 'slug', 'category_name', 'excerpt', 'featured_image', 'view_count', 'created_at']
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
        return None


class BlogPostDetailSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPostModel
        fields = ['id', 'title', 'slug', 'category', 'tags', 'excerpt', 'featured_image',
                  'content', 'view_count', 'comments', 'created_at', 'updated_at']
    
    def get_featured_image(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
        return None
    
    def get_comments(self, obj):
        comments = obj.comments.filter(status='active')
        return BlogCommentSerializer(comments, many=True).data


class BlogCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCommentModel
        fields = ['id', 'full_name', 'comment', 'created_at']


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCommentModel
        fields = ['post', 'full_name', 'email', 'comment']