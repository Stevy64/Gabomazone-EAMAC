let currentProductId = null;
let currentConversationId = null;
let conversationsData = [];

function openChatbot(productId, productName) {
    currentProductId = productId;
    const popup = document.getElementById('chatbotPopup');
    const nameEl = document.getElementById('chatbotProductName');
    if (nameEl) nameEl.textContent = productName || '';
    popup.style.display = 'flex';
    
    // Charger les conversations
    loadConversations(productId);
    
    // Afficher la liste des conversations
    showConversationsList();
}

function closeChatbot() {
    const popup = document.getElementById('chatbotPopup');
    popup.style.display = 'none';
    currentProductId = null;
    currentConversationId = null;
    conversationsData = [];
}

function showConversationsList() {
    document.getElementById('conversationsList').style.display = 'flex';
    document.getElementById('activeConversation').style.display = 'none';
    currentConversationId = null;
}

function showActiveConversation(conversationId) {
    document.getElementById('conversationsList').style.display = 'none';
    document.getElementById('activeConversation').style.display = 'flex';
    
    const conversation = conversationsData.find(c => c.id === conversationId);
    if (!conversation) return;
    
    currentConversationId = conversationId;
    document.getElementById('activeConversationBuyer').textContent = conversation.buyer_name;
    
    // Afficher les messages
    displayMessages(conversation.messages);
    
    // Marquer comme lu
    markConversationAsRead(conversationId);
}

function loadConversations(productId) {
    const loadingDiv = document.getElementById('conversationsLoading');
    const contentDiv = document.getElementById('conversationsContent');
    const noConversationsDiv = document.getElementById('noConversations');
    
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    noConversationsDiv.style.display = 'none';
    
    fetch(`/product-conversations/${productId}/`)
        .then(response => response.json())
        .then(data => {
            loadingDiv.style.display = 'none';
            conversationsData = data.conversations || [];
            
            if (conversationsData.length === 0) {
                noConversationsDiv.style.display = 'block';
            } else {
                contentDiv.style.display = 'block';
                displayConversationsList(conversationsData);
            }
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
            loadingDiv.style.display = 'none';
            noConversationsDiv.style.display = 'block';
        });
}

function displayConversationsList(conversations) {
    const container = document.getElementById('conversationsContent');
    container.innerHTML = '';
    
    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item';
        item.onclick = () => showActiveConversation(conv.id);
        
        const unreadBadge = conv.unread_count > 0 
            ? `<span class="gm-s-90a948">${conv.unread_count}</span>`
            : '';
        
        const lastMessage = conv.messages.length > 0 
            ? conv.messages[conv.messages.length - 1].message.substring(0, 50) + (conv.messages[conv.messages.length - 1].message.length > 50 ? '...' : '')
            : 'Aucun message';
        
        item.innerHTML = `
            <div class="gm-s-1c20bb">
                <div class="gm-s-c65e7b">
                    ${conv.buyer_name.charAt(0).toUpperCase()}
                </div>
                <div class="gm-s-ec2eba">
                    <h4 class="gm-s-0eb60b">${conv.buyer_name}</h4>
                    <p class="gm-s-61380d">
                        ${escapeHtml(lastMessage)}
                    </p>
                </div>
                ${unreadBadge}
            </div>
        `;
        
        container.appendChild(item);
    });
}

function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';
    
    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${msg.is_sender ? 'message-sent' : 'message-received'}`;
        messageDiv.style.display = 'flex';
        messageDiv.style.flexDirection = 'column';
        
        messageDiv.innerHTML = `
            <div class="gm-s-f069af">${escapeHtml(msg.message)}</div>
            <div class="gm-s-c199e1">
                ${msg.created_at}
            </div>
        `;
        
        container.appendChild(messageDiv);
    });
    
    // Scroll vers le bas
    container.scrollTop = container.scrollHeight;
}

function sendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || !currentProductId || !currentConversationId) return;
    
    const conversation = conversationsData.find(c => c.id === currentConversationId);
    if (!conversation) return;
    
    // Envoyer le message
    fetch(`/send-product-message/${currentProductId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            conversation_id: currentConversationId,
            buyer_id: conversation.buyer_id,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            // Recharger les conversations
            loadConversations(currentProductId);
            // Réafficher la conversation active
            setTimeout(() => showActiveConversation(currentConversationId), 300);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        if (typeof GMModal !== 'undefined') {
            GMModal.error('Erreur', 'Erreur lors de l\'envoi du message');
        } else {
            alert('Erreur lors de l\'envoi du message');
        }
    });
}

