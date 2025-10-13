(() => {
  "use strict";

  function getRoot() {
    return document.querySelector(".assemblies-edit-page");
  }

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

  // On DOM ready: optionally auto-open dialog based on template-provided flag
  window.addEventListener("DOMContentLoaded", () => {
    const root = getRoot();
    if (!root) return;

    const openFlag = (root.getAttribute("data-open-flag") || "").trim();
    if (openFlag === "add") {
      openDialog("dlgAddComp");
    }
  });

  // (Optional) expose minimal API for future reuse/debug
  window.AdminAssembliesEdit = {
    openDialog,
    closeDialog,
  };
})();
