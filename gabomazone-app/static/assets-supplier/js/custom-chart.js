(function ($) {
    "use strict";


    $.ajax({
        type: "GET",
        url: `/chart-ajax/`,
        data: {},
        success: function (response) {
            const productCount = response.product_count_list;
            const ordercount = response.order_count_list;
            /*Orders and Products statistics Chart*/
            if ($('#myChart').length) {
                var ctx = document.getElementById('myChart').getContext('2d');
                var chart = new Chart(ctx, {
                    // The type of chart we want to create
                    type: 'line',

                    // The data for our dataset
                    data: {
                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                        datasets: [{
                            label: 'Sales',
                            tension: 0.3,
                            fill: true,
                            backgroundColor: 'rgba(4, 209, 130, 0.2)',
                            borderColor: 'rgb(4, 209, 130)',

                            data: ordercount
                        },
                        // {
                        //     label: 'Visitors',
                        //     tension: 0.3,
                        //     fill: true,
                        //     backgroundColor: 'rgba(44, 120, 220, 0.2)',
                        //     borderColor: 'rgba(44, 120, 220)',
                        //     data: [40, 20, 17, 9, 23, 35, 39, 30, 34, 25, 27, 17]
                        // },
                        {
                            label: 'Products',
                            tension: 0.3,
                            fill: true,
                            backgroundColor: 'rgba(380, 200, 230, 0.2)',
                            borderColor: 'rgb(380, 200, 230)',
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