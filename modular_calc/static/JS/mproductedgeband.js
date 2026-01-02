(function () {
window.materialWhitelist = new Set();
console.clear();
console.log("✅ EDGEBAND JS EXECUTING");

/* ================= GLOBAL STATE ================= */

const SIDES = ["top", "right", "bottom", "left"];

let EDGEBANDS = [];
let EDGEBAND_NAMES = [];

const SIDE_STATE = {};
const SIDE_WHITELIST = {};
const SIDE_DEFAULT = {};
const SIDE_FILTERS = {};

SIDES.forEach(s => {
  SIDE_STATE[s] = false;
  SIDE_WHITELIST[s] = new Set();
  SIDE_DEFAULT[s] = null;
  SIDE_FILTERS[s] = { brand: "", depth: "", thickness: "", name: "" };
});

/* ================= DOM ================= */

const modal = document.getElementById("edgebandModal");
const sidesContainer = document.getElementById("edgeband-sides");
const summaryBox = document.getElementById("selected-edgebands");

/* ================= HTML BUILD ================= */

function buildSidesHTML() {
  sidesContainer.innerHTML = "";

  SIDES.forEach(side => {
    sidesContainer.insertAdjacentHTML("beforeend", `
      <div class="col-md-6 mb-4">

        <div class="d-flex justify-content-between align-items-center">
          <h6 class="mb-0 text-capitalize">${side}</h6>
          <div class="form-check form-switch">
            <input class="form-check-input side-toggle"
                   type="checkbox"
                   data-side="${side}"
                   id="toggle-${side}">
            <label class="form-check-label" for="toggle-${side}">
              Apply
            </label>
          </div>
        </div>

        <div class="collapse mt-2" id="collapse-${side}">
        <div class="text-muted small mb-2">
          Search by <strong>Brand</strong>     <strong>Depth</strong>  
          <strong>Thickness</strong>         <strong>Edgeband</strong>
        </div>
          <div class="row mb-2">
            <div class="col">
              <select class="form-select filter-brand" data-side="${side}">
                <option value="">Brand</option>
              </select>
            </div>
            <div class="col">
              <select class="form-select filter-depth" data-side="${side}">
                <option value="">Depth</option>
              </select>
            </div>
            <div class="col">
              <select class="form-select filter-thickness" data-side="${side}">
                <option value="">Thickness</option>
              </select>
            </div>
            <div class="col">
              <select class="form-select filter-name" data-side="${side}">
                <option value="">Name</option>
              </select>
            </div>
          </div>

          <table class="table table-sm table-bordered">
            <thead>
              <tr>
                <th>Name</th>
                <th class="text-center">Whitelist</th>
                <th class="text-center">Default</th>
              </tr>
            </thead>
            <tbody id="edgeband-body-${side}"></tbody>
          </table>
        </div>
      </div>
    `);
  });
}

/* ================= FETCH ================= */

async function loadEdgebandData() {
  const [bandsRes, namesRes] = await Promise.all([
    fetch("/material/v1/edgebands/"),
    fetch("/material/v1/edgeband-names/")
  ]);

  EDGEBANDS = (await bandsRes.json()).results || [];
  EDGEBAND_NAMES = (await namesRes.json()).results || [];

  console.log("EDGEBANDS", EDGEBANDS.length);
  console.log("EDGEBAND_NAMES", EDGEBAND_NAMES.length);
}

/* ================= FILTER HELPERS ================= */

function fillSelect(select, values, labelFn) {
  const current = select.value;
  select.innerHTML = `<option value=""></option>`;

  [...new Set(values)].forEach(v => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = labelFn ? labelFn(v) : v;
    select.appendChild(opt);
  });

  if ([...select.options].some(o => o.value === current)) {
    select.value = current;
  }
}

/* ================= FILTER LOGIC ================= */

function applyFilters(side) {
  const f = SIDE_FILTERS[side];

  let names = EDGEBAND_NAMES.filter(n => {
    if (f.brand && String(n.brand) !== f.brand) return false;
    if (f.depth && String(n.depth) !== f.depth) return false;
    return true;
  });

  let bands = EDGEBANDS.filter(b => {
    if (f.thickness && String(b.thickness) !== f.thickness) return false;
    if (f.name && String(b.edgeband_name) !== f.name) return false;
    return names.some(n => n.id === b.edgeband_name);
  });

  rebuildFilters(side, names, bands);
  renderTable(side, bands);
}

/* ================= FILTER REBUILD ================= */

function rebuildFilters(side, names, bands) {
  const root = modal;

  fillSelect(
    root.querySelector(`.filter-brand[data-side="${side}"]`),
    names.map(n => String(n.brand)),
    v => names.find(n => String(n.brand) === v)?.brand_name
  );

  fillSelect(
    root.querySelector(`.filter-depth[data-side="${side}"]`),
    names.map(n => String(n.depth)),
    v => `${v} mm`
  );

  fillSelect(
    root.querySelector(`.filter-name[data-side="${side}"]`),
    names.map(n => String(n.id)),
    v => names.find(n => String(n.id) === v)?.name
  );

  fillSelect(
    root.querySelector(`.filter-thickness[data-side="${side}"]`),
    bands.map(b => String(b.thickness)),
    v => `${v} mm`
  );
}

/* ================= TABLE ================= */

function renderTable(side, rows) {
  const tbody = document.getElementById(`edgeband-body-${side}`);
  tbody.innerHTML = "";

  rows.forEach(b => {
    const name = EDGEBAND_NAMES.find(n => n.id === b.edgeband_name)?.name || "-";

    tbody.insertAdjacentHTML("beforeend", `
      <tr>
        <td>${name} (${b.thickness}mm)</td>
        <td class="text-center">
          <input type="checkbox"
            ${SIDE_WHITELIST[side].has(b.id) ? "checked" : ""}
            onchange="toggleEdgeBandWhitelist('${side}', ${b.id})">
        </td>
        <td class="text-center">
          <input type="radio"
            name="default-${side}"
            ${SIDE_DEFAULT[side] === b.id ? "checked" : ""}
            onclick="setEdgeBandDefault('${side}', ${b.id})">
        </td>
      </tr>
    `);
  });
}

/* ================= SELECTION ================= */

window.toggleEdgeBandWhitelist = function (side, id) {
  SIDE_WHITELIST[side].has(id)
    ? SIDE_WHITELIST[side].delete(id)
    : SIDE_WHITELIST[side].add(id);

  if (!SIDE_WHITELIST[side].has(SIDE_DEFAULT[side])) {
    SIDE_DEFAULT[side] = null;
  }

  updateSummary();
};

window.setEdgeBandDefault = function (side, id) {
  if (!SIDE_WHITELIST[side].has(id)) return;
  SIDE_DEFAULT[side] = id;
  updateSummary();
};

/* ================= SUMMARY ================= */

function updateSummary() {
  summaryBox.innerHTML = SIDES.map(side => {
    if (!SIDE_STATE[side]) return "";
    return `
      <div>
        <strong>${side}:</strong>
        default=${SIDE_DEFAULT[side] || "-"},
        whitelist=[${[...SIDE_WHITELIST[side]].join(", ")}]
      </div>
    `;
  }).join("");
}

/* ================= RESET ================= */

function resetSide(side) {
  SIDE_STATE[side] = false;
  SIDE_WHITELIST[side].clear();
  SIDE_DEFAULT[side] = null;
  SIDE_FILTERS[side] = { brand: "", depth: "", thickness: "", name: "" };

  document.getElementById(`toggle-${side}`).checked = false;
  document.getElementById(`edgeband-body-${side}`).innerHTML = "";

  modal
    .querySelectorAll(`[data-side="${side}"]`)
    .forEach(el => el.value = "");

  new bootstrap.Collapse(
    document.getElementById(`collapse-${side}`),
    { hide: true }
  );
}

function resetModal() {
  SIDES.forEach(resetSide);
  summaryBox.innerHTML = "";
}

/* ================= EVENTS ================= */

document.addEventListener("change", e => {
  const side = e.target.dataset.side;
  if (!side) return;

  if (e.target.classList.contains("side-toggle")) {
    SIDE_STATE[side] = e.target.checked;
    const collapse = document.getElementById(`collapse-${side}`);
    new bootstrap.Collapse(collapse, { toggle: true });
    if (SIDE_STATE[side]) applyFilters(side);
    return;
  }

  if (e.target.classList.contains("filter-brand")) SIDE_FILTERS[side].brand = e.target.value;
  if (e.target.classList.contains("filter-depth")) SIDE_FILTERS[side].depth = e.target.value;
  if (e.target.classList.contains("filter-thickness")) SIDE_FILTERS[side].thickness = e.target.value;
  if (e.target.classList.contains("filter-name")) SIDE_FILTERS[side].name = e.target.value;

  applyFilters(side);
});

modal.addEventListener("shown.bs.modal", async () => {
  buildSidesHTML();
  await loadEdgebandData();
});

modal.addEventListener("hidden.bs.modal", resetModal);
/* ============================================================
     BRIDGE EXPORTS: Make these visible to the main UI script
     ============================================================ */
  window.getEdgebandModalState = function() {
    const finalState = {};
    SIDES.forEach(side => {
      // Check if the side is actually toggled "ON"
      if (SIDE_STATE[side]) {
        finalState[side] = {
          default: SIDE_DEFAULT[side],
          whitelist: Array.from(SIDE_WHITELIST[side]) // Convert Set to Array
        };
      } else {
        finalState[side] = { default: null, whitelist: [] };
      }
    });
    return finalState;
  };

  // Allow the main UI to look up names for the table
  window.getEdgebandNames = () => EDGEBAND_NAMES;
  window.getEdgebandBands = () => EDGEBANDS;

})();