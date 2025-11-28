/* ============================================
   DESKTOP SEARCH EXPANSION
   Expansion de la barre de recherche sur desktop
   S'agrandit au focus comme sur mobile
   Fonctionne sur TOUTES les pages
   ============================================ */

(function() {
    'use strict';
    
    let initialized = false;
    
    function initSearchExpansion() {
        const searchDesktop = document.querySelector('.flavoriz-header-actions-desktop .flavoriz-search');
        if (!searchDesktop) {
            // Réessayer après un court délai si l'élément n'existe pas encore
            setTimeout(initSearchExpansion, 100);
            return;
        }
        
        // Marquer comme initialisé pour cet élément
        if (searchDesktop.dataset.initialized === 'true') return;
        searchDesktop.dataset.initialized = 'true';
        
        const searchInput = searchDesktop.querySelector('input');
        if (!searchInput) return;
        
        // Largeur initiale
        const initialWidth = '280px';
        const expandedWidth = '400px';
        
        // S'assurer que la largeur initiale est définie
        if (!searchDesktop.style.width || searchDesktop.style.width === '') {
            searchDesktop.style.width = initialWidth;
        }
        
        // Vérifier si déjà initialisé pour cet input
        if (searchInput.dataset.initialized === 'true') return;
        searchInput.dataset.initialized = 'true';
        
        // Expansion au focus
        searchInput.addEventListener('focus', function() {
            searchDesktop.style.width = expandedWidth;
            searchDesktop.style.transition = 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        });
        
        // Réduction au blur si vide
        searchInput.addEventListener('blur', function() {
            setTimeout(() => {
                if (!searchInput.value.trim()) {
                    searchDesktop.style.width = initialWidth;
                }
            }, 200);
        });
        
        // Garder la largeur si du texte est présent au chargement
        if (searchInput.value && searchInput.value.trim()) {
            searchDesktop.style.width = expandedWidth;
        }
    }
    
    // Initialiser immédiatement si le DOM est déjà chargé
    function startInit() {
        setTimeout(initSearchExpansion, 100);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startInit);
    } else {
        startInit();
    }
    
    // Réinitialiser après les changements de page (pour les SPA ou AJAX)
    const observer = new MutationObserver(function(mutations) {
        const searchDesktop = document.querySelector('.flavoriz-header-actions-desktop .flavoriz-search');
        if (searchDesktop && searchDesktop.dataset.initialized !== 'true') {
            setTimeout(initSearchExpansion, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Réinitialiser aussi après le chargement complet de la page
    window.addEventListener('load', function() {
        setTimeout(initSearchExpansion, 200);
    });
})();

