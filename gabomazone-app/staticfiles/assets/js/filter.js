// Initialiser les variables globales pour le filtrage
if (typeof window.categoryType === 'undefined') {
    window.categoryType = "all";
}
if (typeof window.categoryID === 'undefined') {
    window.categoryID = null;
}
if (typeof window.visible === 'undefined') {
    window.visible = 10;
}

// Protection contre les appels multiples
if (typeof window.shopPageInitialized === 'undefined') {
    window.shopPageInitialized = false;
}

window.onload = function () {
    // Éviter les appels multiples
    if (window.shopPageInitialized) {
        return;
    }
    window.shopPageInitialized = true;
    
    // Attacher les event listeners une fois au chargement initial si la liste existe
    setTimeout(function() {
        if (document.getElementById("products-list")) {
            attachProductEventListeners();
        }
    }, 100);
    
    const productList = document.getElementById("products-list");
    const ulCategoryElement = document.querySelector(".ul-category");
    const ulCategory = ulCategoryElement ? ulCategoryElement.getElementsByTagName('li') : [];
    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const productNum = document.getElementById("product-num")
    const mySelect = document.getElementById("mySelect");
    //console.log(productNum);
    const childern = ulCategory

    // Fonction pour charger les produits avec HTMX
    window.handleGetData = function(sorted) {
        // Éviter les appels multiples simultanés
        if (window.isLoadingProducts) {
            return;
        }
        window.isLoadingProducts = true;
        
        // Utiliser les variables globales
        const currentCategoryType = window.categoryType || "all";
        const currentCategoryID = window.categoryID || null;
        const orderBy = mySelect ? mySelect.value : '-date';
        
        // Construire l'URL HTMX
        const htmxUrl = `/shop-htmx/?page=1&order_by=${orderBy}&cat_type=${currentCategoryType}&cat_id=${currentCategoryID || ''}`;
        
        // Utiliser HTMX pour charger les produits
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', htmxUrl, {
                target: '#products-list',
                swap: sorted ? 'innerHTML' : 'beforeend',
                indicator: '#loading-indicator',
                beforeRequest: function() {
                    if (sorted && spinnerBox) {
                        spinnerBox.classList.remove("not-visible");
                    }
                }
            }).then(function() {
                window.isLoadingProducts = false;
                if (spinnerBox) spinnerBox.classList.add("not-visible");
                
                // Mettre à jour le compteur de produits depuis le template
                const totalCountEl = document.getElementById('total-products-count');
                if (totalCountEl && productNum) {
                    const total = totalCountEl.textContent || '0';
                    if (parseInt(total) > 0) {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: var(--color-orange); font-size: 16px;"></i><span>Nous avons trouvé <strong style="color: var(--color-orange); font-weight: 700;">${total}</strong> articles pour vous !</span></p>`;
                    } else {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: #9CA3AF; font-size: 16px;"></i><span>Aucun produit disponible</span></p>`;
                    }
                }
                
                // Attacher les event listeners après le chargement
                if (typeof attachProductEventListeners === 'function') {
                    attachProductEventListeners();
                }
            }).catch(function() {
                window.isLoadingProducts = false;
                if (spinnerBox) spinnerBox.classList.add("not-visible");
            });
        } else {
            // Fallback si HTMX n'est pas disponible
            console.error('HTMX n\'est pas disponible');
            window.isLoadingProducts = false;
        }
    }
    
    // Ancienne fonction AJAX (désactivée, conservée pour référence)
    window.handleGetDataOld = function(sorted) {
        // Cette fonction est désactivée - utiliser HTMX maintenant
        if (false) { // Désactivé
        $.ajax({
            type: "GET",
            url: `/shop-ajax/`,
            data: {
                    "num_products": window.visible,
                "order_by": mySelect.value,
                    "CAT_id": currentCategoryID,
                    "cat_type": currentCategoryType
            },
            success: function (response) {
                const data = response.data;
                //console.log(data);
                const maxSize = response.max
                emptyBox.classList.add("not-visible")
                spinnerBox.classList.remove("not-visible")
                loadsBox.classList.add("not-visible")
                
                // TOUJOURS vider la liste avant d'ajouter de nouveaux produits pour éviter les doublons
                if (sorted) {
                    productList.innerHTML = ""
                }
                
                setTimeout(() => {
                    spinnerBox.classList.add("not-visible")
                    loadsBox.classList.remove("not-visible")

                    if (response.products_size > 0) {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: var(--color-orange); font-size: 16px;"></i><span>Nous avons trouvé <strong style="color: var(--color-orange); font-weight: 700;">${response.products_size}</strong> articles pour vous !</span></p>`
                    }
                    else {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: #9CA3AF; font-size: 16px;"></i><span>Aucun produit disponible</span></p>`
                    }

                    // Construire le HTML de tous les produits d'abord
                    let productsHTML = '';
                    // Fonction pour formater un prix avec des espaces
                    function formatPrice(priceValue) {
                        const price = parseFloat(priceValue || 0);
                        const intPrice = Math.floor(price);
                        return intPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
                    }

                    data.forEach(product => {
                        const price = formatPrice(product.PRDPrice || 0);
                        const discountPrice = product.PRDDiscountPrice > 0 ? formatPrice(product.PRDDiscountPrice) : null;
                        const likeCount = product.like_count || 0;
                        const viewCount = product.view_count || 0;
                        const isBoosted = product.is_boosted || false;
                        const productName = product.product_name || 'Produit sans nom';
                        const productSlug = product.PRDSlug || '';
                        const productId = product.id;
                        
                        // Préparer les images pour la popup
                        let productImages = [];
                        if (product.product_images && Array.isArray(product.product_images) && product.product_images.length > 0) {
                            productImages = product.product_images.map(img => {
                                // Si l'image commence déjà par /media/, ne pas l'ajouter
                                if (img.startsWith('/media/')) {
                                    return img;
                                }
                                return '/media/' + img;
                            });
                        } else if (product.product_image) {
                            const imgPath = product.product_image.startsWith('/media/') ? product.product_image : '/media/' + product.product_image;
                            productImages = [imgPath];
                        }
                        const productImagesJson = JSON.stringify(productImages).replace(/"/g, '&quot;');

                        productsHTML += `
                            <div class="flavoriz-product-card" style="cursor: pointer; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border: none; display: flex; flex-direction: column; height: 100%;">
                                <div style="position: relative; overflow: hidden; background: #FAFAFA; width: 100%; padding-top: 65%;">
                                    <img src="/media/${product.product_image}" alt="${productName}" class="flavoriz-product-image" onclick="event.stopPropagation(); openImagePreview(${productImagesJson}, 0, '${productName.replace(/'/g, "\\'")}');" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; cursor: zoom-in;" />
                                    <button class="flavoriz-favorite-btn" data-product-id="${productId}" type="button" style="position: absolute; top: 8px; right: 8px; background: rgba(255, 255, 255, 0.95); border: none; border-radius: 16px; padding: 6px 10px; display: flex; align-items: center; gap: 4px; font-size: 10px; color: #6B7280; font-weight: 600; backdrop-filter: blur(4px); box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); cursor: pointer; transition: all 0.3s ease; z-index: 10;">
                                        <i class="fi-rs-heart" style="font-size: 12px; transition: all 0.3s ease;"></i>
                                        <span class="favorite-count">${likeCount}</span>
                                    </button>
                                    ${isBoosted ? `
                                    <div style="position: absolute; top: 8px; left: 8px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #1F2937; padding: 6px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; display: flex; align-items: center; gap: 4px; box-shadow: 0 2px 8px rgba(255, 165, 0, 0.4); z-index: 10; text-transform: uppercase; letter-spacing: 0.5px;">
                                        <i class="fi-rs-rocket" style="font-size: 12px;"></i>
                                        <span>Boosté</span>
                                            </div>
                                    ` : ''}
                                    ${viewCount > 0 ? `
                                    <div style="position: absolute; bottom: 8px; left: 8px; background: rgba(0, 0, 0, 0.6); color: white; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; display: flex; align-items: center; gap: 4px; backdrop-filter: blur(4px); z-index: 10;">
                                        <i class="fi-rs-eye" style="font-size: 11px;"></i>
                                        <span>${viewCount}</span>
                                            </div>
                                    ` : ''}
                                            </div>
                                <div class="flavoriz-product-body" style="padding: 14px; flex: 1; display: flex; flex-direction: column;">
                                    <h3 class="flavoriz-product-title" onclick="window.location.href='/product-details/${productSlug}'" style="font-size: 14px; font-weight: 600; color: #1F2937; margin: 0 0 10px 0; line-height: 1.4; min-height: 40px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; flex-shrink: 0; cursor: pointer;">${productName}</h3>
                                    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; flex-shrink: 0;">
                                        <span style="font-size: 18px; font-weight: 700; color: var(--color-orange);">${price} FCFA</span>
                                        ${discountPrice ? `<span style="font-size: 13px; color: #9CA3AF; text-decoration: line-through;">${discountPrice} FCFA</span>` : ''}
                                        </div>
                                    <div style="display: flex; gap: 8px; margin-top: auto;">
                                        <button class="flavoriz-product-card-btn" onclick="event.stopPropagation(); window.location.href='/product-details/${productSlug}'" style="flex: 1; padding: 10px 16px; background: #1F2937; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 6px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);">
                                            <i class="fi-rs-eye" style="font-size: 13px;"></i>
                                            <span>Voir</span>
                                        </button>
                                        <button class="flavoriz-add-cart-btn" data-product-id="${productId}" data-product-price="${price}" type="button" style="padding: 10px 14px; background: white; color: #1F2937; border: 1px solid #1F2937; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); min-width: 48px;">
                                            <i class="fi-rs-shopping-bag" style="font-size: 15px;"></i>
                                        </button>
                                                </div>
                                            </div>
                                        </div>
                        `;
                    });
                    
                    // Ajouter tous les produits en une seule fois pour éviter les doublons
                    if (sorted) {
                        productList.innerHTML = productsHTML;
                    } else {
                        productList.innerHTML += productsHTML;
                    }
                    
                    // Attacher les event listeners après l'ajout des produits
                    attachProductEventListeners();
                    
                    // Forcer la grille après l'ajout des produits
                    setTimeout(function() {
                        const productsList = document.getElementById('products-list');
                        if (productsList) {
                            const width = window.innerWidth;
                            productsList.style.setProperty('display', 'grid', 'important');
                            productsList.style.setProperty('width', '100%', 'important');
                            productsList.style.setProperty('max-width', '100%', 'important');
                            productsList.style.setProperty('box-sizing', 'border-box', 'important');
                            
                            if (width >= 1200) {
                                productsList.style.setProperty('grid-template-columns', 'repeat(4, 1fr)', 'important');
                                productsList.style.setProperty('gap', '20px', 'important');
                            } else if (width >= 769) {
                                productsList.style.setProperty('grid-template-columns', 'repeat(3, 1fr)', 'important');
                                productsList.style.setProperty('gap', '18px', 'important');
                            } else {
                                productsList.style.setProperty('grid-template-columns', 'repeat(2, 1fr)', 'important');
                                productsList.style.setProperty('gap', '12px', 'important');
                            }
                            
                            // Forcer les enfants à prendre 100% de largeur
                            const children = productsList.children;
                            for (let i = 0; i < children.length; i++) {
                                children[i].style.setProperty('width', '100%', 'important');
                                children[i].style.setProperty('min-width', '0', 'important');
                                children[i].style.setProperty('max-width', '100%', 'important');
                                children[i].style.setProperty('box-sizing', 'border-box', 'important');
                            }
                        }
                    }, 100);
                    
                    if (maxSize) {

                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `
                            <i class="fi-rs-shopping-bag" style="font-size: 64px; color: #D1D5DB; opacity: 0.5; margin-bottom: 16px; display: block;"></i>
                            <p style="font-size: 16px; font-weight: 600; color: #6B7280; margin: 0;">Aucun autre produit disponible !</p>
                        `
                    }
                    
                    // Réinitialiser le flag de chargement
                    window.isLoadingProducts = false;

                }, 500)


            },
                error: function (error) {
                    window.isLoadingProducts = false;
                },
                complete: function() {
                    setTimeout(function() {
                        window.isLoadingProducts = false;
                    }, 100);
                }
            });
        }
    }
    
    // DÉSACTIVÉ : Le chargement est maintenant géré par HTMX
    // Ne pas charger automatiquement pour éviter le doublon avec HTMX
    // productList.innerHTML = "";
    // handleGetData(true); // true = sorted, donc on vide la liste d'abord
    
    // Le bouton "Charger plus" est maintenant géré par HTMX dans le template
    // Plus besoin de gérer manuellement le chargement
    
    // Gérer le changement de tri avec HTMX
    $('.mySelect').on('change', function () {
        const orderBy = $(this).val();
        const catType = $('#cat_type_input').val() || 'all';
        const catId = $('#cat_id_input').val() || '';
        const htmxUrl = `/shop-htmx/?page=1&order_by=${orderBy}&cat_type=${catType}&cat_id=${catId}`;
        
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', htmxUrl, {
                target: '#products-list',
                swap: 'innerHTML',
                indicator: '#loading-indicator'
            }).then(function() {
                // Mettre à jour le compteur
                const totalCountEl = document.getElementById('total-products-count');
                if (totalCountEl && productNum) {
                    const total = totalCountEl.textContent || '0';
                    if (parseInt(total) > 0) {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: var(--color-orange); font-size: 16px;"></i><span>Nous avons trouvé <strong style="color: var(--color-orange); font-weight: 700;">${total}</strong> articles pour vous !</span></p>`;
                    } else {
                        productNum.innerHTML = `<p style="margin: 0; display: flex; align-items: center; gap: 6px;"><i class="fi-rs-box" style="color: #9CA3AF; font-size: 16px;"></i><span>Aucun produit disponible</span></p>`;
                    }
                }
                
                // Réattacher les event listeners
                if (typeof attachProductEventListeners === 'function') {
                    attachProductEventListeners();
                }
            });
        }
    })

    if (categoryType == "sub") {
        for (let i = 0; i < childern.length; i++) {


            childern[i].addEventListener("click", (event) => {
                event.preventDefault();

                console.log(childern[i].value);

                visible = 10;
                categoryID = childern[i].value;
                categoryType = "mini";
                console.log(childern[i])
                miniSelect.innerHTML = childern[i].id;
                handleGetData(true);

            })
        }
    }

}

