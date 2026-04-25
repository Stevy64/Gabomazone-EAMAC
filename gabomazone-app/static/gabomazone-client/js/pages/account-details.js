// Image preview with smooth transition
    const image = document.getElementById('id_image');
    const urlImg = document.getElementById('url-img');
    
    if (image && urlImg) {
        image.addEventListener('change', () => {
            const img_data = image.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                urlImg.style.opacity = '0';
                urlImg.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    urlImg.src = url;
                    urlImg.style.opacity = '1';
                    urlImg.style.transform = 'scale(1)';
                }, 150);
            }
        });
    }
    
    // Province to City mapping (Gabon)
    const provinceCities = {
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
    
    // Auto-fill city based on province with animation
    const provinceSelect = document.getElementById('province');
    const cityInput = document.getElementById('city');
    const provinceDropdown = document.getElementById('provinceDropdown');
    const provinceTrigger = document.getElementById('provinceDropdownTrigger');
    const provinceMenu = document.getElementById('provinceDropdownMenu');
    const provinceLabel = document.getElementById('provinceDropdownLabel');

    function buildProvinceDropdown() {
        if (!provinceSelect || !provinceDropdown || !provinceTrigger || !provinceMenu || !provinceLabel) {
            return;
        }

        const options = Array.from(provinceSelect.options);
        provinceMenu.innerHTML = '';

        options.forEach((option) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'gm-province-option';
            item.textContent = option.textContent;
            item.dataset.value = option.value;
            item.setAttribute('role', 'option');
            if (option.selected) {
                item.classList.add('active');
                provinceLabel.textContent = option.textContent;
            }
            if (!option.value) {
                item.classList.remove('active');
            }
            item.addEventListener('click', () => {
                provinceSelect.value = option.value;
                provinceSelect.dispatchEvent(new Event('change', { bubbles: true }));
                provinceMenu.querySelectorAll('.gm-province-option').forEach((el) => el.classList.remove('active'));
                if (option.value) {
                    item.classList.add('active');
                }
                provinceLabel.textContent = option.textContent;
                provinceMenu.hidden = true;
                provinceDropdown.classList.remove('open');
                provinceTrigger.setAttribute('aria-expanded', 'false');
            });
            provinceMenu.appendChild(item);
        });

        if (!provinceSelect.value) {
            provinceLabel.textContent = options.length ? options[0].textContent : 'Sélectionnez une province';
        }
    }
    
    if (provinceSelect && cityInput) {
        provinceSelect.addEventListener('change', function() {
            const selectedProvince = this.value;
            if (selectedProvince && provinceCities[selectedProvince]) {
                cityInput.style.transition = 'all 0.3s ease';
                cityInput.style.opacity = '0.7';
                setTimeout(() => {
                    cityInput.value = provinceCities[selectedProvince];
                    cityInput.style.opacity = '1';
                }, 150);
            } else {
                cityInput.value = '';
            }
        });
        
        // Initialize city on page load
        if (provinceSelect.value && provinceCities[provinceSelect.value]) {
            cityInput.value = provinceCities[provinceSelect.value];
        }
    }

    if (provinceDropdown && provinceTrigger && provinceMenu) {
        buildProvinceDropdown();
        provinceTrigger.addEventListener('click', function() {
            const willOpen = provinceMenu.hidden;
            provinceMenu.hidden = !willOpen;
            provinceDropdown.classList.toggle('open', willOpen);
            provinceTrigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        });

        document.addEventListener('click', function(event) {
            if (!provinceDropdown.contains(event.target)) {
                provinceMenu.hidden = true;
                provinceDropdown.classList.remove('open');
                provinceTrigger.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    // Smooth scroll to form sections on focus
    document.querySelectorAll('.flavoriz-input').forEach(input => {
        input.addEventListener('focus', function() {
            const section = this.closest('.form-section');
            if (section) {
                const offset = 120;
                const sectionTop = section.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({
                    top: sectionTop,
                    behavior: 'smooth'
                });
            }
        });
    });
