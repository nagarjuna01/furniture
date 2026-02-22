/* ============================================================
   1. GLOBAL STATE & CONFIG
   ============================================================ */
window.productState = window.productState || { parts: [], hardware: {} };
window.currentPartState = null;
let MATERIALS = [], FILTERED_MATERIALS = [];

const FILTER_CONFIG = [
    { id: 'group',     key: 'material_grp',   label: 'material_grp_label' },
    { id: 'type',      key: 'material_type',  label: 'material_type_label' },
    { id: 'model',     key: 'material_model', label: 'material_model_label' },
    { id: 'brand',     key: 'brand',          label: 'brand_label' },
    { id: 'grain',     key: 'grain',          label: 'grain_label' },
    { id: 'thickness', key: 'thickness_mm',   label: 'thickness_mm' }
];

/* ============================================================
   2. SVG INTERACTIVE MAPPING & RESET
   ============================================================ */

window.toggleEdgeClick = function(side) {
    if (!window.currentPartState) return;
    const shape = document.getElementById('pt-shape-type')?.value || "RECT";
    // 1. CIRC logic: Any click toggles perimeter (mapped to 'top' intent)
    const targetSide = (shape === 'CIRC') ? 'top' : side;
    const intentKey = `edgeband_${targetSide}_intent`;

    // 3. Toggle the boolean directly on the part state
    window.currentPartState[intentKey] = !window.currentPartState[intentKey];
    window.updateSVGMapping();
    window.renderEdgebandCheckboxes(); 
};

window.resetBanding = function() {
    if (!window.currentPartState) return;
    ['top', 'right', 'bottom', 'left'].forEach(side => {
        window.currentPartState[`edgeband_${side}_intent`] = false;
    });
    window.updateSVGMapping();
    window.renderEdgebandCheckboxes();
};

window.updateSVGMapping = function() {
    const shape = document.getElementById('pt-shape-type')?.value || "RECT";
    
    const coords = {
        RECT: { 
            top: "M 15,15 L 85,15", right: "M 85,15 L 85,85", 
            bottom: "M 85,85 L 15,85", left: "M 15,85 L 15,15" 
        },
        CIRC: { 
            top: "M 50,15 A 35,35 0 1,1 49.9,15", right: "", bottom: "", left: "" 
        },
        L_SHAPE: { 
            top: "M 15,15 L 85,15", right: "M 85,15 L 85,45", 
            bottom: "M 85,45 L 45,45 L 45,85 L 15,85", left: "M 15,85 L 15,15" 
        }
    };

    const sCoords = coords[shape] || coords.RECT;

    ['top', 'right', 'bottom', 'left'].forEach(side => {
        const pathEl = document.getElementById(`path-${side}`);
        if (!pathEl) return;
        const dPath = sCoords[side] || "";
        pathEl.setAttribute('d', dPath);
        
        // CRITICAL ADDITION: Hide the path if it doesn't exist for this shape
        pathEl.style.opacity = dPath === "" ? "0" : "1";
        pathEl.style.pointerEvents = dPath === "" ? "none" : "auto";
        
        const isActive = window.currentPartState[`edgeband_${side}_intent`] === true;
        pathEl.setAttribute('stroke', isActive ? '#fd0dad' : '#dee2e6');
        pathEl.setAttribute('stroke-width', isActive ? '8' : '4');
        pathEl.style.transition = "stroke 0.2s, stroke-width 0.2s, opacity 0.2s";
    });
};

/* ============================================================
   3. MATERIAL & HARDWARE LOGIC
   ============================================================ */

