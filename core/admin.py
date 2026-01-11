from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, Category, Product, Order, OrderItem, Payment,
    BlogPost, CartItem, PizzaSizePrice
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'location', 'is_active', 'edit_link', 'delete_link')
    list_filter = ('role', 'location', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    actions = ['block_users', 'unblock_users']

    def block_users(self, request, queryset):
        updated = queryset.filter(role='employee').update(is_active=False)
        self.message_user(request, f"{updated} employee(s) blocked.")
    block_users.short_description = "Block selected employees"

    def unblock_users(self, request, queryset):
        updated = queryset.filter(role='employee').update(is_active=True)
        self.message_user(request, f"{updated} employee(s) unblocked.")
    unblock_users.short_description = "Unblock selected employees"

    def edit_link(self, obj):
        return format_html('<a class="button" href="{}">Edit</a>', f'/admin/core/user/{obj.id}/change/')
    edit_link.short_description = 'Edit'

    def delete_link(self, obj):
        return format_html('<a class="button" href="{}">Delete</a>', f'/admin/core/user/{obj.id}/delete/')
    delete_link.short_description = 'Delete'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'employee', 'status', 'total_amount', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('customer__email', 'employee__email')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'food_item', 'quantity', 'price')
    list_filter = ('order__customer',)  # Filter by customer in order
    search_fields = ('food_item__name', 'order__customer__email')  # Search food items or customer email


from django.contrib import admin
from .models import Payment

from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_email',
        'payment_method',
        'amount',
        'status',
        'created_at',
    )

    def customer_email(self, obj):
        return obj.user.email

    customer_email.short_description = 'Customer'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'quantity', 'added_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')


class PizzaSizePriceInline(admin.TabularInline):
    model = PizzaSizePrice
    extra = 3  # Small, Medium, Large


from django.contrib import admin
from .models import Product
from decimal import Decimal

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'availability_status')
    list_editable = ('price', 'stock', 'availability_status')

    def save_model(self, request, obj, form, change):
        # ✅ FORCE Decimal
        obj.price = Decimal(str(obj.price))
        super().save_model(request, obj, form, change)

