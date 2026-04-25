/**
 * negotiation.js — Gestion complète du flux d'achat C2C
 *
 * Couvre les étapes suivantes :
 *   1. Chargement de l'intention d'achat (loadPurchaseIntentForConversation)
 *   2. Historique et actions de négociation (displayNegotiationHistory)
 *   3. Acceptation du prix final / redirection vers le paiement
 *   4. Après paiement : confirmation mutuelle remise/réception (handover)
 *   5. Échange de codes de vérification A-CODE / V-CODE
 *   6. Finalisation de la transaction (commande complétée)
 *
 * Convention de logs dev :
 *   - Tous les logs utilisent le préfixe [GM·C2C] pour filtrer facilement
 *     dans la console du navigateur.
 *   - Les logs n'apparaissent que quand GM_DEV_LOGS est true (activé ci-dessous).
 */

/* ═══════════════════════════════════════════════════════════
   Configuration
   ═══════════════════════════════════════════════════════════ */

/** Active les logs dev dans la console (mettre à false en production) */
const GM_DEV_LOGS = true;

/** z-index au-dessus de #chatbotPopup (~10050) et des feuilles d'options (~10160) */
const GM_VERIFICATION_OVERLAY_Z = 20000;

/* ═══════════════════════════════════════════════════════════
   Utilitaires
   ═══════════════════════════════════════════════════════════ */

/** Log conditionnel — n'affiche rien si GM_DEV_LOGS est false */
function gmLog(/* ...args */) {
    if (!GM_DEV_LOGS) return;
    var args = Array.prototype.slice.call(arguments);
    args[0] = '%c[GM·C2C] ' + args[0];
    args.splice(1, 0, 'color:#3B82F6;font-weight:700');
    console.log.apply(console, args);
}
function gmWarn(/* ...args */) {
    if (!GM_DEV_LOGS) return;
    var args = Array.prototype.slice.call(arguments);
    args[0] = '[GM·C2C] ' + args[0];
    console.warn.apply(console, args);
}
function gmErr(/* ...args */) {
    var args = Array.prototype.slice.call(arguments);
    args[0] = '[GM·C2C] ' + args[0];
    console.error.apply(console, args);
}

/** Récupère un cookie par nom (CSRF principalement) */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').some(function (part) {
            var cookie = part.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                return true;
            }
        });
    }
    return cookieValue;
}

/** Échappe le HTML pour éviter les injections XSS */
function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/** Appelle GMModal de manière sûre (fallback vers alert si absent) */
function gmModalSafe(kind, title, message) {
    if (typeof GMModal !== 'undefined' && GMModal[kind]) {
        GMModal[kind](title, message);
    } else {
        window.alert(message || title || '');
    }
}

/* ═══════════════════════════════════════════════════════════
   État global de la négociation
   ═══════════════════════════════════════════════════════════ */

var currentPurchaseIntentId = null;
var negotiationPollInterval = null;

/* ═══════════════════════════════════════════════════════════
   1. Polling de négociation (rafraîchissement quasi temps réel)
   ═══════════════════════════════════════════════════════════ */

function startNegotiationPolling() {
    stopNegotiationPolling();
    negotiationPollInterval = setInterval(function () {
        if (currentPurchaseIntentId) {
            gmLog('Polling intent #%d', currentPurchaseIntentId);
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
        }
    }, 7000);
}

function stopNegotiationPolling() {
    if (negotiationPollInterval) {
        clearInterval(negotiationPollInterval);
        negotiationPollInterval = null;
    }
}

/* ═══════════════════════════════════════════════════════════
   2. Chargement de l'intention d'achat + état de la commande
   ═══════════════════════════════════════════════════════════ */

/**
 * Récupère l'intention d'achat côté serveur et met à jour l'interface :
 *   - section négociation (historique + formulaire)
 *   - section vérification (après paiement)
 *   - contrôles du chat (actif / bloqué)
 */
async function loadPurchaseIntentForConversation(productId, buyerId, sellerId, intentId) {
    gmLog('loadPurchaseIntent → intentId=%s productId=%s buyerId=%s sellerId=%s',
        intentId, productId, buyerId, sellerId);
    try {
        var url = '/c2c/purchase-intent/';
        if (intentId) {
            url += '?intent_id=' + intentId;
        } else {
            url += '?product_id=' + productId + '&buyer_id=' + buyerId + '&seller_id=' + sellerId;
        }

        var response = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        var data = await response.json();
        
        if (data.success && data.purchase_intent_id) {
            gmLog('Intent #%d chargée — status=%s orderStatus=%s',
                data.purchase_intent_id, data.status, data.order_status || '(aucune commande)');

            window.currentOrderId = data.order_id || null;
            window._intentBuyerId = data.buyer_id;
            window._intentSellerId = data.seller_id;

            var uid = Number(window.currentUserId || 0);
            var isBuyer = Number(data.buyer_id) === uid;
            var isSeller = Number(data.seller_id) === uid;

            // Détection des transitions pour les effets de gamification
            var prevStatus = window._gmLastIntentStatus || null;
            var prevOrderStatus = window._gmLastOrderStatus || null;
            var curStatus = data.status;
            var curOrderStatus = data.order_status || null;
            var isFirstLoad = prevStatus === null;

            if (!isFirstLoad) {
                _detectAndFireMilestone(prevStatus, curStatus, prevOrderStatus, curOrderStatus, data, isBuyer);
            }
            window._gmLastIntentStatus = curStatus;
            window._gmLastOrderStatus = curOrderStatus;

            // Vérification terminée → grand effet
            if (data.verification && data.verification.is_completed && !window._gmTransactionCompleteFired) {
                window._gmTransactionCompleteFired = true;
                _gmMilestone('completed', isBuyer ? '🎉 Transaction terminée ! Article bien reçu.' : '🎉 Transaction terminée ! Paiement libéré.');
            }
            
            toggleNegotiationSection(data.purchase_intent_id, data);
            displayNegotiationHistory(data.negotiations || [], data);
            displayVerificationSection(data.verification, data.order, isBuyer, isSeller);
            _showStepGuide(data, isBuyer, isSeller);
            
            if (typeof updateChatControls === 'function') {
                updateChatControls(data);
            }
        } else {
            gmLog('Aucune intention trouvée pour cette conversation');
            window.currentOrderId = null;
            toggleNegotiationSection(null);
            if (typeof updateChatControls === 'function') {
                updateChatControls(null);
            }
        }
    } catch (error) {
        gmErr('loadPurchaseIntent ERREUR:', error);
        toggleNegotiationSection(null);
        if (typeof updateChatControls === 'function') {
            updateChatControls(null);
        }
    }
}

/* ═══════════════════════════════════════════════════════════
   2b. Popups de guidage contextuel par étape
   ═══════════════════════════════════════════════════════════ */

/**
 * Affiche une popup de guidage une seule fois par session + étape
 * pour expliquer l'étape courante à l'utilisateur (acheteur ou vendeur).
 */
