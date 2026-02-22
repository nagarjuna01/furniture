/* ============================================================
   PART TEMPLATE MODAL JS
   - Geometry
   - Material (with independent filters + select all filtered)
   - Edgeband
   - Hardware
   ============================================================ */

/* ------------------------ GLOBAL STATE ------------------------ */
window.currentPartState = window.currentPartState || {
    id: null,
    name: "",
    geometry: {},
    materials: { whitelist: [], defaultMaterialId: null },
    edgebands: { top:{}, right:{}, bottom:{}, left:{} },
    partHardware: {}
};

let MATERIALS = [];
let FILTERED_MATERIALS = [];

/* ------------------------ ELEMENTS ------------------------ */
const materialModal = document.getElementById("materialModal");
const materialFilters = {
    group: document.getElementById("filter-material-group"),
    type: document.getElementById("filter-material-type"),
    model: document.getElementById("filter-material-model"),
    brand: document.getElementById("filter-material-brand"),
    thickness: document.getElementById("filter-material-thickness")
};
const materialTableBody = document.getElementById("material-body");
const whitelistBox = document.getElementById("selected-materials");
const defaultBox = document.getElementById("default-material");
const selectAllCheckboxId = "select-all-materials";

/* ------------------------ MATERIAL STATE ------------------------ */
function getMaterialState() {
    if (!window.currentPartState.materials) {
        window.currentPartState.materials = { whitelist: [], defaultMaterialId: null };
    }
    return window.currentPartState.materials;
}

/* ------------------------ FILTER HELPERS ------------------------ */
function resetSelect(select, label = "All") {
    select.innerHTML = `<option value="">${label}</option>`;
}

function fillSelect(select, items, idKey, labelKey) {
    const current = select.value;
    resetSelect(select);
    const seen = new Set();
    items.forEach(item => {
        const id = item[idKey];
        const label = item[labelKey] || "-";
        if (id == null || seen.has(id)) return;
        seen.add(id);
        select.appendChild(new Option(label, id));
    });
    if ([...select.options].some(o => o.value === current)) select.value = current;
}

/* ------------------------ FETCH MATERIALS ------------------------ */
async function fetchMaterials() {
    try {
        const res = await fetch("/material/v1/woodens/");
        const data = await res.json();
        MATERIALS = data.results || [];
        console.log("✅ MATERIALS FETCHED", MATERIALS.length);
        initMaterialFilters();
        applyMaterialFilters();
    } catch (e) {
        console.error("❌ MATERIAL FETCH FAILED", e);
    }
}

/* ------------------------ FILTER LOGIC ------------------------ */
function initMaterialFilters() {
    // independent filters: populate all
    fillSelect(materialFilters.group, MATERIALS, "material_grp", "material_grp_label");
    fillSelect(materialFilters.type, MATERIALS, "material_type", "material_type_label");
    fillSelect(materialFilters.model, MATERIALS, "material_model", "material_model_label");
    fillSelect(materialFilters.brand, MATERIALS, "brand", "brand_label");
    fillSelect(
        materialFilters.thickness,
        MATERIALS.map(m => ({ thickness_mm: m.thickness_mm, label: `${m.thickness_mm} mm` })),
        "thickness_mm",
        "label"
    );

    // All onchange → apply filters
    Object.values(materialFilters).forEach(sel => sel.addEventListener("change", applyMaterialFilters));
}

/* ------------------------ APPLY FILTERS ------------------------ */
function applyMaterialFilters() {
    const g = materialFilters.group.value || null;
    const t = materialFilters.type.value || null;
    const m = materialFilters.model.value || null;
    const b = materialFilters.brand.value || null;
    const th = materialFilters.thickness.value || null;

    FILTERED_MATERIALS = MATERIALS.filter(x => {
        if (g && String(x.material_grp) !== g) return false;
        if (t && String(x.material_type) !== t) return false;
        if (m && String(x.material_model) !== m) return false;
        if (b && String(x.brand) !== b) return false;
        if (th && String(x.thickness_mm) !== th) return false;
        return true;
    });

    renderMaterialTable();
}

