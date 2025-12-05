from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import (
    BrandModel, CategoryModel, ProductModel, ProductVariantModel,
    ProductImageModel, ProductSizeModel, ProductWeightModel, ReviewModel
)
from .serializers import (
    BrandSerializer, CategorySerializer, ProductDetailSerializer,
    ProductSizeSerializer, ProductWeightSerializer, ReviewSerializer
)


# ==================== BRAND MANAGEMENT ====================

class AdminBrandListCreateView(APIView):
    """
    Admin: List all brands or create new brand
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        brands = BrandModel.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBrandDetailView(APIView):
    """
    Admin: Get, update, or delete a brand
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            brand = BrandModel.objects.get(pk=pk)
            serializer = BrandSerializer(brand)
            return Response(serializer.data)
        except BrandModel.DoesNotExist:
            return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            brand = BrandModel.objects.get(pk=pk)
            serializer = BrandSerializer(brand, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BrandModel.DoesNotExist:
            return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            brand = BrandModel.objects.get(pk=pk)
            brand.delete()
            return Response({"message": "Brand deleted"}, status=status.HTTP_200_OK)
        except BrandModel.DoesNotExist:
            return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== CATEGORY MANAGEMENT ====================

class AdminCategoryListCreateView(APIView):
    """
    Admin: List all categories or create new category
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        categories = CategoryModel.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminCategoryDetailView(APIView):
    """
    Admin: Get, update, or delete a category
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            category = CategoryModel.objects.get(pk=pk)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except CategoryModel.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            category = CategoryModel.objects.get(pk=pk)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CategoryModel.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            category = CategoryModel.objects.get(pk=pk)
            category.delete()
            return Response({"message": "Category deleted"}, status=status.HTTP_200_OK)
        except CategoryModel.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== PRODUCT SIZE/WEIGHT MANAGEMENT ====================

class AdminSizeListCreateView(APIView):
    """
    Admin: List all sizes or create new size
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        sizes = ProductSizeModel.objects.all()
        serializer = ProductSizeSerializer(sizes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSizeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminWeightListCreateView(APIView):
    """
    Admin: List all weights or create new weight
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        weights = ProductWeightModel.objects.all()
        serializer = ProductWeightSerializer(weights, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductWeightSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== PRODUCT MANAGEMENT ====================

class AdminProductListCreateView(APIView):
    """
    Admin: List all products or create new product
    Supports search: ?search=mattress
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = ProductModel.objects.all()

        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            products = products.filter(name__icontains=search_query)

        products = products.order_by('-created_at')
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminProductDetailView(APIView):
    """
    Admin: Get, update, or delete a product
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            product = ProductModel.objects.get(pk=pk)
            serializer = ProductDetailSerializer(product)
            return Response(serializer.data)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            product = ProductModel.objects.get(pk=pk)
            serializer = ProductDetailSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            product = ProductModel.objects.get(pk=pk)
            product.delete()
            return Response({"message": "Product deleted"}, status=status.HTTP_200_OK)
        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== PRODUCT VARIANT MANAGEMENT ====================

class AdminVariantCreateView(APIView):
    """
    Admin: Create product variant
    Body: {"product": 1, "size": 1, "thickness": "6 inches", "price": 50000}
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        from .serializers import ProductVariantSerializer
        serializer = ProductVariantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminVariantDetailView(APIView):
    """
    Admin: Update or delete a variant
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            from .serializers import ProductVariantSerializer
            variant = ProductVariantModel.objects.get(pk=pk)
            serializer = ProductVariantSerializer(variant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProductVariantModel.DoesNotExist:
            return Response({"error": "Variant not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            variant = ProductVariantModel.objects.get(pk=pk)
            variant.delete()
            return Response({"message": "Variant deleted"}, status=status.HTTP_200_OK)
        except ProductVariantModel.DoesNotExist:
            return Response({"error": "Variant not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== PRODUCT IMAGE MANAGEMENT ====================

class AdminProductImageUploadView(APIView):
    """
    Admin: Upload product images
    Body (multipart): {"product": 1, "image": file, "is_main": true, "order": 0}
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        from .serializers import ProductImageSerializer
        serializer = ProductImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminProductImageDeleteView(APIView):
    """
    Admin: Delete product image
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            image = ProductImageModel.objects.get(pk=pk)
            image.delete()
            return Response({"message": "Image deleted"}, status=status.HTTP_200_OK)
        except ProductImageModel.DoesNotExist:
            return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== REVIEW MANAGEMENT ====================

class AdminReviewListView(APIView):
    """
    Admin: Get all reviews (approved and pending)
    Filter by status: ?status=approved or ?status=pending
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        reviews = ReviewModel.objects.all().order_by('-created_at')

        # Filter by approval status
        status_filter = request.query_params.get('status', None)
        if status_filter == 'approved':
            reviews = reviews.filter(is_approved=True)
        elif status_filter == 'pending':
            reviews = reviews.filter(is_approved=False)

        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class AdminReviewApproveView(APIView):
    """
    Admin: Approve a review
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            review = ReviewModel.objects.get(pk=pk)
            review.is_approved = True
            review.save()
            return Response({"message": "Review approved"})
        except ReviewModel.DoesNotExist:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminReviewDeleteView(APIView):
    """
    Admin: Delete a review
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            review = ReviewModel.objects.get(pk=pk)
            review.delete()
            return Response({"message": "Review deleted"})
        except ReviewModel.DoesNotExist:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