// Fonction pour toggle les favoris - Version globale
window.toggleFavorite = function(productId, buttonElement) {
    console.log('toggleFavorite appelée pour le produit:', productId, buttonElement);
    if (!buttonElement) {
        console.error('buttonElement est null');
        return;
    }
    
    const formData = new FormData();
    formData.append('product_id', productId);
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('Token CSRF non trouvé');
        if (typeof GMModal !== 'undefined') {
            GMModal.error('Erreur', 'Token de sécurité non trouvé. Veuillez recharger la page.');
        } else {
            alert('Erreur: Token de sécurité non trouvé. Veuillez recharger la page.');
        }
        return;
    }
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Désactiver le bouton pendant la requête
    buttonElement.disabled = true;
    buttonElement.style.opacity = '0.6';
    
    fetch('/products/toggle-favorite/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Réponse toggle favorite:', data);
        if (data.success) {
            const heartIcon = buttonElement.querySelector('i');
            const countSpan = buttonElement.querySelector('.favorite-count');
            
            if (data.is_favorited) {
                heartIcon.style.color = '#EF4444';
                buttonElement.classList.add('liked');
                buttonElement.style.background = 'rgba(254, 226, 226, 0.95)';
            } else {
                heartIcon.style.color = '#6B7280';
                buttonElement.classList.remove('liked');
                buttonElement.style.background = 'rgba(255, 255, 255, 0.95)';
            }
            
            if (countSpan) {
                countSpan.textContent = data.like_count || 0;
            }
            
            // Mettre à jour le compteur de la liste à souhaits dans le header
            if (data.wishlist_count !== undefined) {
                if (typeof window.updateWishlistCount === 'function') {
                    window.updateWishlistCount(data.wishlist_count);
                }
            }
        } else {
            console.error('Erreur dans la réponse:', data.error);
            if (data.error) {
                if (typeof GMModal !== 'undefined') {
                    GMModal.error('Erreur', data.error);
                } else {
                    alert('Erreur: ' + data.error);
                }
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout aux favoris:', error);
        if (typeof GMModal !== 'undefined') {
            GMModal.error('Erreur', 'Une erreur est survenue. Veuillez réessayer.');
        } else {
            alert('Une erreur est survenue. Veuillez réessayer.');
        }
    })
    .finally(() => {
        buttonElement.disabled = false;
        buttonElement.style.opacity = '1';
    });
};

