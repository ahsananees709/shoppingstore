
from django.shortcuts import render
from django.db.models import Q,Value,F,Func,ExpressionWrapper,DecimalField
from django.db.models.functions import Concat
from django.db.models.aggregates import Count,Min,Max,Avg,Sum
from django.core.exceptions import ViewDoesNotExist
from store.models import Product,Customer,Collection,Order,OrderItem
# Create your views here.

def start_app(request):
    # products = Product.objects.filter(inventory__lt = 10)
    # products = Product.objects.filter(inventory__lt = 10).filter(unit_price__lt = 20)
    # products = Product.objects.filter(Q(inventory__lt = 10) | Q(unit_price__lt = 20))
    # products = Product.objects.filter(id__in = OrderItem.objects.values('product_id').distinct()).order_by('title')
    # products = Product.objects.values('title')
    # products = Order.objects.select_related('customer').prefetch_related('orderitem_set__product').order_by('-placed_at')[:5]
    # customers = Customer.objects.filter(email__icontains = '.com')
    # collections = Collection.objects.filter(featured_product__isNull = True)
    # orders = Order.objects.filter(customer = 1)
    # order_items = OrderItem.objects.filter(product__collection__id = 3)
    # Aggregation Queries
    # products = Product.objects.filter(collection__id=3).aggregate(count = Count('id'),min_price = Min('unit_price'))
    # orders = Order.objects.aggregate(number_of_orders = Count('id'))
    # orders = OrderItem.objects.filter(product__id = 1).aggregate(Sum('inventory'))
    # orders = Order.objects.filter(customer__id = 1).aggregate(Count('id'))
    # products = Product.objects.filter(collection__id = 3).aggregate(Count('id'),Min('unit_price'),Max('unit_price'),Avg('unit_price'))
    # Annotate Queries(When we want to add a new field while querying)
    # products = Product.objects.annotate(is_new = Value(True))
    # products = Product.objects.annotate(new_id = F('id') +1)
    # DataBase Functions
    # customers = Customer.objects.annotate(
    #     # full_name = Func(F('first_name'),Value(' '),F('last_name'),function = 'CONCAT')
    #     full_name = Concat('first_name',Value(' '),'last_name')
    # )
    # Grouping Data
    # customers = Customer.objects.annotate(
    #     order_count = Count('order')
    # )
    # ExpressionWrapper
    # products = Product.objects.annotate(
    #     discounted_price=ExpressionWrapper(
    #     F('unit_price') * 0.8,
    #     output_field=DecimalField()
    # )
    # Add Object
    # collection = Collection()
    # collection.title = 'New'
    # collection.featured_product = Product(1)
    # collection.save()
    # Update Object
    # collection = Collection.objects.get(pk=11)
    # collection.title = 'Update'
    # collection.save()
    # Delete Object
    Collection.objects.filter(pk=11).delete()
# )
    # print(products)
    return render(request, 'home.html', {'name': 'Ahsan','products':list(products)})