window.applyAllFilters = function() {
    FILTERED_MATERIALS = MATERIALS.filter(m => {
        return FILTER_CONFIG.every(cfg => {
            const dropdown = document.getElementById(`filter-material-${cfg.id}`);
            const selectedValue = dropdown?.value;
            
            // If nothing is selected, let the material through
            if (!selectedValue) return true;

            // Compare selected text (e.g., "OSL") to the label property in the object
            // This ensures we match text-to-text, not text-to-ID
            return String(m[cfg.label]) === selectedValue;
        });
    });
    window.renderMaterialTable();
};
window.toggleWhitelist = function(id) {
    if (!window.currentPartState) return;
    if (!window.currentPartState.materials) {
        window.currentPartState.materials = { whitelist: [] };
    }
    if (!window.currentPartState.materials.whitelist) {
        window.currentPartState.materials.whitelist = [];
    }
    const list = window.currentPartState.materials.whitelist;
    const materialId = Number(id);
    const idx = list.indexOf(materialId);
    idx > -1 ? list.splice(idx, 1) : list.push(materialId);
    console.log(`[Engine] Whitelist updated:`, list);
    window.renderMaterialTable();
};
window.renderMaterialTable = function() {
    const tbody = document.getElementById("material-body");
    // Safety check for both state and the data source
    if (!tbody || !window.currentPartState || typeof FILTERED_MATERIALS === 'undefined') return;

    // Ensure whitelist exists so .includes doesn't fail
    const whitelist = window.currentPartState.materials?.whitelist || [];

    tbody.innerHTML = FILTERED_MATERIALS.map(m => {
        // FIX: Standardize to String or Number for the comparison
        const isWhitelisted = whitelist.some(id => String(id) === String(m.id));
        
        const boardThk = parseFloat(m.thickness_mm) || 0;

        
        

        return `
            <tr class="${isWhitelisted ? 'table-primary-subtle' : ''}">
                <td class="align-middle">
                    <div class="fw-bold">${m.name}</div>
                    <div class="small text-muted">
                        ${m.material_grp_label || ''} | ${m.brand_label || ''} | ${m.grain_label || 'No Grain'}
                    </div>
                </td>
                <td class="text-nowrap align-middle">
                    <div>${boardThk}mm</div>
                    
                </td>
                <td class="text-center align-middle">
                    <input type="checkbox" class="form-check-input" 
                        ${isWhitelisted ? 'checked' : ''} 
                        onclick="window.toggleWhitelist(${m.id})">
                </td>
            </tr>`;
    }).join("");
};

window.renderHardwareTable = function() {
    const tbody = document.getElementById("pt-hardware-body");
    const groupFilter = document.getElementById("hw-filter-group")?.value;
    const searchFilter = document.getElementById("hw-search")?.value.toLowerCase();
    
    if (!tbody || !window.currentPartState) return;
    
    // Ensure the hardware object exists
    if (!window.currentPartState.partHardware) {
        window.currentPartState.partHardware = {};
    }

    const filteredHw = (window.hardwareCache || []).filter(h => {
        const mGroup = !groupFilter || String(h.h_group_id || h.h_group) === groupFilter;
        const mSearch = !searchFilter || (h.h_name || h.name || "").toLowerCase().includes(searchFilter);
        return mGroup && mSearch;
    });

    tbody.innerHTML = filteredHw.map(h => {
        // Use the ID as a string key to be safe
        const hardwareId = String(h.id);
        const rowData = window.currentPartState.partHardware[hardwareId];
        const isChecked = !!rowData;

        return `
            <tr class="${isChecked ? 'table-success-subtle shadow-sm' : ''}">
                <td class="text-center align-middle">
                    <input type="checkbox" class="form-check-input" 
                        ${isChecked ? 'checked' : ''} 
                        onclick="window.toggleHardwareSelection('${hardwareId}')"> </td>
                <td class="align-middle">
                    <div class="fw-bold">${h.h_name || h.name}</div>
                    <small class="text-muted">${h.brand_name || ''}</small>
                </td>
                <td class="align-middle">
                    <input type="text" class="form-control form-control-sm font-monospace" 
                        placeholder="Qty"
                        value="${rowData?.qty || '1'}" 
                        ${!isChecked ? 'disabled' : ''} 
                        onchange="window.updateHwQty('${hardwareId}', this.value)"> </td>
                <td class="align-middle">
                    <input type="text" class="form-control form-control-sm font-monospace" 
                        placeholder="Condition"
                        value="${rowData?.cond || ''}" 
                        ${!isChecked ? 'disabled' : ''} 
                        onfocus="window.applySmartEngine(this)"
                        onblur="window.updateHwCond('${hardwareId}', this.value)"> </td>
            </tr>`;
    }).join("");
};
window.toggleHardwareSelection = function(id) {
    if (window.currentPartState.partHardware[id]) {
        delete window.currentPartState.partHardware[id];
    } else {
        window.currentPartState.partHardware[id] = { qty: '1', cond: '' };
    }
    window.renderHardwareTable(); 
};

window.updateHwQty = function(id, val) {
    if (window.currentPartState.partHardware[id]) {
        window.currentPartState.partHardware[id].qty = val;
    }
    
};

window.updateHwCond = function(id, val) {
    if (window.currentPartState.partHardware[id]) {
        window.currentPartState.partHardware[id].cond = val;
    }
    
};
/* ============================================================
   4. GEOMETRY & SHAPE UI HANDLING
   ============================================================ */
