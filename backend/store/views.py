from typing import Any
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAdminUser,DjangoModelPermissions
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,DestroyModelMixin,UpdateModelMixin
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet,GenericViewSet


from store.filters import ProductFilter
from store.pagination import DefaultPagination
from store.permissions import FullDjangoModelPermission, IsAdminOrReadOnly
from .models import Cart, CartItem, Customer, Order, OrderItem, Product,Collection, ProductImage,Review
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CreateOrderSerializer, CustomerSerializer, OrderSerializer, ProductImageSerializer, ProductSerializer,CollectionSerializer, ReviewSerializer, UpdateCartItemSerializer, UpdateOrderSerializer

class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = ProductSerializer

    # Generic Filtering(Search by any Field)
    '''
    First create Filter Class 
    Then impliment filtering Logic and then in View set
    '''
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title','description']
    ordering_fields = ['unit_price']

    # Generic Filtering
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['collection_id']

    # Simple filtering by id whixh come with query params
    # def get_queryset(self):
    #     queryset = Product.objects.all()
    #     collection_id = self.request.query_params.get('collection_id')
    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset

    def get_serializer_context(self):
        return {'request':self.request}
    
    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk'])>0:
            return Response({'error':'Product belongs to Orderitems so this action is not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

    # def delete(self,request,pk):
    #     product = get_object_or_404(Product, pk =pk)
    #     if product.orderitems.count() > 0:
    #         return Response({'error':'Product belongs to Orderitems so this action is not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
    #     else:
    #         product.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)

class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['product_pk'])
    def get_serializer_context(self):
        return {'product_id':self.kwargs['product_pk']}
    
class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products'))
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']).count()>0:
            return Response({'error':'there are some products which blongs to that collection'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

    # def delete(self,request,pk):
    #     collection = get_object_or_404(
    #     Collection.objects.annotate(products_count=Count('products')),pk=pk)
    #     if collection.products_count > 0:
    #         return Response({'error':'there are some products which blongs to that collection'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
    #     collection.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

class ReviewViewSet(ModelViewSet):
    '''Yhan mere paa product_id ki access nai ha is liye mujhe
    get_queryset funtion implement karna ho ga
    queryset = Review.objects.all()'''
    serializer_class = ReviewSerializer
    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])
    '''
    context ke zariye ham urls main izafi data serializer ko bhej 
    sakte hain
    '''
    def get_serializer_context(self):
        return {'product_id':self.kwargs['product_pk']}

class CartViewSet(CreateModelMixin,RetrieveModelMixin,DestroyModelMixin,GenericViewSet):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get','post','patch','delete']
    # queryset = CartItem.objects.all()
    # serializer_class = CartItemSerializer
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.select_related('product').filter(cart_id = self.kwargs['cart_pk'])

    def get_serializer_context(self):
        return {'cart_id':self.kwargs['cart_pk']}
    
class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # Applying Permissions on Each Customer End POints
    permission_classes = [IsAdminUser]

    # Appliying permissions on different methods
    # def get_permissions(self):
    #     if self.request.method == 'GET':
    #         return [AllowAny()]
    #     return [IsAuthenticated()]
    
    # Applying permissions like that way
    # @action(detail=False,methods=['GET','PUT'],permission_classes=[IsAuthenticated])
    @action(detail=False,methods=['GET','PUT'],permission_classes=[IsAuthenticated])
    def me(self,request):
        customer = Customer.objects.get(user_id= request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class OrderViewSet(ModelViewSet):
    http_method_names = ['get','post','patch','delete','head','options']
    # queryset = Order.objects.prefetch_related('items__product').all()
    # serializer_class = OrderSerializer
    # permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.request.method in ['PATCH','DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
        
    '''
    Hmare pass Response main sirf card id return kar rha tha
    iss liye ham ne context main order return karne k lia
    create method ko overwrite kia haa
    '''
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data,context={'user_id':self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer



    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer_id = Customer.objects.only('id').get(user_id=user)
        return Order.objects.filter(customer_id=customer_id)






# class ProductList(ListCreateAPIView):
#     queryset = Product.objects.filter(id__lt=5)
#     serializer_class = ProductSerializer

#     def get_serializer_context(self):
#         return {'request':self.request}
    
#     # def get(self,request):
#     #     products = Product.objects.filter(id__lt = 5)
#     #     serializer = ProductSerializer(products,many=True,context = {'request':request})
#     #     return Response(serializer.data)
#     # def post(self,request):
#     #     serializer = ProductSerializer(data = request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     serializer.save()
#     #     return Response(serializer.data,status=status.HTTP_201_CREATED)

# class ProductDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     # def get(self,request,id):
#     #     product = get_object_or_404(Product, pk =id)
#     #     serializer = ProductSerializer(product)
#     #     return Response(serializer.data)
#     # def post(self,request,id):
#     #     product = get_object_or_404(Product, pk =id)
#     #     serializer = ProductSerializer(product,data = request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     serializer.save()
#     #     return Response(serializer.data,status=status.HTTP_200_OK)
#     def delete(self,request,pk):
#         product = get_object_or_404(Product, pk =pk)
#         if product.orderitems.count() > 0:
#             return Response({'error':'Product belongs to Orderitems so this action is not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         else:
#             product.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)



# class CollectionList(ListCreateAPIView):
#     queryset = Collection.objects.annotate(products_count=Count('products')).all().order_by('id')
#     serializer_class = CollectionSerializer

#     # def get(self,request):
#     #     collections = Collection.objects.annotate(products_count=Count('products')).all().order_by('id')
#     #     serializer = CollectionSerializer(collections,many=True)
#     #     return Response(serializer.data,status=status.HTTP_200_OK)
#     # def post(self,request):
#     #     serializer = CollectionSerializer(data = request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     serializer.save()
#     #     return Response(serializer.data,status=status.HTTP_201_CREATED)

# class CollectionDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Collection.objects.annotate(products_count=Count('products')).all()
#     serializer_class = CollectionSerializer
#     # def get(self,request,id):
#     #     collection = get_object_or_404(
#     #     Collection.objects.annotate(products_count=Count('products')),pk=id)
#     #     serializer = CollectionSerializer(collection)
#     #     return Response(serializer.data)
#     # def post(self,request,id):
#     #     collection = get_object_or_404(
#     #     Collection.objects.annotate(products_count=Count('products')),pk=id)
#     #     serializer = CollectionSerializer(collection,data=request.data)
#     #     serializer.is_valid(raise_exception=True)
#     #     serializer.save()
#     #     return Response(serializer.data,status=status.HTTP_200_OK)
#     def delete(self,request,pk):
#         collection = get_object_or_404(
#         Collection.objects.annotate(products_count=Count('products')),pk=pk)
#         if collection.products_count > 0:
#             return Response({'error':'there are some products which blongs to that collection'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# Functional Base View
# @api_view(['GET','POST'])
# def product_list(request):
#     if request.method == 'GET':
#         # # serializing Reationships by String Representation
#         # products = Product.objects.select_related('collection').filter(id__lt = 50)
#         products = Product.objects.filter(id__lt = 5)
#         serializer = ProductSerializer(products,many=True,context = {'request':request})
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = ProductSerializer(data = request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data,status=status.HTTP_201_CREATED)


# @api_view(['GET','PUT','DELETE'])
# def product_detail(request,id):
#     product = get_object_or_404(Product, pk = id)
#     if request.method == 'GET':
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#         # try:
#         #     product = Product.objects.get(pk = id)
#         #     serializer = ProductSerializer(product)
#         #     return Response(serializer.data)
#         # except Product.DoesNotExist:
#         #     return Response(status.HTTP_404_NOT_FOUND)
#     elif request.method == 'PUT':
#         serializer = ProductSerializer(product,data = request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data,status=status.HTTP_200_OK)
#     elif request.method == 'DELETE':
#         if product.orderitems.count() > 0:
#             return Response({'error':'Product belongs to Orderitems so this action is not allowed'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         else:
#             product.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)



# @api_view(['GET','POST'])
# def collection_list(request):
#     if request.method == 'GET':
#         collections = Collection.objects.annotate(products_count=Count('products')).all().order_by('id')
#         serializer = CollectionSerializer(collections,many=True)
#         return Response(serializer.data,status=status.HTTP_200_OK)
#     elif request.method == 'POST':
#         serializer = CollectionSerializer(data = request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data,status=status.HTTP_201_CREATED)



# @api_view(['GET','PUT','DELETE'])
# def collection_detail(request,id):
#     collection = get_object_or_404(
#         Collection.objects.annotate(products_count=Count('products')),pk=id)
#     if request.method == 'GET':
#         serializer = CollectionSerializer(collection)
#         return Response(serializer.data)
#     elif request.method == 'PUT':
#         serializer = CollectionSerializer(collection,data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data,status=status.HTTP_200_OK)
#     elif request.method == 'DELETE':
#         if collection.products_count > 0:
#             return Response({'error':'there are some products which blongs to that collection'},status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
