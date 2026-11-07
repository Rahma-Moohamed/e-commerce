from django.db import transaction
from rest_framework import serializers

from storeapp.models import (
    Cart,
    Cartitems,
    Category,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Profile,
    Review,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'title', 'slug']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=10000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'slug', 'inventory',
            'old_price', 'price', 'images', 'uploaded_images',
        ]

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = Product.objects.create(**validated_data)
        for image in uploaded_images:
            ProductImage.objects.create(product=product, image=image)
        return product


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date_created', 'name', 'description']

    def create(self, validated_data):
        return Review.objects.create(
            product_id=self.context['product_id'],
            **validated_data
        )


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'price', 'name']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    sub_total = serializers.FloatField(source='subTotal', read_only=True)

    class Meta:
        model = Cartitems
        fields = ['id', 'cart', 'product', 'quantity', 'sub_total']


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField()

    class Meta:
        model = Cartitems
        fields = ['id', 'product_id', 'quantity']

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No valid product ID; try again.')
        return value

    def create(self, validated_data):
        cart_id = self.context['cart_id']
        product_id = validated_data.pop('product_id')
        quantity = validated_data['quantity']
        with transaction.atomic():
            try:
                cartitem = Cartitems.objects.select_for_update().get(
                    product_id=product_id,
                    cart_id=cart_id,
                )
            except Cartitems.DoesNotExist:
                return Cartitems.objects.create(
                    cart_id=cart_id,
                    product_id=product_id,
                    **validated_data
                )

            cartitem.quantity += quantity
            cartitem.save(update_fields=['quantity'])
            return cartitem


class UpdateCartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = Cartitems
        fields = ['quantity']


class CartSerializer(serializers.ModelSerializer):
    cart_id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField(method_name='main_total')

    class Meta:
        model = Cart
        fields = ['cart_id', 'items', 'grand_total']

    def main_total(self, cart):
        return sum(item.quantity * item.product.price for item in cart.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'placed_at', 'pending_status', 'owner', 'items']
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField(write_only=True)

    def validate_cart_id(self, value):
        user = self.context['request'].user
        cart = Cart.objects.filter(
            cart_id=value,
            owner__user=user,
            completed=False,
        ).first()
        if cart is None or not cart.items.exists():
            raise serializers.ValidationError('No active cart with items was found.')
        if cart.items.filter(product__isnull=True).exists():
            raise serializers.ValidationError('The cart contains an invalid product.')
        if cart.items.filter(quantity__lte=0).exists():
            raise serializers.ValidationError('The cart contains an invalid quantity.')
        if Order.objects.filter(cart=cart).exists():
            raise serializers.ValidationError('This cart has already been ordered.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            try:
                cart = Cart.objects.select_for_update().get(
                    cart_id=validated_data['cart_id'],
                    owner__user=user,
                    completed=False,
                )
            except Cart.DoesNotExist:
                raise serializers.ValidationError(
                    {'cart_id': 'No active cart with items was found.'}
                )

            cart_items = list(cart.items.select_related('product').all())
            if not cart_items or any(item.product_id is None for item in cart_items):
                raise serializers.ValidationError(
                    {'cart_id': 'The cart has no valid items.'}
                )

            order = Order.objects.create(owner=user, cart=cart)
            OrderItem.objects.bulk_create(
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                )
                for item in cart_items
            )
            cart.completed = True
            cart.save(update_fields=['completed'])

        return order


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'bio', 'image']
