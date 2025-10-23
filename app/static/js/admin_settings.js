(function () {
    const $ = (id) => document.getElementById(id);
    const statusEl = document.querySelector("#admin-settings-grid .text-muted") || document.querySelector(".text-muted");

    function setStatus(msg) {
      if (!statusEl) return;
      statusEl.textContent = `App-wide preferences, proposal identity, and estimator defaults. ${msg || ""}`.trim();
    }

    function getVal(id) {
      const el = $(id);
      if (!el) return "";
      if (el.tagName === "SELECT") return el.value;
      if (el.type === "number") return el.value;
      return (el.value || "").trim();
    }

    function setVal(id, v) {
      const el = $(id);
      if (!el) return;
      if (el.tagName === "SELECT") el.value = v ?? el.value;
      else el.value = v ?? el.value;
    }



    function collectSettings() {
      const org = {
        company_name: getVal("orgCompanyName"),
        legal_name:   getVal("orgLegalName"),
        contact_name: getVal("orgContactName"),
        email:        getVal("orgEmail"),
        phone:        getVal("orgPhone"),
        website:      getVal("orgWebsite"),
        address1:     getVal("orgAddress1"),
        address2:     getVal("orgAddress2"),
        city:         getVal("orgCity"),
        state:        getVal("orgState"),
        zip:          getVal("orgZip"),
        license_no:   getVal("orgLicense"),
        proposal_footer: getVal("proposalFooter"),
      };

      const toInt = (v, d) => {
      const s = String(v ?? '').trim();
      if (s === '') return d;
      const n = Number.parseInt(s, 10);
      return Number.isFinite(n) ? n : d;
      };
      const toFloat = (v, d) => {
      const s = String(v ?? '').trim();
      if (s === '') return d;
      const n = Number.parseFloat(s);
      return Number.isFinite(n) ? n : d;
      };

      const pricing = {
      labor_rate: toFloat(getVal("settingLaborRate"), 0),
      overhead_percent: toInt(getVal("settingOverheadPercent"), 30),
      margin_percent:   toInt(getVal("settingProfitMarginPercent"), 10),
      sales_tax_percent: toInt(getVal("settingSalesTaxPercent"), 8),
      misc_percent:        toInt(getVal("settingMiscPercent"), 10),
      small_tools_percent: toInt(getVal("settingSmallToolsPercent"), 5),
      large_tools_percent: toInt(getVal("settingLargeToolsPercent"), 3),
      waste_theft_percent: toInt(getVal("settingWasteTheftPercent"), 10),
      };

      return { version: 1, org, pricing };
    }

    function applyToForm(settings) {
      const s = settings || {};
      const org = s.org || {};
      const p = s.pricing || {};

      setVal("orgCompanyName", org.company_name);
      setVal("orgLegalName",   org.legal_name);
      setVal("orgContactName", org.contact_name);
      setVal("orgEmail",       org.email);
      setVal("orgPhone",       org.phone);
      setVal("orgWebsite",     org.website);
      setVal("orgAddress1",    org.address1);
      setVal("orgAddress2",    org.address2);
      setVal("orgCity",        org.city);
      setVal("orgState",       org.state);
      setVal("orgZip",         org.zip);
      setVal("orgLicense",     org.license_no);
      setVal("proposalFooter", org.proposal_footer);

      if (typeof p.labor_rate === "number") setVal("settingLaborRate", p.labor_rate);
      if (p.overhead_percent != null) setVal("settingOverheadPercent", String(p.overhead_percent));
      if (p.margin_percent   != null) setVal("settingProfitMarginPercent", String(p.margin_percent));
      if (p.sales_tax_percent!= null) setVal("settingSalesTaxPercent", String(p.sales_tax_percent));
      if (p.misc_percent     != null) setVal("settingMiscPercent", String(p.misc_percent));
      if (p.small_tools_percent!=null) setVal("settingSmallToolsPercent", String(p.small_tools_percent));
      if (p.large_tools_percent!=null) setVal("settingLargeToolsPercent", String(p.large_tools_percent));
      if (p.waste_theft_percent!=null) setVal("settingWasteTheftPercent", String(p.waste_theft_percent));
    }

    let saveTimer = null;
    function scheduleSave() {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(doSave, 400);
    }

    function doSave() {
      const payload = { settings: collectSettings() };
      setStatus("Saving…");
      fetch("/admin/settings.json", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
      .then(r => r.json())
      .then(() => setStatus("Saved ✓"))
      .catch(() => setStatus("Save failed"));
    }

    document.addEventListener("DOMContentLoaded", () => {
      const canMeta = document.querySelector('meta[name="x-can-write"]');
      const CAN_WRITE = !!(canMeta && canMeta.content === '1');
      setStatus("");

      // Load existing (if any)
      fetch("/admin/settings.json")
        .then(r => r.ok ? r.json() : {})
        .then(data => {
          if (data && data.settings) applyToForm(data.settings);
        })
        .catch(() => { /* keep defaults */ });
            if (!CAN_WRITE) {
        const scope = document.getElementById('admin-settings-grid') || document;
        scope.querySelectorAll('input, select, textarea, button').forEach((el) => {
          el.setAttribute('disabled', 'disabled');
          el.setAttribute('aria-disabled', 'true');
        });
        // View-only: do not bind autosave handlers.
        return;
      }

      // Auto-save on change/blur
      const ids = [
        "orgCompanyName","orgLegalName","orgContactName","orgEmail","orgPhone","orgWebsite",
        "orgAddress1","orgAddress2","orgCity","orgState","orgZip","orgLicense","proposalFooter",
        "settingLaborRate","settingOverheadPercent","settingProfitMarginPercent","settingSalesTaxPercent",
        "settingMiscPercent","settingSmallToolsPercent","settingLargeToolsPercent","settingWasteTheftPercent",
      ];
      ids.forEach((id) => {
        const el = $(id);
        if (!el) return;
        el.addEventListener("change", scheduleSave);
        el.addEventListener("blur", scheduleSave);
      });
    });
})();
