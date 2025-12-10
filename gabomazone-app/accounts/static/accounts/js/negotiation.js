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
        alert('Aucune intention d\'achat active');
        return;
    }
    
    const priceInput = document.getElementById('negotiationPrice');
    const proposedPrice = parseFloat(priceInput.value);
    
    if (!proposedPrice || proposedPrice <= 0) {
        alert('Veuillez entrer un prix valide');
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
            // Réinitialiser le formulaire
            priceInput.value = '';
            
            // Recharger l'intention d'achat avec l'historique mis à jour
            if (currentPurchaseIntentId && typeof loadPurchaseIntentForConversation === 'function') {
                setTimeout(() => {
                    loadPurchaseIntentForConversation(null, null, null, currentPurchaseIntentId);
                }, 300);
            }
            
            // Recharger les conversations et messages pour afficher la négociation
            if (currentProductId && typeof loadConversations === 'function') {
                loadConversations(currentProductId);
                // Réafficher la conversation active après rechargement
                setTimeout(() => {
                    if (currentConversationId && typeof showActiveConversation === 'function') {
                        showActiveConversation(currentConversationId);
                    }
                }, 800);
            }
        } else {
            alert(data.error || 'Erreur lors de l\'envoi de la proposition');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'envoi de la proposition');
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
            toggleNegotiationSection(data.purchase_intent_id, data);
            displayNegotiationHistory(data.negotiations || [], data);
            if (typeof updateChatControls === 'function') {
                updateChatControls(data);
            }
        } else {
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
        return;
    }
    
    const currentUserId = window.currentUserId || 0;
    let html = '<div style="margin-bottom: 12px; max-height: 220px; overflow-y: auto;">';
    
    negotiations.forEach((neg, idx) => {
        const isProposer = neg.proposer_id === currentUserId;
        const isPending = neg.status === 'pending';
        const isLast = idx === negotiations.length - 1;
        const canAct = isPending && isLast && !isProposer; // seul le destinataire de la dernière offre peut agir
        
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
    
    html += '</div>';
    historyContainer.innerHTML = html;
    
    // Afficher le bouton pour accepter le prix final si applicable
    const acceptFinalPriceBtn = document.getElementById('acceptFinalPriceBtn');
    if (acceptFinalPriceBtn) {
        if (intentData && intentData.status === 'agreed' && intentData.order_id) {
            // Prix final déjà accepté et commande créée : proposer le paiement
            acceptFinalPriceBtn.style.display = 'block';
            acceptFinalPriceBtn.innerHTML = '<i class="fi-rs-credit-card"></i> Accepter le prix final et procéder au paiement';
            acceptFinalPriceBtn.onclick = () => {
                window.location.href = `/c2c/order/${intentData.order_id}/payment/`;
            };
        } else if (intentData && intentData.can_accept_final_price && intentData.negotiated_price) {
            acceptFinalPriceBtn.style.display = 'block';
            acceptFinalPriceBtn.innerHTML = '<i class="fi-rs-hand-holding-usd"></i> Accepter le prix final';
            acceptFinalPriceBtn.onclick = () => acceptFinalPrice(intentData.purchase_intent_id, intentData.negotiated_price);
        } else {
            acceptFinalPriceBtn.style.display = 'none';
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
async function acceptFinalPrice(intentId, finalPrice) {
    if (!confirm(`Êtes-vous sûr d'accepter le prix final de ${parseFloat(finalPrice).toLocaleString()} FCFA ?\n\nVous serez redirigé vers le paiement.`)) {
        return;
    }
    
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
            // Rediriger vers la page de paiement
            window.location.href = `/c2c/order/${data.order_id}/payment/`;
        } else {
            alert(data.error || 'Erreur lors de l\'acceptation du prix final');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'acceptation du prix final');
    }
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
        }
        startNegotiationPolling();
    } else {
        currentPurchaseIntentId = null;
        if (section) section.style.display = 'none';
        stopNegotiationPolling();
    }
}

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
            // recharger l'intention et la conversation
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
            alert(data.error || 'Erreur lors de l\'acceptation de l\'offre');
        }
    } catch (e) {
        console.error(e);
        alert('Erreur lors de l\'acceptation de l\'offre');
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
            alert(data.error || 'Erreur lors du refus de l\'offre');
        }
    } catch (e) {
        console.error(e);
        alert('Erreur lors du refus de l\'offre');
    }
}

