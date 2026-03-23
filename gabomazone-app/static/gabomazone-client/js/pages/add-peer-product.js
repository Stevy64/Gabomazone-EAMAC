(function() {
    var filterSel = document.getElementById('gm-articles-filter');
    var searchInp = document.getElementById('gm-articles-search');
    var emptyMsg = document.getElementById('gm-articles-empty');
    if (!filterSel || !searchInp) return;
    function applyFilter() {
        var status = filterSel.value;
        var query = searchInp.value.toLowerCase().trim();
        var rows = document.querySelectorAll('.gm-article-row');
        var visible = 0;
        rows.forEach(function(row) {
            var matchStatus = (status === 'all' || row.getAttribute('data-status') === status);
            var matchSearch = (!query || row.getAttribute('data-name').indexOf(query) !== -1);
            if (matchStatus && matchSearch) {
                row.style.display = '';
                visible++;
            } else {
                row.style.display = 'none';
            }
        });
        if (emptyMsg) emptyMsg.style.display = visible === 0 ? 'block' : 'none';
    }
    filterSel.addEventListener('change', applyFilter);
    searchInp.addEventListener('input', applyFilter);
})();
