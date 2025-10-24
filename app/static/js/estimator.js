// Module-level flag to prevent writing zeros on first load
let eeBooted = false;

// ===== Row persistence — SAVE only (Bite 1) =====
// ====== Per-estimate namespace (strict) ======
const { eid: EID, gridKey: GRID_KEY, totalsKey: TOTALS_KEY } = nsKeys();
let eeSaveTimer = null;
let eeHydrating = false; // will be used in next bite (restore). harmless for now.

const formatUSD = window.formatUSD || (n => `$${(Number(n) || 0).toFixed(2)}`);

function scheduleSaveGrid() {
  if (eeHydrating) return;                 // ignore saves during future hydrate
  if (eeSaveTimer) clearTimeout(eeSaveTimer);
  eeSaveTimer = setTimeout(saveGridToStorage, 200); // debounce to reduce churn
}

function saveGridToStorage() {
  try {
    const table = document.querySelector('table');
    if (!table) return;
    const tbody = table.tBodies[0] || table;

    const rows = [];
    for (const tr of Array.from(tbody.rows)) {
      if (!tr.cells || tr.cells.length < 10) continue;

      // Cols: 0 Notes | 1 Type | 2 Desc | 3 Qty | 4 Ladj | 5 Cost | 6 Ext | 7 LUnit | 8 LHrs | 9 Unit
      const notes = tr.cells[0].querySelector('input.cell-notes')?.value ?? '';
      const type = tr.cells[1].querySelector('select.cell-type')?.value ?? '';

      const descSel = tr.cells[2].querySelector('select.cell-desc');
      const descValue = descSel ? (descSel.value || '') : '';
      const descText = descSel ? (descSel.selectedOptions?.[0]?.textContent ?? '') : '';

      const qty = tr.cells[3].querySelector('input.cell-qty')?.value ?? '';
      const ladj = tr.cells[4].querySelector('select.cell-labor-adj')?.value ?? '1';

      rows.push({ notes, type, descValue, descText, qty, ladj });
    }

    localStorage.setItem(GRID_KEY, JSON.stringify({ v: 1, rows }));
  } catch {
    // keep console clean
  }
}

// ===== Row persistence — RESTORE (Bite 2) =====
const __DESC_CACHE = new Map(); // type → Promise<items[]>

async function getDescriptionsCached(type) {
  if (!type) return [];
  if (!__DESC_CACHE.has(type)) {
    __DESC_CACHE.set(type, fetchDescriptionsByType(type).catch(() => []));
  }
  return __DESC_CACHE.get(type);
}

function loadGridFromStorage() {
  try {
    const raw = localStorage.getItem(GRID_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data && data.v === 1 && Array.isArray(data.rows)) return data.rows;
  } catch { }
  return null;
}

// Ensure we have at least N data rows available to hydrate into
function ensureRowCount(minCount) {
  const table = document.querySelector('table');
  if (!table) return;
  const tbody = table.tBodies[0] || table;

  // Count rows that look like data rows (≥10 cells)
  let count = 0;
  for (const tr of Array.from(tbody.rows)) {
    if (tr.cells && tr.cells.length >= 10) count++;
  }

  while (count < minCount) {
    const nextIndex = getMaxRowIndex() + 1;
    appendBlankRow(nextIndex);
    count++;
  }
}

async function hydrateGridFromStorage() {
  const saved = loadGridFromStorage();
  if (!saved || !saved.length) return;

  eeHydrating = true;
  try {
    // Make sure enough rows exist
    ensureRowCount(saved.length);

    const table = document.querySelector('table');
    if (!table) return;
    const tbody = table.tBodies[0] || table;

    for (let i = 0; i < saved.length; i++) {
      const row = saved[i];
      const tr = tbody.rows[i];
      if (!tr || !tr.cells || tr.cells.length < 10) continue;

      // Cols: 0 Notes | 1 Type | 2 Desc | 3 Qty | 4 Ladj | 5 Cost | 6 Ext | 7 LUnit | 8 LHrs | 9 Unit
      const notesInput = tr.cells[0].querySelector('input.cell-notes');
      if (notesInput) notesInput.value = row.notes ?? '';

      const typeSel = tr.cells[1].querySelector('select.cell-type');
      if (typeSel) typeSel.value = row.type ?? '';

      // Ensure there is a desc <select>
      const descTd = tr.cells[2];
      let descSel = descTd?.querySelector('select.cell-desc');
      if (descTd && !descSel) {
        descTd.innerHTML = `<select class="cell-desc"><option value=""></option></select>`;
        descSel = descTd.querySelector('select.cell-desc');
      }

      // Populate desc options for this type, then select saved one
      if (descSel && row.type) {
        const items = await getDescriptionsCached(row.type);
        populateDescSelect(descSel, items); // your existing function

        // --- choose saved description (by value, else fallback to text)
        if (row.descValue) {
          descSel.value = row.descValue;
          if (descSel.value !== row.descValue && row.descText) {
            const opt = Array.from(descSel.options).find(o => o.textContent === row.descText);
            if (opt) descSel.value = opt.value;
          }
        } else if (row.descText) {
          const opt = Array.from(descSel.options).find(o => o.textContent === row.descText);
          if (opt) descSel.value = opt.value;
        }

         // --- FILL DEPENDENT CELLS (Cost ea, Labor Unit, Unit) BEFORE recalc
        if (descSel.value) {
          const tdCostEa = tr.cells[5]; // Cost ea
          const tdLaborUnit = tr.cells[7]; // Labor Unit
          const tdUnit = tr.cells[9]; // Unit

          const typeSel = tr.cells[1].querySelector('select.cell-type');
          const currentType = typeSel ? typeSel.value : '';

          if (currentType === 'Assemblies') {
            try {
              const res = await fetch(`/estimator/api/assemblies/${encodeURIComponent(descSel.value)}/rollup`, { headers: { 'Accept': 'application/json' } });
              if (!res.ok) throw new Error(`HTTP ${res.status}`);
              const info = await res.json();
              if (tdCostEa) { tdCostEa.textContent = formatCurrency(info?.material_cost_total || 0); tdCostEa.style.textAlign = 'right'; }
              if (tdLaborUnit) { tdLaborUnit.textContent = String(info?.labor_hours_total || 0); }
              if (tdUnit) { tdUnit.textContent = '1'; }
            } catch (e) {
              if (tdCostEa) { tdCostEa.textContent = formatUSD(0); tdCostEa.style.textAlign = 'right'; }
              if (tdLaborUnit) { tdLaborUnit.textContent = '0'; }
              if (tdUnit) { tdUnit.textContent = '1'; }
            }
          } else {
            const opt = descSel.selectedOptions && descSel.selectedOptions[0];
            if (opt) {
              const priceVal = opt.getAttribute('data-price') || '';
              const laborUnit = opt.getAttribute('data-labor-unit') || '';
              const unit = opt.getAttribute('data-unit') || '';
              if (tdCostEa) { tdCostEa.textContent = formatCurrency(priceVal); tdCostEa.style.textAlign = 'right'; }
              if (tdLaborUnit) tdLaborUnit.textContent = laborUnit;
              if (tdUnit) tdUnit.textContent = unit;
            }
          }

          // now compute Mat Ext / Labor Hrs based on these fields
          recalcFromDescSelect(descSel);
        }
      }

      // Qty
      const qtyInput = tr.cells[3].querySelector('input.cell-qty');
      if (qtyInput) {
        qtyInput.value = row.qty ?? '';
        // ensure Mat Ext/Labor Hrs reflect saved qty (after desc-based fill)
        recalcFromQtyInput(qtyInput);
      }

      // Labor Adj
      const ladjSel = tr.cells[4].querySelector('select.cell-labor-adj');
      if (ladjSel) {
        ladjSel.value = row.ladj ?? '1';
        // ensure Labor Hrs reflects saved ladj (qty/desc may already have run)
        recalcFromLaborAdjSelect(ladjSel);
      }
    }

    // Sync header after hydrate (temporarily bypass boot guard)
    const prevBoot = eeBooted;
    eeBooted = true;
    updateHeaderTotals();
    eeBooted = prevBoot;
  } finally {
    eeHydrating = false;
    scheduleSaveGrid(); // one normalized save after hydrate
  }
}

