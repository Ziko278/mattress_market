from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, Max, Min, Count, Case, When, IntegerField, Value
from django.db.models.functions import Concat
import hashlib
from django.db.models import Q, Avg

from .models import (
    BrandModel, CategoryModel, ProductModel,
    ProductVariantModel, ReviewModel, ProductWeightModel
)
from .serializers import (
    BrandSerializer, CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ReviewCreateSerializer, ReviewSerializer, ProductWeightSerializer
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


class WeightListView(APIView):
    """
    Public endpoint: List all available product weights for buyer's guide
    """
    def get(self, request):
        weights = ProductWeightModel.objects.all().order_by('id')
        serializer = ProductWeightSerializer(weights, many=True)
        return Response(serializer.data)
    

class ProductListView(APIView):
    """
    Get products with filters, search, and sorting with fair distribution
    """
    pagination_class = StandardResultsPagination

    def get(self, request):
        # Clear any default ordering
        products = ProductModel.objects.all().order_by()
        
        # DEBUG: Print total products
        print(f"Total products before filters: {products.count()}")
        
        # Session seed for shuffle
        if not request.session.session_key:
            request.session.create()
        
        session_seed = request.session.get('product_shuffle_seed')
        if not session_seed:
            session_seed = str(random.randint(100000, 999999))
            request.session['product_shuffle_seed'] = session_seed
            request.session.modified = True
        
        print(f"Session seed: {session_seed}")
        
        # Search functionality
        search_query = request.query_params.get('search', None)
        use_relevance_order = False
        
        if search_query:
            search_words = [word.strip() for word in search_query.strip().split() if word.strip()]
            
            q_objects = Q()
            for word in search_words:
                q_objects |= (
                    Q(name__icontains=word) |
                    Q(brand__name__icontains=word) |
                    Q(description__icontains=word) |
                    Q(category__title__icontains=word)
                )
            
            products = products.filter(q_objects)
            
            # Relevance score
            relevance_cases = []
            for word in search_words:
                relevance_cases.extend([
                    When(Q(name__icontains=word), then=Value(1)),
                    When(Q(brand__name__icontains=word), then=Value(1)),
                    When(Q(description__icontains=word), then=Value(1)),
                    When(Q(category__title__icontains=word), then=Value(1)),
                ])
            
            products = products.annotate(
                relevance=Case(
                    *relevance_cases,
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            use_relevance_order = True

        # Filter by weight
        weight_id = request.query_params.get('weight', None)
        if weight_id:
            products = products.filter(weight_id=weight_id)

        # Filter by brand
        brand_id = request.query_params.get('brand', None)
        if brand_id:
            products = products.filter(brand_id=brand_id)

        # Filter by category
        category_id = request.query_params.get('category', None)
        if category_id:
            products = products.filter(category_id=category_id)

        # Filter by price range
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        if min_price or max_price:
            products = products.annotate(
                min_variant_price=Min('variants__price'),
                max_variant_price=Max('variants__price')
            )
            if min_price:
                products = products.filter(min_variant_price__gte=min_price)
            if max_price:
                products = products.filter(max_variant_price__lte=max_price)

        # Filter featured products
        is_featured = request.query_params.get('is_featured', None)
        if is_featured == 'true':
            products = products.filter(is_featured=True)

        # Filter new arrivals
        is_new = request.query_params.get('is_new', None)
        if is_new == 'true':
            products = products.filter(is_new_arrival=True)

        # DEBUG: Print after filters
        print(f"Products after filters: {products.count()}")

        # Get sort parameter
        sort_by = request.query_params.get('sort', 'newest')
        
        # Apply ordering
        if use_relevance_order:
            # Search results by relevance
            products = products.order_by('-relevance', '-created_at')
        elif sort_by == 'price_asc':
            products = products.annotate(
                min_price=Min('variants__price')
            ).order_by('min_price')
        elif sort_by == 'price_desc':
            products = products.annotate(
                max_price=Max('variants__price')
            ).order_by('-max_price')
        elif sort_by == 'popular':
            products = products.order_by('-view_count')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'shuffle':
            # SIMPLE SHUFFLE METHOD - Get all IDs and shuffle them
            product_ids = list(products.values_list('id', flat=True))
            
            # Seed random with session seed for consistency
            random.seed(session_seed)
            random.shuffle(product_ids)
            
            # Create ordering based on shuffled IDs
            id_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(product_ids)])
            products = products.annotate(order=id_order).order_by('order')
            
            print(f"Shuffled order (first 10 IDs): {product_ids[:10]}")

        # Remove duplicates
        products = products.distinct()

        # DEBUG: Print final ordering
        final_ids = list(products.values_list('id', flat=True)[:10])
        print(f"Final product IDs (first 10): {final_ids}")

        # Pagination
        paginator = self.pagination_class()
        paginated_products = paginator.paginate_queryset(products, request)
        
        serializer = ProductListSerializer(
            paginated_products, 
            many=True, 
            context={'request': request}
        )
        
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
