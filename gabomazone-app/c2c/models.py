"""
Modèles pour le système C2C (Consumer-to-Consumer)
Architecture modulaire séparée du système B2C
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import secrets
import string


def generate_verification_code(length=6):
    """Génère un code de vérification aléatoire"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


class PlatformSettings(models.Model):
    """
    Paramètres de la plateforme configurables depuis l'admin
    Gère les commissions C2C et B2C
    """
    # Commissions C2C (par défaut)
    c2c_buyer_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('5.90'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_("Commission acheteur C2C (%)"),
        help_text=_("Pourcentage de commission prélevé sur l'acheteur pour les transactions C2C")
    )
    c2c_seller_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('9.90'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_("Commission vendeur C2C (%)"),
        help_text=_("Pourcentage de commission prélevé sur le vendeur pour les transactions C2C")
    )
    
    # Commissions B2C (par défaut)
    b2c_buyer_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_("Commission acheteur B2C (%)"),
        help_text=_("Pourcentage de commission prélevé sur l'acheteur pour les transactions B2C")
    )
    b2c_seller_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_("Commission vendeur B2C (%)"),
        help_text=_("Pourcentage de commission prélevé sur le vendeur pour les transactions B2C")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Paramètres de la plateforme")
        verbose_name_plural = _("Paramètres de la plateforme")
        ordering = ('-updated_at',)
    
    def __str__(self):
        return f"Paramètres plateforme (C2C: {self.c2c_buyer_commission_rate}%/{self.c2c_seller_commission_rate}%)"
    
    @classmethod
    def get_active_settings(cls):
        """Retourne les paramètres actifs de la plateforme"""
        return cls.objects.filter(is_active=True).first() or cls.objects.create()
    
    def calculate_c2c_commissions(self, price):
        """
        Calcule les commissions C2C pour un prix donné
        Retourne: (commission_acheteur, commission_vendeur, total_plateforme, net_vendeur, total_acheteur)
        """
        price = Decimal(str(price))
        buyer_commission = price * (self.c2c_buyer_commission_rate / Decimal('100'))
        seller_commission = price * (self.c2c_seller_commission_rate / Decimal('100'))
        total_platform_commission = buyer_commission + seller_commission
        seller_net = price - seller_commission
        buyer_total = price + buyer_commission
        
        return {
            'buyer_commission': buyer_commission,
            'seller_commission': seller_commission,
            'platform_commission': total_platform_commission,
            'seller_net': seller_net,
            'buyer_total': buyer_total,
            'original_price': price
        }


