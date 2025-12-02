(function ($) {
    "use strict";


    // Cette fonction est maintenant gérée par le script inline dans index.html
    // pour supporter les périodes de 3, 6 et 12 mois
    // Le code ci-dessous est conservé pour compatibilité mais ne sera utilisé que si loadChartData n'est pas défini
    if (typeof loadChartData === 'undefined') {
        $.ajax({
            type: "GET",
            url: `/chart-ajax/`,
            data: { period: 12 },
            success: function (response) {
                const productCount = response.product_count_list;
                const ordercount = response.order_count_list;
                const labels = response.labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                /*Orders and Products statistics Chart*/
                if ($('#myChart').length) {
                    var ctx = document.getElementById('myChart').getContext('2d');
                    var chart = new Chart(ctx, {
                        // The type of chart we want to create
                        type: 'line',

                        // The data for our dataset
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Ventes',
                                tension: 0.3,
                                fill: true,
                                backgroundColor: 'rgba(4, 209, 130, 0.2)',
                                borderColor: 'rgb(4, 209, 130)',

                                data: ordercount
                            },
                            {
                                label: 'Produits',
                                tension: 0.3,
                                fill: true,
                                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                                borderColor: 'rgb(139, 92, 246)',
                                data: productCount
                            }

                            ]
                        },
                        options: {
                            plugins: {
                                legend: {
                                    labels: {
                                        usePointStyle: true,
                                    },
                                }
                            }
                        }
                    });
                }//end if

            /*Revenue statistics Chart*/
            if ($('#myChart2').length) {
                var ctx = document.getElementById("myChart2");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ["900", "1200", "1400", "1600"],
                        datasets: [
                            {
                                label: "US",
                                backgroundColor: "#5897fb",
                                barThickness: 10,
                                data: [233, 321, 783, 900]
                            },
                            {
                                label: "Europe",
                                backgroundColor: "#7bcf86",
                                barThickness: 10,
                                data: [408, 547, 675, 734]
                            },
                            {
                                label: "Asian",
                                backgroundColor: "#ff9076",
                                barThickness: 10,
                                data: [208, 447, 575, 634]
                            },
                            {
                                label: "Africa",
                                backgroundColor: "#d595e5",
                                barThickness: 10,
                                data: [123, 345, 122, 302]
                            },
                        ]
                    },
                    options: {
                        plugins: {
                            legend: {
                                labels: {
                                    usePointStyle: true,
                                },
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            } //end if

        },
        error: function (error) { }
    })


})(jQuery);