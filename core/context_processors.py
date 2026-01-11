from .models import CartItem

def cart_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(customer=request.user).count()
    else:
        count = 0
    return {'cart_count': count}
