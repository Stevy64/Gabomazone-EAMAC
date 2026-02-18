from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from PIL import Image
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .utils import code_generator, create_shortcode
import random
import string


class Profile(models.Model):
    image = models.ImageField(
        upload_to='profile_pic/', blank=True, null=True, )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True, )
    display_name = models.CharField(max_length=100, blank=True, null=True, )
    bio = models.TextField(blank=True, null=True)
    mobile_number = models.CharField(max_length=100, blank=True, null=True, )
    address = models.CharField(max_length=100, blank=True, null=True, )
    city = models.CharField(max_length=100, blank=True, null=True, )
    post_code = models.CharField(max_length=100, blank=True, null=True, )
    country = models.CharField(max_length=100, blank=True, null=True, )
    state = models.CharField(max_length=100, blank=True, null=True, )

    customer = 'customer'
    vendor = 'vendor'
    account_select = [
        (customer, 'customer'),
        (vendor, 'vendor'),
    ]
    status = models.CharField(
        max_length=13,
        choices=account_select,
        default=customer,
        blank=True, null=True,
    )
    admission = models.BooleanField(default=False, verbose_name=_("admission") , blank=True, null=True)
    code = models.CharField(max_length=250, blank=True, null=True)
    recommended_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommended_by", blank=True, null=True)
    referrals = models.IntegerField(default=0, blank=True, null=True)
    blance = models.FloatField(default=0.00, blank=True, null=True)
    requested = models.FloatField(default=0.00, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)
    slug = models.SlugField(
        blank=True, null=True, allow_unicode=True, unique=True, verbose_name=_("Slugfiy"))

    def __str__(self):
        return self.user.username


