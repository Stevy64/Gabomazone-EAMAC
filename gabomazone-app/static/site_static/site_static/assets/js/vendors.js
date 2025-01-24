
window.onload = function () {

    const vendorsList = document.getElementById("vendors-list");

    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const vendorsNum = document.getElementById("vendors-number")
    //const empty = document.getElementById("empty");

    // const childern = ulCategory


    let visible = 12;
    const handleGetVendors = (sorted) => {
        $.ajax({
            type: "GET",
            url: `/vendors-ajax/`,
            data: {
                "num_vendors": visible,
            },
            success: function (response) {
                const data = response.data;

                const maxSize = response.max
                emptyBox.classList.add("not-visible")
                spinnerBox.classList.remove("not-visible")
                loadsBox.classList.add("not-visible")

                setTimeout(() => {
                    spinnerBox.classList.add("not-visible")
                    loadsBox.classList.remove("not-visible")
                    console.log(data)
                    if (response.vendors_size > 0) {

                        vendorsNum.innerHTML = `${response.vendors_size}`


                        data.map(vendor => {

                            let d = new Date(vendor.date);
                            //let amount = Number(order.amount).toFixed(2)

                            vendorsList.innerHTML += `<!--start vendor card-->
                            <div class="col-lg-3 col-md-6 col-12 col-sm-6">
                                <div class="vendor-wrap mb-40">
                                    <div class="vendor-img-action-wrap">
                                        <div class="vendor-img">
                                            <a href="/vendor-details/${vendor.slug}">
                                                <img class="default-img" src="/media/${vendor.image}" width="144" height="144" style="width:144px;height:144px;" alt="" />
                                            </a>
                                        </div>
                                        <div class="product-badges product-badges-position product-badges-mrg">
                                            
                                        </div>
                                    </div>
                                    <div class="vendor-content-wrap">
                                        <div class="d-flex justify-content-between align-items-end mb-30">
                                            <div>
                                                <div class="product-category">
                                                    <span class="text-muted">Since ${d.getFullYear()}</span>
                                                </div>
                                                <h4 class="mb-5"><a href="/vendor-details/${vendor.slug}">${vendor.display_name}</a></h4>
            
                                            </div>
            
                                            <div class="mb-10">
                                                
                                            </div>
                                        </div>
            
                                        <div class="vendor-info mb-30">
                                            <ul class="contact-infor text-muted">
                                                <li><img src="/static/assets/imgs/theme/icons/icon-location.svg" alt="" /><strong>Address: </strong> <span>${vendor.address}, ${vendor.city} ${vendor.post_code} ${vendor.country}</span></li>
                                                <li><img src="/static/assets/imgs/theme/icons/icon-contact.svg" alt="" /><strong>Call Us:</strong><span>${vendor.mobile_number}</span></li>
                                            </ul>
                                        </div>
                                        <a href="/vendor-details/${vendor.slug}" class="btn btn-xs">Visit Store <i class="fi-rs-arrow-small-right"></i></a>
                                    </div>
                                </div>
                            </div>
                            <!--end vendor card-->`
                        })
                        if (maxSize) {

                            loadsBox.classList.add("not-visible")
                            emptyBox.classList.remove("not-visible")
                            emptyBox.innerHTML = `<strong class="current-price text-brand">No More Vendors !</strong>`
                        }
                    }
                    else {
                        vendorsNum.innerHTML = `0`
                        vendorsList.innerHTML = ``
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
    handleGetVendors();
    loadBtn.addEventListener("click", () => {

        visible += 12;

        handleGetVendors(false);

    })

}