var _guidesShown = {};
function _showStepGuide(data, isBuyer, isSeller) {
    if (typeof GMModal === 'undefined' || !GMModal.show) return;
    var status = data.status;
    var orderStatus = data.order_status;
    var avail = data.availability_confirmed;
    var v = data.verification;
    var codesUnlocked = v && v.codes_unlocked === true;
    var verificationDone = v && v.is_completed;
    var key = 'gm_guide_' + data.purchase_intent_id + '_' + status + '_' + (orderStatus || '') + (codesUnlocked ? '_codes' : '');
    if (_guidesShown[key]) return;
    try { if (sessionStorage.getItem(key)) return; } catch (e) {}
    _guidesShown[key] = true;
    try { sessionStorage.setItem(key, '1'); } catch (e) {}

    var title = null, message = null;

    /* Étape 1 : En attente de disponibilité vendeur */
    if ((status === 'pending' || status === 'awaiting_availability') && !avail) {
        if (isBuyer) {
            title = '1/5 — Demande envoyée';
            message = 'Le vendeur doit confirmer la <strong>disponibilité</strong>. Vous serez notifié.';
        } else if (isSeller) {
            title = '1/5 — Nouvelle demande';
            message = 'Un acheteur veut votre article. <strong>Confirmez la disponibilité</strong> dans « Intentions d\'achat ».';
        }

    } else if (status === 'negotiating' && !data.final_price) {
        if (isBuyer) {
            title = '2/5 — Négociation';
            message = 'Article disponible ! <strong>Proposez votre prix</strong> ci-dessous.';
        } else if (isSeller) {
            title = '2/5 — Négociation';
            message = 'L\'acheteur peut proposer un prix. Acceptez, refusez ou contre-proposez.';
        }

    } else if (status === 'agreed' && (!orderStatus || orderStatus === 'pending_payment')) {
        if (isBuyer) {
            title = '3/5 — Paiement sécurisé';
            message = 'Accord trouvé ! Payez via le bouton vert. <strong>L\'argent est sécurisé</strong> jusqu\'à réception.';
        } else if (isSeller) {
            title = '3/5 — En attente de paiement';
            message = 'Prix accepté ! L\'acheteur doit payer. Vous serez notifié.';
        }

    } else if (orderStatus === 'paid' && !codesUnlocked && !verificationDone) {
        if (isBuyer) {
            title = '4/5 — Rendez-vous';
            message = 'Paiement reçu ! Convenez du <strong>lieu de remise</strong> dans le chat.';
        } else if (isSeller) {
            title = '4/5 — Rendez-vous';
            message = 'Paiement reçu ! Convenez du <strong>lieu de remise</strong> dans le chat.';
        }

    } else if (codesUnlocked && !verificationDone) {
        if (isBuyer) {
            title = '5/5 — Validation';
            message = 'Échangez vos <strong>codes</strong> avec le vendeur pour libérer les fonds.';
        } else if (isSeller) {
            title = '5/5 — Validation';
            message = 'Échangez vos <strong>codes</strong> avec l\'acheteur. Les fonds vous seront versés.';
        }
    }

    if (title && message) {
        setTimeout(function () {
            GMModal.show({ type: 'info', title: title, message: message, confirmText: 'Compris !' });
        }, 600);
    }
}

/* ═══════════════════════════════════════════════════════════
   3. Soumission d'une proposition de prix
   ═══════════════════════════════════════════════════════════ */

async function submitNegotiation(event) {
    event.preventDefault();

    if (!currentPurchaseIntentId) {
        GMModal.warning('Attention', "Aucune intention d'achat active");
        return;
    }

    var priceInput = document.getElementById('negotiationPrice');
    var proposedPrice = parseFloat(priceInput.value);
    if (!proposedPrice || proposedPrice <= 0) {
        GMModal.warning('Prix invalide', 'Veuillez entrer un prix valide');
        return;
    }

    gmLog('submitNegotiation → intent=#%d prix=%d FCFA', currentPurchaseIntentId, proposedPrice);

    try {
        var response = await fetch('/c2c/negotiation/' + currentPurchaseIntentId + '/make-offer/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                proposed_price: proposedPrice,
                message: 'Je propose ' + proposedPrice.toLocaleString() + ' FCFA pour cet article.'
            })
        });
        var data = await response.json();

        if (data.success) {
            gmLog('Proposition envoyée avec succès');
            priceInput.value = '';
            _reloadIntentAndConversation();
        } else {
            gmWarn('Proposition refusée par le serveur: %s', data.error);
            GMModal.error('Erreur', data.error || "Erreur lors de l'envoi de la proposition");
            loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
        }
    } catch (error) {
        gmErr('submitNegotiation ERREUR:', error);
        GMModal.error('Erreur', "Erreur lors de l'envoi de la proposition");
    }
}

/* ═══════════════════════════════════════════════════════════
   4. Historique des négociations + bouton « Accepter le prix »
   ═══════════════════════════════════════════════════════════ */

function displayNegotiationHistory(negotiations, intentData) {
    var historyContainer = document.getElementById('negotiationHistory');
    if (!historyContainer) return;

    var acceptBtn = document.getElementById('acceptFinalPriceBtn');

    // Bannière offres concurrentes (vendeur uniquement, article encore en négociation)
    var competingBuyers = (intentData && intentData.competing_buyers) || 0;
    var uid = window.currentUserId || 0;
    var isSeller = intentData && intentData.seller_id === uid;
    var activeStatuses = ['pending', 'awaiting_availability', 'negotiating'];
    var isActive = intentData && activeStatuses.indexOf(intentData.status) !== -1;
    _updateCompetingBuyersBanner(competingBuyers, isSeller && isActive);
    
    if (negotiations.length === 0) {
        historyContainer.innerHTML = '<p style="margin:0;font-size:12px;color:#9CA3AF;font-style:italic;">Aucune proposition pour le moment</p>';
        if (acceptBtn) acceptBtn.style.display = 'none';
        return;
    }
    var orderStatus = intentData.order_status;
    var isPaid = orderStatus && ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'].indexOf(orderStatus) !== -1;
    var isAgreedNow = intentData.status === 'agreed';

    var html = '';
    negotiations.forEach(function (neg, idx) {
        var isProposer = neg.proposer_id === uid;
        var isPending = neg.status === 'pending';
        var isLast = idx === negotiations.length - 1;
        // Action possible : offre encore en attente, dernière de la liste, vous n'en êtes pas l'auteur,
        // et la négociation n'est pas verrouillée (prix accepté ou commande payée)
        var canAct = isPending && isLast && !isProposer && !isPaid && !isAgreedNow;

        // Countdown timer pour offre en attente avec expires_at
        var countdownHtml = '';
        if (isPending && neg.expires_at_iso) {
            var expiresAt = new Date(neg.expires_at_iso);
            var msLeft = expiresAt - Date.now();
            if (msLeft > 0) {
                var countdownId = 'nego-countdown-' + neg.id;
                countdownHtml = '<span id="' + countdownId + '" class="gm-nego-countdown" data-expires="' + neg.expires_at_iso + '">'
                    + _formatCountdown(msLeft) + '</span>';
            } else {
                countdownHtml = '<span style="font-size:11px;color:#EF4444;font-weight:600;">Offre expirée</span>';
            }
        }

        html += '<div style="background:' + (isProposer ? '#E0F2FE' : 'white') + ';border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid #E5E7EB;">'
            + '<div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:4px;">'
            + '<div><strong style="font-size:12px;color:#1F2937;">' + escapeHtml(neg.proposer_name) + '</strong>'
            + '<span style="font-size:11px;color:#6B7280;margin-left:8px;">' + neg.created_at + '</span></div>'
            + '<span style="font-size:14px;font-weight:700;color:var(--color-orange);">' + parseFloat(neg.proposed_price).toLocaleString() + ' FCFA</span></div>'
            + (neg.message ? '<p style="margin:4px 0 0;font-size:12px;color:#6B7280;">' + escapeHtml(neg.message) + '</p>' : '')
            + '<div style="margin-top:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">'
            + (neg.status === 'accepted' ? '<span style="font-size:11px;color:#10B981;font-weight:700;">✓ Accepté</span>' : '')
            + (neg.status === 'rejected' ? '<span style="font-size:11px;color:#EF4444;font-weight:700;">✗ Refusé</span>' : '')
            + (canAct ? '<button onclick="acceptNegotiation(' + neg.id + ')" style="padding:6px 10px;background:#10B981;color:white;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;">Accepter</button>'
                + '<button onclick="rejectNegotiation(' + neg.id + ')" style="padding:6px 10px;background:#FEE2E2;color:#EF4444;border:none;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;">Refuser</button>' : '')
            + (isPending && !canAct ? '<span style="font-size:11px;color:#6B7280;">En attente de réponse...</span>' : '')
            + countdownHtml
            + '</div></div>';
    });
    
    historyContainer.innerHTML = html;
    
    // Démarrer les timers de countdown
    _startNegotiationCountdowns();

    /* --- Bouton « Accepter le prix final » (acheteur uniquement) --- */
    if (!acceptBtn || !intentData) return;

    var isBuyer = intentData.buyer_id === uid;

    // Post-paiement : résumé lecture seule — formulaire masqué, historique visible
    if (isPaid) {
        acceptBtn.style.display = 'none';
        var negoForm = document.getElementById('negotiationForm');
        if (negoForm) negoForm.style.display = 'none';
        // Mise à jour du header de section en mode résumé
        var negoSection = document.getElementById('negotiationSection');
        if (negoSection) {
            var h5 = negoSection.querySelector('h5');
            var sub = negoSection.querySelector('p.gm-s-3e99bc');
            if (h5) h5.innerHTML = '<i class="fi-rs-list" style="color:#6B7280;margin-right:6px;"></i>Résumé de la négociation';
            if (sub) { sub.textContent = 'Prix final : ' + (intentData && intentData.negotiated_price ? parseFloat(intentData.negotiated_price).toLocaleString() + ' FCFA' : '—'); sub.style.color = '#059669'; sub.style.fontWeight = '600'; }
        }
        return;
    }
    
    if (!isBuyer) { acceptBtn.style.display = 'none'; return; }

    // Accord trouvé, commande créée mais non encore payée → bouton paiement
    if (intentData.status === 'agreed' && intentData.order_id) {
        gmLog('Prix accepté — affichage bouton paiement (order #%d)', intentData.order_id);
        acceptBtn.style.display = 'block';
        acceptBtn.innerHTML = '<i class="fi-rs-credit-card"></i> Procéder au paiement';
        acceptBtn.onclick = function () {
            window.location.href = '/c2c/order/' + intentData.order_id + '/payment/';
        };
        return;
    }
    
    if (intentData.can_accept_final_price && intentData.negotiated_price) {
        acceptBtn.style.display = 'block';
        acceptBtn.innerHTML = '<i class="fi-rs-hand-holding-usd"></i> Accepter ce prix';
        acceptBtn.onclick = function () { acceptFinalPrice(intentData.purchase_intent_id, intentData.negotiated_price); };
        return;
    }
    
    acceptBtn.style.display = 'none';
    lockInputsIfAgreed(intentData);
    updateNegotiationOfferAvailability(intentData);
}

