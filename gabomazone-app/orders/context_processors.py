
from .models import Order, OrderDetails


def orders_cart_obj(request):
        try:
            if request.user.is_authenticated and not request.user.is_anonymous:
                cart = Order.objects.all().filter(user = request.user, is_finished=False).first()
            else:    
                cart_id = request.session.get('cart_id')                     
                cart = Order.objects.all().filter(id = cart_id, is_finished=False)
            
        except:
                cart =False  
        if cart:
            if request.user.is_authenticated and not request.user.is_anonymous:
                order_context = Order.objects.filter(
                    user = request.user, is_finished=False).first()
            else:    
                order_context = Order.objects.get(
                    id = cart_id, is_finished=False)
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
