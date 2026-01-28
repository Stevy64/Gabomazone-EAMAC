from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from accounts.models import Profile, BankAccount, SocialLink
from django.contrib.auth import get_user_model
from products.models import Product, ProductImage, ProductRating, ProductSize
from django.http import JsonResponse
from categories.models import SuperCategory, MainCategory, SubCategory, MiniCategory
from django.views import View
from PIL import Image
from django.http import HttpResponseRedirect
from orders.models import Order, OrderSupplier,  OrderDetailsSupplier, Payment
from .utils import vendor_only
from django.db.models import Sum
from datetime import datetime, date, timedelta
from django.utils import timezone as tz
from payments.models import VendorPayments
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


@vendor_only
def supplier_dashboard(request):
    vendor = Profile.objects.get(user=request.user)
    orders_supplier = OrderSupplier.objects.all().filter(
        vendor=vendor).exclude(status="PENDING")
    products_supplier = Product.objects.all().filter(
        product_vendor=vendor, PRDISactive=True).order_by("-date")
    orders_underway = OrderSupplier.objects.all().filter(
        vendor=vendor, status="Underway")

    context = {
        "orders_supplier": orders_supplier,
        "products_supplier": products_supplier,
        "vendor": vendor,
        "orders_underway": orders_underway,
    }
    return render(request, 'supplier-panel/index.html', context)


class chartJsonListView(View):
    """
    Vue pour récupérer les données des statistiques de vente.
    Supporte les périodes de 3, 6 et 12 mois.
    """
    def get(self, *args, **kwargs):
        today = date.today()
        if self.request.user.is_authenticated and not self.request.user.is_anonymous:
            vendor = Profile.objects.get(user=self.request.user)
            
            # Récupérer la période demandée (par défaut 12 mois)
            period = int(self.request.GET.get('period', 12))
            
            # Calculer la date de début selon la période
            if period == 3:
                start_date = today - timedelta(days=90)
                months_to_show = 3
            elif period == 6:
                start_date = today - timedelta(days=180)
                months_to_show = 6
            else:  # 12 mois par défaut
                start_date = date(today.year, 1, 1)  # Début de l'année
                months_to_show = 12

            product_count_list = []
            order_count_list = []
            labels = []
            
            # Générer les données pour chaque mois de la période
            # Pour 3 et 6 mois, on prend les X derniers mois
            # Pour 12 mois, on prend tous les mois de l'année en cours
            if period == 12:
                # Pour 12 mois, utiliser tous les mois de l'année en cours
                for month in range(1, 13):
                    month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
                    labels.append(month_names[month - 1])
                    
                    # Compter les produits créés ce mois
                    product_count = Product.objects.filter(
                        product_vendor=vendor,
                        date__year=today.year,
                        date__month=month
                    ).count()
                    product_count_list.append(product_count)
                    
                    # Compter les commandes ce mois (hors PENDING)
                    order_count = OrderSupplier.objects.filter(
                        vendor=vendor,
                        order_date__year=today.year,
                        order_date__month=month
                    ).exclude(status="PENDING").count()
                    order_count_list.append(order_count)
            else:
                # Pour 3 et 6 mois, prendre les X derniers mois complets
                month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
                
                # Calculer le mois de départ (X mois en arrière)
                current_month = today.month
                current_year = today.year
                
                for i in range(months_to_show):
                    # Calculer le mois en remontant depuis le mois actuel
                    months_back = months_to_show - 1 - i
                    target_month = current_month - months_back
                    target_year = current_year
                    
                    # Gérer le débordement d'année
                    while target_month <= 0:
                        target_month += 12
                        target_year -= 1
                    while target_month > 12:
                        target_month -= 12
                        target_year += 1
                    
                    # Labels pour le graphique
                    labels.append(month_names[target_month - 1])
                    
                    # Compter les produits créés ce mois
                    product_count = Product.objects.filter(
                        product_vendor=vendor,
                        date__year=target_year,
                        date__month=target_month
                    ).count()
                    product_count_list.append(product_count)
                    
                    # Compter les commandes ce mois (hors PENDING)
                    order_count = OrderSupplier.objects.filter(
                        vendor=vendor,
                        order_date__year=target_year,
                        order_date__month=target_month
                    ).exclude(status="PENDING").count()
                    order_count_list.append(order_count)

            return JsonResponse({
                "product_count_list": product_count_list,
                "order_count_list": order_count_list,
                "labels": labels
            }, safe=False)


class chartJsonListViewAdmin(View):
    def get(self, *args, **kwargs):
        today = date.today()
        if self.request.user.is_authenticated and not self.request.user.is_anonymous:
            user = User.objects.get(username=self.request.user.username)
            if user.is_superuser == True:
                # vendor = Profile.objects.get(user=self.request.user)
                product_count_list = []
                order_count_list = []
                for i in range(1, 13):
                    product_count = Product.objects.all().filter(
                        date__year=today.year, date__month=i,).count()
                    product_count_list.append(product_count)
                    order_count = OrderSupplier.objects.all().filter(order_date__year=today.year,
                                                                     order_date__month=i,).exclude(status="PENDING").count()
                    order_count_list.append(order_count)

                return JsonResponse({"product_count_list": product_count_list, "order_count_list": order_count_list, }, safe=False)


