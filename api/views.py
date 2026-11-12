# from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status

# from .models import Product, Category
# from .serializers import ProductSerializer, CategorySerializer


# # =========================
# # Products
# # =========================

# @api_view(['GET', 'POST'])
# def api_products(request):

#     # Get all products
#     if request.method == 'GET':
#         products = Product.objects.all()
#         serializer = ProductSerializer(products, many=True)
#         return Response(serializer.data)

#     # Create a new product
#     elif request.method == 'POST':
#         serializer = ProductSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET', 'PUT', 'DELETE'])
# def api_product(request, pk):

#     product = get_object_or_404(Product, pk=pk)

#     # Get one product
#     if request.method == 'GET':
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)

#     # Update product
#     elif request.method == 'PUT':
#         serializer = ProductSerializer(product, data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # Delete product
#     elif request.method == 'DELETE':
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# # =========================
# # Categories
# # =========================

# @api_view(['GET', 'POST'])
# def api_categories(request):

#     # Get all categories
#     if request.method == 'GET':
#         categories = Category.objects.all()
#         serializer = CategorySerializer(categories, many=True)
#         return Response(serializer.data)

#     # Create a new category
#     elif request.method == 'POST':
#         serializer = CategorySerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET', 'PUT', 'DELETE'])
# def api_category(request, pk):

#     category = get_object_or_404(Category, pk=pk)

#     # Get one category
#     if request.method == 'GET':
#         serializer = CategorySerializer(category)
#         return Response(serializer.data)

#     # Update category
#     elif request.method == 'PUT':
#         serializer = CategorySerializer(category, data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     # Delete category
#     elif request.method == 'DELETE':
#         category.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)




from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,DestroyModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_201_CREATED

from .filter import ProductFilter
from storeapp.models import Cart, Cartitems, Category, Order, Product, Profile, Review
from .serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    CreateOrderSerializer,
    OrderSerializer,
    ProductSerializer,
    ProfileSerializer,
    ReviewSerializer,
    UpdateCartItemSerializer,
)

class ProductViewSet(ModelViewSet):
   queryset = Product.objects.all()
   serializer_class = ProductSerializer
   filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
   filterset_class = ProductFilter
   search_fields = ['name', 'description' ]
   ordering_fields = ['old_price']
   pagination_class = PageNumberPagination

class CategoryViewSet(ModelViewSet):
   queryset = Category.objects.all()
   serializer_class = CategorySerializer

class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product_id'] = self.kwargs['product_pk']
        return context

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'patch', 'delete', 'post']
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create':
            return AddCartItemSerializer
        if self.action in ('update', 'partial_update'):
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['cart_id'] = self.kwargs['cart_pk']
        return context

    def get_queryset(self):
        return Cartitems.objects.filter(
            cart_id=self.kwargs['cart_pk'],
        ).select_related('product', 'cart')


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related('owner', 'cart').prefetch_related(
        'items__product'
    )
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(owner=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        output = OrderSerializer(order, context=self.get_serializer_context())
        return Response(output.data, status=HTTP_201_CREATED)


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    parser_classes = (MultiPartParser, FormParser)


# class ApiCategories(RetrieveUpdateDestroyAPIVIEW):
#    queryset = Category.objects.all()
#    serializer_class = CategorySerializer
  

# class ApiProduct(RetrieveUpdateDestroyAPIVIEW):
#    queryset = Product.objects.all()
#    serializer_class = ProductSerializer


#    def get(self,request):
#       products = Product.objects.all()
#       serializer = ProductSerializer(products, many = True)
#       return Response(serializer.data)
   
#    def post(self,request):
#       serializer = ProductSerializer(data=request.data)
#       serializer.is_valid(raise_exception=True)
#       serializer.save()
#       return Response(serializer.data)

#    def get(self, request):
#        product = get_object_or_404(Product, id=pk)
#        serializer = ProductSerializer(product)
#        return Response(serializer.data)
#    def put(self,request,pk):
#        product = get_object_or_404(Product, id=pk)
#        serializer = ProductSerializer(product, data=request.data)
#        serializer.is_valid(raise_exception=True)
#        serializer.save()
#        return Response(serializer.data)   

#    def delete(self,request,pk):
#      product = get_object_or_404(Product, id=pk)
#      product.delete()
#      return Response(status=HTTP_204_NO_CONTENT)



# class ApiCategories(APIView):
#    def get(self,request):
#       categories = Category.objects.all()
#       serializer = CategorySerializer(categories, many = True)
#       return Response(serializer.data)
   
#    def post(self,request):
#       serializer = CategorySerializer(data=request.data)
#       serializer.is_valid(raise_exception=True)
#       serializer.save()
#       return Response(serializer.data)

#    class ApiCategory(APIView):
#     def get(self, request):
#        category = get_object_or_404(category, id=pk)
#        serializer = CategorySerializer(product)
#        return Response(serializer.data)
#     def put(self,request,pk):
#        product = get_object_or_404(Product, id=pk)
#        serializer = ProductSerializer(product, data=request.data)
#        if serializer.is_valid():  
#         serializer.save()
#         return Response(serializer.data)   

#     def delete(self,request,pk):
#      product = get_object_or_404(Product, id=pk)
#      product.delete()
#      return Response(status=HTTP_204_NO_CONTENT)


# @api_view(['GET', 'PUT','DELETE'])
# def api_product(request, pk):
#     product = get_object_or_404(Product, id=pk)
#     if request.method == "GET":
#      serializer = ProductSerializer(product)
#      return Response(serializer.data)
#     if request.method == "PUT":
#        serializer = ProductSerializer(product, data=request.data)
#        if serializer.is_valid():
#           serializer.save()
#           return Response(serializer.data)   
#     if request.method == "DELETE":
#        product.delete()
#        return Response(status=HTTP_204_NO_CONTENT)

       
# @api_view(['GET', 'POST'])
# def api_categories(request):
#  if request.method == "GET":
#      categories = Category.objects.all()
#      serializer = CategorySerializer(categories, many = True)
#      return Response(serializer.data)
#  if request.method == "POST":
#        serializer =CategorySerializer(categories, many=True)
#        serializer.is_valid(raise_exception=True)
#        serializer.save()
#        return Response(serializer.data)
#  return Response(serializer.data)

# @api_view(['GET', 'PUT', 'DELETE'])
# def api_category(request, pk):
#     category = get_object_or_404(Category.category_id, id=pk)
#     if request.method == "GET":
#        serializer = CategorySerializer(category)
#        return Response(serializer.data)
#     if request.method == "PUT":
#        serializer = CategorySerializer(category, data=request.data)
#        if serializer.is_valid():
#           serializer.save()
#           return Response(serializer.data)
#        if request.method == "DELETE":
#           category.delete()
#           return Response(status=HTTP_204_NO_CONTENT)
#        serializer = CategorySerializer(category)
#     return Response(serializer.data)    


# class ApiCategories(ListCreateAPIVIEW):
#    queryset = Category.objects.all()
#    serializer_class = CategorySerializer

# class ApiCategories(RetrieveUpdateDestroyAPIVIEW):
#    queryset = Category.objects.all()
#    serializer_class = CategorySerializer
