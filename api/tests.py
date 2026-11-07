from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from storeapp.models import Cart, Cartitems, Order, Product


class CreateOrderTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='buyer@example.com',
            password='test-password',
        )
        self.product = Product.objects.create(name='Test product', old_price=12.5)
        self.cart = Cart.objects.create(
            owner=self.user.customer,
            session_id='test-session',
        )
        Cartitems.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.client.force_authenticate(user=self.user)

    def test_create_order_transfers_cart_items_and_completes_cart(self):
        response = self.client.post(
            '/api/orders/',
            {'cart_id': str(self.cart.cart_id)},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get()
        self.assertEqual(order.owner, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.get().product, self.product)
        self.assertEqual(order.items.get().quantity, 2)
        self.cart.refresh_from_db()
        self.assertTrue(self.cart.completed)
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    def test_cannot_create_an_order_from_another_users_cart(self):
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            password='test-password',
        )
        other_cart = Cart.objects.create(
            owner=other_user.customer,
            session_id='other-session',
        )
        Cartitems.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
            '/api/orders/',
            {'cart_id': str(other_cart.cart_id)},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
