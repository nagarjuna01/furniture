// /* ============================================================
//    HARDWARE DATA STRUCTURE
//    ============================================================ */
// selected.partHardware = selected.partHardware || {};        // {id: { qty, condition }}
// selected.productHardware = selected.productHardware || {}; // {id: { qty }}

// console.log("✅ HARDWARE JS EXECUTING");
// /* ============================================================
//    OPEN MODALS
//    ============================================================ */
// window.openHardwareModal = function () {
//     renderPartHardwareTable();
//     renderPartSummary();
//     showModal("hardwareModal");
// };

// window.openProductHardwareModal = function () {
//     renderProductHardwareTable();
//     renderProductSummary();
//     showModal("productHardwareModal");
// };


// /* ============================================================
//    FILTER INITIALIZATION
//    ============================================================ */
// function initHardwareFilters() {

//     const groups = [...new Set(allData.hardware.map(h => h.h_group?.name).filter(Boolean))];
//     const names  = [...new Set(allData.hardware.map(h => h.h_name).filter(Boolean))];

//     document.querySelectorAll(".filter-hw-group").forEach(sel => {
//         sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
//         groups.forEach(g => sel.appendChild(new Option(g, g)));
//     });

//     document.querySelectorAll(".filter-hw-name").forEach(sel => {
//         sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
//         names.forEach(n => sel.appendChild(new Option(n, n)));
//     });

//     document.querySelectorAll(".filter-hw-group, .filter-hw-name")
//         .forEach(sel => sel.addEventListener("change", e => {
//             const type = e.target.dataset.type;
//             if (type === "part") renderPartHardwareTable();
//             else renderProductHardwareTable();
//         }));
// }


// /* ============================================================
//    PART HARDWARE TABLE
//    ============================================================ */
// function renderPartHardwareTable() {
//     const tbody = document.getElementById("part-hardware-body");
//     if (!tbody) return;

//     tbody.innerHTML = "";

//     const group = document.querySelector('.filter-hw-group[data-type="part"]')?.value;
//     const name  = document.querySelector('.filter-hw-name[data-type="part"]')?.value;

//     const filtered = allData.hardware.filter(h =>
//         (!group || h.h_group?.name === group) &&
//         (!name || h.h_name === name)
//     );

//     filtered.forEach(h => {
//         const row = selected.partHardware[h.id];

//         tbody.insertAdjacentHTML("beforeend", `
//             <tr>
//                 <td>${h.h_name}</td>

//                 <td>
//                     <input type="text"
//                            class="form-control form-control-sm part-qty"
//                            data-id="${h.id}"
//                            placeholder="Qty or Equation"
//                            value="${row?.qty || ""}"
//                            style="display:${row ? "block" : "none"}">
//                 </td>

//                 <td>
//                     <input type="text"
//                            class="form-control form-control-sm part-cond"
//                            data-id="${h.id}"
//                            placeholder="Condition"
//                            value="${row?.condition || ""}"
//                            style="display:${row ? "block" : "none"}">
//                 </td>

//                 <td class="text-center">
//                     <input type="checkbox"
//                            class="form-check-input part-select"
//                            data-id="${h.id}" ${row ? "checked" : ""}>
//                 </td>
//             </tr>
//         `);
//     });

//     attachPartHardwareEvents();
// }


// /* ============================================================
//    PART HARDWARE EVENTS (FIXED)
//    ============================================================ */
// function attachPartHardwareEvents() {

//     document.querySelectorAll(".part-select").forEach(cb => {
//         cb.onchange = function () {
//             const id = this.dataset.id;
//             const qty = document.querySelector(`.part-qty[data-id="${id}"]`);
//             const cond = document.querySelector(`.part-cond[data-id="${id}"]`);

//             if (this.checked) {
//                 qty.style.display = "block";
//                 cond.style.display = "block";

//                 selected.partHardware[id] = {
//                     qty: qty.value || "",
//                     condition: cond.value || ""
//                 };
//             } else {
//                 qty.style.display = "none";
//                 cond.style.display = "none";
//                 delete selected.partHardware[id];
//             }

//             renderPartSummary();
//         };
//     });

