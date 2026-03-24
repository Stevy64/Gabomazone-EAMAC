/**
 * Cart page — preloader, delivery toggle, province/city mapping, Select2.
 */

(function() {
    function hidePreloader() {
        var preloader = document.getElementById('preloader-active');
        if (preloader) {
            preloader.style.display = 'none';
            preloader.style.opacity = '0';
            preloader.style.visibility = 'hidden';
            preloader.style.transition = 'opacity 0.3s ease';
        }
    }
    function removeDuplicateHeaders() {
        var headers = document.querySelectorAll('header.flavoriz-header');
        for (var i = 1; i < headers.length; i++) headers[i].remove();
    }
    function removeDuplicateFooters() {
        var footers = document.querySelectorAll('footer.flavoriz-footer');
        for (var i = 1; i < footers.length; i++) footers[i].remove();
    }
    hidePreloader();
    removeDuplicateHeaders();
    removeDuplicateFooters();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            hidePreloader(); removeDuplicateHeaders(); removeDuplicateFooters();
        });
    }
    window.addEventListener('load', function() {
        setTimeout(function() { hidePreloader(); removeDuplicateHeaders(); removeDuplicateFooters(); }, 100);
    });
})();

/* Toggle « Détails de livraison » : défini dans shop-cart.html (script inline) pour fiabilité.
   Ici : seulement ouvrir la section si le formulaire est invalide à la soumission. */
(function() {
    function bindDeliveryForm() {
        var form = document.getElementById('cart-delivery-form');
        if (!form || form.getAttribute('data-cart-submit-bound') === '1') return;
        form.setAttribute('data-cart-submit-bound', '1');
        form.addEventListener('submit', function(e) {
            var deliveryBody = document.getElementById('cart-delivery-body');
            if (!deliveryBody) return;
            if (!form.checkValidity()) {
                e.preventDefault();
                if (typeof window.expandCartDeliverySection === 'function') {
                    window.expandCartDeliverySection();
                }
                form.reportValidity();
                var firstInvalid = deliveryBody.querySelector('input:invalid, select:invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    setTimeout(function() {
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                }
            }
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindDeliveryForm);
    } else {
        bindDeliveryForm();
    }
})();

(function() {
    var provinceCities = {
        'Estuaire': 'Libreville',
        'Haut-Ogooué': 'Franceville',
        'Moyen-Ogooué': 'Lambaréné',
        'Ngounié': 'Mouila',
        'Nyanga': 'Tchibanga',
        'Ogooué-Ivindo': 'Makokou',
        'Ogooué-Lolo': 'Koulamoutou',
        'Ogooué-Maritime': 'Port-Gentil',
        'Woleu-Ntem': 'Oyem'
    };

    var provinceSelect = document.getElementById('province');
    var cityInput = document.getElementById('city');

    function updateCityFromProvince(selectedProvince) {
        if (cityInput && selectedProvince && provinceCities[selectedProvince]) {
            cityInput.style.transition = 'all 0.3s ease';
            cityInput.style.opacity = '0.7';
            setTimeout(function() {
                cityInput.value = provinceCities[selectedProvince];
                cityInput.style.opacity = '1';
            }, 150);
        } else if (cityInput && !selectedProvince) {
            cityInput.value = '';
        }
    }

    if (provinceSelect && cityInput) {
        provinceSelect.addEventListener('change', function() {
            updateCityFromProvince(this.value.trim());
        });
        /* Ne pas écraser la ville préremplie depuis le profil */
        if (provinceSelect.value && provinceCities[provinceSelect.value.trim()]) {
            var existingCity = (cityInput.value || '').trim();
            if (!existingCity) {
                cityInput.value = provinceCities[provinceSelect.value.trim()];
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        var inputs = document.querySelectorAll('.flavoriz-input');
        inputs.forEach(function(input) {
            if (input.readOnly) return;
            input.addEventListener('focus', function() {
                this.style.borderColor = 'var(--color-orange)';
                this.style.boxShadow = '0 0 0 3px rgba(255, 123, 44, 0.1)';
                this.style.background = 'white';
            });
            input.addEventListener('blur', function() {
                this.style.borderColor = '#E5E7EB';
                this.style.boxShadow = 'none';
                if (!this.readOnly) this.style.background = '#FAFAFA';
            });
        });

        if (typeof jQuery !== 'undefined' && jQuery.fn.select2 && provinceSelect) {
            jQuery(provinceSelect).select2({
                dropdownParent: jQuery(provinceSelect).parent(),
                minimumResultsForSearch: Infinity,
                placeholder: 'Sélectionnez une province',
                allowClear: false,
                width: '100%'
            });
            jQuery(provinceSelect).on('select2:select', function(e) {
                updateCityFromProvince(e.params.data.id);
            });
        }

        if (provinceSelect && cityInput && provinceSelect.value && provinceCities[provinceSelect.value]) {
            var existing = (cityInput.value || '').trim();
            if (!existing) {
                cityInput.value = provinceCities[provinceSelect.value];
            }
        }
    });
})();

/* CTA résumé + barre mobile : même action que le bouton du formulaire (validation HTML5) */
(function() {
    function triggerCartCheckout() {
        var form = document.getElementById('cart-delivery-form');
        if (!form) return;
        if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
        } else {
            form.submit();
        }
    }
    function bind(id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('click', function() {
            triggerCartCheckout();
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            bind('cart-mobile-checkout-btn');
            bind('cart-summary-checkout-btn');
        });
    } else {
        bind('cart-mobile-checkout-btn');
        bind('cart-summary-checkout-btn');
    }
})();
