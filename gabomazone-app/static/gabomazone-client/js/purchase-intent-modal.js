/**
 * Modale « intention d’achat » C2C (remplace la page plein écran).
 */
(function () {
    function gmPiUrl(productId) {
        var base = window.GM_C2C_PURCHASE_INTENT_URL_TEMPLATE || '';
        if (!base) {
            return '/c2c/purchase-intent/' + encodeURIComponent(productId) + '/';
        }
        return base.replace(/\/0\/$/, '/' + productId + '/');
    }

    function gmGetCookie(name) {
        var v = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(function (part) {
                var i = part.indexOf('=');
                var k = part.slice(0, i).trim();
                if (k === name) v = decodeURIComponent(part.slice(i + 1).trim());
            });
        }
        return v;
    }

    function qs(id) {
        return document.getElementById(id);
    }

    function closeModal() {
        var root = qs('gmPiModal');
        if (!root) return;
        root.hidden = true;
        root.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    function openModal() {
        var root = qs('gmPiModal');
        if (!root) return;
        root.hidden = false;
        root.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function showLoading() {
        var ld = qs('gmPiModalLoading');
        var inner = qs('gmPiModalInner');
        var err = qs('gmPiModalError');
        if (ld) ld.hidden = false;
        if (inner) inner.hidden = true;
        if (err) {
            err.hidden = true;
            err.textContent = '';
        }
    }

    function showError(msg) {
        var ld = qs('gmPiModalLoading');
        var inner = qs('gmPiModalInner');
        var err = qs('gmPiModalError');
        if (ld) ld.hidden = true;
        if (inner) inner.hidden = true;
        if (err) {
            err.hidden = false;
            err.textContent = msg || 'Une erreur est survenue.';
        }
    }

    function showContent() {
        var ld = qs('gmPiModalLoading');
        var inner = qs('gmPiModalInner');
        var err = qs('gmPiModalError');
        if (ld) ld.hidden = true;
        if (inner) inner.hidden = false;
        if (err) err.hidden = true;
    }

    window.openPurchaseIntentModal = function (productId) {
        var pid = parseInt(productId, 10);
        if (!pid || pid < 1) {
            if (typeof GMModal !== 'undefined' && GMModal.warning) {
                GMModal.warning('Erreur', 'Article invalide.');
            }
            return;
        }

        var url = gmPiUrl(pid);
        openModal();
        showLoading();

        fetch(url, {
            headers: {
                Accept: 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        })
            .then(function (r) {
                return r.text().then(function (text) {
                    var data = null;
                    try {
                        data = JSON.parse(text);
                    } catch (ignore) {}
                    if (r.status === 401) {
                        closeModal();
                        var login = document.body.getAttribute('data-gm-login-url');
                        if (login) {
                            window.location.href =
                                login +
                                (login.indexOf('?') >= 0 ? '&' : '?') +
                                'next=' +
                                encodeURIComponent(window.location.pathname + window.location.search);
                        }
                        return null;
                    }
                    if (r.status === 403) {
                        showError((data && data.error) || 'Action non autorisée.');
                        return null;
                    }
                    if (!data || !data.success || !data.product) {
                        showError((data && data.error) || 'Impossible de charger cette annonce.');
                        return null;
                    }
                    return data;
                });
            })
            .then(function (data) {
                if (!data || !data.product) return;
                var p = data.product;
                qs('gmPiModalImg').src = p.image_url || '';
                qs('gmPiModalImg').alt = p.name || '';
                qs('gmPiModalProductName').textContent = p.name || '';
                qs('gmPiModalSeller').textContent = p.seller_name || '';
                qs('gmPiModalPrice').textContent = p.price_label || '';
                var form = qs('gmPiModalForm');
                if (form) form.action = url;
                showContent();
            })
            .catch(function () {
                showError('Réponse invalide ou erreur réseau. Réessayez.');
            });
    };

    function init() {
        var root = qs('gmPiModal');
        if (!root) return;

        qs('gmPiModalBackdrop').addEventListener('click', closeModal);
        qs('gmPiModalClose').addEventListener('click', closeModal);

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && root && !root.hidden) closeModal();
        });

        var form = qs('gmPiModalForm');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                var btn = qs('gmPiModalSubmit');
                var action = form.action;
                if (!action) return;

                var fd = new FormData(form);
                var token = gmGetCookie('csrftoken');
                if (token) fd.set('csrfmiddlewaretoken', token);

                if (btn) {
                    btn.disabled = true;
                    btn.dataset._html = btn.innerHTML;
                    btn.innerHTML =
                        '<i class="fi-rs-spinner gm-pi-modal__spin" aria-hidden="true"></i> Création…';
                }

                fetch(action, {
                    method: 'POST',
                    body: fd,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        Accept: 'application/json',
                    },
                    credentials: 'same-origin',
                })
                    .then(function (r) {
                        return r.text().then(function (t) {
                            var j = null;
                            try {
                                j = JSON.parse(t);
                            } catch (ignore) {}
                            return { json: j, ok: r.ok };
                        });
                    })
                    .then(function (res) {
                        if (res.json && res.json.success && res.json.redirect) {
                            closeModal();
                            if (typeof GMModal !== 'undefined' && GMModal.show) {
                                GMModal.show({
                                    type: 'info',
                                    title: 'Demande envoyée !',
                                    message: 'Votre demande de négociation a été envoyée au vendeur.<br><br>'
                                        + '<strong>Prochaine étape :</strong> le vendeur doit confirmer que son article est toujours disponible. '
                                        + 'Vous recevrez un message dans la conversation dès que la négociation sera ouverte.',
                                    confirmText: 'Aller à la messagerie',
                                    onConfirm: function () {
                                        window.location.href = res.json.redirect;
                                    }
                                });
                            } else {
                                window.location.href = res.json.redirect;
                            }
                            return;
                        }
                        var err =
                            (res.json && res.json.error) ||
                            "Impossible de créer l'intention d'achat.";
                        if (typeof GMModal !== 'undefined' && GMModal.error) {
                            GMModal.error('Erreur', err);
                        } else {
                            alert(err);
                        }
                    })
                    .catch(function () {
                        if (typeof GMModal !== 'undefined' && GMModal.error) {
                            GMModal.error('Erreur', 'Erreur réseau. Réessayez.');
                        }
                    })
                    .finally(function () {
                        if (btn) {
                            btn.disabled = false;
                            if (btn.dataset._html) btn.innerHTML = btn.dataset._html;
                        }
                    });
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
