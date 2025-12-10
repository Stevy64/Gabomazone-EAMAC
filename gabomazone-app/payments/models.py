"""
Modèles pour les paiements SingPay
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import Profile
from orders.models import Order
from products.models import Product
from accounts.models import PeerToPeerProduct


class SingPayTransaction(models.Model):
    """
    Modèle pour stocker les transactions SingPay
    """
    # Statuts de transaction
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (SUCCESS, _('Réussi')),
        (FAILED, _('Échoué')),
        (CANCELLED, _('Annulé')),
        (REFUNDED, _('Remboursé')),
    ]
    
    # Types de transaction
    ORDER_PAYMENT = 'order_payment'
    BOOST_PAYMENT = 'boost_payment'
    SUBSCRIPTION_PAYMENT = 'subscription_payment'
    C2C_PAYMENT = 'c2c_payment'
    COMMISSION_PAYMENT = 'commission_payment'
    
    TRANSACTION_TYPE_CHOICES = [
        (ORDER_PAYMENT, _('Paiement de commande')),
        (BOOST_PAYMENT, _('Paiement boost produit')),
        (SUBSCRIPTION_PAYMENT, _('Paiement abonnement')),
        (C2C_PAYMENT, _('Paiement entre particuliers')),
        (COMMISSION_PAYMENT, _('Paiement commission')),
    ]
    
    # Champs SingPay
    transaction_id = models.CharField(
        max_length=100, unique=True, verbose_name=_("ID Transaction SingPay"))
    reference = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Référence"))
    internal_order_id = models.CharField(
        max_length=100, verbose_name=_("ID Commande interne"),
        help_text=_("Identifiant interne de la commande/transaction"))
    
    # Informations de paiement
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name=_("Montant"))
    currency = models.CharField(
        max_length=3, default='XOF', verbose_name=_("Devise"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING, verbose_name=_("Statut"))
    transaction_type = models.CharField(
        max_length=30, choices=TRANSACTION_TYPE_CHOICES, verbose_name=_("Type de transaction"))
    
    # Informations client
    customer_email = models.EmailField(verbose_name=_("Email client"))
    customer_phone = models.CharField(max_length=20, verbose_name=_("Téléphone client"))
    customer_name = models.CharField(max_length=200, verbose_name=_("Nom client"))
    
    # URLs
    payment_url = models.URLField(blank=True, null=True, verbose_name=_("URL de paiement"))
    callback_url = models.URLField(verbose_name=_("URL de callback"))
    return_url = models.URLField(verbose_name=_("URL de retour"))
    
    # Relations
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Utilisateur"))
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Commande"))
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Produit"))
    peer_product = models.ForeignKey(
        PeerToPeerProduct, on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_("Article entre particuliers"))
    
    # Métadonnées
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Métadonnées"))
    
    # Informations de paiement SingPay
    payment_method = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Méthode de paiement"))
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de paiement"))
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Date d'expiration"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Transaction SingPay")
        verbose_name_plural = _("Transactions SingPay")
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['internal_order_id']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency} - {self.get_status_display()}"
    
    def is_expired(self) -> bool:
        """Vérifie si la transaction a expiré"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def can_be_cancelled(self) -> bool:
        """Vérifie si la transaction peut être annulée"""
        return self.status == self.PENDING and not self.is_expired()
    
    def can_be_refunded(self) -> bool:
        """Vérifie si la transaction peut être remboursée"""
        return self.status == self.SUCCESS
    
    def get_status_steps(self):
        """
        Retourne les étapes de la transaction avec leur statut
        """
        steps = [
            {
                'name': 'Initialisation',
                'status': 'completed' if self.created_at else 'pending',
                'date': self.created_at,
                'icon': 'fi-rs-shopping-cart',
                'description': 'Transaction initialisée'
            },
            {
                'name': 'Paiement en attente',
                'status': 'completed' if self.status != self.PENDING else 'active' if self.status == self.PENDING else 'pending',
                'date': self.created_at if self.status == self.PENDING else None,
                'icon': 'fi-rs-clock',
                'description': 'En attente de paiement'
            },
            {
                'name': 'Paiement validé',
                'status': 'completed' if self.status == self.SUCCESS else 'pending',
                'date': self.paid_at if self.status == self.SUCCESS else None,
                'icon': 'fi-rs-check',
                'description': 'Paiement effectué avec succès'
            },
            {
                'name': 'Commande confirmée',
                'status': 'completed' if self.status == self.SUCCESS and self.order and self.order.is_finished else 'pending',
                'date': self.paid_at if self.status == self.SUCCESS and self.order and self.order.is_finished else None,
                'icon': 'fi-rs-shopping-bag',
                'description': 'Commande confirmée et en préparation'
            },
        ]
        
        if self.status == self.FAILED:
            steps.append({
                'name': 'Échec',
                'status': 'failed',
                'date': self.updated_at,
                'icon': 'fi-rs-cross-circle',
                'description': 'Le paiement a échoué'
            })
        elif self.status == self.CANCELLED:
            steps.append({
                'name': 'Annulé',
                'status': 'cancelled',
                'date': self.updated_at,
                'icon': 'fi-rs-ban',
                'description': 'Transaction annulée'
            })
        
        return steps


