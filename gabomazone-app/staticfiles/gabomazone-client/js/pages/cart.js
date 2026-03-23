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

(function() {
    var toggle = document.getElementById('cart-delivery-toggle');
    var card = document.getElementById('cart-delivery-card');
    var body = document.getElementById('cart-delivery-body');
    var form = document.getElementById('cart-delivery-form');
    var labelEl = card && card.querySelector('.cart-delivery-toggle-label');
    var hintEl = card && card.querySelector('.cart-delivery-toggle-hint');
    var key = 'cart-delivery-collapsed';

    function setLabelAndHint(collapsed) {
        if (labelEl) labelEl.textContent = collapsed ? 'Afficher' : 'Masquer';
        if (hintEl) hintEl.textContent = collapsed ? 'Cliquez pour afficher le formulaire de livraison' : 'Cliquez pour afficher ou masquer le formulaire';
    }
    function expandSection() {
        if (card && card.classList.contains('collapsed')) {
            card.classList.remove('collapsed');
            if (toggle) toggle.setAttribute('aria-expanded', 'true');
            sessionStorage.setItem(key, '0');
            setLabelAndHint(false);
        }
    }
    if (toggle && card && body) {
        var collapsed = sessionStorage.getItem(key) === '1';
        if (window.location.search.indexOf('expand_delivery=1') !== -1) collapsed = false;
        if (collapsed) {
            card.classList.add('collapsed');
            toggle.setAttribute('aria-expanded', 'false');
            setLabelAndHint(true);
        } else {
            setLabelAndHint(false);
        }
        toggle.addEventListener('click', function() {
            collapsed = card.classList.toggle('collapsed');
            toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
            sessionStorage.setItem(key, collapsed ? '1' : '0');
            setLabelAndHint(collapsed);
        });
    }
    if (form && card) {
        form.addEventListener('submit', function(e) {
            var deliveryBody = document.getElementById('cart-delivery-body');
            if (!deliveryBody) return;
            if (!form.checkValidity()) {
                e.preventDefault();
                expandSection();
                form.reportValidity();
                var firstInvalid = deliveryBody.querySelector('input:invalid, select:invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    setTimeout(function() { firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 100);
                }
            }
        });
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
        if (provinceSelect.value && provinceCities[provinceSelect.value.trim()]) {
            cityInput.value = provinceCities[provinceSelect.value.trim()];
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
            cityInput.value = provinceCities[provinceSelect.value];
        }
    });
})();
