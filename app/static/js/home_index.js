document.addEventListener("DOMContentLoaded", () => {
  const nudge = document.getElementById("settingsNudgeModal");
  if (nudge && nudge.getAttribute("data-auto-open") === "1") {
    const modal = new bootstrap.Modal(nudge);
    modal.show();
  }
  const tbody = document.getElementById("recentEstimatesBody");
  if (!tbody) return;

  function fmtUpdated(iso) {
    try {
      if (!iso) return "";
      const d = new Date(iso);
      const now = new Date();
      const time = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

      const sameDay = d.toDateString() === now.toDateString();
      if (sameDay) return `Today, ${time}`;

      const y = new Date(now); y.setDate(now.getDate() - 1);
      if (d.toDateString() === y.toDateString()) return `Yesterday, ${time}`;

      const sameYear = d.getFullYear() === now.getFullYear();
      const opts = sameYear ? { month: "short", day: "numeric" }
                            : { month: "short", day: "numeric", year: "numeric" };
      return d.toLocaleDateString([], opts);
    } catch { return ""; }
  }

  function row(item) {
    const id = item.id;
    const name = item.name || "(untitled)";
    const cust = item.customer_name || "";
    const updated = fmtUpdated(item.updated_at);
    const editHref = `/estimates/${id}/edit?rt=/estimates`;

    return `
      <tr>
        <td><a class="text-decoration-none" href="${editHref}">${name}</a></td>
        <td>${cust}</td>
        <td>${updated}</td>
        <td class="text-end">
          <a class="btn btn-sm btn-outline-primary" href="${editHref}">Open</a>
        </td>
      </tr>`;
  }

  function emptyRow(msg) {
    return `<tr><td colspan="4" class="text-center text-muted py-4">${msg}</td></tr>`;
  }

  async function loadRecent() {
    try {
      const res = await fetch("/estimates/recent.json", {
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
      });
      if (!res.ok) {
        // Make 401/403 explicitly render the same friendly message as before
        if (res.status === 401 || res.status === 403) {
          tbody.innerHTML = emptyRow("Failed to load recent estimates.");
          return;
        }
        throw new Error("fetch failed");
      }
      const data = await res.json();
      const rows = (data && data.rows) || [];
      tbody.innerHTML = rows.length ? rows.map(row).join("") : emptyRow("No estimates yet.");
    } catch {
      tbody.innerHTML = emptyRow("Failed to load recent estimates.");
    }
  }

  loadRecent();
});