class SingPayWebhookLog(models.Model):
    """
    Log des webhooks SingPay pour le débogage
    """
    transaction = models.ForeignKey(
        SingPayTransaction, on_delete=models.CASCADE, related_name='webhook_logs',
        verbose_name=_("Transaction"))
    payload = models.JSONField(verbose_name=_("Payload reçu"))
    signature = models.CharField(max_length=200, verbose_name=_("Signature"))
    timestamp = models.CharField(max_length=50, verbose_name=_("Timestamp"))
    is_valid = models.BooleanField(default=False, verbose_name=_("Signature valide"))
    processed = models.BooleanField(default=False, verbose_name=_("Traité"))
    error_message = models.TextField(blank=True, null=True, verbose_name=_("Message d'erreur"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de réception"))
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Log Webhook SingPay")
        verbose_name_plural = _("Logs Webhooks SingPay")
    
    def __str__(self):
        return f"Webhook {self.transaction.transaction_id} - {self.created_at}"


class VendorPayments(models.Model):
    """
    Modèle existant pour les paiements des vendeurs
    Conservé pour compatibilité avec l'admin existant
    """
    vendor_profile = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_("Profil vendeur"))
    request_amount = models.FloatField(
        default=0.00, blank=True, null=True, verbose_name=_("Montant demandé"))
    fee = models.FloatField(
        default=0.00, blank=True, null=True, verbose_name=_("Frais"))
    description = models.TextField(
        blank=True, null=True, verbose_name=_("Description"))
    
    Paid = 'Paid'
    Pending = 'Pending'
    Progressing = 'Progressing'
    Refunded = 'Refunded'
    Status_select = [
        (Paid, 'Paid'),
        (Pending, 'Pending'),
        (Progressing, 'Progressing'),
        (Refunded, 'Refunded'),
    ]
    status = models.CharField(
        max_length=13,
        choices=Status_select,
        default=Pending,
        verbose_name=_("Statut")
    )
    
    Bank = 'Bank'
    Paypal = 'Paypal'
    SingPay = 'SingPay'
    method_select = [
        (Bank, 'Bank'),
        (Paypal, 'Paypal'),
        (SingPay, 'SingPay'),
    ]
    method = models.CharField(
        max_length=15,
        choices=method_select,
        default=Bank,
        verbose_name=_("Méthode de paiement")
    )
    comment = models.TextField(blank=True, null=True, verbose_name=_("Commentaire"))
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=_("Date"))
    date_update = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=_("Date de mise à jour"))
    
    # Lien vers transaction SingPay si applicable
    singpay_transaction = models.ForeignKey(
        SingPayTransaction, on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name=_("Transaction SingPay"))
    
    class Meta:
        ordering = ('-id',)
        verbose_name = _("Paiement vendeur")
        verbose_name_plural = _("Paiements vendeurs")
    
    def __str__(self):
        return f"Paiement {self.id} - {self.vendor_profile} - {self.request_amount}"