/* ------------------------ MATERIAL TABLE ------------------------ */
function renderMaterialTable() {
    const matState = getMaterialState();
    materialTableBody.innerHTML = "";

    // header with select all
    const headerTr = document.createElement("tr");
    headerTr.innerHTML = `
        <th colspan="4">
            <input type="checkbox" id="${selectAllCheckboxId}"> Select All Filtered
        </th>
        <th>Default</th>
    `;
    materialTableBody.appendChild(headerTr);

    FILTERED_MATERIALS.forEach(m => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${m.name}</td>
            <td>${m.thickness_mm} mm</td>
            <td>${m.brand_label || "-"}</td>
            <td class="text-center">
                <input type="checkbox"
                    ${matState.whitelist.includes(m.id) ? "checked" : ""}
                    onchange="toggleWhitelist(${m.id})">
            </td>
            <td class="text-center">
                <input type="radio" name="default_material"
                    ${matState.defaultMaterialId === m.id ? "checked" : ""}
                    onclick="setDefault(${m.id})">
            </td>
        `;
        materialTableBody.appendChild(tr);
    });

    // select all filtered
    const selectAll = document.getElementById(selectAllCheckboxId);
    if (selectAll) {
        selectAll.checked = FILTERED_MATERIALS.every(m => matState.whitelist.includes(m.id));
        selectAll.onchange = function() {
            const mat = getMaterialState();
            if (this.checked) {
                // add all filtered
                const idsToAdd = FILTERED_MATERIALS.map(m => m.id);
                mat.whitelist = Array.from(new Set([...mat.whitelist, ...idsToAdd]));
            } else {
                // remove all filtered
                const idsToRemove = new Set(FILTERED_MATERIALS.map(m => m.id));
                mat.whitelist = mat.whitelist.filter(id => !idsToRemove.has(id));
                if (mat.defaultMaterialId && idsToRemove.has(mat.defaultMaterialId)) mat.defaultMaterialId = null;
            }
            updateMaterialPreview();
            renderMaterialTable(); // refresh table to sync checkboxes
        };
    }

    updateMaterialPreview();
}

/* ------------------------ MATERIAL ACTIONS ------------------------ */
window.toggleWhitelist = function(id) {
    const mat = getMaterialState();
    const set = new Set(mat.whitelist || []);
    set.has(id) ? set.delete(id) : set.add(id);
    mat.whitelist = [...set];
    if (mat.defaultMaterialId && !set.has(mat.defaultMaterialId)) mat.defaultMaterialId = null;
    updateMaterialPreview();
    renderMaterialTable();
};

window.setDefault = function(id) {
    const mat = getMaterialState();
    if (!mat.whitelist.includes(id)) return;
    mat.defaultMaterialId = id;
    updateMaterialPreview();
};

/* ------------------------ PREVIEW ------------------------ */
function updateMaterialPreview() {
    const mat = getMaterialState();
    whitelistBox.innerHTML = mat.whitelist
        .map(id => MATERIALS.find(m => m.id === id)?.name)
        .filter(Boolean)
        .map(n => `<span class="badge bg-secondary me-1">${n}</span>`)
        .join("");

    defaultBox.innerHTML = mat.defaultMaterialId
        ? `<span class="badge bg-success">${MATERIALS.find(m => m.id === mat.defaultMaterialId)?.name}</span>`
        : "<em>No default</em>";
}

/* ------------------------ MODAL EVENTS ------------------------ */
materialModal?.addEventListener("shown.bs.modal", () => {
    if (!MATERIALS.length) fetchMaterials();
    else renderMaterialTable();
});

function resetMaterialModal() {
    Object.values(materialFilters).forEach(sel => sel.value = "");
    renderMaterialTable();
    updateMaterialPreview();
}
