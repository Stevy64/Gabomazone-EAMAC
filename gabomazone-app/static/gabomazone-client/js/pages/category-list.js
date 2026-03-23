$(document).ready(function () {
    // Animation au survol des cartes
    $('.category-card')
        .on('mouseenter', function () {
            $(this).css('transform', 'translateY(-2px)');
        })
        .on('mouseleave', function () {
            $(this).css('transform', 'translateY(0)');
        });

    // Fonctionnalité de recherche
    $('#category-search-input').on('input', function () {
        const searchTerm = $(this).val().toLowerCase().trim();
        const categoryCards = $('.category-card');
        let visibleCount = 0;

        categoryCards.each(function () {
            const categoryName = $(this).attr('data-category-name') || '';

            if (searchTerm === '' || categoryName.includes(searchTerm)) {
                $(this).show();
                visibleCount++;
            } else {
                $(this).hide();
            }
        });

        // Afficher/masquer le message "Aucun résultat"
        const categoriesGrid = $('#categories-grid');
        const noResultsMessage = $('#no-results-message');

        if (visibleCount === 0 && searchTerm !== '') {
            categoriesGrid.hide();
            noResultsMessage.show();
        } else {
            categoriesGrid.show();
            noResultsMessage.hide();
        }
    });

    // Réinitialiser la recherche si l'utilisateur efface tout
    $('#category-search-input').on('keyup', function () {
        if ($(this).val() === '') {
            $('#categories-grid').show();
            $('#no-results-message').hide();
        }
    });
});
