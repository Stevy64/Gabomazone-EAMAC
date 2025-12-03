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

        upper = int(self.request.GET.get("num_products"))
        lower = upper - 10
        orders = list(Order.objects.all().filter(
            user=self.request.user).values().order_by("-order_date")[lower:upper])
        orders_size = len(Order.objects.all().filter(user=self.request.user))
        max_size = True if upper >= orders_size else False
        return JsonResponse({"data": orders,  "max": max_size, "orders_size": orders_size, }, safe=False)


def order(request, order_id):
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')
    context = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        if Order.objects.all().filter(id=order_id, user=request.user, is_finished=True):
            order = Order.objects.get(id=order_id, user=request.user)
            order_details = OrderDetails.objects.all().filter(order=order)
            total = 0
            for sub in order_details:
                total += sub.price * sub.quantity
            context = {
                "order": order,
                "order_details": order_details,
                "total": total,
            }
        elif Order.objects.all().filter(id=order_id, user=request.user, is_finished=False):
            return redirect('orders:cart')
        else:
            messages.warning(
                request, "You don't have access to this page !")
            return redirect('accounts:dashboard_customer')
    return render(request, "accounts/order-archive.html", context)


@login_required(login_url='accounts:login')
def sell_product(request):
    """
    Vue pour ajouter un article à vendre entre particuliers.
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
            user_products = PeerToPeerProduct.objects.filter(seller=request.user).order_by('-date')
    except Exception as e:
        # Si la table n'existe pas encore (migrations non appliquées)
        user_products = []
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        product_name = request.POST.get('product_name', '').strip()
        product_description = request.POST.get('product_description', '').strip()
        PRDPrice = request.POST.get('PRDPrice', '0')
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
        
        # Validation
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
        
        # Créer l'article
        try:
            product = PeerToPeerProduct.objects.create(
                seller=request.user,
                product_name=product_name,
                product_description=product_description,
                PRDPrice=PRDPrice,
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
                PRDSlug=slug,
                status=PeerToPeerProduct.PENDING
            )
            
            # Calculer la commission (fait automatiquement dans save())
            messages.success(request, f'Votre article "{product_name}" a été soumis avec succès. Il sera examiné par notre équipe avant publication.')
            return redirect('accounts:sell-product')
            
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


def peer_product_details(request, slug):
    """Affiche les détails d'un article entre particuliers"""
    from django.shortcuts import get_object_or_404
    
    try:
        peer_product = get_object_or_404(PeerToPeerProduct, PRDSlug=slug, status=PeerToPeerProduct.APPROVED)
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
    
    context = {
        'peer_product': peer_product,
        'similar_products': similar_products,
    }
    return render(request, 'accounts/peer-product-details.html', context)


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