def supplier_login(request):
    # if request.user.is_authenticated:
    #     return redirect('supplier_dashboard:supplier-panel')

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        profile_obj = None

        try:
            if Profile.objects.all().filter(user__username=username).exists():
                profile_obj = Profile.objects.get(user__username=username)
            else:
                user_email = User.objects.get(email=username).email

                profile_obj = Profile.objects.get(user__email=user_email)
        except:
            messages.warning(request, ' username or password is incorrect')
            profile_obj = None

        if profile_obj != None and profile_obj.status == "vendor" and profile_obj.admission == True:

            try:
                user = authenticate(request, username=User.objects.get(
                    email=username), password=password)

            except:
                user = authenticate(
                    request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(
                    request, f'Welcome {username}, You are logged in successfully')
                return redirect('supplier_dashboard:supplier-panel')

            else:
                messages.warning(request, ' username or password is incorrect')
        else:
            messages.warning(
                request, 'Your account is being reviewed by the administrator.')

    return render(request, 'supplier-panel/supplier-account-login.html')


def supplier_register(request):
    # if request.user.is_authenticated:
    #     return redirect('supplier_dashboard:supplier-panel')

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']
        UserModel = get_user_model()
        if not username:
            username = None

        if username != None and not UserModel.objects.filter(username=username).exists() and not UserModel.objects.filter(email=email).exists():
            user = UserModel.objects.create_user(
                username=username, email=email, password=password)
            user.is_superuser = False
            user.is_staff = False
            user.save()
            profile_obj = Profile.objects.get(user__username=username)
            profile_obj.status = 'vendor'
            profile_obj.mobile_number = phone
            profile_obj.save()
            messages.success(
                request, f"Congratulations {username}, your account has been created .")
            return redirect('supplier_dashboard:supplier-login')

        else:
            messages.warning(
                request, 'Username or Email Already Exists Try Other Info')

    return render(request, "supplier-panel/supplier-account-register.html")


@vendor_only
def supplier_add_product(request):
    """
    Vue pour ajouter un nouveau produit.
    Gère la réception et la validation des données du formulaire d'ajout de produit.
    """
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')

    if request.method == 'POST':
        # ============================================
        # 1. RÉCUPÉRATION DES DONNÉES DU FORMULAIRE
        # ============================================
        
        # Informations de base du produit
        nom_produit = request.POST.get('product_name', '').strip()
        description_courte = request.POST.get('introduction', '').strip()
        description_complete = request.POST.get('content', '').strip()
        
        # Prix et remise
        prix_str = request.POST.get('price', '0')
        prix_remise_str = request.POST.get('discount', '0')
        
        # Stock et unités
        quantite_disponible = request.POST.get('available', '0')
        nombre_unites = request.POST.get('pieces', '0')
        
        # Statut et promotion
        statut_produit = request.POST.get('product_status', '1')
        type_promotion = request.POST.get('promotional', 'New')
        
        # Dimensions et poids (optionnels)
        largeur = request.POST.get('width', '').strip() or None
        hauteur = request.POST.get('height', '').strip() or None
        poids = request.POST.get('weight', '').strip() or None
        
        # SKU et tags (optionnels)
        code_sku = request.POST.get('SKU', '').strip() or None
        tags_produit = request.POST.get('tags', '').strip()
        
        # Condition du produit
        condition_produit = request.POST.get('product_condition', '1')
        
        # ============================================
        # 2. VALIDATION DES DONNÉES NUMÉRIQUES
        # ============================================
        
        try:
            prix = float(prix_str)
            if prix < 0:
                raise ValueError("Le prix ne peut pas être négatif")
        except (ValueError, TypeError):
            messages.warning(
                request, 'Veuillez entrer un prix valide (nombre positif)')
            return redirect("supplier_dashboard:supplier-add-product")

        try:
            prix_remise = float(prix_remise_str)
            if prix_remise < 0:
                prix_remise = 0
        except (ValueError, TypeError):
            prix_remise = 0

        # Conversion du statut
        est_actif = (statut_produit == '1')
        
        # ============================================
        # 3. RÉCUPÉRATION DES CATÉGORIES
        # ============================================
        
        super_categorie = None
        categorie_principale = None
        sous_categorie = None
        mini_categorie = None
        
        id_super_categorie = request.POST.get('super_category_value')
        if id_super_categorie:
            try:
                super_categorie = SuperCategory.objects.get(id=id_super_categorie)
            except SuperCategory.DoesNotExist:
                messages.warning(request, 'La super catégorie sélectionnée est invalide')
                return redirect("supplier_dashboard:supplier-add-product")
        
        id_categorie_principale = request.POST.get('main_category_value')
        if id_categorie_principale:
            try:
                categorie_principale = MainCategory.objects.get(id=id_categorie_principale)
            except MainCategory.DoesNotExist:
                pass  # Optionnel
        
        id_sous_categorie = request.POST.get('sub_category_value')
        if id_sous_categorie:
            try:
                sous_categorie = SubCategory.objects.get(id=id_sous_categorie)
            except SubCategory.DoesNotExist:
                pass  # Optionnel
        
        id_mini_categorie = request.POST.get('mini_category_value')
        if id_mini_categorie:
            try:
                mini_categorie = MiniCategory.objects.get(id=id_mini_categorie)
            except MiniCategory.DoesNotExist:
                pass  # Optionnel
        
        # ============================================
        # 4. VALIDATION ET TRAITEMENT DES IMAGES
        # ============================================
        
        def valider_image(fichier_image, nom_champ):
            """Valide qu'un fichier image est valide"""
            if fichier_image:
                try:
                    Image.open(fichier_image)
                    return True
                except Exception:
                    messages.warning(
                        request, f'L\'image "{nom_champ}" est invalide. Formats acceptés : JPG, PNG, GIF, BMP')
                    return False
            return True
        
        # Image principale (obligatoire)
        image_principale = request.FILES.get("main_image")
        if not image_principale:
            messages.warning(request, 'L\'image principale est obligatoire')
            return redirect("supplier_dashboard:supplier-add-product")
        
        if not valider_image(image_principale, "Image principale"):
            return redirect("supplier_dashboard:supplier-add-product")
        
        # Images additionnelles (optionnelles)
        image_additionnelle_1 = request.FILES.get("name_image_1")
        if image_additionnelle_1 and not valider_image(image_additionnelle_1, "Image additionnelle 1"):
            return redirect("supplier_dashboard:supplier-add-product")
        
        image_additionnelle_2 = request.FILES.get("name_image_2")
        if image_additionnelle_2 and not valider_image(image_additionnelle_2, "Image additionnelle 2"):
            return redirect("supplier_dashboard:supplier-add-product")
        
        image_additionnelle_3 = request.FILES.get("name_image_3")
        if image_additionnelle_3 and not valider_image(image_additionnelle_3, "Image additionnelle 3"):
            return redirect("supplier_dashboard:supplier-add-product")
        
        image_additionnelle_4 = request.FILES.get("name_image_4")
        if image_additionnelle_4 and not valider_image(image_additionnelle_4, "Image additionnelle 4"):
            return redirect("supplier_dashboard:supplier-add-product")
        
        # Fichier numérique (optionnel)
        fichier_numerique = request.FILES.get("digital_file")
        
        # ============================================
        # 5. RÉCUPÉRATION DES TAILLES DISPONIBLES
        # ============================================
        
        tailles_disponibles = []
        tailles_possibles = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL']
        
        for taille in tailles_possibles:
            if taille in request.POST:
                tailles_disponibles.append(taille)
        
        # ============================================
        # 6. CRÉATION DU PRODUIT
        # ============================================
        
        try:
            vendeur = Profile.objects.get(user=request.user)
            
            nouveau_produit = Product.objects.create(
                # Informations de base
                product_name=nom_produit,
                product_description=description_courte,
                content=description_complete,
                
                # Prix
                PRDPrice=prix,
                PRDDiscountPrice=prix_remise,
                
                # Images
                product_image=image_principale,
                additional_image_1=image_additionnelle_1,
                additional_image_2=image_additionnelle_2,
                additional_image_3=image_additionnelle_3,
                additional_image_4=image_additionnelle_4,
                digital_file=fichier_numerique,
                
                # Catégories
                product_vendor=vendeur,
                product_supercategory=super_categorie,
                product_maincategory=categorie_principale,
                product_subcategory=sous_categorie,
                product_minicategor=mini_categorie,
                
                # Stock et unités
                available=quantite_disponible,
                pieces=nombre_unites,
                
                # Statut et promotion
                promotional=type_promotion,
                PRDISactive=est_actif,
                
                # Dimensions
                width=largeur,
                height=hauteur,
                # Note: Le champ PRDWeight n'existe pas dans le modèle Product
                # Le poids n'est pas stocké pour le moment
                
                # Métadonnées
                PRDSKU=code_sku,
                PRDtags=tags_produit,
            )
            
            # ============================================
            # 7. CRÉATION DES IMAGES ADDITIONNELLES
            # ============================================
            
            images_additionnelles = [
                image_additionnelle_1,
                image_additionnelle_2,
                image_additionnelle_3,
                image_additionnelle_4
            ]
            
            for image in images_additionnelles:
                if image:
                    ProductImage.objects.create(
                        PRDIProduct=nouveau_produit,
                        PRDIImage=image
                    )
            
            # ============================================
            # 8. GESTION DES TAILLES DISPONIBLES
            # ============================================
            
            for taille in tailles_disponibles:
                if not ProductSize.objects.filter(
                    PRDIProduct=nouveau_produit,
                    name_variation=taille
                ).exists():
                    ProductSize.objects.create(
                        PRDIProduct=nouveau_produit,
                        name_variation=taille
                    )
            
            messages.success(
                request, f'Le produit "{nom_produit}" a été créé avec succès !')
            return redirect('supplier_dashboard:supplier-add-product')
            
        except Exception as e:
            messages.error(
                request, f'Une erreur est survenue lors de la création du produit : {str(e)}')
            return redirect("supplier_dashboard:supplier-add-product")

    # ============================================
    # AFFICHAGE DU FORMULAIRE (GET)
    # ============================================
    
    # Récupération de toutes les super catégories pour le formulaire
    super_categories = SuperCategory.objects.all()
    
    # Récupération de la première super catégorie pour pré-remplir les catégories suivantes
    premiere_super_categorie = super_categories.first()
    
    # Récupération des catégories principales de la première super catégorie
    categories_principales = []
    if premiere_super_categorie:
        categories_principales = MainCategory.objects.filter(
            super_category=premiere_super_categorie
        )
    
    # Récupération de la première catégorie principale pour pré-remplir les sous-catégories
    premiere_categorie_principale = categories_principales.first() if categories_principales else None
    
    # Récupération des sous-catégories de la première catégorie principale
    sous_categories = []
    if premiere_categorie_principale:
        sous_categories = SubCategory.objects.filter(
            main_category=premiere_categorie_principale
        )
    
    # Récupération de la première sous-catégorie pour pré-remplir les mini catégories
    premiere_sous_categorie = sous_categories.first() if sous_categories else None
    
    # Récupération des mini catégories de la première sous-catégorie
    mini_categories = []
    if premiere_sous_categorie:
        mini_categories = MiniCategory.objects.filter(
            sub_category=premiere_sous_categorie
        )
    
    # Récupération de tous les produits du vendeur pour affichage dans la liste
    vendeur = Profile.objects.get(user=request.user)
    produits = Product.objects.filter(
        product_vendor=vendeur,
        PRDISDeleted=False
    ).order_by('-date')
    
    context = {
        "super_category": super_categories,
        "main_category": categories_principales,
        "sub_category": sous_categories,
        "mini_category": mini_categories,
        "products": produits,
        "vendor": vendeur,
    }
    return render(request, 'supplier-panel/supplier-add-product.html', context)


class CategoriesJsonListView(View):
    """
    Vue AJAX pour charger dynamiquement les catégories.
    Retourne les catégories en fonction de la hiérarchie sélectionnée.
    """
    def get(self, *args, **kwargs):
        # Récupération de toutes les super catégories
        super_categories = list(SuperCategory.objects.all().values())
        
        # Récupération des paramètres de filtrage depuis la requête AJAX
        id_super_categorie = self.request.GET.get('super_category_ajax')
        id_categorie_principale = self.request.GET.get('main_category_ajax')
        id_sous_categorie = self.request.GET.get('sub_category_ajax')

        # Chargement des catégories principales si une super catégorie est sélectionnée
        if id_super_categorie:
            categories_principales = list(MainCategory.objects.filter(
                super_category__id=id_super_categorie).values())
        else:
            categories_principales = []

        # Chargement des sous-catégories si une catégorie principale est sélectionnée
        if id_categorie_principale:
            sous_categories = list(SubCategory.objects.filter(
                main_category__id=id_categorie_principale).values())
        else:
            sous_categories = []

        # Chargement des mini catégories si une sous-catégorie est sélectionnée
        if id_sous_categorie:
            mini_categories = list(MiniCategory.objects.filter(
                sub_category__id=id_sous_categorie).values())
        else:
            mini_categories = []

        return JsonResponse({
            "super_category": super_categories,
            "main_category": categories_principales,
            "sub_category": sous_categories,
            "mini_category": mini_categories,
        }, safe=False)


# Page supplier-products-list supprimée - redirection vers supplier-add-product
# @vendor_only
# def supplier_products_list(request):
#     vendor = Profile.objects.get(user=request.user)
#     super_categories = SuperCategory.objects.all()
#     
#     context = {
#         "vendor": vendor,
#         "super_category": super_categories,
#     }
#     return render(request, "supplier-panel/supplier-products-list.html", context)


class SupplierProductsJsonListView(View):
    def get(self, *args, **kwargs):
        user = Profile.objects.get(user=self.request.user)
        upper = int(self.request.GET.get('num_products'))
        order_by = self.request.GET.get('order_by')
        order_by_status = self.request.GET.get('order_by_status')

        lower = upper - 5
        if order_by_status == "All":
            products_list = list(Product.objects.all().filter(
                product_vendor=user, PRDISDeleted=False).values().order_by(order_by)[lower:upper])

            products_size = len(Product.objects.all().filter(
                product_vendor=user, PRDISDeleted=False))

            max_size = True if upper >= products_size else False
        elif order_by_status == "Active":
            products_list = list(Product.objects.all().filter(
                product_vendor=user, PRDISactive=True, PRDISDeleted=False).values().order_by(order_by)[lower:upper])

            products_size = len(Product.objects.all().filter(
                product_vendor=user, PRDISactive=True, PRDISDeleted=False))

            max_size = True if upper >= products_size else False
        else:
            products_list = list(Product.objects.all().filter(
                product_vendor=user, PRDISactive=False, PRDISDeleted=False).values().order_by(order_by)[lower:upper])

            products_size = len(Product.objects.all().filter(
                product_vendor=user, PRDISactive=False, PRDISDeleted=False))

            max_size = True if upper >= products_size else False

        return JsonResponse({"data": products_list,  "max": max_size, "products_size": products_size, }, safe=False)


@vendor_only
def remove_product(request, id):
    """
    Vue pour supprimer un produit (soft delete).
    Marque le produit comme supprimé sans le supprimer définitivement de la base de données.
    """
    if not request.user.is_authenticated or request.user.is_anonymous or not id:
        messages.warning(request, "Vous devez être connecté pour supprimer un produit")
        return redirect('accounts:login')
    
    try:
        produit = Product.objects.get(id=id)
        
        # Vérifier que le produit appartient au vendeur connecté
        if produit.product_vendor.user.id != request.user.id:
            messages.warning(
                request, "Vous n'avez pas l'autorisation de supprimer ce produit")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        # Soft delete : marquer comme supprimé et inactif
        produit.PRDISDeleted = True
        produit.PRDISactive = False
        
        try:
            produit.save()
            messages.success(
                request, f'Le produit "{produit.product_name}" a été supprimé avec succès')
            return redirect('supplier_dashboard:supplier-add-product')
        except Exception as e:
            messages.error(
                request, f'Une erreur est survenue lors de la suppression : {str(e)}')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            
    except Product.DoesNotExist:
        messages.warning(request, "Le produit demandé n'existe pas")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except Exception as e:
        messages.error(
            request, f'Une erreur est survenue : {str(e)}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@vendor_only
def supplier_edit_product(request, id):
    product = None
    product_variations = None
    if not request.user.is_authenticated and request.user.is_anonymous:
        return redirect('accounts:login')

    product_obj = Product.objects.get(id=id)
    if product_obj.product_vendor.user.id == request.user.id:
        if request.method == 'POST':
            super_category_obj = None
            main_category_obj = None
            sub_category_obj = None
            mini_category_obj = None

            product_name = request.POST.get('product_name', '')
            introduction = request.POST.get('introduction', '')
            content = request.POST.get('content', '')
            price = request.POST.get('price', '0')
            discount = request.POST.get('discount', '0')
            # description = request.POST['description']
            try:
                super_category_value = request.POST['super_category_value']
            except:
                super_category_value = None

            try:
                main_category_value = request.POST['main_category_value']
            except:
                main_category_value = None
            try:
                sub_category_value = request.POST['sub_category_value']
            except:
                sub_category_value = None

            try:
                mini_category_value = request.POST['mini_category_value']
            except:
                mini_category_value = None

            XXS = "XXS-Delete"
            try:
                XXS = request.POST['XXS']

            except:
                XSS = "XXS-Delete"
            # print("xxs: ", XXS)

            XS = "XS-Delete"
            try:
                XS = request.POST['XS']

            except:
                XS = "XS-Delete"

            S = "S-Delete"
            try:
                S = request.POST['S']

            except:
                S = "S-Delete"

            M = "M-Delete"
            try:
                M = request.POST['M']

            except:
                M = "M-Delete"

            L = "L-Delete"
            try:
                L = request.POST['L']

            except:
                L = "L-Delete"

            XL = "XL-Delete"
            try:
                XL = request.POST['XL']

            except:
                XL = "XL-Delete"

            XXL = "XXL-Delete"
            try:
                XXL = request.POST['XXL']

            except:
                XXL = "XXL-Delete"
            # checkbox = request.POST['checkbox']
            # if checkbox:
            #     print("checkbox: ", checkbox)
            available = request.POST.get('available', '0')
            pieces = request.POST.get('pieces', '0')
            promotional = request.POST.get('promotional', 'New')

            product_status = int(request.POST.get('product_status', '1'))
            width = request.POST.get('width', '')
            if not width:
                width = None
            height = request.POST.get('height', '')
            if not height:
                height = None
            weight = request.POST.get('weight', '')
            product_SKU = request.POST.get('SKU', '')
            if not product_SKU:
                product_SKU = None
            tags = request.POST.get('tags', '')
            if product_status == 1:
                product_status = True
            else:
                product_status = False
            # print(f"product_status: {product_status}", type(product_status))
            try:
                price = float(request.POST["price"])
            except (ValueError, TypeError):
                messages.warning(
                    request, '-Please Enter A Valid Pricing number')
                return redirect("supplier_dashboard:supplier-add-product")

            try:
                discount = float(request.POST["discount"])
            except (ValueError, TypeError):
                discount = 0

            try:
                main_image = request.FILES["main_image"]
            except:
                main_image = None
            if main_image:
                try:
                    Image.open(main_image)

                except:
                    messages.warning(request, 'sorry, your image is invalid')
                    return redirect("supplier_dashboard:supplier-add-product")

            try:
                name_image_1 = request.FILES["name_image_1"]
            except:
                name_image_1 = None
            if name_image_1:
                try:
                    Image.open(name_image_1)

                except:
                    messages.warning(request, 'sorry, your image is invalid')
                    return redirect("supplier_dashboard:supplier-add-product")

            try:
                name_image_2 = request.FILES["name_image_2"]
            except:
                name_image_2 = None
            if name_image_2:
                try:
                    Image.open(name_image_2)

                except:
                    messages.warning(request, 'sorry, your image is invalid')
                    return redirect("supplier_dashboard:supplier-add-product")

            try:
                name_image_3 = request.FILES["name_image_3"]
            except:
                name_image_3 = None
            if name_image_3:
                try:
                    Image.open(name_image_3)

                except:
                    messages.warning(request, 'sorry, your image is invalid')
                    return redirect("supplier_dashboard:supplier-add-product")

            try:
                name_image_4 = request.FILES["name_image_4"]
            except:
                name_image_4 = None
            if name_image_4:
                try:
                    Image.open(name_image_4)

                except:
                    messages.warning(request, 'sorry, your image is invalid')
                    return redirect("supplier_dashboard:supplier-add-product")

            try:
                digital_file = request.FILES["digital_file"]
            except:
                digital_file = None

            if super_category_value:
                super_category_obj = SuperCategory.objects.get(
                    id=super_category_value)
            if main_category_value:
                main_category_obj = MainCategory.objects.get(
                    id=main_category_value)
            if sub_category_value:
                sub_category_obj = SubCategory.objects.get(
                    id=sub_category_value)
            if mini_category_value:
                mini_category_obj = MiniCategory.objects.get(
                    id=mini_category_value)

            product_vendor = Profile.objects.get(user__username=request.user)

            new_product_obj = Product.objects.get(id=id)
            new_product_obj.product_name = product_name
            new_product_obj.product_description = introduction
            new_product_obj.content = content
            new_product_obj.PRDPrice = price
            new_product_obj.PRDDiscountPrice = discount
            if main_image:
                new_product_obj.product_image = main_image

            if name_image_1:
                new_product_obj.additional_image_1 = name_image_1

            if name_image_2:
                new_product_obj.additional_image_2 = name_image_2

            if name_image_3:
                new_product_obj.additional_image_3 = name_image_3

            if name_image_4:
                new_product_obj.additional_image_4 = name_image_4

            if digital_file:
                new_product_obj.digital_file = digital_file

            # new_product_obj.content=description,
            new_product_obj.product_vendor = product_vendor
            # if super_category_obj:
            new_product_obj.product_supercategory = super_category_obj
            # if main_category_obj:
            new_product_obj.product_maincategory = main_category_obj
            # if sub_category_obj:
            new_product_obj.product_subcategory = sub_category_obj
            # if mini_category_obj:
            new_product_obj.product_minicategor = mini_category_obj
            new_product_obj.available = available
            new_product_obj. pieces = pieces
            new_product_obj.promotional = promotional
            new_product_obj.PRDISactive = product_status
            new_product_obj.width = width
            new_product_obj.height = height
            # Note: Le champ PRDWeight n'existe pas dans le modèle Product
            # Le poids n'est pas stocké pour le moment
            new_product_obj.PRDSKU = product_SKU
            new_product_obj.PRDtags = tags
            try:
                new_product_obj.save()

            except Exception as e:
                messages.warning(request, "You can't Edit This Product ")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            product_variations_list = [XXS, XS, S, M, L, XL, XXL]
            for variation in product_variations_list:
                if "Delete" in variation:
                    variation = variation.replace('-Delete', '')

                    if ProductSize.objects.all().filter(PRDIProduct=new_product_obj, name_variation=variation).exists():
                        product_variations_obj = ProductSize.objects.get(
                            PRDIProduct=new_product_obj,
                            name_variation=variation
                        )

                        product_variations_obj.delete()

                else:
                    if ProductSize.objects.all().filter(PRDIProduct=new_product_obj, name_variation=variation).exists():
                        pass
                    else:
                        ProductSize.objects.create(
                            PRDIProduct=new_product_obj,
                            name_variation=variation
                        )

            messages.success(
                request, 'Votre produit a été modifié avec succès !')
            return redirect('supplier_dashboard:supplier-add-product')

    # product_obj = Product.objects.get(id=id)
    if product_obj.product_vendor.user.id == request.user.id:
        product = Product.objects.all().filter(
            product_vendor__user=request.user, id=id).exists()
        if product:
            product = Product.objects.get(
                product_vendor__user=request.user, id=id)
            product_images = ProductImage.objects.all().filter(PRDIProduct=product)
            product_variations = ProductSize.objects.all().filter(
                PRDIProduct=product)

    try:
        super_category = SuperCategory.objects.all()
        super_category_first = SuperCategory.objects.get(
            name=product.product_supercategory)
    except:
        super_category = None
    try:
        main_category = MainCategory.objects.all().filter(
            super_category=super_category_first)
        main_category_first = MainCategory.objects.get(
            name=product.product_maincategory)
    except:
        main_category = None
    try:
        sub_category = SubCategory.objects.all().filter(
            main_category=main_category_first)
        sub_category_first = SubCategory.objects.get(
            name=product.product_subcategory)
    except:
        sub_category = None
    try:
        mini_category = MiniCategory.objects.all().filter(
            sub_category=sub_category_first
        )
    except:
        mini_category = None
    # Récupération du vendeur et des produits pour le header
    vendor = Profile.objects.get(user=request.user)
    products = Product.objects.filter(
        product_vendor=vendor,
        PRDISDeleted=False
    ).order_by('-date')
    
    # print(sub_category)
    context = {
        "product": product,
        "product_variations": product_variations,
        "product_images": product_images,
        "super_category": super_category,
        "main_category": main_category,
        "sub_category": sub_category,
        "mini_category": mini_category,
        "vendor": vendor,
        "products": products,
    }
    return render(request, 'supplier-panel/supplier-edit-product.html', context)


@vendor_only
def supplier_orders_list(request):
    vendor = Profile.objects.get(user=request.user)
    context = {
        "vendor": vendor,
    }
    return render(request, 'supplier-panel/supplier-orders-list.html', context)


class SupplierOrdersJsonListView(View):
    def get(self, *args, **kwargs):
        user = Profile.objects.get(user=self.request.user)
        upper = int(self.request.GET.get('num_products'))
        order_by = self.request.GET.get('order_by')
        order_by_status = self.request.GET.get('order_by_status')

        lower = upper - 5
        if order_by_status == "All":
            orders_list = list(OrderSupplier.objects.all().filter(
                vendor=user, is_finished=True).values().order_by(order_by)[lower:upper])

            orders_size = len(OrderSupplier.objects.all().filter(
                vendor=user, is_finished=True))

            max_size = True if upper >= orders_size else False

        elif order_by_status == "Underway":
            orders_list = list(OrderSupplier.objects.all().filter(
                vendor=user, status="Underway", is_finished=True).values().order_by(order_by)[lower:upper])

            orders_size = len(OrderSupplier.objects.all().filter(
                vendor=user, status="Underway", is_finished=True))

            max_size = True if upper >= orders_size else False

        elif order_by_status == "COMPLETE":
            orders_list = list(OrderSupplier.objects.all().filter(
                vendor=user, status="COMPLETE", is_finished=True).values().order_by(order_by)[lower:upper])

            orders_size = len(OrderSupplier.objects.all().filter(
                vendor=user, status="COMPLETE", is_finished=True))

            max_size = True if upper >= orders_size else False

        else:
            orders_list = list(OrderSupplier.objects.all().filter(
                vendor=user, status="Refunded", is_finished=True).values().order_by(order_by)[lower:upper])

            orders_size = len(OrderSupplier.objects.all().filter(
                vendor=user, status="Refunded", is_finished=True))

            max_size = True if upper >= orders_size else False

        return JsonResponse({"data": orders_list,  "max": max_size, "orders_size": orders_size, }, safe=False)


@vendor_only
def supplier_orders_detail(request, id):
    user = Profile.objects.get(user=request.user)
    order_supplier = get_object_or_404(
        OrderSupplier, id=id, is_finished=True, vendor=user)
    payment_info = Payment.objects.get(order=order_supplier.order)
    order_details_supplier = OrderDetailsSupplier.objects.all().filter(
        order_supplier=order_supplier, supplier=request.user)
    
    # Récupérer la transaction SingPay si elle existe
    transaction = None
    try:
        from payments.models import SingPayTransaction
        transaction = SingPayTransaction.objects.filter(order=order_supplier.order).first()
    except:
        pass

    context = {
        "order_supplier": order_supplier,
        "order_details_supplier": order_details_supplier,
        "payment_info": payment_info,
        "transaction": transaction,
    }
    return render(request, 'supplier-panel/supplier-orders-detail.html', context)

# @vendor_only
# def supplier_transactions(request):
#     return render(request, 'supplier-panel/supplier-transactions.html')


# def page_settings_1(request):
#     return render(request, 'supplier-panel/page-settings-1.html')


# def page_settings_2(request):
#     return render(request, 'supplier-panel/page-settings-2.html')


@vendor_only
def store_settings(request):
    """
    Vue pour gérer les paramètres du magasin du vendeur.
    Permet de modifier :
    - Les informations du magasin (logo, nom, bio, coordonnées)
    - Les informations bancaires (compte bancaire)
    - Les informations d'adresse (province, ville, quartier, pays)
    """
    context = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        # Récupérer le profil du vendeur
        profile = Profile.objects.get(user=request.user)
        
        # Traitement du formulaire POST
        if request.method == 'POST':
            # Récupération des informations personnelles du vendeur
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            display_name = request.POST.get('display_name', '')  # Nom d'affichage du magasin
            bio = request.POST.get('bio', '')  # Description du magasin
            mobile_number = request.POST.get('mobile_number', '')
            
            # Récupération des informations d'adresse
            province = request.POST.get('province', '')
            city = request.POST.get('city', '')
            quartier = request.POST.get('quartier', '')  # Code postal / Quartier
            address = request.POST.get('address', '')
            country = request.POST.get('country', 'Gabon')
            
            # Mise à jour des informations de l'utilisateur (User model)
            user = request.user
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()
            
            # Traitement de l'upload de l'image du magasin
            try:
                image = request.FILES.get("image")
                if image:
                    # Validation de l'image avant sauvegarde
                    try:
                        Image.open(image)
                        profile.image = image
                    except:
                        messages.warning(request, 'Désolé, votre image est invalide')
                        return redirect("supplier_dashboard:store-settings")
            except:
                pass
            
            # Mise à jour du profil du vendeur (Profile model)
            if display_name:
                profile.display_name = display_name
            if bio:
                profile.bio = bio
            if mobile_number:
                profile.mobile_number = mobile_number
            if city:
                profile.city = city
            if address:
                profile.address = address
            if quartier:
                profile.post_code = quartier
            if country:
                profile.country = country
            if province:
                profile.state = province
            profile.save()
            
            messages.success(request, 'Vos informations ont été enregistrées avec succès !')
            return redirect("supplier_dashboard:store-settings")
        
        # Préparer le contexte pour l'affichage du formulaire
        context = {
            "profile": profile,
        }
        
        return render(request, 'supplier-panel/page-store-settings.html', context)

    else:
        messages.warning(request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def delete_account(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = Profile.objects.get(user=user)
            
            # Supprimer le profil (cela supprimera aussi les données liées via CASCADE)
            profile.delete()
            
            # Déconnecter l'utilisateur
            logout(request)
            
            # Supprimer l'utilisateur
            user.delete()
            
            messages.success(request, 'Votre compte a été supprimé avec succès.')
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, 'Une erreur est survenue lors de la suppression du compte.')
            return redirect("supplier_dashboard:store-settings")
    return redirect("supplier_dashboard:store-settings")


def get_boost_percentage(product):
    """
    Calcule le pourcentage de boost selon la catégorie du produit.
    
    Le système applique des tarifs variables pour les boosts de produits :
    - 15% pour les produits électroniques/technologie (haute valeur)
    - 12% pour les produits mode/lifestyle (valeur moyenne)
    - 8% pour les produits quotidiens (faible valeur)
    - 10% par défaut (moyenne)
    
    Args:
        product: Instance du modèle Product
        
    Returns:
        float: Pourcentage de boost (entre 8.0 et 15.0)
    """
    # Catégories avec pourcentages plus élevés (produits de valeur)
    # Ces produits ont généralement un prix plus élevé, donc un pourcentage plus élevé
    high_value_categories = ['électronique', 'électroniques', 'technologie', 'tech', 'informatique', 
                             'ordinateur', 'smartphone', 'téléphone', 'tablette', 'appareil']
    
    # Catégories avec pourcentages moyens (produits mode/lifestyle)
    # Produits avec une valeur moyenne, tarif intermédiaire
    medium_value_categories = ['mode', 'vêtement', 'habillement', 'accessoire', 'cosmétique', 
                               'beauté', 'parfum', 'bijou', 'montre']
    
    # Catégories avec pourcentages bas (produits quotidiens)
    # Produits de consommation courante, tarif réduit pour encourager les ventes
    low_value_categories = ['alimentaire', 'nourriture', 'boisson', 'hygiène', 'ménage', 
                           'quotidien', 'papeterie', 'fourniture', 'scolaire']
    
    # Vérifier d'abord la super catégorie (niveau le plus haut de la hiérarchie)
    if product.product_supercategory:
        super_cat_name = product.product_supercategory.name.lower()
        for high_cat in high_value_categories:
            if high_cat in super_cat_name:
                return 15.0  # 15% pour produits électroniques/technologie
        for medium_cat in medium_value_categories:
            if medium_cat in super_cat_name:
                return 12.0  # 12% pour produits mode/lifestyle
        for low_cat in low_value_categories:
            if low_cat in super_cat_name:
                return 8.0   # 8% pour produits quotidiens
    
    # Si aucune correspondance dans la super catégorie, vérifier la catégorie principale
    if product.product_maincategory:
        main_cat_name = product.product_maincategory.name.lower()
        for high_cat in high_value_categories:
            if high_cat in main_cat_name:
                return 15.0
        for medium_cat in medium_value_categories:
            if medium_cat in main_cat_name:
                return 12.0
        for low_cat in low_value_categories:
            if low_cat in main_cat_name:
                return 8.0
    
    # Par défaut, utiliser 10% (moyenne) si aucune catégorie ne correspond
    return 10.0


@vendor_only
def subscriptions(request):
    if request.user.is_authenticated and not request.user.is_anonymous:
        profile = Profile.objects.get(user=request.user)
        
        # Get vendor products with category and price info
        products = Product.objects.filter(product_vendor=profile, PRDISactive=True).order_by('-date')
        
        # Prepare products data with boost calculation info
        products_data = []
        for product in products:
            # Calculate boost percentage based on category
            boost_percentage = get_boost_percentage(product)
            product_price = product.PRDPrice or 0
            boost_price_per_week = (product_price * boost_percentage / 100) if product_price > 0 else 0
            
            products_data.append({
                'id': product.id,
                'name': product.product_name,
                'price': product_price,
                'boost_percentage': boost_percentage,
                'boost_price_per_week': boost_price_per_week,
                'super_category': product.product_supercategory.name if product.product_supercategory else None,
                'main_category': product.product_maincategory.name if product.product_maincategory else None,
            })
        
        # Handle POST requests
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'toggle_subscription':
                # Initialiser le paiement d'abonnement premium via SingPay
                from supplier_panel.singpay_services import B2CSingPayService
                from django.http import JsonResponse
                
                try:
                    success, response = B2CSingPayService.init_subscription_payment(profile, request)
                    
                    if success:
                        # Rediriger vers la page de paiement SingPay
                        singpay_transaction = response
                        payment_url = singpay_transaction.payment_url
                        
                        # Si c'est une requête AJAX, retourner JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'payment_url': payment_url,
                                'message': 'Redirection vers le paiement...'
                            })
                        
                        # Sinon, rediriger directement
                        return redirect(payment_url)
                    else:
                        error_msg = response.get('error', 'Erreur lors de l\'initialisation du paiement')
                        messages.error(request, f'Erreur: {error_msg}')
                        return redirect('supplier_dashboard:subscriptions')
                        
                except Exception as e:
                    logger.exception(f"Erreur lors de l'initialisation du paiement d'abonnement: {str(e)}")
                    messages.error(request, f'Une erreur est survenue: {str(e)}')
                    return redirect('supplier_dashboard:subscriptions')
            
            elif action == 'request_boost':
                product_id = request.POST.get('product_id')
                boost_duration = request.POST.get('boost_duration', '7')
                
                if product_id:
                    try:
                        from accounts.models import ProductBoostRequest
                        from django.utils import timezone
                        
                        product = Product.objects.get(id=product_id, product_vendor=profile)
                        
                        # Calculer le pourcentage de boost selon la catégorie
                        boost_percentage = get_boost_percentage(product)
                        
                        # Calculer le prix du boost
                        # Le prix est calculé par semaine, donc on multiplie par le nombre de semaines
                        product_price = product.PRDPrice or 0
                        boost_price_per_week = (product_price * boost_percentage / 100)  # Prix par semaine
                        number_of_weeks = int(boost_duration) / 7.0  # Nombre de semaines
                        total_price = boost_price_per_week * number_of_weeks
                        
                        # Vérifier si une demande en attente existe déjà pour ce produit
                        existing_request = ProductBoostRequest.objects.filter(
                            vendor=profile,
                            product=product,
                            status=ProductBoostRequest.PENDING
                        ).first()
                        
                        if existing_request:
                            messages.warning(request, f'Une demande de boost est déjà en attente pour "{product.product_name}". Veuillez attendre la validation de l\'administrateur.')
                            return redirect('supplier_dashboard:subscriptions')
                        
                        # Créer la demande de boost
                        boost_request = ProductBoostRequest.objects.create(
                            vendor=profile,
                            product=product,
                            duration_days=int(boost_duration),
                            boost_percentage=boost_percentage,
                            price=total_price,
                            payment_status=False,
                            status=ProductBoostRequest.PENDING
                        )
                        
                        # Initialiser le paiement SingPay directement
                        from supplier_panel.singpay_services import B2CSingPayService
                        from django.http import JsonResponse
                        
                        try:
                            success, response = B2CSingPayService.init_boost_payment(boost_request, request)
                            
                            if success:
                                # Rediriger vers la page de paiement SingPay
                                singpay_transaction = response
                                payment_url = singpay_transaction.payment_url
                                
                                # Si c'est une requête AJAX, retourner JSON
                                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                    return JsonResponse({
                                        'success': True,
                                        'payment_url': payment_url,
                                        'message': 'Redirection vers le paiement...'
                                    })
                                
                                # Sinon, rediriger directement
                                return redirect(payment_url)
                            else:
                                error_msg = response.get('error', 'Erreur lors de l\'initialisation du paiement')
                                messages.error(request, f'Erreur lors du paiement: {error_msg}')
                                return redirect('supplier_dashboard:subscriptions')
                                
                        except Exception as e:
                            logger.exception(f"Erreur lors de l'initialisation du paiement de boost: {str(e)}")
                            messages.error(request, f'Une erreur est survenue lors du paiement: {str(e)}')
                            return redirect('supplier_dashboard:subscriptions')
                    except Product.DoesNotExist:
                        messages.error(request, 'Produit introuvable.')
                    except Exception as e:
                        messages.error(request, f'Une erreur est survenue lors de la création de la demande: {str(e)}')
                else:
                    messages.error(request, 'Veuillez sélectionner un produit.')
        
        # Calculate commissions
        # Total commissions from all completed orders
        completed_orders = OrderSupplier.objects.filter(
            vendor=profile,
            status='COMPLETE'
        )
        total_commissions = 0
        for order in completed_orders:
            try:
                amount = float(order.amount.replace(',', '').replace(' ', ''))
                # Assuming 10% commission rate (adjust as needed)
                commission = amount * 0.10
                total_commissions += commission
            except (ValueError, AttributeError):
                pass
        
        # Monthly commissions (current month)
        today = date.today()
        first_day_month = date(today.year, today.month, 1)
        monthly_orders = completed_orders.filter(order_date__gte=first_day_month)
        monthly_commissions = 0
        for order in monthly_orders:
            try:
                amount = float(order.amount.replace(',', '').replace(' ', ''))
                commission = amount * 0.10
                monthly_commissions += commission
            except (ValueError, AttributeError):
                pass
        
        # Pending commissions (orders in progress)
        pending_orders = OrderSupplier.objects.filter(
            vendor=profile,
            status__in=['PENDING', 'Underway']
        )
        pending_commissions = 0
        for order in pending_orders:
            try:
                amount = float(order.amount.replace(',', '').replace(' ', ''))
                commission = amount * 0.10
                pending_commissions += commission
            except (ValueError, AttributeError):
                pass
        
        # Calculate badges based on vendor performance
        vendor_badges = {
            'premium': False,  # Would check subscription status
            'top_seller': False,
            'fast_shipping': False,
            'excellent_rating': False,
            'verified': profile.admission,  # Using admission as verification
            'new_seller': False,
        }
        
        # Top Seller: More than 100 sales
        total_sales = completed_orders.count()
        if total_sales >= 100:
            vendor_badges['top_seller'] = True
        
        # New Seller: Registered less than 30 days ago
        if profile.date:
            days_since_registration = (today - profile.date.date()).days
            if days_since_registration <= 30:
                vendor_badges['new_seller'] = True
        
        # Excellent Rating: Average rating >= 4.5
        ratings = ProductRating.objects.filter(
            PRDIProduct__product_vendor=profile
        )
        if ratings.exists():
            avg_rating = sum(r.rate for r in ratings) / ratings.count()
            if avg_rating >= 4.5:
                vendor_badges['excellent_rating'] = True
        
        # Fast Shipping: Would check order fulfillment times (simplified)
        # For now, we'll check if most orders are completed quickly
        fast_orders = 0
        for order in completed_orders[:10]:  # Check last 10 orders
            if order.date_update and order.order_date:
                days_to_complete = (order.date_update.date() - order.order_date.date()).days
                if days_to_complete <= 1:
                    fast_orders += 1
        if fast_orders >= 7:  # 70% of orders completed within 1 day
            vendor_badges['fast_shipping'] = True
        
        # Subscription status - vérifier l'abonnement premium actif
        subscription_active = False
        try:
            from accounts.models import PremiumSubscription
            premium_sub = PremiumSubscription.objects.filter(vendor=profile).first()
            if premium_sub and premium_sub.is_active():
                subscription_active = True
        except:
            pass
        
        # Récupérer les demandes de boost du vendeur
        boost_requests = []
        try:
            from accounts.models import ProductBoostRequest
            boost_requests = ProductBoostRequest.objects.filter(
                vendor=profile
            ).order_by('-created_date')[:10]  # Les 10 dernières demandes
        except:
            pass
        
        context = {
            'vendor': profile,
            'products': products,
            'products_data': products_data,  # Products with boost calculation data
            'total_commissions': int(total_commissions),
            'monthly_commissions': int(monthly_commissions),
            'pending_commissions': int(pending_commissions),
            'vendor_badges': vendor_badges,
            'subscription_active': subscription_active,
            'boost_requests': boost_requests,
        }
        
        return render(request, 'supplier-panel/page-subscriptions.html', context)
    
    else:
        messages.warning(request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def subscription_success(request):
    """
    Page de succès après paiement d'abonnement premium
    """
    if request.user.is_authenticated and not request.user.is_anonymous:
        profile = Profile.objects.get(user=request.user)
        
        # Récupérer l'abonnement actif
        subscription = None
        try:
            from accounts.models import PremiumSubscription
            subscription = PremiumSubscription.objects.filter(
                vendor=profile,
                status=PremiumSubscription.ACTIVE
            ).first()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la récupération de l'abonnement: {str(e)}")
        
        context = {
            'vendor': profile,
            'subscription': subscription,
        }
        
        return render(request, 'supplier-panel/subscription-success.html', context)
    else:
        messages.warning(request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def boost_success(request, boost_request_id):
    """
    Page de succès après paiement de boost
    """
    if request.user.is_authenticated and not request.user.is_anonymous:
        profile = Profile.objects.get(user=request.user)
        
        # Récupérer la demande de boost
        boost_request = None
        try:
            from accounts.models import ProductBoostRequest
            boost_request = ProductBoostRequest.objects.get(
                id=boost_request_id,
                vendor=profile
            )
        except ProductBoostRequest.DoesNotExist:
            messages.error(request, 'Demande de boost introuvable.')
            return redirect('supplier_dashboard:subscriptions')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la récupération du boost: {str(e)}")
            messages.error(request, 'Une erreur est survenue.')
            return redirect('supplier_dashboard:subscriptions')
        
        context = {
            'vendor': profile,
            'boost_request': boost_request,
        }
        
        return render(request, 'supplier-panel/boost-success.html', context)
    else:
        messages.warning(request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def payments(request):
    if request.user.is_authenticated and not request.user.is_anonymous:
        vendor = Profile.objects.get(user=request.user)
        payments = VendorPayments.objects.all().filter(
            vendor_profile__username=request.user)
        bank_info_obj = BankAccount.objects.filter(
            vendor_profile__user=request.user).first()

        paginator = Paginator(payments, 10)
        page = request.GET.get('page')
        try:
            payments = paginator.page(page)
        except PageNotAnInteger:
            payments = paginator.page(1)
        except EmptyPage:
            payments = paginator.page(paginator.num_page)
        
        # Calculer les récettes totales (commandes complétées)
        completed_orders = OrderSupplier.objects.filter(
            vendor=vendor,
            status='COMPLETE'
        )
        total_revenue = 0
        for order in completed_orders:
            try:
                amount = float(str(order.amount).replace(',', '').replace(' ', ''))
                total_revenue += amount
            except (ValueError, AttributeError, TypeError):
                pass
        
        # Calculer les récettes par période
        today = date.today()
        
        # Récettes du jour
        today_start = tz.make_aware(datetime.combine(today, datetime.min.time()))
        today_orders = completed_orders.filter(order_date__gte=today_start)
        daily_revenue = 0
        for o in today_orders:
            if o.amount:
                try:
                    daily_revenue += float(str(o.amount).replace(',', '').replace(' ', ''))
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # Récettes de la semaine (7 derniers jours)
        week_start = today - timedelta(days=7)
        week_start_dt = tz.make_aware(datetime.combine(week_start, datetime.min.time()))
        week_orders = completed_orders.filter(order_date__gte=week_start_dt)
        weekly_revenue = 0
        for o in week_orders:
            if o.amount:
                try:
                    weekly_revenue += float(str(o.amount).replace(',', '').replace(' ', ''))
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # Récettes du mois
        month_start = date(today.year, today.month, 1)
        month_start_dt = tz.make_aware(datetime.combine(month_start, datetime.min.time()))
        month_orders = completed_orders.filter(order_date__gte=month_start_dt)
        monthly_revenue = 0
        for o in month_orders:
            if o.amount:
                try:
                    monthly_revenue += float(str(o.amount).replace(',', '').replace(' ', ''))
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # Récettes de l'année
        year_start = date(today.year, 1, 1)
        year_start_dt = tz.make_aware(datetime.combine(year_start, datetime.min.time()))
        year_orders = completed_orders.filter(order_date__gte=year_start_dt)
        yearly_revenue = 0
        for o in year_orders:
            if o.amount:
                try:
                    yearly_revenue += float(str(o.amount).replace(',', '').replace(' ', ''))
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # Statistiques de facturation des services
        # Abonnements premium (simulé - à remplacer par un vrai modèle)
        subscription_stats = {
            'active': False,
            'total_paid': 0,
            'monthly_cost': 0,
            'start_date': None,
            'end_date': None,
        }
        
        # Statistiques des boosts (simulé - à remplacer par un vrai modèle)
        boost_stats = {
            'total_requests': 0,
            'approved': 0,
            'pending': 0,
            'rejected': 0,
            'total_spent': 0,
            'monthly_spent': 0,
        }
        
        context = {
            "vendor": vendor,
            "payments": payments,
            "bank_info_obj": bank_info_obj,
            "paginator": paginator,
            "page": page,
            "total_revenue": total_revenue,
            "daily_revenue": daily_revenue,
            "weekly_revenue": weekly_revenue,
            "monthly_revenue": monthly_revenue,
            "yearly_revenue": yearly_revenue,
            "subscription_stats": subscription_stats,
            "boost_stats": boost_stats,
        }
        return render(request, 'supplier-panel/page-payments-detail.html', context)
    else:
        messages.warning(
            request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def request_payment(request):
    if request.user.is_authenticated and not request.user.is_anonymous:
        if request.method == 'POST':
            try:
                request_amount = float(request.POST["request_amount"])
                description = request.POST["description"]
                profile = Profile.objects.get(user=request.user)
                method = request.POST["method"]
                if profile.blance >= request_amount:
                    profile.requested = request_amount
                    profile.blance = profile.blance - request_amount
                    if method in ("Bank", "SingPay"):
                        VendorPayments.objects.create(
                            vendor_profile=request.user,
                            request_amount=request_amount,
                            method=method,
                            description=description,
                        )
                        profile.save()
                        messages.success(
                            request, '-Your request has been received')
                        return redirect("supplier_dashboard:payments")
                else:

                    messages.warning(
                        request, '-You do not have this amount')
                    return redirect("supplier_dashboard:payments")
            except (ValueError, TypeError):
                messages.warning(request, '-Please Enter A Valid number')
                return redirect("supplier_dashboard:payments")

        return redirect("supplier_dashboard:payments")
    else:
        messages.warning(
            request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def get_notifications(request):
    """Retourne les notifications (nouvelles commandes) en JSON"""
    vendor = Profile.objects.get(user=request.user)
    pending_orders = OrderSupplier.objects.filter(
        vendor=vendor, 
        status='PENDING'
    ).order_by('-order_date')[:10]
    
    # Récupérer les notifications lues depuis la session
    read_notifications = request.session.get('read_notifications', [])
    if not isinstance(read_notifications, list):
        read_notifications = []
    
    # Filtrer les commandes pour exclure celles déjà lues
    unread_orders = [order for order in pending_orders if order.id not in read_notifications]
    
    notifications = []
    for order in unread_orders:
        notifications.append({
            'id': order.id,
            'title': f'Nouvelle commande #{order.id}',
            'time': order.order_date.strftime('%d/%m/%Y %H:%M'),
            'time_ago': order.order_date.strftime('%d/%m/%Y à %H:%M'),
            'amount': order.amount,
        })
    
    # Compter uniquement les notifications non lues
    total_count = len(unread_orders)
    
    return JsonResponse({
        'notifications': notifications,
        'count': total_count
    })


@vendor_only
def mark_notification_read(request, notification_id):
    """Marque une notification comme lue"""
    if request.method == 'POST':
        # Récupérer les notifications lues depuis la session
        read_notifications = request.session.get('read_notifications', [])
        if not isinstance(read_notifications, list):
            read_notifications = []
        
        # Ajouter l'ID de la notification à la liste des lues
        if notification_id not in read_notifications:
            read_notifications.append(notification_id)
            request.session['read_notifications'] = read_notifications
            request.session.modified = True
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@vendor_only
def mark_all_notifications_read(request):
    """Marque toutes les notifications comme lues"""
    if request.method == 'POST':
        vendor = Profile.objects.get(user=request.user)
        pending_orders = OrderSupplier.objects.filter(
            vendor=vendor, 
            status='PENDING'
        )
        
        # Récupérer tous les IDs des commandes en attente
        all_order_ids = list(pending_orders.values_list('id', flat=True))
        
        # Mettre à jour la session avec tous les IDs
        request.session['read_notifications'] = all_order_ids
        request.session.modified = True
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def supplier_reviews(request):
    if request.user.is_authenticated and not request.user.is_anonymous:
        profile = Profile.objects.get(user=request.user)
        reviews = ProductRating.objects.all().filter(vendor=profile)
        paginator = Paginator(reviews, 10)
        page = request.GET.get('page')
        try:
            reviews = paginator.page(page)
        except PageNotAnInteger:
            reviews = paginator.page(1)
        except EmptyPage:
            reviews = paginator.page(paginator.num_page)
        context = {
            "reviews": reviews,
            "paginator": paginator,
            "page": page,
        }
        return render(request, "supplier-panel/supplier-reviews.html", context)

    else:
        messages.warning(
            request, '-Please Login First To see This Page !')
        return redirect('accounts:login')
