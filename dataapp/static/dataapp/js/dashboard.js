(function () {
    function ready(fn) {
        if (document.readyState !== "loading") fn();
        else document.addEventListener("DOMContentLoaded", fn);
    }

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    function enhanceTables() {
        document.querySelectorAll(".table-responsive table").forEach((table, index) => {
            if (table.dataset.enhanced === "true") return;
            table.dataset.enhanced = "true";
            table.classList.add("table-hover");

            const wrapper = table.closest(".table-responsive");
            if (wrapper && !wrapper.previousElementSibling?.classList?.contains("table-toolbar")) {
                const toolbar = document.createElement("div");
                toolbar.className = "table-toolbar";
                toolbar.innerHTML = `
                    <div class="text-secondary small">Search and sort table data</div>
                    <input class="form-control table-search" type="search" placeholder="Search table" aria-label="Search table">
                `;
                wrapper.parentNode.insertBefore(toolbar, wrapper);
                const input = toolbar.querySelector("input");
                input.addEventListener("input", () => {
                    const term = normalize(input.value);
                    table.querySelectorAll("tbody tr").forEach((row) => {
                        row.style.display = normalize(row.textContent).includes(term) ? "" : "none";
                    });
                });
            }

            table.querySelectorAll("thead th").forEach((th, colIndex) => {
                th.setAttribute("role", "button");
                th.setAttribute("tabindex", "0");
                th.addEventListener("click", () => sortTable(table, colIndex, th));
                th.addEventListener("keydown", (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        sortTable(table, colIndex, th);
                    }
                });
            });
        });
    }

    function sortTable(table, colIndex, th) {
        const tbody = table.querySelector("tbody");
        if (!tbody) return;
        const direction = th.dataset.sortDirection === "asc" ? "desc" : "asc";
        table.querySelectorAll("thead th").forEach((item) => delete item.dataset.sortDirection);
        th.dataset.sortDirection = direction;

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((a, b) => {
            const av = a.children[colIndex]?.textContent.trim() || "";
            const bv = b.children[colIndex]?.textContent.trim() || "";
            const an = Number(av.replace(/,/g, ""));
            const bn = Number(bv.replace(/,/g, ""));
            const result = Number.isFinite(an) && Number.isFinite(bn)
                ? an - bn
                : av.localeCompare(bv, undefined, { numeric: true, sensitivity: "base" });
            return direction === "asc" ? result : -result;
        });
        rows.forEach((row) => tbody.appendChild(row));
    }

    function enhanceCharts() {
        document.querySelectorAll("[data-chart-card]").forEach((card) => {
            const fullscreen = card.querySelector("[data-chart-fullscreen]");
            const exportBtn = card.querySelector("[data-chart-export]");

            if (fullscreen) {
                fullscreen.addEventListener("click", () => {
                    card.classList.toggle("fullscreen-chart");
                    window.dispatchEvent(new Event("resize"));
                });
            }

            if (exportBtn) {
                exportBtn.addEventListener("click", () => {
                    const text = card.innerText.trim();
                    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "chart-insights.txt";
                    a.click();
                    URL.revokeObjectURL(url);
                });
            }
        });
    }

    function bindMobileSidebar() {
        document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
            button.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
        });
        document.querySelectorAll(".side-link").forEach((link) => {
            link.addEventListener("click", () => document.body.classList.remove("sidebar-open"));
        });
    }

    function copyButtons() {
        document.querySelectorAll("[data-copy-target]").forEach((button) => {
            button.addEventListener("click", async () => {
                const target = document.querySelector(button.dataset.copyTarget);
                if (!target) return;
                await navigator.clipboard.writeText(target.innerText || target.textContent || "");
                const original = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check2"></i>';
                setTimeout(() => { button.innerHTML = original; }, 1200);
            });
        });
    }

    ready(() => {
        enhanceTables();
        enhanceCharts();
        bindMobileSidebar();
        copyButtons();
    });
})();
