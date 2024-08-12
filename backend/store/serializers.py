from decimal import Decimal
from django.db.models import Count
from django.db import transaction
from rest_framework import serializers


from .models import Cart, CartItem, Customer, Order, OrderItem, Product,Collection, ProductImage,Review

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id','title','products_count']
    products_count = serializers.IntegerField(read_only = True)

class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id,**validated_data)
    class Meta:
        model = ProductImage
        fields = ['id','image']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True,read_only=True)
    class Meta:
        model = Product
        fields = ['id','title','slug','description','unit_price','price_with_tax','inventory','collection','images']
    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
  
    # Simple Serializer
    # id = serializers.IntegerField()
    # title = serializers.CharField(max_length = 255)
    # price = serializers.DecimalField(max_digits=6,decimal_places=2,source = 'unit_price')
    # price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    # # # Serializing Relationships by Primary Key
    # # collection = serializers.PrimaryKeyRelatedField(
    # #     queryset = Collection.objects.all()
    # # )
    # # # serializing Reationships by String Representation
    # # collection = serializers.StringRelatedField()
    # # # Serializing Relationships by Nested Object
    # # collection = CollectionSerializer()
    # # Serialixing Relationships by HyperLink
    # collection = serializers.HyperlinkedRelatedField(
    #     queryset = Collection.objects.all(),
    #     view_name= 'collection-detail'
    # )

    def calculate_tax(self,product: Product):
        return product.unit_price * Decimal(1.1)
    

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id','title','unit_price']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id','date' ,'name','description']
        
    '''If i not implemnet this then there will be an error 
    product_id should not be null iss liye ma ne is method
    ko overwrite kia ha or jo product id url main arahi ha
    us ko yahan save kia haa'''
    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id = product_id,**validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    product=SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    
    def get_total_price(self,cartitem:CartItem):
        return cartitem.product.unit_price * cartitem.quantity
    class Meta:
        model = CartItem
        fields = ['product','quantity','total_price']
    
class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    # This is the built in function for validating a single value
    # Name of function  validate_fieldname(self,value(this value is value of our field  which comes with request))
    def validate_product_id(self,value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('This product is not available')
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        try:
            cart_item =  CartItem.objects.get(cart_id=cart_id,product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id,**self.validated_data)
        return self.instance   
    class Meta:
        model = CartItem
        fields = ['id','product_id','quantity']

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']    
    

class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True,read_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    def get_total_price(self,cart:Cart):
        # With List Comprehension
         return sum([item.quantity*item.product.unit_price for item in cart.items.all()])
        # With For Loop
        # for item in cart.items.all():
        #     return sum(item.product.unit_price * item.quantity)

    class Meta:
        model = Cart
        fields = ['id','items','total_price']
        
    # total_price = serializers.SerializerMethodField(method_name='calculate_total_price')
    # def calculate_total_price(self):
    #     return sum(CartItemSerializer.total_price[:-1])

class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Customer
        fields = ['user_id','phone','birth_date','membership']

class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = OrderItem
        fields = ['id','product','unit_price','quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_id = serializers.IntegerField()
    placed_at = serializers.DateTimeField()
    class Meta:
        model = Order
        fields = ['id','customer_id','placed_at','payment_status','items']

class CreateOrderSerializer(serializers.Serializer):
    # get cart id and create order with that cart id
    # then take cart items from card id comes with request
    # then against each cart item create an order item
    # After creating ordertems delete the cart
    cart_id = serializers.UUIDField()
    def validate_cart_id(self,cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart with this id exists')
        if CartItem.objects.filter(cart_id=cart_id).count()==0:
            raise serializers.ValidationError('Cart is Empty')
        return cart_id

    def save(self, **kwargs):
        # If at any point our one or more queries throw exceptions
        # then our database will not updated, its only update when 
        # all querires run jus because of transaction.atomic
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = Customer.objects.get(user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer)

            cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)

            order_items = [
                OrderItem(
                order = order,
                product = item.product,
                unit_price = item.product.unit_price,
                quantity = item.quantity

                ) for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(id = cart_id).delete()
            return order
        
class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']