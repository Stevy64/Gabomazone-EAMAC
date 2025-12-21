"""
Vues et utilitaires pour les notifications admin en temps réel
"""
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import AdminNotification


@staff_member_required
@require_http_methods(["GET"])
def get_admin_notifications(request):
    """
    API endpoint pour récupérer les notifications admin non lues
    Retourne les notifications nécessitant une action
    """
    try:
        # Récupérer les notifications non lues et non résolues
        notifications = AdminNotification.objects.filter(
            is_read=False,
            is_resolved=False
        ).order_by('-created_at')[:20]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'type_display': notification.get_notification_type_display(),
                'title': notification.title,
                'message': notification.message,
                'related_url': notification.related_url,
                'created_at': notification.created_at.isoformat(),
                'created_at_display': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            })
        
        # Compter le total de notifications non lues
        total_unread = AdminNotification.objects.filter(
            is_read=False,
            is_resolved=False
        ).count()
        
        return JsonResponse({
            'notifications': notifications_data,
            'total_unread': total_unread,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        # Si la table n'existe pas encore ou erreur
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur dans get_admin_notifications: {e}", exc_info=True)
        return JsonResponse({
            'notifications': [],
            'total_unread': 0,
            'timestamp': timezone.now().isoformat(),
            'error': 'Table AdminNotification non disponible'
        })


@staff_member_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Marquer une notification comme lue"""
    try:
        notification = AdminNotification.objects.get(id=notification_id)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except AdminNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification introuvable'}, status=404)


@staff_member_required
@require_http_methods(["POST"])
def mark_notification_resolved(request, notification_id):
    """Marquer une notification comme résolue"""
    try:
        notification = AdminNotification.objects.get(id=notification_id)
        notification.mark_as_resolved()
        return JsonResponse({'success': True})
    except AdminNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification introuvable'}, status=404)


@staff_member_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Marquer toutes les notifications comme lues"""
    from django.utils import timezone
    updated = AdminNotification.objects.filter(
        is_read=False,
        is_resolved=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'success': True, 'updated': updated})

