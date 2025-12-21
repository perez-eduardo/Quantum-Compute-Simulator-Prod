/**
 * App name: Quantum Computing Simulation
 * File: states_page.js
 * Description: JavaScript for the Quantum States page.
 *              Handles CRUD operations with normalization validation.
 */

/* ===========================================
   HELPER FUNCTIONS
   =========================================== */
/**
 * Convert backend error messages to user-friendly text
 */
function formatErrorMessage(message) {
    if (!message) return "An error occurred.";
    
    // Handle unique constraint errors
    if (message.includes('unique constraint') || message.includes('Duplicate')) {
        if (message.toLowerCase().includes('name')) {
            return "A state with this name already exists. Please choose a different name.";
        }
        if (message.toLowerCase().includes('symbol')) {
            return "A state with this symbol already exists. Please choose a different symbol.";
        }
        return "This entry already exists. Please use different values.";
    }
    
    return message;
}

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
   ADD STATE (POST)
   =========================================== */
// Open the add form
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("showStatesFormBtn");
    const dialog = document.getElementById("addStateDialog");
    const form = document.getElementById("addStateForm");
    const errorDiv = document.getElementById("addFormErrorMsg");

    if (!button || !dialog) return;

    button.addEventListener("click", () => {
        // Clear error message
        errorDiv.textContent = "";
        
        // Reset form to default values
        form.reset();
        
        // Set default coefficient values
        document.getElementById('addAlphaReal').value = 0.5;
        document.getElementById('addAlphaImgn').value = 0.5;
        document.getElementById('addBetaReal').value = 0.5;
        document.getElementById('addBetaImgn').value = 0.5;
        
        dialog.showModal();
    });
});

// Handle POST submission
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("addStateForm");
    const errorDiv = document.getElementById("addFormErrorMsg");

    if (!form) return;

    form.addEventListener("submit", async function(e) {
        e.preventDefault(); 
        errorDiv.textContent = "";

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch("/states", {
                method: "POST",
                body: new URLSearchParams(data)
            });
            const result = await response.json();

            if (response.status === 201) {
                document.getElementById("addStateDialog").close();
                window.location.href = "/states";
            } else if (response.status === 400) {
                errorDiv.textContent = formatErrorMessage(result.message);
                
                // Auto-populate recommended normalized values
                if (result.data) {
                    if (result.data.alphaReal !== undefined) {
                        document.getElementById('addAlphaReal').value = result.data.alphaReal;
                    }
                    if (result.data.alphaImgn !== undefined) {
                        document.getElementById('addAlphaImgn').value = result.data.alphaImgn;
                    }
                    if (result.data.betaReal !== undefined) {
                        document.getElementById('addBetaReal').value = result.data.betaReal;
                    }
                    if (result.data.betaImgn !== undefined) {
                        document.getElementById('addBetaImgn').value = result.data.betaImgn;
                    }
                }
            } else {
                errorDiv.textContent = formatErrorMessage(result.message);
            }
        } catch (err) {
            console.error(err);
            errorDiv.textContent = "An internal server error occurred.";
        }
    });
});

/* ===========================================
   EDIT STATE (PUT)
   =========================================== */
// Open the edit form
document.addEventListener('DOMContentLoaded', () => {
    const editButtons = document.querySelectorAll('[id^="Edit-"]');
    const errorDiv = document.getElementById("editFormErrorMsg");

    editButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Clear error message
            if (errorDiv) errorDiv.textContent = "";
            
            // Get the table row for this button
            const tr = button.closest('tr');
            const tds = tr.querySelectorAll('td');
            const stateID = tr.dataset.stateId;

            // Populate form fields
            document.getElementById('editStateID').value = stateID;
            document.getElementById('editStateName').value = tds[0].textContent;
            
            // Strip |> wrapper from symbol
            let symbolValue = tds[1].textContent.trim();
            if (symbolValue.startsWith('|') && symbolValue.endsWith('>')) {
                symbolValue = symbolValue.slice(1, -1);
            }
            document.getElementById('editStateSymbol').value = symbolValue;
            
            document.getElementById('editAlphaReal').value = tds[2].textContent;
            document.getElementById('editAlphaImgn').value = tds[3].textContent;
            document.getElementById('editBetaReal').value = tds[4].textContent;
            document.getElementById('editBetaImgn').value = tds[5].textContent;
            document.getElementById('editDescription').value = tds[6].textContent;

            document.getElementById('editStateDialog').showModal();
        });
    });
});

