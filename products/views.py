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
    pagination_class = StandardResultsPagination # Ensure this is imported

    # Words to ignore to improve search quality
    STOP_WORDS = {
        'pillow', 'pillows', 'mattress', 'mattresses', 'foam', 'foams',
        'vitafoam', 'mouka', 'moukafoam', 'winco', 'wincofoam', 'bed', 'bedding'
    }

    def get(self, request):
        # 1. Start with Base Query
        products = ProductModel.objects.all()

        # ---------------------------------------------------------
        # 2. INTELLIGENT SEARCH
        # ---------------------------------------------------------
        search_query = request.query_params.get('search', '').strip()
        is_searching = bool(search_query)
        
        if is_searching:
            raw_words = [w.lower() for w in search_query.split() if w.strip()]
            
            # Remove stop words ONLY if there are other specific words
            if len(raw_words) > 1:
                filtered_words = [w for w in raw_words if w not in self.STOP_WORDS]
                search_words = filtered_words if filtered_words else raw_words
            else:
                search_words = raw_words

            # Use AND logic: Product must match ALL remaining words
            final_query = Q()
            for word in search_words:
                final_query &= (
                    Q(name__icontains=word) |
                    Q(brand__name__icontains=word) |
                    Q(description__icontains=word) |
                    Q(category__title__icontains=word)
                )
            products = products.filter(final_query)

        # ---------------------------------------------------------
        # 3. STANDARD FILTERS
        # ---------------------------------------------------------
        if request.query_params.get('weight'):
            products = products.filter(weight_id=request.query_params.get('weight'))
        if request.query_params.get('brand'):
            products = products.filter(brand_id=request.query_params.get('brand'))
        if request.query_params.get('category'):
            products = products.filter(category_id=request.query_params.get('category'))
        
        # Price Filter
        min_p = request.query_params.get('min_price')
        max_p = request.query_params.get('max_price')
        if min_p or max_p:
            products = products.annotate(
                real_min=Min('variants__price'), 
                real_max=Max('variants__price')
            )
            if min_p: products = products.filter(real_min__gte=min_p)
            if max_p: products = products.filter(real_max__lte=max_p)

        # ---------------------------------------------------------
        # 4. CRITICAL: DISTINCT BEFORE ORDERING
        # ---------------------------------------------------------
        # We must apply distinct here so we don't fetch duplicates for the shuffle list
        products = products.distinct()

        # ---------------------------------------------------------
        # 5. SORTING & SHUFFLING
        # ---------------------------------------------------------
        sort_by = request.query_params.get('sort')

        # DEFAULT BEHAVIOR: 
        # If searching -> Sort by Relevance (implicitly handled by database mostly, or add logic)
        # If browsing -> Shuffle (Random)
        if not sort_by:
            sort_by = 'relevance' if is_searching else 'shuffle'

        if sort_by == 'price_asc':
            products = products.annotate(p_min=Min('variants__price')).order_by('p_min')
        
        elif sort_by == 'price_desc':
            products = products.annotate(p_max=Max('variants__price')).order_by('-p_max')
        
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
            
        elif sort_by == 'shuffle':
            # --- THE SHUFFLE FIX ---
            
            # 1. Get Session Seed (Consistent for this user's browsing session)
            if not request.session.session_key:
                request.session.save()
            
            session_seed = request.session.get('product_shuffle_seed')
            if not session_seed:
                # Use a large range to avoid collision
                session_seed = random.randint(1, 1000000)
                request.session['product_shuffle_seed'] = session_seed

            # 2. Extract IDs specifically for shuffling
            # We convert to a list immediately to manipulate in Python
            product_ids = list(products.values_list('id', flat=True))

            # 3. Deterministic Shuffle
            # Using the same seed guarantees the same order for this user
            random.seed(session_seed)
            random.shuffle(product_ids)

            # 4. Force the Database to respect this order
            if product_ids:
                # Create a list of When() cases
                # "When ID is X, then position is 0", "When ID is Y, then position is 1"...
                ordering = [When(pk=pk, then=Value(i)) for i, pk in enumerate(product_ids)]
                
                # Rebuild queryset specifically for ordering
                # We filter by pk__in to ensure we only get these items (safety)
                # We use ProductModel.objects.filter to start clean and avoid "distinct" conflicts
                products = ProductModel.objects.filter(pk__in=product_ids).annotate(
                    random_order=Case(
                        *ordering,
                        output_field=IntegerField()
                    )
                ).order_by('random_order')

        # ---------------------------------------------------------
        # 6. PAGINATION
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
