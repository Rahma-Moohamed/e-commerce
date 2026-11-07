from django.urls import path, include
#from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import *

router = routers.DefaultRouter()

router.register('products', ProductViewSet)
router.register('categories', CategoryViewSet)
router.register('carts', CartViewSet)
router.register('profile', ProfileViewSet)
router.register('orders', OrderViewSet, basename='orders')



product_router = routers.NestedDefaultRouter(router , 'products' , lookup= 'product')
product_router.register('reviews', ReviewViewSet, basename='reviews-list')

cart_router = routers.NestedDefaultRouter(router , 'carts' , lookup= 'cart')
cart_router.register('items', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(product_router.urls)),
    path('', include(cart_router.urls)),

]
