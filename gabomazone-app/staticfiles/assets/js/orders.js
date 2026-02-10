window.onload = function () {
    const ordersList = document.getElementById("orders-list");
    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box") || document.getElementById("empty");
    const loadsBox = document.getElementById("loading-box");
    const orderNum = document.getElementById("order-number");
    const empty = document.getElementById("empty");
    
    // Vérifier que tous les éléments existent
    if (!ordersList || !spinnerBox || !loadsBox) {
        console.error("Éléments DOM manquants pour la liste des commandes");
        return;
    }

    let visible = 10;
    
    // Fonction pour formater le prix
    function formatPrice(amount) {
        if (!amount) return '0';
        const num = parseFloat(amount);
        if (isNaN(num)) return '0';
        return Math.round(num).toLocaleString('fr-FR');
    }
    
    // Fonction pour traduire le statut
    function translateStatus(status) {
        const statusMap = {
            'PENDING': 'En attente',
            'Underway': 'En cours',
            'COMPLETE': 'Terminée',
            'Refunded': 'Remboursée',
            'En attente': 'En attente',
            'En cours': 'En cours',
            'Terminée': 'Terminée',
            'Remboursée': 'Remboursée'
        };
        return statusMap[status] || status || 'En attente';
    }
    
    // Fonction pour obtenir la classe CSS du statut
    function getStatusClass(status) {
        const classMap = {
            'PENDING': 'status-pending',
            'Underway': 'status-underway',
            'COMPLETE': 'status-complete',
            'Refunded': 'status-refunded',
            'En attente': 'status-pending',
            'En cours': 'status-underway',
            'Terminée': 'status-complete',
            'Remboursée': 'status-refunded'
        };
        // Si le statut n'est pas dans la map, essayer de le mapper
        if (!classMap[status]) {
            if (status && status.toLowerCase().includes('pending') || status && status.toLowerCase().includes('attente')) {
                return 'status-pending';
            } else if (status && status.toLowerCase().includes('underway') || status && status.toLowerCase().includes('cours')) {
                return 'status-underway';
            } else if (status && status.toLowerCase().includes('complete') || status && status.toLowerCase().includes('terminée')) {
                return 'status-complete';
            } else if (status && status.toLowerCase().includes('refunded') || status && status.toLowerCase().includes('remboursée')) {
                return 'status-refunded';
            }
        }
        return classMap[status] || 'status-pending';
    }
    
    const handleGetOrders = () => {
        $.ajax({
            type: "GET",
            url: `/orders-ajax/`,
            data: {
                "num_products": visible,
            },
            success: function (response) {
                const data = response.data;
                const maxSize = response.max;
                
                // Vérifier que les éléments existent avant de manipuler leur classList
                if (emptyBox) emptyBox.classList.add("not-visible");
                if (spinnerBox) spinnerBox.classList.remove("not-visible");
                if (loadsBox) loadsBox.classList.add("not-visible");

                setTimeout(() => {
                    if (spinnerBox) spinnerBox.classList.add("not-visible");
                    if (loadsBox) loadsBox.classList.remove("not-visible");

                    if (response.orders_size > 0) {
                        if (orderNum) {
                            orderNum.innerHTML = `Mes commandes (${response.orders_size})`;
                        }
                        
                        // Vider la liste avant de la remplir
                        ordersList.innerHTML = '';

                        data.forEach(order => {
                            const orderDate = order.order_date ? new Date(order.order_date) : new Date();
                            const formattedDate = orderDate.toLocaleDateString('fr-FR', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            });
                            const formattedAmount = formatPrice(order.amount);
                            const itemsCount = order.items_count || 0;
                            const statusText = order.status_display || translateStatus(order.status);
                            const statusClass = getStatusClass(order.status);
                            
                            // Déterminer les couleurs selon le statut
                            let statusBg = '#FEF3C7';
                            let statusColor = '#92400E';
                            if (statusClass === 'status-complete') {
                                statusBg = '#D1FAE5';
                                statusColor = '#065F46';
                            } else if (statusClass === 'status-underway') {
                                statusBg = '#DBEAFE';
                                statusColor = '#1E40AF';
                            } else if (statusClass === 'status-refunded') {
                                statusBg = '#FEE2E2';
                                statusColor = '#991B1B';
                            }
                            
                            const itemText = itemsCount === 1 ? 'article' : 'articles';
                            
                            // Bouton pour voir les détails de transaction si disponible
                            const isMobile = window.innerWidth <= 768;
                            let transactionButton = '';
                            if (order.has_transaction && order.transaction_id) {
                                transactionButton = `
                                    <button onclick="showTransactionDetails('${order.transaction_id}')" style="flex: 1; min-width: 120px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: ${isMobile ? '12px 16px' : '8px 16px'}; background: #10B981; color: white; border: none; border-radius: ${isMobile ? '10px' : '8px'}; font-size: ${isMobile ? '14px' : '13px'}; font-weight: 600; cursor: pointer; transition: all 0.2s ease; ${isMobile ? '' : 'margin-right: 8px;'} box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);" title="Voir les étapes de paiement">
                                        <i class="fi-rs-credit-card" style="font-size: ${isMobile ? '16px' : '14px'};"></i>
                                        Paiement
                                    </button>
                                `;
                            }
                            
                            // Utiliser isMobile déjà déclaré plus haut
                            if (isMobile) {
                                // Format carte pour mobile
                                ordersList.innerHTML += `
                                    <tr class="mobile-order-card">
                                        <td colspan="5" style="padding: 0 !important; border: none !important;">
                                            <div class="order-card-mobile" style="background: white; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border: 1px solid #E5E7EB;">
                                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                                                    <div>
                                                        <div style="font-size: 18px; font-weight: 700; color: var(--color-orange); margin-bottom: 4px;">#${order.id}</div>
                                                        <div style="font-size: 13px; color: #6B7280;">${formattedDate}</div>
                                                    </div>
                                                    <span class="${statusClass}" style="display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; background: ${statusBg}; color: ${statusColor}; white-space: nowrap;">
                                                        ${statusText}
                                                    </span>
                                                </div>
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 12px; background: #F9FAFB; border-radius: 10px;">
                                                    <div>
                                                        <div style="font-size: 16px; font-weight: 700; color: #1F2937;">${formattedAmount} FCFA</div>
                                                        <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">${itemsCount} ${itemText}</div>
                                                    </div>
                                                </div>
                                                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                                    ${transactionButton}
                                                    <a href="/dashboard/order/${order.id}/" style="flex: 1; min-width: 120px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 12px 16px; background: var(--color-orange); color: white; border-radius: 10px; font-size: 14px; font-weight: 600; text-decoration: none; transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(255, 123, 44, 0.3);">
                                                        <i class="fi-rs-eye" style="font-size: 16px;"></i>
                                                        Voir
                                                    </a>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `;
                            } else {
                                // Format table pour desktop
                                ordersList.innerHTML += `
                                    <tr>
                                        <td style="font-weight: 600; color: var(--color-orange);">#${order.id}</td>
                                        <td>${formattedDate}</td>
                                        <td><strong>${formattedAmount} FCFA</strong><br><small style="color: #6B7280; font-size: 12px;">${itemsCount} ${itemText}</small></td>
                                        <td><span class="${statusClass}" style="display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; background: ${statusBg}; color: ${statusColor};">
                                            ${statusText}
                                        </span></td>
                                        <td style="text-align: center;">
                                            ${transactionButton}
                                        <a href="/dashboard/order/${order.id}/" style="display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; background: var(--color-orange); color: white; border-radius: 8px; font-size: 13px; font-weight: 600; text-decoration: none; transition: all 0.2s ease;">
                                            <i class="fi-rs-eye" style="font-size: 14px;"></i>
                                            Voir
                                        </a>
                                        </td>
                                    </tr>
                                `;
                            }
                        });
                        
                        if (maxSize) {
                            if (loadsBox) loadsBox.classList.add("not-visible");
                            if (emptyBox) {
                                emptyBox.classList.remove("not-visible");
                                emptyBox.innerHTML = `<strong style="color: var(--color-orange); font-size: 15px;">Plus de commandes à afficher</strong>`;
                            }
                        }
                    } else {
                        if (orderNum) {
                            orderNum.innerHTML = `Mes commandes (0)`;
                        }
                        if (ordersList) ordersList.innerHTML = ``;
                        if (empty) empty.classList.remove("not-visible");
                        if (loadsBox) loadsBox.classList.add("not-visible");
                    }
                }, 500);
            },
            error: function (error) {
                console.error('Erreur lors du chargement des commandes:', error);
                if (spinnerBox) spinnerBox.classList.add("not-visible");
                if (loadsBox) loadsBox.classList.add("not-visible");
                if (empty) {
                    empty.classList.remove("not-visible");
                }
            }
        });
    };
    
    handleGetOrders();
    
    if (loadBtn) {
        loadBtn.addEventListener("click", () => {
            visible += 10;
            handleGetOrders();
        });
    }
    
    // Recharger les commandes lors du redimensionnement pour adapter l'affichage mobile/desktop
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            // Recharger seulement si on a déjà des commandes affichées
            if (ordersList && ordersList.innerHTML.trim() !== '') {
                const currentVisible = visible;
                visible = 10;
                handleGetOrders();
                visible = currentVisible;
            }
        }, 300);
    });
    
    // Fonction pour afficher les détails de transaction
    window.showTransactionDetails = function(transactionId) {
        // Afficher un loader
        const modal = document.getElementById('transaction-modal');
        if (modal) {
            modal.style.display = 'flex';
            document.getElementById('transaction-steps').innerHTML = '<div style="text-align: center; padding: 40px;"><div class="flavoriz-spinner"></div><p style="margin-top: 16px; color: #6B7280;">Chargement...</p></div>';
        }
        
        // Récupérer les détails de la transaction
        fetch(`/payments/singpay/details/${transactionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayTransactionSteps(data);
                } else {
                    alert('Erreur lors du chargement des détails de la transaction');
                    if (modal) modal.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Erreur lors du chargement des détails de la transaction');
                if (modal) modal.style.display = 'none';
            });
    };
    
    // Fonction pour afficher les étapes de transaction
    function displayTransactionSteps(data) {
        const stepsContainer = document.getElementById('transaction-steps');
        const transaction = data.transaction;
        const steps = data.steps;
        
        let stepsHTML = '<div style="padding: 24px;">';
        stepsHTML += `
            <div style="margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #E5E7EB;">
                <h3 style="font-size: 20px; font-weight: 700; color: #1F2937; margin: 0 0 12px 0;">Détails de la transaction</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; font-size: 14px;">
                    <div>
                        <span style="color: #6B7280;">Transaction ID:</span>
                        <strong style="color: #1F2937; margin-left: 8px;">${transaction.transaction_id}</strong>
                    </div>
                    <div>
                        <span style="color: #6B7280;">Montant:</span>
                        <strong style="color: var(--color-orange); margin-left: 8px;">${transaction.amount} ${transaction.currency}</strong>
                    </div>
                    <div>
                        <span style="color: #6B7280;">Méthode:</span>
                        <strong style="color: #1F2937; margin-left: 8px;">${transaction.payment_method}</strong>
                    </div>
                    <div>
                        <span style="color: #6B7280;">Statut:</span>
                        <span style="padding: 4px 10px; background: ${transaction.status === 'success' ? '#D1FAE5' : transaction.status === 'pending' ? '#FEF3C7' : '#FEE2E2'}; color: ${transaction.status === 'success' ? '#065F46' : transaction.status === 'pending' ? '#92400E' : '#991B1B'}; border-radius: 6px; font-size: 12px; font-weight: 600; margin-left: 8px;">${transaction.status_display}</span>
                    </div>
                </div>
            </div>
            <h4 style="font-size: 16px; font-weight: 700; color: #1F2937; margin: 0 0 20px 0;">Évolution de la transaction</h4>
        `;
        
        steps.forEach((step, index) => {
            const isLast = index === steps.length - 1;
            const stepStatus = step.status;
            const stepDate = step.date ? new Date(step.date).toLocaleString('fr-FR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : null;
            
            // Utiliser l'icône du modèle si disponible, sinon déterminer selon le statut
            let statusIcon = step.icon || 'fi-rs-circle';
            
            // Déterminer les couleurs et animations selon le statut
            let statusColor = '#9CA3AF';
            let statusBg = '#F3F4F6';
            let animationClass = '';
            let pulseAnimation = '';
            
            if (stepStatus === 'completed') {
                statusColor = '#10B981';
                statusBg = '#D1FAE5';
                animationClass = 'step-completed';
            } else if (stepStatus === 'active') {
                statusColor = '#3B82F6';
                statusBg = '#DBEAFE';
                animationClass = 'step-active';
                pulseAnimation = 'step-pulse';
            } else if (stepStatus === 'failed') {
                statusColor = '#EF4444';
                statusBg = '#FEE2E2';
                animationClass = 'step-failed';
            } else if (stepStatus === 'cancelled') {
                statusColor = '#F59E0B';
                statusBg = '#FEF3C7';
                animationClass = 'step-cancelled';
            } else {
                // pending
                statusColor = '#9CA3AF';
                statusBg = '#F3F4F6';
                animationClass = 'step-pending';
            }
            
            // Déterminer la couleur de la ligne de connexion
            let lineColor = '#E5E7EB';
            if (stepStatus === 'completed' && !isLast) {
                // Si l'étape est complétée, la ligne jusqu'à la suivante est verte
                lineColor = '#10B981';
            } else if (stepStatus === 'active' && !isLast) {
                // Si l'étape est active, la ligne est bleue
                lineColor = '#3B82F6';
            }
            
            stepsHTML += `
                <div class="transaction-step ${animationClass}" style="display: flex; gap: 16px; margin-bottom: ${isLast ? '0' : '24px'}; position: relative; opacity: 0; animation: fadeInUp 0.5s ease-out ${index * 0.1}s forwards;">
                    ${!isLast ? `<div class="step-connector" style="position: absolute; left: 24px; top: 48px; width: 2px; height: 40px; background: ${lineColor}; transition: all 0.3s ease; z-index: 0;"></div>` : ''}
                    <div class="step-icon ${pulseAnimation}" style="width: 48px; height: 48px; border-radius: 50%; background: ${statusBg}; color: ${statusColor}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; z-index: 1; border: 2px solid ${statusColor}; box-shadow: 0 4px 12px ${statusColor}40; transition: all 0.3s ease; position: relative;">
                        <i class="${statusIcon}" style="font-size: 24px;"></i>
                    </div>
                    <div style="flex: 1; padding-top: 4px;">
                        <div style="font-size: 16px; font-weight: 700; color: #1F2937; margin-bottom: 6px;">${step.name}</div>
                        <div style="font-size: 14px; color: #6B7280; margin-bottom: 6px; line-height: 1.5;">${step.description}</div>
                        ${stepDate ? `<div style="font-size: 12px; color: #9CA3AF; display: flex; align-items: center; gap: 6px; margin-top: 4px;"><i class="fi-rs-calendar" style="font-size: 12px;"></i>${stepDate}</div>` : ''}
                    </div>
                </div>
            `;
        });
        
        stepsHTML += '</div>';
        stepsContainer.innerHTML = stepsHTML;
        
        // Ajouter les styles d'animation si pas déjà présents
        if (!document.getElementById('transaction-steps-styles')) {
            const styleSheet = document.createElement('style');
            styleSheet.id = 'transaction-steps-styles';
            styleSheet.textContent = `
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
                    }
                    50% {
                        transform: scale(1.05);
                        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
                    }
                }
                
                @keyframes checkmark {
                    0% {
                        transform: scale(0);
                    }
                    50% {
                        transform: scale(1.2);
                    }
                    100% {
                        transform: scale(1);
                    }
                }
                
                .transaction-step.step-completed .step-icon {
                    animation: checkmark 0.5s ease-out;
                }
                
                .transaction-step.step-active .step-icon {
                    animation: pulse 2s ease-in-out infinite;
                }
                
                .transaction-step.step-pending .step-icon {
                    opacity: 0.6;
                }
                
                .transaction-step.step-failed .step-icon {
                    animation: shake 0.5s ease-out;
                }
                
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-5px); }
                    75% { transform: translateX(5px); }
                }
                
                .step-connector {
                    transition: background-color 0.5s ease;
                }
            `;
            document.head.appendChild(styleSheet);
        }
    }
};