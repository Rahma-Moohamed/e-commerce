from rest_framework import serializers
from storeapp.models import *




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id','title', 'slug']



class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
      model= ProductImage
      fields = ['id','product', 'image']  


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        images= ProductImageSerializer(many=True, read_only=True)
        uploaded_images = serializers.ListField(
        child= serializers.ImageField(max_length=10000,allow_empty_file=False, use_url=False)
        write_only= True
        )
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'slug', 'inventory', 'old_price', 'price', 'images']

    def create(self, validated_data): 
        uploaded_images = validated_data.pop('uploaded_images') 
        product = Product.objects.create(**validated_data)
        for image in uploaded_images:
            newproductimage = ProductImage.objects.create(product=product, image=image)
        return product


    # category =  CategorySerializer()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date_created', 'name', 'description']
    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id=product_id, **validated_data)

    
    

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'price', 'name']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(many=False, read_only=True)
    sub_total = serializers.FloatField(source='subTotal', read_only=True)

    class Meta: 
        model = Cartitems
        fields = ['id','cart', 'product', 'quantity' , 'sub_total']
    def total(self,cartitem:Cartitems):
        return cartitem.quantity *cartitem.product.price

class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cartitems 
        fields = ['id','product_id', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    cart_id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True,read_only=True)
    grand_total = serializers.SerializerMethodField(method_name='main_total')

    class Meta:
        model = Cart
        fields = ['cart_id', 'items', 'grand_total']

    def main_total(self, cart:Cart):
        items = cart.items.all()
        total = sum([item.quantity * item.product.price for item in items])
        return total