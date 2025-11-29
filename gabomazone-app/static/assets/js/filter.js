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

    // Utiliser la variable globale visible
    let visible = window.visible;
    window.handleGetData = function(sorted) {
        // Éviter les appels multiples simultanés
        if (window.isLoadingProducts) {
            return;
        }
        window.isLoadingProducts = true;
        
        // Utiliser les variables globales
        const currentVisible = window.visible || 10;
        const currentCategoryType = window.categoryType || "all";
        const currentCategoryID = window.categoryID || null;
        
        // Mettre à jour visible si nécessaire
        if (sorted) {
            window.visible = 10;
        }
        
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
                    data.forEach(product => {
                        const price = parseFloat(product.PRDPrice || 0).toFixed(0);
                        const discountPrice = product.PRDDiscountPrice > 0 ? parseFloat(product.PRDDiscountPrice).toFixed(0) : null;
                        const likeCount = product.like_count || 0;
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
                                </div>
                                <div class="flavoriz-product-body" style="padding: 14px; flex: 1; display: flex; flex-direction: column;">
                                    <h3 class="flavoriz-product-title" onclick="window.location.href='/product-details/${productSlug}'" style="font-size: 14px; font-weight: 600; color: #1F2937; margin: 0 0 10px 0; line-height: 1.4; min-height: 40px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; flex-shrink: 0; cursor: pointer;">${productName}</h3>
                                    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; flex-shrink: 0;">
                                        <span style="font-size: 18px; font-weight: 700; color: var(--color-orange);">${price} XOF</span>
                                        ${discountPrice ? `<span style="font-size: 13px; color: #9CA3AF; text-decoration: line-through;">${discountPrice} XOF</span>` : ''}
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
                // Réinitialiser le flag après un court délai pour permettre les appels suivants
                setTimeout(function() {
                    window.isLoadingProducts = false;
                }, 100);
            }
        })

    }
    
    // DÉSACTIVÉ : Le chargement est maintenant géré par HTMX
    // Ne pas charger automatiquement pour éviter le doublon avec HTMX
    // productList.innerHTML = "";
    // handleGetData(true); // true = sorted, donc on vide la liste d'abord
    
    loadBtn.addEventListener("click", () => {
        window.visible += 10;
        handleGetData(false); // false = pas sorted, donc on ajoute à la liste existante
    })
    
    $('.mySelect').on('change', function () {
        window.visible = 10;
        handleGetData(true);
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
        alert('Erreur: Token de sécurité non trouvé. Veuillez recharger la page.');
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
                alert('Erreur: ' + data.error);
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout aux favoris:', error);
        alert('Une erreur est survenue. Veuillez réessayer.');
    })
    .finally(() => {
        buttonElement.disabled = false;
        buttonElement.style.opacity = '1';
    });
};

// Fonction pour ajouter au panier rapidement - Version globale
window.addToCartQuick = function(productId, productPrice) {
    console.log('addToCartQuick appelée pour le produit:', productId, 'prix:', productPrice);
    
    // Nettoyer le prix (enlever "XOF" et espaces)
    const cleanPrice = String(productPrice).replace(/[^\d.]/g, '');
    
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('qyt', '1');
    formData.append('product_Price', cleanPrice);
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('Token CSRF non trouvé');
        alert('Erreur: Token de sécurité non trouvé. Veuillez recharger la page.');
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
        // Vérifier le type de contenu
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else if (response.redirected) {
            // Si redirection, c'est probablement vers la page de connexion
            window.location.href = response.url;
            return null;
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
                if (confirm(data.error + '\n\nVoulez-vous être redirigé vers la page de connexion ?')) {
                    window.location.href = '/accounts/login/';
                }
            } else {
                alert(data.error || 'Une erreur est survenue lors de l\'ajout au panier.');
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'ajout au panier:', error);
        alert('Une erreur est survenue lors de l\'ajout au panier. Veuillez réessayer.');
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
    if (count === undefined) {
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
            count = data.wishlist_count || 0;
            updateWishlistBadges(count);
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du compteur de la liste à souhaits:', error);
            updateWishlistBadges(0);
        });
    } else {
        updateWishlistBadges(count);
    }
};