// Handle PUT submission
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("editStateForm");
    const errorDiv = document.getElementById("editFormErrorMsg");

    if (!form) return;

    form.addEventListener("submit", async function(e) {
        e.preventDefault(); 
        errorDiv.textContent = "";

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const stateId = document.getElementById("editStateID").value;

        try {
            const response = await fetch(`/states/${stateId}`, {
                method: "PUT",
                body: new URLSearchParams(data)
            });
            const result = await response.json();

            if (response.status === 200) {
                document.getElementById("editStateDialog").close();
                window.location.href = "/states";
            } else if (response.status === 400) {
                errorDiv.textContent = formatErrorMessage(result.message);
                
                // Auto-populate recommended normalized values
                if (result.data) {
                    if (result.data.alphaReal !== undefined) {
                        document.getElementById('editAlphaReal').value = result.data.alphaReal;
                    }
                    if (result.data.alphaImgn !== undefined) {
                        document.getElementById('editAlphaImgn').value = result.data.alphaImgn;
                    }
                    if (result.data.betaReal !== undefined) {
                        document.getElementById('editBetaReal').value = result.data.betaReal;
                    }
                    if (result.data.betaImgn !== undefined) {
                        document.getElementById('editBetaImgn').value = result.data.betaImgn;
                    }
                }
            } else {
                errorDiv.textContent = formatErrorMessage(result.message);
            }
        } catch (err) {
            console.error(err);
            errorDiv.textContent = "An internal server error occurred.";
        }
    });
});

/* ===========================================
   DELETE STATE
   =========================================== */
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("button[id^='Delete-']").forEach(btn => {
        btn.addEventListener("click", async function() {
            const stateId = this.id.split("-")[1];
            const row = this.closest('tr');
            const stateName = row ? row.querySelector('td').textContent : `ID ${stateId}`;
            
            const confirmed = confirm(
                `Delete "${stateName}"?\n\n` +
                `Related simulations will also be deleted.`
            );
            
            if (!confirmed) return;

            try {
                const response = await fetch(`/states/${stateId}`, {
                    method: 'DELETE'
                });

                if (response.status === 204) {
                    window.location.href = "/states";
                } else {
                    const result = await response.json();
                    alert(formatErrorMessage(result.message));
                }
            } catch (err) {
                console.error(err);
                alert("An internal server error occurred.");
            }
        });
    });
});

/* ===========================================
   COEFFICIENT INCREMENT/DECREMENT HANDLING
   =========================================== */
// Custom 0.1 step for coefficient inputs while allowing precise typed values
document.addEventListener('DOMContentLoaded', () => {
    const coefficientInputs = document.querySelectorAll(
        '#addAlphaReal, #addAlphaImgn, #addBetaReal, #addBetaImgn, ' +
        '#editAlphaReal, #editAlphaImgn, #editBetaReal, #editBetaImgn'
    );
    
    coefficientInputs.forEach(input => {
        let previousValue = parseFloat(input.value) || 0;
        
        // Store value on focus
        input.addEventListener('focus', () => {
            previousValue = parseFloat(input.value) || 0;
        });
        
        // Handle arrow keys
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                e.preventDefault();
                const currentVal = parseFloat(input.value) || 0;
                let newVal = e.key === 'ArrowUp' ? currentVal + 0.1 : currentVal - 0.1;
                newVal = Math.max(-1, Math.min(1, newVal));
                input.value = parseFloat(newVal.toFixed(8));
                previousValue = parseFloat(input.value);
            }
        });
        
        // Handle mouse wheel
        input.addEventListener('wheel', (e) => {
            if (document.activeElement === input) {
                e.preventDefault();
                const currentVal = parseFloat(input.value) || 0;
                let newVal = e.deltaY < 0 ? currentVal + 0.1 : currentVal - 0.1;
                newVal = Math.max(-1, Math.min(1, newVal));
                input.value = parseFloat(newVal.toFixed(8));
                previousValue = parseFloat(input.value);
            }
        });
        
        // Intercept native spinner button clicks
        input.addEventListener('input', () => {
            const currentVal = parseFloat(input.value) || 0;
            const diff = currentVal - previousValue;
            const nativeStep = 0.00000001;
            
            // If change matches native step, it was a spinner click
            if (Math.abs(Math.abs(diff) - nativeStep) < 0.000000001) {
                const direction = diff > 0 ? 1 : -1;
                let newVal = previousValue + (direction * 0.1);
                newVal = Math.max(-1, Math.min(1, newVal));
                input.value = parseFloat(newVal.toFixed(8));
            }
            previousValue = parseFloat(input.value) || 0;
        });
    });
});
