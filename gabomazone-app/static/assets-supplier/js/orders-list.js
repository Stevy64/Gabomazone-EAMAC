window.onload = function () {
    console.log("heeeeeeeeeee")
    const ordersList = document.getElementById("orders-list");

    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const ordersNum = document.getElementById("orders-num")
    const mySelect = document.getElementById("mySelect");
    const selectStatus = document.getElementById("select-status");
    //console.log(productNum);



    let visible = 5;
    const handleGetData = (sorted, sortedStatus) => {
        $.ajax({
            type: "GET",
            url: `/supplier-orders-list-ajax/`,
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
                    ordersList.innerHTML = ""
                }
                setTimeout(() => {
                    spinnerBox.classList.add("not-visible")
                    loadsBox.classList.remove("not-visible")

                    if (response.orders_size > 0) {
                        ordersNum.innerHTML = `<p>We found <strong class="text-brand">${response.orders_size}</strong> items for you!</p>`
                    }
                    else {
                        ordersNum.innerHTML = ` <p>Show 0 Of 0 Product</p>`
                    }

                    data.map(order => {
                        let discount = ""

                        if (order.status == "Underway") {

                            alertStatus = 'alert-warning'
                        }
                        else if (order.status == "COMPLETE") {
                            alertStatus = 'alert-success'

                        }

                        else {

                            alertStatus = 'alert-danger'
                        }

                        let d = new Date(order.order_date);

                        ordersList.innerHTML += `<tr>
                        <td>#${order.id}</td>
                        <td><b>${order.email_client}</b></td>
                        <td>${order.weight}KG</td>
                        <td>$${order.amount}</td>
                        <td><span class="badge rounded-pill ${alertStatus}">${order.status}</span></td>
                        <td>${d.toDateString()}</td>
                        <td class="text-end">
                            <a href="/order-details/${order.id}/" class="btn btn-md rounded font-sm">Detail</a>
                           
                        </td>
                    </tr>`

                    })
                    if (maxSize) {

                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `<strong class="current-price text-brand">No More Orders !</strong>`
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