
from .models import Order, OrderDetails


def orders_cart_obj(request):
        try:
            # Seuls les utilisateurs authentifiés peuvent avoir un panier
            if request.user.is_authenticated and not request.user.is_anonymous:
                cart = Order.objects.all().filter(user = request.user, is_finished=False).first()
            else:    
                cart = None
            
        except:
                cart = None
                
        if cart:
            order_context = cart
            order_details_context = OrderDetails.objects.all().filter(order=order_context)
            cart_count = OrderDetails.objects.all().filter(order=order_context).count()

            return {
                'order_context': order_context,
                "order_details_context": order_details_context,
                "cart_count":cart_count,
            }
        else:
            return{
                "order_context": "None",
                "cart_count":0,

            }
