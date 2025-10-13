// === DJE (Category -> Description -> Cost [read-only]) ===
// Assumptions: table columns = Notes | Category | Description | Qty | Multi | Cost | Ext
// HTML ids used:  djeCategory_{i}, djeDescription_{i}, djeCost_{i}, djeExt_{i}
// Inputs used:    input.cell-notes[data-row], input.cell-qty[data-row], input.cell-multi[data-row]

(() => {
    const API = {
        cats: "/api/dje-categories",
        subs: (category) => `/api/dje-subcategories?category=${encodeURIComponent(category || "")}`,
        descs: (category, subcategory) =>
            `/api/dje-descriptions?category=${encodeURIComponent(category || "")}&subcategory=${encodeURIComponent(subcategory || "")}`,
    };

    // --- Utilities ---
    const $ = (sel, root = document) => root.querySelector(sel);
    const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
    const toNum = (v) => {
        if (v == null) return 0;
        if (typeof v === "number") return Number.isFinite(v) ? v : 0;
        const n = parseFloat(String(v).replace(/[$,]/g, "").trim());
        return Number.isFinite(n) ? n : 0;
    };

    // Use shared formatter if present, else fall back
    const formatUSD = window.formatUSD || (n => `$${(Number(n) || 0).toFixed(2)}`);
    const money = (n) => formatUSD(n);

    // --- Caches ---
    let CATS = [];
    const SUB_CACHE = new Map(); // category -> [subcats]
    const DESC_CACHE = new Map(); // category::subcategory -> [{id, description, cost}]

    // --- Fetchers ---
    async function getJSON(url) {
        const r = await fetch(url, { headers: { Accept: "application/json" } });
        if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
        return r.json();
    }
    async function loadCats() {
        if (CATS.length) return CATS;
        CATS = await getJSON(API.cats);
        return CATS;
    }
    async function loadSubs(category) {
        if (!category) return [];
        if (SUB_CACHE.has(category)) return SUB_CACHE.get(category);
        const list = await getJSON(API.subs(category)); // returns ["EMT", ...]
        SUB_CACHE.set(category, list);
        return list;
    }
    async function loadDescs(category, subcategory) {
        const key = `${category}::${subcategory}`;
        if (!category || !subcategory) return [];
        if (DESC_CACHE.has(key)) return DESC_CACHE.get(key);
        const list = await getJSON(API.descs(category, subcategory)); // returns [{id, description, cost}]
        DESC_CACHE.set(key, list);
        return list;
    }

    // --- UI helpers ---
    function populateSelect(sel, items, selectedId = "") {
        sel.innerHTML = "";
        const def = document.createElement("option");
        def.value = ""; def.textContent = "Select…";
        sel.appendChild(def);

        for (const it of items) {
            // cats/subs: strings; descs: objects
            const isString = (typeof it === "string");
            const value = isString ? it : it.id;
            const label = isString ? it : (it.label ?? it.description ?? it.id);
            const inactive = !isString && it.active === false;
            if (inactive) continue;

            const o = document.createElement("option");
            o.value = value; o.textContent = label;
            if (selectedId && selectedId === value) o.selected = true;
            sel.appendChild(o);
        }
        sel.disabled = false;
    }

    function rowEls(i) {
        const tr = document.querySelector(`#djeCategory_${i}`)?.closest("tr");
        return {
            tr,
            qty: tr?.cells?.[4]?.querySelector("input.cell-qty") || null, // was 3
            multi: tr?.cells?.[5]?.querySelector("input.cell-multi") || null, // was 4
            costCell: document.querySelector(`#djeCost_${i}`) || tr?.cells?.[6] || null, // was 5
            extCell: document.querySelector(`#djeExt_${i}`) || tr?.cells?.[7] || null, // was 6
            catHost: document.querySelector(`#djeCategory_${i}`),
            subHost: document.querySelector(`#djeSubcategory_${i}`),
            descHost: document.querySelector(`#djeDescription_${i}`),
        };
    }

    function recalcRow(i) {
        const { qty, multi, costCell, extCell } = rowEls(i);
        if (!qty || !multi || !costCell || !extCell) return;
        const q = Math.max(0, toNum(qty.value));
        const m = Math.max(1, toNum(multi.value));
        const c = Math.max(0, toNum(costCell.textContent || costCell.innerText));
        extCell.textContent = money(q * m * c);
        updateHeaderTotal();
    }

    function updateHeaderTotal() {
        let total = 0;
        $$("#djeExt_0, #djeExt_1, #djeExt_2, #djeExt_3, #djeExt_4, #djeExt_5, #djeExt_6, #djeExt_7, #djeExt_8, #djeExt_9")
            .concat($$("[id^='djeExt_']:not(#djeExt_0):not(#djeExt_1):not(#djeExt_2):not(#djeExt_3):not(#djeExt_4):not(#djeExt_5):not(#djeExt_6):not(#djeExt_7):not(#djeExt_8):not(#djeExt_9)"))
            .forEach(el => total += toNum(el.textContent));
        const header = $("#djeTotalDisplay") || $("#djePageTotal");
        if (header) header.textContent = money(total);

        // === ADD: keep Summary in sync (matches summary.js expectation) ===
        try { loadEstimateData?.(); } catch { }
        if (!window.estimateData) window.estimateData = {};
        if (!estimateData.costs) estimateData.costs = {};
        estimateData.costs.dje = Number(total);
        try { saveEstimateData?.(); } catch { localStorage.setItem("estimateData", JSON.stringify(estimateData)); }
        // === END ADD ===
    }

    function sanitizeMultiInput(el) {
        // keep digits only; force integer >= 1
        const n = parseInt(String(el.value || "").replace(/[^0-9]/g, ""), 10);
        el.value = String(Number.isFinite(n) ? Math.max(1, n) : 1);
    }

    // --- PERSISTENCE (ADD) ---
    function djeCollectRowsFromDOM() {
        const rows = [];
        const tbody = document.querySelector("table tbody");
        if (!tbody) return rows;

        for (const tr of Array.from(tbody.rows)) {
            const anyDataEl = tr.querySelector("[data-row]"); if (!anyDataEl) continue;
            const i = parseInt(anyDataEl.getAttribute("data-row") || "-1", 10);
            if (!Number.isFinite(i) || i < 0) continue;

            const notes = tr.cells[0]?.querySelector("input.cell-notes")?.value || "";
            const cat_id = tr.cells[1]?.querySelector("select.dje-cat")?.value || "";
            const sub_id = tr.cells[2]?.querySelector("select.dje-sub")?.value || "";
            const desc_id = tr.cells[3]?.querySelector("select.dje-desc")?.value || "";
            const qty = tr.cells[4]?.querySelector("input.cell-qty")?.value || "";
            const multi = tr.cells[5]?.querySelector("input.cell-multi")?.value || "1";

            rows[i] = { notes, cat_id, sub_id, desc_id, qty, multi };
        }
        while (rows.length && rows[rows.length - 1] == null) rows.pop();
        return rows;
    }

    function djePersist() {
        try { loadEstimateData?.(); } catch { }
        if (!window.estimateData) window.estimateData = {};
        if (!estimateData.costs) estimateData.costs = {};
        estimateData.costs.dje_rows = djeCollectRowsFromDOM();
        try { saveEstimateData?.(); }
        catch { localStorage.setItem("estimateData", JSON.stringify(estimateData)); }

        // S3-02b — emit after persisting DJE data
        try {
            if (window.ee && typeof window.ee.fire === 'function') {
                window.ee.fire('ee:djeChanged', { timestamp: Date.now() });
            }
        } catch (_) { /* keep console clean */ }
    }


    // --- Wire a single row (by index) ---
    function wireRow(i) {
        const { tr, catHost, subHost, descHost, qty, multi, costCell } = rowEls(i);
        if (!tr || !catHost || !subHost || !descHost) return;

        // ensure selects
        let catSel = catHost.querySelector("select");
        if (!catSel) { catSel = document.createElement("select"); catSel.className = "dje-cat"; catSel.setAttribute("data-row", String(i)); catHost.appendChild(catSel); }

        let subSel = subHost.querySelector("select");
        if (!subSel) { subSel = document.createElement("select"); subSel.className = "dje-sub"; subSel.setAttribute("data-row", String(i)); subSel.disabled = true; subHost.appendChild(subSel); }

        let descSel = descHost.querySelector("select");
        if (!descSel) { descSel = document.createElement("select"); descSel.className = "dje-desc"; descSel.setAttribute("data-row", String(i)); descSel.disabled = true; descHost.appendChild(descSel); }

        // categories
        populateSelect(catSel, CATS, "");

        catSel.addEventListener("change", async () => {
            const category = catSel.value || "";
            // reset downstream
            populateSelect(subSel, []); subSel.disabled = true;
            populateSelect(descSel, []); descSel.disabled = true;
            if (costCell) costCell.textContent = formatUSD(0);
            const { extCell } = rowEls(i); if (extCell) extCell.textContent = money(0);
            updateHeaderTotal();

            if (!category) return;
            const subs = await loadSubs(category);
            populateSelect(subSel, subs, "");
            subSel.disabled = false;

            ensureAutogrow(i);
            djePersist();
        });

        subSel.addEventListener("change", async () => {
            const category = catSel.value || "";
            const subcat = subSel.value || "";
            // reset desc + cost + ext
            populateSelect(descSel, []); descSel.disabled = true;
            if (costCell) costCell.textContent = formatUSD(0);
            const { extCell } = rowEls(i); if (extCell) extCell.textContent = money(0);
            updateHeaderTotal();

            if (!category || !subcat) return;
            const descs = await loadDescs(category, subcat);
            // map to {id,label,cost} for UI
            populateSelect(descSel, descs.map(d => ({ id: String(d.id ?? d.description), label: d.description ?? String(d.id), cost: d.cost })), "");
            descSel.disabled = false;

            ensureAutogrow(i);
            djePersist();
        });

        descSel.addEventListener("change", async () => {
            const category = catSel.value || "";
            const subcat = subSel.value || "";
            const descId = descSel.value || "";
            if (!category || !subcat || !descId || !costCell) return;

            const descs = await loadDescs(category, subcat);
            const hit = descs.find(d => String(d.id ?? d.description) === descId);
            costCell.textContent = hit ? formatUSD(hit.cost) : formatUSD(0);
            recalcRow(i);
            ensureAutogrow(i);
            djePersist();
        });

        qty?.addEventListener("input", () => { recalcRow(i); ensureAutogrow(i); djePersist(); });
        multi?.addEventListener("input", () => { sanitizeMultiInput(multi); recalcRow(i); ensureAutogrow(i); djePersist(); });
    }

    // --- Simple auto-row (adds one blank row after last when user types in last Notes or Qty) ---
    function appendRow(nextIndex) {
        const tbody = $("table tbody");
        if (!tbody) return;
        const tr = document.createElement("tr");
        tr.innerHTML = `
    <td><input type="text" name="notes_${nextIndex}" class="grid-input cell-notes" data-row="${nextIndex}"></td>
    <td id="djeCategory_${nextIndex}"></td>
    <td id="djeSubcategory_${nextIndex}"></td>
    <td id="djeDescription_${nextIndex}"></td>
    <td><input type="number" name="qty_${nextIndex}" min="0" step="1" class="grid-input cell-qty" data-row="${nextIndex}"></td>
    <td><input type="number" name="multi_${nextIndex}" min="1" step="1" value="1" class="grid-input cell-multi" data-row="${nextIndex}"></td>
    <td id="djeCost_${nextIndex}" class="right"></td>
    <td id="djeExt_${nextIndex}" class="right">$0.00</td>
  `;
        tbody.appendChild(tr);
        wireRow(nextIndex);

        // Autogrow trigger on this new row as well
        const notes = tr.querySelector("input.cell-notes");
        const qty = tr.querySelector("input.cell-qty");
        const trigger = () => ensureAutogrow(nextIndex);
        notes?.addEventListener("input", trigger, { passive: true });
        qty?.addEventListener("input", trigger, { passive: true });
        djePersist();
    }

    function ensureAutogrow(idx) {
        // if user started typing in the last existing row, append one more
        const rows = $$("table tbody tr");
        const lastIdx = rows.length - 1;
        const lastRow = rows[lastIdx];
        const lastDataRow = lastRow?.querySelector("[data-row]");
        const currentIsLast = lastDataRow && Number(lastDataRow.getAttribute("data-row")) === idx;
        if (currentIsLast) appendRow(idx + 1);
    }

    // --- Reset ---
    function wireReset() {
        const btn = document.getElementById("djeResetBtn");
        if (!btn) return;

        btn.addEventListener("click", () => {
            for (let i = 0; i < 50; i++) {
                const { tr, costCell, extCell } = rowEls(i);
                if (!tr) break;

                // Notes
                const notes = tr.cells[0]?.querySelector("input.cell-notes");
                if (notes) notes.value = "";

                // Category / Subcategory / Description
                const catSel = tr.cells[1]?.querySelector("select.dje-cat");
                const subSel = tr.cells[2]?.querySelector("select.dje-sub");
                const descSel = tr.cells[3]?.querySelector("select.dje-desc");
                if (catSel) catSel.value = "";
                if (subSel) { subSel.innerHTML = "<option value=''>Select…</option>"; subSel.disabled = true; }
                if (descSel) { descSel.innerHTML = "<option value=''>Select…</option>"; descSel.disabled = true; }

                // Qty / Multi
                const qty = tr.cells[4]?.querySelector("input.cell-qty");
                const multi = tr.cells[5]?.querySelector("input.cell-multi");
                if (qty) {
                    qty.value = "";
                    qty.dispatchEvent(new Event("input", { bubbles: true }));
                }
                if (multi) {
                    multi.value = "1";
                    multi.dispatchEvent(new Event("input", { bubbles: true }));
                }

                // Cost / Ext
                if (costCell) costCell.textContent = formatUSD(0);
                if (extCell) extCell.textContent = money(0);
            }

            // Trim autogrown rows back to initial 10
            const tbody = $("table tbody");
            while (tbody && tbody.rows.length > 10) tbody.deleteRow(tbody.rows.length - 1);

            updateHeaderTotal();
            djePersist(); // persist cleared state
        });
    }

    // --- Init ---
    document.addEventListener("DOMContentLoaded", async () => {
        await loadCats();

        // Restore saved rows (if any) BEFORE hooking autogrow for the last row
        let savedRows = [];
        try {
            loadEstimateData?.();
            if (Array.isArray(estimateData?.costs?.dje_rows)) savedRows = estimateData.costs.dje_rows;
        } catch { }

        const initialCount = Math.max(10, savedRows.length || 0);

        // If there were more than 10 saved, append the extra rows first
        for (let i = 10; i < initialCount; i++) appendRow(i);

        // Wire rows 0..initialCount-1
        for (let i = 0; i < initialCount; i++) wireRow(i);

        // Seed values from saved (category -> subcategory -> description -> cost; then qty/multi; recalc)
        (async () => {
            for (let i = 0; i < savedRows.length; i++) {
                const row = savedRows[i]; if (!row) continue;
                const { tr } = rowEls(i); if (!tr) continue;

                // notes
                const notesEl = tr.cells[0]?.querySelector("input.cell-notes");
                if (notesEl) notesEl.value = row.notes ?? "";

                // qty / multi
                const qtyEl = tr.cells[4]?.querySelector("input.cell-qty");
                if (qtyEl) qtyEl.value = row.qty ?? "";

                const multiEl = tr.cells[5]?.querySelector("input.cell-multi");
                if (multiEl) { multiEl.value = row.multi ?? "1"; sanitizeMultiInput(multiEl); }

                // selects
                const catSel = tr.cells[1]?.querySelector("select.dje-cat");
                const subSel = tr.cells[2]?.querySelector("select.dje-sub");
                const desSel = tr.cells[3]?.querySelector("select.dje-desc");

                // 1) Category
                if (catSel && row.cat_id) {
                    catSel.value = row.cat_id;
                }

                // 2) Subcategory list and selection (depends on category)
                if (subSel && row.cat_id) {
                    const subs = await loadSubs(row.cat_id);
                    populateSelect(subSel, subs, row.sub_id || "");
                    subSel.disabled = false;
                }

                // 3) Descriptions list and selection (depends on category + subcategory)
                if (desSel && row.cat_id && row.sub_id) {
                    const descs = await loadDescs(row.cat_id, row.sub_id);
                    populateSelect(
                        desSel,
                        descs.map(d => ({ id: String(d.id ?? d.description), label: d.description ?? String(d.id), cost: d.cost })),
                        row.desc_id || ""
                    );
                    desSel.disabled = false;

                    // 4) Cost from selected description
                    const hit = descs.find(d => String(d.id ?? d.description) === row.desc_id);
                    const { costCell } = rowEls(i);
                    if (costCell) costCell.textContent = hit ? formatUSD(hit.cost) : formatUSD(0);
                }

                // 5) Recalc row total
                recalcRow(i);
            }

            updateHeaderTotal();
            djePersist(); // normalize persisted shape
        })();

        // Set autogrow hooks on the actual last row (not hardcoded 9)
        const lastIdx = initialCount - 1;
        const lastTr = rowEls(lastIdx).tr;
        lastTr?.querySelector("input.cell-notes")?.addEventListener("input", () => ensureAutogrow(lastIdx), { passive: true });
        lastTr?.querySelector("input.cell-qty")?.addEventListener("input", () => ensureAutogrow(lastIdx), { passive: true });
        lastTr?.querySelector("input.cell-multi")?.addEventListener("input", () => {
            const el = lastTr.querySelector("input.cell-multi");
            sanitizeMultiInput(el);
            ensureAutogrow(lastIdx);
        }, { passive: true });

        wireReset();
        updateHeaderTotal();
    });
})();





