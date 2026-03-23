/**
 * GMModal — Gabomazone Modal System
 * Provides elegant, accessible modal dialogs for confirmations, alerts, and errors.
 */
const GMModal = {
    show: function(options) {
        const defaults = {
            type: 'info',
            title: 'Information',
            message: '',
            confirmText: 'OK',
            cancelText: 'Annuler',
            showCancel: false,
            onConfirm: null,
            onCancel: null,
            autoClose: false,
            autoCloseDelay: 3000
        };

        const config = { ...defaults, ...options };

        const icons = {
            success: 'fi-rs-check',
            error: 'fi-rs-cross-small',
            warning: 'fi-rs-exclamation',
            info: 'fi-rs-info',
            confirm: 'fi-rs-interrogation'
        };

        const overlay = document.createElement('div');
        overlay.className = 'gm-modal-overlay';

        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };

        const sanitizeMessage = (message) => {
            if (!message) return '';
            let safe = message
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            safe = safe
                .replace(/&lt;br\s*\/?&gt;/gi, '<br>')
                .replace(/&lt;br&gt;/gi, '<br>')
                .replace(/&lt;strong&gt;(.*?)&lt;\/strong&gt;/gi, '<strong>$1</strong>')
                .replace(/&lt;em&gt;(.*?)&lt;\/em&gt;/gi, '<em>$1</em>');
            return safe;
        };

        const safeMessage = sanitizeMessage(config.message);
        const safeTitle = escapeHtml(config.title);
        const btnClass = config.type === 'error' ? 'danger' : config.type === 'success' ? 'success' : 'primary';

        overlay.innerHTML = `
            <div class="gm-modal">
                <div class="gm-modal-header">
                    <div class="gm-modal-icon ${config.type}">
                        <i class="${icons[config.type] || icons.info}"></i>
                    </div>
                    <h3 class="gm-modal-title">${safeTitle}</h3>
                </div>
                <div class="gm-modal-body">
                    <div class="gm-modal-message">${safeMessage}</div>
                </div>
                <div class="gm-modal-footer">
                    ${config.showCancel ? `<button type="button" class="gm-modal-btn secondary" data-action="cancel">${escapeHtml(config.cancelText)}</button>` : ''}
                    <button type="button" class="gm-modal-btn ${btnClass}" data-action="confirm">${escapeHtml(config.confirmText)}</button>
                </div>
            </div>
        `;

        document.getElementById('gm-modal-container').appendChild(overlay);

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                GMModal.close(overlay, config.onCancel);
            }
        });

        overlay.querySelector('[data-action="confirm"]').addEventListener('click', function() {
            GMModal.close(overlay, config.onConfirm);
        });

        const cancelBtn = overlay.querySelector('[data-action="cancel"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                GMModal.close(overlay, config.onCancel);
            });
        }

        if (config.autoClose) {
            setTimeout(() => GMModal.close(overlay), config.autoCloseDelay);
        }

        overlay.querySelector('[data-action="confirm"]').focus();
        return overlay;
    },

    close: function(overlay, callback) {
        overlay.classList.add('closing');
        overlay.querySelector('.gm-modal').classList.add('closing');
        setTimeout(() => {
            overlay.remove();
            if (callback && typeof callback === 'function') {
                callback();
            }
        }, 200);
    },

    success: function(title, message, onConfirm) {
        return this.show({ type: 'success', title, message, onConfirm });
    },

    error: function(title, message, onConfirm) {
        return this.show({ type: 'error', title, message, onConfirm });
    },

    warning: function(title, message, onConfirm) {
        return this.show({ type: 'warning', title, message, onConfirm });
    },

    info: function(title, message, onConfirm) {
        return this.show({ type: 'info', title, message, onConfirm });
    },

    confirm: function(title, message, onConfirm, onCancel) {
        return this.show({ type: 'confirm', title, message, showCancel: true, confirmText: 'Confirmer', cancelText: 'Annuler', onConfirm, onCancel });
    },

    confirmDelete: function(itemName, onConfirm) {
        return this.show({
            type: 'warning',
            title: 'Confirmer la suppression',
            message: `Êtes-vous sûr de vouloir supprimer "${itemName}" ? Cette action est irréversible.`,
            showCancel: true,
            confirmText: 'Supprimer',
            cancelText: 'Annuler',
            onConfirm
        });
    }
};

window.gmAlert = function(message, title) {
    GMModal.info(title || 'Information', message);
};

window.gmConfirm = function(message, title) {
    return new Promise((resolve) => {
        GMModal.confirm(title || 'Confirmation', message, () => resolve(true), () => resolve(false));
    });
};
