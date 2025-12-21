/**
 * App name: Quantum Computing Simulation
 * File: simulations_page.js
 * Description: JavaScript for the Simulations page.
 *              Handles creating new simulations, viewing shots, and deleting.
 *              Uses FloatingProgress from base.js for progress tracking.
 */

/* ===========================================
   COMMON UTILITIES
   =========================================== */
// Clear button functionality
document.querySelectorAll(".clearBtn").forEach(btn => {
    btn.addEventListener("click", function() {
        const form = btn.closest("form");
        if (form) {
            form.reset();
        }
    });
});

// Close modal buttons
document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('dialog').close();
    });
});

/* ===========================================
   ADD SIMULATION (POST)
   =========================================== */
// Open the add form
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("showSimFormBtn");
    const dialog = document.getElementById("addSimDialog");
    const form = document.getElementById("addSimForm");
    const errorDiv = document.getElementById("addFormErrorMsg");

    if (!button || !dialog) return;

    button.addEventListener("click", () => {
        // Check if simulation is already running
        if (window.FloatingProgress && window.FloatingProgress.hasActiveSimulation()) {
            alert("A simulation is already running. Please wait for it to complete.");
            return;
        }

        // Clear error message
        errorDiv.textContent = "";
        
        // Reset form to default values
        form.reset();
        
        dialog.showModal();
    });
});

// Handle POST submission with progress tracking
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("addSimForm");
    const dialog = document.getElementById("addSimDialog");
    const errorDiv = document.getElementById("addFormErrorMsg");

    if (!form) return;

    form.addEventListener("submit", async function(e) {
        e.preventDefault(); 
        errorDiv.textContent = "";

        // Double-check for active simulation
        if (window.FloatingProgress && window.FloatingProgress.hasActiveSimulation()) {
            errorDiv.textContent = "A simulation is already running. Please wait for it to complete.";
            return;
        }

        // Get form values
        const stateSelect = document.getElementById("stateID");
        const gateSelect = document.getElementById("gateID");
        const stateID = stateSelect.value;
        const gateID = gateSelect.value;
        const numShots = parseInt(document.getElementById("numShots").value);

        // Get display text for progress window
        const stateText = stateSelect.options[stateSelect.selectedIndex]?.text || 'state';
        const gateText = gateSelect.options[gateSelect.selectedIndex]?.text || 'gate';

        // Client-side validation
        if (!stateID) {
            errorDiv.textContent = "Please select an initial state.";
            return;
        }
        if (!gateID) {
            errorDiv.textContent = "Please select a gate.";
            return;
        }
        if (isNaN(numShots) || numShots < 5 || numShots > 100) {
            errorDiv.textContent = "Number of shots must be between 5 and 100.";
            return;
        }

        // Prepare data
        const data = {
            stateID: stateID,
            gateID: gateID,
            numShots: numShots
        };

        try {
            const response = await fetch("/simulations", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            if (response.status === 202) {
                // Accepted - close dialog and show floating progress window
                const simID = result.simID;
                const total = result.total || numShots;
                
                // Close the dialog
                dialog.close();
                
                // Start floating progress (from base.js)
                if (window.FloatingProgress) {
                    window.FloatingProgress.startSimulation(simID, total, stateText, gateText);
                }
                
            } else {
                // Display error message from server
                errorDiv.textContent = result.message || "An error occurred.";
            }
        } catch (err) {
            console.error(err);
            errorDiv.textContent = "An internal server error occurred.";
        }
    });
});

/* ===========================================
   VIEW SHOTS
   =========================================== */
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("button[id^='View-']").forEach(btn => {
        btn.addEventListener("click", function() {
            const simID = this.id.split("-")[1];
            window.location.href = `/shots/${simID}`;
        });
    });
});

/* ===========================================
   DELETE SIMULATION
   =========================================== */
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("button[id^='Delete-']").forEach(btn => {
        btn.addEventListener("click", async function() {
            const simID = this.id.split("-")[1];
            
            const confirmed = confirm(
                `Delete Simulation #${simID}?\n\n` +
                `All associated results will also be deleted.`
            );
            
            if (!confirmed) return;

            try {
                const response = await fetch(`/simulations/${simID}`, { 
                    method: 'DELETE' 
                });
                
                if (response.status === 204) {
                    window.location.href = "/simulations";
                } else {
                    const result = await response.json();
                    alert(result.message || "Failed to delete simulation.");
                }
            } catch (err) {
                console.error(err);
                alert("Error while deleting simulation.");
            }
        });
    });
});
