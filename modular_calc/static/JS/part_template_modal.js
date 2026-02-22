const SHAPE_INPUTS = {
    'RECT': '<div class="col-12 text-muted small">Standard rectangular panel.</div>',
    
    'L': `
        <div class="col-md-6"><label class="small fw-bold">Leg A Width</label><input type="number" id="pt-p-lega" class="form-control form-control-sm" placeholder="mm"></div>
        <div class="col-md-6"><label class="small fw-bold">Leg B Width</label><input type="number" id="pt-p-legb" class="form-control form-control-sm" placeholder="mm"></div>`,
    
    'CLIP': `
        <div class="col-md-6"><label class="small fw-bold">Clip X (Length-wise)</label><input type="number" id="pt-p-clipx" class="form-control form-control-sm"></div>
        <div class="col-md-6"><label class="small fw-bold">Clip Y (Width-wise)</label><input type="number" id="pt-p-clipy" class="form-control form-control-sm"></div>`,
    
    'NOTCH': `
        <div class="col-md-6"><label class="small fw-bold">Notch Width</label><input type="number" id="pt-p-nw" class="form-control form-control-sm"></div>
        <div class="col-md-6"><label class="small fw-bold">Notch Depth</label><input type="number" id="pt-p-nd" class="form-control form-control-sm"></div>
        <div class="col-md-12 mt-2"><label class="small fw-bold">Position</label><select class="form-select form-select-sm"><option>Top-Left</option><option>Top-Right</option></select></div>`,
    
    'U': `
        <div class="col-md-4"><label class="small fw-bold">Base Width</label><input type="number" id="pt-p-ubase" class="form-control form-control-sm"></div>
        <div class="col-md-4"><label class="small fw-bold">Left Leg</label><input type="number" id="pt-p-ulef" class="form-control form-control-sm"></div>
        <div class="col-md-4"><label class="small fw-bold">Right Leg</label><input type="number" id="pt-p-urig" class="form-control form-control-sm"></div>`,
    
    'CIRC': `
        <div class="col-md-12"><label class="small fw-bold">Diameter</label><input type="number" id="pt-p-diam" class="form-control form-control-sm" placeholder="Uses Length Eq as default"></div>`,
        
    'RADIUS_CNR': `
        <div class="col-md-6"><label class="small fw-bold">Radius</label><input type="number" id="pt-p-rad" class="form-control form-control-sm"></div>
        <div class="col-md-6"><label class="small fw-bold">Corners</label>
            <div class="small">
                <input type="checkbox"> TL <input type="checkbox"> TR <br>
                <input type="checkbox"> BL <input type="checkbox"> BR
            </div>
        </div>`
};

function updatePreview(shapeType) {
    const preview = document.getElementById('pt-geometry-preview-canvas');
    // Example for a Clipped Corner (Clipped top-right)
    if(shapeType === 'CLIP') {
        preview.style.clipPath = "polygon(0% 0%, 80% 0%, 100% 20%, 100% 100%, 0% 100%)";
        preview.style.background = "#0d6efd";
    } else if(shapeType === 'CIRC') {
        preview.style.borderRadius = "50%";
    } else {
        preview.style.clipPath = "none";
        preview.style.borderRadius = "0";
    }
}
function blankPartDraft() {
    return {
        id: null,
        name: "",
        logic: {material_expression: "",edgeband_bandwidth: 5,rounding_precision: 0.1 },
        geometry: { length_eq: "", width_eq: "", qty_eq: "1", svg: "" },
        materials: { whitelist: []},
        edgebands: { top: false, right: false, bottom: false, left: false },
        hardware: []
    };
}
/* ============================================================
   PART TEMPLATE MODAL JS – SYNCHRONIZED VERSION
   ============================================================ */
window.productState = window.productState || { parts: [], hardware: {} };
window.currentPartState = null;
let MATERIALS = [], EDGEBANDS = [], hardwareCache = [], hardwareGroupsCache = [];
/* ----------------- 1. OPEN MODAL ----------------- */
document.getElementById("open-part-template-btn")?.addEventListener("click", () => {
    const nameInput = document.getElementById("part-name");
    const name = nameInput.value.trim();
    if (!name) return alert("Please enter a Part Name first.");

    const existing = window.productState.parts.find(p => p.name.toLowerCase() === name.toLowerCase());

    if (existing) {
        window.currentPartState = JSON.parse(JSON.stringify(existing));
    } else {
        window.currentPartState = blankPartDraft();
        window.currentPartState.name = name;
        window.currentPartState.id = Date.now();
    }

    fillPartModal(window.currentPartState);
    
    const modalEl = document.getElementById("partTemplateModal");
    if (modalEl) bootstrap.Modal.getOrCreateInstance(modalEl).show();
});