class PeerToPeerProduct(models.Model):
    """Modèle pour les articles vendus C2C"""
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='peer_to_peer_products', verbose_name=_("Vendeur"))
    product_name = models.CharField(max_length=150, verbose_name=_("Nom du produit"))
    product_description = models.TextField(verbose_name=_("Description"))
    product_image = models.ImageField(
        upload_to='peer_to_peer/imgs/', default='peer_to_peer/product.jpg', max_length=500, verbose_name=_("Image du produit"))
    
    # Catégories
    product_supercategory = models.ForeignKey(
        'categories.SuperCategory', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Super Catégorie"))
    product_maincategory = models.ForeignKey(
        'categories.MainCategory', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Catégorie principale"))
    product_subcategory = models.ForeignKey(
        'categories.SubCategory', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Sous-catégorie"))
    
    # Prix et commission
    PRDPrice = models.FloatField(verbose_name=_("Prix"))
    commission_rate = models.FloatField(default=0.20, verbose_name=_("Taux de commission (20%)"))
    commission_amount = models.FloatField(blank=True, null=True, verbose_name=_("Montant de la commission"))
    seller_amount = models.FloatField(blank=True, null=True, verbose_name=_("Montant pour le vendeur"))
    
    # Images supplémentaires
    additional_image_1 = models.ImageField(
        upload_to='peer_to_peer/imgs/', blank=True, null=True, max_length=500, verbose_name=_("Image supplémentaire 1"))
    additional_image_2 = models.ImageField(
        upload_to='peer_to_peer/imgs/', blank=True, null=True, max_length=500, verbose_name=_("Image supplémentaire 2"))
    additional_image_3 = models.ImageField(
        upload_to='peer_to_peer/imgs/', blank=True, null=True, max_length=500, verbose_name=_("Image supplémentaire 3"))
    additional_image_4 = models.ImageField(
        upload_to='peer_to_peer/imgs/', blank=True, null=True, max_length=500, verbose_name=_("Image supplémentaire 4"))
    
    # Statut
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    SOLD = 'SOLD'
    CANCELLED = 'CANCELLED'
    
    Status_select = [
        (PENDING, 'En attente'),
        (APPROVED, 'Approuvé'),
        (REJECTED, 'Rejeté'),
        (SOLD, 'Vendu'),
        (CANCELLED, 'Annulé'),
    ]
    status = models.CharField(
        max_length=13,
        choices=Status_select,
        default=PENDING,
        verbose_name=_("Statut")
    )
    
    # État de l'article (occasion) — valeurs sans tiret (ex. BON ETAT)
    NEUF = 'NEUF'
    COMME_NEUF = 'COMME NEUF'
    BON_ETAT = 'BON ETAT'
    UTILISABLE = 'UTILISABLE'
    CONDITION_CHOICES = [
        (NEUF, _('Neuf')),
        (COMME_NEUF, _('Comme neuf')),
        (BON_ETAT, _('Bon état')),
        (UTILISABLE, _('Utilisable')),
    ]
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default=BON_ETAT,
        blank=True,
        verbose_name=_("État de l'article")
    )

    # Informations de contact
    seller_phone = models.CharField(max_length=20, verbose_name=_("Téléphone du vendeur"))
    seller_address = models.TextField(verbose_name=_("Adresse du vendeur"))
    seller_city = models.CharField(max_length=100, verbose_name=_("Ville"))
    
    # Dates
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_update = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    approved_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'approbation"))
    
    # Slug pour l'URL
    PRDSlug = models.SlugField(
        max_length=150, blank=True, null=True, allow_unicode=True, unique=True, verbose_name=_("Slug"))
    
    # Compteur de vues
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de vues"))
    
    class Meta:
        ordering = ('-date',)
        verbose_name = _("Article C2C")
        verbose_name_plural = _("Articles C2C")
    
    def __str__(self):
        return f"{self.product_name} - {self.seller.username}"
    
    def calculate_commission(self):
        """Calcule la commission de 20% et le montant pour le vendeur"""
        if self.PRDPrice:
            self.commission_amount = self.PRDPrice * self.commission_rate
            self.seller_amount = self.PRDPrice - self.commission_amount
            return self.commission_amount, self.seller_amount
        return 0, 0
    
    def save(self, *args, **kwargs):
        # Calculer la commission avant de sauvegarder
        self.calculate_commission()
        super().save(*args, **kwargs)


def generate_delivery_code():
    """Génère un code de livraison unique de 8 caractères"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not DeliveryCode.objects.filter(code=code).exists():
            return code


class DeliveryCode(models.Model):
    """Modèle pour gérer les codes de livraison"""
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='delivery_codes', verbose_name=_("Commande"), blank=True, null=True)
    peer_to_peer_product = models.ForeignKey(
        PeerToPeerProduct, on_delete=models.CASCADE, related_name='delivery_codes', verbose_name=_("Article"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Code de livraison"))
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='delivery_codes_received', verbose_name=_("Acheteur"))
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='delivery_codes_sent', verbose_name=_("Vendeur"))
    
    # Statut du code
    PENDING = 'PENDING'
    VERIFIED = 'VERIFIED'
    EXPIRED = 'EXPIRED'
    
    Status_select = [
        (PENDING, 'En attente'),
        (VERIFIED, 'Vérifié'),
        (EXPIRED, 'Expiré'),
    ]
    status = models.CharField(
        max_length=13,
        choices=Status_select,
        default=PENDING,
        verbose_name=_("Statut")
    )
    
    # Dates
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    verified_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de vérification"))
    expires_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'expiration"))
    
    class Meta:
        ordering = ('-created_date',)
        verbose_name = _("Code de livraison")
        verbose_name_plural = _("Codes de livraison")
    
    def __str__(self):
        return f"Code {self.code} - {self.buyer.username}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_delivery_code()
        super().save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     return super().save(*args, **kwargs)


class PeerToPeerOrderNotification(models.Model):
    """Modèle pour les notifications de commande peer-to-peer"""
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='peer_notifications', verbose_name=_("Commande"))
    order_detail = models.ForeignKey(
        'orders.OrderDetails', on_delete=models.CASCADE, related_name='peer_notifications', verbose_name=_("Détail de commande"))
    peer_product = models.ForeignKey(
        PeerToPeerProduct, on_delete=models.CASCADE, related_name='order_notifications', verbose_name=_("Article"))
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='peer_order_notifications', verbose_name=_("Vendeur"))
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='peer_orders_made', verbose_name=_("Acheteur"))
    
    # Statut de la notification
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'
    
    Status_select = [
        (PENDING, 'En attente'),
        (ACCEPTED, 'Acceptée'),
        (REJECTED, 'Refusée'),
        (CANCELLED, 'Annulée'),
    ]
    status = models.CharField(
        max_length=13,
        choices=Status_select,
        default=PENDING,
        verbose_name=_("Statut")
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    responded_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de réponse"))
    
    # Message du vendeur (optionnel)
    seller_message = models.TextField(blank=True, null=True, verbose_name=_("Message du vendeur"))
    
    # Indicateur de lecture
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Notification de commande peer-to-peer")
        verbose_name_plural = _("Notifications de commande peer-to-peer")
    
    def __str__(self):
        return f"Commande #{self.order.id} - {self.peer_product.product_name}"


class ProductConversation(models.Model):
    """Modèle pour les conversations entre vendeur et acheteur pour un article"""
    product = models.ForeignKey(
        PeerToPeerProduct, on_delete=models.CASCADE, related_name='conversations', verbose_name=_("Article"))
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='seller_conversations', verbose_name=_("Vendeur"))
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='buyer_conversations', verbose_name=_("Acheteur"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    
    # Indicateur de dernière activité
    last_message_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Dernier message"))
    
    # Archivage
    is_archived_by_seller = models.BooleanField(default=False, verbose_name=_("Archivé par le vendeur"))
    is_archived_by_buyer = models.BooleanField(default=False, verbose_name=_("Archivé par l'acheteur"))
    archived_at_seller = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'archivage (vendeur)"))
    archived_at_buyer = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'archivage (acheteur)"))
    
    class Meta:
        ordering = ('-last_message_at',)
        unique_together = ('product', 'buyer')
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
    
    def __str__(self):
        return f"Conversation - {self.product.product_name} - {self.buyer.username}"
    
    def get_unread_count_for_seller(self):
        """Retourne le nombre de messages non lus pour le vendeur"""
        return self.messages.filter(is_read=False, sender=self.buyer).count()
    
    def get_unread_count_for_buyer(self):
        """Retourne le nombre de messages non lus pour l'acheteur"""
        return self.messages.filter(is_read=False, sender=self.seller).count()
    
    def archive_for_user(self, user):
        """Archive la conversation pour un utilisateur"""
        from django.utils import timezone
        if user == self.seller:
            self.is_archived_by_seller = True
            self.archived_at_seller = timezone.now()
        elif user == self.buyer:
            self.is_archived_by_buyer = True
            self.archived_at_buyer = timezone.now()
        self.save()
    
    def unarchive_for_user(self, user):
        """Désarchive la conversation pour un utilisateur"""
        if user == self.seller:
            self.is_archived_by_seller = False
            self.archived_at_seller = None
        elif user == self.buyer:
            self.is_archived_by_buyer = False
            self.archived_at_buyer = None
        self.save()
    
    def is_archived_for_user(self, user):
        """Vérifie si la conversation est archivée pour un utilisateur"""
        if user == self.seller:
            return self.is_archived_by_seller
        elif user == self.buyer:
            return self.is_archived_by_buyer
        return False
    
    def get_c2c_order(self):
        """Retourne la commande C2C associée si elle existe"""
        from c2c.models import PurchaseIntent
        try:
            intent = PurchaseIntent.objects.filter(
                product=self.product,
                buyer=self.buyer,
                seller=self.seller
            ).first()
            if intent:
                return getattr(intent, 'c2c_order', None)
        except Exception:
            pass
        return None
    
    def get_purchase_intent(self):
        """Retourne l'intention d'achat associée si elle existe"""
        from c2c.models import PurchaseIntent
        try:
            return PurchaseIntent.objects.filter(
                product=self.product,
                buyer=self.buyer,
                seller=self.seller
            ).first()
        except Exception:
            return None


class ProductMessage(models.Model):
    """Modèle pour les messages dans une conversation"""
    conversation = models.ForeignKey(
        ProductConversation, on_delete=models.CASCADE, related_name='messages', verbose_name=_("Conversation"))
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name=_("Expéditeur"))
    message = models.TextField(verbose_name=_("Message"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    
    # Indicateur de lecture
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de lecture"))
    
    class Meta:
        ordering = ('created_at',)
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
    
    def __str__(self):
        return f"Message de {self.sender.username} - {self.created_at}"
    
    def mark_as_read(self):
        """Marque le message comme lu"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

        if self.code is None or self.code == "":
            # code = generate_ref_code()
            # self.code = code
            self.code = f'{self.user}'

        # img = Image.open(self.image.path)
        # if img.width > 300 or img.height > 300:
        #     out_size = (300, 300)
        #     img.thumbnail(out_size)
        #     img.save(self.image.path)

        super().save(*args, **kwargs)


def create_profile(sender, **kwargs):
    if kwargs['created']:
        user_profile = Profile.objects.create(
            user=kwargs['instance'], )


post_save.connect(create_profile, sender=User)



class BankAccount(models.Model):
    vendor_profile = models.OneToOneField(
        Profile, on_delete=models.SET_NULL, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True, )
    account_number = models.CharField(max_length=200, blank=True, null=True, )
    swift_code = models.CharField(max_length=200, blank=True, null=True, )
    account_name = models.CharField(max_length=200, blank=True, null=True, )
    country = models.CharField(max_length=200, blank=True, null=True, )
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True)

    # def __str__(self):
    #      return str(self.account_number)



class SocialLink(models.Model):
    vendor_profile = models.OneToOneField(
        Profile, on_delete=models.SET_NULL, blank=True, null=True)
    facebook = models.CharField(max_length=200, blank=True, null=True, )
    twitter = models.CharField(max_length=200, blank=True, null=True, )
    instagram = models.CharField(max_length=200, blank=True, null=True, )
    pinterest = models.CharField(max_length=200, blank=True, null=True, )


class PremiumSubscription(models.Model):
    """Modèle pour gérer les abonnements premium des vendeurs"""
    vendor = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='premium_subscription', verbose_name=_("Vendeur"))
    
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    CANCELLED = 'CANCELLED'
    PENDING = 'PENDING'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Actif'),
        (EXPIRED, 'Expiré'),
        (CANCELLED, 'Annulé'),
        (PENDING, 'En attente'),
    ]
    
    status = models.CharField(
        max_length=13,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name=_("Statut")
    )
    
    start_date = models.DateTimeField(verbose_name=_("Date de début"))
    end_date = models.DateTimeField(verbose_name=_("Date de fin"))
    price = models.FloatField(default=0.0, verbose_name=_("Prix"))
    payment_status = models.BooleanField(default=False, verbose_name=_("Paiement effectué"))
    
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_date = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    
    class Meta:
        ordering = ('-created_date',)
        verbose_name = _("Abonnement Premium")
        verbose_name_plural = _("Abonnements Premium")
    
    def __str__(self):
        return f"Premium - {self.vendor.user.username} ({self.status})"
    
    def is_active(self):
        """Vérifie si l'abonnement est actif"""
        from django.utils import timezone
        if self.status == self.ACTIVE and self.end_date > timezone.now():
            return True
        return False


class ProductBoostRequest(models.Model):
    """Modèle pour gérer les demandes de boost de produits"""
    vendor = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='boost_requests', verbose_name=_("Vendeur"))
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='boost_requests', verbose_name=_("Produit"))
    
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    
    STATUS_CHOICES = [
        (PENDING, 'En attente'),
        (APPROVED, 'Approuvé'),
        (REJECTED, 'Rejeté'),
        (ACTIVE, 'Actif'),
        (EXPIRED, 'Expiré'),
    ]
    
    status = models.CharField(
        max_length=13,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name=_("Statut")
    )
    
    duration_days = models.PositiveIntegerField(default=7, verbose_name=_("Durée (jours)"))
    boost_percentage = models.FloatField(default=10.0, verbose_name=_("Pourcentage de boost"))
    price = models.FloatField(default=0.0, verbose_name=_("Prix"))
    payment_status = models.BooleanField(default=False, verbose_name=_("Paiement effectué"))
    
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de début"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de fin"))
    
    admin_notes = models.TextField(blank=True, null=True, verbose_name=_("Notes administrateur"))
    
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_date = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    approved_date = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'approbation"))
    
    class Meta:
        ordering = ('-created_date',)
        verbose_name = _("Demande de Boost Produit")
        verbose_name_plural = _("Demandes de Boost Produit")
    
    def __str__(self):
        return f"Boost - {self.product.product_name} ({self.status})"
    
    def is_active(self):
        """Vérifie si le boost est actif"""
        from django.utils import timezone
        if self.status == self.ACTIVE and self.end_date and self.end_date > timezone.now():
            return True
        return False