//     document.querySelectorAll(".part-qty").forEach(input => {
//         input.oninput = function () {
//             const id = this.dataset.id;
//             if (selected.partHardware[id]) {
//                 selected.partHardware[id].qty = this.value;
//             }
//             renderPartSummary();
//         };
//     });

//     document.querySelectorAll(".part-cond").forEach(input => {
//         input.oninput = function () {
//             const id = this.dataset.id;
//             if (selected.partHardware[id]) {
//                 selected.partHardware[id].condition = this.value;
//             }
//             renderPartSummary();
//         };
//     });
// }


// /* ============================================================
//    PRODUCT HARDWARE TABLE
//    ============================================================ */
// function renderProductHardwareTable() {
//     const tbody = document.getElementById("product-hardware-body");
//     if (!tbody) return;

//     tbody.innerHTML = "";

//     const group = document.querySelector('.filter-hw-group[data-type="product"]')?.value;
//     const name  = document.querySelector('.filter-hw-name[data-type="product"]')?.value;

//     const filtered = allData.hardware.filter(h =>
//         (!group || h.h_group?.name === group) &&
//         (!name || `${h.brand?.name} / ${h.h_name}`
// )
//     );

//     filtered.forEach(h => {
//         const row = selected.productHardware[h.id];

//         tbody.insertAdjacentHTML("beforeend", `
//             <tr>
//                 <td>${h.h_name}</td>

//                 <td>
//                     <input type="number"
//                         min="1"
//                         step="1"
//                         class="form-control form-control-sm product-qty"
//                         data-id="${h.id}"
//                         placeholder="Qty"
//                         value="${row?.qty || ""}"
//                         style="display:${row ? "block" : "none"}">
//                 </td>

//                 <td class="text-center">
//                     <input type="checkbox"
//                            class="form-check-input product-select"
//                            data-id="${h.id}" ${row ? "checked" : ""}>
//                 </td>
//             </tr>
//         `);
//     });

//     attachProductHardwareEvents();
// }


// /* ============================================================
//    PRODUCT HARDWARE EVENTS
//    ============================================================ */
// function attachProductHardwareEvents() {

//     document.querySelectorAll(".product-select").forEach(cb => {
//         cb.onchange = function () {
//             const id = this.dataset.id;
//             const qty = document.querySelector(`.product-qty[data-id="${id}"]`);

//             if (this.checked) {
//                 qty.style.display = "block";
//                 selected.productHardware[id] = { qty: qty.value || "" };
//             } else {
//                 qty.style.display = "none";
//                 delete selected.productHardware[id];
//             }

//             renderProductSummary();
//         };
//     });

//     document.querySelectorAll(".product-qty").forEach(input => {
//         input.oninput = function () {
//             const id = this.dataset.id;
//             if (selected.productHardware[id]) {
//                 selected.productHardware[id].qty = this.value;
//             }
//             renderProductSummary();
//         };
//     });
// }


// /* ============================================================
//    SUMMARY SECTIONS
//    ============================================================ */
// function renderPartSummary() {
//     const div = document.getElementById("selected-part-hardware");
//     if (!div) return;

//     div.innerHTML = "";

//     Object.entries(selected.partHardware).forEach(([id, obj]) => {
//         const hw = allData.hardware.find(h => h.id == id);
//         if (!hw) return;

//         div.insertAdjacentHTML("beforeend", `
//             <div>✔ <b>${hw.h_name}</b> → Qty: ${obj.qty || "-"} | Cond: ${obj.condition || "-"}</div>
//         `);
//     });
// }

// function renderProductSummary() {
//     const div = document.getElementById("selected-product-hardware");
//     if (!div) return;

//     div.innerHTML = "";

//     Object.entries(selected.productHardware).forEach(([id, obj]) => {
//         const hw = allData.hardware.find(h => h.id == id);
//         if (!hw) return;

//         div.insertAdjacentHTML("beforeend", `
//             <div>✔ <b>${hw.h_name}</b> → Qty: ${obj.qty || "-"}</div>
//         `);
//     });
// }


// /* ============================================================
//    SAVE BUTTONS
//    ============================================================ */
// document.getElementById("save-part-hardware-btn")?.addEventListener("click", () => {

//     const payload = Object.entries(selected.partHardware).map(([id, obj]) => ({
//         hardware: parseInt(id),
//         quantity_equation: obj.qty || "1",
//         applicability_condition: obj.condition || ""
//     }));

