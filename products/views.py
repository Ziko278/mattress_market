from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, Max, Min, Count, Case, When, IntegerField, Value
from django.db.models.functions import Concat
import hashlib
import random
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
    Get products with filters, intelligent search, and session-consistent shuffling.
    """
    pagination_class = StandardResultsPagination

    # Words to ignore if the search query contains other distinct words
    STOP_WORDS = {
        'pillow', 'pillows', 'mattress', 'mattresses', 'foam', 'foams',
        'vitafoam', 'mouka', 'moukafoam', 'winco', 'wincofoam', 'bed', 'bedding'
    }

    def get(self, request):
        products = ProductModel.objects.all()

        # ---------------------------------------------------------
        # 1. HANDLE SEARCH (Intelligent Filtering)
        # ---------------------------------------------------------
        search_query = request.query_params.get('search', '').strip()
        
        if search_query:
            # Split query into words
            raw_words = [w.lower() for w in search_query.split() if w.strip()]
            
            # Filter Logic: 
            # If we have more than 1 word, try to remove STOP_WORDS.
            # Example 1: "Vita Helix Mattress" -> becomes ["vita", "helix"]
            # Example 2: "Mattress" -> remains ["mattress"] (because it's the only word)
            if len(raw_words) > 1:
                filtered_words = [w for w in raw_words if w not in self.STOP_WORDS]
                # Fallback: If removing stop words leaves us empty (e.g. search was "mouka foam"), 
                # put them back so we don't search for nothing.
                search_words = filtered_words if filtered_words else raw_words
            else:
                search_words = raw_words

            # Build Query: Use AND logic (must contain Word A AND Word B)
            # This fixes the "Orthopedic Mattress" issue.
            final_query = Q()
            for word in search_words:
                word_query = (
                    Q(name__icontains=word) |
                    Q(brand__name__icontains=word) |
                    Q(description__icontains=word) |
                    Q(category__title__icontains=word)
                )
                # Combine with AND (&) instead of OR (|)
                final_query &= word_query
            
            products = products.filter(final_query)

        # ---------------------------------------------------------
        # 2. STANDARD FILTERS
        # ---------------------------------------------------------
        if request.query_params.get('weight'):
            products = products.filter(weight_id=request.query_params.get('weight'))

        if request.query_params.get('brand'):
            products = products.filter(brand_id=request.query_params.get('brand'))

        if request.query_params.get('category'):
            products = products.filter(category_id=request.query_params.get('category'))

        # Price Range
        min_p = request.query_params.get('min_price')
        max_p = request.query_params.get('max_price')
        if min_p or max_p:
            products = products.annotate(
                real_min_price=Min('variants__price'),
                real_max_price=Max('variants__price')
            )
            if min_p:
                products = products.filter(real_min_price__gte=min_p)
            if max_p:
                products = products.filter(real_max_price__lte=max_p)

        if request.query_params.get('is_featured') == 'true':
            products = products.filter(is_featured=True)

        if request.query_params.get('is_new') == 'true':
            products = products.filter(is_new_arrival=True)

        # ---------------------------------------------------------
        # 3. SORTING & SHUFFLING
        # ---------------------------------------------------------
        sort_by = request.query_params.get('sort', 'shuffle') # Default to shuffle

        # If user is Searching, we usually want relevance or Newest, not random shuffle
        # unless explicitly asked.
        if search_query and sort_by == 'shuffle':
             # Optional: Force 'newest' on search to ensure relevance isn't lost
             # sort_by = 'newest' 
             pass

        if sort_by == 'price_asc':
            products = products.annotate(p_min=Min('variants__price')).order_by('p_min')
        elif sort_by == 'price_desc':
            products = products.annotate(p_max=Max('variants__price')).order_by('-p_max')
        elif sort_by == 'popular':
            products = products.order_by('-view_count')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        
        elif sort_by == 'shuffle':
            # 1. Get or Create Session Seed
            if not request.session.session_key:
                request.session.save() # Force session creation
            
            session_seed = request.session.get('product_shuffle_seed')
            if not session_seed:
                session_seed = random.randint(1, 1000000)
                request.session['product_shuffle_seed'] = session_seed
            
            # 2. Get ALL IDs that match current filters
            # distinct() is crucial here before values_list
            product_ids = list(products.distinct().values_list('id', flat=True))

            # 3. Deterministic Shuffle
            # Using the session seed ensures that for this user, the order 
            # remains exactly the same as they scroll down (paginate).
            random.seed(session_seed)
            random.shuffle(product_ids)

            # 4. Apply Order using Case/When
            # Check if list is empty to avoid SQL errors
            if product_ids:
                preserved_order = Case(
                    *[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)],
                    output_field=IntegerField(),
                )
                products = products.filter(pk__in=product_ids).annotate(
                    random_order=preserved_order
                ).order_by('random_order')
            
        # Ensure distinct results just in case joins created duplicates
        # Note: distinct() must come before ordering in some DBs, but after annotate in Django
        products = products.distinct()

        # ---------------------------------------------------------
        # 4. PAGINATION
        # ---------------------------------------------------------
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
