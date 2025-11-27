/* ============================================
   CUSTOM DROPDOWN - Design Moderne
   Remplace le select natif par un dropdown personnalisé
   ============================================ */

(function() {
    'use strict';
    
    function createCustomDropdown(selectElement) {
        // Créer le wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'flavoriz-custom-dropdown';
        
        // Créer le bouton trigger
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'flavoriz-dropdown-trigger';
        button.innerHTML = `
            <span class="flavoriz-dropdown-text">${selectElement.options[selectElement.selectedIndex].text}</span>
            <svg class="flavoriz-dropdown-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
        `;
        
        // Créer le menu dropdown
        const menu = document.createElement('div');
        menu.className = 'flavoriz-dropdown-menu';
        
        // Créer les options
        Array.from(selectElement.options).forEach((option, index) => {
            const item = document.createElement('div');
            item.className = 'flavoriz-dropdown-item';
            if (option.selected) {
                item.classList.add('active');
            }
            item.textContent = option.text;
            item.dataset.value = option.value;
            
            item.addEventListener('click', function() {
                // Mettre à jour le select original
                selectElement.value = option.value;
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Mettre à jour le texte du bouton
                button.querySelector('.flavoriz-dropdown-text').textContent = option.text;
                
                // Mettre à jour les classes actives
                menu.querySelectorAll('.flavoriz-dropdown-item').forEach(item => {
                    item.classList.remove('active');
                });
                item.classList.add('active');
                
                // Fermer le menu
                menu.classList.remove('open');
                button.classList.remove('open');
            });
            
            menu.appendChild(item);
        });
        
        // Toggle menu
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = menu.classList.contains('open');
            
            // Fermer tous les autres dropdowns
            document.querySelectorAll('.flavoriz-dropdown-menu.open').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('open');
                    m.parentElement.querySelector('.flavoriz-dropdown-trigger').classList.remove('open');
                }
            });
            
            menu.classList.toggle('open', !isOpen);
            button.classList.toggle('open', !isOpen);
        });
        
        // Fermer au clic extérieur
        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                menu.classList.remove('open');
                button.classList.remove('open');
            }
        });
        
        // Assembler
        wrapper.appendChild(button);
        wrapper.appendChild(menu);
        
        // Cacher complètement le select natif
        selectElement.style.cssText = 'position: absolute !important; opacity: 0 !important; width: 1px !important; height: 1px !important; pointer-events: none !important; z-index: -1 !important; overflow: hidden !important; clip: rect(0,0,0,0) !important;';
        
        // Insérer le wrapper avant le select
        selectElement.parentNode.insertBefore(wrapper, selectElement);
        wrapper.appendChild(selectElement);
        
        return wrapper;
    }
    
    // Initialiser tous les selects avec la classe sorting
    function init() {
        document.querySelectorAll('select.sorting, select.mySelect, #mySelect').forEach(select => {
            if (!select.parentElement.classList.contains('flavoriz-custom-dropdown')) {
                createCustomDropdown(select);
            }
        });
    }
    
    // Observer les nouveaux selects ajoutés dynamiquement
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    const selects = node.querySelectorAll ? node.querySelectorAll('select.sorting, select.mySelect, #mySelect') : [];
                    selects.forEach(select => {
                        if (!select.parentElement.classList.contains('flavoriz-custom-dropdown')) {
                            createCustomDropdown(select);
                        }
                    });
                }
            });
        });
    });
    
    // Démarrer l'observation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            init();
            observer.observe(document.body, { childList: true, subtree: true });
        });
    } else {
        init();
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();

