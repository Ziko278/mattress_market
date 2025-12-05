from rest_framework import serializers
from .models import OrderModel, OrderItemModel, AddressModel, WishlistModel
from products.serializers import ProductListSerializer


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
        fields = ['id', 'order_id', 'customer_name', 'customer_email', 'customer_phone',
                  'shipping_address', 'city', 'state', 'payment_method', 'status',
                  'total_amount', 'items', 'created_at', 'updated_at']
        read_only_fields = ['order_id', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(write_only=True)

    class Meta:
        model = OrderModel
        fields = ['customer_name', 'customer_email', 'customer_phone', 'shipping_address',
                  'city', 'state', 'payment_method', 'total_amount', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = OrderModel.objects.create(**validated_data)

        for item in items_data:
            OrderItemModel.objects.create(order=order, **item)

        return order


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = WishlistModel
        fields = ['id', 'product', 'added_at']