/* ----------------- HELPER: FILL SELECTS ----------------- */
function fillSelect(select, items, idKey, labelKey) {
    if (!select) return;
    const current = select.value;
    select.innerHTML = `<option value="">All</option>`;
    
    // We use a Set to track labels we've already added to avoid duplicates
    const seenLabels = new Set();
    
    items.forEach(item => {
        const id = item[idKey];
        const label = item[labelKey] || id;
        
        // Skip if label is empty or we've already added this name/model
        if (!label || seenLabels.has(label)) return;
        
        seenLabels.add(label);
        select.appendChild(new Option(label, id));
    });
    
    if ([...select.options].some(o => o.value === current)) select.value = current;
}
/* ----------------- 2. FILL MODAL UI ----------------- */
function fillPartModal(p) {
    const nameDisplay = document.getElementById("modal-part-name");
    if (nameDisplay) nameDisplay.innerText = p.name || "Unnamed Part";

    // 1. Geometry Fields
    document.getElementById("pt-len-eq").value = p.geometry?.length_eq || "";
    document.getElementById("pt-wid-eq").value = p.geometry?.width_eq || "";
    document.getElementById("pt-qty-eq").value = p.geometry?.qty_eq || "1";
    document.getElementById("pt-svg").value = p.geometry?.svg || "";

    // 2. Materials Logic
    // This will refresh the material table based on the state in p.materials
    applyMaterialFilters(); 
   
    renderEdgebandTab();

    // 4. Hardware Logic
    // Ensure hardware exists as an array
    // 1. Hardware Hydration
    if (!p.hardware) p.hardware = [];
    window.currentPartState = p; // Ensure this is set before rendering

    // 2. Initialize Hardware Filters (if not already done)
    initHardwareFilters();

    // 3. FORCE RENDER (This fixes the "empty on load" glitch)
    renderHardwareTable();
    validatePartForm();
}

/* ----------------- 3. SAVE LOGIC ----------------- */
document.getElementById("save-part-template-btn")?.addEventListener("click", function() {
    if (!window.currentPartState) return;
    const part = window.currentPartState;

    if (document.activeElement) document.activeElement.blur();

    // --- CRITICAL FIX: RE-CAPTURE THE NAME ---
    // Make sure 'part-template-name' matches the ID of the name input inside your modal
    const modalNameInput = document.getElementById("part-template-name");
    if (modalNameInput && modalNameInput.value.trim() !== "") {
        part.name = modalNameInput.value.trim();
    }
    // -----------------------------------------

    // Capture Geometry
    part.geometry = {
        length_eq: document.getElementById("pt-len-eq").value.trim(),
        width_eq: document.getElementById("pt-wid-eq").value.trim(),
        qty_eq: document.getElementById("pt-qty-eq").value.trim() || "1",
        svg: document.getElementById("pt-svg").value.trim()
    };

    // Capture Edgebands (Keep your existing logic)
    part.edgebands = part.edgebands || {}; 
    document.querySelectorAll(".eb-select").forEach(sel => {
        const side = sel.dataset.side;
        if(side) part.edgebands[side] = sel.value ? { default: Number(sel.value) } : null;
    });

    // Update Global productState
    const idx = window.productState.parts.findIndex(p => p.id === part.id);
    if (idx !== -1) {
        window.productState.parts[idx] = JSON.parse(JSON.stringify(part)); // Deep copy to prevent reference issues
    } else {
        window.productState.parts.push(JSON.parse(JSON.stringify(part)));
    }

    renderPartRow(part);

    const modalEl = document.getElementById("partTemplateModal");
    bootstrap.Modal.getInstance(modalEl).hide();
    
    // Clear the OUTSIDE input
    const mainNameInput = document.getElementById("part-name");
    if(mainNameInput) mainNameInput.value = "";
    
    window.currentPartState = null;
});

/* ----------------- 5. DELETE FROM TABLE ----------------- */
document.getElementById("part-templates-body")?.addEventListener("click", (e) => {
    if (e.target.closest(".remove-part")) {
        const tr = e.target.closest("tr");
        const id = Number(tr.dataset.id);
        if (confirm("Remove this part template?")) {
            window.productState.parts = window.productState.parts.filter(p => p.id !== id);
            tr.remove();
        }
    }
});


/* ----------------- DATA FETCHING (FIXED) ----------------- */
/* ----------------- DATA FETCHING (FIXED) ----------------- */
async function initData() {
    try {
        // MATCHING: 4 fetches in the array, 4 variables in the brackets
        const [mRes, eRes, hRes, hgRes] = await Promise.all([
            fetch("/material/v1/woodens/"),
            fetch("/material/v1/edgebands/"),
            fetch("/material/v1/hardware/"),
            fetch("/material/v1/hardware-groups/")
        ]);
        
        // Convert all to JSON
        const mData = await mRes.json();
        const eData = await eRes.json();
        const hData = await hRes.json();
        const hgData = await hgRes.json();

        MATERIALS = mData.results || [];
        EDGEBANDS = eData.results || [];
        window.hardwareCache = hData.results || [];
        window.hardwareGroupsCache = hgData.results || [];
        
        FILTERED_MATERIALS = [...MATERIALS];
        
        // Initialize UI components
        initMaterialFilters();
        initHardwareFilters(); // Call this here to prepare the dropdown
        renderMaterialTable(); 
        renderHardwareTable();
        console.log("✅ All System Data Loaded Successfully");
    } catch (e) {
        console.error("❌ Data Fetch Failed:", e);
    }
}


/* ============================================================
   INTEGRATED MATERIAL FILTERS & WHITELIST
   ============================================================ */

