window.onload =  function () {

    //console.log("jffffff")
    const superCategory = document.getElementById("super_category");
    const mainCategory = document.getElementById("main_category");
    const subCategory = document.getElementById("sub_category");
    const miniCategory = document.getElementById("mini_category");

    const handleGetSuperCategories = () => {
        $.ajax({
            type: "GET",

            url: "/supplier-categories-ajax/",

            success: function (response) {
                const dataSuperCategory = response.super_category
                //console.log(dataSuperCategory)

                superCategory.innerHTML = ""
                dataSuperCategory.map(super_category => {
                    //console.log(subspecialization)
                    superCategory.innerHTML += `<option  value="${super_category.id}">${super_category.name}</option>`
                })


            },
            error: function (error) {
                console.log(error)
            },

        })
    }

    const handleGetMainCategories = (value) => {
        $.ajax({
            type: "GET",

            url: "/supplier-categories-ajax/",
            data: {
                "super_category_ajax": value,
            },
            success: function (response) {
                const dataMainCategory = response.main_category
                mainCategory.innerHTML = ""
                dataMainCategory.map(main_category => {

                    mainCategory.innerHTML += `<option  value="${main_category.id}">${main_category.name}</option>`
                })


            },
            error: function (error) {
                console.log(error)
            },

        })
    }

    const handleGetSubCategories = (value) => {
        $.ajax({
            type: "GET",

            url: "/supplier-categories-ajax/",
            data: {
                "main_category_ajax": value,
            },
            success: function (response) {
                const dataSubCategory = response.sub_category
                //console.log(dataSubCategory)
                subCategory.innerHTML = ""
                dataSubCategory.map(sub_category => {

                    subCategory.innerHTML += `<option  value="${sub_category.id}">${sub_category.name}</option>`
                })


            },
            error: function (error) {
                console.log(error)
            },

        })
    }

    const handleGetMiniCategories = (value) => {
        $.ajax({
            type: "GET",

            url: "/supplier-categories-ajax/",
            data: {
                "sub_category_ajax": value,
            },
            success: function (response) {
                const dataMiniCategory = response.mini_category
                //console.log(dataMiniCategory)
                miniCategory.innerHTML = ""
                dataMiniCategory.map(mini_category => {

                    miniCategory.innerHTML += `<option  value="${mini_category.id}">${mini_category.name}</option>`
                })


            },
            error: function (error) {
                console.log(error)
            },

        })
    }


    setTimeout(() => {
        handleGetMainCategories(superCategory.value);
    }, 400)
    
    setTimeout(() => {
        let mainSelected = document.getElementById("main_category");
        handleGetSubCategories(mainSelected.value);
    }, 1000)
    
    setTimeout(() => {
        let subSleceted = document.getElementById("sub_category");
        handleGetMiniCategories(subSleceted.value);
    }, 1900)


    $('.super_category').on('change', function () {

        const superCategoryValue = $(this).val();
        handleGetMainCategories(superCategoryValue);
        setTimeout(() => {
            let mainSelected = document.getElementById("main_category");
            handleGetSubCategories(mainSelected.value);
        }, 1000)
        setTimeout(() => {
            let subSleceted = document.getElementById("sub_category");
            handleGetMiniCategories(subSleceted.value);
        }, 1900)

    })

    $('.main_category').on('change', function () {
        const mainCategoryValue = $(this).val();
        handleGetSubCategories(mainCategoryValue);

        setTimeout(() => {
            let subSleceted = document.getElementById("sub_category");
            handleGetMiniCategories(subSleceted.value);
        }, 1000)

    })

    $('.sub_category').on('change', function () {
        const subCategoryValue = $(this).val();
        setTimeout(() => {
            handleGetMiniCategories(subCategoryValue);
        }, 1000)

    })
}