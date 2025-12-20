from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import OrderModel, OrderItemModel, WishlistModel, AddressModel
from .serializers import (
    OrderSerializer, OrderCreateSerializer,
    WishlistSerializer, AddressSerializer
)
from products.models import ProductModel


class OrderCreateView(APIView):
    """
    Create a new order (guest or authenticated user)
    Expects cart items in request data
    """

    def post(self, request):
        # Add user to data if authenticated
        data = request.data.copy()
        if request.user.is_authenticated:
            data['user'] = request.user.id

        serializer = OrderCreateSerializer(data=data)
        if serializer.is_valid():
            order = serializer.save()

            # Return order details
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderTrackView(APIView):
    """
    Track order by order ID (no authentication required)
    Query: /api/orders/track/?order_id=MM123456
    """

    def get(self, request):
        order_id = request.query_params.get('order_id', None)

        if not order_id:
            return Response({"error": "Order ID required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = OrderModel.objects.get(order_id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except OrderModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class UserOrderListView(APIView):
    """
    Get all orders for authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get orders for logged-in user
        orders = OrderModel.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailView(APIView):
    """
    Get single order detail (must belong to user or use order_id)
    """

    def get(self, request, order_id):
        try:
            # If authenticated, check user owns the order
            if request.user.is_authenticated:
                order = OrderModel.objects.get(order_id=order_id, user=request.user)
            else:
                # Guest order - just match order_id
                order = OrderModel.objects.get(order_id=order_id)

            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except OrderModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class WishlistView(APIView):
    """
    Get user's wishlist
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = WishlistModel.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data)


class WishlistAddView(APIView):
    """
    Add product to wishlist
    Body: {"product_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = ProductModel.objects.get(id=product_id)

            # Check if already in wishlist
            wishlist_item, created = WishlistModel.objects.get_or_create(
                user=request.user,
                product=product
            )

            if created:
                return Response({"message": "Added to wishlist"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Already in wishlist"}, status=status.HTTP_200_OK)

        except ProductModel.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


class WishlistRemoveView(APIView):
    """
    Remove product from wishlist
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, wishlist_id):
        try:
            wishlist_item = WishlistModel.objects.get(id=wishlist_id, user=request.user)
            wishlist_item.delete()
            return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)
        except WishlistModel.DoesNotExist:
            return Response({"error": "Wishlist item not found"}, status=status.HTTP_404_NOT_FOUND)


class AddressListView(APIView):
    """
    Get all addresses for authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = AddressModel.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)


class AddressCreateView(APIView):
    """
    Create new address for user
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id

        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressUpdateView(APIView):
    """
    Update user address
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, address_id):
        try:
            address = AddressModel.objects.get(id=address_id, user=request.user)
            serializer = AddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AddressModel.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)


class AddressDeleteView(APIView):
    """
    Delete user address
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, address_id):
        try:
            address = AddressModel.objects.get(id=address_id, user=request.user)
            address.delete()
            return Response({"message": "Address deleted"}, status=status.HTTP_200_OK)
        except AddressModel.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)
        

