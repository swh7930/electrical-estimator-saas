(() => {
  const $ = (id) => document.getElementById(id);

  function showQuickAddModal() {
    const el = $("customerQuickAddModal");
    if (!el) return;
    const modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest("#btnQuickAddCustomer")) {
      showQuickAddModal();
    }
  }, { passive: true });

  $("quickAddCustomerForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const company_name = $("qaCompanyName")?.value.trim();
    if (!company_name) { $("qaCompanyName")?.focus(); return; }

    const payload = {
      is_active: true,
      company_name,
      contact_name: $("qaContactName")?.value.trim() || null,
      email: $("qaEmail")?.value.trim() || null,
      phone: $("qaPhone")?.value.trim() || null
    };

    try {
      const res = await fetch("/libraries/customers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Create failed");
      const raw = await res.json();
        const c = raw?.customer || raw || {};
        const typedName = (document.getElementById("qaCompanyName")?.value || "").trim();
        const name = c.company_name || c.companyName || typedName;

        // Tell the page a customer was created (id + name)
        document.dispatchEvent(new CustomEvent("customer:created", {
        detail: { id: c.id, company_name: name, name }
        }));

      // Reset + close
      $("quickAddCustomerForm")?.reset();
      bootstrap.Modal.getOrCreateInstance($("customerQuickAddModal")).hide();
    } catch (err) {
      console.error(err);
      alert("Failed to create customer.");
    }
  });
})();
