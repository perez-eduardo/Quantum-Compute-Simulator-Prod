/**
 * App name: Quantum Computing Simulation
 * File: base.js
 * Description: JavaScript for all pages.
 *              - Sidebar toggle with localStorage persistence
 *              - Database reset functionality
 *              - Docked progress bar with polling
 *              - Table scroll detection for gradient indicators
 */

/* ===========================================
   SIDEBAR TOGGLE
   =========================================== */
const SidebarToggle = {
    STORAGE_KEY: 'sidebarCollapsed',
    
    elements: {
        body: null,
        toggle: null
    },
    
    init: function() {
        this.elements.body = document.body;
        this.elements.toggle = document.getElementById('sidebarToggle');
        
        if (!this.elements.toggle) return;
        
        // Apply saved state immediately (transitions are blocked by CSS)
        this.applyState();
        
        // Re-enable transitions after state is applied
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.elements.body.classList.remove('no-transitions');
            });
        });
        
        // Bind click event
        this.elements.toggle.addEventListener('click', this.toggle.bind(this));
    },
    
    toggle: function() {
        const isCollapsed = this.elements.body.classList.toggle('sidebar-collapsed');
        this.saveState(isCollapsed);
    },
    
    saveState: function(isCollapsed) {
        try {
            localStorage.setItem(this.STORAGE_KEY, isCollapsed ? 'true' : 'false');
        } catch (e) {
            console.warn('Could not save sidebar state:', e);
        }
    },
    
    applyState: function() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            // Body starts with sidebar-collapsed class in HTML
            // Only remove it if user explicitly set it to expanded
            if (saved === 'false') {
                this.elements.body.classList.remove('sidebar-collapsed');
            }
        } catch (e) {
            console.warn('Could not restore sidebar state:', e);
        }
    }
};

/* ===========================================
   DATABASE RESET
   =========================================== */
const DatabaseReset = {
    init: function() {
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', this.handleReset.bind(this));
        }
    },
    
    handleReset: async function() {
        const confirmed = confirm(
            "Reset all data to defaults?\n\n" +
            "This will remove all custom entries."
        );
        
        if (!confirmed) return;
        
        try {
            const response = await fetch('/reset', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                window.location.reload();
            } else {
                alert(result.message || "Reset failed. Please try again.");
            }
        } catch (err) {
            console.error('Reset error:', err);
            alert("An error occurred while resetting data.");
        }
    }
};

/* ===========================================
   TABLE SCROLL DETECTION
   =========================================== */
const TableScrollHandler = {
    init: function() {
        const containers = document.querySelectorAll('.table-container');
        
        containers.forEach(container => {
            const wrapper = container.querySelector('.table-scroll-wrapper');
            if (!wrapper) return;
            
            // Check initial scroll state
            this.checkScroll(container, wrapper);
            
            // Listen for scroll events
            wrapper.addEventListener('scroll', () => {
                this.checkScroll(container, wrapper);
            });
            
            // Re-check on resize
            window.addEventListener('resize', () => {
                this.checkScroll(container, wrapper);
            });
        });
    },
    
    checkScroll: function(container, wrapper) {
        const hasHorizontalScroll = wrapper.scrollWidth > wrapper.clientWidth;
        const isScrolledToEnd = wrapper.scrollLeft + wrapper.clientWidth >= wrapper.scrollWidth - 5;
        
        if (hasHorizontalScroll) {
            container.classList.add('has-scroll');
        } else {
            container.classList.remove('has-scroll');
        }
        
        if (isScrolledToEnd) {
            container.classList.add('scrolled-end');
        } else {
            container.classList.remove('scrolled-end');
        }
    }
};

/* ===========================================
   DOCKED PROGRESS BAR
   =========================================== */