class PurchaseIntent(models.Model):
    """
    Intention d'achat - créée lorsqu'un acheteur clique sur "Voir" ou "Négocier"
    Remplace le paiement direct par un système de négociation obligatoire
    """
    PENDING = 'pending'
    NEGOTIATING = 'negotiating'
    AGREED = 'agreed'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (NEGOTIATING, _('En négociation')),
        (AGREED, _('Accord trouvé')),
        (REJECTED, _('Refusé')),
        (CANCELLED, _('Annulé')),
        (EXPIRED, _('Expiré')),
    ]
    
    # Relations
    product = models.ForeignKey(
        'accounts.PeerToPeerProduct', on_delete=models.CASCADE,
        related_name='purchase_intents', verbose_name=_("Article"))
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='c2c_purchase_intents',
        verbose_name=_("Acheteur"))
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='c2c_sale_intents',
        verbose_name=_("Vendeur"))
    
    # Statut
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING,
        verbose_name=_("Statut"))
    
    # Prix initial et prix négocié
    initial_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Prix initial"))
    negotiated_price = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name=_("Prix négocié"))
    final_price = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name=_("Prix final accepté"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    agreed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'accord"))
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'expiration"))
    
    # Notification
    seller_notified = models.BooleanField(default=False, verbose_name=_("Vendeur notifié"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Intention d'achat")
        verbose_name_plural = _("Intentions d'achat")
        unique_together = ('product', 'buyer')
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['product', 'status']),
        ]
    
    def __str__(self):
        return f"Intention #{self.id} - {self.product.product_name} - {self.buyer.username}"
    
    def get_conversation(self):
        """Retourne la conversation associée à cette intention d'achat"""
        from accounts.models import ProductConversation
        return ProductConversation.objects.filter(
            product=self.product,
            buyer=self.buyer,
            seller=self.seller
        ).first()
    
    def can_negotiate(self):
        """Vérifie si la négociation est possible"""
        return self.status in [self.PENDING, self.NEGOTIATING]
    
    def is_expired(self):
        """Vérifie si l'intention d'achat a expiré"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class Negotiation(models.Model):
    """
    Proposition de prix dans le cadre d'une négociation
    Chaque message de négociation peut contenir une proposition
    """
    ACCEPTED = 'accepted'
    PENDING = 'pending'
    REJECTED = 'rejected'
    COUNTERED = 'countered'
    
    STATUS_CHOICES = [
        (ACCEPTED, _('Acceptée')),
        (PENDING, _('En attente')),
        (REJECTED, _('Refusée')),
        (COUNTERED, _('Contre-proposition')),
    ]
    
    # Relations
    purchase_intent = models.ForeignKey(
        PurchaseIntent, on_delete=models.CASCADE, related_name='negotiations',
        verbose_name=_("Intention d'achat"))
    proposer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='c2c_negotiations',
        verbose_name=_("Proposant"))
    
    # Proposition
    proposed_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Prix proposé"))
    message = models.TextField(blank=True, null=True, verbose_name=_("Message"))
    
    # Statut
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING,
        verbose_name=_("Statut"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    responded_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de réponse"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Négociation")
        verbose_name_plural = _("Négociations")
    
    def __str__(self):
        return f"Négociation #{self.id} - {self.proposed_price} FCFA"


class C2COrder(models.Model):
    """
    Commande C2C créée après accord sur le prix final
    Contient toutes les informations de la transaction
    """
    PENDING_PAYMENT = 'pending_payment'
    PAID = 'paid'
    PENDING_DELIVERY = 'pending_delivery'
    DELIVERED = 'delivered'
    VERIFIED = 'verified'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    DISPUTED = 'disputed'
    
    STATUS_CHOICES = [
        (PENDING_PAYMENT, _('Paiement en attente')),
        (PAID, _('Payé')),
        (PENDING_DELIVERY, _('Livraison en attente')),
        (DELIVERED, _('Livré')),
        (VERIFIED, _('Vérifié')),
        (COMPLETED, _('Terminé')),
        (CANCELLED, _('Annulé')),
        (DISPUTED, _('Litige')),
    ]
    
    # Relations
    purchase_intent = models.OneToOneField(
        PurchaseIntent, on_delete=models.CASCADE, related_name='c2c_order',
        verbose_name=_("Intention d'achat"))
    product = models.ForeignKey(
        'accounts.PeerToPeerProduct', on_delete=models.PROTECT,
        related_name='c2c_orders', verbose_name=_("Article"))
    buyer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='c2c_orders_bought',
        verbose_name=_("Acheteur"))
    seller = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='c2c_orders_sold',
        verbose_name=_("Vendeur"))
    
    # Prix et commissions
    final_price = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Prix final"))
    buyer_commission = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Commission acheteur"))
    seller_commission = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Commission vendeur"))
    platform_commission = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Commission plateforme"))
    seller_net = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Net vendeur"))
    buyer_total = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Total à payer"))
    
    # Statut
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING_PAYMENT,
        verbose_name=_("Statut"))
    
    # Transaction de paiement
    payment_transaction = models.ForeignKey(
        'payments.SingPayTransaction', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='c2c_orders',
        verbose_name=_("Transaction de paiement"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de paiement"))
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de livraison"))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de finalisation"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Commande C2C")
        verbose_name_plural = _("Commandes C2C")
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Commande C2C #{self.id} - {self.product.product_name}"
    
    def calculate_commissions(self):
        """Calcule les commissions pour cette commande"""
        settings = PlatformSettings.get_active_settings()
        calculations = settings.calculate_c2c_commissions(self.final_price)
        
        self.buyer_commission = calculations['buyer_commission']
        self.seller_commission = calculations['seller_commission']
        self.platform_commission = calculations['platform_commission']
        self.seller_net = calculations['seller_net']
        self.buyer_total = calculations['buyer_total']
        self.save()


class DeliveryVerification(models.Model):
    """
    Système de double code pour sécuriser la transaction
    - Code vendeur (V-CODE) : confirme qu'il a remis l'article
    - Code acheteur (A-CODE) : confirme qu'il a reçu l'article et qu'il est satisfait
    """
    PENDING = 'pending'
    SELLER_CODE_VERIFIED = 'seller_code_verified'
    BUYER_CODE_VERIFIED = 'buyer_code_verified'
    COMPLETED = 'completed'
    DISPUTED = 'disputed'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (SELLER_CODE_VERIFIED, _('Code vendeur vérifié')),
        (BUYER_CODE_VERIFIED, _('Code acheteur vérifié')),
        (COMPLETED, _('Terminé')),
        (DISPUTED, _('Litige')),
    ]
    
    # Relations
    c2c_order = models.OneToOneField(
        C2COrder, on_delete=models.CASCADE, related_name='delivery_verification',
        verbose_name=_("Commande C2C"))
    
    # Codes de vérification
    seller_code = models.CharField(
        max_length=6, unique=True, verbose_name=_("Code vendeur (V-CODE)"))
    buyer_code = models.CharField(
        max_length=6, unique=True, verbose_name=_("Code acheteur (A-CODE)"))
    
    # Vérifications
    seller_code_verified = models.BooleanField(default=False, verbose_name=_("Code vendeur vérifié"))
    buyer_code_verified = models.BooleanField(default=False, verbose_name=_("Code acheteur vérifié"))
    
    # Dates de vérification
    seller_code_verified_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Date vérification code vendeur"))
    buyer_code_verified_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Date vérification code acheteur"))
    
    # Statut
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=PENDING,
        verbose_name=_("Statut"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de finalisation"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Vérification de livraison")
        verbose_name_plural = _("Vérifications de livraison")
    
    def __str__(self):
        return f"Vérification #{self.id} - Commande C2C #{self.c2c_order.id}"
    
    def save(self, *args, **kwargs):
        """Génère les codes s'ils n'existent pas"""
        if not self.seller_code:
            self.seller_code = generate_verification_code()
        if not self.buyer_code:
            self.buyer_code = generate_verification_code()
        super().save(*args, **kwargs)
    
    def verify_seller_code(self, code):
        """
        Vérifie le code acheteur (A-CODE) saisi par le vendeur
        Le vendeur entre le code A-CODE pour confirmer qu'il a remis l'article
        """
        if code == self.buyer_code and not self.seller_code_verified:
            self.seller_code_verified = True
            self.seller_code_verified_at = timezone.now()
            if self.status == self.PENDING:
                self.status = self.SELLER_CODE_VERIFIED
            self.save()
            return True
        return False
    
    def verify_buyer_code(self, code):
        """
        Vérifie le code vendeur (V-CODE) saisi par l'acheteur
        L'acheteur entre le code V-CODE pour confirmer qu'il a reçu l'article
        """
        if code == self.seller_code and not self.buyer_code_verified:
            self.buyer_code_verified = True
            self.buyer_code_verified_at = timezone.now()
            if self.status == self.SELLER_CODE_VERIFIED:
                self.status = self.COMPLETED
                self.completed_at = timezone.now()
            elif self.status == self.PENDING:
                self.status = self.BUYER_CODE_VERIFIED
            self.save()
            return True
        return False
    
    def is_completed(self):
        """Vérifie si la vérification est complète"""
        return self.seller_code_verified and self.buyer_code_verified


class ProductBoost(models.Model):
    """
    Boost payant pour mettre en avant un article C2C
    """
    BOOST_24H = '24h'
    BOOST_72H = '72h'
    BOOST_7D = '7d'
    
    DURATION_CHOICES = [
        (BOOST_24H, _('24 heures')),
        (BOOST_72H, _('72 heures')),
        (BOOST_7D, _('7 jours')),
    ]
    
    ACTIVE = 'active'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (ACTIVE, _('Actif')),
        (EXPIRED, _('Expiré')),
        (CANCELLED, _('Annulé')),
    ]
    
    # Relations
    product = models.ForeignKey(
        'accounts.PeerToPeerProduct', on_delete=models.CASCADE,
        related_name='boosts', verbose_name=_("Article"))
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='c2c_boosts',
        verbose_name=_("Acheteur"))
    
    # Boost
    duration = models.CharField(
        max_length=10, choices=DURATION_CHOICES, verbose_name=_("Durée"))
    start_date = models.DateTimeField(verbose_name=_("Date de début"))
    end_date = models.DateTimeField(verbose_name=_("Date de fin"))
    
    # Statut
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=ACTIVE,
        verbose_name=_("Statut"))
    
    # Paiement
    payment_transaction = models.ForeignKey(
        'payments.SingPayTransaction', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='c2c_boosts',
        verbose_name=_("Transaction de paiement"))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Prix payé"))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Boost produit")
        verbose_name_plural = _("Boosts produits")
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['end_date', 'status']),
        ]
    
    def __str__(self):
        return f"Boost {self.duration} - {self.product.product_name}"
    
    def is_active(self):
        """Vérifie si le boost est actif"""
        return (
            self.status == self.ACTIVE and
            timezone.now() >= self.start_date and
            timezone.now() <= self.end_date
        )


class SellerBadge(models.Model):
    """
    Badge attribué à un vendeur C2C selon ses performances
    """
    NEW_SELLER = 'new_seller'
    GOOD_SELLER = 'good_seller'
    SERIOUS_SELLER = 'serious_seller'
    BEST_SELLER = 'best_seller'
    
    BADGE_CHOICES = [
        (NEW_SELLER, _('Nouveau Vendeur')),
        (GOOD_SELLER, _('Bon Vendeur')),
        (SERIOUS_SELLER, _('Vendeur Sérieux')),
        (BEST_SELLER, _('Meilleur Vendeur')),
    ]
    
    AUTO = 'auto'
    MANUAL = 'manual'
    
    ASSIGNMENT_CHOICES = [
        (AUTO, _('Automatique')),
        (MANUAL, _('Manuel')),
    ]
    
    # Relations
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='c2c_badges',
        verbose_name=_("Vendeur"))
    
    # Badge
    badge_type = models.CharField(
        max_length=20, choices=BADGE_CHOICES, verbose_name=_("Type de badge"))
    assignment_type = models.CharField(
        max_length=10, choices=ASSIGNMENT_CHOICES, default=AUTO,
        verbose_name=_("Type d'attribution"))
    
    # Critères (pour badges automatiques)
    min_rating = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True,
        verbose_name=_("Note minimale"))
    min_successful_transactions = models.IntegerField(
        default=0, verbose_name=_("Transactions réussies minimales"))
    
    # Dates
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'attribution"))
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'expiration"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        ordering = ('-assigned_at',)
        verbose_name = _("Badge vendeur")
        verbose_name_plural = _("Badges vendeurs")
        unique_together = ('seller', 'badge_type', 'is_active')
    
    def __str__(self):
        return f"{self.get_badge_type_display()} - {self.seller.username}"