function initMaterialFilters() {
    const filters = {
        group: document.getElementById("filter-material-group"),
        type: document.getElementById("filter-material-type"),
        model: document.getElementById("filter-material-model"),
        brand: document.getElementById("filter-material-brand"),
        thickness: document.getElementById("filter-material-thickness"),
        grain: document.getElementById("filter-material-grain")
    };

    fillSelect(filters.group, MATERIALS, "material_grp", "material_grp_label");
    fillSelect(filters.type, MATERIALS, "material_type", "material_type_label");
    fillSelect(filters.brand, MATERIALS, "brand", "brand_label");
    fillSelect(filters.model, MATERIALS, "material_model", "material_model_label");
    fillSelect(filters.grain, MATERIALS, "grain", "grain_label");
    fillSelect(filters.thickness, 
        MATERIALS.map(m => ({ id: m.thickness_mm, label: `${m.thickness_mm}mm` })), 
        "id", "label");

    Object.values(filters).forEach(el => {
        if(el) el.addEventListener("change", applyMaterialFilters);
    });
}

function applyMaterialFilters() {
    // Get label instead of ID for deduplicated filtering
    const gSel = document.getElementById("filter-material-group");
    const tSel = document.getElementById("filter-material-type");
    const mSel = document.getElementById("filter-material-model");
    const bSel = document.getElementById("filter-material-brand");
    const grSel = document.getElementById("filter-material-grain");
    const th = document.getElementById("filter-material-thickness")?.value;

    const gLabel = gSel?.options[gSel.selectedIndex]?.text;
    const tLabel = tSel?.options[tSel.selectedIndex]?.text;
    const mLabel = mSel?.options[mSel.selectedIndex]?.text;
    const bLabel = bSel?.options[bSel.selectedIndex]?.text;
    const grLabel = grSel?.options[grSel.selectedIndex]?.text;

    FILTERED_MATERIALS = MATERIALS.filter(x => {
        if (gLabel && gLabel !== "All" && x.material_grp_label !== gLabel) return false;
        if (tLabel && tLabel !== "All" && x.material_type_label !== tLabel) return false;
        if (mLabel && mLabel !== "All" && x.material_model_label !== mLabel) return false;
        if (bLabel && bLabel !== "All" && x.brand_label !== bLabel) return false;
        if (grLabel && grLabel !== "All" && x.grain_label !== grLabel) return false;
        if (th && String(x.thickness_mm) !== th) return false;
        return true;
    });

    renderMaterialTable();
    if (typeof validatePartForm === "function") validatePartForm();
}

function renderMaterialTable() {
    const tbody = document.getElementById("material-body");
    if (!tbody || !window.currentPartState) return;

    const matState = window.currentPartState.materials;
    const logicExpr = window.currentPartState.logic?.material_expression || "";

    const whitelistedItems = MATERIALS.filter(m => matState.whitelist.includes(m.id));
    const ceilingThickness = whitelistedItems.length > 0 
        ? Math.max(...whitelistedItems.map(m => m.thickness_mm)) 
        : null;

    tbody.innerHTML = FILTERED_MATERIALS.map(m => {
        const isWhitelisted = matState.whitelist.includes(m.id);
        const isCeiling = ceilingThickness && m.thickness_mm === ceilingThickness;
        
        // Python will use this grain_label later to lock/unlock rotation in nesting
        const grainStatus = m.grain_label || "No Grain";

        const metaParts = [
            m.material_grp_label,
            m.material_type_label,
            m.material_model_label,
            m.brand_label,
            grainStatus // RE-INCLUDED
        ].filter(p => p && String(p).trim() !== "");
        
        const subInfo = metaParts.join(" || ");

        return `
            <tr class="${isWhitelisted ? 'table-primary-subtle' : ''}">
                <td>
                    <div class="fw-bold" style="font-size: 0.9rem;">
                        ${m.name} 
                        <span class="badge ${m.grain_label ? 'bg-warning text-dark' : 'bg-light text-muted'} ms-2" style="font-size:0.6rem;">
                            ${grainStatus}
                        </span>
                    </div>
                    <small class="text-muted" style="font-size: 0.75rem;">${subInfo}</small>
                </td>
                <td class="text-nowrap fw-bold">${m.thickness_mm} mm</td>
                <td class="text-center">
                    <input type="checkbox" class="form-check-input" 
                        ${isWhitelisted ? 'checked' : ''} 
                        onclick="toggleMaterialWhitelist(${m.id})">
                </td>
            </tr>
        `;
    }).join("");
    
    updateMaterialPreview();
}

window.toggleMaterialWhitelist = function(id) {
    const matState = window.currentPartState.materials;
    const idx = matState.whitelist.indexOf(id);
    
    // 1. Simple Toggle
    if (idx > -1) {
        matState.whitelist.splice(idx, 1);
    } else {
        matState.whitelist.push(id);
    }
    renderMaterialTable();
    
    
    if (typeof validatePartForm === "function") validatePartForm();
};
function updateMaterialPreview() {
    const mat = window.currentPartState.materials;
    const whitelistEl = document.getElementById("selected-materials");

    // We no longer look for 'ceiling-material-display' because we removed it from HTML
    
    // 1. Render ONLY the Whitelist Badges
    if (whitelistEl) {
        if (mat.whitelist.length > 0) {
            whitelistEl.innerHTML = mat.whitelist.map(id => {
                const m = MATERIALS.find(x => x.id === id);
                // Including thickness in the badge for clarity since the 'Default' column is gone
                return m ? `<span class="badge bg-primary me-1">${m.name} (${m.thickness_mm}mm)</span>` : '';
            }).join("");
        } else {
            whitelistEl.innerHTML = `<span class="text-muted italic small">No materials whitelisted</span>`;
        }
    }
}
window.validatePartForm = function() {
    const p = window.currentPartState;
    const submitBtn = document.getElementById("save-part-template-btn");
    if (!submitBtn || !p) return;

    const hasLen = document.getElementById("pt-len-eq")?.value.trim() !== "";
    const hasWid = document.getElementById("pt-wid-eq")?.value.trim() !== "";
    const hasMaterial = p.materials.whitelist.length > 0;

    const isValid = hasLen && hasWid && hasMaterial;
    submitBtn.disabled = !isValid;
    submitBtn.classList.toggle("btn-primary", isValid);
    submitBtn.classList.toggle("btn-secondary", !isValid);
};