window.handleShapeChange = function() {
    const shapeEl = document.getElementById('pt-shape-type');
    if (!shapeEl) return;
    const shape = shapeEl.value;
    
    const extraParams = document.getElementById('pt-extra-params');
    const lblLen = document.getElementById('lbl-len');
    const lblWid = document.getElementById('lbl-wid');
    const lblP1 = document.getElementById('lbl-p1');
    const lblP2 = document.getElementById('lbl-p2');
    const colWid = document.getElementById('col-wid');
    // Reset UI State
    extraParams?.classList.add('d-none');
    colWid?.classList.remove('d-none');
    if(lblLen) lblLen.innerText = "Length Equation";
    if(lblWid) lblWid.innerText = "Width Equation";

    switch(shape) {
        case 'CIRC':
            if(lblLen) lblLen.innerText = "Diameter Eq.";
            colWid?.classList.add('d-none');
            break;
        case 'L_SHAPE':
            extraParams?.classList.remove('d-none');
            if(lblP1) lblP1.innerText = "Short Arm L";
            if(lblP2) lblP2.innerText = "Short Arm W";
            break;
        case 'CLIP':
            extraParams?.classList.remove('d-none');
            if(lblP1) lblP1.innerText = "Clip X";
            if(lblP2) lblP2.innerText = "Clip Y";
            break;
        case 'RADIUS_CNR':
            extraParams?.classList.remove('d-none');
            if(lblP1) lblP1.innerText = "Corner Radius";
            if(lblP2) lblP2.innerText = "Segments";
            break;
        }
    
    const summary = document.getElementById('edgeband-summary-text');
    if(summary) {
        summary.innerHTML = (shape === 'CIRC') 
            ? "<span class='text-primary fw-bold'>Note: Circular parts will use Perimeter banding logic.</span>" 
            : "Click diagram edges to toggle banding.";
    }
        window.updateSVGMapping();
};
/* ============================================================
   5. MODAL CONTROL & DASHBOARD
   ============================================================ */
window.renderMainPartTable = function() {
    const tbody = document.getElementById("part-templates-body");
    const countEl = document.getElementById("part-count");
    if (!tbody) return;

    if (countEl) countEl.innerText = window.productState.parts.length;

    if (window.productState.parts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-3 italic">No parts added yet. Enter a name above to start.</td></tr>`;
        return;
    }

    tbody.innerHTML = window.productState.parts.map(p => {
        // --- 1. FIXED: Define activeEdges by checking the _intent keys ---
        const sides = ['top', 'right', 'bottom', 'left'];
        const activeEdges = sides
            .filter(side => p[`edgeband_${side}_intent`] === true) 
            .map(side => side.charAt(0).toUpperCase()) // T, R, B, L
            .join(", ");

        const hwCount = p.partHardware ? Object.keys(p.partHardware).length : 0;
        const matCount = p.materials?.whitelist?.length || 0;
        
        const geometryDisplay = p.shape_type === 'CIRC'
            ? `Ø ${p.part_length_equation || p.geometry?.length_eq || ""}`
            : `${p.part_length_equation || p.geometry?.length_eq || ""} × ${p.part_width_equation || p.geometry?.width_eq || ""}`;

        return `
            <tr class="align-middle">
                <td class="fw-bold text-primary">${p.name}</td>
                <td class="font-monospace small">${geometryDisplay}</td>
                <td>
                    <small class="text-muted">${matCount} Materials Selected</small>
                </td>
                <td>
                    ${activeEdges ? `<span class="text-info fw-bold small">${activeEdges}</span>` : `<span class="text-muted small">None</span>`}
                </td>
                <td>
                    ${hwCount > 0 ? `<span class="text-dark small">${hwCount} Items</span>` : `<span class="text-muted small">0</span>`}
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary px-3" onclick="window.editPart('${p.name}')">
                        <i class="bi bi-pencil-square"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="window.deletePart(${p.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`;
    }).join("");
};

// Simple helper to delete a part if you need it
window.deletePart = (id) => {
    if(confirm("Remove this part template?")) { window.productState.parts = window.productState.parts.filter(p => p.id !== id); window.renderMainPartTable(); }
};

