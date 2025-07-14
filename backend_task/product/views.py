from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Product, Cart, CartItem
from .serializers import ProductSerializer, CartSerializer
from .filters import ProductFilter


# Получение списка товаров с фильтрацией, поиском, сортировкой
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name']


# Получение деталей конкретного товара
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# ViewSet для управления корзиной (добавление, просмотр, изменение, удаление)
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # Получение корзины по session_id (создаёт, если не существует)
    def get_cart(self, session_id):
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
        return cart

    # Получение содержимого корзины и общей стоимости
    def list(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        cart = self.get_cart(session_id)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    # Добавление товара в корзину (или обновление количества, если уже есть)
    def create(self, request):
        session_id = request.data.get('session_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not session_id or not product_id:
            return Response({'error': 'session_id and product_id are required'}, status=400)

        cart = self.get_cart(session_id)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if created:
            item.quantity = quantity
        else:
            item.quantity += int(quantity)
        item.save()

        return Response({'message': 'Item added to cart'}, status=201)

    # Обновление количества товара в корзине
    def update(self, request, pk=None):
        try:
            item = CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        quantity = request.data.get('quantity')
        if quantity is None or int(quantity) <= 0:
            return Response({'error': 'Quantity must be positive'}, status=400)

        item.quantity = int(quantity)
        item.save()
        return Response({'message': 'Quantity updated'})

    # Удаление товара из корзины
    def destroy(self, request, pk=None):
        try:
            item = CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)

        item.delete()
        return Response({'message': 'Item removed from cart'})