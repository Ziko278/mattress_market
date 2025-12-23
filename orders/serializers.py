from decimal import Decimal
from rest_framework import serializers
from site_config.models import SettingsModel
from .models import OrderModel, OrderItemModel, AddressModel, WishlistModel
from products.serializers import ProductListSerializer
from products.models import ProductVariantModel
from django.conf import settings
from django.db import transaction
import logging


logger = logging.getLogger(__name__)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressModel
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemModel
        fields = ['id', 'product_name', 'size', 'price', 'quantity', 'subtotal']

    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = OrderModel
        fields = [
            'id', 'order_id', 'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'payment_method', 'status',
            'logistic_price', 'total_amount', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_id', 'created_at', 'updated_at',
                            'logistic_price', 'total_amount']


class OrderCreateSerializer(serializers.ModelSerializer):
    # client sends items list; create() will handle saving items & computing totals
    items = serializers.ListField(write_only=True)

    class Meta:
        model = OrderModel
        # do NOT accept client total_amount — server computes it
        fields = ['user', 'customer_name', 'customer_email', 'customer_phone',
                  'shipping_address', 'payment_method', 'items']
        extra_kwargs = {'user': {'required': False, 'allow_null': True}}

    def _calculate_logistic_fee(self, subtotal: Decimal) -> Decimal:
        """
        Calculate logistic fee using SettingsModel (single-row table).
        """
        settings_obj = SettingsModel.objects.first()

        if not settings_obj:
            return Decimal('0.00')

        if (
            settings_obj.free_shipping_threshold
            and subtotal >= settings_obj.free_shipping_threshold
        ):
            return Decimal('0.00')

        return Decimal(settings_obj.shipping_fee or 0).quantize(Decimal('0.01'))

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])

        # Use transaction so partial writes rollback on error
        with transaction.atomic():
            # Create order with temporary total to satisfy NOT NULL constraint
            order = OrderModel.objects.create(total_amount=Decimal('0.00'), **validated_data)

            subtotal = Decimal('0.00')

            for item in items_data:
                # Keep your original pattern: pop product_variant id and create with **item
                variant_id = item.pop('product_variant', None)

                product_variant = None
                if variant_id is not None:
                    try:
                        product_variant = ProductVariantModel.objects.get(id=variant_id)
                    except ProductVariantModel.DoesNotExist:
                        product_variant = None

                # Determine qty safely
                try:
                    qty = int(item.get('quantity', 1) or 1)
                except Exception:
                    qty = 1

                # Determine price: prefer payload price, else product_variant.price, else 0
                price = item.get('price', None)
                try:
                    price = Decimal(str(price)) if price is not None else None
                except Exception:
                    price = None

                if price is None and product_variant is not None:
                    try:
                        price = Decimal(getattr(product_variant, 'price', 0) or 0)
                    except Exception:
                        price = None

                if price is None:
                    price = Decimal('0.00')

                # Ensure item dict has price and quantity so your **item works
                item['price'] = price
                item['quantity'] = qty

                # Create item using your original flexible behaviour
                OrderItemModel.objects.create(
                    order=order,
                    product_variant=product_variant,
                    **item
                )

                # accumulate subtotal
                try:
                    subtotal += (price * Decimal(qty))
                except Exception:
                    # if something odd happens, continue but log
                    logger.exception("Failed to accumulate subtotal for order %s item %s", getattr(order, 'order_id', 'unknown'), item)

            # Compute logistic fee (server-side) and persist final totals
            logistic_fee = self._calculate_logistic_fee(subtotal)
            order.logistic_price = logistic_fee
            order.total_amount = (subtotal + logistic_fee).quantize(Decimal('.01'))
            order.save(update_fields=['logistic_price', 'total_amount'])

            return order


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = WishlistModel
        fields = ['id', 'product', 'added_at']