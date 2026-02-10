/* ============================================
   MOBILE SEARCH EXPANSION
   Expansion de la barre de recherche sur mobile
   Icône seulement par défaut, se déploie au clic
   ============================================ */

(function() {
    'use strict';
    
    const searchMobile = document.querySelector('.flavoriz-search-mobile');
    const searchTrigger = document.querySelector('.flavoriz-search-trigger-mobile');
    const searchInput = document.getElementById('mobile-search-input');
    const searchForm = document.querySelector('.flavoriz-search-form-mobile');
    const searchClose = document.querySelector('.flavoriz-search-close-mobile');
    const headerActions = document.querySelector('.flavoriz-header-actions-mobile');
    
    if (!searchMobile || !searchTrigger) return;
    
    // Ouvrir la recherche au clic sur l'icône
    searchTrigger.addEventListener('click', function() {
        searchMobile.classList.add('expanded');
        if (searchForm) {
            searchForm.style.display = 'flex';
        }
        // Cacher les autres icônes temporairement
        if (headerActions) {
            const icons = headerActions.querySelectorAll('.flavoriz-icon-btn-mobile');
            icons.forEach(icon => {
                icon.style.display = 'none';
            });
        }
        // Focus sur l'input après un court délai pour l'animation
        setTimeout(() => {
            if (searchInput) {
                searchInput.focus();
            }
        }, 100);
    });
    
    // Expansion au focus de l'input (au cas où)
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            searchMobile.classList.add('expanded');
            if (searchForm) {
                searchForm.style.display = 'flex';
            }
            // Cacher les autres icônes temporairement
            if (headerActions) {
                const icons = headerActions.querySelectorAll('.flavoriz-icon-btn-mobile');
                icons.forEach(icon => {
                    icon.style.display = 'none';
                });
            }
        });
    }
    
    // Fermeture au clic sur close
    if (searchClose) {
        searchClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeSearch();
        });
    }
    
    function closeSearch() {
        searchMobile.classList.remove('expanded');
        if (searchForm) {
            searchForm.style.display = 'none';
        }
        if (searchInput) {
            searchInput.blur();
            searchInput.value = '';
        }
        // Réafficher les icônes
        if (headerActions) {
            const icons = headerActions.querySelectorAll('.flavoriz-icon-btn-mobile');
            icons.forEach(icon => {
                icon.style.display = 'flex';
            });
        }
    }
    
    // Fermeture au blur si vide
    if (searchInput) {
        searchInput.addEventListener('blur', function() {
            setTimeout(() => {
                if (!searchInput.value.trim()) {
                    closeSearch();
                }
            }, 200);
        });
    }
    
    // Empêcher la fermeture lors de la soumission
    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            // Garder l'expansion pendant la recherche
            searchMobile.classList.add('expanded');
            if (searchForm) {
                searchForm.style.display = 'flex';
            }
        });
    }
})();

