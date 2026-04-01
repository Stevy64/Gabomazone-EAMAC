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
            /** Trusted HTML for the modal body (skips message sanitization). Use only with server-controlled markup. */
            messageHtml: null,
            /** Extra class on .gm-modal (e.g. gm-modal--singpay). */
            modalClass: '',
            /** Called after the overlay is mounted (e.g. iframe load hooks). */
            onOpen: null,
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
        const modalExtraClass = (config.modalClass || '').trim();
        const modalClassAttr = modalExtraClass ? ` ${modalExtraClass}` : '';
        const bodyInner = config.messageHtml
            ? config.messageHtml
            : `<div class="gm-modal-message">${safeMessage}</div>`;
        const bodyClass = config.messageHtml ? 'gm-modal-body gm-modal-body--html' : 'gm-modal-body';

        overlay.innerHTML = `
            <div class="gm-modal${modalClassAttr}">
                <div class="gm-modal-header">
                    <div class="gm-modal-icon ${config.type}">
                        <i class="${icons[config.type] || icons.info}"></i>
                    </div>
                    <h3 class="gm-modal-title">${safeTitle}</h3>
                </div>
                <div class="${bodyClass}">
                    ${bodyInner}
                </div>
                <div class="gm-modal-footer">
                    ${config.showCancel ? `<button type="button" class="gm-modal-btn secondary" data-action="cancel">${escapeHtml(config.cancelText)}</button>` : ''}
                    <button type="button" class="gm-modal-btn ${btnClass}" data-action="confirm">${escapeHtml(config.confirmText)}</button>
                </div>
            </div>
        `;

        const modalRoot = document.getElementById('gm-modal-container') || document.body;
        modalRoot.appendChild(overlay);

        if (config.onOpen && typeof config.onOpen === 'function') {
            try {
                config.onOpen(overlay);
            } catch (e) {
                console.error('GMModal.onOpen', e);
            }
        }

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

window.GMModal = GMModal;

/**
 * Lance le paiement SingPay avec une GMModal explicative puis ouverture (nouvel onglet ou même onglet).
 * SingPay ne peut pas être affiché en iframe : leur serveur envoie X-Frame-Options / CSP frame-ancestors
 * qui bloque l’intégration depuis un autre domaine (sécurité anti-clickjacking). Ce n’est pas contournable côté Gabomazone.
 */
window.openSingPayPaymentModal = function (paymentUrl, options) {
    if (!paymentUrl) return;
    if (typeof GMModal === 'undefined' || typeof GMModal.show !== 'function') {
        window.location.href = paymentUrl;
        return;
    }

    function escapeHtml(str) {
        var d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    }

    var opts = options || {};
    var title = opts.title || 'Paiement sécurisé SingPay';
    var safeHref = escapeAttr(paymentUrl);
    var amountBlock = opts.amountText
        ? '<p class="gm-singpay-amount">Montant&nbsp;: <strong>' + escapeHtml(opts.amountText) + '</strong></p>'
        : '';
    var messageHtml =
        amountBlock +
        '<div class="gm-singpay-external">' +
        '<p class="gm-singpay-external-lead">Pour des raisons de sécurité, SingPay n’autorise pas l’affichage de leur page de paiement dans une fenêtre intégrée sur un autre site. C’est normal et voulu côté banque / passerelle.</p>' +
        '<p class="gm-singpay-external-lead">Le paiement s’ouvre dans <strong>un nouvel onglet</strong> (ou une nouvelle fenêtre). Gardez cet onglet Gabomazone ouvert pour y revenir après paiement.</p>' +
        '<ol class="gm-singpay-external-steps">' +
        '<li>Appuyez sur <strong>Ouvrir SingPay</strong>.</li>' +
        '<li>Finalisez le paiement sur SingPay.</li>' +
        '<li>Revenez ici : actualisez ou suivez les instructions à l’écran si besoin.</li>' +
        '</ol>' +
        '<p class="gm-singpay-hint">Si rien ne s’ouvre (anti pop-up), utilisez le lien direct&nbsp;: ' +
        '<a class="gm-singpay-direct-link" href="' +
        safeHref +
        '" target="_blank" rel="noopener noreferrer">Ouvrir SingPay</a>. ' +
        'Sinon&nbsp;: <button type="button" class="gm-singpay-same-tab">Continuer dans cet onglet</button></p>' +
        '</div>';

    try {
        GMModal.show({
            type: 'info',
            title: title,
            message: '',
            messageHtml: messageHtml,
            modalClass: 'gm-modal--singpay',
            showCancel: true,
            cancelText: 'Annuler',
            confirmText: 'Ouvrir SingPay',
            onConfirm: function () {
                var w = window.open(paymentUrl, '_blank', 'noopener,noreferrer');
                if (!w) {
                    window.location.href = paymentUrl;
                }
            },
            onOpen: function (overlay) {
                var same = overlay.querySelector('.gm-singpay-same-tab');
                if (!same) return;
                same.addEventListener('click', function () {
                    GMModal.close(overlay, function () {
                        window.location.href = paymentUrl;
                    });
                });
            }
        });
    } catch (e) {
        console.error('openSingPayPaymentModal', e);
        window.location.href = paymentUrl;
    }
};
