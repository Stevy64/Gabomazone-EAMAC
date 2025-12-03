window.onload = function () {
    // Fonction pour formater un prix avec des espaces
    function formatPrice(priceValue) {
        const price = parseFloat(priceValue || 0);
        const intPrice = Math.floor(price);
        return intPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }

    const productList = document.getElementById("products-list");

    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const productNum = document.getElementById("product-num")
    const mySelect = document.getElementById("mySelect");
    const selectStatus = document.getElementById("select-status");
    //console.log(productNum);



    let visible = 5;
    const handleGetData = (sorted, sortedStatus) => {
        $.ajax({
            type: "GET",
            url: `/supplier-products-list-ajax/`,
            data: {
                "num_products": visible,
                "order_by": mySelect.value,
                'order_by_status': selectStatus.value,
            },
            success: function (response) {
                const data = response.data;
                console.log(data);
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
                        productNum.innerHTML = `<p>Nous avons trouvé <strong class="text-brand">${response.products_size}</strong> produit(s) pour vous !</p>`
                    }
                    else {
                        productNum.innerHTML = ` <p>Aucun produit trouvé</p>`
                    }

                    data.map(product => {
                        let discount = ""
                        if (product.PRDDiscountPrice > 0) {
                            discount = `${product.PRDDiscountPrice} FCFA`
                        }
                        if (product.PRDISactive) {
                            productStatus = 'Active'
                            alertStatus = 'alert-success'
                        } else {
                            productStatus = 'Inactive'
                            alertStatus = 'alert-danger'
                        }
                        let text = product.product_name
                        let textSlice = text.slice(0, 39);
                        let d = new Date(product.date);

                        productList.innerHTML += `<article class="itemlist">
                        <div class="row align-items-center">
                           
                            <div class="col-lg-4 col-sm-4 col-8 flex-grow-1 col-name">
                                <a class="itemside" href="/product-details/${product.PRDSlug}">
                                    <div class="left">
                                        <img src="/media/${product.product_image}" width="100" height="100"   style="width:100px;height:100px;"  class="img-sm img-thumbnail" alt="${product.product_name}" />
                                    </div>
                                    <div class="info">
                                        <h6 class="mb-0">${textSlice}</h6>
                                    </div>
                                </a>
                            </div>
                            <div class="col-lg-2 col-sm-2 col-4 col-price"><span>${formatPrice(product.PRDPrice)} FCFA</span></div>
                            <div class="col-lg-2 col-sm-2 col-4 col-status">
                                <span class="badge rounded-pill ${alertStatus}">${productStatus}</span>
                            </div>
                            <div class="col-lg-1 col-sm-2 col-4 col-date">
                                <span>${d.toDateString()}</span>
                            </div>
                            <div class="col-lg-2 col-sm-2 col-4 col-action text-end">
                                <a href="/supplier-edit-product/${product.id}/" class="btn btn-sm font-sm rounded btn-brand"> <i class="material-icons md-edit"></i> Edit </a>
                                <button type="button" onclick="openDeleteConfirmModal(${product.id}, '${product.product_name.replace(/'/g, "\\'")}')" class="btn btn-sm font-sm btn-danger rounded"> <i class="material-icons md-delete_forever"></i> Delete </button>
                            </div>
                        </div>
                        <!-- row .// -->
                    </article>`

                    })
                    if (maxSize) {

                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `<strong class="current-price text-brand">Plus de produits ! Vous avez atteint la fin de la liste.</strong>`
                    }

                }, 500)


            },
            error: function (error) { }
        })

    }
    handleGetData();
    loadBtn.addEventListener("click", () => {

        visible += 5;

        handleGetData(false);

    })
    $('.mySelect').on('change', function () {

        visible = 5;
        handleGetData(true);
    })

    $('.select-status').on('change', function () {

        visible = 5;
        handleGetData(true);
    })




}