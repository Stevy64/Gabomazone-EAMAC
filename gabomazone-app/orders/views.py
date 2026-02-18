from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderDetails, Payment, Coupon, Country, OrderSupplier, OrderDetailsSupplier, Province, B2CDeliveryVerification
from products.models import Product
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Context, Decimal, InvalidOperation
from accounts.models import Profile
from settings.models import SiteSetting, ContactInfo
from urllib.parse import quote
import re
# from django.contrib.messages.storage import session
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.http import HttpResponseRedirect
from django.views import View
from django.views.decorators.http import require_http_methods
import datetime
# from django_countries import countries as allcountries  # Plus utilisé, on travaille uniquement au Gabon
from .utils import code_generator
from django.db.models import Sum

ts = datetime.datetime.now().timestamp()
time = round(ts * 1000)


def safe_decimal_price(price_value, max_digits=10, decimal_places=2):
    """
    Convertit un prix (float, int, str, Decimal ou None) en Decimal de manière sécurisée.
    Retourne Decimal('0') si la valeur est None ou invalide.
    Valide que la valeur respecte les contraintes max_digits et decimal_places.
    """
    if price_value is None:
        return Decimal('0')
    try:
        if isinstance(price_value, Decimal):
            decimal_value = price_value
        else:
            # Convertir en string puis en Decimal pour éviter les problèmes de précision float
            decimal_value = Decimal(str(price_value))
        
        # Vérifier que la valeur n'est pas NaN ou Infinity
        if decimal_value.is_nan() or decimal_value.is_infinite():
            return Decimal('0')
        
        # Quantifier pour respecter decimal_places
        # Utiliser un contexte avec une précision suffisante
        quantize_value = Decimal('1') / (Decimal('10') ** decimal_places)
        # Utiliser le contexte par défaut avec arrondi
        try:
            return decimal_value.quantize(quantize_value)
        except InvalidOperation:
            # Si la quantification échoue, essayer avec un contexte explicite
            context = Context(prec=28, rounding='ROUND_HALF_UP')
            return decimal_value.quantize(quantize_value, context=context)
    except (ValueError, TypeError, InvalidOperation) as e:
        print(f"Erreur dans safe_decimal_price: {e}, valeur: {price_value}")
        # En cas d'erreur, retourner 0 plutôt que de planter
        return Decimal('0')