/* ═══════════════════════════════════════════════════════════
   5. Contrôle formulaire « Proposer un prix »
   ═══════════════════════════════════════════════════════════ */

/** Active/désactive le formulaire selon les règles de tour renvoyées par le serveur */
function updateNegotiationOfferAvailability(intentData) {
    var form = document.getElementById('negotiationForm');
    var priceInput = document.getElementById('negotiationPrice');
    if (!form || !priceInput || !intentData) return;

    var isAgreed = intentData.status === 'agreed';
    var isPaid = intentData.order_status &&
        ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'].indexOf(intentData.order_status) !== -1;
    if (isAgreed || isPaid) return;

    var submitBtn = form.querySelector('button[type="submit"]');
    var formHint = form.querySelector('.gm-nego-form-hint');
    if (intentData.can_make_offer === false) {
        priceInput.disabled = true;
        if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '0.5'; submitBtn.style.cursor = 'not-allowed'; }
        if (formHint) {
            formHint.textContent = intentData.offer_form_block_message || 'Vous ne pouvez pas proposer de prix pour le moment.';
            formHint.style.display = 'block';
        }
    } else {
        priceInput.disabled = false;
        if (submitBtn) { submitBtn.disabled = false; submitBtn.style.opacity = '1'; submitBtn.style.cursor = 'pointer'; }
        if (formHint) formHint.style.display = 'none';
    }
}

/* ═══════════════════════════════════════════════════════════
   6. Verrouillage des contrôles selon l'état de la commande
   ═══════════════════════════════════════════════════════════ */

/**
 * Gère l'affichage de la section négociation (titre, formulaire, prix)
 * selon le statut courant. Le chat input/helper est géré par updateChatControls.
 */
function lockInputsIfAgreed(intentData) {
    var negotiationForm = document.getElementById('negotiationForm');
    var negotiationPrice = document.getElementById('negotiationPrice');
    var negotiationSection = document.getElementById('negotiationSection');

    var status = intentData ? intentData.status : null;
    var orderStatus = intentData ? intentData.order_status : null;
    var availOk = intentData ? intentData.availability_confirmed : false;
    var isAwaitingAvail = (status === 'pending' || status === 'awaiting_availability') && !availOk;
    var isNegotiating = status === 'negotiating';
    var isAgreed = status === 'agreed';
    var isPaid = orderStatus && ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'].indexOf(orderStatus) !== -1;
    var isCompleted = orderStatus === 'completed';
    var uid = window.currentUserId || 0;
    var isBuyer = intentData ? intentData.buyer_id === uid : false;

    /* Titre de la section */
    if (negotiationSection && intentData) {
        var h5 = negotiationSection.querySelector('h5');
        var sub = negotiationSection.querySelector('p.gm-s-3e99bc');
        if (isAwaitingAvail) {
            if (h5) h5.innerHTML = '<i class="fi-rs-time-past gm-s-a77b0c"></i> En attente de disponibilité';
            if (sub) sub.textContent = isBuyer
                ? 'Le vendeur doit confirmer la disponibilité de l\'article.'
                : 'Confirmez la disponibilité dans « Intentions d\'achat » ci-dessus.';
        } else if (isNegotiating && !isAgreed) {
            if (h5) h5.innerHTML = '<i class="fi-rs-money gm-s-a77b0c"></i> Négocier le prix';
            if (sub) sub.textContent = 'Proposez ou acceptez un prix pour cet article.';
        } else if (isAgreed && !isPaid) {
            if (h5) h5.innerHTML = '<i class="fi-rs-check gm-s-a77b0c" style="color:#10B981"></i> Prix accepté';
            if (sub) sub.textContent = isBuyer ? 'Procédez au paiement.' : 'En attente du paiement.';
        } else if (isPaid && !isCompleted) {
            if (h5) h5.innerHTML = '<i class="fi-rs-time-past"></i> Historique de négociation';
            if (sub) sub.textContent = 'Vos propositions de prix restent visibles.';
        } else if (isCompleted) {
            if (h5) h5.innerHTML = '<i class="fi-rs-check" style="color:#059669"></i> Transaction terminée';
            if (sub) sub.textContent = '';
        }
    }

    /* Formulaire de négociation : visibilité */
    if (isAwaitingAvail) {
        gmLog('Négo: en attente dispo → formulaire masqué');
        if (negotiationForm) negotiationForm.style.display = 'none';
        if (negotiationPrice) negotiationPrice.disabled = true;
    } else if (isAgreed || isPaid) {
        gmLog('Négo: prix fixé / payé → formulaire masqué');
        if (negotiationPrice) { negotiationPrice.disabled = true; negotiationPrice.placeholder = 'Prix fixé'; }
        if (negotiationForm) {
            var sb = negotiationForm.querySelector('button[type="submit"]');
            if (sb) { sb.disabled = true; sb.style.opacity = '0.5'; sb.style.cursor = 'not-allowed'; }
            // Masquer entièrement le formulaire dès qu'un prix est accepté
            negotiationForm.style.display = 'none';
        }
        // Post-paiement : masquer seulement le formulaire (la section reste visible en résumé)
        if (isPaid && negotiationSection) {
            negotiationSection.setAttribute('data-gm-resume-mode', '1');
        }
    }
}

/* ═══════════════════════════════════════════════════════════
   7. Accepter / Refuser une offre de négociation
   ═══════════════════════════════════════════════════════════ */

async function acceptNegotiation(negotiationId) {
    gmLog('acceptNegotiation → negotiation #%d', negotiationId);
    try {
        var resp = await fetch('/c2c/negotiation/' + negotiationId + '/accept/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
        });
        var data = await resp.json();
        if (data.success) {
            gmLog('Offre #%d acceptée', negotiationId);
            _gmMilestone('offer_accepted', '⭐ Offre acceptée !');
            _reloadIntentAndConversation();
        } else {
            GMModal.error('Erreur', data.error || "Erreur lors de l'acceptation de l'offre");
        }
    } catch (e) { gmErr('acceptNegotiation ERREUR:', e); GMModal.error('Erreur', "Erreur lors de l'acceptation de l'offre"); }
}

async function rejectNegotiation(negotiationId) {
    gmLog('rejectNegotiation → negotiation #%d', negotiationId);
    try {
        var resp = await fetch('/c2c/negotiation/' + negotiationId + '/reject/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
        });
        var data = await resp.json();
        if (data.success) {
            gmLog('Offre #%d refusée', negotiationId);
            _reloadIntentAndConversation();
            } else {
            GMModal.error('Erreur', data.error || "Erreur lors du refus de l'offre");
        }
    } catch (e) { gmErr('rejectNegotiation ERREUR:', e); GMModal.error('Erreur', "Erreur lors du refus de l'offre"); }
}

/* ═══════════════════════════════════════════════════════════
   8. Accepter le prix final → créer la commande C2C
   ═══════════════════════════════════════════════════════════ */

