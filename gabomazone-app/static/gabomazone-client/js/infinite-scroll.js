/* ============================================
   INFINITE SCROLL + LAZY LOADING
   Défilement infini comme un réseau social
   ============================================ */

(function() {
    'use strict';
    
    let isLoading = false;
    let hasMore = true;
    let currentPage = 1;
    let productsPerPage = 10;
    let orderBy = '-date';
    
    const productsContainer = document.getElementById('products-list');
    const spinnerBox = document.getElementById('spinner-box');
    const emptyBox = document.getElementById('empty-box');
    const loadingBox = document.getElementById('loading-box');
    const productNum = document.getElementById('product-num');
    const sortSelect = document.getElementById('mySelect');
    
    if (!productsContainer) return;
    
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
    
    // Observer pour le infinite scroll
    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && hasMore && !isLoading) {
                loadMoreProducts();
            }
        });
    }, {
        rootMargin: '200px'
    });
    
    // Créer un élément sentinelle pour détecter le scroll
    const sentinel = document.createElement('div');
    sentinel.id = 'scroll-sentinel';
    sentinel.style.height = '1px';
    sentinel.style.width = '100%';
    
    // Fonction pour créer une carte produit avec lazy loading
    function createProductCard(product) {
        const price = parseFloat(product.PRDPrice || 0).toFixed(0);
        const discountPrice = product.PRDDiscountPrice > 0 ? parseFloat(product.PRDDiscountPrice).toFixed(0) : null;
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
        
        card.innerHTML = `
            <img data-src="/media/${productImage}" src="${placeholder}" alt="${productName}" class="flavoriz-product-image lazy-load" style="height: ${imageHeight}; background: #F3F4F6; object-fit: cover; width: 100%;" />
            <div class="flavoriz-product-body" style="padding: ${bodyPadding};">
                <div class="flavoriz-product-views" style="font-size: ${viewsSize}; margin-bottom: ${isMobile ? '4px' : '6px'};">
                    <i class="fi-rs-eye" style="font-size: ${isMobile ? '10px' : '12px'};"></i>
                    <span>${viewCount}+ vues</span>
                </div>
                <h3 class="flavoriz-product-title" style="font-size: ${titleSize}; font-weight: 700; margin-bottom: ${isMobile ? '6px' : '8px'}; line-height: 1.2; min-height: ${titleMinHeight}; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${productName}</h3>
                <div style="display: flex; align-items: center; gap: 4px; margin-bottom: ${isMobile ? '8px' : '10px'}; flex-wrap: wrap;">
                    <span style="font-size: ${priceSize}; font-weight: 700; color: #FF7B2C;">${price} XOF</span>
                    ${discountPrice ? `<span style="font-size: ${isMobile ? '10px' : '12px'}; color: #9CA3AF; text-decoration: line-through;">${discountPrice} XOF</span>` : ''}
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
    function loadMoreProducts() {
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
                        if (sentinel.parentNode) {
                            sentinel.parentNode.removeChild(sentinel);
                        }
                        productsContainer.appendChild(sentinel);
                        
                        if (hasMore) {
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
    
    // Initialiser le chargement
    function init() {
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
    }
    
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
