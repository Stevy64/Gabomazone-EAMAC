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
 * Lightbox plein ecran - fond noir pur, compteur de photos, swipe tactile.
 * Remplace l'ancienne galerie pour une meilleure UX mobile.
 */
function openImagePreview(images, startIndex, imageAlt) {
    if (typeof images === 'string') images = [images];
    if (!Array.isArray(images) || images.length === 0) return;

    /* Remove any existing lightbox to avoid duplicates */
    var existing = document.getElementById('gm-lightbox');
    if (existing) { existing.parentNode.removeChild(existing); document.body.style.overflow = ''; }

    var idx = startIndex || 0;
    if (idx < 0) idx = 0;
    if (idx >= images.length) idx = images.length - 1;

    /* Inject keyframes once */
    if (!document.getElementById('gm-lightbox-kf')) {
        var kf = document.createElement('style');
        kf.id = 'gm-lightbox-kf';
        kf.textContent =
            '@keyframes gmLbIn{from{opacity:0}to{opacity:1}}' +
            '@keyframes gmLbOut{from{opacity:1}to{opacity:0}}' +
            '@keyframes gmLbZoom{from{transform:scale(.92);opacity:0}to{transform:scale(1);opacity:1}}' +
            '@media(hover:none)and(pointer:coarse){.gm-lb-arrow{display:none!important}}';
        document.head.appendChild(kf);
    }

    /* Overlay - fond noir pur */
    var overlay = document.createElement('div');
    overlay.id = 'gm-lightbox';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:25000;background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:gmLbIn .25s ease;user-select:none;-webkit-user-select:none;';

    /* Counter top center */
    var counter = document.createElement('div');
    counter.setAttribute('aria-live', 'polite');
    counter.style.cssText = 'position:absolute;top:14px;left:50%;transform:translateX(-50%);z-index:25015;background:rgba(0,0,0,.6);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);color:#fff;padding:8px 20px;border-radius:999px;font-size:15px;font-weight:700;letter-spacing:.5px;pointer-events:none;min-width:60px;text-align:center;border:1px solid rgba(255,255,255,.25);';

    /* Close button — large tap target for mobile */
    var closeBtn = document.createElement('button');
    closeBtn.setAttribute('aria-label', 'Fermer');
    closeBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
    closeBtn.style.cssText = 'position:absolute;top:12px;right:12px;z-index:25020;background:rgba(0,0,0,.55);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:2px solid rgba(255,255,255,.35);border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#fff;touch-action:manipulation;-webkit-tap-highlight-color:transparent;';
    closeBtn.onmouseover = function () { this.style.background = 'rgba(255,255,255,.3)'; };
    closeBtn.onmouseout  = function () { this.style.background = 'rgba(0,0,0,.55)'; };

    /* Image container */
    var imgWrap = document.createElement('div');
    imgWrap.style.cssText = 'position:relative;display:flex;align-items:center;justify-content:center;width:100%;flex:1;overflow:hidden;touch-action:pan-y pinch-zoom;';

    var img = document.createElement('img');
    img.src = images[idx];
    img.alt = imageAlt || '';
    img.draggable = false;
    img.style.cssText = 'max-width:94%;max-height:88vh;object-fit:contain;border-radius:4px;animation:gmLbZoom .3s ease;transition:opacity .15s ease,transform .2s ease;';

    /* Arrow factory */
    function makeArrow(dir) {
        var btn = document.createElement('button');
        btn.setAttribute('aria-label', dir === 'prev' ? 'Photo precedente' : 'Photo suivante');
        btn.innerHTML = dir === 'prev'
            ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'
            : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
        btn.className = 'gm-lb-arrow';
        btn.style.cssText = 'position:absolute;top:50%;transform:translateY(-50%);z-index:25005;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.2);border-radius:50%;width:48px;height:48px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#fff;transition:background .2s,opacity .2s;'
            + (dir === 'prev' ? 'left:12px;' : 'right:12px;');
        btn.onmouseover = function () { this.style.background = 'rgba(255,255,255,.25)'; };
        btn.onmouseout  = function () { this.style.background = 'rgba(255,255,255,.12)'; };
        return btn;
    }

    var prevBtn = null, nextBtn = null;
    if (images.length > 1) {
        prevBtn = makeArrow('prev');
        prevBtn.onclick = function (e) { e.stopPropagation(); go(-1); };
        nextBtn = makeArrow('next');
        nextBtn.onclick = function (e) { e.stopPropagation(); go(1); };
    }

    /* Dot indicators */
    var dotsWrap = null;
    if (images.length > 1) {
        dotsWrap = document.createElement('div');
        dotsWrap.style.cssText = 'position:absolute;bottom:20px;left:50%;transform:translateX(-50%);display:flex;gap:7px;z-index:25005;';
        for (var di = 0; di < images.length; di++) {
            var dot = document.createElement('button');
            dot.className = 'gm-lb-dot';
            dot.setAttribute('data-i', di);
            dot.setAttribute('aria-label', 'Photo ' + (di + 1));
            dot.style.cssText = 'width:8px;height:8px;border-radius:50%;border:none;cursor:pointer;transition:all .25s;padding:0;'
                + (di === idx ? 'background:#fff;width:22px;border-radius:4px;' : 'background:rgba(255,255,255,.45);');
            dot.onclick = (function (i) {
                return function (e) { e.stopPropagation(); idx = i; render(); };
            })(di);
            dotsWrap.appendChild(dot);
        }
    }

    /* Render state */
    function render() {
        img.style.opacity = '0';
        setTimeout(function () { img.src = images[idx]; img.style.opacity = '1'; }, 120);
        counter.textContent = (idx + 1) + ' / ' + images.length;
        if (prevBtn) { prevBtn.style.opacity = idx === 0 ? '.35' : '1'; prevBtn.style.pointerEvents = idx === 0 ? 'none' : 'auto'; }
        if (nextBtn) { nextBtn.style.opacity = idx === images.length - 1 ? '.35' : '1'; nextBtn.style.pointerEvents = idx === images.length - 1 ? 'none' : 'auto'; }
        if (dotsWrap) {
            var dots = dotsWrap.querySelectorAll('.gm-lb-dot');
            for (var d = 0; d < dots.length; d++) {
                dots[d].style.background = d === idx ? '#fff' : 'rgba(255,255,255,.45)';
                dots[d].style.width = d === idx ? '22px' : '8px';
                dots[d].style.borderRadius = d === idx ? '4px' : '50%';
            }
        }
    }

    function go(delta) {
        var ni = idx + delta;
        if (ni < 0 || ni >= images.length) return;
        img.style.transform = delta > 0 ? 'translateX(-30px)' : 'translateX(30px)';
        idx = ni;
        setTimeout(function () { img.style.transform = ''; }, 50);
        render();
    }

    /* Close */
    function closeLb() {
        overlay.style.animation = 'gmLbOut .2s ease forwards';
        document.removeEventListener('keydown', onKey);
        setTimeout(function () {
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            document.body.style.overflow = '';
        }, 220);
    }
    closeBtn.addEventListener('click', function (e) { e.stopPropagation(); closeLb(); });
    closeBtn.addEventListener('touchend', function (e) { e.preventDefault(); e.stopPropagation(); closeLb(); });
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay || e.target === imgWrap) closeLb();
    });
    img.addEventListener('click', function (e) { e.stopPropagation(); });

    /* Keyboard */
    function onKey(e) {
        if (e.key === 'Escape') closeLb();
        else if (e.key === 'ArrowLeft') go(-1);
        else if (e.key === 'ArrowRight') go(1);
    }
    document.addEventListener('keydown', onKey);

    /* Touch swipe */
    var touchX0 = 0, touchY0 = 0, touchDx = 0, swiping = false;
    imgWrap.addEventListener('touchstart', function (e) {
        if (e.touches.length !== 1) return;
        touchX0 = e.touches[0].clientX;
        touchY0 = e.touches[0].clientY;
        touchDx = 0; swiping = false;
    }, { passive: true });
    imgWrap.addEventListener('touchmove', function (e) {
        if (e.touches.length !== 1) return;
        var dx = e.touches[0].clientX - touchX0;
        var dy = e.touches[0].clientY - touchY0;
        if (!swiping && Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) swiping = true;
        if (swiping) { touchDx = dx; img.style.transform = 'translateX(' + (dx * 0.4) + 'px)'; e.preventDefault(); }
    }, { passive: false });
    imgWrap.addEventListener('touchend', function () {
        if (!swiping) return;
        img.style.transform = '';
        if (touchDx < -50) go(1); else if (touchDx > 50) go(-1);
        swiping = false; touchDx = 0;
    }, { passive: true });

    /* Assemble */
    imgWrap.appendChild(img);
    if (prevBtn) imgWrap.appendChild(prevBtn);
    if (nextBtn) imgWrap.appendChild(nextBtn);
    if (dotsWrap) imgWrap.appendChild(dotsWrap);
    overlay.appendChild(counter);
    overlay.appendChild(closeBtn);
    overlay.appendChild(imgWrap);

    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
    render();
}