class PeerToPeerProductFavorite(models.Model):
    """Modèle pour gérer les favoris/likes des articles C2C"""
    product = models.ForeignKey(
        PeerToPeerProduct, on_delete=models.CASCADE, verbose_name=_("Article C2C"), related_name='favorites')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("User"), blank=True, null=True, related_name='peer_to_peer_product_favorites')
    session_key = models.CharField(
        max_length=40, blank=True, null=True, verbose_name=_("Session Key"), help_text=_("Pour les utilisateurs non authentifiés"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        unique_together = [['product', 'user'], ['product', 'session_key']]
        verbose_name = _("Favori Article C2C")
        verbose_name_plural = _("Favoris Articles C2C")


class AdminNotification(models.Model):
    """Modèle pour les notifications administrateur nécessitant une action"""
    BOOST_REQUEST = 'BOOST_REQUEST'
    PREMIUM_SUBSCRIPTION = 'PREMIUM_SUBSCRIPTION'
    CONTACT_MESSAGE = 'CONTACT_MESSAGE'
    PRODUCT_APPROVAL = 'PRODUCT_APPROVAL'
    
    TYPE_CHOICES = [
        (BOOST_REQUEST, _('Demande de boost')),
        (PREMIUM_SUBSCRIPTION, _('Abonnement premium')),
        (CONTACT_MESSAGE, _('Message de contact')),
        (PRODUCT_APPROVAL, _('Approbation de produit')),
    ]
    
    notification_type = models.CharField(
        max_length=50, choices=TYPE_CHOICES, verbose_name=_("Type de notification"))
    title = models.CharField(max_length=200, verbose_name=_("Titre"))
    message = models.TextField(verbose_name=_("Message"))
    
    # Lien vers l'objet concerné
    related_object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("ID de l'objet"))
    related_object_type = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Type d'objet"))
    related_url = models.CharField(
        max_length=500, blank=True, null=True, verbose_name=_("URL de l'objet"))
    
    # Statut
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    is_resolved = models.BooleanField(default=False, verbose_name=_("Résolu"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de lecture"))
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de résolution"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Notification administrateur")
        verbose_name_plural = _("Notifications administrateur")
        indexes = [
            models.Index(fields=['is_read', 'is_resolved', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_resolved(self):
        """Marque la notification comme résolue"""
        from django.utils import timezone
        if not self.is_resolved:
            self.is_resolved = True
            self.resolved_at = timezone.now()
            self.save(update_fields=['is_resolved', 'resolved_at'])


class AdminMessage(models.Model):
    """Message envoyé par l'administration à un utilisateur."""
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='admin_messages_sent',
        verbose_name=_("Expéditeur (admin)"))
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='admin_messages_received',
        verbose_name=_("Destinataire"))
    subject = models.CharField(max_length=200, verbose_name=_("Objet"))
    body = models.TextField(verbose_name=_("Message"))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Lu le"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Envoyé le"))
    email_sent = models.BooleanField(
        default=False, verbose_name=_("Email envoyé"),
        help_text=_("Copie envoyée par email au destinataire"))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Message admin → utilisateur")
        verbose_name_plural = _("Messages admin → utilisateurs")

    def __str__(self):
        return f"{self.subject} → {self.recipient.get_full_name() or self.recipient.username}"
