from rest_framework import serializers
from .models import (
    BrandModel, CategoryModel, ProductModel, ProductVariantModel,
    ProductImageModel, ProductSizeModel, ProductWeightModel, ReviewModel
)


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    logo = serializers.SerializerMethodField()
    
    class Meta:
        model = BrandModel
        fields = ['id', 'name', 'logo', 'description', 'product_count']
    
    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoryModel
        fields = ['id', 'title', 'description', 'image', 'product_count']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSizeModel
        fields = ['id', 'size']


class ProductWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWeightModel
        fields = ['id', 'weight']


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImageModel
        fields = ['id', 'image', 'is_main', 'order']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class ProductVariantSerializer(serializers.ModelSerializer):
    size_name = serializers.CharField(source='size.size', read_only=True)
    
    class Meta:
        model = ProductVariantModel
        fields = ['id', 'slug', 'size', 'size_name', 'thickness', 'price']


class ProductListSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.title', read_only=True)
    main_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductModel
        fields = ['id', 'name', 'slug', 'brand_name', 'category_name', 'main_image', 'price_range', 'is_featured', 'is_new_arrival']
    
    def get_main_image(self, obj):
        image = obj.main_image()
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
        return None
    
    def get_price_range(self, obj):
        return obj.price_range()


class ProductDetailSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    weight = ProductWeightSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductModel
        fields = ['id', 'name', 'slug', 'brand', 'category', 'description', 'weight', 
                  'images', 'variants', 'reviews', 'average_rating', 'view_count', 
                  'is_featured', 'is_new_arrival', 'created_at']
    
    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        return ReviewSerializer(reviews, many=True, context=self.context).data
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return sum([r.rating for r in reviews]) / reviews.count()
        return 0


class ReviewSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewModel
        fields = ['id', 'customer_name', 'rating', 'comment', 'image', 'created_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
        
        
class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewModel
        fields = ['product', 'customer_name', 'email', 'rating', 'comment', 'image']