//     console.log("[PART HW PAYLOAD]", payload);

//     document.dispatchEvent(new CustomEvent("partHardwareSaved", {
//         detail: payload
//     }));

//     hideModal("hardwareModal");
// });


// document.getElementById("save-product-hardware-btn")?.addEventListener("click", () => {

//     const payload = Object.entries(selected.productHardware).map(([id, obj]) => ({
//         hardware: parseInt(id),
//         quantity: parseInt(obj.qty || 1)
//     }));

//     console.log("[PRODUCT HW PAYLOAD]", payload);

//     document.dispatchEvent(new CustomEvent("productHardwareSaved", {
//         detail: payload
//     }));

//     hideModal("productHardwareModal");
// });
/* ============================================================
   GLOBAL STATE
   ============================================================ */
let hardwareCache = []; // fetched from API

if (!window.selected) window.selected = {};
if (!window.selected.productHardware) window.selected.productHardware = {};

selected.partHardware = selected.partHardware || {};        // {id: { qty, condition }}


console.log("✅ HARDWARE JS LOADED");


/* ============================================================
   HELPERS
   ============================================================ */
function isIntegerUnit(unit) {
    return ["/SET", "/PCS"].includes(unit);
}

function getProductQtyInputAttrs(unit) {
    if (isIntegerUnit(unit)) {
        return `type="number" min="1" step="1"`;
    }
    return `type="number" min="0" step="0.01"`;
}


/* ============================================================
   API FETCH
   ============================================================ */
async function loadHardwareFromAPI() {
    try {
        const res = await fetch("/material/v1/hardware/");
        if (!res.ok) throw new Error(res.status);

        const data = await res.json();
        hardwareCache = data.results || [];

        console.log("✅ Hardware fetched:", hardwareCache);
        initHardwareFilters();
    } catch (err) {
        console.error("❌ Failed to load hardware", err);
    }
}


/* ============================================================
   OPEN MODALS
   ============================================================ */
window.openHardwareModal = async function () {
    if (!hardwareCache.length) await loadHardwareFromAPI();
    renderPartHardwareTable();
    renderPartSummary();
    showModal("hardwareModal");
};

window.openProductHardwareModal = async function () {
    if (!hardwareCache.length) await loadHardwareFromAPI();
    renderProductHardwareTable();
    renderProductSummary();
    showModal("productHardwareModal");
};


/* ============================================================
   FILTER INITIALIZATION
   ============================================================ */
function initHardwareFilters() {

    const groups = [...new Set(hardwareCache.map(h => h.h_group_label).filter(Boolean))];
    const names  = [...new Set(hardwareCache.map(h => h.h_name).filter(Boolean))];

    document.querySelectorAll(".filter-hw-group").forEach(sel => {
        sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
        groups.forEach(g => sel.appendChild(new Option(g, g)));
    });

    document.querySelectorAll(".filter-hw-name").forEach(sel => {
        sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
        names.forEach(n => sel.appendChild(new Option(n, n)));
    });

    document.querySelectorAll(".filter-hw-group, .filter-hw-name")
        .forEach(sel => sel.onchange = e => {
            const type = e.target.dataset.type;
            type === "part" ? renderPartHardwareTable() : renderProductHardwareTable();
        });
}


/* ============================================================
   PART HARDWARE TABLE
   ============================================================ */
