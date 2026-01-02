/* ============================================================
   MATERIAL MODAL – PART SCOPED STATE (FIXED)
   ============================================================ */

let MATERIALS = [];
let FILTERED = [];

const modal = document.getElementById("materialModal");

const selGroup = document.getElementById("filter-material-group");
const selType = document.getElementById("filter-material-type");
const selModel = document.getElementById("filter-material-model");
const selBrand = document.getElementById("filter-material-brand");
const selThickness = document.getElementById("filter-material-thickness");

const tbody = document.getElementById("material-body");
const whitelistBox = document.getElementById("selected-materials");
const defaultBox = document.getElementById("default-material");


/* ============================================================
   SAFE PART MATERIAL STATE ACCESSOR
   ============================================================ */
function getMaterialState() {
  if (!window.currentPartState) {
    console.warn("⚠️ currentPartState missing, creating fallback");
    window.currentPartState = {};
  }

  if (!window.currentPartState.materials) {
    window.currentPartState.materials = {
      whitelist: [],
      defaultMaterialId: null
    };
  }

  return window.currentPartState.materials;
}


/* ============================================================
   FILTER HELPERS
   ============================================================ */
function resetSelect(select, label = "All") {
  select.innerHTML = `<option value="">${label}</option>`;
}

function fillSelect(select, items, idKey, labelKey) {
  const current = select.value;
  resetSelect(select);
  const seen = new Set();

  items.forEach(item => {
    const id = item[idKey];
    const label = item[labelKey];
    if (id == null || seen.has(id)) return;
    seen.add(id);
    select.appendChild(new Option(label || "-", id));
  });

  if ([...select.options].some(o => o.value === current)) {
    select.value = current;
  }
}


/* ============================================================
   API
   ============================================================ */
async function fetchMaterials() {
  try {
    const res = await fetch("/material/v1/woodens/");
    const data = await res.json();
    MATERIALS = data.results || [];
    console.log("✅ MATERIALS FETCHED", MATERIALS.length);
    initFilters();
    applyFilters();
  } catch (e) {
    console.error("❌ MATERIAL FETCH FAILED", e);
  }
}


/* ============================================================
   FILTER LOGIC
   ============================================================ */
function initFilters() {
  fillSelect(selGroup, MATERIALS, "material_grp", "material_grp_label");
  fillSelect(selBrand, MATERIALS, "brand", "brand_label");
  fillSelect(
    selThickness,
    MATERIALS.map(m => ({
      thickness_mm: m.thickness_mm,
      label: `${m.thickness_mm} mm`
    })),
    "thickness_mm",
    "label"
  );

  selGroup.onchange = () => {
    selType.value = "";
    selModel.value = "";
    applyFilters();
    updateDependentState();
  };

  selType.onchange = () => {
    selModel.value = "";
    applyFilters();
    updateDependentState();
  };

  selModel.onchange = applyFilters;
  selBrand.onchange = applyFilters;
  selThickness.onchange = applyFilters;

  updateDependentState();
}

function updateDependentState() {
  selType.disabled = !selGroup.value;
  selModel.disabled = !selType.value;
}
/* ============================================================
   APPLY FILTERS – FULL BIDIRECTIONAL INTERDEPENDENCE
   ============================================================ */
function applyFilters() {
  const g = selGroup.value || null;
  const t = selType.value || null;
  const m = selModel.value || null;
  const b = selBrand.value || null;
  const th = selThickness.value || null;

  // Filter materials based on all current selections
  FILTERED = MATERIALS.filter(x => {
    if (g && String(x.material_grp) !== g) return false;
    if (t && String(x.material_type) !== t) return false;
    if (m && String(x.material_model) !== m) return false;
    if (b && String(x.brand) !== b) return false;
    if (th && String(x.thickness_mm) !== th) return false;
    return true;
  });

  // Rebuild all dependent filters using filtered results
  rebuildDependentFilters();
  renderTable();
}

/* ============================================================
   REBUILD DEPENDENT FILTERS – FULL BIDIRECTIONAL INTERDEPENDENCE
   ============================================================ */
function rebuildDependentFilters() {
  // Type options filtered by current selections
  fillSelect(
    selType,
    FILTERED,
    "material_type",
    "material_type_label"
  );

  // Model options filtered by current selections
  fillSelect(
    selModel,
    FILTERED,
    "material_model",
    "material_model_label"
  );

  // Brand options filtered by current selections
  fillSelect(
    selBrand,
    FILTERED,
    "brand",
    "brand_label"
  );

  // Thickness options filtered by current selections
  fillSelect(
    selThickness,
    FILTERED.map(m => ({ thickness_mm: m.thickness_mm, label: `${m.thickness_mm} mm` })),
    "thickness_mm",
    "label"
  );

  updateDependentState();
}


/* ============================================================
   TABLE RENDER
   ============================================================ */
function renderTable() {
  const mat = getMaterialState();
  tbody.innerHTML = "";

  FILTERED.forEach(m => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${m.name}</td>
      <td>${m.thickness_mm} mm</td>
      <td>${m.brand_label || "-"}</td>
      <td class="text-center">
        <input type="checkbox"
          ${mat.whitelist.includes(m.id) ? "checked" : ""}
          onchange="toggleWhitelist(${m.id})">
      </td>
      <td class="text-center">
        <input type="radio" name="default_material"
          ${mat.defaultMaterialId === m.id ? "checked" : ""}
          onclick="setDefault(${m.id})">
      </td>
    `;
    tbody.appendChild(tr);
  });
}


/* ============================================================
   ACTIONS
   ============================================================ */
window.toggleWhitelist = function (id) {
  const mat = getMaterialState();
  const set = new Set(mat.whitelist || []);

  set.has(id) ? set.delete(id) : set.add(id);
  mat.whitelist = [...set];

  if (mat.defaultMaterialId && !set.has(mat.defaultMaterialId)) {
    mat.defaultMaterialId = null;
  }

  console.log("🧾 MATERIAL STATE", mat);
  updatePreview();
};

window.setDefault = function (id) {
  const mat = getMaterialState();
  if (!mat.whitelist.includes(id)) return;

  mat.defaultMaterialId = id;
  updatePreview();
};


/* ============================================================
   PREVIEW
   ============================================================ */
function updatePreview() {
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


/* ============================================================
   MODAL EVENTS
   ============================================================ */
function resetModal() {
  selGroup.value = "";
  selType.value = "";
  selModel.value = "";
  selBrand.value = "";
  selThickness.value = "";

  // const mat = getMaterialState();
  // mat.whitelist = [];
  // mat.defaultMaterialId = null;
console.log("🧼 Filters reset, but data preserved.");
  renderTable();
  updatePreview();
  updateDependentState();
}

modal?.addEventListener("shown.bs.modal", () => {
  if (!MATERIALS.length) {
  fetchMaterials().then(() => {
    renderTable();
    updatePreview();
  });
} else {
  renderTable();
  updatePreview();
}
});

// modal?.addEventListener("hidden.bs.modal", resetModal);
