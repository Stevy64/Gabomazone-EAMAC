from django.shortcuts import render, redirect
from .forms import UserCreationForm, LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from orders.models import Order, OrderDetails
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Profile, PeerToPeerProduct, DeliveryCode
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomPasswordChangeForm
from PIL import Image
from django.conf import settings
from wsgiref.util import FileWrapper
# Import mimetypes module
import mimetypes
# import os module
import os
# Import HttpResponse module
from django.http.response import HttpResponse

# Create your views here.


def register(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        # profile_id = request.session.get('ref_profile')
        if form.is_valid():
            new_user = form.save(commit=False)
            # username = form.cleaned_data['username']
            # email = form.cleaned_data['email']
            new_user.set_password(form.cleaned_data['password1'])
            new_user.save()
            username = form.cleaned_data['username']
            # profile_obj = Profile.objects.get(user__username=username)
            # profile_obj.status = 'vendor'
            # profile_obj.save()
            # messages.success(request, f'Congratulations {username}, your account has been created')
            messages.success(
                request, 'Félicitations {}, votre compte a été créé avec succès.'.format(new_user))
            return redirect('accounts:login')
        else:
            # Si le formulaire est invalide, rediriger vers login avec l'onglet inscription actif
            # On passe les erreurs via les messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            # Créer aussi le formulaire de login pour le template
            login_form = LoginForm()
            return render(request, 'accounts/page-login.html', {
                'title': 'Login',
                'form': login_form,
                'register_form': form,
                'active_tab': 'register'  # Indiquer que l'onglet inscription doit être actif
            })

    # Si GET, rediriger vers login avec l'onglet inscription
    login_form = LoginForm()
    return render(request, 'accounts/page-login.html', {
        'title': 'Login',
        'form': login_form,
        'register_form': form,
        'active_tab': 'register'
    })


def login_user(request):
    if request.method == 'POST':
        form = LoginForm()
        username = request.POST['username']
        password = request.POST['password']
        print(password)
        try:
            user = authenticate(request, username=User.objects.get(
                email=username), password=password)

        except:
            user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(
                request, f'Welcome {username} You are logged in successfully')
            return redirect('accounts:dashboard_customer')

        else:
            messages.warning(request, ' username or password is incorrect')

    else:
        form = LoginForm()
    
    # Passer aussi le formulaire d'inscription pour le switch d'onglets
    register_form = UserCreationForm()

    return render(request, 'accounts/page-login.html', {
        'title': 'Login',
        'form': form,
        'register_form': register_form
    })


def logout_user(request):
    logout(request)
    messages.success(
        request, 'Your Now Logout !')
    return redirect('accounts:login')


def dashboard_customer(request):
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')
    context = None
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        display_name = request.POST['display_name']
        bio = request.POST['bio']
        mobile_number = request.POST['mobile_number']
        city = request.POST['city']
        address = request.POST['address']
        post_code = request.POST['post_code']
        country = request.POST['country']
        state = request.POST['state']
        user = User.objects.get(username=request.user)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        profile = Profile.objects.get(user=request.user)
        try:
            image = request.FILES["image"]

        except:
            image = None

        if image:
            profile.image = image
        profile.display_name = display_name
        profile.bio = bio
        profile.mobile_number = mobile_number
        profile.city = city
        profile.address = address
        profile.post_code = post_code
        profile.country = country
        profile.state = state
        profile.save()
        messages.success(
            request, 'Your Profile Info Has Been Saved !')
        return redirect("accounts:dashboard_customer")

    else:
        profile = Profile.objects.get(
            user=request.user)
        print(profile)
        context = {
            "profile": profile,
        }
    return render(request, 'accounts/page-account.html', context)


def dashboard_account_details(request):
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')
    context = None
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        display_name = request.POST['display_name']
        bio = request.POST['bio']
        mobile_number = request.POST['mobile_number']
        province = request.POST.get('province', '')
        city = request.POST.get('city', '')
        quartier = request.POST.get('quartier', '')
        address = request.POST.get('address', '')
        country = request.POST.get('country', 'Gabon')
        user = User.objects.get(username=request.user)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        profile = Profile.objects.get(user=request.user)
        try:
            image = request.FILES.get("image")

        except:
            image = None

        if image:
            profile.image = image

        if image:
            try:
                Image.open(image)

            except:
                messages.warning(request, 'Désolé, votre image est invalide')
                return redirect("accounts:account_details")
        profile.display_name = display_name
        profile.bio = bio
        profile.mobile_number = mobile_number
        profile.city = city
        profile.address = address
        profile.post_code = quartier  # Utiliser post_code pour stocker le quartier
        profile.country = country
        profile.state = province  # Utiliser state pour stocker la province
        profile.save()
        messages.success(
            request, 'Vos informations ont été enregistrées avec succès !')
        return redirect("accounts:account_details")

    else:
        profile = Profile.objects.get(
            user=request.user)
        print(profile)
        context = {
            "profile": profile,
        }
    return render(request, 'accounts/account-details.html', context)


def order_tracking(request):

    return render(request, 'accounts/order-tracking.html')


@login_required(login_url='accounts:login')
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            login(request, request.user)
            messages.success(
                request, 'Votre mot de passe a été modifié avec succès !')
            return redirect('accounts:change_password')

        else:
            messages.warning(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, "accounts/change-password.html",  {
        'form': form,
        'title': 'Changer le mot de passe',
    })


class MyOrdersJsonListView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        # Filtrer uniquement les commandes terminées pour l'affichage
        num_products = self.request.GET.get("num_products", "10")
        try:
            upper = int(num_products)
        except (ValueError, TypeError):
            upper = 10
        lower = upper - 10
        
        # Filtrer les commandes finies uniquement
        # Inclure aussi les commandes avec email_client correspondant si user est None
        import logging
        logger = logging.getLogger(__name__)
        
        # Debug: vérifier toutes les commandes
        all_orders = Order.objects.filter(is_finished=True)
        logger.info(f"Total orders with is_finished=True: {all_orders.count()}")
        
        # Filtrer par utilisateur
        user_orders = Order.objects.filter(user=self.request.user, is_finished=True)
        email_orders = Order.objects.filter(email_client=self.request.user.email, is_finished=True)
        
        logger.info(f"Orders for user {self.request.user.id} ({self.request.user.email}): {user_orders.count()}")
        logger.info(f"Orders for email {self.request.user.email}: {email_orders.count()}")
        
        orders_queryset = Order.objects.filter(
            Q(user=self.request.user) | Q(email_client=self.request.user.email),
            is_finished=True
        ).order_by("-order_date")[lower:upper]
        
        logger.info(f"Final queryset count: {orders_queryset.count()}")
        
        # Convertir en liste de dictionnaires avec les champs nécessaires
        from orders.models import OrderDetails
        from payments.models import SingPayTransaction
        
        orders = []
        for order in orders_queryset:
            # Compter les articles dans la commande
            items_count = OrderDetails.objects.filter(order=order).count()
            
            # Récupérer la transaction SingPay associée si elle existe
            transaction = None
            try:
                transaction = SingPayTransaction.objects.filter(order=order).first()
            except:
                pass
            
            # Obtenir le statut de la commande avec traduction
            status = order.status
            status_display_map = {
                'PENDING': 'En attente',
                'Underway': 'En cours',
                'COMPLETE': 'Terminée',
                'Refunded': 'Remboursée',
            }
            status_display = status_display_map.get(status, status)
            
            order_data = {
                'id': order.id,
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'date_update': order.date_update.isoformat() if order.date_update else None,
                'amount': str(order.amount) if order.amount else '0',
                'status': status,  # Utiliser le statut brut pour le mapping JavaScript
                'status_display': status_display,  # Pour l'affichage traduit
                'tracking_no': order.tracking_no or '',
                'items_count': items_count,
                'is_finished': order.is_finished,
            }
            
            # Ajouter les informations de transaction si disponible
            if transaction:
                order_data['transaction_id'] = transaction.transaction_id
                order_data['transaction_status'] = transaction.status
                order_data['payment_method'] = transaction.payment_method or 'Non spécifié'
                order_data['has_transaction'] = True
            else:
                order_data['has_transaction'] = False
                order_data['transaction_id'] = None
            
            orders.append(order_data)
        
        orders_size = Order.objects.filter(
            Q(user=self.request.user) | Q(email_client=self.request.user.email),
            is_finished=True
        ).count()
        
        logger.info(f"Total orders size: {orders_size}")
        max_size = True if upper >= orders_size else False
        return JsonResponse({"data": orders,  "max": max_size, "orders_size": orders_size, }, safe=False)


def order(request, order_id):
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')
    context = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        # Vérifier l'accès avec user ou email_client
        order = None
        try:
            order = Order.objects.filter(
                Q(user=request.user) | Q(email_client=request.user.email),
                id=order_id,
                is_finished=True
            ).first()
        except:
            pass
        
        if order:
            order_details = OrderDetails.objects.all().filter(order=order)
            total = 0
            for sub in order_details:
                total += sub.price * sub.quantity
            
            # Récupérer les informations de paiement
            payment_info = None
            try:
                from orders.models import Payment as OrderPayment
                payment_info = OrderPayment.objects.filter(order=order).first()
            except:
                pass
            
            # Récupérer la transaction SingPay si elle existe
            transaction = None
            try:
                from payments.models import SingPayTransaction
                transaction = SingPayTransaction.objects.filter(order=order).first()
            except:
                pass
            
            # Traduire le statut
            status_display_map = {
                'PENDING': 'En attente',
                'Underway': 'En cours',
                'COMPLETE': 'Terminée',
                'Refunded': 'Remboursée',
            }
            status_display = status_display_map.get(order.status, order.status)
            
            context = {
                "order": order,
                "order_details": order_details,
                "total": total,
                "payment_info": payment_info,
                "transaction": transaction,
                "status_display": status_display,
            }
        elif Order.objects.all().filter(id=order_id, user=request.user, is_finished=False):
            return redirect('orders:cart')
        else:
            messages.warning(
                request, "Vous n'avez pas accès à cette page !")
            return redirect('accounts:dashboard_customer')
    return render(request, "accounts/order-archive.html", context)


@login_required(login_url='accounts:login')
def sell_product(request):
    """
    Vue pour ajouter un article C2C.
    Remplace l'ancienne page de téléchargement.
    """
    from categories.models import SuperCategory, MainCategory, SubCategory
    from django.utils.text import slugify
    import random
    import string
    from datetime import datetime, timedelta
    from django.db import connection
    
    # Récupérer les catégories pour le formulaire
    super_categories = SuperCategory.objects.all()
    main_categories = MainCategory.objects.all()
    sub_categories = SubCategory.objects.all()
    
    # Récupérer les articles de l'utilisateur (avec gestion d'erreur si la table n'existe pas encore)
    user_products = []
    try:
        # Vérifier si la table existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_peertopeerproduct'")
            table_exists = cursor.fetchone() is not None
        
        if table_exists:
            user_products = PeerToPeerProduct.objects.filter(seller=request.user).exclude(status=PeerToPeerProduct.SOLD).order_by('-date')
            # Vérifier si les produits sont boostés
            from c2c.models import ProductBoost
            from django.utils import timezone
            now = timezone.now()
            for product in user_products:
                try:
                    active_boost = ProductBoost.objects.filter(
                        product=product,
                        status=ProductBoost.ACTIVE,
                        start_date__lte=now,
                        end_date__gte=now
                    ).first()
                    product.is_boosted = active_boost is not None
                except:
                    product.is_boosted = False
    except Exception as e:
        # Si la table n'existe pas encore (migrations non appliquées)
        user_products = []
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        product_name = request.POST.get('product_name', '').strip()
        product_description = request.POST.get('product_description', '').strip()
        PRDPrice = request.POST.get('PRDPrice', '0')
        condition = request.POST.get('condition', PeerToPeerProduct.BON_ETAT).strip()
        seller_phone = request.POST.get('seller_phone', '').strip()
        seller_address = request.POST.get('seller_address', '').strip()
        seller_city = request.POST.get('seller_city', '').strip()
        
        # Catégories
        super_category_id = request.POST.get('product_supercategory', '')
        main_category_id = request.POST.get('product_maincategory', '')
        sub_category_id = request.POST.get('product_subcategory', '')
        
        # Images
        product_image = request.FILES.get('product_image')
        additional_image_1 = request.FILES.get('additional_image_1')
        additional_image_2 = request.FILES.get('additional_image_2')
        additional_image_3 = request.FILES.get('additional_image_3')
        additional_image_4 = request.FILES.get('additional_image_4')
        
        # Validation
        valid_conditions = [c[0] for c in PeerToPeerProduct.CONDITION_CHOICES]
        if condition not in valid_conditions:
            condition = PeerToPeerProduct.BON_ETAT
        if not product_name or not product_description or not PRDPrice or not seller_phone or not seller_address or not seller_city:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
            return redirect('accounts:sell-product')
        
        try:
            PRDPrice = float(PRDPrice)
            if PRDPrice <= 0:
                messages.error(request, 'Le prix doit être supérieur à 0.')
                return redirect('accounts:sell-product')
        except ValueError:
            messages.error(request, 'Le prix doit être un nombre valide.')
            return redirect('accounts:sell-product')
        
        if not product_image:
            messages.error(request, 'Veuillez ajouter une image principale.')
            return redirect('accounts:sell-product')
        
        # Récupérer les catégories
        super_category = None
        main_category = None
        sub_category = None
        
        if super_category_id:
            try:
                super_category = SuperCategory.objects.get(id=super_category_id)
            except SuperCategory.DoesNotExist:
                pass
        
        if main_category_id:
            try:
                main_category = MainCategory.objects.get(id=main_category_id)
            except MainCategory.DoesNotExist:
                pass
        
        if sub_category_id:
            try:
                sub_category = SubCategory.objects.get(id=sub_category_id)
            except SubCategory.DoesNotExist:
                pass
        
        # Générer un slug unique
        base_slug = slugify(product_name, allow_unicode=True)
        slug = base_slug
        counter = 1
        while PeerToPeerProduct.objects.filter(PRDSlug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Vérifier si la table existe avant de créer l'article
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_peertopeerproduct'")
                table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                messages.error(request, 'Les migrations n\'ont pas encore été appliquées. Veuillez exécuter: python manage.py makemigrations accounts && python manage.py migrate')
                return redirect('accounts:sell-product')
        except Exception as e:
            messages.error(request, f'Erreur de base de données: {str(e)}. Veuillez exécuter les migrations.')
            return redirect('accounts:sell-product')
        
        # Créer l'article (mis en ligne directement ; l'admin reçoit une notification)
        try:
            from django.utils import timezone
            product = PeerToPeerProduct.objects.create(
                seller=request.user,
                product_name=product_name,
                product_description=product_description,
                PRDPrice=PRDPrice,
                condition=condition,
                seller_phone=seller_phone,
                seller_address=seller_address,
                seller_city=seller_city,
                product_supercategory=super_category,
                product_maincategory=main_category,
                product_subcategory=sub_category,
                product_image=product_image,
                additional_image_1=additional_image_1,
                additional_image_2=additional_image_2,
                additional_image_3=additional_image_3,
                additional_image_4=additional_image_4,
                PRDSlug=slug,
                status=PeerToPeerProduct.APPROVED,
                approved_date=timezone.now()
            )
            
            messages.success(request, f'Votre article "{product_name}" est en ligne.')
            
            # Rediriger vers "Mes articles publiés" avec une proposition de boost
            # Une fois approuvé, l'utilisateur pourra booster son article
            return redirect('accounts:my-published-products')
            
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de la création de l\'article: {str(e)}')
            return redirect('accounts:sell-product')
    
    context = {
        'super_categories': super_categories,
        'main_categories': main_categories,
        'sub_categories': sub_categories,
        'user_products': user_products,
    }
    return render(request, 'accounts/add-peer-to-peer-product.html', context)


@login_required(login_url='accounts:login')
def edit_peer_product(request, product_id):
    """
    Vue pour modifier un article peer-to-peer existant.
    """
    from categories.models import SuperCategory, MainCategory, SubCategory
    from django.utils.text import slugify
    
    try:
        product = PeerToPeerProduct.objects.get(id=product_id, seller=request.user)
    except PeerToPeerProduct.DoesNotExist:
        messages.error(request, 'Article introuvable ou vous n\'avez pas la permission de le modifier.')
        return redirect('accounts:sell-product')
    
    # Récupérer les catégories pour le formulaire
    super_categories = SuperCategory.objects.all()
    main_categories = MainCategory.objects.all()
    sub_categories = SubCategory.objects.all()
    
    # Récupérer les catégories sélectionnées pour pré-remplir le formulaire
    selected_super = product.product_supercategory.id if product.product_supercategory else None
    selected_main = product.product_maincategory.id if product.product_maincategory else None
    selected_sub = product.product_subcategory.id if product.product_subcategory else None
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        product_name = request.POST.get('product_name', '').strip()
        product_description = request.POST.get('product_description', '').strip()
        PRDPrice = request.POST.get('PRDPrice', '0')
        condition = request.POST.get('condition', PeerToPeerProduct.BON_ETAT).strip()
        seller_phone = request.POST.get('seller_phone', '').strip()
        seller_address = request.POST.get('seller_address', '').strip()
        seller_city = request.POST.get('seller_city', '').strip()
        
        # Catégories
        super_category_id = request.POST.get('product_supercategory', '')
        main_category_id = request.POST.get('product_maincategory', '')
        sub_category_id = request.POST.get('product_subcategory', '')
        
        # Images
        product_image = request.FILES.get('product_image')
        additional_image_1 = request.FILES.get('additional_image_1')
        additional_image_2 = request.FILES.get('additional_image_2')
        additional_image_3 = request.FILES.get('additional_image_3')
        additional_image_4 = request.FILES.get('additional_image_4')
        
        # Validation
        if not product_name or not product_description or not PRDPrice or not seller_phone or not seller_address or not seller_city:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
            return redirect('accounts:edit-peer-product', product_id=product_id)
        
        try:
            PRDPrice = float(PRDPrice)
            if PRDPrice <= 0:
                messages.error(request, 'Le prix doit être supérieur à 0.')
                return redirect('accounts:edit-peer-product', product_id=product_id)
        except ValueError:
            messages.error(request, 'Le prix doit être un nombre valide.')
            return redirect('accounts:edit-peer-product', product_id=product_id)
        
        # Récupérer les catégories
        super_category = None
        main_category = None
        sub_category = None
        
        if super_category_id:
            try:
                super_category = SuperCategory.objects.get(id=super_category_id)
            except SuperCategory.DoesNotExist:
                pass
        
        if main_category_id:
            try:
                main_category = MainCategory.objects.get(id=main_category_id)
            except MainCategory.DoesNotExist:
                pass
        
        if sub_category_id:
            try:
                sub_category = SubCategory.objects.get(id=sub_category_id)
            except SubCategory.DoesNotExist:
                pass
        
        # Mettre à jour l'article
        valid_conditions = [c[0] for c in PeerToPeerProduct.CONDITION_CHOICES]
        if condition in valid_conditions:
            product.condition = condition
        product.product_name = product_name
        product.product_description = product_description
        product.PRDPrice = PRDPrice
        product.seller_phone = seller_phone
        product.seller_address = seller_address
        product.seller_city = seller_city
        product.product_supercategory = super_category
        product.product_maincategory = main_category
        product.product_subcategory = sub_category
        
        # Mettre à jour les images seulement si de nouvelles sont fournies
        if product_image:
            product.product_image = product_image
        if additional_image_1:
            product.additional_image_1 = additional_image_1
        if additional_image_2:
            product.additional_image_2 = additional_image_2
        if additional_image_3:
            product.additional_image_3 = additional_image_3
        if additional_image_4:
            product.additional_image_4 = additional_image_4
        
        # Si le nom a changé, mettre à jour le slug
        old_name = product.product_name
        if product_name != old_name:
            base_slug = slugify(product_name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while PeerToPeerProduct.objects.filter(PRDSlug=slug).exclude(id=product.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            product.PRDSlug = slug
        
        product.save()
        
        messages.success(request, f'Votre article "{product_name}" a été modifié avec succès.')
        return redirect('accounts:sell-product')
    
    # Récupérer les articles de l'utilisateur pour l'affichage (exclure les vendus)
    user_products = PeerToPeerProduct.objects.filter(seller=request.user).exclude(status=PeerToPeerProduct.SOLD).order_by('-date')
    
    context = {
        'product': product,
        'super_categories': super_categories,
        'main_categories': main_categories,
        'sub_categories': sub_categories,
        'user_products': user_products,
        'selected_super': selected_super,
        'selected_main': selected_main,
        'selected_sub': selected_sub,
        'is_edit': True,
    }
    return render(request, 'accounts/add-peer-to-peer-product.html', context)


@login_required(login_url='accounts:login')
def delete_peer_product(request, product_id):
    """
    Vue pour supprimer un article peer-to-peer.
    Empêche la suppression si des commandes C2C sont associées.
    """
    if request.method == 'POST':
        try:
            product = PeerToPeerProduct.objects.get(id=product_id, seller=request.user)
            product_name = product.product_name
            
            # Vérifier si des commandes C2C sont associées
            from c2c.models import C2COrder
            c2c_orders_count = C2COrder.objects.filter(product=product).count()
            
            if c2c_orders_count > 0:
                messages.error(
                    request, 
                    f'Impossible de supprimer l\'article "{product_name}". '
                    f'Il est associé à {c2c_orders_count} commande(s) C2C. '
                    f'Pour préserver l\'historique des transactions, vous pouvez uniquement modifier ou archiver cet article.'
                )
            else:
                # Vérifier aussi les intentions d'achat en cours
                from c2c.models import PurchaseIntent
                active_intents = PurchaseIntent.objects.filter(
                    product=product,
                    status__in=['pending', 'negotiating', 'accepted']
                ).count()
                
                if active_intents > 0:
                    messages.warning(
                        request,
                        f'L\'article "{product_name}" a {active_intents} intention(s) d\'achat en cours. '
                        f'Veuillez attendre la finalisation ou l\'annulation de ces intentions avant de supprimer l\'article.'
                    )
                else:
                    # Supprimer l'article
                    product.delete()
                    messages.success(request, f'L\'article "{product_name}" a été supprimé avec succès.')
                    
        except PeerToPeerProduct.DoesNotExist:
            messages.error(request, 'Article introuvable ou vous n\'avez pas la permission de le supprimer.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')
    else:
        messages.error(request, 'Méthode non autorisée.')
    
    return redirect('accounts:my-published-products')


@login_required(login_url='accounts:login')
def my_published_products(request):
    """
    Vue pour afficher tous les articles publiés par l'utilisateur.
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_peertopeerproduct'")
            table_exists = cursor.fetchone() is not None
        
        if table_exists:
            user_products = PeerToPeerProduct.objects.filter(seller=request.user).exclude(status=PeerToPeerProduct.SOLD).order_by('-date')
            # Calculer le nombre de messages non lus et vérifier si le produit est boosté
            from .models import ProductConversation
            from c2c.models import ProductBoost
            from django.utils import timezone
            now = timezone.now()
            
            for product in user_products:
                try:
                    conversations = ProductConversation.objects.filter(product=product, seller=request.user)
                    unread_count = 0
                    for conv in conversations:
                        unread_count += conv.get_unread_count_for_seller()
                    product.unread_messages_count = unread_count
                except:
                    product.unread_messages_count = 0
                
                # Vérifier si le produit a un boost actif
                try:
                    active_boost = ProductBoost.objects.filter(
                        product=product,
                        status=ProductBoost.ACTIVE,
                        start_date__lte=now,
                        end_date__gte=now
                    ).first()
                    product.is_boosted = active_boost is not None
                    if active_boost:
                        product.boost_end_date = active_boost.end_date
                except:
                    product.is_boosted = False
        else:
            user_products = []
    except Exception as e:
        user_products = []
    
    context = {
        'user_products': user_products,
    }
    return render(request, 'accounts/my-published-products.html', context)


@login_required(login_url='accounts:login')
def get_product_conversations(request, product_id):
    """
    Vue pour obtenir les conversations d'un produit (API JSON)
    Peut être appelée par le vendeur ou l'acheteur
    """
    from django.http import JsonResponse
    from .models import ProductConversation, ProductMessage
    from django.utils import timezone
    from django.contrib.auth.models import User
    from django.db import connection as db_connection
    import json
    
    try:
        # Récupérer le produit
        try:
            product = PeerToPeerProduct.objects.get(id=product_id)
        except PeerToPeerProduct.DoesNotExist:
            # Si le produit a été supprimé ou est inexistant, retourner une liste vide
            return JsonResponse({'conversations': []})
        
        # Vérifier que l'utilisateur est soit le vendeur soit un acheteur
        if product.seller != request.user:
            # Vérifier si la table ProductConversation existe
            conv_table_exists = False
            try:
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
                    conv_table_exists = cursor.fetchone() is not None
            except Exception:
                conv_table_exists = False
            
            # Vérifier si l'utilisateur a une intention d'achat ou une conversation pour ce produit
            from c2c.models import PurchaseIntent
            
            # Vérifier si la table PurchaseIntent existe
            c2c_table_exists = False
            try:
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c2c_purchaseintent'")
                    c2c_table_exists = cursor.fetchone() is not None
            except Exception:
                c2c_table_exists = False
            
            # Si l'utilisateur n'est pas le vendeur, vérifier s'il a une intention d'achat ou une conversation
            has_intent_or_conv = False
            if c2c_table_exists:
                try:
                    has_intent_or_conv = PurchaseIntent.objects.filter(
                        product=product,
                        buyer=request.user
                    ).exists()
                except Exception:
                    has_intent_or_conv = False
            
            has_conversation = False
            if conv_table_exists:
                try:
                    has_conversation = ProductConversation.objects.filter(
                        product=product,
                        buyer=request.user
                    ).exists()
                except Exception:
                    has_conversation = False
            
            if not has_intent_or_conv and not has_conversation:
                # Autoriser quand même l'accès pour permettre la création d'une intention d'achat
                return JsonResponse({'conversations': []})
    except Exception:
        # En cas d'erreur inattendue, ne pas bloquer l'UI : retourner une liste vide
        return JsonResponse({'conversations': []})
    
    # Vérifier si la table ProductConversation existe avant de l'utiliser
    conv_table_exists = False
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
            conv_table_exists = cursor.fetchone() is not None
    except Exception:
        conv_table_exists = False
    
    if not conv_table_exists:
        return JsonResponse({'conversations': []})
    
    # Si c'est le vendeur, récupérer toutes les conversations
    # Si c'est un acheteur, récupérer uniquement sa conversation
    if product.seller == request.user:
        conversations = ProductConversation.objects.filter(product=product).select_related('buyer', 'seller')
    else:
        conversations = ProductConversation.objects.filter(product=product, buyer=request.user).select_related('buyer', 'seller')

    # Si aucune conversation n'existe encore, tenter de la créer à partir d'une intention d'achat
    if not conversations.exists():
        try:
            from c2c.models import PurchaseIntent
            # Chercher une intention d'achat en cours
            from django.db.models import Q
            intent = PurchaseIntent.objects.filter(
                product=product,
                status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]
            ).filter(
                Q(buyer=request.user) | Q(seller=request.user)
            ).order_by('-created_at').first()

            if intent:
                buyer = intent.buyer
                seller = intent.seller
                if request.user in [buyer, seller]:
                    conversation, _ = ProductConversation.objects.get_or_create(
                        product=product,
                        buyer=buyer,
                        seller=seller,
                        defaults={'last_message_at': timezone.now()}
                    )
                    conversations = ProductConversation.objects.filter(id=conversation.id).select_related('buyer', 'seller')
        except Exception:
            pass
    
    conversations_data = []
    for conv in conversations:
        messages = conv.messages.all().order_by('created_at')
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'sender_id': msg.sender.id,
                'message': msg.message,
                'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M'),
                'is_read': msg.is_read,
                'is_sender': msg.sender == request.user,
            })
        
        # Déterminer qui est l'autre utilisateur
        if request.user == conv.seller:
            other_user = conv.buyer
            unread_count = conv.get_unread_count_for_seller()
        else:
            other_user = conv.seller
            unread_count = conv.get_unread_count_for_buyer()
        
        conversations_data.append({
            'id': conv.id,
            'product_id': conv.product.id,
            'buyer_id': conv.buyer.id,
            'seller_id': conv.seller.id,
            'buyer_username': conv.buyer.username,
            'buyer_name': conv.buyer.get_full_name() or conv.buyer.username,
            'seller_name': conv.seller.get_full_name() or conv.seller.username,
            'other_user_name': other_user.get_full_name() or other_user.username,
            'messages': messages_data,
            'unread_count': unread_count,
            'last_message_at': conv.last_message_at.strftime('%d/%m/%Y %H:%M') if conv.last_message_at else None,
        })
    
    return JsonResponse({'conversations': conversations_data})


@login_required(login_url='accounts:login')
def send_product_message(request, product_id):
    """
    Vue pour envoyer un message dans une conversation (API JSON)
    Accepte conversation_id pour permettre l'envoi même si le produit a été supprimé
    """
    from django.http import JsonResponse
    from .models import ProductConversation, ProductMessage
    from django.utils import timezone
    from django.contrib.auth.models import User
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return JsonResponse({'error': 'Le message ne peut pas être vide'}, status=400)
    
    # Récupérer la conversation
    try:
        if conversation_id:
            # Si conversation_id fourni, l'utiliser directement (même si le produit a été supprimé)
            conversation = ProductConversation.objects.get(id=conversation_id)
        else:
            # Si pas de conversation_id, on a besoin du produit
            try:
                product = PeerToPeerProduct.objects.get(id=product_id)
            except PeerToPeerProduct.DoesNotExist:
                return JsonResponse({'error': 'Article introuvable. Utilisez conversation_id.'}, status=404)
            
            # Utiliser buyer_id (ancien système)
            buyer_id = data.get('buyer_id')
            if not buyer_id:
                return JsonResponse({'error': 'conversation_id ou buyer_id requis'}, status=400)
            
            buyer = User.objects.get(id=buyer_id)
            conversation, created = ProductConversation.objects.get_or_create(
                product=product,
                seller=product.seller,
                buyer=buyer,
                defaults={'last_message_at': timezone.now()}
            )
        
        # Vérifier que l'utilisateur peut envoyer un message dans cette conversation
        if request.user not in [conversation.seller, conversation.buyer]:
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        
        # Vérifier si une commande C2C existe et si elle est terminée (bloquer le chat)
        try:
            from c2c.models import C2COrder
            c2c_order = C2COrder.objects.filter(
                product=conversation.product,
                buyer=conversation.buyer,
                seller=conversation.seller,
                status=C2COrder.COMPLETED
            ).first()
            
            if c2c_order:
                return JsonResponse({
                    'error': 'Cette transaction est terminée. Le chat est désactivé.'
                }, status=403)
        except Exception:
            # Si erreur lors de la vérification C2C, continuer quand même
            pass
        
    except ProductConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Utilisateur introuvable'}, status=404)
    
    # Mettre à jour la date du dernier message
    conversation.last_message_at = timezone.now()
    conversation.save()
    
    # Créer le message
    message = ProductMessage.objects.create(
        conversation=conversation,
        sender=request.user,
        message=message_text
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'message': message.message,
            'created_at': message.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_read': message.is_read,
            'is_sender': True,
        }
    })


@login_required(login_url='accounts:login')
@require_POST
def delete_product_message(request, message_id):
    """
    Supprime un message d'une conversation si l'utilisateur est l'expéditeur
    """
    from django.http import JsonResponse
    from .models import ProductMessage
    
    try:
        message = ProductMessage.objects.select_related('conversation').get(id=message_id)
    except ProductMessage.DoesNotExist:
        return JsonResponse({'error': 'Message introuvable'}, status=404)
    
    # Permission : seul l'expéditeur peut supprimer son message
    if message.sender != request.user:
        return JsonResponse({'error': 'Vous ne pouvez supprimer que vos propres messages'}, status=403)
    
    message.delete()
    return JsonResponse({'success': True})


@login_required(login_url='accounts:login')
@require_POST
def archive_conversation(request, conversation_id):
    """
    Archive une conversation pour l'utilisateur courant
    """
    from django.http import JsonResponse
    from .models import ProductConversation
    
    try:
        conversation = ProductConversation.objects.get(id=conversation_id)
    except ProductConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in [conversation.seller, conversation.buyer]:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    conversation.archive_for_user(request.user)
    return JsonResponse({'success': True, 'message': 'Conversation archivée'})


@login_required(login_url='accounts:login')
@require_POST
def unarchive_conversation(request, conversation_id):
    """
    Désarchive une conversation pour l'utilisateur courant
    """
    from django.http import JsonResponse
    from .models import ProductConversation
    
    try:
        conversation = ProductConversation.objects.get(id=conversation_id)
    except ProductConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    
    # Vérifier que l'utilisateur fait partie de la conversation
    if request.user not in [conversation.seller, conversation.buyer]:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    conversation.unarchive_for_user(request.user)
    return JsonResponse({'success': True, 'message': 'Conversation désarchivée'})


@login_required(login_url='accounts:login')
@require_POST
def delete_conversation(request, conversation_id):
    """
    Supprime une conversation et tous ses messages. Seul un participant (vendeur ou acheteur) peut supprimer.
    """
    from django.http import JsonResponse
    from .models import ProductConversation

    try:
        conversation = ProductConversation.objects.get(id=conversation_id)
    except ProductConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)

    if request.user not in [conversation.seller, conversation.buyer]:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)

    conversation.delete()
    return JsonResponse({'success': True, 'message': 'Conversation supprimée'})


@login_required(login_url='accounts:login')
def mark_conversation_messages_read(request, conversation_id):
    """
    Vue pour marquer les messages d'une conversation comme lus (API JSON)
    """
    from django.http import JsonResponse
    from .models import ProductConversation, ProductMessage
    from django.utils import timezone
    
    try:
        conversation = ProductConversation.objects.get(id=conversation_id)
        if request.user not in [conversation.seller, conversation.buyer]:
            return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    except ProductConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation introuvable'}, status=404)
    
    # Marquer les messages de l'autre participant comme lus
    ProductMessage.objects.filter(
        conversation=conversation,
        sender__in=[conversation.seller, conversation.buyer],
        is_read=False
    ).exclude(sender=request.user).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'success': True})


@login_required(login_url='accounts:login')
def my_messages(request):
    """
    Vue pour afficher toutes les conversations de l'utilisateur (en tant que vendeur et acheteur)
    """
    from .models import ProductConversation, ProductMessage, PeerToPeerOrderNotification, PeerToPeerProduct
    from django.db import connection
    from django.utils import timezone
    
    all_conversations = []
    total_unread = 0
    peer_notifications = []
    orders_unread_count = 0
    auto_open_product_id = None
    auto_open_conversation_id = None
    
    # Vérifier d'abord si la table existe avant d'essayer de créer une conversation
    table_exists = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_productconversation'")
            table_exists = cursor.fetchone() is not None
    except Exception:
        table_exists = False
    
    # Vérifier si c'est une proposition d'offre ou un retour après paiement (seulement si la table existe)
    if table_exists:
        product_id = request.GET.get('product_id')
        action = request.GET.get('action')
        
        if product_id:
            try:
                product = PeerToPeerProduct.objects.get(id=product_id)
                
                # Si c'est une proposition d'offre (nouvel acheteur)
                if action == 'propose_offer' and product.seller != request.user and product.status == PeerToPeerProduct.APPROVED:
                    # Créer ou récupérer la conversation
                    conversation, created = ProductConversation.objects.get_or_create(
                        product=product,
                        seller=product.seller,
                        buyer=request.user,
                        defaults={'last_message_at': timezone.now()}
                    )
                    
                    # Si la conversation existe déjà, mettre à jour la date du dernier message
                    if not created:
                        conversation.last_message_at = timezone.now()
                        conversation.save()
                    
                    auto_open_product_id = product.id
                    auto_open_conversation_id = conversation.id
                else:
                    # Sinon, essayer de trouver une conversation existante (retour après paiement)
                    conversation = ProductConversation.objects.filter(
                        product=product,
                    ).filter(
                        Q(seller=request.user) | Q(buyer=request.user)
                    ).first()
                    
                    if conversation:
                        auto_open_product_id = product.id
                        auto_open_conversation_id = conversation.id
            except (PeerToPeerProduct.DoesNotExist, ValueError, Exception):
                pass  # Ignorer les erreurs et continuer normalement
    
    try:
        
        if not table_exists:
            context = {
                'conversations': [],
                'total_unread': 0,
                'peer_notifications': [],
                'orders_unread_count': 0,
                'purchase_intents': [],
                'purchase_intents_unread': 0,
                'auto_open_product_id': auto_open_product_id,
                'auto_open_conversation_id': auto_open_conversation_id,
            }
            return render(request, 'accounts/my-messages.html', context)
        
        # Marquer les intentions d'achat comme notifiées quand le vendeur visite la page
        try:
            from c2c.models import PurchaseIntent
            from django.db import connection as db_connection
            c2c_table_exists = False
            try:
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c2c_purchaseintent'")
                    c2c_table_exists = cursor.fetchone() is not None
            except Exception:
                c2c_table_exists = False
            
            if c2c_table_exists:
                # Marquer toutes les intentions d'achat comme notifiées (le vendeur a vu la page)
                PurchaseIntent.objects.filter(
                    seller=request.user,
                    seller_notified=False
                ).update(seller_notified=True)
        except Exception:
            pass  # Ignorer les erreurs
        
        # Conversations où l'utilisateur est vendeur
        seller_conversations = ProductConversation.objects.filter(seller=request.user).select_related('product', 'buyer').prefetch_related('messages').order_by('-last_message_at')
        
        # Conversations où l'utilisateur est acheteur
        buyer_conversations = ProductConversation.objects.filter(buyer=request.user).select_related('product', 'seller').prefetch_related('messages').order_by('-last_message_at')
        
        # Calculer le nombre total de messages non lus
        total_unread = 0
        
        # Messages non lus en tant que vendeur
        for conv in seller_conversations:
            total_unread += conv.get_unread_count_for_seller()
        
        # Messages non lus en tant qu'acheteur
        for conv in buyer_conversations:
            total_unread += conv.get_unread_count_for_buyer()
        
        # Ajouter le nombre de messages non lus à chaque conversation et précharger le dernier message
        active_conversations = []
        archived_conversations = []
        
        for conv in seller_conversations:
            conv.unread_count = conv.get_unread_count_for_seller()
            conv.other_user = conv.buyer
            conv.user_role = 'seller'
            conv.last_message = conv.messages.order_by('-created_at').first()
            conv.c2c_order = conv.get_c2c_order()
            conv.purchase_intent = conv.get_purchase_intent()
            active_conversations.append(conv)
        
        for conv in buyer_conversations:
            conv.unread_count = conv.get_unread_count_for_buyer()
            conv.other_user = conv.seller
            conv.user_role = 'buyer'
            conv.last_message = conv.messages.order_by('-created_at').first()
            conv.c2c_order = conv.get_c2c_order()
            conv.purchase_intent = conv.get_purchase_intent()
            active_conversations.append(conv)
        
        # Toutes les conversations (archivage désactivé)
        all_conversations = active_conversations
        all_conversations.sort(key=lambda x: (x.last_message_at is None, x.last_message_at), reverse=True)
        
        # Récupérer les notifications de commandes
        try:
            peer_notifications_qs = PeerToPeerOrderNotification.objects.filter(
                seller=request.user
            ).select_related('order', 'buyer', 'peer_product').order_by('-created_at')
            orders_unread_count = peer_notifications_qs.filter(is_read=False).count()
            # Convertir en liste pour faciliter l'utilisation dans le template
            peer_notifications = list(peer_notifications_qs)
        except Exception as e:
            peer_notifications = []
            orders_unread_count = 0
        
        # Récupérer les intentions d'achat C2C pour le vendeur
        try:
            from c2c.models import PurchaseIntent
            from django.db import connection as db_connection
            # Vérifier si la table existe
            c2c_table_exists = False
            try:
                with db_connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c2c_purchaseintent'")
                    c2c_table_exists = cursor.fetchone() is not None
            except Exception:
                c2c_table_exists = False
            
            if c2c_table_exists:
                purchase_intents_qs = PurchaseIntent.objects.filter(
                    seller=request.user,
                    status__in=[PurchaseIntent.PENDING, PurchaseIntent.NEGOTIATING]
                ).select_related('product', 'buyer').order_by('-created_at')
                # Compter les intentions non notifiées (seller_notified=False) comme non lues
                purchase_intents_unread = purchase_intents_qs.filter(seller_notified=False).count()
                purchase_intents = list(purchase_intents_qs)
            else:
                purchase_intents = []
                purchase_intents_unread = 0
        except Exception as e:
            purchase_intents = []
            purchase_intents_unread = 0
        
    except Exception as e:
        all_conversations = []
        total_unread = 0
        # Récupérer les notifications de commandes même en cas d'erreur
        try:
            peer_notifications_qs = PeerToPeerOrderNotification.objects.filter(
                seller=request.user
            ).select_related('order', 'buyer', 'peer_product').order_by('-created_at')
            orders_unread_count = peer_notifications_qs.filter(is_read=False).count()
            # Convertir en liste pour faciliter l'utilisation dans le template
            peer_notifications = list(peer_notifications_qs)
        except Exception as e:
            peer_notifications = []
            orders_unread_count = 0
    
    context = {
        'conversations': all_conversations,
        'total_unread': total_unread,
        'messages_count': total_unread,  # pour le badge "Ma messagerie" dans _mon_compte_card.html
        'peer_notifications': peer_notifications,
        'orders_unread_count': orders_unread_count,
        'purchase_intents': purchase_intents,
        'purchase_intents_unread': purchase_intents_unread,
        'auto_open_product_id': auto_open_product_id,
        'auto_open_conversation_id': auto_open_conversation_id,
        'archived_conversations': [],  # option d'archivage supprimée
    }
    return render(request, 'accounts/my-messages.html', context)


def peer_product_details(request, slug):
    """Affiche les détails d'un article C2C"""
    from django.shortcuts import get_object_or_404
    
    try:
        peer_product = get_object_or_404(PeerToPeerProduct, PRDSlug=slug, status=PeerToPeerProduct.APPROVED)
        
        # Incrémenter le compteur de vues
        from django.db.models import F
        PeerToPeerProduct.objects.filter(id=peer_product.id).update(view_count=F('view_count') + 1)
        peer_product.refresh_from_db()
    except Exception as e:
        messages.error(request, "Cet article n'existe pas ou n'est pas encore approuvé.")
        return redirect('categories:shop')
    
    # Récupérer les articles similaires (même catégorie principale)
    similar_products = []
    try:
        if peer_product.product_maincategory:
            similar_products = PeerToPeerProduct.objects.filter(
                product_maincategory=peer_product.product_maincategory,
                status=PeerToPeerProduct.APPROVED
            ).exclude(id=peer_product.id)[:8]
    except:
        pass
    
    # Récupérer les statistiques du vendeur (avec gestion d'erreur si la table n'existe pas)
    seller_stats = None
    try:
        from c2c.models import SellerReview
        seller_stats = SellerReview.get_seller_stats(peer_product.seller)
    except Exception as e:
        seller_stats = {
            'average_rating': 0,
            'total_reviews': 0,
        }
    
    # Nombre d'articles publiés par le vendeur (annonces approuvées)
    seller_products_count = PeerToPeerProduct.objects.filter(
        seller=peer_product.seller, status=PeerToPeerProduct.APPROVED
    ).count()
    
    context = {
        'peer_product': peer_product,
        'similar_products': similar_products,
        'seller_stats': seller_stats,
        'seller_products_count': seller_products_count,
    }
    return render(request, 'accounts/peer-product-details.html', context)


@login_required(login_url='accounts:login')
def peer_orders_list(request):
    """
    Vue pour afficher les commandes reçues par un vendeur peer-to-peer
    """
    from accounts.models import PeerToPeerOrderNotification
    from orders.models import OrderDetails
    
    # Récupérer toutes les notifications de commande pour ce vendeur
    notifications = PeerToPeerOrderNotification.objects.filter(
        seller=request.user
    ).order_by('-created_at')
    
    # Compter les notifications non lues
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/peer-orders-list.html', context)


@login_required(login_url='accounts:login')
def accept_peer_order(request, notification_id):
    """
    Vue pour accepter une commande peer-to-peer
    """
    from django.shortcuts import get_object_or_404
    from accounts.models import PeerToPeerOrderNotification
    from django.utils import timezone
    from orders.models import Order
    
    notification = get_object_or_404(
        PeerToPeerOrderNotification,
        id=notification_id,
        seller=request.user,
        status=PeerToPeerOrderNotification.PENDING
    )
    
    if request.method == 'POST':
        seller_message = request.POST.get('seller_message', '').strip()
        
        notification.status = PeerToPeerOrderNotification.ACCEPTED
        notification.responded_at = timezone.now()
        notification.is_read = True
        if seller_message:
            notification.seller_message = seller_message
        notification.save()
        
        # Créer ou récupérer la conversation pour ce produit et cet acheteur
        from .models import ProductConversation, ProductMessage
        conversation, created = ProductConversation.objects.get_or_create(
            product=notification.peer_product,
            seller=request.user,
            buyer=notification.buyer,
            defaults={'last_message_at': timezone.now()}
        )
        
        # Si une conversation existe déjà, mettre à jour la date du dernier message
        if not created:
            conversation.last_message_at = timezone.now()
            conversation.save()
        
        # Créer un message automatique pour informer l'acheteur que la commande a été acceptée
        buyer_name = notification.buyer.get_full_name() or notification.buyer.username
        welcome_message = f"Bonjour {buyer_name}, votre commande #{notification.order.id} pour l'article '{notification.peer_product.product_name}' a été acceptée !"
        if seller_message:
            welcome_message += f"\n\nMessage du vendeur : {seller_message}"
        
        ProductMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            message=welcome_message
        )
        
        # Mettre à jour le statut de la commande si nécessaire
        if notification.order:
            notification.order.status = Order.Underway
            notification.order.save()
        
        messages.success(request, f'Vous avez accepté la commande #{notification.order.id}. Une conversation a été créée avec l\'acheteur.')
        return redirect('accounts:my-messages')
    
    context = {
        'notification': notification,
    }
    return render(request, 'accounts/accept-peer-order.html', context)


@login_required(login_url='accounts:login')
def reject_peer_order(request, notification_id):
    """
    Vue pour refuser une commande peer-to-peer
    """
    from accounts.models import PeerToPeerOrderNotification
    from django.utils import timezone
    
    notification = get_object_or_404(
        PeerToPeerOrderNotification,
        id=notification_id,
        seller=request.user,
        status=PeerToPeerOrderNotification.PENDING
    )
    
    if request.method == 'POST':
        seller_message = request.POST.get('seller_message', '').strip()
        
        notification.status = PeerToPeerOrderNotification.REJECTED
        notification.responded_at = timezone.now()
        notification.is_read = True
        if seller_message:
            notification.seller_message = seller_message
        notification.save()
        
        messages.info(request, f'Vous avez refusé la commande #{notification.order.id}.')
        return redirect('accounts:peer-orders-list')
    
    context = {
        'notification': notification,
    }
    return render(request, 'accounts/reject-peer-order.html', context)


@login_required(login_url='accounts:login')
def mark_notification_read(request, notification_id):
    """
    Vue pour marquer une notification comme lue (AJAX)
    """
    from accounts.models import PeerToPeerOrderNotification
    
    notification = get_object_or_404(
        PeerToPeerOrderNotification,
        id=notification_id,
        seller=request.user
    )
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'success': True})


@login_required(login_url='accounts:login')
def download_file(request, order_id, filename):
    if request.user.is_authenticated and not request.user.is_anonymous:
        if Order.objects.all().filter(id=order_id, user=request.user, is_finished=True):
            # Define Django project base directory
            # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            BASE_DIR = settings.MEDIA_ROOT
            # Define the full file path
            filepath = BASE_DIR + '/products/files/' + filename
            # filepath = os.path.join(settings.MEDIA_ROOT, filename)
            print(filepath)
            # Open the file for reading content
            # path = open(filepath, 'rb')
            path = FileWrapper(open(filepath, 'rb'))
            # Set the mime type
            mime_type, _ = mimetypes.guess_type(filepath)
            # Set the return value of the HttpResponse
            response = HttpResponse(path, content_type=mime_type)
            # Set the HTTP header for sending to browser
            response['Content-Disposition'] = f"attachment; filename={filename}"
            # Return the response value
            return response

        elif Order.objects.all().filter(id=order_id, user=request.user, is_finished=False):
            return redirect('orders:cart')
        else:
            messages.warning(
                request, "You don't have access to this page !")
            return redirect('accounts:dashboard_customer')
