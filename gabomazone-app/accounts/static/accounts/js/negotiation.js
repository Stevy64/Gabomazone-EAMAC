/**
 * Fonctions pour la négociation de prix dans le chatbot
 */

let currentPurchaseIntentId = null;
let negotiationPollInterval = null;

/**
 * Démarre un polling léger pour rafraîchir l'historique de négociation en quasi temps réel.
 */
function startNegotiationPolling() {
    stopNegotiationPolling();
    negotiationPollInterval = setInterval(() => {
        if (currentPurchaseIntentId && typeof loadPurchaseIntentForConversation === 'function') {
            loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
        }
    }, 7000);
}

/**
 * Stoppe le polling de négociation.
 */
function stopNegotiationPolling() {
    if (negotiationPollInterval) {
        clearInterval(negotiationPollInterval);
        negotiationPollInterval = null;
    }
}

/**
 * Soumet une proposition de négociation
 */
async function submitNegotiation(event) {
    event.preventDefault();
    
    if (!currentPurchaseIntentId) {
        GMModal.warning('Attention', 'Aucune intention d\'achat active');
        return;
    }
    
    const priceInput = document.getElementById('negotiationPrice');
    const proposedPrice = parseFloat(priceInput.value);
    
    if (!proposedPrice || proposedPrice <= 0) {
        GMModal.warning('Prix invalide', 'Veuillez entrer un prix valide');
        return;
    }
    
    try {
        const response = await fetch(`/c2c/negotiation/${currentPurchaseIntentId}/make-offer/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                proposed_price: proposedPrice,
                message: `Je propose ${proposedPrice.toLocaleString()} FCFA pour cet article.`
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            priceInput.value = '';
            
            if (currentPurchaseIntentId && typeof loadPurchaseIntentForConversation === 'function') {
                setTimeout(() => {
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                }, 300);
            }
            
            if (currentProductId && typeof loadConversations === 'function') {
                loadConversations(currentProductId);
                setTimeout(() => {
                    if (currentConversationId && typeof showActiveConversation === 'function') {
                        showActiveConversation(currentConversationId);
                    }
                }, 800);
            }
        } else {
            GMModal.error('Erreur', data.error || 'Erreur lors de l\'envoi de la proposition');
        }
    } catch (error) {
        console.error('Erreur:', error);
        GMModal.error('Erreur', 'Erreur lors de l\'envoi de la proposition');
    }
}

/**
 * Récupère le cookie CSRF
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
 * Charge l'intention d'achat pour une conversation avec l'historique des négociations
 */
async function loadPurchaseIntentForConversation(productId, buyerId, sellerId, intentId = null) {
    try {
        let url = '/c2c/purchase-intent/';
        if (intentId) {
            url += `?intent_id=${intentId}`;
        } else {
            url += `?product_id=${productId}&buyer_id=${buyerId}&seller_id=${sellerId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.purchase_intent_id) {
            // Stocker l'order_id pour la vérification
            window.currentOrderId = data.order_id || null;
            
            toggleNegotiationSection(data.purchase_intent_id, data);
            displayNegotiationHistory(data.negotiations || [], data);
            
            // Afficher la section de vérification si la commande est payée
            const currentUserId = window.currentUserId || 0;
            const isBuyer = data.buyer_id === currentUserId;
            const isSeller = data.seller_id === currentUserId;
            displayVerificationSection(data.verification, data.order, isBuyer, isSeller);
            
            if (typeof updateChatControls === 'function') {
                updateChatControls(data);
            }
        } else {
            window.currentOrderId = null;
            toggleNegotiationSection(null);
            if (typeof updateChatControls === 'function') {
                updateChatControls(null);
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement de l\'intention d\'achat:', error);
        toggleNegotiationSection(null);
        if (typeof updateChatControls === 'function') {
            updateChatControls(null);
        }
    }
}

/**
 * Affiche l'historique des négociations et les actions disponibles
 */
function displayNegotiationHistory(negotiations, intentData) {
    const historyContainer = document.getElementById('negotiationHistory');
    if (!historyContainer) return;
    
    if (negotiations.length === 0) {
        historyContainer.innerHTML = '<p style="margin: 0; font-size: 12px; color: #9CA3AF; font-style: italic;">Aucune proposition pour le moment</p>';
        const acceptFinalPriceBtn = document.getElementById('acceptFinalPriceBtn');
        if (acceptFinalPriceBtn) {
            acceptFinalPriceBtn.style.display = 'none';
        }
        return;
    }
    
    const currentUserId = window.currentUserId || 0;
    
    let html = '';
    
    negotiations.forEach((neg, idx) => {
        const isProposer = neg.proposer_id === currentUserId;
        const isPending = neg.status === 'pending';
        const isLast = idx === negotiations.length - 1;
        const canAct = isPending && isLast && !isProposer;
        
        html += `
            <div style="background: ${isProposer ? '#E0F2FE' : 'white'}; border-radius: 8px; padding: 10px; margin-bottom: 8px; border: 1px solid #E5E7EB;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 4px;">
                    <div>
                        <strong style="font-size: 12px; color: #1F2937;">${escapeHtml(neg.proposer_name)}</strong>
                        <span style="font-size: 11px; color: #6B7280; margin-left: 8px;">${neg.created_at}</span>
                    </div>
                    <span style="font-size: 14px; font-weight: 700; color: var(--color-orange);">${parseFloat(neg.proposed_price).toLocaleString()} FCFA</span>
                </div>
                ${neg.message ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: #6B7280;">${escapeHtml(neg.message)}</p>` : ''}
                <div style="margin-top: 6px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                    ${neg.status === 'accepted' ? '<span style="font-size: 11px; color: #10B981; font-weight: 700;">✓ Accepté</span>' : ''}
                    ${neg.status === 'rejected' ? '<span style="font-size: 11px; color: #EF4444; font-weight: 700;">✗ Refusé</span>' : ''}
                    ${canAct ? `
                        <button onclick="acceptNegotiation(${neg.id})" style="padding: 6px 10px; background: #10B981; color: white; border: none; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer;">Accepter</button>
                        <button onclick="rejectNegotiation(${neg.id})" style="padding: 6px 10px; background: #FEE2E2; color: #EF4444; border: none; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer;">Refuser</button>
                    ` : ''}
                    ${isPending && !canAct ? '<span style="font-size: 11px; color: #6B7280;">En attente de réponse...</span>' : ''}
                </div>
            </div>
        `;
    });
    
    historyContainer.innerHTML = html;
    
    // Gérer le bouton "Accepter le prix final" - UNIQUEMENT pour l'acheteur
    const acceptFinalPriceBtn = document.getElementById('acceptFinalPriceBtn');
    if (!acceptFinalPriceBtn || !intentData) {
        return;
    }
    
    const isBuyer = intentData.buyer_id === currentUserId;
    const isSeller = intentData.seller_id === currentUserId;
    
    if (isSeller || !isBuyer) {
        acceptFinalPriceBtn.style.display = 'none';
        return;
    }
    
    if (intentData.status === 'agreed' && intentData.order_id) {
        acceptFinalPriceBtn.style.display = 'block';
        acceptFinalPriceBtn.innerHTML = '<i class="fi-rs-credit-card"></i> Accepter le prix final et procéder au paiement';
        acceptFinalPriceBtn.onclick = () => {
            window.location.href = `/c2c/order/${intentData.order_id}/payment/`;
        };
        return;
    }
    
    if (intentData.can_accept_final_price && intentData.negotiated_price) {
        acceptFinalPriceBtn.style.display = 'block';
        acceptFinalPriceBtn.innerHTML = '<i class="fi-rs-hand-holding-usd"></i> Accepter le prix final';
        acceptFinalPriceBtn.onclick = () => acceptFinalPrice(intentData.purchase_intent_id, intentData.negotiated_price);
        return;
    }
    
    acceptFinalPriceBtn.style.display = 'none';
    lockInputsIfAgreed(intentData);
}

/**
 * Bloque tous les inputs si le prix est accepté mais pas encore payé
 */
function lockInputsIfAgreed(intentData) {
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.querySelector('#messageForm button[type="submit"]');
    const negotiationForm = document.getElementById('negotiationForm');
    const negotiationPrice = document.getElementById('negotiationPrice');
    const helper = document.getElementById('chatHelper');
    
    const status = intentData ? intentData.status : null;
    const orderStatus = intentData ? intentData.order_status : null;
    const isAgreed = status === 'agreed';
    const isPaid = orderStatus && ['paid', 'pending_delivery', 'delivered', 'verified', 'completed'].includes(orderStatus);
    const isCompleted = orderStatus === 'completed';
    
    if (isAgreed && !isPaid) {
        if (messageInput) {
            messageInput.disabled = true;
            messageInput.placeholder = '⏳ En attente du paiement...';
        }
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.style.opacity = '0.5';
            sendBtn.style.cursor = 'not-allowed';
        }
        
        if (negotiationPrice) {
            negotiationPrice.disabled = true;
            negotiationPrice.placeholder = 'Prix accepté';
        }
        if (negotiationForm) {
            const submitBtn = negotiationForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.5';
                submitBtn.style.cursor = 'not-allowed';
            }
        }
        
        if (helper) {
            const currentUserId = window.currentUserId || 0;
            const isBuyer = intentData.buyer_id === currentUserId;
            helper.style.display = 'block';
            helper.innerHTML = isBuyer 
                ? '✅ Prix accepté ! Cliquez sur le bouton vert pour procéder au paiement.'
                : '✅ Prix accepté ! En attente du paiement de l\'acheteur.';
            helper.style.color = '#10B981';
        }
    } else if (isPaid) {
        if (isCompleted) {
            // Transaction terminée → BLOQUER le chat définitivement
            if (messageInput) {
                messageInput.disabled = true;
                messageInput.placeholder = 'Transaction terminée - Le chat est désactivé';
            }
            if (sendBtn) {
                sendBtn.disabled = true;
                sendBtn.style.opacity = '0.5';
                sendBtn.style.cursor = 'not-allowed';
            }
        } else {
            // Paiement effectué mais transaction en cours → chat ouvert
            if (messageInput) {
                messageInput.disabled = false;
                messageInput.placeholder = 'Discutez du lieu et de l\'heure de rencontre...';
            }
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.style.opacity = '1';
                sendBtn.style.cursor = 'pointer';
            }
        }
        
        if (negotiationPrice) {
            negotiationPrice.disabled = true;
        }
        if (negotiationForm) {
            negotiationForm.style.display = 'none';
        }
        
        const negotiationSection = document.getElementById('negotiationSection');
        if (negotiationSection) {
            negotiationSection.style.display = 'none';
        }
        
        if (helper) {
            if (isCompleted) {
                helper.style.display = 'block';
                helper.innerHTML = '🎉 Transaction terminée avec succès ! Le chat est maintenant fermé.';
                helper.style.color = '#059669';
            } else {
                helper.style.display = 'block';
                helper.innerHTML = '💬 Paiement confirmé ! Échangez pour convenir du lieu et de l\'heure de remise.';
                helper.style.color = '#2563EB';
            }
        }
    }
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
 * Accepte le prix final et crée la commande C2C
 */
function acceptFinalPrice(intentId, finalPrice) {
    GMModal.show({
        type: 'confirm',
        title: 'Accepter le prix final',
        message: `Êtes-vous sûr d'accepter le prix final de <strong>${parseFloat(finalPrice).toLocaleString()} FCFA</strong> ?<br><br>Vous serez redirigé vers le paiement.`,
        showCancel: true,
        confirmText: 'Accepter',
        cancelText: 'Annuler',
        onConfirm: async function() {
            try {
                const response = await fetch(`/c2c/purchase-intent/${intentId}/accept-price/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        final_price: finalPrice
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = `/c2c/order/${data.order_id}/payment/`;
                } else {
                    GMModal.error('Erreur', data.error || 'Erreur lors de l\'acceptation du prix final');
                }
            } catch (error) {
                console.error('Erreur:', error);
                GMModal.error('Erreur', 'Erreur lors de l\'acceptation du prix final');
            }
        }
    });
}

/**
 * Affiche/masque la section de négociation et (dés)active le polling
 */
function toggleNegotiationSection(purchaseIntentId, intentData = null) {
    const section = document.getElementById('negotiationSection');
    if (purchaseIntentId) {
        currentPurchaseIntentId = purchaseIntentId;
        if (section) section.style.display = 'block';
        
        if (intentData && intentData.negotiations) {
            displayNegotiationHistory(intentData.negotiations, intentData);
        } else {
            const acceptFinalPriceBtn = document.getElementById('acceptFinalPriceBtn');
            if (acceptFinalPriceBtn) {
                acceptFinalPriceBtn.style.display = 'none';
            }
        }
        
        if (intentData) {
            lockInputsIfAgreed(intentData);
        }
        
        startNegotiationPolling();
    } else {
        currentPurchaseIntentId = null;
        if (section) section.style.display = 'none';
        const acceptFinalPriceBtn = document.getElementById('acceptFinalPriceBtn');
        if (acceptFinalPriceBtn) {
            acceptFinalPriceBtn.style.display = 'none';
        }
        stopNegotiationPolling();
    }
}

/**
 * Accepter / Refuser une négociation
 */
async function acceptNegotiation(negotiationId) {
    try {
        const resp = await fetch(`/c2c/negotiation/${negotiationId}/accept/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await resp.json();
        if (data.success) {
            if (currentPurchaseIntentId) {
                loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
            }
            if (currentProductId && typeof loadConversations === 'function') {
                loadConversations(currentProductId);
                setTimeout(() => {
                    if (currentConversationId && typeof showActiveConversation === 'function') {
                        showActiveConversation(currentConversationId);
                    }
                }, 400);
            }
        } else {
            GMModal.error('Erreur', data.error || 'Erreur lors de l\'acceptation de l\'offre');
        }
    } catch (e) {
        console.error(e);
        GMModal.error('Erreur', 'Erreur lors de l\'acceptation de l\'offre');
    }
}

async function rejectNegotiation(negotiationId) {
    try {
        const resp = await fetch(`/c2c/negotiation/${negotiationId}/reject/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await resp.json();
        if (data.success) {
            if (currentPurchaseIntentId) {
                loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
            }
            if (currentProductId && typeof loadConversations === 'function') {
                loadConversations(currentProductId);
                setTimeout(() => {
                    if (currentConversationId && typeof showActiveConversation === 'function') {
                        showActiveConversation(currentConversationId);
                    }
                }, 400);
            }
        } else {
            GMModal.error('Erreur', data.error || 'Erreur lors du refus de l\'offre');
        }
    } catch (e) {
        console.error(e);
        GMModal.error('Erreur', 'Erreur lors du refus de l\'offre');
    }
}

/**
 * Affiche la section de vérification de livraison
 * Utilise un bouton simple qui ouvre un popup modal
 */
function displayVerificationSection(verificationData, orderData, isBuyer, isSeller) {
    const verificationSection = document.getElementById('verificationSection');
    if (!verificationSection) return;
    
    if (!verificationData || !orderData) {
        verificationSection.style.display = 'none';
        return;
    }
    
    // Afficher seulement si la commande est payée
    if (!['paid', 'pending_delivery', 'delivered', 'verified', 'completed'].includes(orderData.status)) {
        verificationSection.style.display = 'none';
        return;
    }
    
    // Stocker les données globalement
    window._verificationData = verificationData;
    window._orderData = orderData;
    window._isBuyer = isBuyer;
    window._isSeller = isSeller;
    
    // Afficher la section
    verificationSection.style.display = 'block';
    
    // Si transaction déjà complète
    if (verificationData.is_completed) {
        verificationSection.innerHTML = `
            <div style="background: #D1FAE5; padding: 16px; border-radius: 12px; text-align: center; border: 1px solid #10B981;">
                <i class="fi-rs-check-circle" style="font-size: 32px; color: #059669;"></i>
                <p style="margin: 12px 0 0 0; font-size: 16px; color: #065F46; font-weight: 700;">
                    🎉 Transaction terminée avec succès !
                </p>
            </div>
        `;
        return;
    }
    
    // Bouton simple pour ouvrir le popup
    verificationSection.innerHTML = `
        <button onclick="openVerificationModal()" style="width: 100%; padding: 14px 16px; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: all 0.3s; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);">
            <i class="fi-rs-shield-check" style="font-size: 18px;"></i>
            Valider la transaction (codes de vérification)
        </button>
    `;
}

/**
 * Ouvre le popup modal personnalisé pour la vérification des codes
 * Modal personnalisé qui capture la valeur AVANT de se fermer
 */
function openVerificationModal() {
    const verificationData = window._verificationData;
    const isBuyer = window._isBuyer;
    const isSeller = window._isSeller;
    
    if (!verificationData) {
        GMModal.error('Erreur', 'Données de vérification non disponibles');
        return;
    }
    
    // Déterminer si on doit afficher le bouton de validation
    const showValidateBtn = (isBuyer && !verificationData.buyer_code_verified) || (isSeller && !verificationData.seller_code_verified);
    
    // Créer le modal personnalisé
    const overlay = document.createElement('div');
    overlay.id = 'verificationModalOverlay';
    overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 20px;';
    
    let inputHtml = '';
    let codeDisplayHtml = '';
    
    // ACHETEUR : Son code est buyer_code (A-CODE), il doit entrer seller_code (V-CODE du vendeur)
    if (isBuyer) {
        codeDisplayHtml = `
            <div style="margin-bottom: 20px; padding: 16px; background: #FEF3C7; border-radius: 12px; border: 1px solid #F59E0B;">
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #92400E; font-weight: 600;">
                    📤 Votre code A-CODE (à donner au vendeur) :
                </p>
                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 28px; font-weight: 800; color: #D97706; letter-spacing: 6px; font-family: monospace;">${verificationData.buyer_code || '------'}</span>
                </div>
                <p style="margin: 8px 0 0 0; font-size: 11px; color: #78350F;">
                    Donnez ce code au vendeur quand vous recevez l'article.
                </p>
            </div>
        `;
        
        if (!verificationData.buyer_code_verified) {
            inputHtml = `
                <div style="padding: 16px; background: #EFF6FF; border-radius: 12px; border: 1px solid #3B82F6;">
                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #1E40AF; font-weight: 600;">
                        📥 Entrez le code V-CODE du vendeur :
                    </p>
                    <input type="text" id="verificationCodeInput" maxlength="6" placeholder="V-CODE" 
                           style="width: 100%; padding: 14px; border: 2px solid #93C5FD; border-radius: 8px; font-size: 20px; letter-spacing: 6px; text-align: center; text-transform: uppercase; font-family: monospace; font-weight: 700; box-sizing: border-box;">
                    <p style="margin: 8px 0 0 0; font-size: 11px; color: #1E3A8A;">
                        Le vendeur vous donnera ce code après vous avoir remis l'article.
                    </p>
                </div>
            `;
        } else {
            inputHtml = `
                <div style="background: #D1FAE5; padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px; border: 1px solid #10B981;">
                    <i class="fi-rs-check-circle" style="font-size: 20px; color: #059669;"></i>
                    <span style="color: #065F46; font-weight: 600;">Votre code a été vérifié !</span>
                </div>
            `;
        }
    }
    
    // VENDEUR : Son code est seller_code (V-CODE), il doit entrer buyer_code (A-CODE de l'acheteur)
    if (isSeller) {
        codeDisplayHtml = `
            <div style="margin-bottom: 20px; padding: 16px; background: #FEF3C7; border-radius: 12px; border: 1px solid #F59E0B;">
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #92400E; font-weight: 600;">
                    📤 Votre code V-CODE (à donner à l'acheteur) :
                </p>
                <div style="background: white; padding: 12px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 28px; font-weight: 800; color: #D97706; letter-spacing: 6px; font-family: monospace;">${verificationData.seller_code || '------'}</span>
                </div>
                <p style="margin: 8px 0 0 0; font-size: 11px; color: #78350F;">
                    Donnez ce code à l'acheteur après lui avoir remis l'article.
                </p>
            </div>
        `;
        
        if (!verificationData.seller_code_verified) {
            inputHtml = `
                <div style="padding: 16px; background: #EFF6FF; border-radius: 12px; border: 1px solid #3B82F6;">
                    <p style="margin: 0 0 12px 0; font-size: 13px; color: #1E40AF; font-weight: 600;">
                        📥 Entrez le code A-CODE de l'acheteur :
                    </p>
                    <input type="text" id="verificationCodeInput" maxlength="6" placeholder="A-CODE" 
                           style="width: 100%; padding: 14px; border: 2px solid #93C5FD; border-radius: 8px; font-size: 20px; letter-spacing: 6px; text-align: center; text-transform: uppercase; font-family: monospace; font-weight: 700; box-sizing: border-box;">
                    <p style="margin: 8px 0 0 0; font-size: 11px; color: #1E3A8A;">
                        L'acheteur vous donnera ce code quand il recevra l'article.
                    </p>
                </div>
            `;
        } else {
            inputHtml = `
                <div style="background: #D1FAE5; padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 10px; border: 1px solid #10B981;">
                    <i class="fi-rs-check-circle" style="font-size: 20px; color: #059669;"></i>
                    <span style="color: #065F46; font-weight: 600;">Votre code a été vérifié !</span>
                </div>
            `;
        }
    }
    
    overlay.innerHTML = `
        <div style="background: white; border-radius: 16px; max-width: 420px; width: 100%; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 40px rgba(0,0,0,0.3);">
            <div style="padding: 20px; border-bottom: 1px solid #E5E7EB; display: flex; align-items: center; justify-content: space-between;">
                <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #1F2937; display: flex; align-items: center; gap: 10px;">
                    <i class="fi-rs-shield-check" style="color: #3B82F6;"></i>
                    Vérification de la transaction
                </h3>
                <button id="closeVerificationModal" style="background: none; border: none; font-size: 24px; color: #9CA3AF; cursor: pointer; padding: 4px;">&times;</button>
            </div>
            <div style="padding: 20px;">
                ${codeDisplayHtml}
                ${inputHtml}
            </div>
            <div style="padding: 16px 20px; border-top: 1px solid #E5E7EB; display: flex; gap: 12px; justify-content: flex-end;">
                <button id="cancelVerificationBtn" style="padding: 12px 24px; background: #F3F4F6; color: #374151; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer;">
                    Annuler
                </button>
                ${showValidateBtn ? `
                <button id="confirmVerificationBtn" style="padding: 12px 24px; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    <i class="fi-rs-check"></i> Valider le code
                </button>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Focus sur l'input
    setTimeout(() => {
        const input = document.getElementById('verificationCodeInput');
        if (input) input.focus();
    }, 100);
    
    // Fermer le modal
    const closeModal = () => {
        overlay.remove();
    };
    
    document.getElementById('closeVerificationModal').addEventListener('click', closeModal);
    document.getElementById('cancelVerificationBtn').addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });
    
    // Valider le code
    const confirmBtn = document.getElementById('confirmVerificationBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async () => {
            const input = document.getElementById('verificationCodeInput');
            const code = input ? input.value.trim().toUpperCase() : '';
            
            if (!code || code.length !== 6) {
                GMModal.warning('Code invalide', 'Le code doit contenir 6 caractères');
                return;
            }
            
            // Désactiver le bouton pendant le traitement
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fi-rs-spinner" style="animation: spin 1s linear infinite;"></i> Vérification...';
            
            try {
                if (isBuyer) {
                    await verifyBuyerCodeFromModal(code);
                } else if (isSeller) {
                    await verifySellerCodeFromModal(code);
                }
                closeModal();
            } catch (error) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fi-rs-check"></i> Valider le code';
            }
        });
    }
    
    // Valider avec Entrée
    const codeInput = document.getElementById('verificationCodeInput');
    if (codeInput) {
        codeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && confirmBtn) {
                confirmBtn.click();
            }
        });
    }
}

/**
 * Vérifie le code vendeur (V-CODE) depuis le modal
 * Retourne une promesse pour permettre la gestion du bouton
 */
async function verifySellerCodeFromModal(code) {
    if (!window.currentOrderId) {
        GMModal.error('Erreur', 'Impossible de trouver la commande');
        throw new Error('No order ID');
    }
    
    const response = await fetch(`/c2c/order/${window.currentOrderId}/verify-seller-code/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ code: code })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Vérifier si les deux codes sont validés pour proposer la notation
        const canReview = data.can_review || false;
        const reviewUrl = data.review_url || null;
        
        if (canReview && reviewUrl) {
            GMModal.success('Code vérifié !', 
                data.message || 'Code vérifié avec succès !<br><br>Les deux codes sont maintenant validés. Vous pouvez noter l\'acheteur.', 
                function() {
                    // Proposer de noter
                    GMModal.confirm(
                        'Noter l\'acheteur',
                        'Souhaitez-vous noter l\'acheteur maintenant ?',
                        function() {
                            window.location.href = reviewUrl;
                        },
                        function() {
                            if (currentPurchaseIntentId) {
                                loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                            }
                        }
                    );
                }
            );
        } else {
            GMModal.success('Succès !', data.message || 'Code vérifié avec succès', function() {
                if (currentPurchaseIntentId) {
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                }
            });
        }
        return true;
    } else {
        GMModal.error('Erreur', data.error || 'Code invalide');
        throw new Error(data.error || 'Code invalide');
    }
}

/**
 * Vérifie le code acheteur (A-CODE) depuis le modal
 * Retourne une promesse pour permettre la gestion du bouton
 */
async function verifyBuyerCodeFromModal(code) {
    if (!window.currentOrderId) {
        GMModal.error('Erreur', 'Impossible de trouver la commande');
        throw new Error('No order ID');
    }
    
    const response = await fetch(`/c2c/order/${window.currentOrderId}/verify-buyer-code/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ code: code })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Vérifier si les deux codes sont validés pour proposer la notation
        const canReview = data.can_review || false;
        const reviewUrl = data.review_url || null;
        
        if (canReview && reviewUrl) {
            GMModal.success('Transaction terminée !', 
                data.message || 'La transaction est maintenant complète !<br><br>Vous pouvez maintenant noter le vendeur pour partager votre expérience.', 
                function() {
                    // Proposer de noter
                    GMModal.confirm(
                        'Noter le vendeur',
                        'Souhaitez-vous noter le vendeur maintenant ?',
                        function() {
                            window.location.href = reviewUrl;
                        },
                        function() {
                            if (currentPurchaseIntentId) {
                                loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                            }
                        }
                    );
                }
            );
        } else {
            GMModal.success('Transaction terminée !', data.message || 'La transaction est maintenant complète !', function() {
                if (currentPurchaseIntentId) {
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                }
            });
        }
        return true;
    } else {
        GMModal.error('Erreur', data.error || 'Code invalide');
        throw new Error(data.error || 'Code invalide');
    }
}

/**
 * Archive une conversation
 */
async function archiveConversation(conversationId) {
    GMModal.confirm(
        'Archiver la conversation',
        'Voulez-vous archiver cette conversation ? Vous pourrez la retrouver dans la section "Archives".',
        async function() {
            try {
                const response = await fetch(`/archive-conversation/${conversationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    GMModal.success('Archivée', 'Conversation archivée avec succès', () => location.reload());
                } else {
                    GMModal.error('Erreur', data.error || 'Erreur lors de l\'archivage');
                }
            } catch (error) {
                console.error('Erreur:', error);
                GMModal.error('Erreur', 'Erreur lors de l\'archivage');
            }
        }
    );
}

/**
 * Désarchive une conversation
 */
async function unarchiveConversation(conversationId) {
    try {
        const response = await fetch(`/unarchive-conversation/${conversationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            GMModal.success('Désarchivée', 'Conversation désarchivée', () => location.reload());
        } else {
            GMModal.error('Erreur', data.error || 'Erreur lors de la désarchivage');
        }
    } catch (error) {
        console.error('Erreur:', error);
        GMModal.error('Erreur', 'Erreur lors de la désarchivage');
    }
}
