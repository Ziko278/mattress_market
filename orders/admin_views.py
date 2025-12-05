from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import OrderModel, OrderItemModel
from .serializers import OrderSerializer


# ==================== ORDER MANAGEMENT ====================

class AdminOrderListView(APIView):
    """
    Admin: Get all orders with filters
    Filters: ?status=pending, ?search=MM123456, ?customer=email@example.com
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = OrderModel.objects.all().order_by('-created_at')

        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            orders = orders.filter(status=status_filter)

        # Search by order ID or customer name
        search_query = request.query_params.get('search', None)
        if search_query:
            orders = orders.filter(
                order_id__icontains=search_query
            ) | orders.filter(
                customer_name__icontains=search_query
            )

        # Filter by customer email
        customer_email = request.query_params.get('customer', None)
        if customer_email:
            orders = orders.filter(customer_email=customer_email)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class AdminOrderDetailView(APIView):
    """
    Admin: Get single order details
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            order = OrderModel.objects.get(pk=pk)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except OrderModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminOrderUpdateStatusView(APIView):
    """
    Admin: Update order status
    Body: {"status": "processing"} or "shipped" or "delivered" or "cancelled"
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            order = OrderModel.objects.get(pk=pk)
            new_status = request.data.get('status')

            # Validate status
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            if new_status not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Choose from: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = new_status
            order.save()

            serializer = OrderSerializer(order)
            return Response(serializer.data)

        except OrderModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class AdminOrderDeleteView(APIView):
    """
    Admin: Delete an order (use with caution)
    """
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            order = OrderModel.objects.get(pk=pk)
            order.delete()
            return Response({"message": "Order deleted"}, status=status.HTTP_200_OK)
        except OrderModel.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


# ==================== DASHBOARD STATS ====================

class AdminDashboardStatsView(APIView):
    """
    Admin: Get dashboard statistics
    Returns: total orders, revenue, pending orders, recent orders
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Date filters
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Total stats
        total_orders = OrderModel.objects.count()
        total_revenue = OrderModel.objects.filter(
            status__in=['delivered', 'processing', 'shipped']
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Today's stats
        today_orders = OrderModel.objects.filter(created_at__date=today).count()
        today_revenue = OrderModel.objects.filter(
            created_at__date=today
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # This week's stats
        week_orders = OrderModel.objects.filter(created_at__date__gte=week_ago).count()
        week_revenue = OrderModel.objects.filter(
            created_at__date__gte=week_ago
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # This month's stats
        month_orders = OrderModel.objects.filter(created_at__date__gte=month_ago).count()
        month_revenue = OrderModel.objects.filter(
            created_at__date__gte=month_ago
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Orders by status
        pending_orders = OrderModel.objects.filter(status='pending').count()
        processing_orders = OrderModel.objects.filter(status='processing').count()
        shipped_orders = OrderModel.objects.filter(status='shipped').count()
        delivered_orders = OrderModel.objects.filter(status='delivered').count()
        cancelled_orders = OrderModel.objects.filter(status='cancelled').count()

        # Recent orders (last 10)
        recent_orders = OrderModel.objects.all().order_by('-created_at')[:10]
        recent_orders_data = OrderSerializer(recent_orders, many=True).data

        return Response({
            "total": {
                "orders": total_orders,
                "revenue": float(total_revenue)
            },
            "today": {
                "orders": today_orders,
                "revenue": float(today_revenue)
            },
            "this_week": {
                "orders": week_orders,
                "revenue": float(week_revenue)
            },
            "this_month": {
                "orders": month_orders,
                "revenue": float(month_revenue)
            },
            "by_status": {
                "pending": pending_orders,
                "processing": processing_orders,
                "shipped": shipped_orders,
                "delivered": delivered_orders,
                "cancelled": cancelled_orders
            },
            "recent_orders": recent_orders_data
        })