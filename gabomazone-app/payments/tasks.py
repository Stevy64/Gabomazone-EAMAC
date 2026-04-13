from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def reconcile_pending_transactions():
    """Vérifie le statut réel des transactions PENDING depuis plus de 15 min."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import SingPayTransaction
    from .services.singpay import singpay_service

    cutoff = timezone.now() - timedelta(minutes=15)
    pending = SingPayTransaction.objects.filter(
        status='pending',
        created_at__lt=cutoff
    )

    reconciled = 0
    for tx in pending:
        try:
            success, response = singpay_service.verify_payment(tx.transaction_id)
            if success:
                actual_status = response.get('status', '').lower()
                if actual_status in ['success', 'completed']:
                    tx.status = SingPayTransaction.SUCCESS
                    tx.save()
                    logger.info('Transaction %s réconciliée → SUCCESS', tx.transaction_id)
                    reconciled += 1
                elif actual_status in ['failed', 'cancelled']:
                    tx.status = SingPayTransaction.FAILED
                    tx.save()
                    reconciled += 1
        except Exception as e:
            logger.error('Erreur réconciliation transaction %s: %s', tx.transaction_id, e)

    return f'{reconciled}/{pending.count()} transactions réconciliées.'
