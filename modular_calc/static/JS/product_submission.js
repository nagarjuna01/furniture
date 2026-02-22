/* ============================================================
   GLOBAL ENGINE: DRAFT MANAGER (ENTERPRISE LIB)
   ============================================================ */
const DraftManager = {
    STORAGE_KEY: 'modular_engine_enterprise_lib',

    getAll: function() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY) || "{}");
        } catch (e) {
            console.error("Storage Corrupted:", e);
            return {};
        }
    },

    // 1. SAVE: Capture Metadata, Dynamic Selects, State, and Hardware
    save: function() {
        const name = document.getElementById('product-name')?.value.trim();
        if (!name) return window.showToast("Product Name required for indexing.", "error");

        const drafts = this.getAll();

        drafts[name] = {
            meta: {
                name: name,
                updatedAt: new Date().toISOString(),
                category: document.getElementById('categoryselect')?.value,
                type: document.getElementById('type-select')?.value,
                model: document.getElementById('model-select')?.value,
                partCount: window.productState?.parts?.length || 0
            },
            payload: {
                validation_expression: document.getElementById('validation-expr')?.value,
                is_public: document.getElementById('is-public-check')?.checked,
                // The "Golden" State
                productState: window.productState,               // Parts & Parameters
                submissionState: window.productSubmissionState, // Product Hardware
            }
        };

        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(drafts));
        window.showToast(`Enterprise Draft "${name}" Synchronized.`, "success");
        this.renderManagerTable();
    },

    // 2. LOAD: Hydrate UI and Trigger Dependency Chains
    load: function(name) {
        const data = this.getAll()[name];
        if (!data) return;

        try {
            // --- Basic Fields ---
            document.getElementById('product-name').value = data.meta.name || "";
            document.getElementById('validation-expr').value = data.payload.validation_expression || "";
            document.getElementById('is-public-check').checked = !!data.payload.is_public;

            // --- Dropdown Hydration (with Event Cascading) ---
            const catEl = document.getElementById('categoryselect');
            if (catEl) {
                catEl.value = data.meta.category || "";
                catEl.dispatchEvent(new Event('change')); // Triggers 'Type' fetch
            }

            // Sequential timeouts to allow dynamic options to populate
            setTimeout(() => {
                const typeEl = document.getElementById('type-select');
                if (typeEl && data.meta.type) {
                    typeEl.value = data.meta.type;
                    typeEl.dispatchEvent(new Event('change')); // Triggers 'Model' fetch
                }
                setTimeout(() => {
                    const modelEl = document.getElementById('model-select');
                    if (modelEl && data.meta.model) modelEl.value = data.meta.model;
                }, 300);
            }, 300);

            // --- State Injection ---
            window.productState = data.payload.productState || { parts: [], parameters: [] };
            window.productSubmissionState = data.payload.submissionState || { product_hardware: [] };

            // --- UI Refresh ---
            if (window.renderMainPartTable) window.renderMainPartTable();
            if (window.renderGlobalHardwareTable) window.renderGlobalHardwareTable();
            if (window.renderParameterTable) window.renderParameterTable();

            bootstrap.Modal.getInstance(document.getElementById('draftManagerModal'))?.hide();
            window.showToast(`Draft "${name}" Restored.`, "info");

        } catch (e) {
            console.error("Hydration Error:", e);
            window.showToast("Load failed. Data structure might be incompatible.", "error");
        }
    },

    delete: function(name) {
        if (!confirm(`Delete "${name}"?`)) return;
        const drafts = this.getAll();
        delete drafts[name];
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(drafts));
        this.renderManagerTable();
    },

    renderManagerTable: function() {
        const container = document.getElementById('draft-manager-list');
        if (!container) return;

        const items = Object.values(this.getAll()).sort((a, b) => new Date(b.meta.updatedAt) - new Date(a.meta.updatedAt));
        
        container.innerHTML = items.map(d => `
            <tr class="align-middle">
                <td>
                    <div class="fw-bold">${d.meta.name}</div>
                    <small class="text-muted">${d.meta.category || 'Uncategorized'}</small>
                </td>
                <td><span class="badge bg-primary-subtle text-primary">${d.meta.partCount} Parts</span></td>
                <td><small class="text-muted">${new Date(d.meta.updatedAt).toLocaleDateString()}</small></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-primary px-3" onclick="DraftManager.load('${d.meta.name}')">Load</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="DraftManager.delete('${d.meta.name}')"><i class="bi bi-trash"></i></button>
                </td>
            </tr>`).join('') || '<tr><td colspan="4" class="text-center py-4">No drafts found.</td></tr>';
    }
};
/* ============================================================
   2. TIER 5 ENGINE: EVALUATION & DRY RUN PREVIEW
   ============================================================ */