// Fonction pour ajouter au panier rapidement - Version globale
window.addToCartQuick = function(productId, productPrice) {
    console.log('addToCartQuick appelée pour le produit:', productId, 'prix:', productPrice);
    
    // Nettoyer le prix (enlever "FCFA" et espaces)
    const cleanPrice = String(productPrice).replace(/[^\d.]/g, '');
    
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('qyt', '1');
    formData.append('product_Price', cleanPrice);
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('Token CSRF non trouvé');
        if (typeof GMModal !== 'undefined') {
            GMModal.error('Erreur', 'Token de sécurité non trouvé. Veuillez recharger la page.');
        } else {
            alert('Erreur: Token de sécurité non trouvé. Veuillez recharger la page.');
        }
        return;
    }
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Trouver le bouton et le désactiver
    const buttons = document.querySelectorAll(`[data-product-id="${productId}"].flavoriz-add-cart-btn`);
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
    });
    
    fetch('/orders/add_to_cart/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        // Si redirection (status 302 ou 301), c'est probablement vers la page de connexion
        if (response.redirected || response.status === 302 || response.status === 301) {
            // Rediriger vers la page de connexion avec le paramètre next
            const currentUrl = window.location.pathname + window.location.search;
            window.location.href = '/login/?next=' + encodeURIComponent(currentUrl);
            return null;
        }
        
        // Vérifier si c'est une erreur 403 (Forbidden) ou 401 (Unauthorized) - utilisateur non authentifié
        if (response.status === 403 || response.status === 401) {
            const currentUrl = window.location.pathname + window.location.search;
            window.location.href = '/login/?next=' + encodeURIComponent(currentUrl);
            return null;
        }
        
        // Vérifier le type de contenu
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else if (response.ok) {
            // Si ce n'est pas du JSON, c'est probablement une redirection HTML
            return response.text().then(text => {
                // Essayer de parser comme JSON si possible
                try {
                    return JSON.parse(text);
                } catch {
                    return {success: true, message: 'Produit ajouté au panier'};
                }
            });
        } else {
            return response.json().catch(() => {
                throw new Error(`HTTP error! status: ${response.status}`);
            });
        }
    })
    .then(data => {
        if (data === null) {
            // Redirection en cours
            return;
        }
        
        if (data.success) {
            // Afficher un message de succès
            if (typeof window.showCartSuccessMessage === 'function') {
                window.showCartSuccessMessage();
            }
            // Mettre à jour le compteur du panier
            if (data.cart_count !== undefined) {
                const cartBadges = document.querySelectorAll('.flavoriz-cart-badge, .flavoriz-cart-badge-mobile, .flavoriz-cart-badge-bottom');
                cartBadges.forEach(badge => {
                    if (data.cart_count > 0) {
                        badge.textContent = data.cart_count;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                });
            } else {
                setTimeout(() => {
                    if (typeof window.updateCartCount === 'function') {
                        window.updateCartCount();
                    }
                }, 500);
            }
        } else {
            // Erreur retournée par le serveur
            if (data.requires_login) {
                if (typeof GMModal !== 'undefined') {
                    GMModal.confirm(
                        'Connexion requise',
                        data.error + '<br><br>Voulez-vous être redirigé vers la page de connexion ?',
                        function() {
                            const currentUrl = window.location.pathname + window.location.search;
                            window.location.href = '/login/?next=' + encodeURIComponent(currentUrl);
                        }
                    );
                } else {
                    if (confirm(data.error + '\n\nVoulez-vous être redirigé vers la page de connexion ?')) {
                        const currentUrl = window.location.pathname + window.location.search;
                        window.location.href = '/login/?next=' + encodeURIComponent(currentUrl);
                    }
                }
            } else {
                if (typeof GMModal !== 'undefined') {
                    GMModal.error('Erreur', data.error || 'Une erreur est survenue lors de l\'ajout au panier.');
                } else {
                    alert(data.error || 'Une erreur est survenue lors de l\'ajout au panier.');
                }
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout au panier:', error);
        if (typeof GMModal !== 'undefined') {
            GMModal.error('Erreur', 'Une erreur est survenue lors de l\'ajout au panier. Veuillez réessayer.');
        } else {
            alert('Une erreur est survenue lors de l\'ajout au panier. Veuillez réessayer.');
        }
    })
    .finally(() => {
        // Réactiver les boutons
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
    });
};

// Fonction pour obtenir le cookie CSRF
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


// Fonction pour mettre à jour le compteur de la liste à souhaits - Version globale
window.updateWishlistCount = function(count) {
    if (count === undefined || count === null) {
        // Si count n'est pas fourni, le récupérer depuis le serveur
        fetch('/products/api/wishlist-count/', {
            method: 'GET',
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const wishlistCount = data.wishlist_count || 0;
            updateWishlistBadges(wishlistCount);
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du compteur de la liste à souhaits:', error);
            updateWishlistBadges(0);
        });
    } else {
        // Convertir en nombre pour s'assurer que c'est un entier
        const wishlistCount = parseInt(count, 10) || 0;
        updateWishlistBadges(wishlistCount);
    }
};

function updateWishlistBadges(count) {
    // S'assurer que count est un nombre valide
    const wishlistCount = parseInt(count, 10) || 0;
    
    const wishlistBadges = document.querySelectorAll('.flavoriz-wishlist-badge, .flavoriz-wishlist-badge-mobile');
    
    if (wishlistBadges.length === 0) {
        console.warn('Aucun badge de wishlist trouvé dans le DOM');
        return;
    }
    
    wishlistBadges.forEach(badge => {
        if (!badge) return;
        
        if (wishlistCount > 0) {
            badge.textContent = wishlistCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    });
    
    console.log('Compteur de wishlist mis à jour:', wishlistCount);
}

// Fonction pour mettre à jour le compteur du panier - Version globale
window.updateCartCount = function() {
    fetch('/orders/api/cart-count/', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Compteur panier mis à jour:', data.cart_count);
        // Mettre à jour les badges du panier
        const cartBadges = document.querySelectorAll('.flavoriz-cart-badge, .flavoriz-cart-badge-mobile, .flavoriz-cart-badge-bottom');
        cartBadges.forEach(badge => {
            if (data.cart_count > 0) {
                badge.textContent = data.cart_count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });
    })
    .catch(error => {
        console.error('Erreur lors de la mise à jour du compteur:', error);
    });
};

// Fonction pour afficher un message de succès - Version globale
window.showCartSuccessMessage = function() {
    // Créer un message toast
    const toast = document.createElement('div');
    toast.style.cssText = 'position: fixed; top: 100px; right: 20px; background: #10B981; color: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); z-index: 10000; display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; animation: slideInRight 0.3s ease;';
    toast.innerHTML = '<i class="fi-rs-check" style="font-size: 16px;"></i><span>Produit ajouté au panier !</span>';
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
};

// Fonction pour attacher les event listeners aux produits
function attachProductEventListeners() {
    console.log('Attachement des event listeners aux produits...');
    
    // Vérifier si un listener existe déjà pour éviter les doublons
    if (document.body.hasAttribute('data-product-listeners-attached')) {
        console.log('Listeners déjà attachés');
        return;
    }
    
    // Marquer comme attaché
    document.body.setAttribute('data-product-listeners-attached', 'true');
    
    // Utiliser la délégation d'événements sur le document pour capturer tous les clics
    // Cela fonctionne pour products-list ET pour les carrousels (popular-carousel, new-carousel)
    document.addEventListener('click', function(e) {
        // Bouton favoris
        const favoriteBtn = e.target.closest('.flavoriz-favorite-btn');
        if (favoriteBtn) {
            e.stopPropagation();
            e.preventDefault();
            const productId = favoriteBtn.getAttribute('data-product-id');
            if (productId && typeof window.toggleFavorite === 'function') {
                console.log('Clic sur bouton favoris, produit:', productId);
                // Ne pas parser les IDs "peer_X" comme des entiers
                const parsedId = productId.toString().startsWith('peer_') ? productId : parseInt(productId);
                window.toggleFavorite(parsedId, favoriteBtn);
            } else {
                console.error('toggleFavorite non disponible ou productId manquant', productId, typeof window.toggleFavorite);
            }
            return false;
        }
        
        // Bouton panier
        const cartBtn = e.target.closest('.flavoriz-add-cart-btn');
        if (cartBtn) {
            e.stopPropagation();
            e.preventDefault();
            const productId = cartBtn.getAttribute('data-product-id');
            const productPrice = cartBtn.getAttribute('data-product-price');
            if (productId && productPrice && typeof window.addToCartQuick === 'function') {
                console.log('Clic sur bouton panier, produit:', productId, 'prix:', productPrice);
                // Ne pas parser les IDs "peer_X" comme des entiers
                const parsedId = productId.toString().startsWith('peer_') ? productId : parseInt(productId);
                window.addToCartQuick(parsedId, productPrice);
            } else {
                console.error('addToCartQuick non disponible ou données manquantes', productId, productPrice, typeof window.addToCartQuick);
            }
            return false;
        }
    });
    
    console.log('Event listeners attachés avec succès (délégation sur document)');
}

// Ajouter les animations CSS si elles n'existent pas
if (!document.getElementById('cart-toast-styles')) {
    const style = document.createElement('style');
    style.id = 'cart-toast-styles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        @keyframes zoomIn {
            from {
                transform: scale(0.8);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Aperçu plein écran (lightbox) — gabomazone-client/css/image-lightbox.css (.gm-lightbox).
 * Signature inchangée : openImagePreview(images, startIndex, imageAlt)
 */
function openImagePreview(images, startIndex, imageAlt) {
    if (typeof images === 'string') {
        images = [images];
    }
    if (!Array.isArray(images) || images.length === 0) {
        return;
    }

    const prevOpen = document.getElementById('flavoriz-image-preview');
    if (prevOpen && prevOpen.parentNode) {
        prevOpen.parentNode.removeChild(prevOpen);
    }

    let currentIndex = startIndex || 0;
    if (currentIndex < 0) currentIndex = 0;
    if (currentIndex >= images.length) currentIndex = images.length - 1;

    const titleText = (imageAlt && String(imageAlt).trim()) || 'Aperçu';
    const multi = images.length > 1;
    const previousActiveElement = document.activeElement;

    const popup = document.createElement('div');
    popup.id = 'flavoriz-image-preview';
    popup.className = 'gm-lightbox';
    popup.setAttribute('role', 'dialog');
    popup.setAttribute('aria-modal', 'true');
    popup.setAttribute('aria-labelledby', 'gm-lightbox-title');

    const bg = document.createElement('div');
    bg.className = 'gm-lightbox__bg';

    const shell = document.createElement('div');
    shell.className = 'gm-lightbox__shell';

    const topbar = document.createElement('div');
    topbar.className = 'gm-lightbox__topbar';

    const topInfo = document.createElement('div');
    topInfo.className = 'gm-lightbox__topbar-info';

    const titleEl = document.createElement('p');
    titleEl.className = 'gm-lightbox__title';
    titleEl.id = 'gm-lightbox-title';
    titleEl.textContent = titleText;

    const meta = document.createElement('div');
    meta.className = 'gm-lightbox__meta';

    const badge = document.createElement('span');
    badge.className = 'gm-lightbox__badge';
    badge.setAttribute('aria-live', 'polite');
    badge.setAttribute('aria-atomic', 'true');
    const badgeDot = document.createElement('span');
    badgeDot.className = 'gm-lightbox__badge-dot';
    badgeDot.setAttribute('aria-hidden', 'true');
    const badgeText = document.createElement('span');
    badgeText.className = 'gm-lightbox__badge-text';
    badge.appendChild(badgeDot);
    badge.appendChild(badgeText);

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'gm-lightbox__close';
    closeBtn.setAttribute('aria-label', 'Fermer la galerie');
    closeBtn.innerHTML = '<i class="fi-rs-cross" aria-hidden="true"></i>';

    meta.appendChild(badge);
    topInfo.appendChild(titleEl);
    topInfo.appendChild(meta);
    topbar.appendChild(topInfo);
    topbar.appendChild(closeBtn);

    const stage = document.createElement('div');
    stage.className = 'gm-lightbox__stage';

    const prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className =
        'gm-lightbox__nav gm-lightbox__nav--prev' + (multi ? '' : ' gm-lightbox__nav--hidden');
    prevBtn.setAttribute('aria-label', 'Photo précédente');
    prevBtn.innerHTML = '<i class="fi-rs-angle-left" aria-hidden="true"></i>';

    const frame = document.createElement('div');
    frame.className = 'gm-lightbox__frame';

    const img = document.createElement('img');
    img.className = 'gm-lightbox__img';
    img.alt = titleText;
    img.decoding = 'async';

    const loading = document.createElement('div');
    loading.className = 'gm-lightbox__loading';
    loading.setAttribute('aria-hidden', 'true');
    loading.innerHTML = '<div class="gm-lightbox__spinner"></div>';

    const nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className =
        'gm-lightbox__nav gm-lightbox__nav--next' + (multi ? '' : ' gm-lightbox__nav--hidden');
    nextBtn.setAttribute('aria-label', 'Photo suivante');
    nextBtn.innerHTML = '<i class="fi-rs-angle-right" aria-hidden="true"></i>';

    frame.appendChild(img);
    frame.appendChild(loading);

    stage.appendChild(prevBtn);
    stage.appendChild(frame);
    stage.appendChild(nextBtn);

    const thumbButtons = [];

    shell.appendChild(topbar);
    shell.appendChild(stage);

    if (multi) {
        const thumbsWrap = document.createElement('div');
        thumbsWrap.className = 'gm-lightbox__thumbs-wrap';
        const thumbsEl = document.createElement('div');
        thumbsEl.className = 'gm-lightbox__thumbs';
        thumbsEl.setAttribute('role', 'tablist');
        thumbsEl.setAttribute('aria-label', 'Miniatures');
        images.forEach((src, i) => {
            const tb = document.createElement('button');
            tb.type = 'button';
            tb.className = 'gm-lightbox__thumb' + (i === currentIndex ? ' is-active' : '');
            tb.setAttribute('role', 'tab');
            tb.setAttribute('aria-selected', i === currentIndex ? 'true' : 'false');
            tb.setAttribute('aria-label', 'Afficher la photo ' + (i + 1) + ' sur ' + images.length);
            const tim = document.createElement('img');
            tim.src = src;
            tim.alt = '';
            tim.loading = 'lazy';
            tb.appendChild(tim);
            tb.addEventListener('click', function (e) {
                e.stopPropagation();
                if (i !== currentIndex) {
                    showAt(i, false);
                }
            });
            thumbsEl.appendChild(tb);
            thumbButtons.push(tb);
        });
        thumbsWrap.appendChild(thumbsEl);
        shell.appendChild(thumbsWrap);
    }

    popup.appendChild(bg);
    popup.appendChild(shell);

    function updateChrome() {
        badgeText.textContent =
            images.length === 1
                ? '1 photo'
                : 'Photo ' + (currentIndex + 1) + ' sur ' + images.length;
        if (multi) {
            prevBtn.disabled = currentIndex <= 0;
            nextBtn.disabled = currentIndex >= images.length - 1;
            thumbButtons.forEach(function (tb, i) {
                tb.classList.toggle('is-active', i === currentIndex);
                tb.setAttribute('aria-selected', i === currentIndex ? 'true' : 'false');
            });
            const activeThumb = thumbButtons[currentIndex];
            if (activeThumb && typeof activeThumb.scrollIntoView === 'function') {
                activeThumb.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
            }
        }
    }

    let loadSeq = 0;
    function showAt(index, initialOpen) {
        if (index < 0 || index >= images.length) {
            return;
        }
        currentIndex = index;
        loadSeq += 1;
        const seq = loadSeq;
        loading.classList.add('is-visible');
        img.classList.remove('gm-lightbox__img--swap-in');
        if (initialOpen) {
            img.classList.remove('gm-lightbox__img--swap-out');
        } else {
            img.classList.add('gm-lightbox__img--swap-out');
        }

        const src = images[currentIndex];

        function onDone() {
            if (seq !== loadSeq) {
                return;
            }
            img.removeEventListener('load', onDone);
            img.removeEventListener('error', onDone);
            loading.classList.remove('is-visible');
            img.classList.remove('gm-lightbox__img--swap-out');
            requestAnimationFrame(function () {
                if (seq !== loadSeq) {
                    return;
                }
                img.classList.add('gm-lightbox__img--swap-in');
                updateChrome();
            });
        }

        img.addEventListener('load', onDone);
        img.addEventListener('error', onDone);
        img.src = src;
        if (img.complete && img.naturalWidth > 0) {
            onDone();
        }
    }

    let closed = false;
    let domRemoved = false;
    function closePopup() {
        if (closed) {
            return;
        }
        closed = true;
        document.removeEventListener('keydown', onKey);
        stage.removeEventListener('touchstart', onTouchStart);
        stage.removeEventListener('touchend', onTouchEnd);
        document.body.style.overflow = '';
        popup.classList.add('gm-lightbox--closing');

        function cleanup() {
            if (domRemoved) {
                return;
            }
            domRemoved = true;
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
            if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
                try {
                    previousActiveElement.focus();
                } catch (e) {
                    /* ignore */
                }
            }
        }

        function onAnimEnd(ev) {
            if (ev.target === popup && ev.animationName === 'gmLightboxExit') {
                popup.removeEventListener('animationend', onAnimEnd);
                cleanup();
            }
        }
        popup.addEventListener('animationend', onAnimEnd);
        setTimeout(cleanup, 350);
    }

    function onKey(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            closePopup();
        } else if (multi && e.key === 'ArrowLeft' && currentIndex > 0) {
            e.preventDefault();
            showAt(currentIndex - 1, false);
        } else if (multi && e.key === 'ArrowRight' && currentIndex < images.length - 1) {
            e.preventDefault();
            showAt(currentIndex + 1, false);
        }
    }

    let touchStartX = 0;
    function onTouchStart(e) {
        if (!multi || !e.changedTouches || !e.changedTouches[0]) {
            return;
        }
        touchStartX = e.changedTouches[0].screenX;
    }
    function onTouchEnd(e) {
        if (!multi || !e.changedTouches || !e.changedTouches[0]) {
            return;
        }
        const dx = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(dx) < 50) {
            return;
        }
        if (dx < 0 && currentIndex < images.length - 1) {
            showAt(currentIndex + 1, false);
        } else if (dx > 0 && currentIndex > 0) {
            showAt(currentIndex - 1, false);
        }
    }

    bg.addEventListener('click', closePopup);
    closeBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        closePopup();
    });
    prevBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (currentIndex > 0) {
            showAt(currentIndex - 1, false);
        }
    });
    nextBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (currentIndex < images.length - 1) {
            showAt(currentIndex + 1, false);
        }
    });
    img.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    document.addEventListener('keydown', onKey);
    if (multi) {
        stage.addEventListener('touchstart', onTouchStart, { passive: true });
        stage.addEventListener('touchend', onTouchEnd, { passive: true });
    }

    document.body.appendChild(popup);
    document.body.style.overflow = 'hidden';
    showAt(currentIndex, true);
    try {
        closeBtn.focus({ preventScroll: true });
    } catch (e) {
        closeBtn.focus();
    }
}

window.openImagePreview = openImagePreview;
