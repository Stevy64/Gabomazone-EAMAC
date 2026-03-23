// Fonction pour ouvrir le modal de détails de l'avis
    function openReviewDetailsModal(reviewId) {
        const reviewItem = document.querySelector(`[data-review-id="${reviewId}"]`);
        if (!reviewItem) return;
        
        const modal = document.getElementById('reviewDetailsModal');
        const content = document.getElementById('reviewDetailsContent');
        
        if (!modal || !content) return;
        
        // Récupérer les données depuis les attributs data
        const clientName = reviewItem.getAttribute('data-review-client') || 'Client';
        const date = reviewItem.getAttribute('data-review-date') || '';
        const rate = parseInt(reviewItem.getAttribute('data-review-rate')) || 0;
        const comment = reviewItem.getAttribute('data-review-comment') || '';
        const productName = reviewItem.getAttribute('data-review-product-name') || '';
        const productSlug = reviewItem.getAttribute('data-review-product-slug') || '';
        const productImage = reviewItem.getAttribute('data-review-product-image') || '';
        
        // Calculer le pourcentage pour les étoiles
        const ratingPercent = rate * 20;
        
        // Construire le HTML du rating avec mise en valeur
        let ratingSectionHTML = '';
        if (rate > 0) {
            ratingSectionHTML = `
                <div class="review-details-rating-section">
                    <p class="review-details-rating-label">
                        <i class="fas fa-star"></i>
                        Note attribuée
                    </p>
                    <div class="review-details-rating">
                        <div class="stars-container-large">
                            <div class="stars-background-large">
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                            </div>
                            <div class="stars-fill-large gm-s-488ed7" >
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                                <i class="fas fa-star"></i>
                            </div>
                        </div>
                        <span class="rating-value-large">${rate}/5</span>
                    </div>
                </div>
            `;
        } else {
            ratingSectionHTML = `
                <div class="review-details-rating-section gm-s-569cc7" >
                    <p class="review-details-rating-label gm-s-ffe680" >
                        <i class="far fa-star"></i>
                        Aucune note
                    </p>
                </div>
            `;
        }
        
        const commentHTML = comment 
            ? `<p class="review-details-comment-text">${comment}</p>`
            : `<p class="review-details-comment-empty">Aucun commentaire</p>`;
        
        const productImageHTML = productImage 
            ? `<img src="${productImage}" alt="${productName}" class="review-details-product-image" />`
            : '';
        
        // Construire l'URL du produit
        const productLink = productSlug 
            ? `/product-details/${productSlug}/`
            : '#';
        
        content.innerHTML = `
            <div class="review-details-card">
                <div class="review-details-header">
                    <div class="review-details-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="review-details-user">
                        <h3 class="review-details-user-name">${clientName}</h3>
                        <p class="review-details-date">
                            <i class="far fa-clock"></i>
                            ${date}
                        </p>
                    </div>
                </div>
                
                ${ratingSectionHTML}
                
                <div class="review-details-product">
                    <div class="review-details-product-header">
                        <i class="fas fa-boxes-stacked"></i>
                        <div class="review-details-product-content">
                            <p class="review-details-product-label">Produit évalué</p>
                            <h4 class="review-details-product-name">${productName}</h4>
                            ${productImageHTML}
                            <a href="${productLink}" target="_blank" class="review-details-product-link">
                                <i class="fas fa-eye"></i>
                                Voir le produit
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="review-details-comment">
                    <h4 class="review-details-comment-label">
                        <i class="fas fa-comment"></i>
                        Commentaire du client
                    </h4>
                    ${commentHTML}
                </div>
                
                <div class="review-details-footer">
                    <span class="review-details-id">ID Avis: #${reviewId}</span>
                </div>
            </div>
        `;
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    // Fonction pour fermer le modal
    function closeReviewDetailsModal() {
        const modal = document.getElementById('reviewDetailsModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    
    // Fermer le modal en cliquant sur l'overlay
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('reviewDetailsModal');
        if (modal && e.target === modal) {
            closeReviewDetailsModal();
        }
    });
    
    // Fermer le modal avec la touche Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeReviewDetailsModal();
        }
    });
