// Custom Dropdown Functionality
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize dropdowns
        const dropdowns = document.querySelectorAll('.custom-dropdown');
        
        dropdowns.forEach(dropdown => {
            const trigger = dropdown.querySelector('.custom-dropdown-trigger');
            const menu = dropdown.querySelector('.custom-dropdown-menu');
            const options = dropdown.querySelectorAll('.dropdown-option');
            const select = dropdown.parentElement.querySelector('select');
            
            // Toggle dropdown
            trigger.addEventListener('click', function(e) {
                e.stopPropagation();
                const isActive = dropdown.classList.contains('active');
                
                // Close all other dropdowns
                dropdowns.forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('active');
                    }
                });
                
                // Toggle current dropdown
                dropdown.classList.toggle('active', !isActive);
            });
            
            // Handle option selection
            options.forEach(option => {
                option.addEventListener('click', function() {
                    const value = this.getAttribute('data-value');
                    const text = this.textContent.trim();
                    
                    // Update selected text
                    trigger.querySelector('.dropdown-selected-text').textContent = text;
                    
                    // Update selected state
                    options.forEach(opt => {
                        opt.removeAttribute('data-selected');
                    });
                    this.setAttribute('data-selected', 'true');
                    
                    // Update native select
                    if (select) {
                        select.value = value;
                        // Trigger change event for jQuery
                        if (typeof jQuery !== 'undefined') {
                            jQuery(select).trigger('change');
                        } else {
                            select.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                    
                    // Close dropdown
                    dropdown.classList.remove('active');
                });
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(e) {
                if (!dropdown.contains(e.target)) {
                    dropdown.classList.remove('active');
                }
            });
            
            // Initialize selected option from native select
            if (select && select.value) {
                const selectedOption = Array.from(select.options).find(opt => opt.value === select.value);
                if (selectedOption) {
                    const matchingOption = Array.from(options).find(opt => opt.getAttribute('data-value') === select.value);
                    if (matchingOption) {
                        trigger.querySelector('.dropdown-selected-text').textContent = selectedOption.textContent.trim();
                        options.forEach(opt => opt.removeAttribute('data-selected'));
                        matchingOption.setAttribute('data-selected', 'true');
                    }
                }
            }
        });
    });
