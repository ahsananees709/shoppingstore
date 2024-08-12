from typing import Any
from django.contrib import admin,messages
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils.html import format_html,urlencode
from django.urls import reverse
from django.http.request import HttpRequest
from . import models

class InventoryFilter(admin.SimpleListFilter):
    title = 'Inventory'
    parameter_name = 'Inventory'

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[Any, str]]:
        return [('<10','Low')]
    
    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        if self.value() == '<10':
            return queryset.filter(inventory__lt = 10)

# class TagInline(GenericTabularInline):
#     model = TaggedItem
#     autocomplete_fields = ['tag']

class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    readonly_fields = ['thumbnail']

    def thumbnail(self,instance):
        if instance.image.name != '':
            return format_html(f'<img src="{instance.image.url}" class="thumbnail">')
        return ''



@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    autocomplete_fields = ['collection']
    prepopulated_fields = {'slug':['title']}
    actions = ['clear_inventory']
    # inlines = [ProductImageInline]
    list_display = ['title','unit_price','inventory_status','collection_title']
    list_editable = ['unit_price']
    list_per_page = 10
    list_select_related = ['collection']
    list_filter = ['collection__title','last_update',InventoryFilter]
    search_fields = ['product']


    @admin.display(ordering='inventory')
    def inventory_status(self,product):
        if product.inventory < 10:
            return 'LOW'
        else:
            return 'OK'
    @admin.display(ordering='title')  
    def collection_title(self,product):
        return product.collection.title
    
    @admin.action(description="Clear Inventory")
    def clear_inventory(self,request,queryset):
        updated_count = queryset.update(inventory = 0)
        self.message_user(
            request,
            f"{updated_count} products inventory were updated.",
            messages.SUCCESS
        )
    class Media:
         css = {
            "all": ["store/styles.css"],
        }

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','membership','orders_count']
    list_select_related = ['user']
    ordering = ['user__first_name','user__last_name']
    list_editable = ['membership']
    autocomplete_fields = ['user']
    list_per_page = 10
    search_fields = ['user__first_name__istartswith','user__last_name__istartswith']

    @admin.display(ordering='orders_count')
    def orders_count(self,customer):
        return customer.orders_count
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            orders_count = Count('order')
        )

@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title','products_count']
    search_fields = ['title']

    @admin.display(ordering='products_count')
    def products_count(self,collection):
        # admin:app_modal_list
        url = (reverse('admin:store_product_changelist')
               + "?"
               + urlencode(
                   {'collection__id' : str(collection.id)}
               ) )
        return format_html('<a href="{}">{}<a>',url,collection.products_count)

    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            products_count = Count('product')
        )
    
class OrderItemInline(admin.StackedInline):
    model = models.OrderItem
    min_num = 1
    max_num = 1
    autocomplete_fields = ['product']
    extra = 0
    

@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['payment_status','customer_title']
    autocomplete_fields = ['customer']
    list_select_related = ['customer']
    inlines = [OrderItemInline]

    @admin.display(ordering='customer__first_name')
    def customer_title(self,order):
        return order.customer.first_name + ' ' + order.customer.last_name

