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
    def get(self, *args, **kwargs):
        today = date.today()
        if self.request.user.is_authenticated and not self.request.user.is_anonymous:
            vendor = Profile.objects.get(user=self.request.user)

            product_count_list = []
            order_count_list = []
            for i in range(1, 13):
                product_count = Product.objects.filter(
                    product_vendor=vendor,  date__year=today.year, date__month=i,).count()
                product_count_list.append(product_count)
                order_count = OrderSupplier.objects.all().filter(vendor=vendor, order_date__year=today.year,
                                                                 order_date__month=i,).exclude(status="PENDING").count()
                order_count_list.append(order_count)

            return JsonResponse({"product_count_list": product_count_list, "order_count_list": order_count_list, }, safe=False)


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


@vendor_only
def supplier_products_list(request):
    vendor = Profile.objects.get(user=request.user)
    super_categories = SuperCategory.objects.all()
    
    context = {
        "vendor": vendor,
        "super_category": super_categories,
    }
    return render(request, "supplier-panel/supplier-products-list.html", context)


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
            return redirect('supplier_dashboard:supplier-products-list')
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

    context = {
        "order_supplier": order_supplier,
        "order_details_supplier": order_details_supplier,
        "payment_info": payment_info,
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
def bank_info(request):
    context = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        if request.method == 'POST':
            bank_name = request.POST["bank_name"]
            account_number = request.POST["account_number"]
            account_name = request.POST["account_name"]
            swift_code = request.POST["swift_code"]
            country = request.POST["country"]
            paypal_email = request.POST["paypal_email"]
            description = request.POST["description"]
            profile = Profile.objects.get(user=request.user)
            if BankAccount.objects.all().filter(vendor_profile=profile,).exists():
                old_bank_info = BankAccount.objects.get(
                    vendor_profile=profile,)
                old_bank_info.bank_name = bank_name

                old_bank_info.account_number = account_number
                old_bank_info.account_name = account_name
                old_bank_info.swift_code = swift_code
                old_bank_info.country = country
                old_bank_info.paypal_email = paypal_email
                old_bank_info.description = description
                old_bank_info.save()
                messages.success(
                    request, 'Your Bank Info Has Been Saved !')
                # return redirect("supplier_dashboard:bank-info")

            else:
                new_bank_info = BankAccount.objects.create(
                    vendor_profile=profile,
                    bank_name=bank_name,
                    account_number=account_number,
                    account_name=account_name,
                    swift_code=swift_code,
                    country=country,
                    paypal_email=paypal_email,
                    description=description,
                )
                messages.success(
                    request, 'Your Bank Info Has Been Saved !')
                # return redirect("supplier_dashboard:bank-info")
        if BankAccount.objects.all().filter(vendor_profile__user=request.user,).exists():
            bank_info_obj = BankAccount.objects.get(
                vendor_profile__user=request.user,)
            context = {
                "bank_info_obj": bank_info_obj,
            }
        return render(request, 'supplier-panel/page-bank-info.html', context)

    else:
        messages.warning(
            request, '-Please Login First To see This Page !')
        return redirect('accounts:login')


@vendor_only
def social_links(request):
    context = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        if request.method == 'POST':
            facebook = request.POST["facebook"]
            twitter = request.POST["twitter"]
            instagram = request.POST["instagram"]
            pinterest = request.POST["pinterest"]

            profile = Profile.objects.get(user=request.user)
            if SocialLink.objects.all().filter(vendor_profile=profile,).exists():
                old_social_links = SocialLink.objects.get(
                    vendor_profile=profile,)
                old_social_links.facebook = facebook
                old_social_links.twitter = twitter
                old_social_links.instagram = instagram
                old_social_links.pinterest = pinterest
                old_social_links.save()
                messages.success(
                    request, 'Your Social Links Has Been Saved !')
                # return redirect("supplier_dashboard:bank-info")

            else:
                new_social_links = SocialLink.objects.create(
                    vendor_profile=profile,
                    facebook=facebook,
                    twitter=twitter,
                    instagram=instagram,
                    pinterest=pinterest,
                )
                messages.success(
                    request, 'Your  Social Links Has Been Saved !')
                # return redirect("supplier_dashboard:bank-info")
        if SocialLink.objects.all().filter(vendor_profile__user=request.user,).exists():
            social_links_obj = SocialLink.objects.get(
                vendor_profile__user=request.user,)
            context = {
                "social_links_obj": social_links_obj,
            }
        return render(request, 'supplier-panel/page-social-links.html', context)

    else:
        messages.warning(
            request, '-Please Login First To see This Page !')
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
        context = {
            "vendor": vendor,
            "payments": payments,
            "bank_info_obj": bank_info_obj,
            "paginator": paginator,
            "page": page,
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
                    if method == "Paypal" or method == "Bank":
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
    
    total_count = OrderSupplier.objects.filter(
        vendor=vendor, 
        status='PENDING'
    ).count()
    
    notifications = []
    for order in pending_orders:
        notifications.append({
            'id': order.id,
            'title': f'Nouvelle commande #{order.id}',
            'time': order.order_date.strftime('%d/%m/%Y %H:%M'),
            'time_ago': order.order_date.strftime('%d/%m/%Y à %H:%M'),
            'amount': order.amount,
        })
    
    return JsonResponse({
        'notifications': notifications,
        'count': total_count
    })

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
