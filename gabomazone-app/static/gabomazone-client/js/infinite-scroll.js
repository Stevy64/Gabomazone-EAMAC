/* ============================================
   INFINITE SCROLL + LAZY LOADING
   Défilement infini comme un réseau social
   ============================================ */

(function() {
    'use strict';
    
    // DÉSACTIVÉ : Ce fichier est désactivé car HTMX gère maintenant le scroll infini
    // Toutes les fonctionnalités sont gérées par HTMX via product_list_partial.html
    // Ce fichier est conservé uniquement pour le lazy loading des images
    
    // Vérifier si on est sur une page avec products-list (shop page)
    const productsContainer = document.getElementById('products-list');
    if (!productsContainer) {
        // Si pas de products-list, on peut quand même activer le lazy loading des images
        // mais on sort pour éviter d'exécuter le reste du code
        return;
    }
    
    // DÉSACTIVER TOUTES LES FONCTIONNALITÉS DE SCROLL INFINI
    // HTMX gère maintenant tout cela
    let isLoading = false;
    let hasMore = false; // Désactivé
    let currentPage = 1;
    let productsPerPage = 10;
    let orderBy = '-date';
    
    const spinnerBox = document.getElementById('spinner-box');
    const emptyBox = document.getElementById('empty-box');
    const loadingBox = document.getElementById('loading-box');
    const productNum = document.getElementById('product-num');
    const sortSelect = document.getElementById('mySelect');
    
    // Observer pour le lazy loading des images
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    const tempImg = new Image();
                    tempImg.onload = function() {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    };
                    tempImg.onerror = function() {
                        img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="220"%3E%3Crect width="300" height="220" fill="%23F3F4F6"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%239CA3AF" font-family="sans-serif" font-size="14"%3EImage non disponible%3C/text%3E%3C/svg%3E';
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    };
                    tempImg.src = img.dataset.src;
                }
            }
        });
    }, {
        rootMargin: '100px'
    });
    
    // Observer pour le infinite scroll - DÉSACTIVÉ car HTMX gère maintenant le scroll infini
    // Le scrollObserver n'est plus nécessaire car HTMX utilise hx-trigger="revealed" dans le template
    const scrollObserver = null; // Désactivé
    
    // Créer un élément sentinelle pour détecter le scroll - DÉSACTIVÉ
    // HTMX gère maintenant le scroll infini via hx-trigger="revealed" dans product_list_partial.html
    const sentinel = null; // Désactivé
    
    // Fonction pour créer une carte produit avec lazy loading
    // Fonction pour formater un prix avec des espaces
    function formatPrice(priceValue) {
        const price = parseFloat(priceValue || 0);
        const intPrice = Math.floor(price);
        return intPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }

    function createProductCard(product) {
        const price = formatPrice(product.PRDPrice || 0);
        const discountPrice = product.PRDDiscountPrice > 0 ? formatPrice(product.PRDDiscountPrice) : null;
        const viewCount = product.view_count || 0;
        const productName = product.product_name || 'Produit sans nom';
        const productSlug = product.PRDSlug || '';
        const productImage = product.product_image || '';
        
        const card = document.createElement('div');
        card.className = 'flavoriz-product-card';
        card.style.cursor = 'pointer';
        card.onclick = () => window.location.href = `/product-details/${productSlug}`;
        
        // Image placeholder pour le lazy loading
        const placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="220"%3E%3Crect width="300" height="220" fill="%23F3F4F6"/%3E%3C/svg%3E';
        
        // Détecter si on est sur mobile
        const isMobile = window.innerWidth <= 768;
        const imageHeight = isMobile ? '120px' : '160px';
        const titleSize = isMobile ? '11px' : '14px';
        const titleMinHeight = isMobile ? '28px' : '40px';
        const bodyPadding = isMobile ? '6px 8px' : '10px 12px';
        const priceSize = isMobile ? '12px' : '15px';
        const buttonPadding = isMobile ? '6px' : '10px';
        const buttonFontSize = isMobile ? '9px' : '12px';
        const viewsSize = isMobile ? '8px' : '11px';
        
        // Formatage du nombre de vues
        const formattedViews = viewCount > 0 ? viewCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '0';
        
        card.innerHTML = `
            <div style="position: relative; overflow: hidden; background: #FAFAFA; width: 100%; height: ${imageHeight};">
                <img data-src="/media/${productImage}" src="${placeholder}" alt="${productName}" class="flavoriz-product-image lazy-load" style="height: 100%; width: 100%; object-fit: cover;" />
                ${viewCount > 0 ? `
                <div style="position: absolute; bottom: 8px; left: 8px; background: rgba(0, 0, 0, 0.6); color: white; padding: 4px 8px; border-radius: 12px; font-size: ${viewsSize}; font-weight: 600; display: flex; align-items: center; gap: 4px; backdrop-filter: blur(4px); z-index: 10;">
                    <i class="fi-rs-eye" style="font-size: ${isMobile ? '10px' : '11px'};"></i>
                    <span>${formattedViews}</span>
                </div>
                ` : ''}
            </div>
            <div class="flavoriz-product-body" style="padding: ${bodyPadding};">
                <h3 class="flavoriz-product-title" style="font-size: ${titleSize}; font-weight: 700; margin-bottom: ${isMobile ? '6px' : '8px'}; line-height: 1.2; min-height: ${titleMinHeight}; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${productName}</h3>
                <div style="display: flex; align-items: center; gap: 4px; margin-bottom: ${isMobile ? '8px' : '10px'}; flex-wrap: wrap;">
                    <span style="font-size: ${priceSize}; font-weight: 700; color: #FF7B2C;">${price} FCFA</span>
                    ${discountPrice ? `<span style="font-size: ${isMobile ? '10px' : '12px'}; color: #9CA3AF; text-decoration: line-through;">${discountPrice} FCFA</span>` : ''}
                </div>
                <button class="flavoriz-product-card-btn" onclick="event.stopPropagation(); window.location.href='/product-details/${productSlug}'" style="padding: ${buttonPadding}; font-size: ${buttonFontSize}; margin-top: 0; width: 100%; background: #1A1A1A; color: white; border: none; border-radius: ${isMobile ? '10px' : '12px'}; font-weight: 600; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 3px;">
                    <i class="fi-rs-eye" style="font-size: ${isMobile ? '11px' : '13px'};"></i>
                    <span>Voir</span>
                </button>
            </div>
        `;
        
        // Observer l'image pour le lazy loading
        const img = card.querySelector('img');
        if (img) {
            imageObserver.observe(img);
        }
        
        return card;
    }
    
    // Fonction pour charger plus de produits
    // DÉSACTIVÉ COMPLÈTEMENT : Le scroll infini est maintenant géré par HTMX
    function loadMoreProducts() {
        // HTMX gère maintenant le scroll infini via product_list_partial.html
        // Cette fonction est complètement désactivée pour éviter les conflits
        // Ne rien faire - retourner immédiatement
        return;
    }
    
    /* ANCIEN CODE COMPLÈTEMENT DÉSACTIVÉ - CONSERVÉ POUR RÉFÉRENCE UNIQUEMENT
    function loadMoreProductsOld() {
        if (isLoading || !hasMore) return;
        
        isLoading = true;
        if (spinnerBox) spinnerBox.classList.remove('not-visible');
        if (loadingBox) loadingBox.classList.add('not-visible');
        
        const upper = currentPage * productsPerPage;
        
        fetch(`/shop-ajax/?num_products=${upper}&order_by=${orderBy}&CAT_id=&cat_type=all`)
            .then(response => response.json())
            .then(data => {
                setTimeout(() => {
                    if (spinnerBox) spinnerBox.classList.add('not-visible');
                    
                    if (data.products_size > 0 && productNum) {
                        productNum.innerHTML = `<p style="margin: 0;">Nous avons trouvé <strong>${data.products_size}</strong> articles pour vous !</p>`;
                    }
                    
                    if (data.data && data.data.length > 0) {
                        data.data.forEach(product => {
                            const card = createProductCard(product);
                            productsContainer.appendChild(card);
                        });
                        
                        currentPage++;
                        hasMore = !data.max;
                        
                        // Réajouter le sentinel à la fin
                        if (sentinel && sentinel.parentNode) {
                            sentinel.parentNode.removeChild(sentinel);
                        }
                        if (sentinel) {
                            productsContainer.appendChild(sentinel);
                        }
                        
                        if (hasMore && scrollObserver) {
                            scrollObserver.observe(sentinel);
                        } else {
                            if (emptyBox) {
                                emptyBox.classList.remove('not-visible');
                                emptyBox.innerHTML = `<p style="font-size: 14px; font-weight: 600; color: #6B7280;">Tous les produits ont été chargés !</p>`;
                            }
                        }
                    } else {
                        hasMore = false;
                        if (emptyBox) {
                            emptyBox.classList.remove('not-visible');
                            emptyBox.innerHTML = `<p style="font-size: 14px; font-weight: 600; color: #6B7280;">Aucun produit disponible.</p>`;
                        }
                    }
                    
                    isLoading = false;
                }, 300);
            })
            .catch(error => {
                console.error('Erreur lors du chargement:', error);
                isLoading = false;
                if (spinnerBox) spinnerBox.classList.add('not-visible');
                if (loadingBox) loadingBox.classList.remove('not-visible');
            });
    }
    */
    
    // Initialiser le chargement
    // DÉSACTIVÉ : HTMX gère maintenant le chargement initial
    function init() {
        // HTMX charge les produits automatiquement via hx-trigger="load"
        // Plus besoin d'appeler loadMoreProducts() ici
        return;
        
        /* ANCIEN CODE DÉSACTIVÉ
        // Charger les premiers produits
        loadMoreProducts();
        
        // Écouter les changements de tri
        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                orderBy = this.value;
                currentPage = 1;
                hasMore = true;
                isLoading = false;
                productsContainer.innerHTML = '';
                if (emptyBox) emptyBox.classList.add('not-visible');
                if (sentinel.parentNode) {
                    sentinel.parentNode.removeChild(sentinel);
                }
                loadMoreProducts();
            });
        }
        // FIN DU COMMENTAIRE */
    }
    
    // DÉSACTIVÉ : HTMX gère maintenant l'initialisation
    // Plus besoin d'appeler init() car HTMX charge automatiquement les produits
    /*
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    */
})();