function acceptFinalPrice(intentId, finalPrice) {
    gmLog('acceptFinalPrice → intent #%d prix=%s FCFA', intentId, finalPrice);
    GMModal.show({
        type: 'confirm',
        title: 'Accepter ce prix',
        message: 'Êtes-vous sûr d\'accepter ce prix de <strong>' + parseFloat(finalPrice).toLocaleString() + ' FCFA</strong> ?<br><br>Un bouton de paiement apparaîtra après l\'acceptation.',
        showCancel: true,
        confirmText: 'Accepter',
        cancelText: 'Annuler',
        onConfirm: async function () {
            try {
                var response = await fetch('/c2c/purchase-intent/' + intentId + '/accept-price/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ final_price: finalPrice })
                });
                var data = await response.json();
                if (data.success) {
                    gmLog('Prix final accepté — order #%d total=%s', data.order_id, data.buyer_total);
                    GMModal.show({
                        type: 'success',
                        title: 'Prix accepté !',
                        message: data.message || 'Prix accepté ! Cliquez sur le bouton vert pour procéder au paiement.',
                        confirmText: 'OK',
                        onConfirm: function () {
                                loadPurchaseIntentForConversation(null, null, null, intentId);
                        }
                    });
                } else {
                    gmWarn('acceptFinalPrice refusé: %s', data.error);
                    GMModal.error('Erreur', data.error || "Erreur lors de l'acceptation du prix final");
                }
            } catch (error) {
                gmErr('acceptFinalPrice ERREUR:', error);
                GMModal.error('Erreur', "Erreur lors de l'acceptation du prix final");
            }
        }
    });
}

/* ═══════════════════════════════════════════════════════════
   9. Section de vérification (après paiement)
   ═══════════════════════════════════════════════════════════ */

/** Style commun des boutons handover dans le fil du chat */
var GM_HANDOVER_BTN_BUYER_STYLE =
    'width:100%;padding:14px 16px;margin-top:8px;background:linear-gradient(135deg,#059669 0%,#047857 100%);'
    + 'color:white;border:none;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;'
    + 'display:flex;align-items:center;justify-content:center;gap:10px;'
    + 'box-shadow:0 4px 12px rgba(5,150,105,0.35);';
var GM_HANDOVER_BTN_SELLER_STYLE =
    'width:100%;padding:14px 16px;margin-top:8px;background:linear-gradient(135deg,var(--color-orange,#ff7b2c) 0%,#ea580c 100%);'
    + 'color:white;border:none;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;'
    + 'display:flex;align-items:center;justify-content:center;gap:10px;'
    + 'box-shadow:0 4px 12px rgba(255,123,44,0.4);';
var GM_HANDOVER_WAIT_STYLE =
    'margin-top:10px;padding:12px 14px;border-radius:10px;background:#F3F4F6;border:1px solid #E5E7EB;'
    + 'font-size:13px;color:#4B5563;line-height:1.45;';

/**
 * POST /c2c/order/:id/confirm-handover/ — utilisé par le chat et l’overlay legacy.
 */
async function _postHandoverConfirm() {
    if (!window.currentOrderId) {
        throw new Error('Commande introuvable');
    }
    var resp = await fetch('/c2c/order/' + window.currentOrderId + '/confirm-handover/', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
        },
        body: '{}'
    });
    var data = await resp.json();
    if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Enregistrement impossible');
    }
    return data;
}

/**
 * Popup d’avertissement obligatoire avant d’enregistrer la remise / la réception.
 * @param {'buyer'|'seller'} role
 */
function promptHandoverWarningAndSubmit(role) {
    if (!window.currentOrderId) {
        GMModal.error('Erreur', 'Commande introuvable');
        return;
    }
    var isBuyer = role === 'buyer';
    var title = isBuyer ? 'Article récupéré ?' : 'Article remis ?';
    var message = isBuyer
        ? 'Confirmez <strong>uniquement</strong> si vous avez l’article en main. Les codes seront débloqués.'
        : 'Confirmez <strong>uniquement</strong> si la remise a eu lieu. Les codes seront débloqués.';

    GMModal.show({
        type: 'warning',
        title: title,
        message: message,
        showCancel: true,
        confirmText: 'Oui, je confirme',
        cancelText: 'Annuler',
        onConfirm: function () {
            _runHandoverAfterUserConfirms(role);
        }
    });
}

/**
 * Envoie la confirmation serveur après la popup, recharge l’intent, guide l’utilisateur.
 */
async function _runHandoverAfterUserConfirms(role) {
    gmLog('Handover (chat) — envoi API role=%s', role);
    try {
        var data = await _postHandoverConfirm();
        gmLog('Handover OK — codes_unlocked=%s', data.codes_unlocked);
        await loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
        if (data.codes_unlocked) {
            GMModal.success(
                'Étape suivante',
                'Confirmations enregistrées. Utilisez le bouton '
                + 'de validation pour échanger les codes.'
            );
        } else {
            GMModal.success(
                'Confirmation enregistrée',
                'En attente de la confirmation de l’autre partie.'
            );
        }
    } catch (err) {
        gmErr('confirm-handover ERREUR:', err);
        GMModal.error('Erreur', err.message || 'Une erreur est survenue');
    }
}

/**
 * Section vérification après paiement :
 *   1) Tant que remise/réception non confirmées des deux côtés : boutons « Article récupéré » / « Article remis »
 *      + popup d’avertissement obligatoire (pas de bouton codes avant déverrouillage).
 *   2) Ensuite seulement : bouton « Valider la transaction (codes de vérification) ».
 */
function displayVerificationSection(verificationData, orderData, isBuyer, isSeller) {
    var section = document.getElementById('verificationSection');
    if (!section) return;
    
    if (!verificationData || !orderData) {
        section.style.display = 'none';
        return;
    }
    
    var paidStatuses = ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'];
    if (paidStatuses.indexOf(orderData.status) === -1) {
        section.style.display = 'none';
        return;
    }
    
    window._verificationData = verificationData;
    window._orderData = orderData;
    window._isBuyer = isBuyer;
    window._isSeller = isSeller;
    
    section.style.display = 'block';
    
    if (verificationData.is_completed) {
        gmLog('Vérification terminée — transaction complète');
        section.innerHTML =
            '<div style="background:#D1FAE5;padding:16px;border-radius:12px;text-align:center;border:1px solid #10B981;">'
            + '<i class="fi-rs-check-circle" style="font-size:32px;color:#059669;"></i>'
            + '<p style="margin:12px 0 0;font-size:16px;color:#065F46;font-weight:700;">🎉 Transaction terminée avec succès !</p>'
            + '</div>';
        return;
    }
    
    var buyerDone = verificationData.buyer_handover_confirmed === true;
    var sellerDone = verificationData.seller_handover_confirmed === true;
    var codesUnlocked = verificationData.codes_unlocked === true;

    /* --- Phase 1 : confirmations remise / réception (obligatoires avant les codes) --- */
    if (!codesUnlocked) {
        var intro =
            '<p style="margin:0 0 10px;font-size:12px;color:#6B7280;line-height:1.5;">'
            + '<strong>Étape obligatoire :</strong> l’acheteur confirme la récupération de l’article, '
            + 'le vendeur confirme la remise. Une fenêtre d’avertissement s’affiche avant chaque validation. '
            + 'Les codes de vérification ne sont accessibles qu’après les deux confirmations.</p>';
        var chunks = [intro];

        if (isBuyer) {
            if (!buyerDone) {
                chunks.push(
                    '<button type="button" data-gm-handover-chat data-role="buyer" style="' + GM_HANDOVER_BTN_BUYER_STYLE + '">'
                    + '<i class="fi-rs-check" style="font-size:18px;"></i>Article récupéré</button>'
                );
            } else if (!sellerDone) {
                chunks.push(
                    '<div style="' + GM_HANDOVER_WAIT_STYLE + '">'
                    + '<strong>Vous avez confirmé la récupération.</strong> En attente que le vendeur confirme '
                    + 'la remise (« Article remis »).</div>'
                );
            }
        }
        if (isSeller) {
            if (!sellerDone) {
                chunks.push(
                    '<button type="button" data-gm-handover-chat data-role="seller" style="' + GM_HANDOVER_BTN_SELLER_STYLE + '">'
                    + '<i class="fi-rs-box" style="font-size:18px;"></i>Article remis</button>'
                );
            } else if (!buyerDone) {
                chunks.push(
                    '<div style="' + GM_HANDOVER_WAIT_STYLE + '">'
                    + '<strong>Vous avez confirmé la remise.</strong> En attente que l’acheteur confirme '
                    + 'la récupération (« Article récupéré »).</div>'
                );
            }
        }

        section.innerHTML = chunks.join('');
        section.querySelectorAll('[data-gm-handover-chat]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var r = btn.getAttribute('data-role');
                gmLog('Clic bouton handover chat role=%s', r);
                promptHandoverWarningAndSubmit(r);
            });
        });
        return;
    }

    /* --- Phase 2 : codes déverrouillés — bouton validation transaction --- */
    section.innerHTML =
        '<p style="margin:0 0 10px;font-size:12px;color:#6B7280;line-height:1.45;">'
        + 'Remise et réception sont confirmées. Ouvrez le formulaire ci-dessous pour voir vos codes et finaliser.</p>'
        + '<button type="button" data-gm-open-verification '
        + 'style="width:100%;padding:14px 16px;background:linear-gradient(135deg,#3B82F6 0%,#2563EB 100%);'
        + 'color:white;border:none;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;'
        + 'display:flex;align-items:center;justify-content:center;gap:10px;'
        + 'box-shadow:0 4px 12px rgba(59,130,246,0.4);">'
        + '<i class="fi-rs-shield-check" style="font-size:18px;"></i>'
        + 'Valider la transaction (codes de vérification)</button>';

    var openBtn = section.querySelector('[data-gm-open-verification]');
    if (openBtn) {
        openBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            gmLog('Clic « Valider la transaction » — modal codes');
            openVerificationModal();
        });
    }
}

