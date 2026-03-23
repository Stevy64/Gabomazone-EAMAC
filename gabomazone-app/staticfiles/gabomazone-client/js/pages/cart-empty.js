// Supprimer les doublons de header
    (function() {
        function removeDuplicateHeaders() {
            const headers = document.querySelectorAll('header.flavoriz-header');
            if (headers.length > 1) {
                // Garder seulement le premier header, supprimer les autres
                for (let i = 1; i < headers.length; i++) {
                    headers[i].remove();
                }
            }
        }
        
        // Exécuter immédiatement
        removeDuplicateHeaders();
        
        // Exécuter après DOMContentLoaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', removeDuplicateHeaders);
        } else {
            removeDuplicateHeaders();
        }
        
        // Exécuter après window.load
        window.addEventListener('load', removeDuplicateHeaders);
    })();
