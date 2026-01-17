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
        self.environment = getattr(settings, 'SINGPAY_ENVIRONMENT', 'sandbox')  # 'sandbox' ou 'production'
        bypass_setting = getattr(settings, 'SINGPAY_BYPASS_API', None)
        
        # Si les credentials sont configurés, désactiver automatiquement le mode bypass
        if all([self.api_key, self.api_secret, self.merchant_id]):
            # Credentials présents
            if bypass_setting is None:
                # Si SINGPAY_BYPASS_API n'est pas défini dans .env, désactiver automatiquement le bypass
                self.bypass_api = False
                logger.info("✅ SingPay API réelle activée - Credentials configurés (bypass désactivé automatiquement)")
            elif bypass_setting is False:
                # Explicitement désactivé
                self.bypass_api = False
                logger.info("✅ SingPay API réelle activée - Credentials configurés")
            else:
                # Explicitement activé (bypass_setting is True)
                self.bypass_api = True
                logger.warning("⚠️ SingPay en mode BYPASS malgré les credentials configurés (SINGPAY_BYPASS_API=True dans .env)")
        else:
            # Pas de credentials : mode bypass obligatoire
            self.bypass_api = True
            logger.warning("⚠️ SingPay credentials manquants - Mode BYPASS activé")
            if not self.api_key:
                logger.warning("  - SINGPAY_API_KEY manquant")
            if not self.api_secret:
                logger.warning("  - SINGPAY_API_SECRET manquant")
            if not self.merchant_id:
                logger.warning("  - SINGPAY_MERCHANT_ID manquant")
        
        if self.environment == 'production':
            self.base_url = self.BASE_URL_PRODUCTION
        else:
            self.base_url = self.BASE_URL_SANDBOX
        
        if not all([self.api_key, self.api_secret, self.merchant_id]) and not self.bypass_api:
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
        
        # Mode bypass pour les tests
        if self.bypass_api:
            logger.warning(f"SingPay API BYPASS MODE ACTIVÉ - {method} {endpoint}")
            logger.warning("⚠️ ATTENTION: Les paiements sont simulés. Pour utiliser l'API réelle, configurez SINGPAY_BYPASS_API = False dans settings.py")
            # Simuler une réponse réussie
            if endpoint == '/v1/ext':
                import uuid
                from datetime import timedelta
                transaction_id = f"TEST-{uuid.uuid4().hex[:16].upper()}"
                return True, {
                    'payment_url': f'/payments/singpay/test-payment/{transaction_id}/',
                    'transaction_id': transaction_id,
                    'reference': f"REF-{data.get('order_id', 'UNKNOWN')}",
                    'expires_at': (timezone.now() + timedelta(hours=24)).isoformat(),
                }
            elif '/verify' in endpoint or '/transaction/' in endpoint:
                return True, {
                    'status': 'success',
                    'amount': data.get('amount', 0),
                    'currency': data.get('currency', 'XOF'),
                    'order_id': data.get('order_id', ''),
                    'paid_at': timezone.now().isoformat(),
                    'payment_method': 'AirtelMoney',  # Simulé
                    'metadata': {},
                }
            elif '/cancel' in endpoint:
                return True, {
                    'status': 'cancelled',
                    'message': 'Transaction annulée avec succès (mode test)',
                }
            elif '/refund' in endpoint:
                import uuid
                return True, {
                    'refund_id': f"REFUND-{uuid.uuid4().hex[:16].upper()}",
                    'status': 'pending',
                    'amount': data.get('amount', 0),
                    'message': 'Remboursement initié (mode test)',
                }
            elif '/74/paiement' in endpoint or '/62/paiement' in endpoint or '/maviance/paiement' in endpoint:
                import uuid
                transaction_id = f"TEST-{uuid.uuid4().hex[:16].upper()}"
                return True, {
                    'transaction_id': transaction_id,
                    'status': 'pending',
                    'message': 'USSD Push envoyé (mode test)',
                }
            elif '/disbursement' in endpoint or '/virement' in endpoint:
                import uuid
                return True, {
                    'disbursement_id': f"DISB-{uuid.uuid4().hex[:16].upper()}",
                    'status': 'pending',
                    'message': 'Virement initié (mode test)',
                }
            else:
                return True, {'status': 'success', 'message': 'Bypass mode - operation simulated'}
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(data)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return False, {'error': f'Unsupported method: {method}'}
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"SingPay API {method} {endpoint} - Success")
            logger.debug(f"Réponse SingPay: {response_data}")
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
                    logger.error(f"SingPay API Error Response: {error_response}")
                except:
                    error_details['response_text'] = e.response.text[:500]  # Limiter la taille
            
            logger.error(f"SingPay API {method} {endpoint} - Error: {error_details}")
            return False, error_details
        except json.JSONDecodeError as e:
            logger.error(f"SingPay API response JSON decode error: {str(e)}")
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
            'disbursement': '',  # Optionnel - pour les virements
            'logoURL': '',  # Optionnel - URL du logo à afficher
            'isTransfer': False,  # Type de transaction (False = paiement, True = virement)
            'order_id': order_id,  # Ajouter order_id pour le mode bypass
        }
        
        if metadata:
            # Ajouter les métadonnées si nécessaire
            if 'logo_url' in metadata:
                data['logoURL'] = metadata['logo_url']
            if 'disbursement' in metadata:
                data['disbursement'] = metadata['disbursement']
        
        # Logger les données envoyées pour le débogage
        logger.info(f"Initialisation paiement SingPay - Order ID: {order_id}, Amount: {amount}, Currency: {currency}")
        logger.debug(f"Données envoyées à SingPay: {data}")
        logger.debug(f"URLs - Callback: {callback_url}, Return: {return_url}")
        
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
                logger.info(f"URL de paiement SingPay obtenue: {payment_url}")
                logger.info(f"transaction_id final: {transaction_id}")
                logger.info(f"reference: {reference}")
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
                logger.warning(f"Réponse SingPay sans lien de paiement: {response}")
                return False, {'error': 'Lien de paiement manquant dans la réponse', 'response': response}
        
        return False, response
    
    def verify_payment(self, transaction_id: str) -> Tuple[bool, Dict]:
        """
        Vérifie le statut d'une transaction
        
        Args:
            transaction_id: ID de la transaction SingPay
            
        Returns:
            Tuple (success, transaction_data)
        """
        # Endpoint de vérification selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        endpoint = f"/v1/transaction/{transaction_id}"
        success, response = self._make_request('GET', endpoint)
        
        if success:
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
        # Endpoint d'annulation selon la documentation SingPay
        # Documentation: https://client.singpay.ga/doc/reference/index.html
        data = {}
        if reason:
            data['reason'] = reason
        
        endpoint = f"/v1/transaction/{transaction_id}/cancel"
        success, response = self._make_request('POST', endpoint, data if data else None)
        
        if success:
            return True, {
                'status': response.get('status', 'cancelled'),
                'message': response.get('message', 'Transaction annulée avec succès'),
                'transaction_id': response.get('transaction_id') or response.get('id') or transaction_id,
            }
        
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
            return True, {
                'refund_id': response.get('refund_id') or response.get('id'),
                'status': response.get('status', 'pending'),
                'amount': response.get('amount') or amount,
                'transaction_id': transaction_id,
                'message': response.get('message', 'Remboursement initié avec succès'),
            }
        
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
        
        logger.info(f"Initialisation paiement Airtel Money - Order ID: {order_id}, Phone: {customer_phone}")
        success, response = self._make_request('POST', '/74/paiement', data)
        
        if success:
            return True, {
                'transaction_id': response.get('transaction_id') or response.get('id'),
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'USSD Push envoyé'),
            }
        
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
        
        logger.info(f"Initialisation paiement Moov Money - Order ID: {order_id}, Phone: {customer_phone}")
        success, response = self._make_request('POST', '/62/paiement', data)
        
        if success:
            return True, {
                'transaction_id': response.get('transaction_id') or response.get('id'),
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'USSD Push envoyé'),
            }
        
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
        
        logger.info(f"Initialisation paiement Maviance - Order ID: {order_id}, Phone: {customer_phone}")
        success, response = self._make_request('POST', '/maviance/paiement', data)
        
        if success:
            return True, {
                'transaction_id': response.get('transaction_id') or response.get('id'),
                'status': response.get('status', 'pending'),
                'message': response.get('message', 'Paiement Maviance initié'),
            }
        
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
        
        data = {
            'portefeuille': self.merchant_id,
            'reference': reference,
            'amount': float(amount),
            'phone': recipient_phone,
            'name': recipient_name,
            'description': description,
            'isTransfer': True,  # Indique que c'est un virement
        }
        
        if callback_url:
            data['callback_url'] = callback_url
        
        if metadata:
            data.update(metadata)
        
        logger.info(f"Initialisation virement - Reference: {reference}, Amount: {amount}, Recipient: {recipient_phone}")
        success, response = self._make_request('POST', '/v1/disbursement', data)
        
        if success:
            return True, {
                'disbursement_id': response.get('disbursement_id') or response.get('id') or reference,
                'status': response.get('status', 'pending'),
                'amount': response.get('amount', amount),
                'message': response.get('message', 'Virement initié avec succès'),
            }
        
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
        
        logger.info(f"Récupération historique transactions - Status: {status}, Limit: {limit}")
        success, response = self._make_request('GET', '/v1/transactions', params)
        
        if success:
            return True, {
                'transactions': response.get('transactions', []) or response.get('data', []),
                'total': response.get('total', 0),
                'limit': limit,
                'offset': offset,
            }
        
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
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la signature: {e}")
            return False


# Instance globale du service
singpay_service = SingPayService()