function renderPartHardwareTable() {
    const tbody = document.getElementById("part-hardware-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    const group = document.querySelector('.filter-hw-group[data-type="part"]')?.value;
    const name  = document.querySelector('.filter-hw-name[data-type="part"]')?.value;

    hardwareCache
        .filter(h =>
            (!group || h.h_group_label === group) &&
            (!name || h.h_name === name)
        )
        .forEach(h => {
            const row = selected.partHardware[h.id];

            tbody.insertAdjacentHTML("beforeend", `
                <tr data-id="${h.id}">
                    <td class="text-center">
                        <input type="checkbox"
                               class="form-check-input part-select"
                               data-id="${h.id}" 
                               data-name="${h.h_name}" 
                               ${row ? "checked" : ""}>
                    </td>

                    <td class="align-middle fw-bold small">${h.h_name}</td>

                    <td class="align-middle">
                        <span class="badge bg-light text-dark border">${h.billing_unit_code || ""}</span>
                    </td>

                    <td>
                        <div class="input-group input-group-sm">
                            <input type="text"
                                   class="form-control part-qty font-monospace"
                                   data-id="${h.id}"
                                   placeholder="Qty / Equation"
                                   value="${row?.qty || "1"}"
                                   style="display:${row ? "block" : "block"}">
                        </div>
                    </td>

                    <td>
                        <input type="text"
                               class="form-control form-control-sm part-cond font-monospace"
                               data-id="${h.id}"
                               placeholder="Condition"
                               value="${row?.condition || ""}"
                               style="display:${row ? "block" : "block"}">
                    </td>
                </tr>
            `);
        });

    attachPartHardwareEvents();
}

/* ============================================================
   PART HARDWARE EVENTS
   ============================================================ */
function attachPartHardwareEvents() {

    document.querySelectorAll(".part-select").forEach(cb => {
        cb.onchange = function () {
            const id = this.dataset.id;
            const qty = document.querySelector(`.part-qty[data-id="${id}"]`);
            const cond = document.querySelector(`.part-cond[data-id="${id}"]`);

            if (this.checked) {
                qty.style.display = "block";
                cond.style.display = "block";
                selected.partHardware[id] = {
                    qty: qty.value || "",
                    condition: cond.value || ""
                };
            } else {
                qty.style.display = "none";
                cond.style.display = "none";
                delete selected.partHardware[id];
            }

            renderPartSummary();
        };
    });

    document.querySelectorAll(".part-qty").forEach(input => {
        input.oninput = function () {
            const id = this.dataset.id;
            if (selected.partHardware[id]) {
                selected.partHardware[id].qty = this.value;
            }
            renderPartSummary();
        };
    });

    document.querySelectorAll(".part-cond").forEach(input => {
        input.oninput = function () {
            const id = this.dataset.id;
            if (selected.partHardware[id]) {
                selected.partHardware[id].condition = this.value;
            }
            renderPartSummary();
        };
    });
}


/* ============================================================
   PRODUCT HARDWARE TABLE
   ============================================================ */
function renderProductHardwareTable() {
    const tbody = document.getElementById("product-hardware-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    const group = document.querySelector('.filter-hw-group[data-type="product"]')?.value;
    const name  = document.querySelector('.filter-hw-name[data-type="product"]')?.value;

    hardwareCache
        .filter(h =>
            (!group || h.h_group_label === group) &&
            (!name || h.h_name === name)
        )
        .forEach(h => {
            // Check if this hardware is already saved in our state
            const rowState = window.selected.productHardware[h.id];

            tbody.insertAdjacentHTML("beforeend", `
                <tr data-id="${h.id}">
                    <td class="text-center">
                        <input type="checkbox"
                               class="form-check-input product-select"
                               data-id="${h.id}" 
                               data-name="${h.h_name}" 
                               ${rowState ? "checked" : ""}>
                    </td>

                    <td class="align-middle">
                        <span class="fw-bold small">${h.h_name}</span>
                    </td>

                    <td class="align-middle">
                        <span class="badge bg-light text-dark border">${h.billing_unit_code || "pcs"}</span>
                    </td>

                    <td>
                        <div class="input-group input-group-sm">
                            <input type="text" 
                                   class="form-control product-qty font-monospace"
                                   data-id="${h.id}"
                                   placeholder="Qty or Equation"
                                   value="${rowState?.qty || "1"}"
                                   style="display:${rowState ? "block" : "block"}"> 
                            
                            <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                <i class="bi bi-magic"></i>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPreset(this, 'range')">Range Logic</a></li>
                                <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPreset(this, 'step')">Step Logic</a></li>
                            </ul>
                        </div>
                    </td>
                </tr>
            `);
        });

    attachProductHardwareEvents();
}

/* ============================================================
   PRODUCT HARDWARE EVENTS (UNIT ENFORCED)
   ============================================================ */
function attachProductHardwareEvents() {

    document.querySelectorAll(".product-select").forEach(cb => {
        cb.onchange = function () {
            const id = this.dataset.id;
            const qty = document.querySelector(`.product-qty[data-id="${id}"]`);

            if (this.checked) {
                qty.style.display = "block";
                selected.productHardware[id] = { qty: qty.value || "" };
            } else {
                qty.style.display = "none";
                delete selected.productHardware[id];
            }

            renderProductSummary();
        };
    });

    document.querySelectorAll(".product-qty").forEach(input => {
        input.oninput = function () {
            const id = this.dataset.id;
            const hw = hardwareCache.find(h => h.id == id);
            if (!hw || !selected.productHardware[id]) return;

            if (isIntegerUnit(hw.billing_unit_code)) {
                this.value = this.value.replace(/\D/g, "");
            }

            selected.productHardware[id].qty = this.value;
            renderProductSummary();
        };
    });
}


/* ============================================================
   SUMMARY
   ============================================================ */
function renderPartSummary() {
    const div = document.getElementById("selected-part-hardware");
    if (!div) return;

    div.innerHTML = "";

    Object.entries(selected.partHardware).forEach(([id, obj]) => {
        const hw = hardwareCache.find(h => h.id == id);
        if (!hw) return;

        div.insertAdjacentHTML("beforeend", `
            <div>
                ✔ <b>${hw.h_name}</b>
                → Qty: ${obj.qty || "-"} ${hw.billing_unit_code || ""}
                | Cond: ${obj.condition || "-"}
            </div>
        `);
    });
}

function renderProductSummary() {
    const div = document.getElementById("selected-product-hardware");
    if (!div) return;

    div.innerHTML = "";

    Object.entries(selected.productHardware).forEach(([id, obj]) => {
        const hw = hardwareCache.find(h => h.id == id);
        if (!hw) return;

        div.insertAdjacentHTML("beforeend", `
            <div>
                ✔ <b>${hw.h_name}</b>
                → Qty: ${obj.qty || "-"} ${hw.billing_unit_code || ""}
            </div>
        `);
    });
}


/* ============================================================
   SAVE EVENTS
   ============================================================ */
document.getElementById("save-part-hardware-btn")?.addEventListener("click", () => {

    const payload = Object.entries(selected.partHardware).map(([id, obj]) => ({
        hardware: Number(id),
        quantity_equation: obj.qty || "1",
        applicability_condition: obj.condition || ""
    }));

    console.log("✅ PART HW PAYLOAD", payload);
    document.dispatchEvent(new CustomEvent("partHardwareSaved", { detail: payload }));
    hideModal("hardwareModal");
});

document.getElementById("save-product-hardware-btn")?.addEventListener("click", () => {
    // 1. Initialize the global object
    if (!window.selected) window.selected = {};
    window.selected.productHardware = {};

    // 2. Select the rows in your table
    const rows = document.querySelectorAll("#product-hardware-body tr");
    
    rows.forEach((row) => {
        // MATCHING YOUR ACTUAL DOM: 'product-select'
        const checkbox = row.querySelector(".product-select");
        
        if (checkbox && checkbox.checked) {
            const id = checkbox.dataset.id;
            const name = checkbox.dataset.name;
            
            // MATCHING YOUR ACTUAL DOM: 'product-qty'
            const qtyInput = row.querySelector(".product-qty");

            if (id) {
                window.selected.productHardware[id] = {
                    name: name || `Hardware ${id}`,
                    qty: qtyInput ? qtyInput.value : "1"
                };
            }
        }
    });

    console.log("✅ Final State Synced:", window.selected.productHardware);

    // 3. Refresh the Right Column
    if (typeof renderProductHardwareSummary === "function") {
        renderProductHardwareSummary();
    }

    // 4. Close Modal
    const modalEl = document.getElementById('productHardwareModal');
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) modalInstance.hide();
});

function createHardwareRow(hw) {
    return `
    <tr>
        <td>
            <input type="checkbox" class="form-check-input hw-select" 
                   data-id="${hw.id}" 
                   data-name="${hw.name}">
        </td>
        <td class="small fw-bold">${hw.name}</td>
        <td><span class="badge bg-light text-dark border">${hw.unit || 'pcs'}</span></td>
        <td>
            <div class="input-group input-group-sm">
                <input type="text" class="form-control hw-qty-input font-monospace" 
                       value="1">
                </div>
        </td>
    </tr>`;
}