/* ----------------- 3. EDGEBAND LOGIC (DECOUPLED) ----------------- */
function renderEdgebandTab() {
    const container = document.getElementById("edgeband-selection-container");
    if (!container || !window.currentPartState) return;

    const ebState = window.currentPartState.edgebands;

    container.innerHTML = SIDES.map(side => {
        const isApplied = ebState[side] === true;
        return `
            <div class="col-md-6 mb-3">
                <div class="card border ${isApplied ? 'border-primary bg-primary-subtle' : 'border-light-subtle'}">
                    <div class="card-body d-flex justify-content-between align-items-center py-2 px-3">
                        <div>
                            <span class="fw-bold small text-uppercase">${side}</span>
                            <div class="text-muted" style="font-size: 0.7rem;">
                                ${isApplied ? 'Banding Required' : 'Raw Edge'}
                            </div>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" 
                                   style="transform: scale(1.2);"
                                   ${isApplied ? 'checked' : ''} 
                                   onchange="toggleSideBanding('${side}')">
                        </div>
                    </div>
                </div>
            </div>`;
    }).join("");

    updateEdgeSummary();
}
window.toggleSideBanding = function(side) {
    window.currentPartState.edgebands[side] = !window.currentPartState.edgebands[side];
    renderEdgebandTab();
    validatePartForm();
};

