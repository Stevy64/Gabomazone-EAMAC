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
                        const viewCount = product.view_count || 0;
                        const productName = product.product_name || 'Produit sans nom';
                        const productSlug = product.PRDSlug || '';

                        productsHTML += `
                            <div class="flavoriz-product-card" onclick="window.location.href='/product-details/${productSlug}'" style="cursor: pointer; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border: none; display: flex; flex-direction: column; height: 100%;">
                                <div style="position: relative; overflow: hidden; background: #FAFAFA; width: 100%; padding-top: 65%;">
                                    <img src="/media/${product.product_image}" alt="${productName}" class="flavoriz-product-image" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease;" />
                                    <div style="position: absolute; top: 8px; right: 8px; background: rgba(255, 193, 7, 0.95); border-radius: 16px; padding: 4px 8px; display: flex; align-items: center; gap: 4px; font-size: 10px; color: #1F2937; font-weight: 600; backdrop-filter: blur(4px); box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);">
                                        <i class="fi-rs-eye" style="font-size: 11px;"></i>
                                        <span>${viewCount}+</span>
                                    </div>
                                </div>
                                <div class="flavoriz-product-body" style="padding: 12px; flex: 1; display: flex; flex-direction: column;">
                                    <h3 class="flavoriz-product-title" style="font-size: 13px; font-weight: 600; color: #1F2937; margin: 0 0 8px 0; line-height: 1.4; min-height: 36px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; flex-shrink: 0;">${productName}</h3>
                                    <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; flex-shrink: 0;">
                                        <span style="font-size: 16px; font-weight: 700; color: var(--color-orange);">${price} XOF</span>
                                        ${discountPrice ? `<span style="font-size: 12px; color: #9CA3AF; text-decoration: line-through;">${discountPrice} XOF</span>` : ''}
                                    </div>
                                    <button class="flavoriz-product-card-btn" onclick="event.stopPropagation(); window.location.href='/product-details/${productSlug}'" style="width: 100%; padding: 8px 14px; background: #1F2937; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 12px; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: auto; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);">
                                        <i class="fi-rs-eye" style="font-size: 12px;"></i>
                                        <span>Voir</span>
                                    </button>
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
    
    // S'assurer que la liste est vide au départ et appeler handleGetData une seule fois
    productList.innerHTML = "";
    handleGetData(true); // true = sorted, donc on vide la liste d'abord
    
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