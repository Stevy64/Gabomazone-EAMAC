window.onload = function () {
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
                        productNum.innerHTML = `<p>We found <strong class="text-brand">${response.products_size}</strong> items for you!</p>`
                    }
                    else {
                        productNum.innerHTML = ` <p>Show 0 Of 0 Product</p>`
                    }

                    data.map(product => {
                        let discount = ""
                        if (product.PRDDiscountPrice > 0) {
                            discount = `$${product.PRDDiscountPrice}`
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
                            <div class="col-lg-2 col-sm-2 col-4 col-price"><span>$${product.PRDPrice}</span></div>
                            <div class="col-lg-2 col-sm-2 col-4 col-status">
                                <span class="badge rounded-pill ${alertStatus}">${productStatus}</span>
                            </div>
                            <div class="col-lg-1 col-sm-2 col-4 col-date">
                                <span>${d.toDateString()}</span>
                            </div>
                            <div class="col-lg-2 col-sm-2 col-4 col-action text-end">
                                <a href="/supplier-edit-product/${product.id}/" class="btn btn-sm font-sm rounded btn-brand"> <i class="material-icons md-edit"></i> Edit </a>
                                <a href="/supplier-products/remeve-product/${product.id}/" class="btn btn-sm font-sm btn-danger rounded"> <i class="material-icons md-delete_forever"></i> Delete </a>
                            </div>
                        </div>
                        <!-- row .// -->
                    </article>`

                    })
                    if (maxSize) {

                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `<strong class="current-price text-brand">No More Products !</strong>`
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