function updateWishlistBadges(count) {
    const wishlistBadges = document.querySelectorAll('.flavoriz-wishlist-badge, .flavoriz-wishlist-badge-mobile');
    wishlistBadges.forEach(badge => {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    });
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
                window.toggleFavorite(parseInt(productId), favoriteBtn);
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
                window.addToCartQuick(parseInt(productId), productPrice);
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

// Fonction pour ouvrir l'aperçu d'image avec galerie
function openImagePreview(images, startIndex, imageAlt) {
    // Normaliser les images en tableau
    if (typeof images === 'string') {
        images = [images];
    }
    if (!Array.isArray(images) || images.length === 0) {
        return;
    }
    
    let currentIndex = startIndex || 0;
    if (currentIndex < 0) currentIndex = 0;
    if (currentIndex >= images.length) currentIndex = images.length - 1;
    
    // Créer le conteneur de la popup
    const popup = document.createElement('div');
    popup.id = 'flavoriz-image-preview';
    popup.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.95); z-index: 10000; display: flex; align-items: center; justify-content: center; cursor: zoom-out; animation: fadeIn 0.3s ease;';
    
    // Conteneur pour l'image
    const imageContainer = document.createElement('div');
    imageContainer.style.cssText = 'position: relative; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; min-height: 100vh;';
    
    // Créer l'image
    const img = document.createElement('img');
    img.src = images[currentIndex];
    img.alt = imageAlt;
    img.id = 'preview-main-image';
    img.style.cssText = 'max-width: 90%; max-height: 90%; object-fit: contain; border-radius: 8px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); animation: zoomIn 0.3s ease; cursor: zoom-out; transition: opacity 0.3s ease;';
    
    // Créer le bouton précédent (si plusieurs images)
    let prevBtn = null;
    let nextBtn = null;
    if (images.length > 1) {
        prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="fi-rs-angle-left" style="font-size: 28px; color: white;"></i>';
        prevBtn.className = 'preview-nav-btn preview-prev-btn';
        prevBtn.style.cssText = 'position: fixed; left: 20px; top: 50%; transform: translateY(-50%); background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 50%; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); z-index: 10001;';
        prevBtn.onmouseover = function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.transform = 'translateY(-50%) scale(1.1)';
        };
        prevBtn.onmouseout = function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.transform = 'translateY(-50%) scale(1)';
        };
        prevBtn.onclick = function(e) {
            e.stopPropagation();
            if (currentIndex > 0) {
                currentIndex--;
                updateImage();
            }
        };
        
        // Créer le bouton suivant
        nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="fi-rs-angle-right" style="font-size: 28px; color: white;"></i>';
        nextBtn.className = 'preview-nav-btn preview-next-btn';
        nextBtn.style.cssText = 'position: fixed; right: 20px; top: 50%; transform: translateY(-50%); background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 50%; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); z-index: 10001;';
        nextBtn.onmouseover = function() {
            this.style.background = 'rgba(255, 255, 255, 0.2)';
            this.style.transform = 'translateY(-50%) scale(1.1)';
        };
        nextBtn.onmouseout = function() {
            this.style.background = 'rgba(255, 255, 255, 0.1)';
            this.style.transform = 'translateY(-50%) scale(1)';
        };
        nextBtn.onclick = function(e) {
            e.stopPropagation();
            if (currentIndex < images.length - 1) {
                currentIndex++;
                updateImage();
            }
        };
    }
    
    // Créer les indicateurs de pagination (si plusieurs images)
    let indicatorsContainer = null;
    if (images.length > 1) {
        indicatorsContainer = document.createElement('div');
        indicatorsContainer.className = 'preview-indicators';
        indicatorsContainer.style.cssText = 'position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%); display: flex; gap: 8px; z-index: 10001;';
        
        for (let i = 0; i < images.length; i++) {
            const indicator = document.createElement('button');
            indicator.className = 'preview-indicator';
            indicator.setAttribute('data-index', i);
            indicator.style.cssText = `width: ${i === currentIndex ? '24px' : '8px'}; height: 8px; border-radius: 4px; background: ${i === currentIndex ? 'white' : 'rgba(255, 255, 255, 0.4)'}; border: none; cursor: pointer; transition: all 0.3s ease;`;
            indicator.onclick = function(e) {
                e.stopPropagation();
                currentIndex = parseInt(this.getAttribute('data-index'));
                updateImage();
            };
            indicatorsContainer.appendChild(indicator);
        }
    }
    
    // Fonction pour mettre à jour l'image affichée
    function updateImage() {
        img.style.opacity = '0';
        setTimeout(() => {
            img.src = images[currentIndex];
            img.style.opacity = '1';
        }, 150);
        
        // Mettre à jour les indicateurs
        if (indicatorsContainer) {
            const indicators = indicatorsContainer.querySelectorAll('.preview-indicator');
            indicators.forEach((ind, i) => {
                if (i === currentIndex) {
                    ind.style.width = '24px';
                    ind.style.background = 'white';
                } else {
                    ind.style.width = '8px';
                    ind.style.background = 'rgba(255, 255, 255, 0.4)';
                }
            });
        }
        
        // Mettre à jour l'état des boutons de navigation
        if (prevBtn) {
            prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
            prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
        }
        if (nextBtn) {
            nextBtn.style.opacity = currentIndex === images.length - 1 ? '0.5' : '1';
            nextBtn.style.pointerEvents = currentIndex === images.length - 1 ? 'none' : 'auto';
        }
    }
    
    // Créer le bouton de fermeture
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '<i class="fi-rs-cross" style="font-size: 24px; color: white;"></i>';
    closeBtn.style.cssText = 'position: absolute; top: 20px; right: 20px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); z-index: 10001;';
    closeBtn.onmouseover = function() {
        this.style.background = 'rgba(255, 255, 255, 0.2)';
        this.style.transform = 'scale(1.1)';
    };
    closeBtn.onmouseout = function() {
        this.style.background = 'rgba(255, 255, 255, 0.1)';
        this.style.transform = 'scale(1)';
    };
    
    // Fonction pour fermer la popup
    const closePopup = function() {
        popup.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
            document.body.style.overflow = '';
        }, 300);
    };
    
    closeBtn.onclick = closePopup;
    popup.onclick = function(e) {
        if (e.target === popup || e.target === imageContainer) {
            closePopup();
        }
    };
    
    // Empêcher la fermeture quand on clique sur l'image ou les boutons
    img.onclick = function(e) {
        e.stopPropagation();
    };
    
    // Navigation au clavier
    const handleKeyboard = function(e) {
        if (e.key === 'Escape') {
            closePopup();
            document.removeEventListener('keydown', handleKeyboard);
        } else if (e.key === 'ArrowLeft' && images.length > 1 && currentIndex > 0) {
            currentIndex--;
            updateImage();
        } else if (e.key === 'ArrowRight' && images.length > 1 && currentIndex < images.length - 1) {
            currentIndex++;
            updateImage();
        }
    };
    document.addEventListener('keydown', handleKeyboard);
    
    // Ajouter les éléments à la popup
    imageContainer.appendChild(img);
    if (prevBtn) imageContainer.appendChild(prevBtn);
    if (nextBtn) imageContainer.appendChild(nextBtn);
    if (indicatorsContainer) imageContainer.appendChild(indicatorsContainer);
    popup.appendChild(imageContainer);
    popup.appendChild(closeBtn);
    
    // Ajouter la popup au body et empêcher le scroll
    document.body.appendChild(popup);
    document.body.style.overflow = 'hidden';
    
    // Initialiser l'état des boutons
    updateImage();
    
    // Ajouter l'animation fadeOut si elle n'existe pas
    if (!document.getElementById('image-preview-animations')) {
        const style = document.createElement('style');
        style.id = 'image-preview-animations';
        style.textContent = `
            @keyframes fadeOut {
                from {
                    opacity: 1;
                }
                to {
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}
