// Fonction pour afficher les détails de transaction (surcharge si nécessaire)
    if (typeof window.showTransactionDetails === 'undefined') {
        window.showTransactionDetails = function(transactionId) {
            const modal = document.getElementById('transaction-modal');
            if (modal) {
                modal.style.display = 'flex';
                const stepsContainer = document.getElementById('transaction-steps');
                if (stepsContainer) {
                    stepsContainer.innerHTML = '<div class="gm-s-9fcb89"><div class="gm-s-efbd1e"></div><p class="gm-s-463ca0">Chargement...</p></div>';
                }
            }
            
            fetch(`/payments/singpay/details/${transactionId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Utiliser la fonction de orders.js si disponible
                        if (typeof displayTransactionSteps !== 'undefined') {
                            displayTransactionSteps(data);
                        } else {
                            // Implémentation inline
                            const stepsContainer = document.getElementById('transaction-steps');
                            const transaction = data.transaction;
                            const steps = data.steps;
                            
                            let stepsHTML = '<div style="padding: 24px;">';
                            stepsHTML += `
                                <div class="gm-s-d0011b">
                                    <h3 class="gm-s-86e044">Détails de la transaction</h3>
                                    <div class="gm-s-e501d2">
                                        <div>
                                            <span class="gm-s-ffe680">Transaction ID:</span>
                                            <strong class="gm-s-692717">${transaction.transaction_id}</strong>
                                        </div>
                                        <div>
                                            <span class="gm-s-ffe680">Montant:</span>
                                            <strong class="gm-s-1fb6a7">${parseFloat(transaction.amount).toLocaleString('fr-FR')} ${transaction.currency}</strong>
                                        </div>
                                        <div>
                                            <span class="gm-s-ffe680">Méthode:</span>
                                            <strong class="gm-s-7e72ca">${transaction.payment_method}</strong>
                                        </div>
                                        <div>
                                            <span class="gm-s-ffe680">Statut:</span>
                                            <span class="gm-s-b72e06">${transaction.status_display}</span>
                                        </div>
                                    </div>
                                </div>
                                <h4 class="gm-s-b8a0fa">Évolution de la transaction</h4>
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
                                
                                let statusIcon = step.icon || 'fi-rs-circle';
                                let statusColor = '#9CA3AF';
                                let statusBg = '#F3F4F6';
                                
                                if (stepStatus === 'completed') {
                                    statusColor = '#10B981';
                                    statusBg = '#D1FAE5';
                                    statusIcon = 'fi-rs-check';
                                } else if (stepStatus === 'active') {
                                    statusColor = '#3B82F6';
                                    statusBg = '#DBEAFE';
                                    statusIcon = 'fi-rs-clock';
                                } else if (stepStatus === 'failed') {
                                    statusColor = '#EF4444';
                                    statusBg = '#FEE2E2';
                                    statusIcon = 'fi-rs-cross';
                                }
                                
                                let lineColor = '#E5E7EB';
                                if (stepStatus === 'completed' && !isLast) {
                                    lineColor = '#10B981';
                                } else if (stepStatus === 'active' && !isLast) {
                                    lineColor = '#3B82F6';
                                }
                                
                                stepsHTML += `
                                    <div class="gm-s-99e576">
                                        ${!isLast ? `<div class="gm-s-aa5de8"></div>` : ''}
                                        <div class="gm-s-631666">
                                            <i class="${statusIcon} gm-s-1551e6" ></i>
                                        </div>
                                        <div class="gm-s-9ea7fd">
                                            <div class="gm-s-4fa42d">${step.name}</div>
                                            <div class="gm-s-9423bd">${step.description}</div>
                                            ${stepDate ? `<div class="gm-s-5216bc"><i class="fi-rs-calendar gm-s-345895" ></i>${stepDate}</div>` : ''}
                                        </div>
                                    </div>
                                `;
                            });
                            
                            stepsHTML += '</div>';
                            if (stepsContainer) {
                                stepsContainer.innerHTML = stepsHTML;
                            }
                        }
                    } else {
                        if (typeof GMModal !== 'undefined') {
                            GMModal.error('Erreur', 'Erreur lors du chargement des détails de la transaction');
                        } else {
                            alert('Erreur lors du chargement des détails de la transaction');
                        }
                        if (modal) modal.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (typeof GMModal !== 'undefined') {
                        GMModal.error('Erreur', 'Erreur lors du chargement des détails de la transaction');
                    } else {
                        alert('Erreur lors du chargement des détails de la transaction');
                    }
                    if (modal) modal.style.display = 'none';
                });
        };
    }
    
    // Fermer la modal en cliquant sur l'overlay
    document.addEventListener('DOMContentLoaded', function() {
        const modal = document.getElementById('transaction-modal');
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.style.display = 'none';
                }
            });
        }
    });
