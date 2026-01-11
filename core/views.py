from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required,user_passes_test
from decimal import Decimal
from django.utils import timezone
from .models import User, Product, Category, CartItem, Order, OrderItem, Payment
from django.utils import translation
from .forms import BlogPostForm
from .models import BlogPost  # NOT blogpost (capitalization matters!)
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from .models import DeliveryAddress
from decimal import Decimal
from .models import Payment, Order, DeliveryAddress
from django.utils import timezone
from bson import ObjectId
from django.contrib import messages

def home(request):
    lang = request.GET.get('lang')
    if lang in ['en', 'ur']:
        translation.activate(lang)
        request.session[translation.LANGUAGE_SESSION_KEY] = lang

    categories = ['prathas', 'biryani', 'pizza', 'shawarma', 'tea', 'burger', 'desserts', 'asian food', 'drinks']
    selected_category = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_option = request.GET.get('sort')  # New: Read sort option

    products = Product.objects.all()

    if selected_category:
        products = products.filter(category__name__iexact=selected_category)

    if search_query:
        products = products.filter(name__icontains=search_query)

    # Apply sorting based on sort_option
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    elif sort_option == 'newest':
        products = products.order_by('-id')  # or use created_at if you have that field

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'sort_option': sort_option,  # Pass to template to retain selected option
    }
    return render(request, 'core/home.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    pid = str(product_id)
    qty = cart.get(pid, 0)

    if qty >= product.stock:
        return JsonResponse({'success': False, 'message': 'Not enough stock'})

    cart[pid] = qty + 1
    request.session['cart'] = cart

    return JsonResponse({
        'success': True,
        'cart_count': sum(cart.values())
    })


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # Role-based redirect
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'employee':
                return redirect('employee_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'core/login.html')

from django.contrib.auth import authenticate
def register_view(request):
    if request.method == 'POST':
        picture = request.FILES.get('picture')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        location = request.POST.get('location')

        if role == 'employee':
            admin_user = authenticate(request, email=request.POST.get('admin_email'), password=request.POST.get('admin_password'))
            if not admin_user or admin_user.role != 'admin':
                messages.error(request, 'Admin credentials are invalid or unauthorized.')
                return render(request, 'core/register.html')

        if location not in [loc[0] for loc in User.LOCATION_CHOICES]:
            messages.error(request, 'Invalid location selected.')
            return render(request, 'core/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                location=location,
                picture=picture  # ✅ Fix: This line saves the uploaded image
            )
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    return render(request, 'core/register.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@staff_member_required
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_customers = User.objects.filter(role='customer').count()
    products = Product.objects.all()

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_customers': total_customers,
        'products': products
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')

    cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        price = Decimal(str(product.price))  # Convert product price to Decimal
        item_total = price * quantity
        total_price += item_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total,
        })

    # Calculate total amount from orders for showing in dashboard (if needed)
    orders_total_amount = sum(Decimal(str(order.total_amount)) for order in orders)

    context = {
        'orders': orders,
        'cart_items': cart_items,
        'total_price': total_price,
        'orders_total_amount': orders_total_amount,  # Pass this if you want to show total orders value
    }

    return render(request, 'core/customer_dashboard.html', context)
@login_required
def payment(request):
    user = request.user
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    cart_items = []
    total_price = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        price_decimal = Decimal(str(product.price))
        item_total = price_decimal * quantity
        total_price += item_total
        cart_items.append({
            'id': product.id,  
            'product': product,
            'quantity': quantity,
            'total': item_total,
        })

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return render(request, "core/payment_form.html", {'cart_items': cart_items, 'total_price': total_price})

        order = Order.objects.create(
            customer=user,
            payment_status='pending',
            payment_method=payment_method,
            status='pending',
            total_amount=total_price,
            delivery_date=timezone.now() 
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                food_item=item['product'],
                quantity=item['quantity'],
                price=Decimal(str(item['product'].price)),  # convert price to Decimal here too
            )
            order.payment_status = 'completed'  
            order.status = 'delivered'  # or 'delivered' as per your flow
            order.save()

        request.session['cart'] = {}

        messages.success(request, "Payment done successfully!")
        return redirect('order_success')

    return render(request, "core/payment_form.html", {'cart_items': cart_items, 'total_price': total_price})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    items = order.items.all()
    address = DeliveryAddress.objects.filter(user=request.user).last()

    # Delivery time text
    remaining = order.delivery_date - timezone.now()
    minutes = max(int(remaining.total_seconds() // 60), 0)
    hours = minutes // 60
    minutes = minutes % 60

    if hours > 0:
        delivery_text = f"{hours} hours {minutes} minutes"
    else:
        delivery_text = f"{minutes} minutes"

    context = {
        'order': order,
        'items': items,
        'address': address,
        'delivery_text': delivery_text,
    }

    return render(request, 'core/order_success.html', context)

@login_required
def employee_dashboard(request):
    if request.user.role != 'employee' and not request.user.is_staff:
        return redirect('home')

    orders = Order.objects.all().select_related('customer').prefetch_related('items__food_item')

    context = {
        'orders': orders
    }
    return render(request, 'core/employee_dashboard.html', context)


from django.shortcuts import render

def help_center(request):
    return render(request, 'core/help_center.html')

def how_to_buy(request):
    return render(request, 'core/how_to_buy.html')

def contact_us(request):
    return render(request, 'core/contact_us.html')

def returns_refunds(request):
    return render(request, 'core/returns_refunds.html')

from django.urls import reverse

from django.shortcuts import redirect
from django.urls import reverse

def subscribe_newsletter(request):
    if request.method == "POST":
        # Your subscription logic here (e.g. save email, etc.)
        
        # After processing, redirect somewhere (e.g. homepage)
        return redirect('home')  # or use: HttpResponseRedirect(reverse('home'))
    
    # If request is not POST, redirect somewhere or return a response
    return redirect('home')

def faq(request):
    # Your logic here, e.g. render a FAQ page
    return render(request, 'core/faq.html')

# core/views.py

from .models import BlogPost

def blog(request):
    posts = BlogPost.objects.all().order_by('-created_at')  # latest first
    return render(request, 'core/blog.html', {'posts': posts})

def create_blog(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('blog')  # blog list page
    else:
        form = BlogPostForm()
    return render(request, 'core/create_blog.html', {'form': form})



# Only admin allowed
@user_passes_test(lambda u: u.is_superuser)
def delete_blog_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.delete()
    return redirect('blog')  # Redirect to blog list after deletion

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    requested_qty = int(request.POST.get('quantity', 1))
    
    if requested_qty > product.quantity:
        messages.error(request, f"Sorry, only {product.quantity} units of {product.name} are available.")
        # Redirect back or to the order page, no order processed
        return redirect('order_page')  # replace 'order_page' with your actual URL name
    
    # If enough quantity is available, process the order
    product.quantity -= requested_qty
    product.save()
    
    messages.success(request, "Order and Payment Successful! Thank you for your order.")
    return redirect('success_page')  # replace with your success URL

from datetime import timedelta

DELIVERY_TIMES = {
    "kahuta": timedelta(hours=2),       # 2 hours
    "islamabad": timedelta(hours=4),    # 4 hours
    "lahore": timedelta(hours=6),       # 6 hours
    "karachi": timedelta(hours=8),      # 8 hours
    "multan": timedelta(hours=5),       # 5 hours
    "other": timedelta(hours=10),       # 10 hours default
}

def get_delivery_time_delta(location):
    return DELIVERY_TIMES.get(location.lower(), DELIVERY_TIMES['other'])
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages

def place_order(request):
    user = request.user
    delivery_location = user.location
    delivery_time_delta = get_delivery_time_delta(delivery_location)
    
    print(f"Delivery time delta: {delivery_time_delta}")  # Debug print
    
    order = Order.objects.create(
        customer=user,
        status='pending',
        payment_status='pending',
    )
    
    delivery_date = order.order_date + delivery_time_delta
    order.delivery_date = delivery_date
    order.save()
    
    hours = delivery_time_delta.seconds // 3600
    minutes = (delivery_time_delta.seconds % 3600) // 60
    
    messages.success(
        request,
        f"Order and Payment Successful! Thank you for your order. Estimated delivery time: {hours} hours {minutes} minutes."
    )
    return redirect('order_success')

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required  # Only staff/superuser can access
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from core.models import User, Order

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from decimal import Decimal
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    query = request.GET.get("q", "")
    employees = User.objects.filter(role='employee')
    customers = User.objects.filter(role='customer')
    if query:
        employees = employees.filter(Q(first_name__icontains=query) | Q(email__icontains=query))
        customers = customers.filter(Q(first_name__icontains=query) | Q(email__icontains=query))

    orders = Order.objects.select_related('customer').all()
    total_orders = orders.count()
    total_revenue = sum(Decimal(str(order.total_amount)) for order in orders if order.total_amount is not None)

    return render(request, 'core/admin_dashboard.html', {
        'employees': employees,
        'customers': customers,
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    })
from django.http import HttpResponseRedirect
from django.http import HttpResponse

def edit_user(request, user_id):
    # Add your user edit logic or form here
    return HttpResponse(f"Edit user {user_id}")

def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.delete()
    return redirect('admin_dashboard')

def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # render detailed view template if needed
    return HttpResponse(f"Order #{order.id} for {order.customer.email}")

def delete_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.delete()
    return redirect('admin_dashboard')



@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0')

    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        price = Decimal(str(product.price))
        subtotal = price * qty
        total += subtotal

        cart_items.append({
            'product': product,
            'qty': qty,
            'subtotal': subtotal,
        })

    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

@login_required
def update_cart_ajax(request, product_id):
    cart = request.session.get('cart', {})
    action = request.POST.get('action')
    pid = str(product_id)

    if pid in cart:
        if action == 'plus':
            cart[pid] += 1
        elif action == 'minus' and cart[pid] > 1:
            cart[pid] -= 1

    request.session['cart'] = cart

    product = get_object_or_404(Product, id=product_id)
    price = Decimal(str(product.price))
    subtotal = price * cart.get(pid, 0)

    # calculate grand total
    total = Decimal('0')
    for p, q in cart.items():
        prod = get_object_or_404(Product, id=p)
        total += Decimal(str(prod.price)) * q

    return JsonResponse({
        'qty': cart.get(pid, 0),
        'subtotal': str(subtotal),
        'total': str(total),
        'cart_count': sum(cart.values())
    })


@login_required
def remove_cart_ajax(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart

    total = 0.0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        total += float(product.price) * qty


    return JsonResponse({
        'success': True,
        'total': str(total),
        'cart_count': sum(cart.values())
    })

from bson import ObjectId
@login_required
def checkout_address(request):
    if request.method == 'POST':
        try:
            # Data extraction
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            address_text = request.POST.get('address')
            city = request.POST.get('city')
            address_type = request.POST.get('address_type')

            # Create address
            address = DeliveryAddress.objects.create(
                user=request.user,
                name=name,
                phone=phone,
                email=email,
                address=address_text,
                city=city,
                address_type=address_type
            )

            # Store in session
            request.session['selected_address_id'] = str(address.id)
            request.session.modified = True

            # messages.success(request, "Address saved successfully!")
            return redirect('checkout_payment') # Ensure this name matches urls.py

        except Exception as e:
            messages.error(request, f"Error saving address: {e}")
            return redirect('checkout_address')

    return render(request, 'core/checkout_address.html')


@login_required
def checkout_payment(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Cart is empty")
        return redirect('cart')

    total = Decimal('0.00')
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=pid)
        total += Decimal(str(product.price)) * qty

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        if not method:
            messages.error(request, "Select payment method")
            return redirect('checkout_payment')

        # 1. Address nikalne ka sab se asaan tareeka (Last Saved Address)
        # Agar session wala ID fail ho jaye, toh hum user ka latest address utha lein gay
        address_id = request.session.get('selected_address_id')
        
        address = None
        if address_id:
            try:
                # Pehle koshish karein session ID se dhoondne ki
                address = DeliveryAddress.objects.filter(id=address_id, user=request.user).first()
            except:
                address = None

        if not address:
            # AGAR session ID kaam na kare, toh user ka sab se latest address khud utha lo
            address = DeliveryAddress.objects.filter(user=request.user).last()

        if not address:
            messages.error(request, "Please add delivery address")
            return redirect('checkout_address')

        # 2. City logic fix (Default time agar city list mein na ho)
        city = address.city.strip().lower()
        # Default 2 hours agar city match na ho
        delivery_delta = DELIVERY_TIME_BY_CITY.get(city, timedelta(hours=2))

        # 3. Order Create karein
        order = Order.objects.create(
            customer=request.user,
            total_amount=total,
            payment_method=method,
            payment_status='completed',
            status='pending',
            order_date=timezone.now(),
            is_new=True,
            delivery_date=timezone.now() + delivery_delta
        )

        # 4. Items save karein aur stock kam karein
        for pid, qty in cart.items():
            product = get_object_or_404(Product, id=pid)
            product.stock = max(product.stock - qty, 0)
            product.save()

            OrderItem.objects.create(
                order=order,
                food_item=product,
                quantity=qty,
                price=Decimal(str(product.price))
            )

        # 5. Payment Record
        Payment.objects.create(
            user=request.user,
            order=order,
            payment_method=method,
            amount=total,
            status='success'
        )

        # 6. Session clear karein aur SUCCESS page par bhejein
        request.session['cart'] = {}
        request.session.pop('selected_address_id', None)

        # messages.success(request, "Order placed successfully!")
        return redirect('order_success', order_id=str(order.id)) # order_id string mein bhejein

    return render(request, 'core/checkout_payment.html', {'total': total})
from datetime import timedelta

DELIVERY_TIME_BY_CITY = {
    'kahuta': timedelta(minutes=45),
    'islamabad': timedelta(hours=2),
    'rawalpindi': timedelta(hours=2),
    'murree': timedelta(hours=3),
    'lahore': timedelta(hours=6),
    'multan': timedelta(hours=8),
    'karachi': timedelta(hours=12),
}
def get_delivery_time(city):
    return DELIVERY_TIME_BY_CITY.get(city.lower())


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product, ProductRating

@login_required
def rate_product(request):
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        rating = int(request.POST.get('rating'))

        product = Product.objects.get(id=product_id)

        ProductRating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating}
        )

        return JsonResponse({
            'success': True,
            'average_rating': product.average_rating()
        })

    return JsonResponse({'success': False})
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status

        if new_status != 'pending':
            order.is_new = False   # NEW badge remove

        # 👇 SIRF ye fields update hongi — Decimal error khatam
        order.save(update_fields=['status', 'is_new'])

    return redirect('employee_dashboard')

