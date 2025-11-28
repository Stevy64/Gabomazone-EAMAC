/**
 * Smart Header - Barre de navigation intelligente
 * Se rétracte légèrement lors du scroll vers le bas
 */
(function() {
    'use strict';
    
    const header = document.querySelector('.flavoriz-header');
    if (!header) return;
    
    let lastScrollTop = 0;
    let scrollThreshold = 50; // Seuil de scroll pour déclencher l'animation
    let ticking = false;
    
    function updateHeader() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > scrollThreshold) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        lastScrollTop = scrollTop;
        ticking = false;
    }
    
    function onScroll() {
        if (!ticking) {
            window.requestAnimationFrame(updateHeader);
            ticking = true;
        }
    }
    
    // Écouter le scroll
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // Vérifier l'état initial
    if (window.pageYOffset > scrollThreshold) {
        header.classList.add('scrolled');
    }
})();


