// Number input +/- functions
    function incrementValue(fieldId) {
        const input = document.getElementById(fieldId);
        if (input) {
            const currentValue = parseInt(input.value) || 0;
            input.value = currentValue + 1;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    
    function decrementValue(fieldId) {
        const input = document.getElementById(fieldId);
        if (input) {
            const currentValue = parseInt(input.value) || 0;
            if (currentValue > 0) {
                input.value = currentValue - 1;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }
    
    // Custom Dropdown Functionality
    document.addEventListener('DOMContentLoaded', function() {
        const dropdowns = document.querySelectorAll('.custom-dropdown');
        
        dropdowns.forEach(dropdown => {
            const trigger = dropdown.querySelector('.custom-dropdown-trigger');
            const menu = dropdown.querySelector('.custom-dropdown-menu');
            const select = dropdown.parentElement.querySelector('select');
            
            if (!trigger || !menu || !select) return;
            
            // Sync dropdown with select
            function syncDropdown() {
                menu.innerHTML = '';
                Array.from(select.options).forEach(option => {
                    const optionDiv = document.createElement('div');
                    optionDiv.className = 'dropdown-option';
                    optionDiv.setAttribute('data-value', option.value);
                    optionDiv.textContent = option.textContent.trim();
                    
                    if (option.selected) {
                        optionDiv.setAttribute('data-selected', 'true');
                        trigger.querySelector('.dropdown-selected-text').textContent = option.textContent.trim();
                    }
                    
                    optionDiv.addEventListener('click', function() {
                        const value = this.getAttribute('data-value');
                        const text = this.textContent.trim();
                        
                        trigger.querySelector('.dropdown-selected-text').textContent = text;
                        menu.querySelectorAll('.dropdown-option').forEach(opt => {
                            opt.removeAttribute('data-selected');
                        });
                        this.setAttribute('data-selected', 'true');
                        
                        select.value = value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        if (select.classList.contains('super_category') || 
                            select.classList.contains('main_category') || 
                            select.classList.contains('sub_category')) {
                            $(select).trigger('change');
                        }
                        
                        dropdown.classList.remove('active');
                    });
                    
                    menu.appendChild(optionDiv);
                });
            }
            
            syncDropdown();
            
            // Toggle dropdown
            trigger.addEventListener('click', function(e) {
                e.stopPropagation();
                const isActive = dropdown.classList.contains('active');
                
                dropdowns.forEach(d => {
                    if (d !== dropdown) d.classList.remove('active');
                });
                
                dropdown.classList.toggle('active', !isActive);
            });
            
            // Close on outside click
            document.addEventListener('click', function(e) {
                if (!dropdown.contains(e.target)) {
                    dropdown.classList.remove('active');
                }
            });
            
            // Watch for select changes (from get-category.js)
            const observer = new MutationObserver(function() {
                syncDropdown();
            });
            
            observer.observe(select, {
                childList: true,
                subtree: true
            });
        });
    });
    
    // Image preview
    const image = document.getElementById('id_image');
    if (image) {
        image.addEventListener('change', () => {
            const img_data = image.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                document.getElementById("url-img").src = url;
            }
        });
    }
    
    const image_1 = document.getElementById('id_image_1');
    if (image_1) {
        image_1.addEventListener('change', () => {
            const img_data = image_1.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                document.getElementById("url-img-1").src = url;
            }
        });
    }
    
    const image_2 = document.getElementById('id_image_2');
    if (image_2) {
        image_2.addEventListener('change', () => {
            const img_data = image_2.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                document.getElementById("url-img-2").src = url;
            }
        });
    }
    
    const image_3 = document.getElementById('id_image_3');
    if (image_3) {
        image_3.addEventListener('change', () => {
            const img_data = image_3.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                document.getElementById("url-img-3").src = url;
            }
        });
    }
    
    const image_4 = document.getElementById('id_image_4');
    if (image_4) {
        image_4.addEventListener('change', () => {
            const img_data = image_4.files[0];
            if (img_data) {
                const url = URL.createObjectURL(img_data);
                document.getElementById("url-img-4").src = url;
            }
        });
    }
    
    // Discount checkbox
    const discounted = document.getElementById("discounted");
    const discountBox = document.getElementById("discount_box");
    if (discounted && discountBox) {
        discounted.addEventListener('change', function() {
            if (this.checked) {
                discountBox.classList.remove("not-visible");
            } else {
                discountBox.classList.add("not-visible");
            }
        });
    }
    
    // File validation
    var _validFileExtensions = [".jpg", ".jpeg", ".bmp", ".gif", ".png"];
    function Validate(oForm) {
        var arrInputs = oForm.getElementsByTagName("input");
        for (var i = 0; i < arrInputs.length; i++) {
            var oInput = arrInputs[i];
            if (oInput.type == "file") {
                var sFileName = oInput.value;
                if (sFileName.length > 0) {
                    var blnValid = false;
                    for (var j = 0; j < _validFileExtensions.length; j++) {
                        var sCurExtension = _validFileExtensions[j];
                        if (sFileName.substr(sFileName.length - sCurExtension.length, sCurExtension.length).toLowerCase() == sCurExtension.toLowerCase()) {
                            blnValid = true;
                            break;
                        }
                    }
                    
                    if (!blnValid) {
                        alert("Désolé, " + sFileName + " est invalide. Extensions autorisées: " + _validFileExtensions.join(", "));
                        return false;
                    }
                }
            }
        }
        return true;
    }
    
    // Sync dropdowns before form submission
    document.addEventListener('DOMContentLoaded', function() {
        const editProductForm = document.getElementById('editProductForm');
        if (editProductForm) {
            editProductForm.addEventListener('submit', function(e) {
                const allDropdowns = document.querySelectorAll('.custom-dropdown');
                allDropdowns.forEach(dropdown => {
                    const select = dropdown.parentElement.querySelector('select');
                    const trigger = dropdown.querySelector('.custom-dropdown-trigger');
                    
                    if (select && trigger) {
                        const selectedText = trigger.querySelector('.dropdown-selected-text').textContent.trim();
                        const selectedOption = Array.from(dropdown.querySelectorAll('.dropdown-option')).find(opt => {
                            return opt.textContent.trim() === selectedText && opt.getAttribute('data-selected') === 'true';
                        });
                        
                        if (selectedOption) {
                            const value = selectedOption.getAttribute('data-value');
                            if (value !== null && value !== undefined) {
                                select.value = value;
                            }
                        }
                    }
                });
                
                if (!Validate(this)) {
                    e.preventDefault();
                    return false;
                }
                
                return true;
            });
        }
    });
