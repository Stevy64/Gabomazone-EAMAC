window.onload = function () {

    const ordersList = document.getElementById("orders-list");

    const loadBtn = document.getElementById("load-btn");
    const spinnerBox = document.getElementById("spinner-box");
    const emptyBox = document.getElementById("empty-box");
    const loadsBox = document.getElementById("loading-box");
    const orderNum = document.getElementById("order-number")
    const empty = document.getElementById("empty");

    // const childern = ulCategory


    let visible = 10;
    const handleGetOrders = (sorted) => {
        $.ajax({
            type: "GET",
            url: `/accounts/orders-ajax/`,
            data: {
                "num_products": visible,
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

                    if (response.orders_size > 0) {
                        orderNum.innerHTML = `Your Orders(${response.orders_size})</p>`


                        data.map(order => {
                            let is_finished = order.is_finished
                            let d = new Date(order.order_date);
                            let amount = Number(order.amount).toFixed(2)

                            if (is_finished) {
                                is_finished = "Yes"
                            }
                            else {
                                is_finished = "No"
                            }
                            ordersList.innerHTML += `   <tr>
                            <td>#${order.id}</td>
                            <td>${d.toDateString()}</td>
                            <td>$${amount} for 2 item</td>
                            
                            <td>${is_finished}</td>
                            <td></td>
                            <td><a href="order/${order.id}/" class="btn-small d-block">${order.status}</a></td>
                        </tr>`
                        })
                        if (maxSize) {

                            loadsBox.classList.add("not-visible")
                            emptyBox.classList.remove("not-visible")
                            emptyBox.innerHTML = `<strong class="current-price text-brand">No More Orders !</strong>`
                        }
                    }
                    else {
                        orderNum.innerHTML = `Your Orders(0)</p>`
                        ordersList.innerHTML = ``
                        empty.classList.remove("not-visible")
                        loadsBox.classList.add("not-visible")
                    }

                }, 500)


            },
            error: function (error) { }
        })

    }
    handleGetOrders();
    loadBtn.addEventListener("click", () => {

        visible += 10;

        handleGetOrders(false);

    })

}