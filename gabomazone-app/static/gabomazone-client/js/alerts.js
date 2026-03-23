/**
 * Alert toast auto-dismiss behavior.
 * Toasts slide in, auto-dismiss after 4s, with hover-to-pause.
 */
document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.flavoriz-alert-toast');
    alerts.forEach(function(alert, index) {
        setTimeout(function() {
            alert.style.opacity = '1';
            alert.style.transform = 'translateX(0)';
        }, index * 100);

        var dismissTimeout = setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(function() { alert.remove(); }, 300);
        }, 4000);

        alert.addEventListener('mouseenter', function() {
            clearTimeout(dismissTimeout);
        });
    });
});
