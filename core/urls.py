from django.urls import path
from . import views
from django.contrib import admin
from .views import employee_dashboard
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),
    # path('admin/', admin.site.urls),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:product_id>/', views.update_cart_ajax, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_cart_ajax, name='remove_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('cart/', views.cart_view, name='cart'),
    path('payment/', views.payment, name='payment'),
    path('order-success/<str:order_id>/', views.order_success, name='order_success') ,
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('help-center/', views.help_center, name='help_center'),
    path('how-to-buy/', views.how_to_buy, name='how_to_buy'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('faq/', views.faq, name='faq'),    
    path('blog/', views.blog, name='blog'),
    path('blog/delete/<int:post_id>/', views.delete_blog_post, name='delete_blog_post'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('returns-refunds/', views.returns_refunds, name='returns_refunds'),
    path('checkout/address/', views.checkout_address, name='checkout_address'),
    path('checkout/payment/', views.checkout_payment, name='checkout_payment'),
    path('order/success/', views.order_success, name='order_success'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)