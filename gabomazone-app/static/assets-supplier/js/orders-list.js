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

                    if (response.orders_size > 0) {
                        const orderText = response.orders_size === 1 ? 'commande' : 'commandes';
                        ordersNum.innerHTML = `Nous avons trouvé <strong>${response.orders_size}</strong> ${orderText} pour vous !`
                        loadsBox.classList.remove("not-visible")
                        emptyBox.classList.add("not-visible")
                    }
                    else {
                        ordersNum.innerHTML = `Nous avons trouvé <strong>0</strong> commande(s) pour vous !`
                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `
                            <i class="material-icons">shopping_cart</i>
                            <h3>Aucune commande trouvée</h3>
                            <p>Vous n'avez aucune commande correspondant à vos filtres.</p>
                        `
                    }

                    data.map(order => {
                        let statusClass = "";
                        let statusText = "";

                        if (order.status == "Underway") {
                            statusClass = 'status-underway'
                            statusText = 'En cours'
                        }
                        else if (order.status == "COMPLETE") {
                            statusClass = 'status-complete'
                            statusText = 'Terminée'
                        }
                        else if (order.status == "Refunded") {
                            statusClass = 'status-refunded'
                            statusText = 'Remboursée'
                        }
                        else {
                            statusClass = 'status-pending'
                            statusText = 'En attente'
                        }

                        let d = new Date(order.order_date);
                        let formattedDate = d.toLocaleDateString('fr-FR', { 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric' 
                        });

                        ordersList.innerHTML += `<tr>
                        <td class="order-id-cell">#${order.id}</td>
                        <td class="order-email-cell">${order.email_client || 'N/A'}</td>
                        <td class="order-weight-cell">${order.weight || 0} kg</td>
                        <td class="order-total-cell">${order.amount || 0} XOF</td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td class="order-date-cell">${formattedDate}</td>
                        <td class="text-right">
                            <a href="/order-details/${order.id}/" class="view-details-link">Voir détails</a>
                        </td>
                    </tr>`

                    })
                    if (maxSize) {
                        loadsBox.classList.add("not-visible")
                        emptyBox.classList.remove("not-visible")
                        emptyBox.innerHTML = `
                            <i class="material-icons">shopping_cart</i>
                            <h3>Plus de commandes</h3>
                            <p>Vous avez atteint la fin de la liste.</p>
                        `
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
    $('#mySelect').on('change', function () {
        visible = 5;
        handleGetData(true);
    })

    $('#select-status').on('change', function () {
        visible = 5;
        handleGetData(true);
    })




}