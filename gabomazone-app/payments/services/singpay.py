"""
Service d'intégration SingPay pour Gabomazone
Gère l'authentification, les signatures et les appels API SingPay
"""
import requests
import hashlib
import hmac
import json
import time
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Préfixe pour filtrer les logs du flux de paiement SingPay
LOG_PREFIX = "[SingPay]"


def _sanitize_for_log(data: Optional[Dict], max_len: int = 200) -> Dict:
    """Retourne une copie des données safe pour les logs (sans secrets, champs tronqués)."""
    if not data:
        return {}
    safe = {}
    skip_keys = {'x-client-secret', 'api_secret', 'password', 'token'}
    for k, v in data.items():
        key_lower = k.lower() if isinstance(k, str) else str(k)
        if any(s in key_lower for s in skip_keys):
            safe[k] = "***"
        elif isinstance(v, str) and len(v) > max_len:
            safe[k] = v[:max_len] + "..."
        else:
            safe[k] = v
    return safe


class SingPayService:
    """
    Service complet pour interagir avec l'API SingPay
    Documentation officielle: https://client.singpay.ga/doc/reference/index.html
    
    Ce service gère:
    - L'initialisation des paiements (interface externe via /v1/ext)
    - Les paiements directs via USSD Push (Airtel, Moov, Maviance)
    - La vérification du statut des transactions
    - L'annulation des paiements
    - Les remboursements (partiels ou totaux)
    - Les virements (disbursements)
    - La récupération de l'historique des transactions
    - La consultation du solde du portefeuille
    - La vérification des signatures webhook
    
    Endpoints disponibles:
    - POST /v1/ext : Interface de paiement externe
    - POST /74/paiement : USSD Push Airtel Money
    - POST /62/paiement : USSD Push Moov Money
    - POST /maviance/paiement : Paiement Maviance Mobile Money
    - POST /v1/disbursement : Virement vers un portefeuille
    - GET /v1/transaction/{id} : Vérifier une transaction
    - POST /v1/transaction/{id}/cancel : Annuler une transaction
    - POST /v1/transaction/{id}/refund : Rembourser une transaction
    - GET /v1/transactions : Historique des transactions
    - GET /v1/wallet/balance : Solde du portefeuille
    """
    
    # URLs de l'API SingPay selon la documentation officielle
    # Documentation: https://client.singpay.ga/doc/reference/index.html
    # L'API Gateway est sur gateway.singpay.ga (pas client.singpay.ga)
    BASE_URL_SANDBOX = "https://gateway.singpay.ga"
    BASE_URL_PRODUCTION = "https://gateway.singpay.ga"
    
    # Endpoints selon la documentation officielle SingPay
    # Documentation: https://client.singpay.ga/doc/reference/index.html
    # 
    # Endpoints disponibles pour les paiements :
    # - POST /ext : Récupération du lien permettant d'accéder à l'interface de paiement externe de SingPay
    # - POST /74/paiement : Lancer le USSD Push chez le client pour le paiement Airtel money
    # - POST /62/paiement : Lancer le USSD Push chez le client pour le paiement Moov money
    # - POST /maviance/paiement : Lancer le paiement pour client mobile money maviance
    
    def __init__(self):
        """Initialise le service SingPay avec les credentials"""
        self.api_key = getattr(settings, 'SINGPAY_API_KEY', '')
        self.api_secret = getattr(settings, 'SINGPAY_API_SECRET', '')
        self.merchant_id = getattr(settings, 'SINGPAY_MERCHANT_ID', '')
        self.disbursement_id = getattr(settings, 'SINGPAY_DISBURSEMENT_ID', '')  # ID portefeuille pour disbursement (requête paiement/virement)
        self.environment = getattr(settings, 'SINGPAY_ENVIRONMENT', 'sandbox')  # 'sandbox' ou 'production'
        # Les credentials sont obligatoires en production: on bloque les appels si incomplets.
        if not all([self.api_key, self.api_secret, self.merchant_id]):
            logger.error("SingPay credentials manquants - l'API ne peut pas être utilisée")
            if not self.api_key:
                logger.error("  - SINGPAY_API_KEY manquant")
            if not self.api_secret:
                logger.error("  - SINGPAY_API_SECRET manquant")
            if not self.merchant_id:
                logger.error("  - SINGPAY_MERCHANT_ID manquant")
        
        if self.environment == 'production':
            self.base_url = self.BASE_URL_PRODUCTION
        else:
            self.base_url = self.BASE_URL_SANDBOX
        
        if not all([self.api_key, self.api_secret, self.merchant_id]):
            logger.warning("SingPay credentials not fully configured")
    
    def _generate_signature(self, data: Dict, timestamp: str) -> str:
        """
        Génère la signature HMAC-SHA256 pour authentifier la requête
        
        Args:
            data: Données à signer
            timestamp: Timestamp de la requête
            
        Returns:
            Signature hexadécimale
        """
        # Construire la chaîne à signer
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        message = f"{timestamp}{sorted_data}"
        
        # Générer la signature HMAC-SHA256
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_headers(self, data: Dict = None) -> Dict[str, str]:
        """
        Génère les headers pour une requête API
        Selon la documentation SingPay, les headers sont :
        - x-client-id : API Key
        - x-client-secret : API Secret
        - x-wallet : Merchant ID
        
        Args:
            data: Données de la requête (non utilisé pour l'instant)
            
        Returns:
            Dictionnaire des headers
        """
        return {
            'Content-Type': 'application/json',
            'accept': '*/*',
            'x-client-id': self.api_key,
            'x-client-secret': self.api_secret,
            'x-wallet': self.merchant_id,
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Effectue une requête HTTP vers l'API SingPay
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            endpoint: Endpoint de l'API
            data: Données à envoyer
            
        Returns:
            Tuple (success, response_data)
        """
        if data is None:
            data = {}
        
        if not all([self.api_key, self.api_secret, self.merchant_id]):
            return False, {
                'error': 'SingPay credentials missing',
                'details': 'Configure SINGPAY_API_KEY, SINGPAY_API_SECRET, SINGPAY_MERCHANT_ID',
            }
        
        # Toutes les requêtes passent par la gateway SingPay
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(data)
        
        logger.info(
            f"{LOG_PREFIX} REQUEST phase=api_call method={method} endpoint={endpoint} "
            f"payload={_sanitize_for_log(data)}"
        )
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                logger.error(f"{LOG_PREFIX} REQUEST phase=api_call error=unsupported_method method={method}")
                return False, {'error': f'Unsupported method: {method}'}
            
            # Erreurs HTTP -> exception pour un logging cohérent
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(
                f"{LOG_PREFIX} RESPONSE phase=api_call method={method} endpoint={endpoint} "
                f"status={response.status_code} success=True response_keys={list(response_data.keys()) if isinstance(response_data, dict) else 'n/a'}"
            )
            logger.debug(f"{LOG_PREFIX} RESPONSE body: {_sanitize_for_log(response_data)}")
            return True, response_data
            
        except requests.exceptions.RequestException as e:
            error_details = {
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }
            # Essayer de récupérer le message d'erreur de la réponse
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_response = e.response.json()
                    error_details['api_error'] = error_response
                except Exception:
                    error_details['response_text'] = (e.response.text or '')[:500]
            
            logger.error(
                f"{LOG_PREFIX} RESPONSE phase=api_call method={method} endpoint={endpoint} "
                f"success=False error={error_details.get('error')} status_code={error_details.get('status_code')} "
                f"api_error={error_details.get('api_error')} response_text={error_details.get('response_text', '')[:100]}"
            )
            return False, error_details
        except json.JSONDecodeError as e:
            logger.error(f"{LOG_PREFIX} RESPONSE phase=api_call endpoint={endpoint} success=False error=json_decode details={e}")
            return False, {'error': 'Invalid JSON response', 'details': str(e)}
    
    def init_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_email: str,
        customer_phone: str,
        customer_name: str,
        description: str,
        callback_url: str,
        return_url: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initialise un paiement SingPay
        
        Args:
            amount: Montant à payer
            currency: Code devise (XOF, XAF, etc.)
            order_id: ID unique de la commande
            customer_email: Email du client
            customer_phone: Téléphone du client (format international)
            customer_name: Nom du client
            description: Description de la transaction
            callback_url: URL de callback pour les notifications
            return_url: URL de retour après paiement
            metadata: Métadonnées supplémentaires
            
        Returns:
            Tuple (success, response_data) avec payment_url et transaction_id
        """
        _phone = (customer_phone or '')[:6] + '***' if customer_phone else 'n/a'
        _cb = (callback_url or '')[:60] + ('...' if len(callback_url or '') > 60 else '')
        _ret = (return_url or '')[:60] + ('...' if len(return_url or '') > 60 else '')
        logger.info(
            f"{LOG_PREFIX} phase=init_payment order_id={order_id} amount={amount} currency={currency} "
            f"customer_phone={_phone} callback_url={_cb} return_url={_ret}"
        )
        # Structure des données selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        # L'endpoint /v1/ext attend les paramètres suivants :
        # Note: 'portefeuille' doit être le Merchant ID (wallet), pas l'order_id
        data = {
            'portefeuille': self.merchant_id,  # Merchant ID (wallet) - requis
            'reference': f"REF-{order_id}",  # Référence unique de la transaction
            'redirect_success': return_url,  # URL de redirection en cas de succès
            'redirect_error': return_url,  # URL de redirection en cas d'erreur
            'amount': float(amount),  # Montant
            'disbursement': self.disbursement_id or '',  # ID portefeuille disbursement (SINGPAY_DISBURSEMENT_ID)
            'logoURL': '',  # Optionnel - URL du logo à afficher
            'isTransfer': False,  # Type de transaction (False = paiement, True = virement)
            'order_id': order_id,
        }
        
        if metadata:
            # Ajouter les métadonnées si nécessaire
            if 'logo_url' in metadata:
                data['logoURL'] = metadata['logo_url']
            if 'disbursement' in metadata:
                data['disbursement'] = metadata['disbursement']
        
        logger.debug(f"{LOG_PREFIX} phase=init_payment payload={_sanitize_for_log(data)}")
        
        # Endpoint selon la documentation SingPay officielle
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        # Endpoint /v1/ext : Récupération du lien permettant d'accéder à l'interface de paiement externe de SingPay
        success, response = self._make_request('POST', '/v1/ext', data)
        
        if success:
            # Structure de réponse selon la documentation SingPay
            # La réponse contient :
            # - 'link' : URL de paiement
            # - 'exp' : Date d'expiration
            payment_url = None
            transaction_id = None
            reference = None
            expires_at = None
            
            # Extraire le lien de paiement
            if 'link' in response:
                payment_url = response['link']
                # Extraire l'ID de transaction depuis l'URL si possible
                # Formats possibles:
                # - https://gateway.singpay.ga/ext/v1/payment/{transaction_id}
                # - https://gateway.singpay.ga/payment/{transaction_id}
                # - https://gateway.singpay.ga/ext?transaction_id={transaction_id}
                if payment_url:
                    # Essayer d'extraire depuis /payment/
                    if '/payment/' in payment_url:
                        try:
                            transaction_id = payment_url.split('/payment/')[-1].split('/')[0].split('?')[0]
                            if transaction_id:
                                logger.info(f"transaction_id extrait de l'URL: {transaction_id}")
                        except:
                            pass
                    # Essayer d'extraire depuis les paramètres de requête
                    if not transaction_id and 'transaction_id=' in payment_url:
                        try:
                            from urllib.parse import urlparse, parse_qs
                            parsed = urlparse(payment_url)
                            params = parse_qs(parsed.query)
                            if 'transaction_id' in params:
                                transaction_id = params['transaction_id'][0]
                                logger.info(f"transaction_id extrait des paramètres: {transaction_id}")
                        except:
                            pass
                    # Essayer d'extraire depuis /ext/ ou autres patterns
                    if not transaction_id:
                        # Chercher un ID dans l'URL (format UUID ou alphanumérique)
                        import re
                        match = re.search(r'/([a-f0-9]{8,}-[a-f0-9]{4,}-[a-f0-9]{4,}-[a-f0-9]{4,}-[a-f0-9]{12,})', payment_url, re.IGNORECASE)
                        if match:
                            transaction_id = match.group(1)
                            logger.info(f"transaction_id extrait par regex: {transaction_id}")
            elif 'payment_url' in response:
                payment_url = response['payment_url']
                # Même logique d'extraction
                if payment_url and '/payment/' in payment_url:
                    try:
                        transaction_id = payment_url.split('/payment/')[-1].split('/')[0].split('?')[0]
                    except:
                        pass
            elif 'url' in response:
                payment_url = response['url']
                # Même logique d'extraction
                if payment_url and '/payment/' in payment_url:
                    try:
                        transaction_id = payment_url.split('/payment/')[-1].split('/')[0].split('?')[0]
                    except:
                        pass
            
            # Vérifier aussi si transaction_id est directement dans la réponse
            if not transaction_id and 'transaction_id' in response:
                transaction_id = response['transaction_id']
                logger.info(f"transaction_id trouvé directement dans la réponse: {transaction_id}")
            elif not transaction_id and 'id' in response:
                transaction_id = response['id']
                logger.info(f"transaction_id trouvé dans le champ 'id': {transaction_id}")
            
            # Extraire la référence et la date d'expiration
            reference = response.get('reference') or data.get('reference')
            expires_at_raw = response.get('exp') or response.get('expires_at')
            
            # Parser la date d'expiration si elle existe
            expires_at = None
            if expires_at_raw:
                try:
                    # L'API SingPay retourne 'exp' au format "1/9/2026, 11:41:11 PM" ou "01/09/2026, 11:41:11 PM"
                    # On doit le convertir en datetime Python
                    from datetime import datetime
                    import re
                    expires_at_str = str(expires_at_raw).strip()
                    
                    parsed = False
                    
                    # Essayer d'abord avec regex pour gérer les formats avec/sans zéro padding
                    # Format: "1/9/2026, 11:41:11 PM" ou "01/09/2026, 11:41:11 PM"
                    match = re.match(r'(\d+)/(\d+)/(\d+), (\d+):(\d+):(\d+) (AM|PM)', expires_at_str)
                    if match:
                        try:
                            month, day, year, hour, minute, second, am_pm = match.groups()
                            hour = int(hour)
                            if am_pm == 'PM' and hour != 12:
                                hour += 12
                            elif am_pm == 'AM' and hour == 12:
                                hour = 0
                            expires_at = datetime(int(year), int(month), int(day), hour, int(minute), int(second))
                            parsed = True
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Erreur lors de la construction de la date depuis regex: {e}")
                    
                    if not parsed:
                        # Essayer le format ISO
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                            parsed = True
                        except ValueError:
                            try:
                                # Essayer le format avec T
                                expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%S")
                                parsed = True
                            except ValueError:
                                logger.warning(f"Impossible de parser la date d'expiration: {expires_at_raw}")
                                expires_at = None
                    
                    if not parsed:
                        expires_at = None
                    
                    # Convertir en timezone-aware si nécessaire
                    if expires_at and timezone.is_naive(expires_at):
                        expires_at = timezone.make_aware(expires_at)
                except Exception as e:
                    logger.warning(f"Erreur lors du parsing de la date d'expiration: {e}")
                    expires_at = None
            
            # Si pas de transaction_id, utiliser la référence ou générer un ID unique
            # Vérifier aussi si transaction_id est une chaîne vide
            if not transaction_id or (isinstance(transaction_id, str) and not transaction_id.strip()):
                import uuid
                if reference:
                    # Utiliser la référence comme base, mais ajouter un suffixe unique pour éviter les collisions
                    # La référence est déjà unique (REF-ORDER-{order_id})
                    transaction_id = f"{reference}-{uuid.uuid4().hex[:8].upper()}"
                else:
                    # Si pas de référence non plus, utiliser order_id
                    transaction_id = f"TXN-{order_id}-{uuid.uuid4().hex[:12].upper()}"
                logger.warning(f"transaction_id manquant ou vide dans la réponse API, génération d'un ID: {transaction_id}")
                logger.warning(f"Réponse complète de l'API: {response}")
            
            if payment_url:
                logger.info(
                    f"{LOG_PREFIX} phase=init_payment_result order_id={order_id} success=True "
                    f"transaction_id={transaction_id} reference={reference} payment_url={payment_url[:60]}..."
                )
                # S'assurer que transaction_id est toujours présent et valide
                if not transaction_id or (isinstance(transaction_id, str) and not transaction_id.strip()):
                    import uuid
                    if reference:
                        transaction_id = f"{reference}-{uuid.uuid4().hex[:8].upper()}"
                    else:
                        transaction_id = f"TXN-{order_id}-{uuid.uuid4().hex[:12].upper()}"
                    logger.error(f"transaction_id toujours manquant ou invalide après extraction! Génération d'urgence: {transaction_id}")
                
                return True, {
                    'payment_url': payment_url,
                    'transaction_id': transaction_id,
                    'reference': reference,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                }
            else:
                logger.warning(
                    f"{LOG_PREFIX} phase=init_payment_result order_id={order_id} success=False "
                    f"error=no_payment_link response={response}"
                )
                return False, {'error': 'Lien de paiement manquant dans la réponse', 'response': response}
        
        logger.warning(
            f"{LOG_PREFIX} phase=init_payment_result order_id={order_id} success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def verify_payment(self, transaction_id: str) -> Tuple[bool, Dict]:
        """
        Vérifie le statut d'une transaction
        
        Args:
            transaction_id: ID de la transaction SingPay
            
        Returns:
            Tuple (success, transaction_data)
        """
        logger.info(f"{LOG_PREFIX} phase=verify_payment transaction_id={transaction_id}")
        # Endpoint de vérification selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        endpoint = f"/v1/transaction/{transaction_id}"
        success, response = self._make_request('GET', endpoint)
        
        if success:
            status = response.get('status')
            logger.info(
                f"{LOG_PREFIX} phase=verify_payment_result transaction_id={transaction_id} success=True status={status}"
            )
            return True, {
                'status': response.get('status'),  # pending, success, failed, cancelled
                'amount': response.get('amount'),
                'currency': response.get('currency'),
                'order_id': response.get('order_id') or response.get('reference'),
                'paid_at': response.get('paid_at') or response.get('paidAt'),
                'payment_method': response.get('payment_method') or response.get('paymentMethod'),
                'metadata': response.get('metadata', {}),
                'transaction_id': response.get('transaction_id') or response.get('id') or transaction_id,
                'reference': response.get('reference'),
            }
        
        logger.warning(
            f"{LOG_PREFIX} phase=verify_payment_result transaction_id={transaction_id} success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def cancel_payment(self, transaction_id: str, reason: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Annule une transaction en attente
        
        Args:
            transaction_id: ID de la transaction
            reason: Raison de l'annulation (optionnel)
            
        Returns:
            Tuple (success, response_data)
        """
        logger.info(f"{LOG_PREFIX} phase=cancel_payment transaction_id={transaction_id} reason={reason}")
        # Endpoint d'annulation selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        data = {}
        if reason:
            data['reason'] = reason
        
        endpoint = f"/v1/transaction/{transaction_id}/cancel"
        success, response = self._make_request('POST', endpoint, data if data else None)
        
        if success:
            logger.info(f"{LOG_PREFIX} phase=cancel_payment_result transaction_id={transaction_id} success=True")
            return True, {
                'status': response.get('status', 'cancelled'),
                'message': response.get('message', 'Transaction annulée avec succès'),
                'transaction_id': response.get('transaction_id') or response.get('id') or transaction_id,
            }
        
        logger.warning(
            f"{LOG_PREFIX} phase=cancel_payment_result transaction_id={transaction_id} success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Effectue un remboursement (partiel ou total)
        
        Args:
            transaction_id: ID de la transaction originale
            amount: Montant à rembourser (None = remboursement total)
            reason: Raison du remboursement
            
        Returns:
            Tuple (success, refund_data) avec refund_id, status, etc.
        """
        logger.info(
            f"{LOG_PREFIX} phase=refund_payment transaction_id={transaction_id} amount={amount} reason={reason}"
        )
        # Structure des données selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        data = {
            'portefeuille': self.merchant_id,  # Merchant ID (wallet)
        }
        if amount:
            data['amount'] = float(amount)
        if reason:
            data['reason'] = reason
        
        # Endpoint de remboursement selon la documentation SingPay
        endpoint = f"/v1/transaction/{transaction_id}/refund"
        success, response = self._make_request('POST', endpoint, data)
        
        if success:
            logger.info(
                f"{LOG_PREFIX} phase=refund_payment_result transaction_id={transaction_id} success=True "
                f"refund_id={response.get('refund_id') or response.get('id')}"
            )
            return True, {
                'refund_id': response.get('refund_id') or response.get('id'),
                'status': response.get('status', 'pending'),
                'amount': response.get('amount') or amount,
                'transaction_id': transaction_id,
                'message': response.get('message', 'Remboursement initié avec succès'),
            }
        
        logger.warning(
            f"{LOG_PREFIX} phase=refund_payment_result transaction_id={transaction_id} success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def init_airtel_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_phone: str,
        description: str,
        callback_url: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initialise un paiement via USSD Push Airtel Money
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Args:
            amount: Montant à payer
            currency: Code devise (XOF, XAF, etc.)
            order_id: ID unique de la commande
            customer_phone: Téléphone du client (format international, ex: +24101234567)
            description: Description de la transaction
            callback_url: URL de callback pour les notifications
            metadata: Métadonnées supplémentaires
            
        Returns:
            Tuple (success, response_data) avec transaction_id
        """
        data = {
            'portefeuille': self.merchant_id,
            'reference': f"REF-{order_id}",
            'amount': float(amount),
            'phone': customer_phone,
            'description': description,
            'callback_url': callback_url,
        }
        
        if metadata:
            data.update(metadata)
        
        logger.info(
            f"{LOG_PREFIX} phase=init_airtel_payment order_id={order_id} amount={amount} phone={(customer_phone or '')[:6]}***"
        )
        success, response = self._make_request('POST', '/74/paiement', data)
        
        if success:
            txn_id = response.get('transaction_id') or response.get('id')
            logger.info(f"{LOG_PREFIX} phase=init_airtel_payment_result order_id={order_id} success=True transaction_id={txn_id}")
            return True, {
                'transaction_id': txn_id,
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'USSD Push envoyé'),
            }
        
        logger.warning(f"{LOG_PREFIX} phase=init_airtel_payment_result order_id={order_id} success=False response={_sanitize_for_log(response)}")
        return False, response
    
    def init_moov_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_phone: str,
        description: str,
        callback_url: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initialise un paiement via USSD Push Moov Money
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Args:
            amount: Montant à payer
            currency: Code devise (XOF, XAF, etc.)
            order_id: ID unique de la commande
            customer_phone: Téléphone du client (format international)
            description: Description de la transaction
            callback_url: URL de callback pour les notifications
            metadata: Métadonnées supplémentaires
            
        Returns:
            Tuple (success, response_data) avec transaction_id
        """
        data = {
            'portefeuille': self.merchant_id,
            'reference': f"REF-{order_id}",
            'amount': float(amount),
            'phone': customer_phone,
            'description': description,
            'callback_url': callback_url,
        }
        
        if metadata:
            data.update(metadata)
        
        logger.info(
            f"{LOG_PREFIX} phase=init_moov_payment order_id={order_id} amount={amount} phone={(customer_phone or '')[:6]}***"
        )
        success, response = self._make_request('POST', '/62/paiement', data)
        
        if success:
            txn_id = response.get('transaction_id') or response.get('id')
            logger.info(f"{LOG_PREFIX} phase=init_moov_payment_result order_id={order_id} success=True transaction_id={txn_id}")
            return True, {
                'transaction_id': txn_id,
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'USSD Push envoyé'),
            }
        
        logger.warning(f"{LOG_PREFIX} phase=init_moov_payment_result order_id={order_id} success=False response={_sanitize_for_log(response)}")
        return False, response
    
    def init_maviance_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_phone: str,
        description: str,
        callback_url: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initialise un paiement via Maviance Mobile Money
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Args:
            amount: Montant à payer
            currency: Code devise (XOF, XAF, etc.)
            order_id: ID unique de la commande
            customer_phone: Téléphone du client (format international)
            description: Description de la transaction
            callback_url: URL de callback pour les notifications
            metadata: Métadonnées supplémentaires
            
        Returns:
            Tuple (success, response_data) avec transaction_id
        """
        data = {
            'portefeuille': self.merchant_id,
            'reference': f"REF-{order_id}",
            'amount': float(amount),
            'phone': customer_phone,
            'description': description,
            'callback_url': callback_url,
        }
        
        if metadata:
            data.update(metadata)
        
        logger.info(
            f"{LOG_PREFIX} phase=init_maviance_payment order_id={order_id} amount={amount} phone={(customer_phone or '')[:6]}***"
        )
        success, response = self._make_request('POST', '/maviance/paiement', data)
        
        if success:
            txn_id = response.get('transaction_id') or response.get('id')
            logger.info(f"{LOG_PREFIX} phase=init_maviance_payment_result order_id={order_id} success=True transaction_id={txn_id}")
            return True, {
                'transaction_id': txn_id,
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'Paiement Maviance initié'),
            }
        
        logger.warning(f"{LOG_PREFIX} phase=init_maviance_payment_result order_id={order_id} success=False response={_sanitize_for_log(response)}")
        return False, response
    
    def init_disbursement(
        self,
        amount: float,
        currency: str,
        recipient_phone: str,
        recipient_name: str,
        description: str,
        reference: Optional[str] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Initialise un virement (disbursement) vers un portefeuille mobile money
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Args:
            amount: Montant à virer
            currency: Code devise (XOF, XAF, etc.)
            recipient_phone: Téléphone du bénéficiaire (format international)
            recipient_name: Nom du bénéficiaire
            description: Description du virement
            reference: Référence unique (générée automatiquement si None)
            callback_url: URL de callback pour les notifications
            metadata: Métadonnées supplémentaires
            
        Returns:
            Tuple (success, response_data) avec disbursement_id
        """
        if not reference:
            import uuid
            reference = f"DISB-{uuid.uuid4().hex[:12].upper()}"
        
        logger.info(
            f"{LOG_PREFIX} phase=init_disbursement reference={reference} amount={amount} currency={currency} "
            f"recipient_phone={(recipient_phone or '')[:6]}*** recipient_name={recipient_name}"
        )
        data = {
            'portefeuille': self.merchant_id,
            'reference': reference,
            'amount': float(amount),
            'phone': recipient_phone,
            'name': recipient_name,
            'description': description,
            'disbursement': self.disbursement_id or '',  # ID portefeuille disbursement (SINGPAY_DISBURSEMENT_ID)
            'isTransfer': True,  # Indique que c'est un virement
        }
        
        if callback_url:
            data['callback_url'] = callback_url
        
        if metadata:
            data.update(metadata)
        
        success, response = self._make_request('POST', '/v1/disbursement', data)
        
        if success:
            disb_id = response.get('disbursement_id') or response.get('id') or reference
            logger.info(
                f"{LOG_PREFIX} phase=init_disbursement_result reference={reference} success=True "
                f"disbursement_id={disb_id} status={response.get('status')}"
            )
            return True, {
                'disbursement_id': disb_id,
                'status': response.get('status', 'pending'),
                'amount': response.get('amount', amount),
                'message': response.get('message', 'Virement initié avec succès'),
            }
        
        logger.warning(
            f"{LOG_PREFIX} phase=init_disbursement_result reference={reference} success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def get_transaction_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[bool, Dict]:
        """
        Récupère l'historique des transactions
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Args:
            start_date: Date de début (format ISO ou YYYY-MM-DD)
            end_date: Date de fin (format ISO ou YYYY-MM-DD)
            status: Filtrer par statut (pending, success, failed, cancelled)
            limit: Nombre de résultats à retourner
            offset: Offset pour la pagination
            
        Returns:
            Tuple (success, response_data) avec liste de transactions
        """
        params = {
            'limit': limit,
            'offset': offset,
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if status:
            params['status'] = status
        
        logger.info(
            f"{LOG_PREFIX} phase=get_transaction_history status={status} limit={limit} offset={offset} "
            f"start_date={start_date} end_date={end_date}"
        )
        success, response = self._make_request('GET', '/v1/transactions', params)
        
        if success:
            count = len(response.get('transactions', []) or response.get('data', []))
            logger.info(
                f"{LOG_PREFIX} phase=get_transaction_history_result success=True count={count} total={response.get('total')}"
            )
            return True, {
                'transactions': response.get('transactions', []) or response.get('data', []),
                'total': response.get('total', 0),
                'limit': limit,
                'offset': offset,
            }
        
        logger.warning(
            f"{LOG_PREFIX} phase=get_transaction_history_result success=False response={_sanitize_for_log(response)}"
        )
        return False, response
    
    def get_balance(self) -> Tuple[bool, Dict]:
        """
        Récupère le solde du portefeuille marchand
        Documentation: https://client.singpay.ga/doc/reference/index.html
        
        Returns:
            Tuple (success, response_data) avec balance, currency, etc.
        """
        logger.info("Récupération du solde du portefeuille")
        success, response = self._make_request('GET', '/v1/wallet/balance')
        
        if success:
            return True, {
                'balance': response.get('balance', 0),
                'currency': response.get('currency', 'XOF'),
                'available_balance': response.get('available_balance', response.get('balance', 0)),
            }
        
        logger.warning(f"{LOG_PREFIX} phase=get_balance_result success=False response={_sanitize_for_log(response)}")
        return False, response
    
    def pay_commission(
        self,
        amount: float,
        recipient_phone: str,
        recipient_name: str,
        order_id: str,
        commission_type: str = 'seller',
        description: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Effectue le paiement d'une commission (vendeur, plateforme, etc.)
        Utilise le système de virement (disbursement) pour payer les commissions
        
        Args:
            amount: Montant de la commission à payer
            recipient_phone: Téléphone du bénéficiaire (format international)
            recipient_name: Nom du bénéficiaire
            order_id: ID de la commande associée
            commission_type: Type de commission (seller, platform, etc.)
            description: Description du paiement (générée automatiquement si None)
            callback_url: URL de callback pour les notifications
            
        Returns:
            Tuple (success, response_data) avec disbursement_id
        """
        if not description:
            description = f"Commission {commission_type} pour commande {order_id}"
        
        reference = f"COMM-{commission_type.upper()}-{order_id}"
        logger.info(
            f"{LOG_PREFIX} phase=pay_commission order_id={order_id} commission_type={commission_type} "
            f"amount={amount} reference={reference}"
        )
        metadata = {
            'order_id': order_id,
            'commission_type': commission_type,
            'is_commission': True,
        }
        
        return self.init_disbursement(
            amount=amount,
            currency='XOF',
            recipient_phone=recipient_phone,
            recipient_name=recipient_name,
            description=description,
            reference=reference,
            callback_url=callback_url,
            metadata=metadata
        )
    
    def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Vérifie la signature d'un webhook SingPay
        
        Args:
            payload: Corps de la requête webhook
            signature: Signature reçue dans les headers
            timestamp: Timestamp de la requête
            
        Returns:
            True si la signature est valide
        """
        try:
            payload_data = json.loads(payload) if isinstance(payload, str) else payload
            expected_signature = self._generate_signature(payload_data, timestamp)
            is_valid = hmac.compare_digest(expected_signature, signature)
            logger.info(
                f"{LOG_PREFIX} phase=webhook_verify_signature valid={is_valid} "
                f"payload_keys={list(payload_data.keys()) if isinstance(payload_data, dict) else 'n/a'}"
            )
            return is_valid
        except Exception as e:
            logger.error(
                f"{LOG_PREFIX} phase=webhook_verify_signature valid=False error={e} payload_preview={(payload[:200] if isinstance(payload, str) else str(payload)[:200])}..."
            )
            return False


# Instance globale du service
singpay_service = SingPayService()

