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
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import logging


logger = logging.getLogger(__name__)


def send_order_confirmation(order):
    """
    Send order confirmation email to customer AND admin list.
    This function is safe: it logs exceptions and does not raise.
    Expects order to have: customer_email, customer_name, order_id, items, total_amount
    """
    try:
        customer_email = getattr(order, 'customer_email', None)
        if not customer_email:
            logger.info("No customer email on order %s", getattr(order, 'order_id', 'unknown'))
            return False

        # Get admin email list
        admin_emails = getattr(settings, 'ADMIN_EMAIL', [])
        if isinstance(admin_emails, str):
            admin_emails = [admin_emails]

        # All recipients: customer + admins
        all_recipients = [customer_email] + admin_emails

        subject = f"Order Confirmation — {order.order_id}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mattressmarket.ng')

        context = {'order': order}

        # Render templates with proper error logging
        try:
            html_body = render_to_string('emails/order_confirmation.html', context)
            text_body = render_to_string('emails/order_confirmation.txt', context)
        except Exception as e:
            logger.warning("Template rendering failed: %s. Using fallback.", e)
            text_body = f"Order {order.order_id} confirmed. Total: ₦{order.total_amount:,.2f}"
            html_body = f"<p>Order <strong>{order.order_id}</strong> confirmed.</p>"

        # Send to customer + admins in one email
        msg = EmailMultiAlternatives(subject, text_body, from_email, all_recipients)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=True)
        
        logger.info("Order confirmation sent for %s to %s", order.order_id, all_recipients)
        return True
        
    except Exception as exc:
        logger.exception("Failed to send order confirmation: %s", exc)
        return False


class OrderCreateView(APIView):
    """
    Thin view: uses serializer.create() to do heavy lifting (items/totals).
    Sends immediate email for pay_on_delivery; defers for online.
    """
    def post(self, request):
        data = request.data.copy()
        if request.user.is_authenticated:
            data['user'] = request.user.id

        serializer = OrderCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = serializer.save()
        except Exception as exc:
            logger.exception("Order creation failed: %s", exc)
            return Response({'error': 'Failed to create order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order_data = OrderSerializer(order).data

        payment_method = (order.payment_method or '').lower()
        payment_required = (payment_method == 'online')

        # send confirmation email only for pay_on_delivery
        if payment_method == 'pay_on_delivery':
            try:
                send_order_confirmation(order)
            except Exception:
                logger.exception("Error sending immediate email for order %s", order.order_id)

        return Response({
            "order": order_data,
            "payment_required": payment_required
        }, status=status.HTTP_201_CREATED)
     
    
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
        


class PaymentCallbackView(APIView):
    """
    Endpoint to verify and mark payments as paid.
    Expects POST JSON including:
      - order_id (recommended) OR reference
      - reference (gateway reference)
      - status (optional) e.g. 'success' to force mark in debug
      - provider (optional) 'paystack' or 'flutterwave'
    Behaviour:
      - Verifies with gateway if provider + secret key available
      - Marks order as paid (idempotent)
      - Sends confirmation email AFTER successful payment
      - Returns {"status":"success","order_id":"..."} on success
    """
    permission_classes = []  # public, gateway will post or frontend will POST

    def post(self, request):
        data = request.data or {}
        order_id = data.get('order_id')
        reference = data.get('reference')
        status_input = (data.get('status') or '').lower()
        provider = (data.get('provider') or '').lower()

        if not (order_id or reference):
            return Response({"error": "order_id or reference required."}, status=status.HTTP_400_BAD_REQUEST)

        # Find order if possible
        order = None
        try:
            if order_id:
                order = OrderModel.objects.get(order_id=order_id)
            elif reference:
                # fallback: try to locate by payment_reference field if exists
                order = OrderModel.objects.filter(payment_reference=reference).first()
        except OrderModel.DoesNotExist:
            order = None

        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # If already paid - idempotent
        if getattr(order, 'is_paid', False) or getattr(order, 'payment_status', '') == 'paid':
            return Response({"status": "success", "order_id": order.order_id}, status=status.HTTP_200_OK)

        # Helper to mark paid and send email
        def mark_paid_and_email(ref):
            try:
                if hasattr(order, 'payment_reference'):
                    order.payment_reference = ref or getattr(order, 'payment_reference', '')
                if hasattr(order, 'is_paid'):
                    order.is_paid = True
                if hasattr(order, 'payment_status'):
                    order.payment_status = 'paid'
                if hasattr(order, 'status'):
                    # change to whichever status you prefer
                    order.status = 'processing'
                if hasattr(order, 'paid_at'):
                    order.paid_at = timezone.now()
                order.save()
            except Exception:
                logger.exception("Failed to mark order %s paid", getattr(order, 'order_id', 'unknown'))
                raise

            # send confirmation after successfully marking paid
            try:
                send_order_confirmation(order)
            except Exception:
                logger.exception("Failed to send confirmation email after payment for order %s", order.order_id)

        # 1) If frontend gave a simple trusted success (useful for debug/dev)
        if status_input == 'success':
            mark_paid_and_email(reference or getattr(order, 'payment_reference', ''))
            return Response({"status": "success", "order_id": order.order_id}, status=status.HTTP_200_OK)

        # 2) Server-side verification with Paystack
        if provider == 'paystack' and getattr(settings, 'PAYSTACK_SECRET_KEY', None) and reference:
            try:
                headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
                url = f"https://api.paystack.co/transaction/verify/{reference}"
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                payload = resp.json()

                if payload.get("status") and payload.get("data", {}).get("status") == "success":
                    paystack_amount = int(payload["data"].get("amount", 0))  # in kobo
                    order_amount_naira = Decimal(getattr(order, "total_amount", 0) or 0)
                    expected = int(order_amount_naira * 100)
                    if paystack_amount == expected:
                        mark_paid_and_email(reference)
                        return Response({"status": "success", "order_id": order.order_id}, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Paystack reports unsuccessful transaction."}, status=status.HTTP_400_BAD_REQUEST)
            except requests.RequestException as e:
                logger.exception("Paystack verification error for %s: %s", reference, e)
                return Response({"error": "Paystack verification failed."}, status=status.HTTP_502_BAD_GATEWAY)

        # 3) Server-side verification with Flutterwave
        if provider == 'flutterwave' and getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None) and reference:
            try:
                headers = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"}
                # Note: depending on your Flutterwave reference type you might need /v3/transactions/{id}/verify
                url = f"https://api.flutterwave.com/v3/transactions/{reference}/verify"
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("status") == "success" and payload.get("data", {}).get("status") == "successful":
                    fw_amount = Decimal(payload["data"].get("amount", 0))
                    order_amount_naira = Decimal(getattr(order, "total_amount", 0) or 0)
                    if fw_amount == order_amount_naira:
                        mark_paid_and_email(reference)
                        return Response({"status": "success", "order_id": order.order_id}, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "Amount mismatch"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": "Flutterwave reports unsuccessful transaction."}, status=status.HTTP_400_BAD_REQUEST)
            except requests.RequestException as e:
                logger.exception("Flutterwave verification error for %s: %s", reference, e)
                return Response({"error": "Flutterwave verification failed."}, status=status.HTTP_502_BAD_GATEWAY)

        # 4) If we reach here - we couldn't verify
        return Response({
            "error": "Could not verify payment. Provide provider and valid reference, or post status:'success' in DEBUG."
        }, status=status.HTTP_400_BAD_REQUEST)
