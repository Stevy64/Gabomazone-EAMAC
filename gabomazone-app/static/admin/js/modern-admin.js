/* Global admin ergonomics helpers */
(function () {
  function openCurrentTree() {
    var activeLink = document.querySelector(".main-sidebar .nav-link.active");
    if (!activeLink) return;
    var tree = activeLink.closest(".has-treeview");
    while (tree) {
      tree.classList.add("menu-open");
      var trigger = tree.querySelector(":scope > .nav-link");
      if (trigger) trigger.classList.add("active");
      tree = tree.parentElement ? tree.parentElement.closest(".has-treeview") : null;
    }
  }

  function improveFocusFlow() {
    var firstSearch = document.querySelector("#changelist-search input[type='text'], #changelist-search input[type='search']");
    if (firstSearch && window.location.search.indexOf("q=") === -1) {
      firstSearch.setAttribute("placeholder", "Rechercher rapidement...");
    }
  }

  /**
   * Change / add form on narrow viewports: duplicate submit-on-top is hidden via CSS;
   * bottom submit row becomes a fixed action bar (styled in modern-admin.css).
   */
  function enhanceAdminChangeFormActions() {
    if (document.body.classList.contains("popup")) return;
    if (!document.body.classList.contains("change-form") && !document.body.classList.contains("add-form")) return;
    var form = document.querySelector("#content-main form[id$='_form']");
    if (!form) return;
    var rows = form.querySelectorAll(".submit-row");
    if (rows.length >= 2) {
      rows[0].classList.add("gm-admin-submit-row-top");
    }
    if (rows.length >= 1) {
      rows[rows.length - 1].classList.add("gm-admin-submit-row-bottom");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    openCurrentTree();
    improveFocusFlow();
    enhanceAdminChangeFormActions();
  });
})();