/* ═══════════════════════════════════════════════════════════
   10. Modal de vérification — point d'entrée
   ═══════════════════════════════════════════════════════════ */

/**
 * Ouvre le modal d’échange de codes (appelé uniquement quand les codes sont déverrouillés
 * et que le bouton bleu est visible dans le chat).
 */
function openVerificationModal() {
    var v = window._verificationData;
    var uid = Number(window.currentUserId || 0);
    var isBuyer = window._isBuyer === true;
    var isSeller = window._isSeller === true;

    if (window._intentBuyerId != null && window._intentSellerId != null) {
        isBuyer = Number(window._intentBuyerId) === uid;
        isSeller = Number(window._intentSellerId) === uid;
    }

    if (!v) { gmModalSafe('error', 'Erreur', 'Données de vérification non disponibles'); return; }
    if (v.is_completed) { gmModalSafe('info', 'Transaction', 'Cette transaction est déjà finalisée.'); return; }

    gmLog('openVerificationModal — codesUnlocked=%s', v.codes_unlocked);

    /* Le flux handover se fait dans le chat (« Article récupéré » / « Article remis ») */
    if (v.codes_unlocked === false) {
        if (typeof GMModal !== 'undefined' && GMModal.show) {
            GMModal.show({
                type: 'info',
                title: 'Étape requise',
                message: 'Confirmez d’abord la récupération ou la remise de l’article avec les boutons verts/orange dans cette conversation. Les codes seront disponibles ensuite.',
                confirmText: 'OK'
            });
        } else {
            gmModalSafe('info', 'Étape requise',
                'Utilisez les boutons « Article récupéré » ou « Article remis » dans le chat avant les codes.');
        }
        return;
    }
    
    openCodesExchangeModal();
}

/* Exposition globale pour le bouton dans verificationSection */
if (typeof window !== 'undefined') {
    window.openVerificationModal = openVerificationModal;
}

/* ═══════════════════════════════════════════════════════════
   11. Overlays de vérification — utilitaires communs
   ═══════════════════════════════════════════════════════════ */

/** Crée un overlay de vérification avec le bon z-index */
function _createVerifOverlay() {
    var overlay = document.createElement('div');
    overlay.className = 'gm-peer-verif-overlay';
    overlay.style.cssText =
        'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);'
        + 'display:flex;align-items:center;justify-content:center;z-index:'
        + GM_VERIFICATION_OVERLAY_Z + ';padding:20px;';
    return overlay;
}

/** Lie les boutons [data-gm-verif-dismiss] et le clic sur le fond pour fermer */
function _bindVerificationOverlayClose(overlay, closeModal) {
    overlay.querySelectorAll('[data-gm-verif-dismiss]').forEach(function (el) {
        el.addEventListener('click', closeModal);
    });
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeModal();
    });
}

/* ═══════════════════════════════════════════════════════════
   12. Modal « En attente de l'autre partie »
   ═══════════════════════════════════════════════════════════ */

function openHandoverWaitingModal(message) {
    gmLog('openHandoverWaitingModal: %s', message);
    var overlay = _createVerifOverlay();
    overlay.innerHTML =
        '<div style="background:white;border-radius:16px;max-width:420px;width:100%;box-shadow:0 20px 40px rgba(0,0,0,0.3);">'
        + '<div style="padding:20px;border-bottom:1px solid #E5E7EB;display:flex;align-items:center;justify-content:space-between;">'
        + '<h3 style="margin:0;font-size:18px;font-weight:700;color:#1F2937;">Confirmation</h3>'
        + '<button type="button" data-gm-verif-dismiss style="background:none;border:none;font-size:24px;color:#9CA3AF;cursor:pointer;padding:4px;">&times;</button>'
        + '</div>'
        + '<div style="padding:20px;"><p style="margin:0;font-size:14px;color:#374151;line-height:1.5;">' + escapeHtml(message) + '</p></div>'
        + '<div style="padding:16px 20px;border-top:1px solid #E5E7EB;display:flex;justify-content:flex-end;">'
        + '<button type="button" data-gm-verif-dismiss style="padding:12px 24px;background:#3B82F6;color:white;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;">Fermer</button>'
        + '</div></div>';
    document.body.appendChild(overlay);
    _bindVerificationOverlayClose(overlay, function () { overlay.remove(); });
}

/* ═══════════════════════════════════════════════════════════
   13. Modal « Confirmer remise / réception » (handover)
   ═══════════════════════════════════════════════════════════ */

function openHandoverConfirmModal(role) {
    gmLog('openHandoverConfirmModal → role=%s', role);
    var overlay = _createVerifOverlay();
    var title = role === 'buyer' ? "Réception de l\u2019article" : "Remise de l\u2019article";
    var question = role === 'buyer'
        ? "Confirmez-vous avoir <strong>reçu l\u2019article</strong> ?"
        : "Confirmez-vous avoir <strong>remis l\u2019article</strong> à l\u2019acheteur ?";

    overlay.innerHTML =
        '<div style="background:white;border-radius:16px;max-width:420px;width:100%;box-shadow:0 20px 40px rgba(0,0,0,0.3);">'
        + '<div style="padding:20px;border-bottom:1px solid #E5E7EB;display:flex;align-items:center;justify-content:space-between;">'
        + '<h3 style="margin:0;font-size:18px;font-weight:700;color:#1F2937;">' + title + '</h3>'
        + '<button type="button" data-gm-verif-dismiss style="background:none;border:none;font-size:24px;color:#9CA3AF;cursor:pointer;padding:4px;">&times;</button></div>'
        + '<div style="padding:20px;">'
        + '<p style="margin:0;font-size:14px;color:#374151;line-height:1.5;">' + question + '</p>'
        + '<p style="margin:12px 0 0;font-size:12px;color:#6B7280;">Ensuite seulement, vos codes de vérification seront affichés pour l\u2019échange.</p></div>'
        + '<div style="padding:16px 20px;border-top:1px solid #E5E7EB;display:flex;gap:12px;justify-content:flex-end;">'
        + '<button type="button" data-gm-verif-dismiss style="padding:12px 24px;background:#F3F4F6;color:#374151;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;">Annuler</button>'
        + '<button type="button" data-gm-handover-confirm style="padding:12px 24px;background:linear-gradient(135deg,#10B981 0%,#059669 100%);color:white;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;">Oui, je confirme</button>'
        + '</div></div>';

    document.body.appendChild(overlay);
    var closeModal = function () { overlay.remove(); };
    _bindVerificationOverlayClose(overlay, closeModal);

    var confirmBtn = overlay.querySelector('[data-gm-handover-confirm]');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            gmLog('confirm-handover (overlay) → role=%s', role);
            confirmBtn.disabled = true;
            try {
                var data = await _postHandoverConfirm();
                gmLog('Handover confirmé — codesUnlocked=%s', data.codes_unlocked);
                closeModal();
                await loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                if (data.codes_unlocked) {
                    GMModal.success(
                        'Étape suivante',
                        'Utilisez le bouton « Valider la transaction (codes de vérification) » dans le chat.'
                    );
        } else {
                    GMModal.success(
                        'Confirmation enregistrée',
                        'L’autre partie doit encore confirmer de son côté.'
                    );
                }
            } catch (err) {
                gmErr('confirm-handover ERREUR:', err);
                GMModal.error('Erreur', err.message || 'Une erreur est survenue');
                confirmBtn.disabled = false;
            }
        });
    }
}