window.runProductionDryRun = async function() {
    const container = document.getElementById('cutlist-container');
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-2"></div>
            <p class="text-muted small fw-bold">SOLVING CONSTRAINTS...</p>
        </div>`;

    const payload = {
        L: parseFloat(document.getElementById('test-product-length').value) || 1000,
        W: parseFloat(document.getElementById('test-product-width').value) || 600,
        H: parseFloat(document.getElementById('test-product-height').value) || 800,
        material_id: 1, 
        parameters: {},
        part_templates: (window.productState?.parts || []).map(p => ({
            name: p.name,
            part_length_equation: p.part_length_equation,
            part_width_equation: p.part_width_equation,
            part_qty_equation: p.part_qty_equation || "1"
        })),
        constraints: [document.getElementById('validation-expr').value].filter(x => x)
    };

    if (window.productState?.parameters) {
        window.productState.parameters.forEach(p => {
            payload.parameters[p.abbreviation || p.abbr] = p.default_value;
        });
    }

    try {
        const response = await fetch("/modularcalc/api/products/evaluate/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie('csrftoken') },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            renderEngineResults(result);
        } else {
            throw new Error(result.error || "Solving failed.");
        }
    } catch (err) {
        container.innerHTML = `<div class="alert alert-danger m-3 small">Engine Error: ${err.message}</div>`;
    }
};

function renderEngineResults(data) {
    const container = document.getElementById('cutlist-container');
    const { engine_output, ai_suggestions } = data;

    let html = `<div class="p-3">`;
    if (ai_suggestions?.length) {
        html += `<div class="alert alert-info small mb-2"><i class="bi bi-robot me-2"></i>${ai_suggestions[0]}</div>`;
    }

    html += `
        <table class="table table-sm x-small border">
            <thead class="table-light"><tr><th>Part</th><th>Dimensions</th><th>Qty</th></tr></thead>
            <tbody>
                ${engine_output.parts.map(p => `
                    <tr>
                        <td>${p.name}</td>
                        <td class="font-monospace">${p.evaluated_l} x ${p.evaluated_w}</td>
                        <td>${p.evaluated_qty}</td>
                    </tr>`).join('')}
            </tbody>
        </table></div>`;
    container.innerHTML = html;
}
/* ============================================================
   GLOBAL ENGINE: SUBMISSION & VALIDATION
   ============================================================ */

window.validateProductData = function() {
    const errors = [];
    const productName = document.getElementById('product-name')?.value.trim();
    const category = document.getElementById('categoryselect')?.value;
    const validationExpr = document.getElementById('validation-expr')?.value.trim();

    if (!productName) errors.push("Product Name is required.");
    
    if (!category || category === "") {
        errors.push("Product Category is required.");
        window.showToast("Please select a valid Category.", "error", "Category Error");
    }

    if (!validationExpr) {
        errors.push("Validation Expression is missing.");
        window.showToast("The Main Math (Validation Expression) is required.", "error", "Logic Error");
    }

    if (!window.productState?.parts || window.productState.parts.length === 0) {
        errors.push("At least one Part Template is required.");
        window.showToast("You must add at least one Part to the product.", "warning", "Incomplete Product");
    }

    return errors;
};
/** * TIER 5 UTILITIES 
 * Prevents engine crashes on empty strings or null inputs
 */

window.submitProduct = async function() {
    const btn = event?.currentTarget || document.getElementById('submit-product-btn');
    const originalText = btn.innerHTML;
    
    // 1. Validate before wasting a network call
    const errors = window.validateProductData();
    if (errors.length > 0) {
        alert("❌ Cannot Sync:\n" + errors.join("\n"));
        return;
    }
    
    const payload = {
        name: document.getElementById('product-name').value,
        category: parseInt(document.getElementById('categoryselect').value),
        type: parseInt(document.getElementById('type-select')?.value) || null,
        productmodel: parseInt(document.getElementById('model-select')?.value) || null,
        product_validation_expression: document.getElementById('validation-expr').value,
        parameters: (window.productSubmissionState.parameters || []).map(p => ({
        name: p.name,          // <--- THIS was missing from your last payload!
        abbreviation: p.abbreviation,  // Maps 'abbr' from UI to 'abbreviation' in Django
        datatype: "number",    // Required for the Global Engine logic
        default_value: p.default_value,
        description: p.description || ""
    })),
        // Map the parts to the structure the Serializer expects
        part_templates: window.productState.parts.map(p => ({
            name: p.name,
            shape_type: p.shape_type,
            part_length_equation: p.part_length_equation,
            part_width_equation: p.part_width_equation,
            part_qty_equation: p.part_qty_equation || "1",
            material_whitelist: (p.materials?.whitelist || []).map(matId => ({
                material: matId,
                selected_sides: ['top', 'bottom', 'left', 'right'].filter(side => p[`edgeband_${side}_intent`] === true)
            })),
            hardware_rules: Object.entries(p.partHardware || {}).map(([id, h]) => ({
                hardware: parseInt(id),
                quantity_equation: h.qty || "1",
                applicability_condition: h.cond || ""
            }))
        })),
                product_hardware: window.productSubmissionState?.product_hardware || []
    };
    
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Syncing to Factory...`;

    try {
        const response = await fetch("/modularcalc/api/products/create_full/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.CSRF_TOKEN // Ensure this is set in your base template
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
             window.showToast("🚀 Global Engine Sync Successful!", "success");
             console.log("Backend Response:", result);
            //  setTimeout(() => {
        //         window.location.href = "/modularcalc/mproduct/"; 
        //     }, 1000);
        // } else {
        //     // Log the specific DRF error to console for debugging
        //     console.error("Factory Error Details:", result);
        //     alert("Factory Error: " + (result.message || "Check console for field errors."));
        // }
        } else {
            console.error("Backend Validation Errors:", result);
            const msg = result.message || JSON.stringify(result);
            alert("⚠️ Factory Error:\n" + msg);
            window.showToast("Factory Sync Failed. Check console.", "error");
        }
    } catch (err) {
        console.error("Network Error:", err);
        alert("Critical: Could not connect to the Backend Factory.");
        window.showToast("Network Error during sync.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
};
