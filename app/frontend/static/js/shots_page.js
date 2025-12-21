/**
 * App name: Quantum Computing Simulation
 * File: shots_page.js
 * Description: JavaScript for the Measurement Shots page.
 *              Handles filtering by simulation ID and client-side pagination
 *              with Google-style numbered page links (5 pages at a time).
 */

document.addEventListener("DOMContentLoaded", function() {
    /* ===========================================
       FILTER BY SIMULATION ID
       =========================================== */
    const simSelect = document.getElementById("filterSimID");

    if (simSelect) {
        // Auto-apply filter on dropdown change
        simSelect.addEventListener("change", () => {
            const simID = simSelect.value;

            if (!simID) {
                window.location.href = "/shots";
            } else {
                window.location.href = `/shots/${simID}`;
            }
        });
    }

    /* ===========================================
       CLIENT-SIDE PAGINATION
       =========================================== */
    const rowsPerPage = 20;
    const tbody = document.getElementById("shotsTableBody");
    const paginationContainer = document.getElementById("shotsPagination");

    // Exit if table doesn't exist (no simulation selected)
    if (!tbody || !paginationContainer) {
        return;
    }

    const rows = Array.from(tbody.querySelectorAll("tr"));
    if (rows.length === 0) {
        paginationContainer.style.display = "none";
        return;
    }

    let currentPage = 1;
    const totalPages = Math.ceil(rows.length / rowsPerPage);

    /**
     * Determine which 5 pages to display based on current page
     */
    function getPageRange(current, total) {
        let start, end;

        if (total <= 5) {
            // Less than 5 pages total, show all
            start = 1;
            end = total;
        } else if (current <= 3) {
            // Current page is 1-3, show pages 1-5
            start = 1;
            end = 5;
        } else if (current >= total - 2) {
            // Current page is among last 3, show last 5 pages
            start = total - 4;
            end = total;
        } else {
            // Show current page with 2 before and 2 after
            start = current - 2;
            end = current + 2;
        }

        return { start, end };
    }

    /**
     * Render pagination controls
     */
    function renderPagination() {
        paginationContainer.innerHTML = "";

        const { start, end } = getPageRange(currentPage, totalPages);

        for (let i = start; i <= end; i++) {
            const pageLink = document.createElement("a");
            pageLink.href = "#";
            pageLink.textContent = i;
            pageLink.classList.add("page-link");

            if (i === currentPage) {
                pageLink.classList.add("active");
            }

            pageLink.addEventListener("click", (e) => {
                e.preventDefault();
                renderPage(i);
            });

            paginationContainer.appendChild(pageLink);
        }
    }

    /**
     * Render a specific page of results
     */
    function renderPage(page) {
        if (page < 1) {
            page = 1;
        } else if (page > totalPages) {
            page = totalPages;
        }

        // Hide all rows
        rows.forEach((row) => {
            row.style.display = "none";
        });

        // Show rows for current page
        const startIndex = (page - 1) * rowsPerPage;
        const endIndex = startIndex + rowsPerPage;

        rows.slice(startIndex, endIndex).forEach((row) => {
            row.style.display = "";
        });

        currentPage = page;
        renderPagination();
    }

    // Initialize pagination
    if (totalPages <= 1) {
        paginationContainer.style.display = "none";
    } else {
        paginationContainer.style.display = "flex";
        renderPage(1);
    }
});
