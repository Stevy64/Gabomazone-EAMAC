/* ============================================
   ACCOUNT DROPDOWN FIX
   Correction du menu déroulant du compte
   Fonctionne sur desktop et mobile
   ============================================ */

(function() {
    'use strict';
    
    function initAccountDropdown() {
        // Desktop
        const accountTrigger = document.getElementById('account-dropdown-trigger');
        const accountMenu = document.getElementById('account-dropdown-menu');
        
        if (accountTrigger && accountMenu) {
            // Vérifier si déjà initialisé
            if (accountTrigger.dataset.initialized === 'true') return;
            accountTrigger.dataset.initialized = 'true';
            
            accountTrigger.addEventListener('click', function(e) {
                // Si le menu est déjà ouvert, on le ferme et on empêche la navigation
                if (accountMenu.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    accountMenu.classList.remove('show');
                    accountMenu.style.display = 'none';
                } else {
                    // Si le menu n'est pas ouvert, on l'ouvre et on empêche la navigation
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Close other menus
                    document.querySelectorAll('.flavoriz-account-menu').forEach(menu => {
                        if (menu !== accountMenu) {
                            menu.classList.remove('show');
                            menu.style.display = 'none';
                        }
                    });
                    accountMenu.classList.add('show');
                    accountMenu.style.display = 'block';
                }
            });
            
            // Close menu when clicking on links
            accountMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', function() {
                    accountMenu.classList.remove('show');
                    accountMenu.style.display = 'none';
                });
            });
        }
        
        // Mobile
        const accountTriggerMobile = document.getElementById('account-dropdown-trigger-mobile');
        const accountMenuMobile = document.getElementById('account-dropdown-menu-mobile');
        
        if (accountTriggerMobile && accountMenuMobile) {
            // Vérifier si déjà initialisé
            if (accountTriggerMobile.dataset.initialized === 'true') return;
            accountTriggerMobile.dataset.initialized = 'true';
            
            accountTriggerMobile.addEventListener('click', function(e) {
                // Si le menu est déjà ouvert, on le ferme et on empêche la navigation
                if (accountMenuMobile.classList.contains('show')) {
                    e.preventDefault();
                    e.stopPropagation();
                    accountMenuMobile.classList.remove('show');
                    accountMenuMobile.style.display = 'none';
                } else {
                    // Si le menu n'est pas ouvert, on l'ouvre et on empêche la navigation
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Close other menus
                    document.querySelectorAll('.flavoriz-account-menu-mobile').forEach(menu => {
                        if (menu !== accountMenuMobile) {
                            menu.classList.remove('show');
                            menu.style.display = 'none';
                        }
                    });
                    accountMenuMobile.classList.add('show');
                    accountMenuMobile.style.display = 'block';
                    
                    // FORCER le positionnement en bas sur mobile
                    if (window.innerWidth <= 768) {
                        accountMenuMobile.style.position = 'fixed';
                        accountMenuMobile.style.top = 'auto';
                        accountMenuMobile.style.bottom = '80px';
                        accountMenuMobile.style.right = '16px';
                        accountMenuMobile.style.left = 'auto';
                        accountMenuMobile.style.transform = 'none';
                        accountMenuMobile.style.margin = '0';
                    }
                }
            });
            
            // Close menu when clicking on links
            accountMenuMobile.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', function() {
                    accountMenuMobile.classList.remove('show');
                    accountMenuMobile.style.display = 'none';
                });
            });
        }
        
        // Close menus when clicking outside (une seule fois)
        if (!window.accountDropdownOutsideClickHandler) {
            window.accountDropdownOutsideClickHandler = function(e) {
                const accountTrigger = document.getElementById('account-dropdown-trigger');
                const accountMenu = document.getElementById('account-dropdown-menu');
                const accountTriggerMobile = document.getElementById('account-dropdown-trigger-mobile');
                const accountMenuMobile = document.getElementById('account-dropdown-menu-mobile');
                
                if (accountMenu && accountTrigger && !accountTrigger.contains(e.target) && !accountMenu.contains(e.target)) {
                    accountMenu.classList.remove('show');
                    accountMenu.style.display = 'none';
                }
                if (accountMenuMobile && accountTriggerMobile && !accountTriggerMobile.contains(e.target) && !accountMenuMobile.contains(e.target)) {
                    accountMenuMobile.classList.remove('show');
                    accountMenuMobile.style.display = 'none';
                }
            };
            document.addEventListener('click', window.accountDropdownOutsideClickHandler);
        }
    }
    
    // Initialiser
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAccountDropdown);
    } else {
        initAccountDropdown();
    }
})();