/* ═══════════════════════════════════════════════════════════
   14. Modal « Échange de codes A-CODE / V-CODE »
   ═══════════════════════════════════════════════════════════ */

function openCodesExchangeModal() {
    var v = window._verificationData;
    var isBuyer = window._isBuyer;
    var isSeller = window._isSeller;
    if (!v) { GMModal.error('Erreur', 'Données de vérification non disponibles'); return; }

    gmLog('openCodesExchangeModal — isBuyer=%s isSeller=%s buyerVerified=%s sellerVerified=%s',
        isBuyer, isSeller, v.buyer_code_verified, v.seller_code_verified);

    var showValidateBtn = (isBuyer && !v.buyer_code_verified) || (isSeller && !v.seller_code_verified);
    var overlay = _createVerifOverlay();

    /* Construire le contenu du modal selon le rôle */
    var codeDisplayHtml = '';
    var inputHtml = '';

    if (isBuyer) {
        codeDisplayHtml = _buildCodeDisplayBlock('A-CODE', 'à donner au vendeur', v.buyer_code,
            'Donnez ce code au vendeur quand vous recevez l\u2019article.');
        inputHtml = v.buyer_code_verified
            ? _buildVerifiedBadge()
            : _buildCodeInputBlock('V-CODE du vendeur', 'V-CODE',
                'Le vendeur vous donnera ce code après vous avoir remis l\u2019article.');
    }
    if (isSeller) {
        codeDisplayHtml = _buildCodeDisplayBlock('V-CODE', 'à donner à l\u2019acheteur', v.seller_code,
            'Donnez ce code à l\u2019acheteur après lui avoir remis l\u2019article.');
        inputHtml = v.seller_code_verified
            ? _buildVerifiedBadge()
            : _buildCodeInputBlock('A-CODE de l\u2019acheteur', 'A-CODE',
                'L\u2019acheteur vous donnera ce code quand il recevra l\u2019article.');
    }

    overlay.innerHTML =
        '<div style="background:white;border-radius:16px;max-width:420px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 40px rgba(0,0,0,0.3);">'
        + '<div style="padding:20px;border-bottom:1px solid #E5E7EB;display:flex;align-items:center;justify-content:space-between;">'
        + '<h3 style="margin:0;font-size:18px;font-weight:700;color:#1F2937;display:flex;align-items:center;gap:10px;">'
        + '<i class="fi-rs-shield-check" style="color:#3B82F6;"></i> Vérification de la transaction</h3>'
        + '<button type="button" data-gm-verif-dismiss style="background:none;border:none;font-size:24px;color:#9CA3AF;cursor:pointer;padding:4px;">&times;</button></div>'
        + '<div style="padding:20px;">' + codeDisplayHtml + inputHtml + '</div>'
        + '<div style="padding:16px 20px;border-top:1px solid #E5E7EB;display:flex;gap:12px;justify-content:flex-end;">'
        + '<button type="button" data-gm-verif-dismiss style="padding:12px 24px;background:#F3F4F6;color:#374151;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;">Annuler</button>'
        + (showValidateBtn
            ? '<button type="button" data-gm-verif-confirm style="padding:12px 24px;background:linear-gradient(135deg,#10B981 0%,#059669 100%);color:white;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:8px;">'
              + '<i class="fi-rs-check"></i> Valider le code</button>'
            : '')
        + '</div></div>';
    
    document.body.appendChild(overlay);
    
    /* Focus sur le champ de saisie */
    setTimeout(function () {
        var input = overlay.querySelector('#gmPeerVerificationCodeInput');
        if (input) input.focus();
    }, 100);
    
    var closeModal = function () { overlay.remove(); };
    _bindVerificationOverlayClose(overlay, closeModal);

    /* Bouton « Valider le code » */
    var confirmBtn = overlay.querySelector('[data-gm-verif-confirm]');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function () {
            var input = overlay.querySelector('#gmPeerVerificationCodeInput');
            var code = input ? input.value.trim().toUpperCase() : '';
            if (!code || code.length !== 6) {
                GMModal.warning('Code invalide', 'Le code doit contenir 6 caractères');
                return;
            }
            gmLog('Validation code « %s » — isBuyer=%s isSeller=%s', code, isBuyer, isSeller);
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fi-rs-spinner" style="animation:spin 1s linear infinite;"></i> Vérification...';
            try {
                if (isBuyer) { await _verifyCodeFromModal('buyer', code); }
                else if (isSeller) { await _verifyCodeFromModal('seller', code); }
                closeModal();
            } catch (err) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fi-rs-check"></i> Valider le code';
            }
        });
    }
    
    /* Valider avec Entrée */
    var codeInput = overlay.querySelector('#gmPeerVerificationCodeInput');
    if (codeInput && confirmBtn) {
        codeInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') confirmBtn.click();
        });
    }
}

/* --- Blocs HTML réutilisables pour le modal des codes --- */

function _buildCodeDisplayBlock(codeName, hint, codeValue, footerText) {
    return '<div style="margin-bottom:20px;padding:16px;background:#FEF3C7;border-radius:12px;border:1px solid #F59E0B;">'
        + '<p style="margin:0 0 8px;font-size:13px;color:#92400E;font-weight:600;">📤 Votre code ' + codeName + ' (' + hint + ') :</p>'
        + '<div style="background:white;padding:12px;border-radius:8px;text-align:center;">'
        + '<span style="font-size:28px;font-weight:800;color:#D97706;letter-spacing:6px;font-family:monospace;">' + (codeValue || '------') + '</span></div>'
        + '<p style="margin:8px 0 0;font-size:11px;color:#78350F;">' + footerText + '</p></div>';
}

function _buildCodeInputBlock(labelText, placeholder, helpText) {
    return '<div style="padding:16px;background:#EFF6FF;border-radius:12px;border:1px solid #3B82F6;">'
        + '<p style="margin:0 0 12px;font-size:13px;color:#1E40AF;font-weight:600;">📥 Entrez le code ' + labelText + ' :</p>'
        + '<label for="gmPeerVerificationCodeInput" style="display:block;margin:0 0 8px;font-size:12px;color:#1E40AF;font-weight:600;">Code ' + labelText + '</label>'
        + '<input type="text" id="gmPeerVerificationCodeInput" name="peer_verification_code" maxlength="6" placeholder="' + placeholder + '" '
        + 'autocomplete="one-time-code" inputmode="text" '
        + 'style="width:100%;padding:14px;border:2px solid #93C5FD;border-radius:8px;font-size:20px;letter-spacing:6px;'
        + 'text-align:center;text-transform:uppercase;font-family:monospace;font-weight:700;box-sizing:border-box;">'
        + '<p style="margin:8px 0 0;font-size:11px;color:#1E3A8A;">' + helpText + '</p></div>';
}

function _buildVerifiedBadge() {
    return '<div style="background:#D1FAE5;padding:12px;border-radius:8px;display:flex;align-items:center;gap:10px;border:1px solid #10B981;">'
        + '<i class="fi-rs-check-circle" style="font-size:20px;color:#059669;"></i>'
        + '<span style="color:#065F46;font-weight:600;">Votre code a été vérifié !</span></div>';
}

/* ═══════════════════════════════════════════════════════════
   15. Vérification de code (appel API)
   ═══════════════════════════════════════════════════════════ */

/**
 * Envoie le code saisi au serveur pour vérification.
 * @param {string} role - 'buyer' ou 'seller'
 * @param {string} code - code à 6 caractères
 */
