/**
 * Smart Header - Barre de navigation intelligente
 * Se rétracte légèrement lors du scroll vers le bas
 * Optimisé pour mobile avec animation fluide
 * IMPORTANT: Le header reste TOUJOURS visible, il ne disparaît JAMAIS
 */
(function() {
    'use strict';
    
    const header = document.querySelector('.flavoriz-header');
    if (!header) return;
    
    let lastScrollTop = 0;
    let scrollThreshold = 30;
    let ticking = false;
    let isMobile = window.innerWidth <= 768;
    
    // Détecter les changements de taille d'écran
    window.addEventListener('resize', function() {
        isMobile = window.innerWidth <= 768;
    }, { passive: true });
    
    function updateHeader() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > scrollThreshold) {
            if (!header.classList.contains('scrolled')) {
                header.classList.add('scrolled');
            }
        } else {
            if (header.classList.contains('scrolled')) {
                header.classList.remove('scrolled');
            }
        }
        
        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
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
    
    // FORCER le header à rester TOUJOURS visible - PROTECTION MAXIMALE
    function enforceHeaderVisibility() {
        header.style.setProperty('position', 'fixed', 'important');
        header.style.setProperty('top', '0', 'important');
        header.style.setProperty('left', '0', 'important');
        header.style.setProperty('right', '0', 'important');
        header.style.setProperty('z-index', '9999', 'important');
        header.style.setProperty('display', 'block', 'important');
        header.style.setProperty('visibility', 'visible', 'important');
        header.style.setProperty('opacity', '1', 'important');
        header.style.setProperty('transform', 'translateY(0)', 'important');
    }
    
    // Appliquer immédiatement
    enforceHeaderVisibility();
    
    // Réappliquer toutes les 100ms pour garantir la visibilité
    setInterval(enforceHeaderVisibility, 100);
    
    // Observer les mutations pour empêcher la disparition
    const observer = new MutationObserver(function(mutations) {
        let needsFix = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes') {
                if (mutation.attributeName === 'style') {
                    const style = header.style;
                    if (style.display === 'none' || 
                        style.visibility === 'hidden' || 
                        style.opacity === '0' ||
                        (style.transform && style.transform.includes('translateY') && !style.transform.includes('translateY(0)'))) {
                        needsFix = true;
                    }
                }
                if (mutation.attributeName === 'class') {
                    // Vérifier si une classe cache le header
                    if (header.classList.contains('hide') || 
                        header.classList.contains('hidden') ||
                        header.classList.contains('d-none')) {
                        needsFix = true;
                    }
                }
            }
        });
        
        if (needsFix) {
            enforceHeaderVisibility();
            // Retirer les classes qui cachent
            header.classList.remove('hide', 'hidden', 'd-none');
        }
    });
    
    observer.observe(header, {
        attributes: true,
        attributeFilter: ['style', 'class'],
        childList: false,
        subtree: false
    });
    
    // Observer aussi le document pour détecter les changements de style inline
    const styleObserver = new MutationObserver(function() {
        enforceHeaderVisibility();
    });
    
    styleObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false
    });
    
    // Protection supplémentaire : écouter les événements qui pourraient cacher le header
    document.addEventListener('scroll', function() {
        enforceHeaderVisibility();
    }, { passive: true });
    
    window.addEventListener('resize', function() {
        enforceHeaderVisibility();
    }, { passive: true });
})();
