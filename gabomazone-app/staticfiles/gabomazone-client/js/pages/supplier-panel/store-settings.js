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
    
    // Custom Dropdown for Province
    const provinceDropdown = document.getElementById('customDropdownProvince');
    const provinceSelect = document.getElementById('province-select');
    
    if (provinceDropdown && provinceSelect) {
        const trigger = provinceDropdown.querySelector('.custom-dropdown-trigger');
        const menu = provinceDropdown.querySelector('.custom-dropdown-menu');
        const options = menu.querySelectorAll('.dropdown-option');
        const selectedText = trigger.querySelector('.dropdown-selected-text');
        
        // Initialize selected option
        const selectedOption = menu.querySelector('[data-selected="true"]');
        if (selectedOption) {
            selectedText.textContent = selectedOption.textContent;
            provinceSelect.value = selectedOption.getAttribute('data-value');
        }
        
        // Toggle dropdown
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            provinceDropdown.classList.toggle('active');
        });
        
        // Handle option selection
        options.forEach(option => {
            option.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const text = this.textContent;
                
                // Update select
                provinceSelect.value = value;
                
                // Update display
                selectedText.textContent = text;
                
                // Update selected state
                options.forEach(opt => opt.removeAttribute('data-selected'));
                this.setAttribute('data-selected', 'true');
                
                // Close dropdown
                provinceDropdown.classList.remove('active');
                
                // Auto-fill city
                updateCity(value);
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!provinceDropdown.contains(e.target)) {
                provinceDropdown.classList.remove('active');
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
    function updateCity(province) {
        const cityInput = document.getElementById('city');
        if (cityInput && province && provinceCities[province]) {
            cityInput.style.transition = 'all 0.3s ease';
            cityInput.style.opacity = '0.7';
            setTimeout(() => {
                cityInput.value = provinceCities[province];
                cityInput.style.opacity = '1';
            }, 150);
        } else if (cityInput) {
            cityInput.value = '';
        }
    }
    
    // Initialize city on page load
    const provinceSelectInit = document.getElementById('province-select');
    const cityInputInit = document.getElementById('city');
    if (provinceSelectInit && cityInputInit && provinceSelectInit.value && provinceCities[provinceSelectInit.value]) {
        cityInputInit.value = provinceCities[provinceSelectInit.value];
    }
    
    // Smooth scroll to form sections on focus
    document.querySelectorAll('.form-input, .form-textarea').forEach(input => {
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
    
    // Delete Account Modal Functions
    function openDeleteAccountModal() {
        const modal = document.getElementById('deleteAccountModal');
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    function closeDeleteAccountModal() {
        const modal = document.getElementById('deleteAccountModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    
    // Fermer le modal en cliquant sur l'overlay
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('deleteAccountModal');
        if (modal && e.target === modal) {
            closeDeleteAccountModal();
        }
    });
    
    // Fermer le modal avec la touche Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDeleteAccountModal();
        }
    });