async function _verifyCodeFromModal(role, code) {
    if (!window.currentOrderId) {
        GMModal.error('Erreur', 'Impossible de trouver la commande');
        throw new Error('No order ID');
    }
    
    var endpoint = role === 'buyer' ? 'verify-buyer-code' : 'verify-seller-code';
    gmLog('_verifyCodeFromModal → POST /c2c/order/%d/%s/ code=%s', window.currentOrderId, endpoint, code);

    var response = await fetch('/c2c/order/' + window.currentOrderId + '/' + endpoint + '/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ code: code })
    });
    var data = await response.json();
    
    if (data.success) {
        gmLog('Code vérifié avec succès — canReview=%s', data.can_review);
        var otherRole = role === 'buyer' ? 'vendeur' : 'acheteur';
        var completeMsg = data.can_review
            ? (data.message || 'Transaction complète !') + '<br><br>Vous pouvez maintenant noter le ' + otherRole + '.'
            : (data.message || 'Code vérifié avec succès !');

        GMModal.success(data.can_review ? 'Transaction terminée !' : 'Code vérifié !', completeMsg, function () {
            if (data.can_review && data.review_url) {
                GMModal.show({
                    type: 'confirm',
                    title: 'Noter le ' + otherRole,
                    message: 'Souhaitez-vous noter le ' + otherRole + ' maintenant ?',
                    showCancel: true,
                    confirmText: 'Oui, noter',
                    cancelText: 'Plus tard',
                    onConfirm: function () { window.location.href = data.review_url; },
                    onCancel: function () { _reloadIntent(); }
                });
        } else {
                _reloadIntent();
                }
            });
        return true;
    } else {
        gmWarn('Code refusé: %s', data.error);
        GMModal.error('Erreur', data.error || 'Code invalide');
        throw new Error(data.error || 'Code invalide');
    }
}

/* ═══════════════════════════════════════════════════════════
   16. Affichage / masquage section négociation + polling
   ═══════════════════════════════════════════════════════════ */

function toggleNegotiationSection(purchaseIntentId, intentData) {
    var section = document.getElementById('negotiationSection');
    var acceptBtn = document.getElementById('acceptFinalPriceBtn');

    if (purchaseIntentId) {
        currentPurchaseIntentId = purchaseIntentId;

        var _paidStatuses = ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'];
        var _orderStatus = intentData ? intentData.order_status : null;
        var _isPaid = _orderStatus && _paidStatuses.indexOf(_orderStatus) !== -1;

        if (section) {
            section.style.display = 'block';
            // Post-paiement : marquer la section comme "résumé" (formulaire masqué, lecture seule)
            if (_isPaid) {
                section.setAttribute('data-gm-resume-mode', '1');
            } else {
                section.removeAttribute('data-gm-resume-mode');
            }
        }
        if (_isPaid && acceptBtn) acceptBtn.style.display = 'none';

        if (intentData && intentData.negotiations) {
            displayNegotiationHistory(intentData.negotiations, intentData);
        } else if (intentData) {
            lockInputsIfAgreed(intentData);
            if (acceptBtn) acceptBtn.style.display = 'none';
        } else if (acceptBtn) {
            acceptBtn.style.display = 'none';
        }
        startNegotiationPolling();
        } else {
        currentPurchaseIntentId = null;
        if (section) section.style.display = 'none';
        if (acceptBtn) acceptBtn.style.display = 'none';
        stopNegotiationPolling();
    }
}

/* ═══════════════════════════════════════════════════════════
   17. Helpers de rechargement (DRY)
   ═══════════════════════════════════════════════════════════ */

function _reloadIntent() {
                if (currentPurchaseIntentId) {
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                }
}

function _reloadIntentAndConversation() {
    _reloadIntent();
    if (typeof currentProductId !== 'undefined' && currentProductId && typeof loadConversations === 'function') {
        loadConversations(currentProductId);
        setTimeout(function () {
            if (typeof currentConversationId !== 'undefined' && currentConversationId && typeof showActiveConversation === 'function') {
                showActiveConversation(currentConversationId);
            }
        }, 500);
    }
}

/* ═══════════════════════════════════════════════════════════
   18. Actions secondaires (archivage de conversation)
   ═══════════════════════════════════════════════════════════ */

async function archiveConversation(conversationId) {
    GMModal.show({
        type: 'confirm',
        title: 'Archiver la conversation',
        message: 'Voulez-vous archiver cette conversation ?',
        showCancel: true,
        confirmText: 'Archiver',
        cancelText: 'Annuler',
        onConfirm: async function () {
            try {
                var response = await fetch('/archive-conversation/' + conversationId + '/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
                });
                var data = await response.json();
                if (data.success) { GMModal.success('Archivée', 'Conversation archivée avec succès', function () { location.reload(); }); }
                else { GMModal.error('Erreur', data.error || "Erreur lors de l'archivage"); }
            } catch (e) { gmErr('archiveConversation ERREUR:', e); GMModal.error('Erreur', "Erreur lors de l'archivage"); }
        }
    });
}

async function unarchiveConversation(conversationId) {
    try {
        var response = await fetch('/unarchive-conversation/' + conversationId + '/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
        });
        var data = await response.json();
        if (data.success) { GMModal.success('Désarchivée', 'Conversation désarchivée', function () { location.reload(); }); }
        else { GMModal.error('Erreur', data.error || 'Erreur lors de la désarchivage'); }
    } catch (e) { gmErr('unarchiveConversation ERREUR:', e); GMModal.error('Erreur', 'Erreur lors de la désarchivage'); }
}

/* ═══════════════════════════════════════════════════════════
   Countdown timers — offres de négociation (24h)
   ═══════════════════════════════════════════════════════════ */

var _countdownInterval = null;

function _formatCountdown(ms) {
    if (ms <= 0) return 'Expirée';
    var totalSecs = Math.floor(ms / 1000);
    var h = Math.floor(totalSecs / 3600);
    var m = Math.floor((totalSecs % 3600) / 60);
    var s = totalSecs % 60;
    var urgency = ms < 3600000; // < 1h = orange/rouge
    var color = ms < 1800000 ? '#EF4444' : ms < 3600000 ? '#F59E0B' : '#6B7280';
    var label = h > 0
        ? h + 'h ' + String(m).padStart(2, '0') + 'min'
        : m > 0
            ? m + 'min ' + String(s).padStart(2, '0') + 's'
            : s + 's';
    return '<i class="fi-rs-clock" style="margin-right:3px;"></i>'
        + '<span style="color:' + color + ';font-weight:' + (urgency ? '700' : '600') + ';">'
        + 'Expire dans ' + label + '</span>';
}

function _startNegotiationCountdowns() {
    if (_countdownInterval) clearInterval(_countdownInterval);
    var countdownEls = document.querySelectorAll('.gm-nego-countdown[data-expires]');
    if (!countdownEls.length) return;

    _countdownInterval = setInterval(function () {
        var els = document.querySelectorAll('.gm-nego-countdown[data-expires]');
        if (!els.length) { clearInterval(_countdownInterval); return; }
        els.forEach(function (el) {
            var expires = new Date(el.getAttribute('data-expires'));
            var ms = expires - Date.now();
            if (ms <= 0) {
                el.innerHTML = '<span style="font-size:11px;color:#EF4444;font-weight:600;">Offre expirée</span>';
                el.removeAttribute('data-expires');
                } else {
                el.innerHTML = _formatCountdown(ms);
            }
        });
    }, 1000);
}

/* ═══════════════════════════════════════════════════════════
   Gamification — Milestones & Effets visuels
   ═══════════════════════════════════════════════════════════ */

/**
 * Détecte les transitions de statut et déclenche le milestone correspondant.
 */
