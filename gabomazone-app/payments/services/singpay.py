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
    Service pour interagir avec l'API SingPay
    Documentation: https://docs.singpay.com
    """
    
    # URLs de l'API SingPay (à configurer selon l'environnement)
    BASE_URL_SANDBOX = "https://api-sandbox.singpay.com"
    BASE_URL_PRODUCTION = "https://api.singpay.com"
    
    def __init__(self):
        """Initialise le service SingPay avec les credentials"""
        self.api_key = getattr(settings, 'SINGPAY_API_KEY', '')
        self.api_secret = getattr(settings, 'SINGPAY_API_SECRET', '')
        self.merchant_id = getattr(settings, 'SINGPAY_MERCHANT_ID', '')
        self.environment = getattr(settings, 'SINGPAY_ENVIRONMENT', 'sandbox')  # 'sandbox' ou 'production'
        self.bypass_api = getattr(settings, 'SINGPAY_BYPASS_API', True)  # Mode test : bypass l'API
        
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
    
    def _get_headers(self, data: Dict) -> Dict[str, str]:
        """
        Génère les headers pour une requête API
        
        Args:
            data: Données de la requête
            
        Returns:
            Dictionnaire des headers
        """
        timestamp = str(int(time.time()))
        signature = self._generate_signature(data, timestamp)
        
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'X-Merchant-ID': self.merchant_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature,
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
            logger.info(f"SingPay API BYPASS MODE - {method} {endpoint}")
            # Simuler une réponse réussie
            if endpoint == '/api/v1/payments/init':
                import uuid
                from datetime import timedelta
                transaction_id = f"TEST-{uuid.uuid4().hex[:16].upper()}"
                return True, {
                    'payment_url': f'/payments/singpay/test-payment/{transaction_id}/',
                    'transaction_id': transaction_id,
                    'reference': f"REF-{data.get('order_id', 'UNKNOWN')}",
                    'expires_at': (timezone.now() + timedelta(hours=24)).isoformat(),
                }
            elif '/verify' in endpoint:
                return True, {
                    'status': 'success',
                    'amount': data.get('amount', 0),
                    'currency': data.get('currency', 'XOF'),
                    'order_id': data.get('order_id', ''),
                    'paid_at': datetime.now().isoformat(),
                    'payment_method': 'AirtelMoney',  # Simulé
                    'metadata': {},
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
            return True, response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SingPay API {method} {endpoint} - Error: {str(e)}")
            return False, {'error': str(e), 'status_code': getattr(e.response, 'status_code', None)}
        except json.JSONDecodeError as e:
            logger.error(f"SingPay API response JSON decode error: {str(e)}")
            return False, {'error': 'Invalid JSON response'}
    
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
        data = {
            'amount': float(amount),
            'currency': currency.upper(),
            'order_id': str(order_id),
            'customer': {
                'email': customer_email,
                'phone': customer_phone,
                'name': customer_name,
            },
            'description': description,
            'callback_url': callback_url,
            'return_url': return_url,
        }
        
        if metadata:
            data['metadata'] = metadata
        
        success, response = self._make_request('POST', '/api/v1/payments/init', data)
        
        if success and 'payment_url' in response:
            return True, {
                'payment_url': response['payment_url'],
                'transaction_id': response.get('transaction_id'),
                'reference': response.get('reference'),
                'expires_at': response.get('expires_at'),
            }
        
        return False, response
    
    def verify_payment(self, transaction_id: str) -> Tuple[bool, Dict]:
        """
        Vérifie le statut d'une transaction
        
        Args:
            transaction_id: ID de la transaction SingPay
            
        Returns:
            Tuple (success, transaction_data)
        """
        endpoint = f"/api/v1/payments/{transaction_id}/verify"
        success, response = self._make_request('GET', endpoint)
        
        if success:
            return True, {
                'status': response.get('status'),  # pending, success, failed, cancelled
                'amount': response.get('amount'),
                'currency': response.get('currency'),
                'order_id': response.get('order_id'),  # ID utilisé par SingPay (peut être différent de internal_order_id)
                'paid_at': response.get('paid_at'),
                'payment_method': response.get('payment_method'),
                'metadata': response.get('metadata', {}),
            }
        
        return False, response
    
    def cancel_payment(self, transaction_id: str) -> Tuple[bool, Dict]:
        """
        Annule une transaction en attente
        
        Args:
            transaction_id: ID de la transaction
            
        Returns:
            Tuple (success, response_data)
        """
        endpoint = f"/api/v1/payments/{transaction_id}/cancel"
        success, response = self._make_request('POST', endpoint)
        return success, response
    
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
            Tuple (success, refund_data)
        """
        data = {}
        if amount:
            data['amount'] = float(amount)
        if reason:
            data['reason'] = reason
        
        endpoint = f"/api/v1/payments/{transaction_id}/refund"
        success, response = self._make_request('POST', endpoint, data)
        return success, response
    
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
        expected_signature = self._generate_signature(json.loads(payload), timestamp)
        return hmac.compare_digest(expected_signature, signature)


# Instance globale du service
singpay_service = SingPayService()

