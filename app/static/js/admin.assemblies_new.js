(() => {
  "use strict";

  function openDialog(id) {
    const d = document.getElementById(id);
    if (!d) return;
    if (typeof d.showModal === "function") d.showModal();
    else d.setAttribute("open", "");
  }

  function closeDialog(id) {
    const d = document.getElementById(id);
    if (!d) return;
    if (typeof d.close === "function") d.close();
    else d.removeAttribute("open");
  }

  // Delegate clicks for [data-open] / [data-close]
  document.addEventListener("click", (e) => {
    const opener = e.target.closest("[data-open]");
    if (opener) {
      e.preventDefault();
      openDialog(opener.getAttribute("data-open"));
      return;
    }
    const closer = e.target.closest("[data-close]");
    if (closer) {
      e.preventDefault();
      closeDialog(closer.getAttribute("data-close"));
    }
  });

  // Auto-open on page load (matches the original inline behavior)
  window.addEventListener("DOMContentLoaded", () => {
    openDialog("dlgCreate");
  });

  // Optional debug handle
  window.AdminAssembliesNew = { openDialog, closeDialog };
})();
