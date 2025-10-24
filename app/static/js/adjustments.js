document.addEventListener("DOMContentLoaded", () => {
    // Use the same per-estimate totals key as Estimator/Summary
    // Use the same per-estimate totals key as Estimator/Summary
    const { eid: EID, totalsKey: TOTALS_KEY, estimateDataKey: ESTIMATE_DATA_KEY } = nsKeys();
    const defaultLabels = [
        "Building Conditions", "Change Orders", "Embedded and exposed Wiring",
        "Construction Schedule", "Job Location", "Safety", "Teamwork",
        "Temperature", "Materials Handler", "Subcontract Supervision"
    ];

    const additionalLabels = [
        "As-Built Drawings", "Overtime Hours", "Environmentally Hazardous Material Disposal",
        "Excavation, Trenching, and Backfill", "Superintendent", "Materials Handler",
        "Testing/QAQC", "Safety", "Subcontract Supervision", "Training"
    ];

    const tableBody = document.getElementById("laborAdjustmentsBody");
    const additionalTableBody = document.getElementById("additionalLaborBody");

    let adjLastGrown = -1;
    let addLastGrown = -1;

    // Autogrow for Labor Adjustments: only when typing in the actual last row
    tableBody.addEventListener('input', (e) => {
        if (!(e.target instanceof HTMLInputElement)) return;
        if (e.target.type !== 'text') return;

        const tr = e.target.closest('tr');
        if (!tr) return;

        const idx = parseInt(tr.getAttribute('data-row') || '-1', 10);
        const isLast = tr.nextElementSibling === null;
        const hasText = e.target.value.trim() !== '';

        if (isLast && hasText && idx !== adjLastGrown) {
            createRow("", false);        // append exactly one new blank row
            adjLastGrown = idx;          // remember which row spawned it
        }

        updateFooterTotals();          // keep your totals flow
    });

    // Autogrow for Additional Labor: same pattern
    additionalTableBody.addEventListener('input', (e) => {
        if (!(e.target instanceof HTMLInputElement)) return;
        if (e.target.type !== 'text') return;

        const tr = e.target.closest('tr');
        if (!tr) return;

        const idx = parseInt(tr.getAttribute('data-row') || '-1', 10);
        const isLast = tr.nextElementSibling === null;
        const hasText = e.target.value.trim() !== '';

        if (isLast && hasText && idx !== addLastGrown) {
            createAdditionalRow("", false);
            addLastGrown = idx;
        }

        updateAdditionalLaborTotals();
    });

    // ---- S2-01: Sync 'Estimated Labor Hours' from Summary (localStorage.ee.totals) ----
    // Reads ee.totals.labor_hours_pricing_sheet and paints it into #est_lbr_hrs.
    // Quietly no-ops if data is missing/bad to keep console clean.
    function syncEstimatedLaborFromSummary() {
        try {
            const raw = localStorage.getItem(TOTALS_KEY);
            if (!raw) return;
            const data = JSON.parse(raw);

            const hrs = (data && typeof data.labor_hours_pricing_sheet === 'number')
                ? data.labor_hours_pricing_sheet
                : null;

            if (hrs == null) return;

            const cell = document.getElementById('est_lbr_hrs');
            if (cell) cell.textContent = hrs.toFixed(2);
        } catch (_) {
            // swallow parse or DOM errors; maintain a clean console
        }
    }

    function getEstimatedLaborHours() {
        const raw = document.getElementById("est_lbr_hrs").innerText;
        const value = parseFloat(raw.replace(/[^0-9.]/g, ""));
        return isNaN(value) ? 0 : value;
    }

    function populateAdjustmentTable() {
        tableBody.innerHTML = ""; // Clear any existing rows

        if (estimateData.adjustments.length > 0) {
            estimateData.adjustments.forEach((item, idx) => {
                // Make the LAST row dynamic if it's blank so it can autogrow on first keystroke
                const row = createRow(item.label, false);

                const inputs = row.querySelectorAll("input");
                const selects = row.querySelectorAll("select");

                if (inputs.length >= 2 && selects.length === 1) {
                    inputs[0].value = item.label;
                    selects[0].value = item.percent;
                    inputs[1].value = item.hours.toFixed(2);
                }
            });

            // If the last saved label is filled, add one blank dynamic row (keeps your original behavior)
            const last = estimateData.adjustments.at(-1);
            if (last?.label?.trim()) createRow("", false);
        } else {
            // First-time use: defaults + one dynamic row
            defaultLabels.forEach(label => createRow(label, false));
            createRow("", false);
        }

        updateFooterTotals(); // Update totals and persist structure

        // Ensure exactly one blank trailing row
        (function ensureTrailingBlankRow(tbody, makeRow) {
            const lastInput = tbody.lastElementChild?.querySelector('input[type="text"]');
            if (!lastInput || lastInput.value.trim() !== '') {
                makeRow("", false);  // append a dynamic blank row
            }
        })(tableBody, createRow);

        adjLastGrown = -1;

    }

    function populateAdditionalLaborTable() {
        additionalTableBody.innerHTML = ""; // Clear any existing rows

        if (estimateData.additionalLabor.length > 0) {
            estimateData.additionalLabor.forEach((item, idx) => {
                // Make the LAST row dynamic if it's blank so it can autogrow on first keystroke
                const row = createAdditionalRow(item.label, false);

                const inputs = row.querySelectorAll("input");
                const selects = row.querySelectorAll("select");

                if (inputs.length >= 2 && selects.length === 1) {
                    inputs[0].value = item.label;
                    selects[0].value = item.percent;
                    inputs[1].value = item.hours.toFixed(2);
                }
            });

            // If the last saved label is filled, add one blank dynamic row (keeps your original behavior)
            const last = estimateData.additionalLabor.at(-1);
            if (last?.label?.trim()) createAdditionalRow("", false);

        } else {
            // First-time use: defaults + one dynamic row
            additionalLabels.forEach(label => createAdditionalRow(label, false));
            createAdditionalRow("", false);
        }

        updateAdditionalLaborTotals(); // Refresh summary

        // Ensure exactly one blank trailing row
        (function ensureTrailingBlankRow(tbody, makeRow) {
            const lastInput = tbody.lastElementChild?.querySelector('input[type="text"]');
            if (!lastInput || lastInput.value.trim() !== '') {
                makeRow("", false);  // append a dynamic blank row
            }
        })(additionalTableBody, createAdditionalRow);

        addLastGrown = -1;

    }

    function createRow(label = "", isDynamic = false) {
        const row = document.createElement("tr");
        row.setAttribute('data-row', String(tableBody.rows.length));

        const descCell = document.createElement("td");
        const descInput = document.createElement("input");
        descInput.type = "text";
        descInput.style.width = "100%";
        descInput.value = label;
        descInput.classList.add("grid-input");        // make height consistent
        descCell.appendChild(descInput);
        row.appendChild(descCell);

        const adjCell = document.createElement("td");
        const select = document.createElement("select");
        select.className = "adjustment-percent";
        select.style.width = "100%";
        select.classList.add("grid-input");           // make height consistent
        for (let i = 0; i <= 100; i++) {
            const option = document.createElement("option");
            option.value = i;
            option.text = `${i}%`;
            select.appendChild(option);
        }
        adjCell.appendChild(select);
        row.appendChild(adjCell);

        const hrsCell = document.createElement("td");
        const hrsInput = document.createElement("input");
        hrsInput.type = "number";
        hrsInput.step = "0.01";
        hrsInput.value = "0.00";
        hrsInput.className = "adjustment-hours";
        hrsInput.style.width = "100%";
        hrsInput.classList.add("grid-input");         // make height consistent
        hrsCell.appendChild(hrsInput);
        row.appendChild(hrsCell);

        hrsInput.addEventListener("focus", () => {
            setTimeout(() => hrsInput.select(), 0);
            hrsInput.value = hrsInput.value.replace(/[^0-9.]/g, "");
        });

        hrsInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                let raw = parseFloat(hrsInput.value);
                hrsInput.value = isNaN(raw) ? "0.00" : raw.toFixed(2);
                hrsInput.blur();
                updateFooterTotals();
            }
        });

        hrsInput.addEventListener("blur", function () {
            let raw = parseFloat(hrsInput.value);
            hrsInput.value = isNaN(raw) ? "0.00" : raw.toFixed(2);
            updateFooterTotals();
        });


        descInput.addEventListener("input", () => {
            updateFooterTotals();  // 🔹 This makes sure label changes get saved
        });

        tableBody.appendChild(row);
        return row;
    }

    function createAdditionalRow(label = "", isDynamic = false) {
        const row = document.createElement("tr");
        row.setAttribute('data-row', String(additionalTableBody.rows.length));

        const descCell = document.createElement("td");
        const descInput = document.createElement("input");
        descInput.type = "text";
        descInput.style.width = "100%";
        descInput.value = label;
        descInput.classList.add("grid-input");        // make height consistent
        descCell.appendChild(descInput);
        row.appendChild(descCell);

        const adjCell = document.createElement("td");
        const select = document.createElement("select");
        select.className = "additional-percent";
        select.style.width = "100%";
        select.classList.add("grid-input");           // make height consistent
        for (let i = 0; i <= 100; i++) {
            const option = document.createElement("option");
            option.value = i;
            option.text = `${i}%`;
            select.appendChild(option);
        }
        adjCell.appendChild(select);
        row.appendChild(adjCell);

        const hrsCell = document.createElement("td");
        const hrsInput = document.createElement("input");
        hrsInput.type = "number";
        hrsInput.step = "0.01";
        hrsInput.value = "0.00";
        hrsInput.className = "additional-hours";
        hrsInput.style.width = "100%";
        hrsInput.classList.add("grid-input");         // make height consistent
        hrsCell.appendChild(hrsInput);
        row.appendChild(hrsCell);

        hrsInput.addEventListener("focus", () => {
            setTimeout(() => hrsInput.select(), 0);
            hrsInput.value = hrsInput.value.replace(/[^0-9.]/g, "");
        });

        hrsInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                let raw = parseFloat(hrsInput.value);
                hrsInput.value = isNaN(raw) ? "0.00" : raw.toFixed(2);
                hrsInput.blur();
                updateAdditionalLaborTotals();
            }
        });

        hrsInput.addEventListener("blur", function () {
            let raw = parseFloat(hrsInput.value);
            hrsInput.value = isNaN(raw) ? "0.00" : raw.toFixed(2);
            updateAdditionalLaborTotals();
        });

        // 🔹 Save label when edited
        descInput.addEventListener("input", () => {
            updateAdditionalLaborTotals();
        });

        // 🔹 Support Enter key to blur and move forward
        descInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                descInput.blur();
                const nextInput = row.querySelector("select, .additional-hours");
                if (nextInput) nextInput.focus();
            }
        });

        additionalTableBody.appendChild(row);
        return row;
    }

    function updateFooterTotals() {
        const hoursInputs = document.querySelectorAll(".adjustment-hours");
        const descInputs = document.querySelectorAll("#laborAdjustmentsBody input[type='text']");
        const percentSelects = document.querySelectorAll(".adjustment-percent");

        let totalAdjustment = 0;
        estimateData.adjustments = []; // Reset

        for (let i = 0; i < hoursInputs.length; i++) {
            const label = descInputs[i]?.value || "";
            const percent = parseFloat(percentSelects[i]?.value) || 0;
            const hours = parseFloat(hoursInputs[i]?.value) || 0;

            estimateData.adjustments.push({
                label: label,
                percent: percent,
                hours: hours
            });

            totalAdjustment += hours;
        }

        const base = getEstimatedLaborHours();
        estimateData.totals.estimated = base;
        estimateData.totals.adjustments = totalAdjustment;
        estimateData.totals.final = base + totalAdjustment + estimateData.totals.additional;

        document.getElementById("adjustmentHours").innerText = totalAdjustment.toFixed(2);
        document.getElementById("totalAdjustedHours").innerText = (base + totalAdjustment).toFixed(2);
        // Mirror into Additional Labor header base
        document.getElementById("total_adjusted_base").innerText = (base + totalAdjustment).toFixed(2);
        // Recompute 'Total Hours w/ Additional Labor' using current Additional total
        document.getElementById("totalWithAdditionalLabor").innerText = ((base + totalAdjustment) + (parseFloat(document.getElementById("additionalLaborTotal").innerText) || 0)).toFixed(2);


        saveEstimateData();  // 🔹 Persist changes
        syncSummaryPage();
    }

    function updateAdditionalLaborTotals() {
        const hrsInputs = document.querySelectorAll(".additional-hours");
        const descInputs = document.querySelectorAll("#additionalLaborBody input[type='text']");
        const percentSelects = document.querySelectorAll(".additional-percent");

        let totalAdditional = 0;
        estimateData.additionalLabor = []; // Reset

        for (let i = 0; i < hrsInputs.length; i++) {
            const label = descInputs[i]?.value || "";
            const percent = parseFloat(percentSelects[i]?.value) || 0;
            const hours = parseFloat(hrsInputs[i]?.value) || 0;

            estimateData.additionalLabor.push({
                label: label,
                percent: percent,
                hours: hours
            });

            totalAdditional += hours;
        }

        estimateData.totals.additional = totalAdditional;
        estimateData.totals.final =
            estimateData.totals.estimated +
            estimateData.totals.adjustments +
            totalAdditional;

        const base = parseFloat(document.getElementById("totalAdjustedHours").innerText) || 0;

        document.getElementById("additionalLaborTotal").innerText = totalAdditional.toFixed(2);
        document.getElementById("totalWithAdditionalLabor").innerText = (base + totalAdditional).toFixed(2);

        saveEstimateData();  // 🔹 Persist changes
        syncSummaryPage();
    }

    function syncSummaryPage() {
        const adjusted = document.getElementById("adjustmentHours");
        const additional = document.getElementById("additionalLaborTotal");

        const summaryAdjusted = document.getElementById("summaryAdjustedHours");
        const summaryAdditional = document.getElementById("summaryAdditionalHours");

        if (adjusted && summaryAdjusted) {
            summaryAdjusted.innerText = adjusted.innerText;
        }

        if (additional && summaryAdditional) {
            summaryAdditional.innerText = additional.innerText;
        }
    }

    // ---- S2-Reset: Reset BOTH tables (keep Estimated Labor Hours) -----------------
    // Zeros percents & hours in both tables, then reuses existing recompute flows.
    // Quietly no-ops on any DOM hiccup to keep console clean.
    function resetAdjustmentsPage() {
        try {

            // Trim autogrown rows in BOTH tables (keep base sets only)
            Array.from(tableBody.querySelectorAll('tr[data-row]')).forEach(tr => {
                const idx = parseInt(tr.getAttribute('data-row') || '-1', 10);
                if (!Number.isNaN(idx) && idx >= defaultLabels.length) tr.remove();
            });

            Array.from(additionalTableBody.querySelectorAll('tr[data-row]')).forEach(tr => {
                const idx = parseInt(tr.getAttribute('data-row') || '-1', 10);
                if (!Number.isNaN(idx) && idx >= additionalLabels.length) tr.remove();
            });
            // Zero all % selects
            document.querySelectorAll(".adjustment-percent").forEach(sel => sel.value = "0");
            document.querySelectorAll(".additional-percent").forEach(sel => sel.value = "0");

            // Zero all hours inputs
            document.querySelectorAll(".adjustment-hours").forEach(inp => inp.value = "0.00");
            document.querySelectorAll(".additional-hours").forEach(inp => inp.value = "0.00");

            // Recompute using your existing logic (also persists)
            updateFooterTotals();          // updates #adjustmentHours, #totalAdjustedHours, estimateData.totals.*
            updateAdditionalLaborTotals(); // updates #additionalLaborTotal, #totalWithAdditionalLabor

            // Ensure the Additional header base mirrors the adjusted total
            const baseAdj = parseFloat(document.getElementById("totalAdjustedHours").innerText) || 0;
            const baseCell = document.getElementById("total_adjusted_base");
            if (baseCell) baseCell.innerText = baseAdj.toFixed(2);

            // Ensure exactly one blank trailing row in BOTH tables
            (function ensureTrailingBlankRows() {
                // Labor Adjustments table
                const lastAdj = tableBody.lastElementChild?.querySelector('input[type="text"]');
                if (!lastAdj || lastAdj.value.trim() !== '') {
                    createRow("", false);   
                }

                // Additional Labor table
                const lastAdd = additionalTableBody.lastElementChild?.querySelector('input[type="text"]');
                if (!lastAdd || lastAdd.value.trim() !== '') {
                    createAdditionalRow("", false);  
                }
            })();

            // Note: #est_lbr_hrs is preserved (it’s sourced from ee.totals on load)
        } catch (_) { /* silent */ }

        // re-arm autogrow for the new last rows
        adjLastGrown = -1;
        addLastGrown = -1;

    }

    // Initialize
    loadEstimateData(); // Load from localStorage
    syncEstimatedLaborFromSummary(); // S2-01: pull Summary hours into #est_lbr_hrs
    populateAdjustmentTable();
    populateAdditionalLaborTable();

    // S2-Reset: hook up the header button
    const resetBtn = document.getElementById("resetAdjustmentsPageBtn");
    if (resetBtn) resetBtn.addEventListener("click", resetAdjustmentsPage);

    document.getElementById("laborAdjustmentsTable").addEventListener("change", function (e) {
        if (e.target && e.target.classList.contains("adjustment-percent")) {
            const percent = parseFloat(e.target.value);
            const baseHours = getEstimatedLaborHours();
            const row = e.target.closest("tr");
            const hoursInput = row.querySelector(".adjustment-hours");
            if (hoursInput && !isNaN(percent)) {
                hoursInput.value = ((percent / 100) * baseHours).toFixed(2);
            }
            updateFooterTotals();
        }
    });

    document.getElementById("additionalLaborTable").addEventListener("change", function (e) {
        if (e.target && e.target.classList.contains("additional-percent")) {
            const percent = parseFloat(e.target.value);
            const base = parseFloat(document.getElementById("totalAdjustedHours").innerText) || 0;
            const row = e.target.closest("tr");
            const hoursInput = row.querySelector(".additional-hours");
            if (hoursInput && !isNaN(percent)) {
                hoursInput.value = ((percent / 100) * base).toFixed(2);
            }
            updateAdditionalLaborTotals();
        }
    });

    document.getElementById("additionalLaborTable").addEventListener("input", function (e) {
        if (e.target && e.target.classList.contains("additional-hours")) {
            updateAdditionalLaborTotals();
        }
    });

    // --- S2-06: React to Summary resets/cross-page changes ---
    function __eeRecalcFromStorage() {
        // Pull fresh Estimator hours, then recompute both tables
        try { syncEstimatedLaborFromSummary(); } catch { }
        try { updateFooterTotals(); } catch { }
        try { updateAdditionalLaborTotals(); } catch { }
    }

    // When Summary clears/rewrites localStorage, update immediately
    window.addEventListener("storage", (e) => {
        const k = e.key || '';
        if (k === TOTALS_KEY || k === ESTIMATE_DATA_KEY) __eeRecalcFromStorage();
    });

    // When you switch back to this tab/page, ensure it’s fresh
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) __eeRecalcFromStorage();
    });

    // --- Mirror Estimator: paint header numbers straight from storage (no recompute needed) ---
    function paintAdjustmentsFromStorage() {
        let ed = {};
        try { ed = JSON.parse(localStorage.getItem(ESTIMATE_DATA_KEY) || '{}'); } catch { }
        const t = ed.totals || {};

        // Base (Estimator hours)
        let base = Number(t.estimated) || 0;
        if (!base) {
            try {
                const raw = localStorage.getItem(TOTALS_KEY);
                if (raw) base = Number(JSON.parse(raw).labor_hours_pricing_sheet) || 0;
            } catch { }
        }

        const adjusted = Number(t.adjustments) || 0;
        const additional = Number(t.additional) || 0;

        // Paint header cells
        const estCell = document.getElementById('est_lbr_hrs');
        const adjEl = document.getElementById('adjustmentHours');
        const totAdjEl = document.getElementById('totalAdjustedHours');
        const baseHdr = document.getElementById('total_adjusted_base');
        const addEl = document.getElementById('additionalLaborTotal');
        const withAdd = document.getElementById('totalWithAdditionalLabor');

        if (estCell) estCell.textContent = base.toFixed(2);
        if (adjEl) adjEl.innerText = adjusted.toFixed(2);
        if (totAdjEl) totAdjEl.innerText = (base + adjusted).toFixed(2);
        if (baseHdr) baseHdr.innerText = (base + adjusted).toFixed(2);
        if (addEl) addEl.innerText = additional.toFixed(2);
        if (withAdd) withAdd.innerText = (base + adjusted + additional).toFixed(2);

        // Keep in-memory totals coherent
        if (window.estimateData && estimateData.totals) {
            estimateData.totals.estimated = base;
            estimateData.totals.adjustments = adjusted;
            estimateData.totals.additional = additional;
            estimateData.totals.final = base + adjusted + additional;
        }
    }

    // Paint on return / storage change, just like Estimator’s header paint
    document.addEventListener("visibilitychange", () => { if (!document.hidden) paintAdjustmentsFromStorage(); });
    window.addEventListener("storage", (e) => {
        const k = e.key || '';
        if (k === TOTALS_KEY || k === ESTIMATE_DATA_KEY) paintAdjustmentsFromStorage();
    });
    window.addEventListener("pageshow", (e) => { if (e.persisted) paintAdjustmentsFromStorage(); });

    // Initial paint (after your tables are built)
    paintAdjustmentsFromStorage();

    // Consume a Summary "Reset All" that happened BEFORE this page loaded.
    (function consumeSummaryReset() {
        const last = localStorage.getItem('ee.reset');                 // timestamp set by Summary resetAllFromSummary()
        const seen = sessionStorage.getItem('ee.reset.seen@adjustments');
        if (last && last !== seen) {
            // Pull zeros from storage → zero the UI → persist zeros → repaint headers
            try { syncEstimatedLaborFromSummary(); } catch { }
            try { resetAdjustmentsPage(); } catch { }          // clears inputs/selects to 0
            try { updateFooterTotals(); } catch { }
            try { updateAdditionalLaborTotals(); } catch { }
            try { paintAdjustmentsFromStorage(); } catch { }
            sessionStorage.setItem('ee.reset.seen@adjustments', last);   // don’t repeat until next reset
        }
    })();

    // React to Summary "Reset All" (ee.reset) by hard-clearing the tables/UI
    window.addEventListener('storage', (e) => {
        if (e.key === 'ee.reset') {
            // zero the rows/inputs (your existing function)
            try { resetAdjustmentsPage(); } catch { }

            // re-seed headers from storage and persist zeros
            try { syncEstimatedLaborFromSummary(); } catch { }
            try { updateFooterTotals(); } catch { }
            try { updateAdditionalLaborTotals(); } catch { }
        }
    });


});

