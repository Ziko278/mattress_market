from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from .models import (
    BrandModel, CategoryModel, ProductModel,
    ProductVariantModel, ReviewModel
)
from .serializers import (
    BrandSerializer, CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ReviewCreateSerializer, ReviewSerializer
)


class StandardResultsPagination(PageNumberPagination):
    """
    Custom pagination - 20 products per page
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BrandListView(APIView):
    """
    Get all brands with product count
    """
    def get(self, request):
        brands = BrandModel.objects.all()
        serializer = BrandSerializer(brands, many=True, context={'request': request})  # Add context
        return Response(serializer.data)


class CategoryListView(APIView):
    """
    Get all categories with product count
    """
    def get(self, request):
        categories = CategoryModel.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})  # Add context
        return Response(serializer.data)



class ProductListView(APIView):
    """
    Get products with filters, search, and sorting

    Query params:
    - search: Search in product name, brand, description
    - brand: Filter by brand ID
    - category: Filter by category ID
    - min_price: Minimum price
    - max_price: Maximum price
    - is_featured: true/false
    - is_new: true/false
    - sort: price_asc, price_desc, newest, popular
    """
    pagination_class = StandardResultsPagination

    def get(self, request):
        # Start with all products
        products = ProductModel.objects.all()

        # Search functionality - search in name, brand, description
        search_query = request.query_params.get('search', None)
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(brand__name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__title__icontains=search_query)
            )

        # Filter by brand
        brand_id = request.query_params.get('brand', None)
        if brand_id:
            products = products.filter(brand_id=brand_id)

        # Filter by category
        category_id = request.query_params.get('category', None)
        if category_id:
            products = products.filter(category_id=category_id)

        # Filter by price range (check variants)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        if min_price:
            products = products.filter(variants__price__gte=min_price).distinct()
        if max_price:
            products = products.filter(variants__price__lte=max_price).distinct()

        # Filter featured products
        is_featured = request.query_params.get('is_featured', None)
        if is_featured == 'true':
            products = products.filter(is_featured=True)

        # Filter new arrivals
        is_new = request.query_params.get('is_new', None)
        if is_new == 'true':
            products = products.filter(is_new_arrival=True)

        # Sorting
        sort_by = request.query_params.get('sort', 'newest')
        if sort_by == 'price_asc':
            # Sort by minimum variant price (ascending)
            products = products.order_by('variants__price')
        elif sort_by == 'price_desc':
            # Sort by maximum variant price (descending)
            products = products.order_by('-variants__price')
        elif sort_by == 'popular':
            # Sort by view count
            products = products.order_by('-view_count')
        else:  # newest (default)
            products = products.order_by('-created_at')

        # Remove duplicates (can occur with variant filtering)
        products = products.distinct()

        # Pagination
        paginator = self.pagination_class()
        paginated_products = paginator.paginate_queryset(products, request)
        
        serializer = ProductListSerializer(paginated_products, many=True, context={'request': request})  # Add context
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    def get(self, request, slug):
        try:
            product = ProductModel.objects.get(slug=slug)
            
            # Increment view count
            product.view_count += 1
            product.save()
            
            serializer = ProductDetailSerializer(product, context={'request': request})  # Add context
            return Response(serializer.data)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)



class FeaturedProductsView(APIView):
    def get(self, request):
        products = ProductModel.objects.filter(is_featured=True)[:8]
        serializer = ProductListSerializer(products, many=True, context={'request': request})  # Add context
        return Response(serializer.data)


class NewArrivalsView(APIView):
    def get(self, request):
        products = ProductModel.objects.filter(is_new_arrival=True).order_by('-created_at')[:8]
        serializer = ProductListSerializer(products, many=True, context={'request': request})  # Add context
        return Response(serializer.data)


class RelatedProductsView(APIView):
    def get(self, request, product_id):
        try:
            product = ProductModel.objects.get(id=product_id)
            related = ProductModel.objects.filter(category=product.category).exclude(id=product_id)[:4]
            serializer = ProductListSerializer(related, many=True, context={'request': request})  # Add context
            return Response(serializer.data)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


class ProductReviewCreateView(APIView):
    """
    Create a product review (requires moderation - is_approved=False by default)
    """

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Review submitted for approval"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