window.editPart = (name) => {
    const input = document.getElementById("part-name");
    if (input) { input.value = name; window.openPartModal(); }
};
window.openPartModal = function() {
    const nameInput = document.getElementById("part-name");
    const name = nameInput?.value.trim();
    if (!name) return alert("Enter Part Name");

    const existing = window.productState.parts.find(p => p.name.toLowerCase() === name.toLowerCase());
    
    if (existing) {
        // 1. CLONE
        window.currentPartState = JSON.parse(JSON.stringify(existing));
        delete window.currentPartState.edgebands;
        delete window.currentPartState.partHardware; // Cleanup UI noise while we're at it

    } else {
        // NEW PART: Clean by design
        window.currentPartState = {
            id: Date.now(), 
            name: name, 
            shape_type: "RECT",
            geometry: { length_eq: "", width_eq: "", p1_eq: "", p2_eq: "", qty_eq: "1" },
            materials: { whitelist: [] },
            partHardware: {},
            edgeband_top_intent: false,             edgeband_bottom_intent: false,
            edgeband_left_intent: false,             edgeband_right_intent: false
            
        };
    }
    const geo = window.currentPartState.geometry || {};
    document.getElementById("part-template-name").value = name;
    document.getElementById("pt-len-eq").value = window.currentPartState.part_length_equation || geo.length_eq || "";
    document.getElementById("pt-wid-eq").value = window.currentPartState.part_width_equation || geo.width_eq || "";
    document.getElementById("pt-p1-eq").value = window.currentPartState.param1_eq || geo.p1_eq || "";
    document.getElementById("pt-p2-eq").value = window.currentPartState.param2_eq || geo.p2_eq || "";
    document.getElementById("pt-qty-eq").value = window.currentPartState.part_qty_equation || geo.qty_eq || "1";
    document.getElementById("pt-shape-type").value = window.currentPartState.shape_type || "RECT";
    
    // Re-trigger Engine logic
    window.handleShapeChange();
    window.applyAllFilters();
    window.renderHardwareTable();
    window.renderEdgebandCheckboxes();

    const smartFieldMapping = [
    { id: "pt-len-eq", key: "part_length_equation" },
    { id: "pt-wid-eq", key: "part_width_equation" },
    { id: "pt-p1-eq",  key: "param1_eq" },
    { id: "pt-p2-eq",  key: "param2_eq" },
    { id: "pt-qty-eq", key: "part_qty_equation" }
];

smartFieldMapping.forEach(field => {
    const el = document.getElementById(field.id);
    if (!el) return;

    // 1. AT ENTRY (Focus): Wake up the Autocomplete
    window.applySmartEngine(el); 

    // 2. AT EXIT (Blur): The Forensic Check & Clean Save
    el.onblur = () => {
        window.validateAndCommit(el, (validatedValue) => {
            // Only hits this if the math is valid
            window.currentPartState[field.key] = validatedValue;
            console.log(`✅ Clean Entry: ${field.key} updated to [${validatedValue}]`);
        });
    };
});
    bootstrap.Modal.getOrCreateInstance(document.getElementById("partTemplateModal")).show();
};

