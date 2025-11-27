window.onload = function () {
    const productList = document.getElementById("products-list");
    const ulCategory = document.querySelector(".ul-category").getElementsByTagName('li');
    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const productNum = document.getElementById("product-num")
    const mySelect = document.getElementById("mySelect");
    //console.log(productNum);
    const childern = ulCategory


    let visible = 10;
    const handleGetData = (sorted) => {
        $.ajax({
            type: "GET",
            url: `/shop-ajax/`,
            data: {
                "num_products": visible,
                "order_by": mySelect.value,
                "CAT_id": categoryID,
                "cat_type": categoryType
            },
            success: function (response) {
                const data = response.data;
                //console.log(data);
                const maxSize = response.max
                emptyBox.classList.add("not-visible")
                spinnerBox.classList.remove("not-visible")
                loadsBox.classList.add("not-visible")
                if (sorted) {
                    productList.innerHTML = ""
                }
                setTimeout(() => {
                    spinnerBox.classList.add("not-visible")
                    loadsBox.classList.remove("not-visible")

                    if (response.products_size > 0) {
                        productNum.innerHTML = `<p style="margin: 0;">Nous avons trouvé <strong>${response.products_size}</strong> articles pour vous !</p>`
                    }
                    else {
                        productNum.innerHTML = `<p style="margin: 0;">Aucun produit disponible</p>`
                    }

                    data.map(product => {
                        const price = parseFloat(product.PRDPrice || 0).toFixed(0);
                        const discountPrice = product.PRDDiscountPrice > 0 ? parseFloat(product.PRDDiscountPrice).toFixed(0) : null;
                        const viewCount = product.view_count || 0;
                        const productName = product.product_name || 'Produit sans nom';
                        const productSlug = product.PRDSlug || '';

                        productList.innerHTML += `
                            <div class="flavoriz-product-card" onclick="window.location.href='/product-details/${productSlug}'" style="cursor: pointer;">
                                <img src="/media/${product.product_image}" alt="${productName}" class="flavoriz-product-image" />
                                <div class="flavoriz-product-body">
                                    <div class="flavoriz-product-views">
                                        <i class="fi-rs-eye"></i>
                                        <span>${viewCount}+ vues</span>
                                    </div>
                                    <h3 class="flavoriz-product-title">${productName}</h3>
                                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                        <span style="font-size: 20px; font-weight: 700; color: #FF7B2C;">${price} XOF</span>
                                        ${discountPrice ? `<span style="font-size: 14px; color: #9CA3AF; text-decoration: line-through;">${discountPrice} XOF</span>` : ''}
                                    </div>
                                    <button class="flavoriz-product-card-btn" onclick="event.stopPropagation(); window.location.href='/product-details/${productSlug}'">
                                        <i class="fi-rs-eye"></i>
                                        <span>Voir le produit</span>
                                    </button>
                                </div>
                            </div>
                        `

                    })
                    if (maxSize) {

                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `<p style="font-size: 16px; font-weight: 600; color: #6B7280;">Aucun autre produit disponible !</p>`
                    }

                }, 500)


            },
            error: function (error) { }
        })

    }
    handleGetData();
    loadBtn.addEventListener("click", () => {

        visible += 10;

        handleGetData(false);

    })
    $('.mySelect').on('change', function () {

        visible = 10;
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