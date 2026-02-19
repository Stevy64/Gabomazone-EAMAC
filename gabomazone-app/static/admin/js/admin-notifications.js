/**
 * Système de notifications en temps réel pour l'admin
 * Polling automatique toutes les 10 secondes
 */
(function() {
    'use strict';
    
    const NOTIFICATIONS_URL = '/staff/notifications/';
    const MARK_READ_URL = '/staff/notifications/';
    const MARK_ALL_READ_URL = '/staff/notifications/read-all/';
    const POLL_INTERVAL = 10000; // 10 secondes
    
    let pollInterval = null;
    let lastNotificationCount = 0;
    
    /**
     * Récupère les notifications depuis l'API
     */
    async function fetchNotifications() {
        try {
            const response = await fetch(NOTIFICATIONS_URL, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                // Si 404, l'endpoint n'existe pas encore
                if (response.status === 404) {
                    console.warn('Endpoint de notifications non trouvé. Vérifiez que les migrations sont appliquées.');
                    return;
                }
                throw new Error('Erreur lors de la récupération des notifications');
            }
            
            const data = await response.json();
            updateNotificationsUI(data);
            
        } catch (error) {
            // Ne pas afficher d'erreur si c'est juste que l'endpoint n'existe pas
            if (error.message && !error.message.includes('404')) {
                console.error('Erreur notifications:', error);
            }
        }
    }
    
    /**
     * Met à jour l'interface des notifications
     */
    function updateNotificationsUI(data) {
        const badge = document.getElementById('admin-notifications-badge');
        const header = document.getElementById('admin-notifications-header');
        const list = document.getElementById('admin-notifications-list');
        const empty = document.getElementById('admin-notifications-empty');
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        
        const notifications = data.notifications || [];
        const totalUnread = data.total_unread || 0;
        
        // Mettre à jour le badge
        if (totalUnread > 0) {
            badge.textContent = totalUnread > 99 ? '99+' : totalUnread;
            badge.style.display = 'inline-block';
            header.textContent = `${totalUnread} Notification${totalUnread > 1 ? 's' : ''}`;
            markAllReadBtn.style.display = 'block';
        } else {
            badge.style.display = 'none';
            header.textContent = 'Notifications';
            markAllReadBtn.style.display = 'none';
        }
        
        // Mettre à jour la liste
        if (notifications.length === 0) {
            list.innerHTML = '<div class="dropdown-item text-center text-muted" id="admin-notifications-empty"><i class="far fa-bell-slash mr-2"></i> Aucune notification</div>';
        } else {
            let html = '';
            notifications.forEach(notification => {
                const iconClass = getNotificationIcon(notification.type);
                const timeAgo = getTimeAgo(notification.created_at);
                
                html += `
                    <a href="${notification.related_url || '#'}" class="dropdown-item notification-item" data-notification-id="${notification.id}">
                        <div class="d-flex align-items-start">
                            <div class="mr-3">
                                <i class="${iconClass} text-${getNotificationColor(notification.type)}"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="font-weight-bold">${escapeHtml(notification.title)}</div>
                                <div class="text-sm text-muted">${escapeHtml(notification.message)}</div>
                                <div class="text-xs text-muted mt-1">
                                    <i class="far fa-clock mr-1"></i> ${timeAgo}
                                </div>
                            </div>
                            <button type="button" class="btn btn-sm btn-link text-muted mark-read-btn" data-notification-id="${notification.id}" onclick="event.stopPropagation(); markNotificationRead(${notification.id});" title="Marquer comme lu">
                                <i class="far fa-check-circle"></i>
                            </button>
                        </div>
                    </a>
                    <div class="dropdown-divider"></div>
                `;
            });
            list.innerHTML = html;
        }
        
        // Animation du badge si nouvelle notification
        if (totalUnread > lastNotificationCount) {
            animateBadge();
        }
        lastNotificationCount = totalUnread;
    }
    
    /**
     * Obtient l'icône selon le type de notification
     */
    function getNotificationIcon(type) {
        const icons = {
            'BOOST_REQUEST': 'fas fa-rocket',
            'PREMIUM_SUBSCRIPTION': 'fas fa-crown',
            'CONTACT_MESSAGE': 'fas fa-envelope',
            'PRODUCT_APPROVAL': 'fas fa-box',
        };
        return icons[type] || 'fas fa-bell';
    }
    
    /**
     * Obtient la couleur selon le type de notification
     */
    function getNotificationColor(type) {
        const colors = {
            'BOOST_REQUEST': 'warning',
            'PREMIUM_SUBSCRIPTION': 'info',
            'CONTACT_MESSAGE': 'primary',
            'PRODUCT_APPROVAL': 'success',
        };
        return colors[type] || 'secondary';
    }
    
    /**
     * Calcule le temps écoulé depuis la création
     */
    function getTimeAgo(isoDate) {
        const now = new Date();
        const date = new Date(isoDate);
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'À l\'instant';
        if (diffMins < 60) return `Il y a ${diffMins} min`;
        if (diffHours < 24) return `Il y a ${diffHours} h`;
        if (diffDays < 7) return `Il y a ${diffDays} j`;
        return date.toLocaleDateString('fr-FR');
    }
    
    /**
     * Échappe le HTML pour éviter les injections XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Anime le badge lors d'une nouvelle notification
     */
    function animateBadge() {
        const badge = document.getElementById('admin-notifications-badge');
        if (badge) {
            badge.style.animation = 'none';
            setTimeout(() => {
                badge.style.animation = 'pulse 0.5s ease-in-out';
            }, 10);
        }
    }
    
    /**
     * Marque une notification comme lue
     */
    window.markNotificationRead = async function(notificationId) {
        try {
            const response = await fetch(`${MARK_READ_URL}${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                // Recharger les notifications
                fetchNotifications();
            }
        } catch (error) {
            console.error('Erreur lors du marquage comme lu:', error);
        }
    };
    
    /**
     * Marque toutes les notifications comme lues
     */
    window.markAllNotificationsRead = async function() {
        try {
            const response = await fetch(MARK_ALL_READ_URL, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                fetchNotifications();
            }
        } catch (error) {
            console.error('Erreur lors du marquage de toutes les notifications:', error);
        }
    };
    
    /**
     * Récupère un cookie par son nom
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    /**
     * Initialise le système de notifications
     */
    function init() {
        // Charger les notifications immédiatement
        fetchNotifications();
        
        // Démarrer le polling
        pollInterval = setInterval(fetchNotifications, POLL_INTERVAL);
        
        // Écouter le clic sur "Tout marquer comme lu"
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                markAllNotificationsRead();
            });
        }
        
        // Recharger les notifications quand le dropdown est ouvert
        const dropdown = document.getElementById('admin-notifications-dropdown');
        if (dropdown) {
            const dropdownToggle = dropdown.querySelector('[data-toggle="dropdown"]');
            if (dropdownToggle) {
                dropdownToggle.addEventListener('click', function() {
                    fetchNotifications();
                });
            }
        }
    }
    
    // Attendre que le DOM soit chargé
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Nettoyer l'intervalle quand la page est déchargée
    window.addEventListener('beforeunload', function() {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
    });
})();