function _detectAndFireMilestone(prevStatus, curStatus, prevOrderStatus, curOrderStatus, data, isBuyer) {
    var paidList = ['paid', 'pending_delivery', 'delivered', 'verified'];

    // Ouverture de la négociation (première fois visible)
    if (prevStatus !== 'negotiating' && curStatus === 'negotiating') {
        _gmMilestone('negotiating', isBuyer
            ? '🚀 Négociation ouverte ! Faites votre offre.'
            : '🚀 Nouvelle demande ! Un acheteur veut négocier.');
        return;
    }

    // Accord trouvé
    if (prevStatus !== 'agreed' && curStatus === 'agreed') {
        _gmMilestone('agreed', isBuyer
            ? '🤝 Accord trouvé ! Procédez au paiement sécurisé.'
            : '🤝 Accord trouvé ! En attente du paiement de l\'acheteur.');
        return;
    }

    // Paiement confirmé (escrow)
    if (prevOrderStatus !== 'paid' && paidList.indexOf(curOrderStatus) !== -1
            && (prevOrderStatus === null || paidList.indexOf(prevOrderStatus) === -1)) {
        _gmMilestone('paid', isBuyer
            ? '🔒 Argent sécurisé en escrow ! Convenez du lieu de remise.'
            : '🔒 Paiement reçu et sécurisé ! Préparez la remise de l\'article.');
        return;
    }

    // Codes déverrouillés (les deux confirmations faites)
    var v = data.verification;
    var prevV = window._gmLastVerification;
    if (v && v.codes_unlocked && !(prevV && prevV.codes_unlocked)) {
        _gmMilestone('codes_unlocked', '🔓 Codes déverrouillés ! Validez l\'échange avec les codes.');
    }
    window._gmLastVerification = v ? { codes_unlocked: v.codes_unlocked, is_completed: v.is_completed } : null;
}

/**
 * Affiche/met à jour la bannière "X autres acheteurs intéressés" pour le vendeur.
 */
function _updateCompetingBuyersBanner(count, show) {
    var host = document.getElementById('gmCompetingBuyersHost');
    if (!host) {
        // Créer le conteneur une seule fois dans negotiationSection
        var sec = document.getElementById('negotiationSection');
        if (!sec) return;
        host = document.createElement('div');
        host.id = 'gmCompetingBuyersHost';
        sec.insertBefore(host, sec.firstChild);
    }
    if (!show || count < 1) { host.innerHTML = ''; return; }
    host.innerHTML =
        '<div style="background:#FFF7ED;border:1.5px solid #FED7AA;border-radius:10px;'
        + 'padding:10px 14px;margin-bottom:10px;font-size:12px;color:#92400E;display:flex;align-items:center;gap:8px;">'
        + '<span style="font-size:18px;">🔥</span>'
        + '<span><strong>' + count + ' autre' + (count > 1 ? 's acheteurs sont' : ' acheteur est')
        + ' également intéressé' + (count > 1 ? 's' : '')
        + '</strong> par cet article. Choisissez la meilleure offre !</span>'
        + '</div>';
}

/**
 * Affiche un toast de milestone dans le chat.
 * types : 'negotiating' | 'offer_accepted' | 'agreed' | 'paid' | 'codes_unlocked' | 'completed'
 */
function _gmMilestone(type, message) {
    var cfg = {
        negotiating:  { icon: '🚀', color: '#2563EB', bg: '#EFF6FF', border: '#BFDBFE', duration: 4000 },
        offer_accepted:{ icon: '⭐', color: '#D97706', bg: '#FFFBEB', border: '#FDE68A', duration: 3500 },
        agreed:       { icon: '🤝', color: '#059669', bg: '#ECFDF5', border: '#6EE7B7', duration: 5000 },
        paid:         { icon: '🔒', color: '#7C3AED', bg: '#F5F3FF', border: '#DDD6FE', duration: 5000 },
        codes_unlocked:{ icon: '🔓', color: '#0891B2', bg: '#ECFEFF', border: '#A5F3FC', duration: 4000 },
        completed:    { icon: '🎉', color: '#065F46', bg: '#D1FAE5', border: '#34D399', duration: 7000, confetti: true },
    };
    var c = cfg[type] || cfg.negotiating;

    // Toast
    var toast = document.createElement('div');
    toast.className = 'gm-milestone-toast gm-milestone-toast--' + type;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML =
        '<span class="gm-milestone-toast__icon">' + c.icon + '</span>'
        + '<span class="gm-milestone-toast__msg">' + (message || '') + '</span>';
    toast.style.cssText =
        'background:' + c.bg + ';border:1.5px solid ' + c.border + ';color:' + c.color + ';';

    var host = document.getElementById('gmMilestoneHost');
    if (!host) {
        host = document.createElement('div');
        host.id = 'gmMilestoneHost';
        host.style.cssText =
            'position:fixed;bottom:90px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
        document.body.appendChild(host);
    }
    host.appendChild(toast);

    // Entrée
    requestAnimationFrame(function () { toast.classList.add('gm-milestone-toast--in'); });

    // Sortie
    setTimeout(function () {
        toast.classList.remove('gm-milestone-toast--in');
        toast.classList.add('gm-milestone-toast--out');
        setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 400);
    }, c.duration);

    // Confetti pour la completion
    if (c.confetti) {
        _gmConfetti();
    }
}

/**
 * Lance un mini-confetti CSS pur au centre de l'écran.
 */
function _gmConfetti() {
    var colors = ['#FF7B2C', '#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'];
    var host = document.createElement('div');
    host.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:10000;overflow:hidden;';
    document.body.appendChild(host);

    for (var i = 0; i < 60; i++) {
        var p = document.createElement('div');
        var size = 6 + Math.random() * 8;
        var x = 10 + Math.random() * 80;
        var delay = Math.random() * 0.8;
        var dur = 1.2 + Math.random() * 1.4;
        var rot = Math.random() * 360;
        var color = colors[Math.floor(Math.random() * colors.length)];
        var isRect = Math.random() > 0.5;
        p.style.cssText =
            'position:absolute;top:-20px;left:' + x + '%;'
            + 'width:' + size + 'px;height:' + (isRect ? size * 0.4 : size) + 'px;'
            + 'background:' + color + ';'
            + (isRect ? '' : 'border-radius:50%;')
            + 'opacity:1;'
            + 'animation:gmConfettiFall ' + dur + 's ' + delay + 's ease-in forwards;'
            + 'transform:rotate(' + rot + 'deg);';
        host.appendChild(p);
    }

    setTimeout(function () {
        if (host.parentNode) host.parentNode.removeChild(host);
    }, 3500);
}

/**
 * Injecte les styles CSS nécessaires aux milestones (une seule fois).
 */
(function _injectMilestoneCSS() {
    if (document.getElementById('gm-milestone-styles')) return;
    var style = document.createElement('style');
    style.id = 'gm-milestone-styles';
    style.textContent = [
        '.gm-milestone-toast{',
            'display:flex;align-items:center;gap:10px;',
            'padding:12px 16px;border-radius:12px;',
            'font-size:13px;font-weight:600;line-height:1.4;',
            'max-width:280px;box-shadow:0 4px 20px rgba(0,0,0,0.12);',
            'opacity:0;transform:translateX(24px) scale(0.96);',
            'transition:opacity 0.3s ease,transform 0.3s ease;',
        '}',
        '.gm-milestone-toast--in{opacity:1;transform:translateX(0) scale(1);}',
        '.gm-milestone-toast--out{opacity:0;transform:translateX(24px) scale(0.95);}',
        '.gm-milestone-toast__icon{font-size:20px;flex-shrink:0;}',
        '.gm-milestone-toast__msg{flex:1;}',

        /* Confetti keyframe */
        '@keyframes gmConfettiFall{',
            '0%{transform:translateY(0) rotate(0deg);opacity:1;}',
            '80%{opacity:1;}',
            '100%{transform:translateY(100vh) rotate(720deg);opacity:0;}',
        '}',

        /* Pulse ring sur les boutons d'action clés */
        '@keyframes gmPulseRing{',
            '0%{box-shadow:0 0 0 0 currentColor;}',
            '70%{box-shadow:0 0 0 10px transparent;}',
            '100%{box-shadow:0 0 0 0 transparent;}',
        '}',
        '.gm-pulse{animation:gmPulseRing 1.8s ease-in-out infinite;}',

        /* Apparition rebond des boutons importants */
        '@keyframes gmBounceIn{',
            '0%{transform:scale(0.7);opacity:0;}',
            '60%{transform:scale(1.06);}',
            '80%{transform:scale(0.97);}',
            '100%{transform:scale(1);opacity:1;}',
        '}',
        '.gm-bounce-in{animation:gmBounceIn 0.45s cubic-bezier(.36,.07,.19,.97) both;}',

        /* Section résumé négociation (lecture seule post-paiement) */
        '#negotiationSection[data-gm-resume-mode]{',
            'background:#F8FAFF;border-top:1.5px solid #DBEAFE;',
        '}',
        '#negotiationSection[data-gm-resume-mode] .gm-s-7b754e{',
            'opacity:0.8;',
        '}',
    ].join('');
    document.head.appendChild(style);
})();