const DockedProgress = {
    elements: {
        // Docked progress bar
        container: null,
        spinner: null,
        status: null,
        barFill: null,
        count: null,
        percent: null,
        // Result modal
        modal: null,
        resultIcon: null,
        resultTitleText: null,
        resultMessage: null,
        resultDetails: null,
        viewBtn: null,
        retryBtn: null,
        closeBtn: null,
        closeX: null
    },

    // Polling state
    pollingInterval: null,
    pollingDelay: 300,
    maxRetries: 3,
    retryCount: 0,

    // Session storage key
    STORAGE_KEY: 'activeSimulation',

    // Current simulation info for retry
    currentSimInfo: null,

    /**
     * Initialize docked progress
     */
    init: function() {
        this.cacheElements();
        if (!this.elements.container) return;
        
        this.bindEvents();
        this.checkAndResumeSession();
    },

    /**
     * Cache DOM element references
     */
    cacheElements: function() {
        // Docked progress bar elements
        this.elements.container = document.getElementById('dockedProgress');
        if (!this.elements.container) return;
        
        this.elements.spinner = this.elements.container.querySelector('.docked-spinner');
        this.elements.status = document.getElementById('dockedStatus');
        this.elements.barFill = document.getElementById('dockedBarFill');
        this.elements.count = document.getElementById('dockedCount');
        this.elements.percent = document.getElementById('dockedPercent');
        
        // Result modal elements
        this.elements.modal = document.getElementById('simulationResultModal');
        if (this.elements.modal) {
            this.elements.resultIcon = document.getElementById('simResultIcon');
            this.elements.resultTitleText = document.getElementById('simResultTitleText');
            this.elements.resultMessage = document.getElementById('simResultMessage');
            this.elements.resultDetails = document.getElementById('simResultDetails');
            this.elements.viewBtn = document.getElementById('simResultViewBtn');
            this.elements.retryBtn = document.getElementById('simResultRetryBtn');
            this.elements.closeBtn = document.getElementById('simResultCloseBtn');
            this.elements.closeX = document.getElementById('simResultCloseX');
        }
    },

    /**
     * Bind event listeners
     */
    bindEvents: function() {
        if (this.elements.viewBtn) {
            this.elements.viewBtn.addEventListener('click', this.onViewResults.bind(this));
        }
        if (this.elements.retryBtn) {
            this.elements.retryBtn.addEventListener('click', this.onRetry.bind(this));
        }
        if (this.elements.closeBtn) {
            this.elements.closeBtn.addEventListener('click', this.onCloseModal.bind(this));
        }
        if (this.elements.closeX) {
            this.elements.closeX.addEventListener('click', this.onCloseModal.bind(this));
        }
        
        // Close modal on backdrop click
        if (this.elements.modal) {
            this.elements.modal.addEventListener('click', (e) => {
                if (e.target === this.elements.modal) {
                    this.onCloseModal();
                }
            });
        }
    },

    /* ===========================================
       SESSION STORAGE MANAGEMENT
       =========================================== */
    getSession: function() {
        const data = sessionStorage.getItem(this.STORAGE_KEY);
        if (!data) return null;
        try {
            return JSON.parse(data);
        } catch (e) {
            return null;
        }
    },

    setSession: function(simID, total, stateText, gateText) {
        const session = {
            simID: simID,
            total: total,
            stateText: stateText,
            gateText: gateText,
            status: 'processing',
            startedAt: Date.now()
        };
        sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
    },

    updateSessionStatus: function(status) {
        const session = this.getSession();
        if (session) {
            session.status = status;
            sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
        }
    },

    clearSession: function() {
        sessionStorage.removeItem(this.STORAGE_KEY);
    },

    hasActiveSimulation: function() {
        const session = this.getSession();
        return session && session.status === 'processing';
    },

    checkAndResumeSession: function() {
        const session = this.getSession();
        if (!session) return;

        this.currentSimInfo = {
            stateText: session.stateText,
            gateText: session.gateText
        };

        if (session.status === 'processing') {
            this.showProgressBar(session.total, session.stateText, session.gateText);
            this.startPolling(session.simID, session.total);
        } else if (session.status === 'complete') {
            this.showCompleteModal(session.simID, session.total);
        } else if (session.status === 'error') {
            this.showErrorModal('Previous simulation encountered an error');
        }
    },

    /* ===========================================
       PROGRESS BAR UI
       =========================================== */
    showProgressBar: function(total, stateText, gateText) {
        if (!this.elements.container) return;
        
        this.elements.status.textContent = `Generating shots...`;
        this.elements.barFill.style.width = '0%';
        this.elements.count.textContent = `0/${total}`;
        this.elements.percent.textContent = '(0%)';
        
        this.elements.container.classList.remove('hidden');
    },

    hideProgressBar: function() {
        if (this.elements.container) {
            this.elements.container.classList.add('hidden');
        }
        this.stopPolling();
    },

    updateProgress: function(current, total, pct) {
        if (this.elements.barFill) {
            this.elements.barFill.style.width = pct + '%';
            this.elements.count.textContent = `${current}/${total}`;
            this.elements.percent.textContent = `(${pct}%)`;
        }
    },

    /* ===========================================
       RESULT MODAL UI
       =========================================== */
    showCompleteModal: function(simID, total) {
        this.hideProgressBar();
        
        if (!this.elements.modal) return;
        
        this.elements.resultIcon.className = 'fas fa-check-circle';
        this.elements.resultTitleText.textContent = 'Simulation Complete!';
        this.elements.resultMessage.textContent = 'Your simulation has finished successfully.';
        this.elements.resultDetails.textContent = `${total} shots generated`;
        
        this.elements.viewBtn.classList.remove('hidden');
        this.elements.viewBtn.dataset.simId = simID;
        this.elements.retryBtn.classList.add('hidden');
        
        this.elements.modal.showModal();
        this.updateSessionStatus('complete');
    },

    showErrorModal: function(message) {
        this.hideProgressBar();
        
        if (!this.elements.modal) return;
        
        this.elements.resultIcon.className = 'fas fa-exclamation-triangle';
        this.elements.resultTitleText.textContent = 'Simulation Error';
        this.elements.resultMessage.textContent = message;
        this.elements.resultDetails.textContent = '';
        
        this.elements.viewBtn.classList.add('hidden');
        this.elements.retryBtn.classList.remove('hidden');
        
        this.elements.modal.showModal();
        this.updateSessionStatus('error');
    },

    closeModal: function() {
        if (this.elements.modal) {
            this.elements.modal.close();
        }
    },

    /* ===========================================
       POLLING
       =========================================== */
    startPolling: function(simID, total) {
        this.stopPolling();
        this.retryCount = 0;

        const poll = async () => {
            try {
                const response = await fetch(`/simulations/${simID}/progress`);
                
                if (response.status === 404) {
                    console.warn('Progress not found, simulation may have completed');
                    this.showCompleteModal(simID, total);
                    this.stopPolling();
                    return;
                }
                
                const data = await response.json();
                
                this.updateProgress(data.current, data.total, data.pct);
                this.retryCount = 0;
                
                if (data.status === 'complete') {
                    await fetch(`/simulations/${simID}/progress`, { method: 'DELETE' });
                    this.showCompleteModal(simID, data.total);
                    this.stopPolling();
                    return;
                }
                
                if (data.status === 'error') {
                    this.showErrorModal(data.message || 'An error occurred');
                    this.stopPolling();
                    return;
                }
                
                this.pollingInterval = setTimeout(poll, this.pollingDelay);
                
            } catch (err) {
                console.error('Polling error:', err);
                this.retryCount++;
                
                if (this.retryCount >= this.maxRetries) {
                    this.showErrorModal('Connection lost. Please check your network.');
                    this.stopPolling();
                    return;
                }
                
                this.pollingInterval = setTimeout(poll, this.pollingDelay * (this.retryCount + 1));
            }
        };
        
        poll();
    },

    stopPolling: function() {
        if (this.pollingInterval) {
            clearTimeout(this.pollingInterval);
            this.pollingInterval = null;
        }
    },

    /* ===========================================
       EVENT HANDLERS
       =========================================== */
    onCloseModal: function() {
        this.closeModal();
        this.clearSession();
    },

    onViewResults: function() {
        const simID = this.elements.viewBtn.dataset.simId;
        this.closeModal();
        this.clearSession();
        window.location.href = `/shots/${simID}`;
    },

    onRetry: function() {
        this.closeModal();
        this.clearSession();
        if (!window.location.pathname.includes('/simulations')) {
            window.location.href = '/simulations';
        }
    },

    /* ===========================================
       PUBLIC API (for simulations_page.js)
       =========================================== */
    startSimulation: function(simID, total, stateText, gateText) {
        this.currentSimInfo = { stateText, gateText };
        this.setSession(simID, total, stateText, gateText);
        this.showProgressBar(total, stateText, gateText);
        this.startPolling(simID, total);
    }
};

// Alias for backward compatibility
const FloatingProgress = DockedProgress;

/* ===========================================
   INITIALIZATION
   =========================================== */
document.addEventListener('DOMContentLoaded', function() {
    SidebarToggle.init();
    DatabaseReset.init();
    TableScrollHandler.init();
    DockedProgress.init();
});

// Expose globally for other scripts
window.FloatingProgress = FloatingProgress;
window.DockedProgress = DockedProgress;
