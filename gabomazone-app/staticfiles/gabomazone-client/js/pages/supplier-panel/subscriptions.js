// Variables globales pour le calcul du boost
    let selectedProductPrice = 0;
    let selectedBoostPercentage = 0;
    let selectedBoostPricePerWeek = 0;
    
    // Fonction pour mettre à jour l'affichage du prix du boost
    function updateBoostPriceDisplay() {
        const productPriceDisplay = document.getElementById('product-price-display');
        const boostPercentageDisplay = document.getElementById('boost-percentage-display');
        const boostUnitPrice = document.getElementById('boost-unit-price');
        const boostTotalPrice = document.getElementById('boost-total-price');
        const boostPriceDisplay = document.getElementById('boost-price-display');
        const durationSelect = document.getElementById('duration-select');
        const selectedDurationText = document.getElementById('selected-duration-text');
        
        if (selectedProductPrice > 0 && selectedBoostPricePerWeek > 0) {
            // Afficher le prix du produit
            if (productPriceDisplay) {
                productPriceDisplay.textContent = selectedProductPrice.toLocaleString('fr-FR') + ' FCFA';
            }
            
            // Afficher le pourcentage de boost
            if (boostPercentageDisplay) {
                boostPercentageDisplay.textContent = selectedBoostPercentage.toFixed(1) + '%';
            }
            
            // Afficher le prix unitaire par semaine
            if (boostUnitPrice) {
                boostUnitPrice.textContent = selectedBoostPricePerWeek.toLocaleString('fr-FR') + ' FCFA / semaine';
            }
            
            // Calculer le prix total selon la durée
            const days = durationSelect ? parseInt(durationSelect.value) || 7 : 7;
            const weeks = days / 7;
            const totalPrice = selectedBoostPricePerWeek * weeks;
            
            if (boostTotalPrice) {
                boostTotalPrice.textContent = totalPrice.toLocaleString('fr-FR') + ' FCFA';
            }
            
            // Mettre à jour l'affichage principal
            if (boostPriceDisplay) {
                boostPriceDisplay.innerHTML = selectedBoostPricePerWeek.toLocaleString('fr-FR') + ' FCFA <span>/ produit / semaine</span>';
            }
        } else {
            // Réinitialiser l'affichage
            if (productPriceDisplay) productPriceDisplay.textContent = '-';
            if (boostPercentageDisplay) boostPercentageDisplay.textContent = '-';
            if (boostUnitPrice) boostUnitPrice.textContent = '-';
            if (boostTotalPrice) boostTotalPrice.textContent = '-';
            if (boostPriceDisplay) {
                boostPriceDisplay.innerHTML = 'Sélectionnez un produit <span>pour voir le prix</span>';
            }
        }
    }
    
    // Custom Dropdown for Product Selection
    const productDropdown = document.getElementById('customDropdownProduct');
    const productSelect = document.getElementById('product-select');
    
    if (productDropdown && productSelect) {
        const trigger = productDropdown.querySelector('.custom-dropdown-trigger');
        const menu = productDropdown.querySelector('.custom-dropdown-menu');
        const options = menu.querySelectorAll('.dropdown-option');
        const selectedText = trigger.querySelector('.dropdown-selected-text');
        
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            productDropdown.classList.toggle('active');
        });
        
        options.forEach(option => {
            option.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const price = parseFloat(this.getAttribute('data-price')) || 0;
                const boostPercentage = parseFloat(this.getAttribute('data-boost-percentage')) || 0;
                const boostPricePerWeek = parseFloat(this.getAttribute('data-boost-price')) || 0;
                const category = this.getAttribute('data-category') || '';
                
                // Mettre à jour les variables globales
                selectedProductPrice = price;
                selectedBoostPercentage = boostPercentage;
                selectedBoostPricePerWeek = boostPricePerWeek;
                
                // Mettre à jour le select
                productSelect.value = value;
                
                // Mettre à jour le texte affiché (sans le prix dans le dropdown)
                const productName = this.textContent.split(' - ')[0];
                selectedText.textContent = productName || 'Sélectionnez un produit';
                
                // Mettre à jour l'affichage du prix
                updateBoostPriceDisplay();
                
                options.forEach(opt => opt.removeAttribute('data-selected'));
                this.setAttribute('data-selected', 'true');
                
                productDropdown.classList.remove('active');
            });
        });
        
        document.addEventListener('click', function(e) {
            if (!productDropdown.contains(e.target)) {
                productDropdown.classList.remove('active');
            }
        });
    }
    
    // Custom Dropdown for Duration Selection
    const durationDropdown = document.getElementById('customDropdownDuration');
    const durationSelect = document.getElementById('duration-select');
    
    if (durationDropdown && durationSelect) {
        const trigger = durationDropdown.querySelector('.custom-dropdown-trigger');
        const menu = durationDropdown.querySelector('.custom-dropdown-menu');
        const options = menu.querySelectorAll('.dropdown-option');
        const selectedText = trigger.querySelector('.dropdown-selected-text');
        const durationText = document.getElementById('selected-duration-text');
        
        const durationLabels = {
            '7': '1 semaine',
            '14': '2 semaines',
            '30': '1 mois'
        };
        
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            durationDropdown.classList.toggle('active');
        });
        
        options.forEach(option => {
            option.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const text = this.textContent;
                
                durationSelect.value = value;
                selectedText.textContent = text;
                
                if (durationText) {
                    durationText.textContent = durationLabels[value] || text;
                }
                
                // Mettre à jour le prix total
                updateBoostPriceDisplay();
                
                options.forEach(opt => opt.removeAttribute('data-selected'));
                this.setAttribute('data-selected', 'true');
                
                durationDropdown.classList.remove('active');
            });
        });
        
        document.addEventListener('click', function(e) {
            if (!durationDropdown.contains(e.target)) {
                durationDropdown.classList.remove('active');
            }
        });
    }
