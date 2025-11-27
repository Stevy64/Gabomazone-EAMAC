
window.onload = function () {
    console.log(vendorSlug)
    const productsList = document.getElementById("products-list");

    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const itemsNum = document.getElementById("items-number")
    const mySelect = document.getElementById("mySelect");
    //const empty = document.getElementById("empty");

    // const childern = ulCategory


    let visible = 10;
    const handleGetVendorDetails = (sorted) => {
        $.ajax({
            type: "GET",
            url: `/vendor-details-ajax/`,
            data: {
                "num_products": visible,
                "order_by": mySelect.value,
                "vendor_slug": vendorSlug,
            },
            success: function (response) {
                const data = response.data;

                const maxSize = response.max
                emptyBox.classList.add("not-visible")
                spinnerBox.classList.remove("not-visible")
                loadsBox.classList.add("not-visible")
                if (sorted) {
                    productsList.innerHTML = ""
                }
                setTimeout(() => {
                    spinnerBox.classList.add("not-visible")
                    loadsBox.classList.remove("not-visible")
                    console.log(data)
                    if (response.products_size > 0) {

                        itemsNum.innerHTML = `${response.products_size}`


                        data.map(product => {
                            let discount = ""
                            if (product.PRDDiscountPrice > 0) {
                                discount = `$${product.PRDDiscountPrice}`
                            }

                            if (product.promotional == "New") {
                                promotional = 'new'
                            }
                            if (product.promotional == "Hot") {
                                promotional = 'hot'
                            }
                            let text = product.product_name
                            let textSlice = text.slice(0, 39);



                            productsList.innerHTML += `<div class="col-lg-1-5 col-md-4 col-12 col-sm-6">
                            <div class="product-cart-wrap mb-30">
                                <div class="product-img-action-wrap">
                                    <div class="product-img product-img-zoom">
                                        <a href="/product-details/${product.PRDSlug}">
                                            <img class="default-img" width="182" height="182" style="width:182px;height:182px;" src="/media/${product.product_image}" alt="${product.product_name}" />
                                            <img class="hover-img" width="182" height="182" style="width:182px;height:182px;" src="/media/${product.product_image}" alt="${product.product_name}" />
                                        </a>
                                    </div>
                                    <div class="product-action-1">
                                        
                                    </div>
                                    <div class="product-badges product-badges-position product-badges-mrg">
                                        <span class="${promotional}">${product.promotional}</span>
                                    </div>
                                </div>
                                <div class="product-content-wrap">
                                    <div class="product-category">
                                        
                                    </div>
                                    <h2><a href="/product-details/${product.PRDSlug}">${textSlice}</a></h2>
                                    <div class="product-rate-cover">
                                        <div class="product-rate d-inline-block">
                                            <div class="product-rating" style="width: ${product.feedbak_average}%"></div>
                                        </div>
                                        <span class="font-small ml-5 text-muted"> (${product.feedbak_number})</span>
                                    </div>
                                    <div>
                                       
                                    </div>
                                    <div class="product-card-bottom">
                                        <div class="product-price">
                                            <span>$${product.PRDPrice}</span>
                                            <span class="old-price">${discount}</span>
                                        </div>
                                        <div class="add-cart">
                                            <a class="add" href="/product-details/${product.PRDSlug}"><i class="fi-rs-shopping-cart mr-5"></i>View </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>`
                        })
                        if (maxSize) {

                            loadsBox.classList.add("not-visible")
                            emptyBox.classList.remove("not-visible")
                            emptyBox.innerHTML = `<strong class="current-price text-brand">No More Orders !</strong>`
                        }
                    }
                    else {
                        itemsNum.innerHTML = `0`
                        productsList.innerHTML = ``
                        //empty.classList.remove("not-visible")
                        loadsBox.classList.add("not-visible")
                    }

                }, 500)


            },
            error: function (error) {
                console.log(error)
            }
        })

    }
    handleGetVendorDetails();
    loadBtn.addEventListener("click", () => {

        visible += 10;

        handleGetVendorDetails(false);

    })

    $('.mySelect').on('change', function () {

        visible = 10;
        handleGetVendorDetails(true);
    })

}