// 4. Visual Summary
function updateEdgeSummary() {
    const sides = window.currentPartState.edgebands;
    const active = Object.keys(sides).filter(s => sides[s]);
    const el = document.getElementById("edgeband-summary-text");
    if (active.length > 0) {
        el.innerHTML = `Banding will be applied to: <strong>${active.join(", ").toUpperCase()}</strong>`;
    } else {
        el.innerHTML = "Raw edges on all sides (No banding).";
    }
}
function renderHardwareTable() {
    const tbody = document.getElementById("pt-hardware-body");
    if (!tbody || !window.currentPartState) return;

    const data = window.hardwareCache || []; 
    const groupFilter = document.getElementById("hw-filter-group")?.value || "";
    const searchFilter = (document.getElementById("hw-search")?.value || "").toLowerCase();
    
    // Ensure the part state has a hardware array
    if (!window.currentPartState.hardware) window.currentPartState.hardware = [];
    const selectedHw = window.currentPartState.hardware;

    const filtered = data.filter(h => {
        // String match against the Group Name
        const matchesGroup = !groupFilter || h.h_group_label === groupFilter;
        // Search against the Hardware Name
        const matchesSearch = !searchFilter || (h.h_name && h.h_name.toLowerCase().includes(searchFilter));
        return matchesGroup && matchesSearch;
    });

    if (filtered.length === 0 && data.length > 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No matching hardware found.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(h => {
        const rowData = selectedHw.find(item => Number(item.id) === Number(h.id));
        const isChecked = !!rowData;

        return `
            <tr class="${isChecked ? 'table-primary-subtle' : ''}">
                <td class="text-center">
                    <input type="checkbox" class="form-check-input" 
                        ${isChecked ? 'checked' : ''} 
                        onclick="toggleHardwareSelection(${h.id})">
                </td>
                <td>
                    <div class="fw-bold small">${h.h_name}</div>
                    <small class="text-muted">${h.h_group_label || 'General'} | ${h.billing_unit_code || 'pcs'}</small>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm text-center" 
                        value="${rowData ? rowData.qty : '1'}" 
                        ${!isChecked ? 'disabled' : ''}
                        onchange="updateHardwareData(${h.id}, 'qty', this.value)">
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm" 
                        placeholder="Condition" 
                        value="${rowData ? rowData.condition : ''}" 
                        ${!isChecked ? 'disabled' : ''}
                        onchange="updateHardwareData(${h.id}, 'condition', this.value)">
                </td>
            </tr>`;
    }).join("");
}

window.toggleHardwareSelection = function(id) {
    // Safety check: ensure hardware array exists
    if (!window.currentPartState.hardware) {
        window.currentPartState.hardware = [];
    }
    
    const hwList = window.currentPartState.hardware;
    const index = hwList.findIndex(item => Number(item.id) === Number(id));
    
    if (index > -1) {
        hwList.splice(index, 1);
    } else {
        hwList.push({ id: id, qty: "1", condition: "" });
    }
    renderHardwareTable();
};
window.updateHardwareData = function(id, field, value) {
    const item = window.currentPartState.hardware.find(h => h.id === id);
    if (item) {
        item[field] = value;
    }
};

function initHardwareFilters() {
    const sel = document.getElementById("hw-filter-group");
    if (!sel) return;
    
    const groups = window.hardwareGroupsCache || [];
    
    sel.innerHTML = '<option value="">All Groups</option>';
    groups.forEach(g => {
        // Value: g.name (string), Text: g.name
        // This allows (h.h_group_label === groupFilter) to be TRUE
        sel.appendChild(new Option(g.name, g.name)); 
    });

    // Refresh table when dropdown changes
    sel.onchange = () => renderHardwareTable();
}


async function loadHardwareFromAPI() {
    try {
        const res = await fetch("/material/v1/hardware/");
        const data = await res.json();
        
        // Store globally
        window.hardwareCache = data.results || [];
        
        console.log("✅ Hardware Cache Initialized");
    } catch (err) {
        console.error("❌ Hardware Fetch Failed", err);
    }
}

/* ============================================================
   UPDATED DRAFT SYSTEM
============================================================ */

const DRAFT_KEY = "modularProductDrafts";

// 1. REPLACING YOUR "save-draft-btn"
document.getElementById("save-draft-btn")?.addEventListener("click", () => {
    const nameField = document.getElementById("product-name");
    const draftTitle = prompt("Enter a name for this draft:", nameField.value || "Untitled Draft");
    
    if (!draftTitle) return; 

    // Build the payload using the same logic as the final submit
    const draft = {
        draftId: Date.now(),
        draftTitle: draftTitle,
        timestamp: new Date().toLocaleString(),
        payload: {
            name: nameField.value.trim(),
            category: document.getElementById("categoryselect").value,
            type: document.getElementById("type-select").value,
            productmodel: document.getElementById("model-select").value,
            parameters: collectParameters(),
            // CRITICAL: Use the standardized payload builder
            part_templates: buildPartTemplatesPayload(productState.parts), 
            hardware_rules: Object.entries(window.selected.productHardware || {}).map(([id, obj]) => ({
                hardware: Number(id),
                quantity_equation: obj.qty || "1",
                applicability_condition: obj.cond || ""
            })),
            validation_expr: document.getElementById("validation-expr")?.value || ""
        }
    };

    const allDrafts = JSON.parse(localStorage.getItem(DRAFT_KEY) || "[]");
    allDrafts.push(draft);
    localStorage.setItem(DRAFT_KEY, JSON.stringify(allDrafts));
    
    alert(`Draft "${draftTitle}" saved to local storage.`);
});

// 2. THE NEW "load-draft-btn" (WAS PREVIOUSLY A SHOWPIECE)
document.getElementById("load-draft-btn")?.addEventListener("click", () => {
    const allDrafts = JSON.parse(localStorage.getItem(DRAFT_KEY) || "[]");
    
    if (allDrafts.length === 0) {
        alert("No drafts found.");
        return;
    }

    let menu = "Select a draft (Enter number):\n";
    allDrafts.forEach((d, i) => menu += `${i + 1}. ${d.draftTitle} (${d.timestamp})\n`);

    const choice = prompt(menu);
    const selected = allDrafts[parseInt(choice) - 1];

    if (selected) {
        const data = selected.payload;

        // Reset UI before loading
        window.productState.parts = [];
        document.getElementById("part-templates-body").innerHTML = "";
        document.getElementById("parameter-body").innerHTML = "";

        // Fill Data
        document.getElementById("product-name").value = data.name || "";
        document.getElementById("categoryselect").value = data.category || "";
        document.getElementById("type-select").value = data.type || "";
        document.getElementById("model-select").value = data.productmodel || "";
        if (data.validation_expr) document.getElementById("validation-expr").value = data.validation_expr;

        // Parameters
        if (Array.isArray(data.parameters)) {
            const tbody = document.getElementById("parameter-body");
            data.parameters.forEach(p => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${p.name}</td><td>${p.abbreviation}</td><td>${p.default_value}</td><td>${p.description || ""}</td><td class="text-center"><button class="btn btn-sm btn-danger remove-param">✕</button></td>`;
                tbody.appendChild(tr);
            });
        }

        // Parts (Re-rendering table)
        if (Array.isArray(data.part_templates)) {
            data.part_templates.forEach(p => {
                if(!p.id) p.id = Date.now() + Math.random();
                window.productState.parts.push(p);
                renderPartRow(p);
            });
        }
        alert("Draft Loaded.");
    }
});

// 3. REPLACING YOUR "DOMContentLoaded" (STOPPING AUTO-LOAD)
window.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 System initialized. Editor is fresh.");
    
    // Only init functional components, not data
    if (typeof initProductHardwareAccordion === 'function') {
        initProductHardwareAccordion();
    }
});

function fillPartModal(p) {
    // 1. Header & Identity
    const nameInput = document.getElementById("part-template-name");
    if (nameInput) nameInput.value = p.name || "Unnamed Part";

    // 2. Geometry Tab
    document.getElementById("pt-len-eq").value = p.geometry?.length_eq || p.part_length_equation || "";
    document.getElementById("pt-wid-eq").value = p.geometry?.width_eq || p.part_width_equation || "";
    document.getElementById("pt-qty-eq").value = p.geometry?.qty_eq || p.part_qty_equation || "1";

    // 3. Logic Tab (The Decoupled Rule)
    const logicInput = document.getElementById("pt-logic-expression");
    if (logicInput) {
        logicInput.value = p.logic?.material_expression || p.material_expression || "T <= 19";
    }
    window.currentPartState.materials.whitelist = p.materials?.whitelist || 
        (p.material_whitelist ? p.material_whitelist.map(m => m.material) : []);
    renderMaterialTable();
    const sides = ["top", "right", "bottom", "left"];
    sides.forEach(side => {
        const savedWhitelist = p.edgebands?.[side]?.whitelist || [];
        const savedApplied = p.edgebands?.[side]?.applied || !!p[`edgeband_${side}`];
        window.currentPartState.edgebands[side] = {
            applied: savedApplied,
            whitelist: savedWhitelist
        };
    });
    renderEdgebandTab();
    if (typeof renderPartHardware === "function") {
        const hwData = p.partHardware || p.hardware_rules || {};
        renderPartHardware(hwData);
    }
    if (typeof validatePartForm === "function") validatePartForm();
}

window.savePartFromModal = () => {
    // 1. We update the 'window.currentPartState' which has been updated via 
    // the various tabs (Material, EB, Hardware) during the modal session.
    const p = window.currentPartState;
    
    // 2. Capture Header Inputs
    p.name = document.getElementById("part-template-name").value || p.name;
    
    // 3. Capture Geometry Tab
    p.geometry.length_eq = document.getElementById("pt-len-eq").value;
    p.geometry.width_eq = document.getElementById("pt-wid-eq").value;
    p.geometry.qty_eq = document.getElementById("pt-qty-eq").value;

    // 4. Capture Logic Expression
    p.logic.material_expression = document.getElementById("pt-logic-expression")?.value || "";

    // 5. Update Global Product State
    const idx = window.productState.parts.findIndex(item => item.id === p.id);
    if (idx !== -1) {
        window.productState.parts[idx] = JSON.parse(JSON.stringify(p));
    } else {
        window.productState.parts.push(JSON.parse(JSON.stringify(p)));
    }

    // 6. UI Update
    renderPartRow(p);
    $("#partTemplateModal").modal("hide");
};
const addPartBtn = document.getElementById("open-part-template-btn");

if (addPartBtn) {
    addPartBtn.addEventListener("click", () => {
        console.log("➕ Add Part clicked");

        // 1. FIRST: Get the name from the main input screen
        const mainInput = document.getElementById("part-name");
        const mainInputName = mainInput ? mainInput.value.trim() : "";

        if (!mainInputName) {
            alert("Please enter a Part Name first.");
            return;
        }

        // 2. SECOND: Create the state with that name
        window.currentPartState = {
            id: Date.now(), // Unique ID
            name: mainInputName,
            geometry: { length_eq: "", width_eq: "", qty_eq: "1" },
            materials: { whitelist: [], defaultMaterialId: null },
            edgebands: { top:{}, right:{}, bottom:{}, left:{} },
            partHardware: {}
        };

        // 3. THIRD: Sync the Modal UI using our standardized "pt-" IDs
        document.getElementById("part-template-name").value = mainInputName;
        document.getElementById("pt-len-eq").value = "";
        document.getElementById("pt-wid-eq").value = "";
        document.getElementById("pt-qty-eq").value = "1";

        $("#partTemplateModal").modal("show");
    });
}
/* ============================================================
   GLOBAL UTILITIES
============================================================ */
window.showModal = id => {
    const el = document.getElementById(id);
    if (!el) return console.error("Modal not found:", id);
    let modal = bootstrap.Modal.getInstance(el);
    if (!modal) modal = new bootstrap.Modal(el);
    modal.show();
};

window.hideModal = id => {
    const el = document.getElementById(id);
    bootstrap.Modal.getInstance(el)?.hide();
};

let editingPartId = null;

const blankPartState = () => ({
    id: Date.now() + Math.random(),
    name: "",
    logic: {
        material_expression: "T <= 19", // Default starting rule
        edgeband_bandwidth: 5
    },
    geometry: { length_eq: "", width_eq: "", qty_eq: "1" },
    materials: { whitelist: []},
    edgebands: { 
        top:    { applied: false, whitelist: [] }, 
        right:  { applied: false, whitelist: [] }, 
        bottom: { applied: false, whitelist: [] }, 
        left:   { applied: false, whitelist: [] } 
    },
    partHardware: {}
});
window.currentPartState = blankPartState();

/* ============================================================
   MODAL BUTTONS HOOK
============================================================ */

document.getElementById("open-product-hardware-modal-btn")?.addEventListener("click",()=>window.openProductHardwareModal?.());
document.getElementById("dry-run-btn")?.addEventListener("click",()=>window.showModal?.("dryRunModal"));

/* ============================================================
   PART TABLE RENDERING
============================================================ */
const partTable = document.getElementById("part-templates-body");
const partNameInput = document.getElementById("part-name");

function renderPartRow(part) {
    const tbody = document.getElementById("part-templates-body");
    if (!tbody) return;

    let tr = tbody.querySelector(`tr[data-id="${part.id}"]`);
    if (!tr) {
        tr = document.createElement("tr");
        tr.dataset.id = part.id;
        tbody.appendChild(tr);
    }

    // --- GEOMETRY: Look for nested geometry (from Modal) OR flat keys (from Serializer) ---
    const L = part.part_length_equation || part.geometry?.length_eq || "0";
    const W = part.part_width_equation  || part.geometry?.width_eq  || "0";
    const Q = part.part_qty_equation    || part.geometry?.qty_eq    || "1";

    // --- EDGEBANDS: Clockwise (Top -> Right -> Bottom -> Left) ---
    const sides = ['top', 'right', 'bottom', 'left'];
    const ebIcons = sides.map(side => {
        // Look for flat key (edgeband_top) OR nested key (edgebands.top.default)
        const ebValue = part[`edgeband_${side}`] || part.edgebands?.[side]?.default;
        const color = ebValue ? '#198754' : '#dee2e6'; 
        return `<span title="${side}" style="color: ${color}; font-size:1.2rem; margin:0 2px;">●</span>`;
    }).join("");

    // --- HARDWARE ---
    const hwRules = part.hardware_rules || (part.partHardware ? Object.keys(part.partHardware) : []);
    const hwCount = hwRules.length;

    tr.innerHTML = `
        <td class="fw-bold text-primary">${part.name}</td>
        <td>
            <div class="fw-bold">${L} × ${W}</div>
            <small class="text-muted">Qty: ${Q}</small>
        </td>
        <td><span class="badge bg-light text-dark border">Material Whitelist</span></td>
        <td class="text-center text-nowrap">
            <div class="small text-muted mb-1" style="font-size: 0.6rem;">T R B L</div>
            ${ebIcons}
        </td>
        <td class="text-center"><span class="badge bg-primary">${hwCount} Rules</span></td>
        <td class="text-center">
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-warning edit-part">✏️</button>
                <button class="btn btn-outline-danger remove-part">🗑</button>
            </div>
        </td>
    `;
}

/* ============================================================
   PART EDIT / DELETE
============================================================ */
partTable.addEventListener("click", e => {
    const tr = e.target.closest("tr"); 
    if (!tr) return;
    const id = tr.dataset.id; 
    const part = productState.parts.find(p => p.id == id);
    if (e.target.classList.contains("edit-part")) {
        if (!part) return console.error("Part not found in state:", id);
        console.log("✏️ Editing Part:", part.name);
        editingPartId = id;
        window.currentPartState = JSON.parse(JSON.stringify(part));
        if (partNameInput) partNameInput.value = part.name;
        fillPartModal(window.currentPartState);
        window.showModal("partTemplateModal");
    }

    if (e.target.classList.contains("remove-part")) {
        if (!confirm(`Remove "${part?.name || 'this part'}"?`)) return;
        productState.parts = productState.parts.filter(p => p.id != id); 
        tr.remove();
    }
});

/* ============================================================
   BUILD PART TEMPLATES PAYLOAD
============================================================ */
function buildPartTemplatesPayload(parts) {
    return (parts || []).map(part => {
        // Find the 'Ceiling' for the main fields (used for initial Quote math)
        const whitelistedMats = MATERIALS.filter(m => part.materials?.whitelist?.includes(m.id));
        const ceilingMatId = whitelistedMats.length > 0 
            ? whitelistedMats.reduce((p, c) => (p.thickness_mm > c.thickness_mm ? p : c)).id 
            : null;

        return {
            name: part.name || "Unnamed Part",
            // Logic Expressions (The Dynamic Part)
            material_expression: part.logic?.material_expression || "",
            
            // Flattening Geometry
            part_length_equation: part.part_length_equation || part.geometry?.length_eq || "0",
            part_width_equation:  part.part_width_equation  || part.geometry?.width_eq  || "0",
            part_qty_equation:    part.part_qty_equation    || part.geometry?.qty_eq    || "1",

            // Material Whitelist (Mapping to Django objects)
            material_whitelist: (part.materials?.whitelist || []).map(mid => ({
                material: parseInt(mid),
                is_default: parseInt(mid) === ceilingMatId // Python picks the ceiling
            })),

            // Edgeband Primary IDs (satisfies edgeband_top, etc. fields)
            edgeband_top:    part.edgebands?.top?.whitelist?.[0]    || null,
            edgeband_right:  part.edgebands?.right?.whitelist?.[0]  || null,
            edgeband_bottom: part.edgebands?.bottom?.whitelist?.[0] || null,
            edgeband_left:   part.edgebands?.left?.whitelist?.[0]   || null,

            // Full Edgeband Whitelist (fixes the "Logical Friction")
            // This maps to the PartEdgeBandWhitelist model
            edgeband_whitelist: [
                ...(part.edgebands?.top?.whitelist    || []).map(id => ({ edgeband: id, side: 'top' })),
                ...(part.edgebands?.right?.whitelist  || []).map(id => ({ edgeband: id, side: 'right' })),
                ...(part.edgebands?.bottom?.whitelist || []).map(id => ({ edgeband: id, side: 'bottom' })),
                ...(part.edgebands?.left?.whitelist   || []).map(id => ({ edgeband: id, side: 'left' }))
            ],

            hardware_rules: Object.entries(part.partHardware || {}).map(([hid, r]) => ({
                hardware: parseInt(hid),
                quantity_equation: r.qty || "1",
                applicability_condition: r.cond || ""
            }))
        };
    });
}
/* ============================================================
   PARAMETERS HANDLING
============================================================ */
const saveParamBtn=document.getElementById("save-param-btn");
const paramBody=document.getElementById("parameter-body");
saveParamBtn?.addEventListener("click",()=>{
    const name=document.getElementById("param-name").value.trim();
    const abbr=document.getElementById("param-abbr").value.trim();
    const def=document.getElementById("param-default").value.trim();
    const desc=document.getElementById("param-desc").value.trim();
    if(!name||!abbr){alert("Parameter Name & Abbreviation required"); return;}
    const tr=document.createElement("tr");
    tr.innerHTML=`<td>${name}</td><td>${abbr}</td><td>${def||0}</td><td>${desc||""}</td><td class="text-center"><button class="btn btn-sm btn-danger remove-param">✕</button></td>`;
    paramBody.appendChild(tr);
    document.getElementById("param-name").value="";
    document.getElementById("param-abbr").value="";
    document.getElementById("param-default").value="";
    document.getElementById("param-desc").value="";
});
paramBody?.addEventListener("click", e=>{
    if(e.target.classList.contains("remove-param")) e.target.closest("tr").remove();
});
function collectParameters(){ return [...document.querySelectorAll("#parameter-body tr")].map(tr=>{
    const td=tr.querySelectorAll("td");
    return { name:td[0].innerText, abbreviation:td[1].innerText, default_value:td[2].innerText, description:td[3].innerText };
}); }

// Add this to your JS
document.getElementById("save-part-hardware-btn")?.addEventListener("click", () => {
    console.log("Button Clicked!");
    window.savePartFromModal();
});
/* ============================================================
   FINAL PRODUCT SAVE
============================================================ */
document.getElementById("submit-product-btn")?.addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const originalText = btn.innerHTML;
    
    // 1. Enter Loading State (Enterprise standard to prevent double-POST)
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Saving...`;

    try {
        const partTemplates = buildPartTemplatesPayload(productState.parts);
        const hardwareRulesArray = Object.entries(selected.productHardware || {}).map(([id, obj]) => ({
            hardware: Number(id),
            quantity_equation: obj.qty || "1",
            applicability_condition: obj.cond || ""
        }));
        const parameters = collectParameters();

        const payload = {
            name: document.getElementById("product-name").value.trim(),
            category: document.getElementById("categoryselect").value,
            type: document.getElementById("type-select").value,
            productmodel: document.getElementById("model-select").value,
            parameters: parameters,
            part_templates: partTemplates,
            hardware_rules: hardwareRulesArray,
            validation_expr: document.getElementById("validation-expr")?.value.trim() || ""
        };

        // 2. Expression Pre-Validation
        if (payload.validation_expr) {
            const validRes = await fetch("/modularcalc/api/validate-expression/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": window.CSRF_TOKEN },
                body: JSON.stringify({ expression: payload.validation_expr })
            });
            const json = await validRes.json();
            if (!json.valid) throw new Error(`Validation Logic Error: ${json.error}`);
        }

        // 3. Final Commit to LignumX Engine
        const res = await fetch("/modularcalc/api/products/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": window.CSRF_TOKEN },
            body: JSON.stringify(payload)
        });

        const responseData = await res.json();

        if (res.ok) {
            alert("Success: Modular Product Committed to Database.");
            localStorage.removeItem("modularProductDraft");
            window.location.href = '/modularcalc/mproduct/';
        } else {
            // Handle Django Rest Framework field errors (e.g., 400 Bad Request)
            const errorMsg = responseData.detail || JSON.stringify(responseData);
            throw new Error(`Server Rejected Payload: ${errorMsg}`);
        }

    } catch (err) {
        console.error("Submission Error:", err);
        alert(err.message || "Critical System Error during save");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
});
// 1. Updated State Structure

/* ============================================================
   AI EXPRESSION SUGGESTION
============================================================ */
$("#suggestBtn").on("click", async function(){
    const intent=$("#intentInput").val();
    try{
        const res=await fetch("/modularcalc/api/expression-suggest/", {
            method:"POST",
            headers: {"Content-Type":"application/json","X-CSRFToken":window.CSRF_TOKEN},
            body: JSON.stringify({intent, product_id:productId})
        });
        const json=await res.json();
        $("#expressionTextarea").val(json.suggestion).trigger("input");
    }catch(e){console.error("AI suggestion failed", e);}
});

/* ============================================================
   DRY-RUN PREVIEW
============================================================ */
document.getElementById("dry-run-btn")?.addEventListener("click", async ()=>{
    try{
        const partTemplates = buildPartTemplatesPayload(productState.parts);
        const parameters = collectParameters();
        const dims = {
            product_length: Number(document.getElementById("product-length")?.value||1000),
            product_width: Number(document.getElementById("product-width")?.value||500),
            product_height: Number(document.getElementById("product-height")?.value||800)
        };
        const payload = {product_dims: dims, parameters, part_templates: partTemplates};
        const res = await fetch("/modularcalc/api/products/dry-run/", {
            method:"POST",
            headers: {"Content-Type":"application/json","X-CSRFToken":window.CSRF_TOKEN},
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if(json.error) throw new Error(json.error);
        window.showDryRunPreview?.(json.preview);
    }catch(e){ console.error(e); alert("Dry-run failed: "+e.message); }
});
// Initialization
initData();