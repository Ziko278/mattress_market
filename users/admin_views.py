from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import User
from orders.models import OrderModel
from orders.serializers import OrderSerializer
from .serializers import UserSerializer


# ==================== USER/CUSTOMER MANAGEMENT ====================

class AdminUserListView(APIView):
    """
    Admin: Get all users/customers
    Search: ?search=username or email
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')

        # Search by username or email
        search_query = request.query_params.get('search', None)
        if search_query:
            users = users.filter(
                username__icontains=search_query
            ) | users.filter(
                email__icontains=search_query
            )

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    """
    Admin: Get single user details with order history
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user_data = UserSerializer(user).data

            # Get user's orders
            orders = OrderModel.objects.filter(user=user).order_by('-created_at')
            orders_data = OrderSerializer(orders, many=True).data

            # Calculate total spent
            total_spent = sum([order.total_amount for order in orders])

            return Response({
                "user": user_data,
                "orders": orders_data,
                "total_orders": orders.count(),
                "total_spent": float(total_spent)
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminUserToggleActiveView(APIView):
    """
    Admin: Activate or deactivate user account
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)

            # Don't allow admin to deactivate themselves
            if user.id == request.user.id:
                return Response(
                    {"error": "You cannot deactivate your own account"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.is_active = not user.is_active
            user.save()

            return Response({
                "message": f"User {'activated' if user.is_active else 'deactivated'}",
                "is_active": user.is_active
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminUserDeleteView(APIView):
    """
    Admin: Delete user (use with caution - will affect order history)
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)

            # Don't allow admin to delete themselves
            if user.id == request.user.id:
                return Response(
                    {"error": "You cannot delete your own account"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.delete()
            return Response({"message": "User deleted"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)