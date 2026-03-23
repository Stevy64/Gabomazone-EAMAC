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