function markConversationAsRead(conversationId) {
    fetch(`/mark-conversation-read/${conversationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour le badge
            updateMessageBadges();
        }
    });
}

function updateMessageBadges() {
    // Les badges de messages non lus ne sont plus affichés sur cette page ; pas de rechargement pour éviter de fermer le popup.
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

let selectedBoostDuration = null;
let selectedBoostPrice = null;
let currentBoostProductId = null;

const BOOST_PRICES = {
    '24h': 500,
    '72h': 1200,
    '7d': 2500
};

const BOOST_DURATIONS = {
    '24h': '24 heures',
    '72h': '72 heures',
    '7d': '7 jours'
};

function openBoostModal(productId, productName) {
    currentBoostProductId = productId;
    const modal = document.getElementById('boostModal');
    const productNameEl = document.getElementById('boostProductName');
    const optionsContainer = document.getElementById('boostOptions');
    
    productNameEl.textContent = productName;
    
    // Générer les options de boost
    let html = '';
    for (const [duration, price] of Object.entries(BOOST_PRICES)) {
        html += `
            <div onclick="selectBoostDuration('${duration}', ${price})" id="boostOption_${duration}" class="gm-s-a6e0a1">
                <div class="gm-s-f38161">
                    <div>
                        <h4 class="gm-s-6a026e">${BOOST_DURATIONS[duration]}</h4>
                        <p class="gm-s-ce10c0">Mise en avant pendant ${BOOST_DURATIONS[duration]}</p>
                    </div>
                    <div class="gm-s-7851db">
                        <div class="gm-s-78ff43">${price.toLocaleString()}</div>
                        <div class="gm-s-7f67b5">FCFA</div>
                    </div>
                </div>
                <div class="gm-s-bcee33">
                    <div class="gm-s-ef5f97">
                        <i class="fi-rs-check"></i>
                        <span>Visibilité maximale</span>
                    </div>
                </div>
            </div>
        `;
    }
    optionsContainer.innerHTML = html;
    
    modal.style.display = 'flex';
    selectedBoostDuration = null;
    selectedBoostPrice = null;
    updateBoostButton();
}

function closeBoostModal() {
    document.getElementById('boostModal').style.display = 'none';
    selectedBoostDuration = null;
    selectedBoostPrice = null;
    currentBoostProductId = null;
}

function selectBoostDuration(duration, price) {
    selectedBoostDuration = duration;
    selectedBoostPrice = price;
    
    // Mettre à jour l'apparence des options
    document.querySelectorAll('[id^="boostOption_"]').forEach(el => {
        el.style.borderColor = '#E5E7EB';
        el.style.background = 'white';
    });
    
    const selectedEl = document.getElementById(`boostOption_${duration}`);
    if (selectedEl) {
        selectedEl.style.borderColor = '#10B981';
        selectedEl.style.background = '#F0FDF4';
    }
    
    updateBoostButton();
}

function updateBoostButton() {
    const btn = document.getElementById('confirmBoostBtn');
    if (selectedBoostDuration && selectedBoostPrice) {
        btn.disabled = false;
        btn.style.background = 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
        btn.style.cursor = 'pointer';
        btn.innerHTML = `<i class="fi-rs-credit-card"></i> Payer ${selectedBoostPrice.toLocaleString()} FCFA`;
    } else {
        btn.disabled = true;
        btn.style.background = '#D1D5DB';
        btn.style.cursor = 'not-allowed';
        btn.innerHTML = '<i class="fi-rs-credit-card"></i> Procéder au paiement';
    }
}

async function confirmBoost() {
    if (!selectedBoostDuration || !currentBoostProductId) {
        GMModal.warning('Attention', 'Veuillez sélectionner une durée de boost');
        return;
    }
    
    GMModal.show({
        type: 'confirm',
        title: 'Confirmer le boost',
        message: `Vous allez booster votre article pendant <strong>${BOOST_DURATIONS[selectedBoostDuration]}</strong> pour <strong>${selectedBoostPrice.toLocaleString()} FCFA</strong>.<br><br>Vous serez redirigé vers le paiement.`,
        showCancel: true,
        confirmText: 'Confirmer',
        cancelText: 'Annuler',
        onConfirm: async function() {
            try {
                // Désactiver le bouton pendant le traitement
                const btn = document.getElementById('confirmBoostBtn');
                btn.disabled = true;
                btn.innerHTML = '<i class="fi-rs-spinner gm-s-6f8b10" ></i> Traitement...';
                
                const response = await fetch(`/c2c/boost/${currentBoostProductId}/purchase/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        duration: selectedBoostDuration
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Rediriger vers la page de paiement
                    if (data.payment_url) {
                        if (typeof window.openSingPayPaymentModal === 'function') {
                            window.openSingPayPaymentModal(data.payment_url, { title: 'Paiement boost SingPay' });
                        } else {
                            window.location.href = data.payment_url;
                        }
                    } else {
                        GMModal.success('Boost activé !', data.message || 'Votre boost a été activé avec succès !', () => {
                            location.reload();
                        });
                    }
                } else {
                    btn.disabled = false;
                    updateBoostButton();
                    GMModal.error('Erreur', data.error || 'Erreur lors de l\'activation du boost');
                }
            } catch (error) {
                console.error('Erreur:', error);
                const btn = document.getElementById('confirmBoostBtn');
                btn.disabled = false;
                updateBoostButton();
                GMModal.error('Erreur', 'Erreur lors de l\'activation du boost');
            }
        }
    });
}

// Fermer la modal en cliquant en dehors
document.getElementById('boostModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeBoostModal();
    }
});
