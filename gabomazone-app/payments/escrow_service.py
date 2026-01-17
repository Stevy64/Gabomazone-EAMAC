"""
Service de gestion de l'escrow (séquestre) pour les paiements
Mode escrow sans wallet interne : les fonds restent chez SingPay jusqu'à confirmation de livraison
"""
import logging
from decimal import Decimal
from django.utils import timezone
from typing import Optional, Tuple

from .models import SingPayTransaction
from .services.singpay import singpay_service
from accounts.models import Profile
from orders.models import Order, OrderDetails
from c2c.models import C2COrder
from c2c.services import CommissionCalculator

logger = logging.getLogger(__name__)


class EscrowService:
    """Service pour gérer l'escrow des paiements"""
    
    @staticmethod
    def release_escrow_for_order(order: Order) -> Tuple[bool, dict]:
        """
        Libère les fonds en escrow pour une commande B2C après confirmation de livraison
        
        Args:
            order: Commande B2C
            
        Returns:
            Tuple (success, response_data)
        """
        try:
            # Récupérer la transaction de paiement
            transaction = SingPayTransaction.objects.filter(
                order=order,
                status=SingPayTransaction.SUCCESS,
                escrow_status=SingPayTransaction.ESCROW_PENDING,
                transaction_type=SingPayTransaction.ORDER_PAYMENT
            ).first()
            
            if not transaction:
                logger.warning(f"Aucune transaction en escrow trouvée pour la commande {order.id}")
                return False, {'error': 'Aucune transaction en escrow trouvée'}
            
            # Calculer les commissions et le montant à verser au vendeur
            calculator = CommissionCalculator()
            order_details = OrderDetails.objects.filter(order=order)
            
            total_seller_net = Decimal('0')
            vendor_profiles = {}
            
            for order_detail in order_details:
                if order_detail.product and order_detail.product.vendor:
                    vendor = order_detail.product.vendor
                    commissions = calculator.calculate_b2c_commissions(float(order_detail.price))
                    seller_net = Decimal(str(commissions['seller_net']))
                    total_seller_net += seller_net
                    
                    # Stocker le profil du vendeur
                    try:
                        vendor_profile = Profile.objects.get(user=vendor)
                        if vendor.id not in vendor_profiles:
                            vendor_profiles[vendor.id] = {
                                'profile': vendor_profile,
                                'amount': Decimal('0')
                            }
                        vendor_profiles[vendor.id]['amount'] += seller_net
                    except Profile.DoesNotExist:
                        logger.warning(f"Profil vendeur non trouvé pour user {vendor.id}")
            
            if total_seller_net <= 0:
                logger.warning(f"Montant total à verser nul ou négatif pour la commande {order.id}")
                return False, {'error': 'Montant à verser invalide'}
            
            # Libérer les fonds pour chaque vendeur
            disbursement_results = []
            for vendor_id, vendor_data in vendor_profiles.items():
                vendor_profile = vendor_data['profile']
                amount = float(vendor_data['amount'])
                
                if not vendor_profile.mobile_number:
                    logger.warning(f"Numéro de téléphone manquant pour le vendeur {vendor_id}")
                    continue
                
                # Effectuer le virement via SingPay
                success, response = singpay_service.init_disbursement(
                    amount=amount,
                    currency='XOF',
                    recipient_phone=vendor_profile.mobile_number,
                    recipient_name=f"{vendor_profile.user.first_name} {vendor_profile.user.last_name}",
                    description=f"Libération escrow - Commande #{order.id}",
                    reference=f"ESCROW-ORDER-{order.id}-VENDOR-{vendor_id}",
                    metadata={
                        'order_id': order.id,
                        'vendor_id': vendor_id,
                        'escrow_transaction_id': transaction.transaction_id,
                        'type': 'escrow_release'
                    }
                )
                
                if success:
                    disbursement_id = response.get('disbursement_id')
                    disbursement_results.append({
                        'vendor_id': vendor_id,
                        'disbursement_id': disbursement_id,
                        'amount': amount
                    })
                    logger.info(f"Virement escrow initié pour vendeur {vendor_id}: {disbursement_id}")
                else:
                    logger.error(f"Erreur virement escrow pour vendeur {vendor_id}: {response.get('error')}")
            
            # Mettre à jour le statut de l'escrow
            if disbursement_results:
                transaction.escrow_status = SingPayTransaction.ESCROW_RELEASED
                transaction.escrow_released_at = timezone.now()
                # Stocker le premier disbursement_id (ou tous si nécessaire)
                transaction.disbursement_id = disbursement_results[0]['disbursement_id']
                transaction.save()
                
                logger.info(f"Escrow libéré pour la commande {order.id}, {len(disbursement_results)} virement(s) effectué(s)")
                return True, {
                    'disbursements': disbursement_results,
                    'total_amount': float(total_seller_net),
                    'message': f'{len(disbursement_results)} virement(s) effectué(s)'
                }
            else:
                return False, {'error': 'Aucun virement n\'a pu être effectué'}
                
        except Exception as e:
            logger.exception(f"Erreur lors de la libération de l'escrow pour la commande {order.id}: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def release_escrow_for_c2c_order(c2c_order: C2COrder) -> Tuple[bool, dict]:
        """
        Libère les fonds en escrow pour une commande C2C après confirmation de livraison
        
        Args:
            c2c_order: Commande C2C
            
        Returns:
            Tuple (success, response_data)
        """
        try:
            # Récupérer la transaction de paiement via payment_transaction de C2COrder
            transaction = None
            
            # Essayer via payment_transaction de C2COrder
            if hasattr(c2c_order, 'payment_transaction') and c2c_order.payment_transaction:
                transaction = c2c_order.payment_transaction
                if (transaction.status != SingPayTransaction.SUCCESS or 
                    transaction.escrow_status != SingPayTransaction.ESCROW_PENDING):
                    transaction = None
            
            # Si pas trouvé, chercher via metadata
            if not transaction:
                transaction = SingPayTransaction.objects.filter(
                    status=SingPayTransaction.SUCCESS,
                    escrow_status=SingPayTransaction.ESCROW_PENDING,
                    transaction_type=SingPayTransaction.C2C_PAYMENT,
                    metadata__c2c_order_id=c2c_order.id
                ).first()
            
            # Dernière tentative : chercher par internal_order_id
            if not transaction:
                transaction = SingPayTransaction.objects.filter(
                    internal_order_id__icontains=f"C2C-{c2c_order.id}",
                    status=SingPayTransaction.SUCCESS,
                    escrow_status=SingPayTransaction.ESCROW_PENDING,
                    transaction_type=SingPayTransaction.C2C_PAYMENT
                ).first()
            
            if not transaction:
                logger.warning(f"Aucune transaction en escrow trouvée pour la commande C2C {c2c_order.id}")
                return False, {'error': 'Aucune transaction en escrow trouvée'}
            
            # Récupérer le profil du vendeur
            try:
                seller_profile = Profile.objects.get(user=c2c_order.seller)
            except Profile.DoesNotExist:
                logger.error(f"Profil vendeur non trouvé pour user {c2c_order.seller.id}")
                return False, {'error': 'Profil vendeur non trouvé'}
            
            if not seller_profile.mobile_number:
                logger.error(f"Numéro de téléphone manquant pour le vendeur {c2c_order.seller.id}")
                return False, {'error': 'Numéro de téléphone vendeur manquant'}
            
            # Le montant à verser est seller_net (déjà calculé dans la commande C2C)
            amount = float(c2c_order.seller_net)
            
            if amount <= 0:
                logger.warning(f"Montant à verser nul ou négatif pour la commande C2C {c2c_order.id}")
                return False, {'error': 'Montant à verser invalide'}
            
            # Effectuer le virement via SingPay
            success, response = singpay_service.init_disbursement(
                amount=amount,
                currency='XOF',
                recipient_phone=seller_profile.mobile_number,
                recipient_name=f"{c2c_order.seller.first_name} {c2c_order.seller.last_name}",
                description=f"Libération escrow - Commande C2C #{c2c_order.id}",
                reference=f"ESCROW-C2C-{c2c_order.id}",
                metadata={
                    'c2c_order_id': c2c_order.id,
                    'seller_id': c2c_order.seller.id,
                    'escrow_transaction_id': transaction.transaction_id,
                    'type': 'escrow_release_c2c'
                }
            )
            
            if success:
                disbursement_id = response.get('disbursement_id')
                
                # Mettre à jour le statut de l'escrow
                transaction.escrow_status = SingPayTransaction.ESCROW_RELEASED
                transaction.escrow_released_at = timezone.now()
                transaction.disbursement_id = disbursement_id
                transaction.save()
                
                logger.info(f"Escrow libéré pour la commande C2C {c2c_order.id}, disbursement: {disbursement_id}")
                return True, {
                    'disbursement_id': disbursement_id,
                    'amount': amount,
                    'message': 'Virement effectué avec succès'
                }
            else:
                error_msg = response.get('error', 'Erreur lors du virement')
                logger.error(f"Erreur virement escrow C2C: {error_msg}")
                return False, {'error': error_msg}
                
        except Exception as e:
            logger.exception(f"Erreur lors de la libération de l'escrow pour la commande C2C {c2c_order.id}: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def refund_escrow(transaction: SingPayTransaction, reason: str = 'Remboursement escrow') -> Tuple[bool, dict]:
        """
        Rembourse les fonds en escrow à l'acheteur
        
        Args:
            transaction: Transaction en escrow
            reason: Raison du remboursement
            
        Returns:
            Tuple (success, response_data)
        """
        try:
            if transaction.escrow_status != SingPayTransaction.ESCROW_PENDING:
                return False, {'error': 'La transaction n\'est pas en escrow'}
            
            # Utiliser la méthode de remboursement SingPay
            success, response = singpay_service.refund_payment(
                transaction_id=transaction.transaction_id,
                reason=reason
            )
            
            if success:
                transaction.escrow_status = SingPayTransaction.ESCROW_REFUNDED
                transaction.status = SingPayTransaction.REFUNDED
                transaction.save()
                
                logger.info(f"Escrow remboursé pour la transaction {transaction.transaction_id}")
                return True, {
                    'refund_id': response.get('refund_id'),
                    'message': 'Remboursement effectué avec succès'
                }
            else:
                return False, response
                
        except Exception as e:
            logger.exception(f"Erreur lors du remboursement de l'escrow: {str(e)}")
            return False, {'error': str(e)}