@login_required(login_url='accounts:login')
def add_to_cart(request):
    try:
        if not request.session.has_key('currency'):
            request.session['currency'] = settings.DEFAULT_CURRENCY

        # Détecter si c'est une requête AJAX
        is_ajax = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            'application/json' in request.headers.get('Accept', '') or
            request.headers.get('Content-Type') == 'application/json'
        )

        if "qyt" in request.POST and "product_id" in request.POST and "product_Price" in request.POST:

            product_id = request.POST['product_id']
            qyt = int(request.POST['qyt'])
            size = None
            try:
                size = request.POST['name_variation']
            except:
                size = None

            # Vérifier si c'est un article C2C
            is_peer_to_peer = str(product_id).startswith('peer_')
            
            # Initialiser les variables
            product = None
            peer_product = None
            
            if is_peer_to_peer:
                # Extraire l'ID réel (après "peer_")
                from accounts.models import PeerToPeerProduct
                try:
                    # Gérer le cas où product_id pourrait déjà avoir "peer_" ou être juste un ID
                    # Enlever tous les préfixes "peer_" possibles (gérer les cas "peer_1", "peer_peer_1", etc.)
                    peer_id_str = str(product_id)
                    while peer_id_str.startswith('peer_'):
                        peer_id_str = peer_id_str.replace('peer_', '', 1)
                    peer_id = int(peer_id_str)
                    peer_product = PeerToPeerProduct.objects.get(id=peer_id, status=PeerToPeerProduct.APPROVED)
                    product = None  # S'assurer que product est None pour les articles C2C
                except (ValueError, PeerToPeerProduct.DoesNotExist):
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'Article C2C introuvable ou non approuvé.'}, status=404)
                    messages.error(request, 'Article C2C introuvable ou non approuvé.')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else:
                # Produit normal
                try:
                    product_id_int = int(product_id)
                except (ValueError, TypeError):
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'ID de produit invalide.'}, status=400)
                    messages.error(request, 'ID de produit invalide.')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                
                product = Product.objects.get(id=product_id_int)

            # Vérifier que le produit a un prix valide
            product_price = peer_product.PRDPrice if peer_product else (product.PRDPrice if product else None)
            if product_price is None or product_price <= 0:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Ce produit n\'a pas de prix valide !'}, status=400)
                messages.warning(request, 'Ce produit n\'a pas de prix valide !')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

            # Pour les articles C2C, on ne vérifie pas le stock (disponibilité = 1 par défaut)
            if not is_peer_to_peer:
                if qyt <= 0 and product.available == 0:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'Ce produit est en rupture de stock !'}, status=400)
                    messages.warning(request, 'Ce produit est en rupture de stock !')
                    return redirect('orders:cart')

                if product.available < qyt and product.available == 0:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'Ce produit est en rupture de stock !'}, status=400)
                    messages.warning(request, 'Ce produit est en rupture de stock !')
                    return redirect('orders:cart')

                if qyt <= 0 and product.available != 0:
                    qyt = 1

                if product.available < qyt and product.available != 0:
                    qyt = product.available
            else:
                # Pour les articles C2C, quantité minimum = 1
                if qyt <= 0:
                    qyt = 1

            try:
                # Utilisateur doit être authentifié (décorateur @login_required)
                order = Order.objects.filter(
                    user=request.user, is_finished=False).first()
                print("order: ", order)

            except Exception as e:
                print(f"Erreur lors de la récupération de la commande: {e}")
                order = None

            # Vérifier que le produit existe (normal ou C2C)
            if not is_peer_to_peer and not Product.objects.all().filter(id=product_id).exists():
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Produit non trouvé !'}, status=404)
                return HttpResponse(f"this product not found !")

            if order:
                if request.user.is_authenticated and not request.user.is_anonymous:
                    # Utilisateur doit être authentifié (décorateur @login_required)
                    old_orde = Order.objects.filter(
                        user=request.user, is_finished=False).first()
                
                if not old_orde:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'Erreur: Commande non trouvée'}, status=400)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
                # old_orde_supplier = OrderSupplier.objects.get(
                #     user=request.user, is_finished=False, order=old_orde)
                # print("old_orde_supplier:", old_orde_supplier)
                # Chercher l'item dans OrderDetails (produit normal ou C2C)
                if is_peer_to_peer:
                    item = OrderDetails.objects.filter(order=old_orde, peer_product=peer_product).first()
                else:
                    item = OrderDetails.objects.filter(order=old_orde, product=product).first()
                
                if item:
                    # Vérifier si OrderDetailsSupplier existe, sinon le créer
                    # Seulement si le produit a un vendeur (product_vendor) - pas pour les articles C2C
                    if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                        if OrderDetailsSupplier.objects.all().filter(order=old_orde, product=product).exists():
                            item_supplier = OrderDetailsSupplier.objects.get(
                                order=old_orde, product=product)
                        else:
                            # Créer OrderDetailsSupplier si il n'existe pas
                            try:
                                old_order_supplier = OrderSupplier.objects.get(
                                    is_finished=False, order=old_orde, vendor=product.product_vendor)
                            except OrderSupplier.DoesNotExist:
                                old_order_supplier = OrderSupplier.objects.create(
                                    user=request.user if request.user.is_authenticated else None,
                                    order=old_orde,
                                    vendor=product.product_vendor,
                                    is_finished=False
                                )
                            item_supplier = OrderDetailsSupplier.objects.create(
                                supplier=product.product_vendor.user,
                                product=product,
                                order=old_orde,
                                order_supplier=old_order_supplier,
                                order_details=item,
                                price=safe_decimal_price(product.PRDPrice),
                                quantity=item.quantity,
                                size=size if hasattr(item, 'size') else None,
                                weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                            )
                    else:
                        # Si le produit n'a pas de vendeur ou c'est un article C2C, on ne crée pas OrderDetailsSupplier
                        item_supplier = None
                    # for i in items:
                    # Vérifier le stock seulement pour les produits normaux
                    if not is_peer_to_peer and product and item.quantity >= product.available:
                        qyt = item.quantity
                        # i.quantity = int(qyt)
                        # i.save()
                        if is_ajax:
                            return JsonResponse({'success': False, 'error': f"Vous ne pouvez pas ajouter plus de ce produit, disponible seulement : {qyt}"}, status=400)
                        messages.warning(
                            request, f"You can't add more from this product, available only : {qyt}")
                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                    elif is_peer_to_peer or (product and qyt < product.available):
                        if not is_peer_to_peer and product:
                            qyt = qyt + item.quantity
                            if qyt > product.available:
                                qyt = product.available
                        else:
                            qyt = qyt + item.quantity

                        item.quantity = int(qyt)
                        item.save()
                        if item_supplier:
                            item_supplier.quantity = int(qyt)
                            item_supplier.save()

                        # code for total amount main order
                        order_details_main = OrderDetails.objects.all().filter(order=old_orde)
                        f_total = Decimal('0')
                        w_total = Decimal('0')
                        weight = Decimal('0')
                        for sub in order_details_main:
                            if sub.price and sub.quantity:
                                f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                            if sub.weight and sub.quantity:
                                w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                        total = f_total
                        weight = w_total

                        old_orde.sub_total = str(f_total)
                        old_orde.weight = float(weight)
                        old_orde.amount = str(total)
                        old_orde.save()

                        # code for total amount supplier order - seulement si le produit a un vendeur (pas pour les articles C2C)
                        if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                            try:
                                old_order_supplier = OrderSupplier.objects.get(
                                    is_finished=False, order=old_orde, vendor=product.product_vendor)
                                order_supplier = OrderDetailsSupplier.objects.all().filter(
                                    order_supplier=old_order_supplier)
                                weight = Decimal('0')
                                f_total = Decimal('0')
                                w_total = Decimal('0')
                                for sub in order_supplier:
                                    if sub.price and sub.quantity:
                                        f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                    if sub.weight and sub.quantity:
                                        w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                                total = f_total
                                weight = w_total
                                old_order_supplier.weight = float(weight)
                                old_order_supplier.amount = str(total)
                                old_order_supplier.save()
                            except OrderSupplier.DoesNotExist:
                                # Créer OrderSupplier si il n'existe pas
                                old_order_supplier = OrderSupplier.objects.create(
                                    user=request.user if request.user.is_authenticated else None,
                                    order=old_orde,
                                    vendor=product.product_vendor,
                                    is_finished=False
                                )
                                # Mettre à jour item_supplier avec le nouveau order_supplier
                                if item_supplier:
                                    try:
                                        item_supplier.order_supplier = old_order_supplier
                                        item_supplier.save()
                                    except:
                                        pass
                                # Calculer le total
                                order_supplier = OrderDetailsSupplier.objects.all().filter(
                                    order_supplier=old_order_supplier)
                                weight = Decimal('0')
                                f_total = Decimal('0')
                                w_total = Decimal('0')
                                for sub in order_supplier:
                                    if sub.price and sub.quantity:
                                        f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                    if sub.weight and sub.quantity:
                                        w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                                total = f_total
                                weight = w_total
                                old_order_supplier.weight = float(weight)
                                old_order_supplier.amount = str(total)
                                old_order_supplier.save()
                            except Exception as e:
                                if is_ajax:
                                    return JsonResponse({'success': False, 'error': f'Erreur lors de la mise à jour: {str(e)}'}, status=500)
                                messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
                                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                    # if i.size != size:
                    #     order_details = OrderDetails.objects.create(
                    #         supplier=product.product_vendor.user,
                    #         product=product,
                    #         order=old_orde,
                    #         price=product.PRDPrice,
                    #         quantity=qyt,
                    #         size=size,
                    #         weight=product.PRDWeight

                    #     )
                    #     break

                    else:
                        item.quantity = int(qyt)
                        # i.supplier = product.product_vendor.user
                        item.save()
                        # Vérifier si item_supplier existe avant de le mettre à jour - seulement si le produit a un vendeur (pas pour les articles C2C)
                        if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                            try:
                                item_supplier = OrderDetailsSupplier.objects.get(
                                    order=old_orde, product=product)
                                item_supplier.quantity = int(qyt)
                                item_supplier.save()
                            except OrderDetailsSupplier.DoesNotExist:
                                # Créer OrderDetailsSupplier si il n'existe pas
                                try:
                                    old_order_supplier = OrderSupplier.objects.get(
                                        is_finished=False, order=old_orde, vendor=product.product_vendor)
                                except OrderSupplier.DoesNotExist:
                                    old_order_supplier = OrderSupplier.objects.create(
                                        user=request.user if request.user.is_authenticated else None,
                                        order=old_orde,
                                        vendor=product.product_vendor,
                                        is_finished=False
                                    )
                                OrderDetailsSupplier.objects.create(
                                    supplier=product.product_vendor.user,
                                    product=product,
                                    order=old_orde,
                                    order_supplier=old_order_supplier,
                                    order_details=item,
                                    price=safe_decimal_price(product.PRDPrice),
                                    quantity=int(qyt),
                                    size=size if hasattr(item, 'size') else None,
                                    weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                                )

                        # code for total amount main order
                        order_details_main = OrderDetails.objects.all().filter(order=old_orde)
                        f_total = Decimal('0')
                        w_total = Decimal('0')
                        weight = Decimal('0')
                        for sub in order_details_main:
                            if sub.price and sub.quantity:
                                f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                            if sub.weight and sub.quantity:
                                w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                        total = f_total
                        weight = w_total

                        old_orde.sub_total = str(f_total)
                        old_orde.weight = float(weight)
                        old_orde.amount = str(total)
                        old_orde.save()

                        # code for total amount supplier order
                        try:
                            old_order_supplier = OrderSupplier.objects.get(
                                is_finished=False, order=old_orde, vendor=product.product_vendor)
                            order_supplier = OrderDetailsSupplier.objects.all().filter(
                                order_supplier=old_order_supplier)

                            f_total = Decimal('0')
                            w_total = Decimal('0')
                            weight = Decimal('0')
                            for sub in order_supplier:
                                if sub.price and sub.quantity:
                                    f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                if sub.weight and sub.quantity:
                                    w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                            total = f_total
                            weight = w_total
                            old_order_supplier.weight = float(weight)
                            old_order_supplier.amount = str(total)
                            old_order_supplier.save()
                        except OrderSupplier.DoesNotExist:
                            # Si OrderSupplier n'existe pas, le créer
                            old_order_supplier = OrderSupplier.objects.create(
                                user=request.user if request.user.is_authenticated else None,
                                order=old_orde,
                                vendor=product.product_vendor,
                                is_finished=False
                            )
                            # Récupérer ou créer OrderDetailsSupplier
                            try:
                                item_supplier = OrderDetailsSupplier.objects.get(
                                    order=old_orde, product=product)
                                item_supplier.order_supplier = old_order_supplier
                                item_supplier.save()
                            except OrderDetailsSupplier.DoesNotExist:
                                OrderDetailsSupplier.objects.create(
                                    supplier=product.product_vendor.user,
                                    product=product,
                                    order=old_orde,
                                    order_supplier=old_order_supplier,
                                    order_details=item,
                                    price=safe_decimal_price(product.PRDPrice),
                                    quantity=int(qyt),
                                    size=size if hasattr(item, 'size') else None,
                                    weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                                )
                            # Calculer le total
                            order_supplier = OrderDetailsSupplier.objects.all().filter(
                                order_supplier=old_order_supplier)
                            f_total = Decimal('0')
                            w_total = Decimal('0')
                            weight = Decimal('0')
                            for sub in order_supplier:
                                if sub.price and sub.quantity:
                                    f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                if sub.weight and sub.quantity:
                                    w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                            total = f_total
                            weight = w_total
                            old_order_supplier.weight = float(weight)
                            old_order_supplier.amount = str(total)
                            old_order_supplier.save()
                        
                        # Retourner une réponse JSON pour AJAX
                        if is_ajax:
                            from django.db.models import Sum
                            cart_count = OrderDetails.objects.filter(order=old_orde).aggregate(total=Sum('quantity'))['total'] or 0
                            return JsonResponse({'success': True, 'message': 'Produit ajouté au panier avec succès !', 'cart_count': cart_count})
                        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                else:
                    # Créer un nouvel OrderDetails
                    if is_peer_to_peer:
                        # Pour les articles C2C, pas de supplier
                        order_details = OrderDetails.objects.create(
                            supplier=None,
                            product=None,
                            peer_product=peer_product,
                            order=old_orde,
                            price=safe_decimal_price(peer_product.PRDPrice),
                            quantity=qyt,
                            size=size,
                            weight=Decimal('0')  # Pas de poids pour les articles C2C
                        )
                    else:
                        # Pour les produits normaux
                        supplier_user = product.product_vendor.user if (hasattr(product, 'product_vendor') and product.product_vendor) else None
                        order_details = OrderDetails.objects.create(
                            supplier=supplier_user,
                            product=product,
                            peer_product=None,
                            order=old_orde,
                            price=safe_decimal_price(product.PRDPrice),
                            quantity=qyt,
                            size=size,
                            weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                        )
                    # code for total amount main order

                    order_details_main = OrderDetails.objects.all().filter(order=old_orde)
                    weight = Decimal('0')
                    f_total = Decimal('0')
                    w_total = Decimal('0')
                    for sub in order_details_main:
                        if sub.price and sub.quantity:
                            f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                        if sub.weight and sub.quantity:
                            w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                    total = f_total
                    weight = w_total

                    old_orde.sub_total = str(f_total)
                    old_orde.weight = float(weight)
                    old_orde.amount = str(total)
                    old_orde.save()
                    # add product for old order supplier - seulement si le produit a un vendeur (pas pour les articles C2C)
                    if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                        if OrderSupplier.objects.all().filter(
                                order=old_orde, is_finished=False, vendor=product.product_vendor).exists():
                            old_order_supplier = OrderSupplier.objects.get(
                                is_finished=False, order=old_orde, vendor=product.product_vendor)
                            order_details_supplier = OrderDetailsSupplier.objects.create(
                                supplier=product.product_vendor.user,
                                product=product,
                                order=old_orde,
                                order_supplier=old_order_supplier,
                                order_details=order_details,
                                price=safe_decimal_price(product.PRDPrice),
                                quantity=qyt,
                                size=size,
                                weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                            )

                            # code for total amount supplier order
                            order__supplier = OrderDetailsSupplier.objects.all().filter(
                                order_supplier=old_order_supplier)
                            f_total = Decimal('0')
                            w_total = Decimal('0')
                            weight = Decimal('0')
                            for sub in order__supplier:
                                if sub.price and sub.quantity:
                                    f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                if sub.weight and sub.quantity:
                                    w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                            total = f_total
                            weight = w_total
                            old_order_supplier.weight = float(weight)
                            old_order_supplier.amount = str(total)
                            old_order_supplier.save()

                        else:
                            # order for  new supllier
                            new_order_supplier = OrderSupplier()
                            if request.user.is_authenticated and not request.user.is_anonymous:
                                new_order_supplier.user = request.user
                                new_order_supplier.email_client = request.user.email

                            new_order_supplier.vendor = product.product_vendor
                            new_order_supplier.order = old_orde
                            new_order_supplier.save()
                            order_details_supplier = OrderDetailsSupplier.objects.create(
                                supplier=product.product_vendor.user,
                                product=product,
                                order=old_orde,
                                order_supplier=new_order_supplier,
                                order_details=order_details,
                                price=safe_decimal_price(product.PRDPrice),
                                quantity=qyt,
                                size=size,
                                weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                            )

                            # code for total amount supplier order
                            order_supplier = OrderDetailsSupplier.objects.all().filter(
                                order_supplier=new_order_supplier)
                            weight = Decimal('0')
                            f_total = Decimal('0')
                            w_total = Decimal('0')
                            for sub in order_supplier:
                                if sub.price and sub.quantity:
                                    f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                if sub.weight and sub.quantity:
                                    w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                            total = f_total
                            weight = w_total
                            new_order_supplier.weight = float(weight)
                            new_order_supplier.amount = str(total)
                            new_order_supplier.save()

                messages.success(request, 'Produit ajouté au panier avec succès !')
                # return redirect('orders:cart')
                if is_ajax:
                    # Compter les articles dans le panier
                    try:
                        cart_count = OrderDetails.objects.filter(order=old_orde).count()
                    except:
                        cart_count = 0
                    return JsonResponse({'success': True, 'message': 'Produit ajouté au panier avec succès !', 'cart_count': cart_count})
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            else:
                # order for all
                new_order = Order()
                if request.user.is_authenticated and not request.user.is_anonymous:
                    new_order.user = request.user
                    new_order.email_client = request.user.email

                new_order.save()
                # will edite
                # new_order.supplier = product.product_vendor.user
                # new_order.vendors.add(product.product_vendor)

                # order for supllier - seulement si le produit a un vendeur (pas pour les articles C2C)
                if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                    new_order_supplier = OrderSupplier()
                    if request.user.is_authenticated and not request.user.is_anonymous:
                        new_order_supplier.user = request.user
                        new_order_supplier.email_client = request.user.email

                    new_order_supplier.vendor = product.product_vendor
                    new_order_supplier.order = new_order
                    new_order_supplier.save()

                # Créer OrderDetails
                if is_peer_to_peer:
                    order_details = OrderDetails.objects.create(
                        supplier=None,
                        product=None,
                        peer_product=peer_product,
                        order=new_order,
                        price=safe_decimal_price(peer_product.PRDPrice),
                        quantity=qyt,
                        size=size,
                        weight=Decimal('0')  # Pas de poids pour les articles C2C
                    )
                else:
                    order_details = OrderDetails.objects.create(
                        supplier=product.product_vendor.user if (hasattr(product, 'product_vendor') and product.product_vendor) else None,
                        product=product,
                        peer_product=None,
                        order=new_order,
                        price=safe_decimal_price(product.PRDPrice),
                        quantity=qyt,
                        size=size,
                        weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                    )

                # Créer OrderDetailsSupplier seulement si le produit a un vendeur (pas pour les articles C2C)
                if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor:
                    order_details_supplier = OrderDetailsSupplier.objects.create(
                        supplier=product.product_vendor.user,
                        product=product,
                        order=new_order,
                        order_supplier=new_order_supplier,
                        order_details=order_details,
                        price=safe_decimal_price(product.PRDPrice),
                        quantity=qyt,
                        size=size,
                        weight=safe_decimal_price(getattr(product, 'PRDWeight', 0))
                    )
                # code for total amount main order

                order_details_main = OrderDetails.objects.all().filter(order=new_order)
                f_total = Decimal('0')
                w_total = Decimal('0')
                weight = Decimal('0')
                for sub in order_details_main:
                    if sub.price and sub.quantity:
                        f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                    if sub.weight and sub.quantity:
                        w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                total = f_total
                weight = w_total

                new_order.sub_total = str(f_total)
                new_order.weight = float(weight)
                new_order.amount = str(total)
                new_order.save()
                # code for total amount supplier order - seulement si new_order_supplier existe (produits avec vendeur)
                if not is_peer_to_peer and product and hasattr(product, 'product_vendor') and product.product_vendor and 'new_order_supplier' in locals():
                    order_details__supplier = OrderDetailsSupplier.objects.all().filter(
                        order_supplier=new_order_supplier)
                    f_total = Decimal('0')
                    w_total = Decimal('0')
                    weight = Decimal('0')
                    for sub in order_details__supplier:
                        if sub.price and sub.quantity:
                            f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                        if sub.weight and sub.quantity:
                            w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                    total = f_total
                    weight = w_total
                    new_order_supplier.weight = float(weight)
                    new_order_supplier.amount = str(total)
                    new_order_supplier.save()
                request.session['cart_id'] = new_order.id
                messages.success(request, 'Produit ajouté au panier avec succès !')
                # return redirect('orders:cart')
                if is_ajax:
                    # Compter les articles dans le panier
                    try:
                        cart_count = OrderDetails.objects.filter(order=new_order).count()
                    except:
                        cart_count = 0
                    return JsonResponse({'success': True, 'message': 'Produit ajouté au panier avec succès !', 'cart_count': cart_count})
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Vous devez d\'abord vous connecter pour ajouter un produit au panier.', 'requires_login': True}, status=403)
            messages.warning(
                request, 'You must first log in to your account to purchase the product')
            return redirect('accounts:login')
    except Product.DoesNotExist:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Produit non trouvé !'}, status=404)
        messages.error(request, 'Produit non trouvé !')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    except InvalidOperation as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erreur Decimal dans add_to_cart: {str(e)}")
        print(f"Traceback: {error_trace}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Erreur de calcul lors de l\'ajout au panier. Veuillez réessayer.'}, status=500)
        messages.error(request, 'Erreur de calcul lors de l\'ajout au panier. Veuillez réessayer.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erreur dans add_to_cart: {str(e)}")
        print(f"Traceback: {error_trace}")
        if is_ajax:
            return JsonResponse({'success': False, 'error': f'Erreur lors de l\'ajout au panier: {str(e)}'}, status=500)
        messages.error(request, f'Erreur lors de l\'ajout au panier: {str(e)}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='accounts:login')
def cart(request):
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY

    if "code" in request.POST:
        now = timezone.now()
        code = request.POST['code']
        request.session['code'] = code
        coupon = None
        if Coupon.objects.all().filter(code=code, active=True):
            coupon = Coupon.objects.get(code=code, active=True)
            request.session['coupon_id'] = coupon.id
            messages.success(
                request, 'Code de réduction ajouté avec succès')

        else:
            messages.warning(
                request, 'Le code de réduction n\'est pas disponible ou a expiré')
            request.session['coupon_id'] = None
            # request.session['code'] = None
        return redirect('orders:cart')

    context = None
    # Plus de gestion des pays, on travaille uniquement au Gabon
    provinces = Province.objects.all()

    try:
        # Utilisateur doit être authentifié (décorateur @login_required)
        order_view = Order.objects.all().filter(
            user=request.user, is_finished=False).first()
        if order_view:
            request.session['cart_id'] = order_view.id
    except Exception as e:
        order_view = None

    if order_view:
        try:
            blance = Profile.objects.get(user=request.user).blance

        except:
            blance = 0

        if request.user.is_authenticated and not request.user.is_anonymous:
            order = Order.objects.filter(
                user=request.user, is_finished=False).first()
        else:
            order = Order.objects.get(id=cart_id, is_finished=False)

        order_details = OrderDetails.objects.all().filter(order=order)

        # Vérifier s'il y a des articles peer-to-peer dans le panier
        has_peer_products = order_details.filter(peer_product__isnull=False).exists()

        coupon_id = None
        value = None
        total = None
        weight = None
        code = None
        f_total = 0
        w_total = 0
        for sub in order_details:
            f_total += sub.price * sub.quantity
            w_total += sub.weight * sub.quantity
            total = f_total
            weight = w_total

        if request.session.get("coupon_id"):
            coupon_id = request.session.get("coupon_id")
            code = request.session.get("code")
            if Coupon.objects.all().filter(id=coupon_id):
                discount = Coupon.objects.get(id=coupon_id).discount
                value = (discount / Decimal("100")) * f_total
                total = f_total-value
                # print(total)

                # order = Order.objects.all().filter(user=request.user, is_finished=False)
                if order:
                    if request.user.is_authenticated and not request.user.is_anonymous:
                        old_orde = Order.objects.get(
                            user=request.user, is_finished=False)
                    else:
                        old_orde = Order.objects.get(
                            id=cart_id, is_finished=False)

                    old_orde.amount = total
                    old_orde.discount = value
                    old_orde.sub_total = f_total
                    # old_orde = weight
                    old_orde.coupon = Coupon.objects.get(id=coupon_id)
                    old_orde.save()

            # else:
            #     total = f_total
            #     coupon_id = None
        else:
            # total = f_total
            # coupon_id = None
            # Utilisateur doit être authentifié (décorateur @login_required)
            old_orde = Order.objects.get(
                user=request.user, is_finished=False)
            old_orde.amount = total
            old_orde.discount = 0
            old_orde.sub_total = f_total
            old_orde.weight = weight
            old_orde.coupon = None
            # if request.user.is_authenticated and not request.user.is_anonymous:
            #     old_orde.user = request.user
            #     old_orde.email_client = request.user.email
            old_orde.save()

            # print(total)

        # if "coupon_id" in request.session.keys():
        #     del request.session["coupon_id"]

        # Récupérer le profil utilisateur pour pré-remplir le formulaire
        profile = None
        if request.user.is_authenticated and not request.user.is_anonymous:
            try:
                profile = Profile.objects.get(user=request.user)
            except Profile.DoesNotExist:
                profile = None

        context = {
            "order": order,
            "order_details": order_details,
            "total": total,
            "f_total": f_total,
            "coupon_id": coupon_id,
            "value": value,
            "code": code,
            "blance": blance,
            "provinces": provinces,
            # "states": states,
            "weight": weight,
            "profile": profile,
            "has_peer_products": has_peer_products,
        }
    else:
        # Panier vide - définir un contexte minimal
        # Récupérer le profil utilisateur pour pré-remplir le formulaire
        profile = None
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None
        
        context = {
            "order_details": None,
            "provinces": provinces,
            "profile": profile,
            "has_peer_products": False,
        }
    return render(request, "orders/shop-cart.html", context)


class StatesJsonListView(View):
    def get(self, *args, **kwargs):
        # Pays fixé au Gabon uniquement
        country = 'GA'  # Code ISO du Gabon

        states = None
        provinces = Province.objects.all()
        # Plus de gestion des pays multiples, on travaille uniquement au Gabon
        states = [province.name_province for province in provinces]

        return JsonResponse({"success": True, "data": states}, safe=False)
        # return JsonResponse({"success": False, }, safe=False)


def remove_item(request, productdeatails_id):
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY

    # if request.user.is_authenticated and not request.user.is_anonymous and productdeatails_id:
    item_id = OrderDetails.objects.get(id=productdeatails_id)
    try:
        # Utilisateur doit être authentifié (décorateur @login_required)
        # Vérifier que l'item appartient à l'utilisateur connecté
        if item_id.order.user.id != request.user.id:
            messages.error(request, 'Vous n\'avez pas l\'autorisation de modifier cette commande.')
            return redirect('orders:cart')
        if item_id.order.id == order.id:
            # if item_id.order.user.id == request.user.id:
            item = OrderDetails.objects.all().filter(order_id=item_id.order_id).count()
            if item-1 == 0:
                # order = Order.objects.all().filter(user=request.user, is_finished=False)
                try:

                    # Utilisateur doit être authentifié (décorateur @login_required)
                    old_orde = order
                    old_orde.delete()
                    messages.warning(request, 'Produit supprimé du panier')
                    return redirect('orders:cart')
                except:
                    order_view = False
                if "coupon_id" in request.session.keys():
                    del request.session["coupon_id"]
                messages.warning(request, 'Commande supprimée')
                return redirect('orders:cart')
            else:
                # Recalculer les totaux avant de supprimer l'article
                all_orders = OrderDetails.objects.filter(order_id=item_id.order_id)
                f_total = Decimal('0')
                w_total = Decimal('0')
                weight = Decimal('0')
                for sub in all_orders:
                    if sub.price and sub.quantity:
                        f_total += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                    if sub.weight and sub.quantity:
                        w_total += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                total = f_total
                weight = w_total

                old_orde = Order.objects.get(id=cart_id, is_finished=False)
                old_orde.sub_total = str(f_total)
                old_orde.weight = float(weight)
                old_orde.amount = str(total)
                old_orde.save()

                # Vérifier si c'est un article C2C (pas de product_vendor)
                if item_id.peer_product:
                    # Pour les articles C2C, pas de OrderDetailsSupplier
                    item_id.delete()
                    messages.warning(request, 'Produit supprimé du panier')
                    return redirect('orders:cart')
                elif item_id.product and hasattr(item_id.product, 'product_vendor') and item_id.product.product_vendor:
                    # Pour les produits normaux avec vendeur, gérer OrderDetailsSupplier
                    try:
                        item_supplier = OrderDetailsSupplier.objects.get(order_details=item_id)
                        obj_order_supplier = OrderSupplier.objects.get(
                            is_finished=False, order=old_orde, vendor=item_id.product.product_vendor)

                        item_supplier_count = OrderDetailsSupplier.objects.filter(
                            order_supplier=obj_order_supplier).count()

                        if item_supplier_count == 1:
                            # C'est le dernier article de ce vendeur
                            obj_order_supplier.delete()
                            item_id.delete()
                            messages.warning(request, 'Produit supprimé du panier')
                            return redirect('orders:cart')
                        else:
                            # Il reste d'autres articles de ce vendeur
                            item_id.delete()
                            # Recalculer les totaux du vendeur
                            order_details__supplier = OrderDetailsSupplier.objects.filter(
                                order_supplier=obj_order_supplier)
                            f_total_supplier = Decimal('0')
                            w_total_supplier = Decimal('0')
                            for sub in order_details__supplier:
                                if sub.price and sub.quantity:
                                    f_total_supplier += Decimal(str(sub.price)) * Decimal(str(sub.quantity))
                                if sub.weight and sub.quantity:
                                    w_total_supplier += Decimal(str(sub.weight)) * Decimal(str(sub.quantity))
                            obj_order_supplier.weight = float(w_total_supplier)
                            obj_order_supplier.amount = str(f_total_supplier)
                            obj_order_supplier.save()
                            messages.warning(request, 'Produit supprimé du panier')
                            return redirect('orders:cart')
                    except OrderDetailsSupplier.DoesNotExist:
                        # Pas de OrderDetailsSupplier, supprimer directement
                        item_id.delete()
                        messages.warning(request, 'Produit supprimé du panier')
                        return redirect('orders:cart')
                else:
                    # Produit sans vendeur, supprimer directement
                    item_id.delete()
                    messages.warning(request, 'Produit supprimé du panier')
                    return redirect('orders:cart')
    except:
        messages.warning(request, "Vous ne pouvez pas supprimer ce produit !")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='accounts:login')
def payment(request):
    """
    Page de paiement - Uniquement SingPay et paiement à la livraison
    Nécessite une authentification
    """
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY

    context = None
    try:
        shipping = SiteSetting.objects.all().first().shipping
    except:
        shipping = 0
    if shipping is None:
        shipping = 0

    # if "vodafone_cash" in request.POST and "pubg_username" in request.POST and "pubg_id" in request.POST and "notes" in request.POST and request.user.is_authenticated and not request.user.is_anonymous:
    if request.method == 'POST':

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        # Pays fixé au Gabon uniquement
        country = 'GA'  # Code ISO du Gabon
        country_code = 'GA'

        # Gestion de la province et de l'état
        province_state = request.POST.get('state')
        other_state = request.POST.get('other_state')

        if province_state == 'autre_ville' and other_state:
            state = other_state  # On récupère ce que l'utilisateur a saisi
            province = request.POST.get('province')
        else:
            state = request.POST.get('state', '')
            if '|' in state:
                province, state = state.split("|")
            else:
                province = request.POST.get('province', '')

        street_address = request.POST['street']
        city = request.POST['city']
        email_address = request.POST['email_address']
        phone = request.POST['phone']

        # Informations du pays (Gabon uniquement)
        state_obj = state
        province_obj = province
        country_obj = "Gabon"  # Nom du pays
        # Configuration pour le Gabon uniquement
        product_group = "DOM"
        product_type = "OND"
        # country_obj = Country.objects.get(
        #     country_code=country)
        # country_code = country_obj.country_code
        # Utilisateur doit être authentifié (décorateur @login_required)
        order = Order.objects.filter(
            user=request.user, is_finished=False).first()
        if not order:
            messages.error(request, 'Aucune commande en cours.')
            return redirect('orders:cart')
        cart_id = order.id
        request.session['cart_id'] = cart_id

        # Utilisateur doit être authentifié (décorateur @login_required)
        order = Order.objects.filter(user=request.user, is_finished=False).first()

        if order:
            old_orde = order
            old_orde.amount = float(old_orde.amount)+shipping
            old_orde.shipping = shipping
            old_orde.save()
            request.session['order_id'] = old_orde.id
            order_details = OrderDetails.objects.all().filter(order=old_orde)
            try:
                if Payment.objects.all().filter(order=old_orde):
                    payment_info = Payment.objects.get(order=old_orde)
                    payment_info.delete()
            except:
                pass
            order_payment = Payment.objects.create(
                order=old_orde,
                first_name=first_name,
                last_name=last_name,
                country=country_obj,
                country_code=country_code,
                state=state_obj,
                province=province_obj,
                street_address=street_address,
                City=city,
                Email_Address=email_address,
                phone=phone,
                payment_method='Cash on Delivery',  # Par défaut, sera mis à jour si SingPay est sélectionné
            )
            # old_orde.is_finished = True
            # old_orde.status = "جارى التنفيذ"
            # old_orde.save()

            if "coupon_id" in request.session.keys():
                del request.session["coupon_id"]

            if Payment.objects.all().filter(order=old_orde):
                payment_info = Payment.objects.get(order=old_orde)

            site = SiteSetting.objects.first()
            cash_fee = int(site.cash_delivery_service_fee) if site and getattr(site, 'cash_delivery_service_fee', None) is not None else 500
            context = {
                "order": old_orde,
                "payment_info": payment_info,
                "order_details": order_details,
                "cash_service_fee": cash_fee,
            }
            messages.success(
                request, 'Vos informations de facturation ont été enregistrées')
            return render(request, "orders/shop-checkout.html", context)

    # Utilisateur doit être authentifié (décorateur @login_required)
    # Vérifier qu'il y a une commande en cours
    order = Order.objects.filter(user=request.user, is_finished=False).first()
    if not order:
        messages.warning(request, 'Aucune commande à acheter')
        return redirect('orders:cart')
    
    # Rediriger vers le panier si pas de POST (affichage initial)
    return redirect('orders:cart')


def payment_blance(request):
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')

    order = Order.objects.all().filter(user=request.user, is_finished=False)

    if order:
        old_orde = Order.objects.get(user=request.user, is_finished=False)
        try:
            Consignee_id = old_orde.user.id
            Consignee_email = old_orde.user.email
        except:
            pass

        profile = Profile.objects.get(user=request.user)
        if float(old_orde.amount) <= float(profile.blance):
            # print(f"{old_orde.amount} - {profile.blance}")

            # order_payment = Payment.objects.create(

            #     order=old_orde,
            #     by_blance=True
            # )
            payment_method = Payment.objects.get(order=old_orde)
            payment_method.payment_method = "Blance"
            payment_method.save()
        if not old_orde.tracking_no:
            old_orde.tracking_no = code_generator()
            old_orde.rpt_cache = None

            old_orde.is_finished = True
            old_orde.status = "Underway"
            old_orde.save()
            profile.blance = float(profile.blance) - float(old_orde.amount)
            profile.save()

            obj_order_suppliers = OrderSupplier.objects.all().filter(
                user=request.user,  order=old_orde)
            for obj_order_supplier in obj_order_suppliers:
                # order_details__supplier = OrderDetailsSupplier.objects.all().filter(
                #     order_supplier=obj_order_supplier, order=old_orde)
                # f_total = 0
                # w_total = 0
                # weight = 0
                # for sub in order_details__supplier:
                #     f_total += sub.price * sub.quantity
                #     w_total += sub.weight * sub.quantity
                #     total = f_total
                #     weight = w_total
                supplier = Profile.objects.get(id=obj_order_supplier.vendor.id)
                supplier.blance = float(
                    supplier.blance) + float(obj_order_supplier.amount)
                supplier.save()

            if "coupon_id" in request.session.keys():
                del request.session["coupon_id"]
            # messages.success(
            #     request, ' Great, you have completed your purchase, we will work to complete your order from our side')

            return redirect("orders:success")
        else:
            messages.warning(
                request, 'Vous n\'avez pas assez de crédit pour acheter ce produit')
            return redirect("orders:payment")
    messages.warning(request, 'Aucune commande à acheter')
    return redirect("home:index")


@login_required(login_url='accounts:login')
def payment_cash(request):
    """
    Paiement à la livraison : enregistre le choix Cash et redirige vers la page
    de paiement des frais de service (SingPay) avant de finaliser la commande.
    """
    order = Order.objects.filter(user=request.user, is_finished=False).first()
    if not order:
        messages.error(request, 'Aucune commande en cours.')
        return redirect('orders:cart')
    payment_obj = Payment.objects.filter(order=order).first()
    if not payment_obj:
        messages.error(request, 'Informations de paiement manquantes.')
        return redirect('orders:payment')
    payment_obj.payment_method = "Cash"
    payment_obj.save()
    request.session['cart_id'] = order.id
    request.session['order_id'] = order.id
    return redirect('orders:payment-cash-fee')


@login_required(login_url='accounts:login')
def payment_cash_fee(request):
    """
    Page de paiement des frais de service pour le paiement à la livraison.
    Affiche le montant des frais et un bouton pour payer via SingPay.
    """
    order_id = request.session.get('cart_id') or request.session.get('order_id')
    if not order_id:
        messages.error(request, 'Aucune commande en cours.')
        return redirect('orders:cart')
    order = Order.objects.filter(id=order_id, user=request.user, is_finished=False).first()
    if not order:
        if Order.objects.filter(id=order_id, is_finished=True).exists():
            request.session['order_id'] = order_id
            request.session['cart_id'] = order_id
            return redirect('orders:success')
        messages.error(request, 'Commande introuvable ou déjà finalisée.')
        return redirect('orders:cart')
    site = SiteSetting.objects.first()
    fee = 0
    if site and getattr(site, 'cash_delivery_service_fee', None) is not None:
        fee = float(site.cash_delivery_service_fee)
    context = {
        'order': order,
        'cash_fee': fee,
        'cash_fee_formatted': f"{int(fee):,}".replace(',', ' '),
    }
    return render(request, 'orders/payment_cash_fee.html', context)


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
def verify_b2c_buyer_code(request, order_id):
    """
    Le client (acheteur) saisit le code vendeur (V-CODE) pour confirmer la réception.
    """
    order = get_object_or_404(Order, id=order_id, is_finished=True)
    if order.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé.")
        return redirect('accounts:dashboard_customer')
    try:
        verification = order.b2c_delivery_verification
    except B2CDeliveryVerification.DoesNotExist:
        messages.error(request, "Aucune vérification de livraison pour cette commande.")
        return redirect('accounts:dashboard_customer')
    if verification.is_completed():
        messages.success(request, "Cette commande est déjà finalisée.")
        return redirect('orders:invoice-print', order_id=order_id)
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        if verification.verify_buyer_code(code):
            messages.success(request, "Réception confirmée. La transaction est finalisée.")
            return redirect('orders:invoice-print', order_id=order_id)
        messages.error(request, "Code incorrect ou déjà utilisé.")
    context = {
        "order": order,
        "verification": verification,
        "is_buyer": True,
        "code_label": "Code vendeur (V-CODE)",
        "code_help": "Saisissez le code fourni par le vendeur/livreur pour confirmer que vous avez bien reçu la commande.",
    }
    return render(request, "orders/verify_b2c_code.html", context)


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
def verify_b2c_seller_code(request, order_id):
    """
    Le vendeur/livreur saisit le code client (A-CODE) pour confirmer la livraison.
    """
    order = get_object_or_404(Order, id=order_id, is_finished=True)
    order_suppliers = OrderSupplier.objects.filter(order=order)
    vendor_users = [os.vendor.user for os in order_suppliers if os.vendor and os.vendor.user]
    can_verify = request.user.is_staff or request.user.is_superuser or request.user in vendor_users
    if not can_verify:
        messages.error(request, "Accès refusé.")
        return redirect('home:index')
    try:
        verification = order.b2c_delivery_verification
    except B2CDeliveryVerification.DoesNotExist:
        messages.error(request, "Aucune vérification de livraison pour cette commande.")
        return redirect('home:index')
    if verification.is_completed():
        messages.success(request, "Cette commande est déjà finalisée.")
        return redirect('home:index')
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        if verification.verify_seller_code(code):
            messages.success(request, "Livraison confirmée. En attente de la confirmation du client.")
            return redirect('home:index')
        messages.error(request, "Code incorrect ou déjà utilisé.")
    context = {
        "order": order,
        "verification": verification,
        "is_buyer": False,
        "code_label": "Code client (A-CODE)",
        "code_help": "Saisissez le code du client pour confirmer que la livraison a été effectuée.",
    }
    return render(request, "orders/verify_b2c_code.html", context)


def success(request):
    if not request.session.has_key('currency'):
        request.session['currency'] = settings.DEFAULT_CURRENCY

    try:
        try:
            order_id = request.session['cart_id']

        except:
            order_id = request.session.get("order_id")
    except:
        pass

    order = Order.objects.all().filter(id=order_id, is_finished=True)

    if order:
        order_success = Order.objects.get(
            id=order_id, is_finished=True)
        order_details_success = OrderDetails.objects.filter(
            order=order_success)
        payment_info = Payment.objects.get(order=order_success)

        # Lien WhatsApp pour paiement à la livraison (confirmation auprès de Gabomazone)
        whatsapp_url = ""
        if payment_info.payment_method == "Cash":
            contact = ContactInfo.objects.filter(active=True).first()
            if contact and getattr(contact, "phone", None):
                phone_digits = re.sub(r"\D", "", str(contact.phone))
                if phone_digits:
                    message = (
                        f"Bonjour Gabomazone, je souhaite confirmer ma commande #{order_success.id} "
                        f"et finaliser mon paiement à la livraison. Merci de prendre en compte mon ticket de commande."
                    )
                    whatsapp_url = f"https://wa.me/{phone_digits}?text={quote(message)}"

        # B2C : lien pour confirmer la réception (code V-CODE) si vérification existante et non terminée
        b2c_verification = getattr(order_success, 'b2c_delivery_verification', None)
        show_b2c_confirm_reception = (
            b2c_verification
            and not b2c_verification.is_completed()
            and request.user.is_authenticated
            and order_success.user == request.user
        )
        context = {
            "order_success": order_success,
            "order_details_success": order_details_success,
            "payment_info": payment_info,
            "whatsapp_url": whatsapp_url,
            "b2c_verification": b2c_verification,
            "show_b2c_confirm_reception": show_b2c_confirm_reception,
        }
        # Notification courte (affichage temporaire)
        if whatsapp_url:
            messages.success(request, 'Commande enregistrée. Validez-la via WhatsApp en bas de page.')
        else:
            messages.success(request, 'Commande enregistrée. Consultez votre facture ci-dessous.')
        return render(request, "orders/success.html", context)
    else:
        messages.success(request, 'Commande enregistrée.')
        return render(request, "orders/success-x.html")


class CancelView(TemplateView):
    template_name = "orders/cancel.html"


@login_required(login_url='accounts:login')
def invoice_print(request, order_id):
    """
    Vue pour afficher la facture imprimable avec le nouveau design
    Supporte l'export PDF via le paramètre ?format=pdf
    """
    from django.shortcuts import get_object_or_404
    from orders.models import Payment
    from payments.models import SingPayTransaction
    from settings.models import SiteSetting, ContactInfo
    
    # Vérifier que la commande appartient à l'utilisateur
    order = get_object_or_404(
        Order,
        id=order_id,
        is_finished=True
    )
    
    # Vérifier l'accès (admin et vendeur peuvent aussi voir)
    is_admin = request.user.is_staff or request.user.is_superuser
    is_vendor = False
    if hasattr(order, 'ordersupplier'):
        try:
            from accounts.models import Profile
            vendor_profile = Profile.objects.get(user=request.user)
            is_vendor = order.ordersupplier.vendor == vendor_profile
        except:
            pass
    
    if not is_admin and not is_vendor and order.user != request.user and order.email_client != request.user.email:
        messages.error(request, "Vous n'avez pas accès à cette facture.")
        return redirect('accounts:dashboard_customer')
    
    # Récupérer les détails de la commande
    order_details = OrderDetails.objects.filter(order=order)
    
    # Récupérer les informations de paiement
    payment_info = None
    try:
        payment_info = Payment.objects.filter(order=order).first()
    except:
        pass
    
    # Récupérer la transaction SingPay si elle existe
    transaction = None
    try:
        transaction = SingPayTransaction.objects.filter(order=order).first()
    except:
        pass
    
    # Récupérer les informations du site
    site_info = SiteSetting.objects.first()
    contact_info = ContactInfo.objects.all()
    
    context = {
        "order_success": order,
        "order_details_success": order_details,
        "payment_info": payment_info,
        "transaction": transaction,
        "site_info": site_info,
        "contact_info": contact_info,
    }
    
    # Générer PDF si demandé
    if request.GET.get('format') == 'pdf':
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            import io
            
            # Ajouter un flag pour forcer le design desktop dans le PDF
            context['force_desktop_design'] = True
            
            html_string = render_to_string("orders/invoice-print.html", context)
            
            # Créer le HTML avec une largeur fixe pour le PDF (design desktop)
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            
            # CSS pour forcer le design desktop dans le PDF
            pdf_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1cm;
                }
                body {
                    width: 100%;
                }
                .products-table-mobile {
                    display: none !important;
                }
                .products-table {
                    display: table !important;
                    width: 100%;
                }
                .invoice-header {
                    flex-direction: row !important;
                }
                .invoice-info {
                    grid-template-columns: 1fr 1fr !important;
                }
                .invoice-bottom {
                    grid-template-columns: 1fr 1fr !important;
                }
                .invoice-payment {
                    border-right: 1px solid #E5E7EB !important;
                    border-bottom: none !important;
                }
            ''')
            
            pdf_file = io.BytesIO()
            html.write_pdf(pdf_file, stylesheets=[pdf_css])
            
            response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="facture_{order_id}.pdf"'
            return response
        except ImportError:
            import sys
            error_msg = (
                "La génération PDF nécessite WeasyPrint. "
                "Pour l'installer, exécutez dans votre terminal :\n\n"
                "pip install weasyprint\n\n"
                "Ou sur Windows/WSL, vous devrez peut-être installer les dépendances système d'abord.\n"
                "Utilisez l'impression du navigateur en attendant."
            )
            messages.warning(request, error_msg)
            return render(request, "orders/invoice-print.html", context)
        except Exception as e:
            error_msg = (
                f"Erreur lors de la génération PDF: {str(e)}\n\n"
                "Assurez-vous que WeasyPrint est correctement installé avec toutes ses dépendances système."
            )
            messages.error(request, error_msg)
            return render(request, "orders/invoice-print.html", context)
    
    return render(request, "orders/invoice-print.html", context)


@require_http_methods(["GET"])
def get_cart_count(request):
    """Vue AJAX pour obtenir le nombre d'articles dans le panier"""
    try:
        if request.user.is_authenticated and not request.user.is_anonymous:
            order = Order.objects.filter(user=request.user, is_finished=False).first()
        else:
            # Seuls les utilisateurs authentifiés peuvent avoir un panier
            order = None
        
        if order:
            cart_count = OrderDetails.objects.filter(order=order).count()
        else:
            cart_count = 0
        
        return JsonResponse({'cart_count': cart_count})
    except Exception as e:
        return JsonResponse({'cart_count': 0, 'error': str(e)})