// Fetch estimate JSON and expose its snapshot for the page (no UI changes here)
async function fetchEstimateSnapshot(eid) {
  try {
    const res = await fetch(`/estimates/${encodeURIComponent(eid)}.json`, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    window.ESTIMATE_SNAPSHOT = data && data.settings_snapshot ? data.settings_snapshot : null;
  } catch (e) {
    console.error('[Estimator] Failed to load estimate snapshot for eid=%s', eid, e);
    window.ESTIMATE_SNAPSHOT = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  paintHeaderFromStorage();   // ← show last known totals immediately
  if (EID) { fetchEstimateSnapshot(EID).catch(() => {}); }
  fetch("/estimator/api/material-types")
    .then(response => response.json())
    .then(async data => {
      // S1-05b: cache for populating Material Type on new rows
      let types = Array.isArray(data) ? data.slice() : [];
      types = ['Assemblies', ...types.filter(t => t !== 'Assemblies')]; // put first, dedupe
      window.MATERIAL_TYPES = types;
      // Loop over the 10 rows rendered by estimator.html
      for (let i = 0; i < 10; i++) {
        const cell = document.getElementById(`materialType_${i}`);
        if (cell) {
          // Create a <select> element for Material Type
          const select = document.createElement("select");         // build a new <select> element
          select.name = `material-type_${i}`;                      // give it a unique name attribute tied to row index
          select.classList.add("material-type");                   // existing class for styling / hydration
          select.classList.add("cell-type");                       // S1-06b: NEW standard hook class used by delegated event listener
          select.setAttribute('data-row', String(i));              // S1-06b: tag with row index

          // Add the default "Select Type" option
          const defaultOption = document.createElement("option");
          defaultOption.value = "";
          defaultOption.textContent = "Select Type";
          select.appendChild(defaultOption);

          // Add the DB-driven options (with Assemblies first)
          types.forEach(t => {
            const option = document.createElement("option");
            option.value = t;
            option.textContent = t;
            select.appendChild(option);
          });

          // Insert the <select> into this cell
          cell.appendChild(select);
        }
      }
      await hydrateGridFromStorage();
    })
    .catch(error => {
      console.error("Failed to load material types:", error);
    });

  // 🔽 S1-05: Attach a single delegated listener to the table
  // This listener watches all inputs inside the table
  // and forwards relevant events to handleNotesInput().
  document.querySelector('table').addEventListener('input', handleNotesInput, { passive: true });

  // 🔽 S1-06b: delegated listener for Material Type changes
  // This will react whenever a <select class="cell-type"> changes value
  document.querySelector('table').addEventListener(
    'change',
    handleTypeChange,   // we’ll define this function in the next bite
    { passive: true }
  );

  // 🔽 S1-06c: delegated listener for Description changes
  document.querySelector('table').addEventListener(
    'change',
    handleDescChange,   // defined below
    { passive: true }
  );

  // 🔽 S1-06d: live calc — listen for Qty typing
  document.querySelector('table').addEventListener('input', handleQtyInput, { passive: true });

  // 🔽 S1-06d: live calc — listen for Labor Adj changes
  document.querySelector('table').addEventListener('change', handleLaborAdjChange, { passive: true });

  // 🔽 Qty formatting on blur (round to 2 decimals)
  document.querySelector('table').addEventListener('blur', handleQtyBlur, true);

  // ensure Description dropdowns exist on initial rows
  ensureInitialDescSelects();

  ensureQtyIntegerMode();

  //updateHeaderTotals();

  eeBooted = true;

  // 🔽 Reset button (top header) — clears rows and totals
  const resetBtn = document.getElementById('estimatorResetBtn');
  if (resetBtn) resetBtn.addEventListener('click', resetEstimate);
});

function paintHeaderFromStorage() {
  try {
    const raw = localStorage.getItem(TOTALS_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);

    const mat = (typeof data?.material_cost_price_sheet === 'number') ? data.material_cost_price_sheet : 0;
    const hrs = (typeof data?.labor_hours_pricing_sheet === 'number') ? data.labor_hours_pricing_sheet : 0;

    const matEl = document.getElementById('materialTotalDisplay');
    const hrsEl = document.getElementById('laborTotalDisplay');
    if (matEl) matEl.textContent = formatUSD(mat);
    if (hrsEl) hrsEl.textContent = (Number(hrs) || 0).toFixed(2);
  } catch { /* keep console clean */ }
}

/// --- Type-change handler — row-scoped Description (API + autogrow) ---
function handleTypeChange(e) {
  // Ensure the event target is the Material Type <select>
  const el = e.target;
  if (!(el instanceof HTMLSelectElement)) return;          // ignore non-selects
  if (!el.classList.contains('cell-type')) return;         // only handle our Type selects

  // Read the row index (from data-row) and the selected Type ('' if default)
  const rowIndex = parseInt(el.getAttribute('data-row') || '-1', 10);
  const selectedType = el.value;

  // NEW: avoid refetching if the type hasn't changed for this select
  if (el.dataset.lastType === selectedType) return;
  el.dataset.lastType = selectedType;

  // Locate the Description <td> that sits immediately to the right of the Type <td>
  const descTd = getDescTdFromTypeSelect(el);
  if (!descTd) return; // keep console clean if table structure is unexpected

  // If the Type was cleared, reset Description and all dependent fields in the same row
  if (!selectedType) {
    // Blank Description (no label)
    descTd.innerHTML = `<select class="cell-desc"><option value=""></option></select>`;

    // 2) Walk right from Description cell to clear downstream columns
    // 0 Notes | 1 Type | 2 Description | 3 Qty | 4 Labor Adj | 5 Cost ea | 6 Mat Ext | 7 Labor Unit | 8 Labor Hrs | 9 Unit
    const tdQty = descTd.nextElementSibling;                                // 3
    const tdLaborAdj = tdQty ? tdQty.nextElementSibling : null;                  // 4
    const tdCostEa = tdLaborAdj ? tdLaborAdj.nextElementSibling : null;        // 5
    const tdMatExt = tdCostEa ? tdCostEa.nextElementSibling : null;            // 6
    const tdLaborUnit = tdMatExt ? tdMatExt.nextElementSibling : null;            // 7
    const tdLaborHrs = tdLaborUnit ? tdLaborUnit.nextElementSibling : null;      // 8
    const tdUnit = tdLaborHrs ? tdLaborHrs.nextElementSibling : null;        // 9

    // NEW: clear Qty input too
    if (tdQty) {
      const qtyInput = tdQty.querySelector('input.cell-qty');
      if (qtyInput) qtyInput.value = '';
    }

    if (tdCostEa) { tdCostEa.textContent = ''; tdCostEa.style.textAlign = 'right'; }
    if (tdMatExt) { tdMatExt.textContent = formatUSD(0); tdMatExt.style.textAlign = 'right'; }
    if (tdLaborUnit) { tdLaborUnit.textContent = ''; }
    if (tdLaborHrs) { tdLaborHrs.textContent = '0.00'; tdLaborHrs.style.textAlign = 'right'; }
    if (tdUnit) { tdUnit.textContent = ''; }

    // 🔽 totals
    updateHeaderTotals();

    scheduleSaveGrid();

    return;
  }

  // Otherwise, show a "Loading…" select in that same row's Description cell
  const descSelect = renderLoadingDescSelect(descTd);

  // Kick off async fetch to populate options for this Type (row-scoped)
  populateDescForType(descSelect, selectedType);

  // Autogrow when picking Type in the *current last* row
  const idxForType = parseInt(el.getAttribute('data-row') || '-1', 10);
  autogrowIfLast(idxForType);
}

// Find the Description <td> that follows the Type <td> in the same row
// Assumption: In each row, the Description cell's <td> is immediately to the right of the Type cell's <td>.
function getDescTdFromTypeSelect(typeSelectEl) {
  const typeTd = typeSelectEl.closest('td');
  if (!typeTd) return null;
  return typeTd.nextElementSibling; // This targets the Description cell
}

// Render a "Loading..." <select> into the given Description <td>
function renderLoadingDescSelect(descTd) {
  descTd.innerHTML = `
    <select class="cell-desc" disabled aria-busy="true">
      <option value="">Loading…</option>
    </select>
  `;
  return descTd.querySelector('select.cell-desc');
}

// --- Bite 2 helper: fetch descriptions for a given Material Type from the API ---
// Returns a Promise resolving to an array (possibly empty). Keeps errors handled upstream.
async function fetchDescriptionsByType(selectedType) {
  // Assemblies: list assemblies as description options (id + name)
  if (selectedType === 'Assemblies') {
    const res = await fetch('/estimator/api/assemblies', { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const items = await res.json();
    if (!Array.isArray(items)) throw new Error('Bad payload (not an array)');
    // Shape to match populateDescSelect() expectations
    return items.map(it => ({
      id: it.id,
      item_description: it.name || it.item_description || ''
    }));
  }

  // Materials: existing path
  const url = `/estimator/api/material-descriptions?type=${encodeURIComponent(selectedType)}`;
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const payload = await res.json();
  if (!Array.isArray(payload)) throw new Error('Bad payload (not an array)');
  return payload;
}


// --- Bite 2 helper: populate a <select> element with description options ---
function populateDescSelect(descSelectEl, items) {
  // Default prompt option (enabled, selectable)
  const fragments = ['<option value="">Select description…</option>'];

  for (const it of items) {
    const value = (it.id != null) ? String(it.id) : String(it.item_description ?? '');
    const text = String(it.item_description ?? value);
    // Use *per-each* values in the dropdown data
    const priceEach = (it.price_each ?? it.price ?? '') + '';
    const laborEach = (it.labor_each ?? it.labor_unit ?? '') + '';

    // Keep original pack size for reference, but UI should act per-each
    const packSize = (it.unit ?? it.unit_quantity_size ?? '') + '';
    const unitEach = '1'; // always show/compute per-each in the estimator UI

    fragments.push(
      `<option value="${escapeHtml(value)}"
           data-price="${escapeHtml(priceEach)}"
           data-labor="${escapeHtml(laborEach)}"
           data-labor-unit="${escapeHtml(laborEach)}"
           data-unit="${escapeHtml(unitEach)}"
           data-pack="${escapeHtml(packSize)}"
           title="${escapeHtml(text)}${packSize ? ' — Pack: ' + escapeHtml(packSize) : ''}">${escapeHtml(text)}</option>`
    );
  }

  descSelectEl.innerHTML = fragments.join('');
  // Enable after the options are in
  descSelectEl.removeAttribute('disabled');
  descSelectEl.removeAttribute('aria-busy');
  // Put focus on the dropdown so user can immediately choose
  descSelectEl.focus();
}

// --- Bite 2 helper: orchestrate fetch + populate for the row's Description select ---
async function populateDescForType(descSelectEl, selectedType) {
  try {
    const items = await fetchDescriptionsByType(selectedType);

    if (!items.length) {
      descSelectEl.innerHTML = '<option value="">No matches</option>';
      descSelectEl.removeAttribute('aria-busy');
      descSelectEl.removeAttribute('disabled'); // keep enabled so user sees it’s interactive
      return;
    }

    populateDescSelect(descSelectEl, items); // enables & focuses
  } catch (err) {
    console.error('[Desc-B2] failed to load descriptions:', err);
    descSelectEl.innerHTML = '<option value="">— Error loading —</option>';
    descSelectEl.removeAttribute('aria-busy');
    descSelectEl.removeAttribute('disabled');
  }
}

// --- Small utility for HTML-escaping strings safely (used above) ---
function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

// ========== S1-06c — When Description changes, fill Cost ea, Labor Unit, Unit (row-scoped) ==========

function formatCurrency(value) { return formatUSD(value); }

// Helper: get a human-friendly row id for logs (works with/without data-row)
function getRowIdForLog(el) {
  const tr = el.closest('tr');
  if (!tr) return '?';
  return tr.getAttribute('data-row') || (el.getAttribute('data-row') || '?');
}

// =================== S1-06d — Live row calculations (helpers) ===================

// Parse "$1,234.56", "1234.56", "  12 " to a Number; fallback 0 on bad input
function toNumberLoose(s) {
  if (s == null) return 0;
  if (typeof s === 'number') return Number.isFinite(s) ? s : 0;
  const cleaned = String(s).replace(/[$,]/g, '').trim();
  const n = parseFloat(cleaned);
  return Number.isFinite(n) ? n : 0;
}

// Parse to non-negative integer; floor decimals; fallback 0
function toIntLoose(s) {
  const n = toNumberLoose(s);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.floor(n);
}

// Format hours to two decimals (e.g., 1.5 -> "1.50")
function formatHours(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0.00';
  return n.toFixed(2);
}

// From a <td>, walk N siblings to the right; return null if not found
function tdRight(td, steps) {
  let cur = td;
  for (let i = 0; i < steps && cur; i++) {
    cur = cur.nextElementSibling;
  }
  return cur || null;
}

// Recalc ext/hrs when user types Qty (anchor = Qty <input>)
function recalcFromQtyInput(qtyInput) {
  const tdQty = qtyInput.closest('td');
  if (!tdQty) return;

  // Column map (0-based): 0 Notes | 1 Type | 2 Desc | 3 Qty | 4 Ladj | 5 Cost | 6 Ext | 7 LUnit | 8 LHrs | 9 Unit
  const tdLaborAdj = tdRight(tdQty, 1); // col 4
  const tdCostEa = tdRight(tdQty, 2); // col 5
  const tdMatExt = tdRight(tdQty, 3); // col 6
  const tdLaborUnit = tdRight(tdQty, 4); // col 7
  const tdLaborHrs = tdRight(tdQty, 5); // col 8

  if (!tdCostEa || !tdMatExt || !tdLaborUnit || !tdLaborHrs || !tdLaborAdj) return;

  const qty = toIntLoose(qtyInput.value);
  const price = toNumberLoose(tdCostEa.textContent);
  const lunit = toNumberLoose(tdLaborUnit.textContent);
  const ladjSel = tdLaborAdj.querySelector('select');
  const ladj = ladjSel ? toNumberLoose(ladjSel.value) : 1;

  // Compute + write
  const matExt = qty * price;
  const laborH = qty * lunit * ladj;

  tdMatExt.textContent = formatCurrency(matExt);
  tdMatExt.style.textAlign = 'right';

  tdLaborHrs.textContent = formatHours(laborH);
  tdLaborHrs.style.textAlign = 'right';

  // 🔽 update header totals whenever a row changes
  updateHeaderTotals();
}

// Recalc hrs when user changes Labor Adj (anchor = Labor Adj <select>)
function recalcFromLaborAdjSelect(ladjSelect) {
  const tdLaborAdj = ladjSelect.closest('td');
  if (!tdLaborAdj) return;

  const tdQty = tdLaborAdj.previousElementSibling;  // col 3
  const tdLaborUnit = tdRight(tdLaborAdj, 3);             // col 7
  const tdLaborHrs = tdRight(tdLaborAdj, 4);             // col 8
  const tdCostEa = tdRight(tdLaborAdj, 1);             // col 5
  const tdMatExt = tdRight(tdLaborAdj, 2);             // col 6

  if (!tdQty || !tdLaborUnit || !tdLaborHrs) return;

  const qty = (tdQty.querySelector('input')) ? toIntLoose(tdQty.querySelector('input').value) : 0;
  const lunit = toNumberLoose(tdLaborUnit.textContent);
  const ladj = toNumberLoose(ladjSelect.value);

  // Hours depend on Ladj; recompute
  const laborH = qty * lunit * ladj;
  tdLaborHrs.textContent = formatHours(laborH);
  tdLaborHrs.style.textAlign = 'right';

  // Mat Ext recompute in case Qty changed recently
  if (tdCostEa && tdMatExt && tdQty) {
    const price = toNumberLoose(tdCostEa.textContent);
    const matExt = qty * price;
    tdMatExt.textContent = formatCurrency(matExt);
    tdMatExt.style.textAlign = 'right';
  }

  // 🔽 totals
  updateHeaderTotals();
}

// Recalc both when Description changes (anchor = Description <select>)
function recalcFromDescSelect(descSelect) {
  const descTd = descSelect.closest('td');
  if (!descTd) return;

  const tdQty = tdRight(descTd, 1); // col 3
  const tdLaborAdj = tdRight(descTd, 2); // col 4
  const tdCostEa = tdRight(descTd, 3); // col 5
  const tdMatExt = tdRight(descTd, 4); // col 6
  const tdLaborUnit = tdRight(descTd, 5); // col 7
  const tdLaborHrs = tdRight(descTd, 6); // col 8

  if (!tdQty || !tdLaborAdj || !tdCostEa || !tdMatExt || !tdLaborUnit || !tdLaborHrs) return;

  const qtyInput = tdQty.querySelector('input');
  const ladjSel = tdLaborAdj.querySelector('select');

  const qty = qtyInput ? toIntLoose(qtyInput.value) : 0;
  const price = toNumberLoose(tdCostEa.textContent);
  const lunit = toNumberLoose(tdLaborUnit.textContent);
  const ladj = ladjSel ? toNumberLoose(ladjSel.value) : 1;

  const matExt = qty * price;
  const laborH = qty * lunit * ladj;

  tdMatExt.textContent = formatCurrency(matExt);
  tdMatExt.style.textAlign = 'right';

  tdLaborHrs.textContent = formatHours(laborH);
  tdLaborHrs.style.textAlign = 'right';

  // 🔽 totals
  updateHeaderTotals();
}

// After picking a Description, move focus to Qty in the same row
function focusQtyFromDesc(descSelectEl) {
  const descTd = descSelectEl.closest('td');
  if (!descTd) return;
  const tdQty = descTd.nextElementSibling; // col 3
  const qtyInput = tdQty ? tdQty.querySelector('input.cell-qty') : null;
  if (qtyInput) {
    qtyInput.focus();
    // Optional: select existing value so user can overwrite quickly
    qtyInput.select?.();
  }
}

// =================== Header totals (position-based) ===================
// Uses your header spans:
//   <span id="materialTotalDisplay">...</span>
//   <span id="laborTotalDisplay">...</span>
function updateHeaderTotals() {
  // During initial boot, don't overwrite the header UI
  if (!eeBooted) return;

  const table = document.querySelector('table');
  if (!table) return;
  const tbody = table.tBodies[0] || table;

  let matTotal = 0;
  let hrsTotal = 0;

  // Column order (0-based):
  // 0 Notes | 1 Type | 2 Desc | 3 Qty | 4 Ladj | 5 Cost | 6 Mat Ext | 7 LUnit | 8 LHrs | 9 Unit
  for (const tr of Array.from(tbody.rows)) {
    // Skip non-data rows if any
    if (!tr.cells || tr.cells.length < 9) continue;

    const tdMatExt = tr.cells[6]; // Material Ext
    const tdLaborHrs = tr.cells[8]; // Labor Hrs

    if (tdMatExt) matTotal += toNumberLoose(tdMatExt.textContent);
    if (tdLaborHrs) hrsTotal += toNumberLoose(tdLaborHrs.textContent);
  }

  const matEl = document.getElementById('materialTotalDisplay');
  const hrsEl = document.getElementById('laborTotalDisplay');
  if (matEl) matEl.textContent = formatCurrency(matTotal);
  if (hrsEl) hrsEl.textContent = formatHours(hrsTotal);

  // NEW: persist raw numbers for Summary consumers — but only after boot
  if (eeBooted && (matTotal !== 0 || hrsTotal !== 0)) {
    persistEstimatorTotals(matTotal, hrsTotal);
  }

}

function ensureQtyIntegerMode() {
  document.querySelectorAll('input.cell-qty').forEach(inp => {
    inp.step = '1';
    inp.min = '0';
    inp.inputMode = 'numeric';
    inp.pattern = '\\d*';
  });
}

// Persist Estimator header totals to localStorage for Summary
// Keys must match spec; values are numbers (not formatted strings).
function persistEstimatorTotals(materialTotalNumber, laborTotalHoursNumber) {
  try {
    const payload = {
      material_cost_price_sheet: Number(materialTotalNumber) || 0,
      labor_hours_pricing_sheet: Number(laborTotalHoursNumber) || 0,
      updated_at: new Date().toISOString(),
    };
    window.localStorage.setItem(TOTALS_KEY, JSON.stringify(payload));
    // S3-02b — emit after persisting header totals
    try {
      if (window.ee && typeof window.ee.fire === 'function') {
        window.ee.fire('ee:totalsChanged', { totals: payload });
      }
    } catch (_) { /* keep console clean */ }

  } catch (_) {
    // Swallow storage errors (quota / private mode) to keep console clean.
  }
}

// ---- Qty hygiene helpers (integers only) ----

// Keep digits only; strip everything else. No decimals, no signs.
function sanitizeQtyInput(el) {
  if (!(el && typeof el.value === 'string')) return;
  let v = el.value.replace(/\D/g, '');      // keep digits only
  v = v.replace(/^0+(?=\d)/, '');           // trim leading zeros like "0005" -> "5"
  if (el.value !== v) el.value = v;
}

// On blur, normalize to a clean integer string (or blank if not a number)
function formatQtyOnBlur(el) {
  const digits = (el && el.value || '').toString().replace(/\D/g, '');
  if (!digits) return '';
  return String(parseInt(digits, 10));      // no decimals
}

// Put a blank <select class="cell-desc"> into the Description cell (col 2) for all existing rows
function ensureInitialDescSelects() {
  const table = document.querySelector('table');
  if (!table) return;
  const tbody = table.tBodies[0] || table;

  // Column order (0-based): 0 Notes | 1 Type | 2 Description | ...
  for (const tr of Array.from(tbody.rows)) {
    if (!tr.cells || tr.cells.length < 3) continue;
    const tdDesc = tr.cells[2];
    if (tdDesc && !tdDesc.querySelector('select.cell-desc')) {
      tdDesc.innerHTML = `<select class="cell-desc"><option value=""></option></select>`;
    }
  }
}

function getNextRowIndex() {
  const rows = document.querySelectorAll('tbody tr[data-row]');
  let maxIdx = -1;
  rows.forEach(tr => {
    const n = Number(tr.getAttribute('data-row'));
    if (!Number.isNaN(n) && n > maxIdx) maxIdx = n;
  });
  return maxIdx + 1;
}

// ---- Autogrow helpers (robust to initial + autogrown rows) ----

// Get a row index from ANY data-bearing element in the row
function getRowIndexFromAny(tr) {
  if (!tr) return -1;
  const el = tr.querySelector('select.cell-type[data-row], input.cell-notes[data-row], input.cell-qty[data-row]');
  const v = el ? parseInt(el.getAttribute('data-row') || '-1', 10) : -1;
  return Number.isNaN(v) ? -1 : v;
}

// Find the highest data-row index present across type/notes/qty
function getMaxRowIndex() {
  let max = -1;
  document.querySelectorAll('select.cell-type[data-row], input.cell-notes[data-row], input.cell-qty[data-row]')
    .forEach(el => {
      const v = parseInt(el.getAttribute('data-row') || '-1', 10);
      if (!Number.isNaN(v)) max = Math.max(max, v);
    });
  return max;
}

// If 'idx' is the current last index, append exactly one new blank row
function autogrowIfLast(idx) {
  if (Number.isNaN(idx) || idx < 0) return;
  const max = getMaxRowIndex();
  if (idx !== max) return;
  if (__AUTO_GROW_EXPANDED.has(idx)) return;

  __AUTO_GROW_EXPANDED.add(idx);
  const nextIndex = max + 1;
  appendBlankRow(nextIndex);
}

// ========== Reset everything to a clean slate (keeps the original 10 rows) ==========
function resetEstimate() {
  const table = document.querySelector('table');
  if (!table) return;
  const tbody = table.tBodies[0] || table;

  // Remove only autogrown rows (keep base rows 0..9)
  tbody.querySelectorAll('tr[data-row]').forEach(tr => {
    const idx = parseInt(tr.getAttribute('data-row') || '-1', 10);
    if (!Number.isNaN(idx) && idx >= 10) tr.remove();
  });

  // B) Reset each remaining row by column position
  // Column order (0-based):
  // 0 Notes | 1 Type | 2 Description | 3 Qty | 4 Ladj | 5 Cost | 6 Mat Ext | 7 LUnit | 8 LHrs | 9 Unit
  for (const tr of Array.from(tbody.rows)) {
    if (!tr.cells || tr.cells.length < 10) continue;

    // Notes (input)
    const notesInput = tr.cells[0].querySelector('input.cell-notes');
    if (notesInput) notesInput.value = '';

    // Type (select)
    const typeSelect = tr.cells[1].querySelector('select.cell-type');
    if (typeSelect) typeSelect.value = '';

    // Blank Description (no label)
    const descTd = tr.cells[2];
    if (descTd) {
      descTd.innerHTML = `<select class="cell-desc"><option value=""></option></select>`;
    }

    // Qty (input)
    const qtyInput = tr.cells[3].querySelector('input.cell-qty');
    if (qtyInput) qtyInput.value = '';

    // Labor Adj (select) — default back to 1.0
    const ladjSelect = tr.cells[4].querySelector('select.cell-labor-adj');
    if (ladjSelect) ladjSelect.value = '1';

    // Cost ea (blank, right-align)
    if (tr.cells[5]) {
      tr.cells[5].textContent = '';
      tr.cells[5].style.textAlign = 'right';
    }

    // Material Ext ($0.00, right-align)
    if (tr.cells[6]) {
      tr.cells[6].textContent = formatUSD(0);
      tr.cells[6].style.textAlign = 'right';
    }

    // Labor Unit (blank)
    if (tr.cells[7]) {
      tr.cells[7].textContent = '';
    }

    // Labor Hrs (0.00, right-align)
    if (tr.cells[8]) {
      tr.cells[8].textContent = '0.00';
      tr.cells[8].style.textAlign = 'right';
    }

    // Unit (blank)
    if (tr.cells[9]) {
      tr.cells[9].textContent = '';
    }
  }

  // C) Clear the autogrow guard and refresh header totals
  if (typeof __AUTO_GROW_EXPANDED?.clear === 'function') {
    __AUTO_GROW_EXPANDED.clear();
  }
  updateHeaderTotals();

  try { localStorage.removeItem(TOTALS_KEY); } catch { }

  try { localStorage.removeItem(GRID_KEY); } catch { }
}

// =================== S1-06d — Live row calculations (handlers) ===================

// Fires on any input event in the table; we only care about Qty <input>
function handleQtyInput(e) {
  const el = e.target;
  if (!(el instanceof HTMLInputElement)) return;
  if (!el.classList.contains('cell-qty')) return;

  // 1) Live sanitize (non-negative, strip junk, keep one dot)
  sanitizeQtyInput(el);

  // 2) Recalc
  recalcFromQtyInput(el);

  // 3) Autogrow if this row is the current last
  const tr = el.closest('tr');
  const idxForQty = getRowIndexFromAny(tr);
  autogrowIfLast(idxForQty);

  scheduleSaveGrid();
}

function handleQtyBlur(e) {
  const el = e.target;
  if (!(el instanceof HTMLInputElement)) return;
  if (!el.classList.contains('cell-qty')) return;

  // Format neatly to 2 decimals on blur (leave blank if not a number)
  const formatted = formatQtyOnBlur(el);
  if (formatted === '') {
    el.value = '';
  } else {
    el.value = formatted;
  }

  // Recalc (and header totals) with the final formatted value
  recalcFromQtyInput(el);

  scheduleSaveGrid();
}

// Fires on any change in the table; we only care about Labor Adj <select>
function handleLaborAdjChange(e) {
  const el = e.target;
  if (!(el instanceof HTMLSelectElement)) return;
  if (!el.classList.contains('cell-labor-adj')) return;
  recalcFromLaborAdjSelect(el);

  scheduleSaveGrid();
}

// Delegated handler: fires when a <select class="cell-desc"> changes
function handleDescChange(e) {
  const el = e.target;
  if (!(el instanceof HTMLSelectElement)) return;          // ignore non-selects
  if (!el.classList.contains('cell-desc')) return;         // only Description selects

  // Anchor = the Description <td>
  const descTd = el.closest('td');
  if (!descTd) return;

  // Column order per row (0-based):
  // 0 Notes | 1 Type | 2 Description | 3 Qty | 4 Labor Adj | 5 Cost ea | 6 Mat Ext | 7 Labor Unit | 8 Labor Hrs | 9 Unit
  const tdQty = descTd.nextElementSibling;                                // 3
  const tdLaborAdj = tdQty ? tdQty.nextElementSibling : null;                  // 4
  const tdCostEa = tdLaborAdj ? tdLaborAdj.nextElementSibling : null;        // 5
  const tdMatExt = tdCostEa ? tdCostEa.nextElementSibling : null;            // 6
  const tdLaborUnit = tdMatExt ? tdMatExt.nextElementSibling : null;            // 7
  const tdLaborHrs = tdLaborUnit ? tdLaborUnit.nextElementSibling : null;      // 8
  const tdUnit = tdLaborHrs ? tdLaborHrs.nextElementSibling : null;        // 9

  // --- CLEARED CASE: user unselects Description (value = "")
  if (!el.value) {
    // Clear Qty ONLY when Description is cleared
    if (tdQty) {
      const qtyInput = tdQty.querySelector('input.cell-qty');
      if (qtyInput) qtyInput.value = '';
    }

    if (tdCostEa) { tdCostEa.textContent = ''; tdCostEa.style.textAlign = 'right'; }
    if (tdMatExt) { tdMatExt.textContent = formatUSD(0); tdMatExt.style.textAlign = 'right'; }
    if (tdLaborUnit) { tdLaborUnit.textContent = ''; }
    if (tdLaborHrs) { tdLaborHrs.textContent = '0.00'; tdLaborHrs.style.textAlign = 'right'; }
    if (tdUnit) { tdUnit.textContent = ''; }

    updateHeaderTotals();
    return;
  }

  // --- ASSEMBLIES CASE: Type = 'Assemblies' → fetch rollup and fill cells
  // Detect the current row's Type value
  const tr = el.closest('tr');
  const typeSel = tr ? tr.querySelector('select.cell-type') : null;
  const currentType = typeSel ? typeSel.value : '';
  if (currentType === 'Assemblies') {
    if (!tdCostEa || !tdLaborUnit || !tdUnit) return; // structure guard
    tdUnit.textContent = '1';
    fetch(`/estimator/api/assemblies/${encodeURIComponent(el.value)}/rollup`, { headers: { 'Accept': 'application/json' } })
      .then(res => res.ok ? res.json() : Promise.reject(res.status))
      .then(info => {
        const priceEach = Number(info?.material_cost_total || 0);
        const laborEach = Number(info?.labor_hours_total || 0);
        tdCostEa.textContent = formatCurrency(priceEach);
        tdCostEa.style.textAlign = 'right';
        tdLaborUnit.textContent = String(laborEach);

        // Compute Material Ext & Labor Hrs immediately (also updates header totals)
        recalcFromDescSelect(el);

        // Move cursor to Qty for fast entry
        focusQtyFromDesc(el);

        scheduleSaveGrid();
      })
      .catch(err => {
        console.error('[ASM] rollup fetch failed:', err);
        tdCostEa.textContent = formatUSD(0);
        tdCostEa.style.textAlign = 'right';
        tdLaborUnit.textContent = '0';
        recalcFromDescSelect(el);
        scheduleSaveGrid();
      });
    return; // skip normal material flow
  }

  // --- SELECTED CASE: fill fields from option data-* and recalc row
  if (!tdCostEa || !tdLaborUnit || !tdUnit) return; // structure guard
  const opt = el.selectedOptions && el.selectedOptions[0];
  if (!opt) return;

  // Prefer dataset (fast + correct); fall back to getAttribute for safety
  const priceVal = (opt.dataset?.price ?? opt.getAttribute('data-price') ?? '0');

  // Labor per-each might be stored as data-labor-unit OR data-labor.
  // Try both so it never shows blank.
  const laborEach =
    (opt.dataset?.laborUnit ??
      opt.getAttribute('data-labor-unit') ??
      opt.dataset?.labor ??
      opt.getAttribute('data-labor') ??
      '0');

  // We always show per-each in the UI, so Unit should display "1"
  const unitEach = (opt.dataset?.unit ?? opt.getAttribute('data-unit') ?? '1');

  // (Optional) original pack size remains available if you ever want it:
  // const packSize = opt.dataset?.pack ?? opt.getAttribute('data-pack') ?? '';

  tdCostEa.textContent = formatCurrency(priceVal);
  tdCostEa.style.textAlign = 'right';
  tdLaborUnit.textContent = laborEach;
  tdUnit.textContent = unitEach;

  // Compute Material Ext & Labor Hrs immediately (also updates header totals)
  recalcFromDescSelect(el);

  // Move cursor to Qty for fast entry
  focusQtyFromDesc(el);

  scheduleSaveGrid();
}

// --- S1-05: guard so each last row only expands once ---
const __AUTO_GROW_EXPANDED = new Set(); // stores row indices we've already expanded

// 🔽 S1-05: Handle Notes input
// This function fires whenever an <input> event bubbles up from the table
function handleNotesInput(e) {
  const el = e.target;

  // Ensure the event target is an <input> element
  if (!(el instanceof HTMLInputElement)) return;

  // Only continue if this input has the .cell-notes class
  if (!el.classList.contains('cell-notes')) return;

  // Get the row index from its data-row attribute
  const idx = parseInt(el.getAttribute('data-row') || '-1', 10);

  // Ignore if the Notes cell is still empty
  if (!el.value.trim()) return;

  // Find the highest (last) Notes index currently on the page
  let max = -1;
  document.querySelectorAll('input.cell-notes[data-row]').forEach(inp => {
    const v = parseInt(inp.getAttribute('data-row') || '-1', 10);
    if (!Number.isNaN(v)) max = Math.max(max, v);
  });

  // Only act when typing inside the current last row
  if (idx === max) {
    // Guard: if we've already expanded this index, do nothing
    if (__AUTO_GROW_EXPANDED.has(idx)) return;

    __AUTO_GROW_EXPANDED.add(idx);      // remember we've expanded this row once
    const nextIndex = max + 1;          // compute the new row's data-row
    appendBlankRow(nextIndex);          // 🔧 build + append exactly one new blank row
  }
  scheduleSaveGrid();
}

// --- S1-05: build + append one new blank estimator row ---
function appendBlankRow(index) {
  // 1) Find the estimator table and its <tbody> (fallback to the table itself)
  const table = document.querySelector('table'); // same element we attached the listener to
  if (!table) return;
  const tbody = table.tBodies[0] || table;

  // 2) Create the new table row with the correct data-row
  const tr = document.createElement('tr');
  tr.setAttribute('data-row', String(index));

  // 3) Build cells in the same column order as Estimator.html
  // Notes (editable input, required class + data-row)
  const tdNotes = document.createElement('td');
  const notes = document.createElement('input');
  notes.type = 'text';
  notes.name = `notes_${index}`;
  notes.classList.add('cell-notes');
  notes.setAttribute('data-row', String(index));
  tdNotes.appendChild(notes);

  // Material Type host cell (id pattern used by your initial hydration)
  // We will populate the <select> in a later bite; id is critical now.
  const tdMatType = document.createElement('td');
  tdMatType.id = `materialType_${index}`;

  // Description: always render a blank <select> so it doesn't "appear" later
  const tdDesc = document.createElement('td');
  tdDesc.classList.add('cell-description');
  tdDesc.innerHTML = `<select class="cell-desc"><option value=""></option></select>`;

  // Qty (editable input, required class + data-row)
  const tdQty = document.createElement('td');
  const qty = document.createElement('input');
  qty.type = 'number';
  qty.step = '1';
  qty.inputMode = 'numeric';     // mobile keyboards
  qty.pattern = '\\d*';          // HTML hint: digits only
  qty.min = '0';
  qty.name = `qty_${index}`;
  qty.classList.add('cell-qty');
  qty.setAttribute('data-row', String(index));
  tdQty.appendChild(qty);

  // Labor Adj (dropdown, required class + data-row)
  const tdLaborAdj = document.createElement('td');
  const ladj = document.createElement('select');
  ladj.name = `labor_adj_${index}`;
  ladj.classList.add('cell-labor-adj');
  ladj.setAttribute('data-row', String(index));
  [0.25, 0.5, 1, 1.5, 2].forEach(v => {
    const o = document.createElement('option');
    o.value = String(v);
    o.textContent = String(v);
    ladj.appendChild(o);
  });

  // Default selection = 1.0
  ladj.value = '1';
  tdLaborAdj.appendChild(ladj);

  // Remaining columns (placeholders to preserve grid shape; wiring comes later)
  const tdCostEa = document.createElement('td'); tdCostEa.classList.add('cell-cost-ea');
  const tdMatExt = document.createElement('td'); tdMatExt.classList.add('cell-material-ext');
  tdMatExt.textContent = formatUSD(0); // default display
  tdMatExt.style.textAlign = 'right'; // align right
  const tdLaborUnit = document.createElement('td'); tdLaborUnit.classList.add('cell-labor-unit');
  const tdLaborHrs = document.createElement('td'); tdLaborHrs.classList.add('cell-labor-hrs');
  tdLaborHrs.textContent = '0.00'; // default display
  tdLaborHrs.style.textAlign = 'right'; // align right
  const tdUnit = document.createElement('td'); tdUnit.classList.add('cell-unit');

  // 4) Append cells in the exact display order used by the table
  [
    tdNotes,
    tdMatType,
    tdDesc,
    tdQty,
    tdLaborAdj,
    tdCostEa,
    tdMatExt,
    tdLaborUnit,
    tdLaborHrs,
    tdUnit
  ].forEach(td => tr.appendChild(td));

  // 5) Append the new row to the table
  tbody.appendChild(tr);

  // Populate the Material Type <select> for this new row
  hydrateMaterialTypeCell(index);

  scheduleSaveGrid();
}

// --- S1-05b: populate Material Type <select> for the given row index ---
function hydrateMaterialTypeCell(index) {
  const cell = document.getElementById(`materialType_${index}`);
  if (!cell) return;

  const select = document.createElement('select');         // build a new <select> element
  select.name = `material-type_${index}`;                  // give it a unique name attribute tied to row index
  select.classList.add('material-type');                   // existing class for styling / hydration
  select.classList.add('cell-type');                       // S1-06b: NEW standard hook class used by delegated event listener
  select.setAttribute('data-row', String(index));          // S1-06b: tag with row index

  // Default option
  const def = document.createElement('option');
  def.value = '';
  def.textContent = 'Select Type';
  select.appendChild(def);

  // Options from cached list set during initial fetch
  const types = Array.isArray(window.MATERIAL_TYPES) ? window.MATERIAL_TYPES : [];
  types.forEach(t => {
    const o = document.createElement('option');
    o.value = t;
    o.textContent = t;
    select.appendChild(o);
  });

  cell.appendChild(select);
}