window.validateAndCommit = function(el, callback) {
    const val = el.value.trim();
    // Simple Balance Check: Parentheses must match
    const isBalanced = (val.match(/\(/g) || []).length === (val.match(/\)/g) || []).length;
    
    if (!isBalanced) {
        el.classList.add('is-invalid');
        window.showToast("Unbalanced parentheses!", "error");
        return;
    }

    el.classList.remove('is-invalid');
    el.classList.add('is-valid');
    if (typeof callback === "function") callback(val);
};
window.savePartFromModal = function() {
    const p = window.currentPartState;
    if (!p) return;

    // 1. Final Field Capture (Existing logic is good)
    p.name = document.getElementById("part-template-name").value;
    p.shape_type = document.getElementById("pt-shape-type").value;
    p.part_length_equation = document.getElementById("pt-len-eq").value;
    p.part_width_equation = document.getElementById("pt-wid-eq").value;
    p.param1_eq = document.getElementById("pt-p1-eq").value || "0";
    p.param2_eq = document.getElementById("pt-p2-eq").value || "0";
    p.part_qty_equation = document.getElementById("pt-qty-eq").value || "1";


    // 4. Transformation: Hardware Rules (Keep this on 'p')
    p.hardware_rules = Object.entries(p.partHardware || {}).map(([hwId, data]) => ({
        hardware: parseInt(hwId),
        quantity_equation: data.qty || "1",
        condition_equation: data.cond || ""
    }));

    // ❌ REMOVE STEP 5 (THE SCRUB) FROM HERE
    // We don't want to delete keys while the user is still working in the browser.
    // Save the WHOLE object 'p' to the global state.
    
    // 6. Save to Global State (Use 'p', not 'finalObject')
    const idx = window.productState.parts.findIndex(item => item.id === p.id);
    if (idx !== -1) {
        window.productState.parts[idx] = JSON.parse(JSON.stringify(p));
    } else {
        window.productState.parts.push(JSON.parse(JSON.stringify(p)));
    }

    window.renderMainPartTable();
    window.showToast(`Part "${p.name}" saved.`, "success");
    bootstrap.Modal.getInstance(document.getElementById("partTemplateModal")).hide();
};
window.runProductionDryRun = function() {
    console.log("🛠️ Dry Run Initiated...");
    console.log("Current State:", window.productState);
    window.showToast("Dry Run logged to console (check F12)", "info");
};
window.renderEdgebandCheckboxes = function() {
    const container = document.getElementById("edgeband-checks-container");
    if (!container || !window.currentPartState) return;

    const sides = ['top', 'right', 'bottom', 'left'];
    const shape = document.getElementById('pt-shape-type')?.value || "RECT";

    container.innerHTML = sides.map(side => {
        // Hide irrelevant sides for CIRC
        if (shape === 'CIRC' && side !== 'top') return '';

        const isActive = window.currentPartState[`edgeband_${side}_intent`] === true;
        const label = shape === 'CIRC' ? 'Perimeter' : side.charAt(0).toUpperCase() + side.slice(1);

        return `
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="checkbox" id="check-${side}" 
                    ${isActive ? 'checked' : ''} 
                    onchange="window.handleCheckboxToggle('${side}', this.checked)">
                <label class="form-check-label" for="check-${side}">${label}</label>
            </div>
        `;
    }).join('');
};

window.handleCheckboxToggle = function(side, isChecked) {
    window.currentPartState[`edgeband_${side}_intent`] = isChecked;
    window.updateSVGMapping(); // Sync the SVG highlight!
};

/* ============================================================
   6. DATA INITIALIZATION
   ============================================================ */

async function initData() {
    try {
        const [mRes, hRes] = await Promise.all([
            fetch("/material/v1/woodens/").then(r => r.json()),
            fetch("/material/v1/hardware/").then(r => r.json())
            
        ]);

        MATERIALS = mRes.results || [];
        window.hardwareCache = hRes.results || [];
        

        syncFilterDropdowns();
        syncHardwareGroups();
        window.renderMainPartTable();
        
        console.log("✅ Global Engine Ready");
    } catch (e) { 
        console.error("❌ Global Engine Init Failed:", e); 
    }
}

function syncFilterDropdowns() {
    FILTER_CONFIG.forEach(cfg => {
        const el = document.getElementById(`filter-material-${cfg.id}`);
        if (!el) return;
        const unique = [...new Set(MATERIALS.map(m => m[cfg.label]))].filter(Boolean);
        el.innerHTML = '<option value="">All</option>' + unique.map(v => `<option value="${v}">${v}</option>`).join("");
        el.onchange = window.applyAllFilters;
    });
}

function syncHardwareGroups() {
    const el = document.getElementById("hw-filter-group");
    if (!el || !window.hardwareCache) return;
    
    // Most hardware APIs return the group name in 'h_group' 
    // If it returns an ID, you might need 'h_group_label' depending on your Django Serializer
    const groups = [...new Set(window.hardwareCache.map(h => h.h_group))].filter(Boolean);
    
    el.innerHTML = '<option value="">All Groups</option>' + 
        groups.map(g => `<option value="${g}">${g}</option>`).join("");
    
    el.onchange = window.renderHardwareTable;
}

// Global UI Listeners
document.getElementById("open-part-template-btn")?.addEventListener("click", window.openPartModal);
document.getElementById("save-part-template-btn")?.addEventListener("click", window.savePartFromModal);
document.getElementById("hw-search")?.addEventListener("input", window.renderHardwareTable);

window.validateAndCommit = function(el, successCallback) {
    const val = el.value.trim();
    
    // Check 1: Balanced Parentheses (The most common error)
    const openP = (val.match(/\(/g) || []).length;
    const closeP = (val.match(/\)/g) || []).length;
    
    if (openP !== closeP) {
        el.classList.add('is-invalid');
        el.classList.remove('is-valid');
        // Optional: show a small toast or tooltip
        return; 
    }

    // Success: Clean the UI and run the save
    el.classList.remove('is-invalid');
    el.classList.add('is-valid');
    successCallback(val);
};
initData();