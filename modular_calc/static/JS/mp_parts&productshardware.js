
/* ============================================================
   HARDWARE DATA STRUCTURE
   ============================================================ */
selected.partHardware = {};        // {id: { qty, condition }}
selected.productHardware = {};     // {id: { qty, condition }}


/* ============================================================
   OPEN MODALS
   ============================================================ */
window.openHardwareModal = function () {
    renderPartHardwareTable();
    renderPartSummary();
    new bootstrap.Modal(document.getElementById("hardwareModal")).show();
};

window.openProductHardwareModal = function () {
    renderProductHardwareTable();
    renderProductSummary();
    new bootstrap.Modal(document.getElementById("productHardwareModal")).show();
};


/* ============================================================
   FILTER INITIALIZATION
   ============================================================ */
function initHardwareFilters() {

    const groups = [...new Set(allData.hardware.map(h => h.h_group?.name).filter(Boolean))];
    const names  = [...new Set(allData.hardware.map(h => h.h_name).filter(Boolean))];

    // Populate all dropdowns
    document.querySelectorAll(".filter-hw-group").forEach(sel => {
        sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
        groups.forEach(g => sel.appendChild(new Option(g, g)));
    });

    document.querySelectorAll(".filter-hw-name").forEach(sel => {
        sel.querySelectorAll("option:not(:first-child)").forEach(o => o.remove());
        names.forEach(n => sel.appendChild(new Option(n, n)));
    });

    // Bind change events
    document.querySelectorAll(".filter-hw-group, .filter-hw-name")
        .forEach(sel => sel.addEventListener("change", e => {
            const type = e.target.dataset.type;
            if (type === "part") renderPartHardwareTable();
            else renderProductHardwareTable();
        }));
}


/* ============================================================
   PART HARDWARE TABLE
   ============================================================ */
function renderPartHardwareTable() {
    const tbody = document.getElementById("part-hardware-body");
    tbody.innerHTML = "";

    const group = document.querySelector('.filter-hw-group[data-type="part"]').value;
    const name  = document.querySelector('.filter-hw-name[data-type="part"]').value;

    let filtered = allData.hardware.filter(h =>
        (!group || h.h_group?.name === group) &&
        (!name || h.h_name === name)
    );

    filtered.forEach(h => {
        const selectedRow = selected.partHardware[h.id] || null;

        tbody.innerHTML += `
            <tr>
                <td>${h.h_name}</td>

                <td>
                    <input type="text" class="form-control form-control-sm part-qty"
                           data-id="${h.id}"
                           placeholder="Qty or Equation"
                           value="${selectedRow ? selectedRow.qty : ""}"
                           style="display:${selectedRow ? "block" : "none"}">
                </td>

                <td>
                    <input type="text" class="form-control form-control-sm part-cond"
                           data-id="${h.id}"
                           placeholder="Condition"
                           value="${selectedRow ? selectedRow.condition : ""}"
                           style="display:${selectedRow ? "block" : "none"}">
                </td>

                <td>
                    <input type="checkbox" class="form-check-input part-select"
                           data-id="${h.id}" ${selectedRow ? "checked" : ""}>
                </td>
            </tr>
        `;
    });
}


/* ============================================================
   PRODUCT HARDWARE TABLE
   ============================================================ */
function renderProductHardwareTable() {
    const tbody = document.getElementById("product-hardware-body");
    tbody.innerHTML = "";

    const group = document.querySelector('.filter-hw-group[data-type="product"]').value;
    const name  = document.querySelector('.filter-hw-name[data-type="product"]').value;

    let filtered = allData.hardware.filter(h =>
        (!group || h.h_group?.name === group) &&
        (!name || h.h_name === name)
    );

    filtered.forEach(h => {
        const selectedRow = selected.productHardware[h.id] || null;

        tbody.innerHTML += `
            <tr>
                <td>${h.h_name}</td>

                <td>
                    <input type="text" class="form-control form-control-sm product-qty"
                           data-id="${h.id}"
                           placeholder="Qty or Equation"
                           value="${selectedRow ? selectedRow.qty : ""}"
                           style="display:${selectedRow ? "block" : "none"}">
                </td>

                <td class="text-center">
                    <input type="checkbox" class="form-check-input product-select"
                           data-id="${h.id}" ${selectedRow ? "checked" : ""}>
                </td>
            </tr>
        `;
    });

    attachProductHardwareEvents();
}


/* ============================================================
   PRODUCT HARDWARE EVENTS
   ============================================================ */
function attachProductHardwareEvents() {

    document.querySelectorAll(".product-select").forEach(cb => {
        cb.onchange = function () {
            const id = this.dataset.id;
            const qtyInput = document.querySelector(`.product-qty[data-id="${id}"]`);

            if (this.checked) {
                qtyInput.style.display = "block";
                selected.productHardware[id] = {
                    qty: qtyInput.value || "",
                    condition: ""     // Product hardware has condition field available later
                };
            } else {
                qtyInput.style.display = "none";
                delete selected.productHardware[id];
            }

            renderProductSummary();
        };
    });

    document.querySelectorAll(".product-qty").forEach(input => {
        input.oninput = function () {
            const id = this.dataset.id;
            if (selected.productHardware[id]) selected.productHardware[id].qty = this.value;
            renderProductSummary();
        };
    });
}


/* ============================================================
   SUMMARY SECTIONS
   ============================================================ */
function renderPartSummary() {
    const div = document.getElementById("selected-part-hardware");
    div.innerHTML = "";

    Object.entries(selected.partHardware).forEach(([id, obj]) => {
        const hw = allData.hardware.find(h => h.id == id);
        div.innerHTML += `
            <div>✔ <b>${hw.h_name}</b> → Qty: ${obj.qty || "-"} | Cond: ${obj.condition || "-"}</div>
        `;
    });
}

function renderProductSummary() {
    const div = document.getElementById("selected-product-hardware");
    div.innerHTML = "";

    Object.entries(selected.productHardware).forEach(([id, obj]) => {
        const hw = allData.hardware.find(h => h.id == id);
        div.innerHTML += `
            <div>✔ <b>${hw.h_name}</b> → Qty: ${obj.qty || "-"}</div>
        `;
    });
}


/* ============================================================
   SAVE BUTTONS
   ============================================================ */
document.getElementById("save-part-hardware-btn").addEventListener("click", () => {
    document.dispatchEvent(new CustomEvent("partHardwareSaved", { detail: selected.partHardware }));
    bootstrap.Modal.getInstance(document.getElementById("hardwareModal")).hide();
});

document.getElementById("save-product-hardware-btn").addEventListener("click", () => {
    document.dispatchEvent(new CustomEvent("productHardwareSaved", { detail: selected.productHardware }));
    bootstrap.Modal.getInstance(document.getElementById("productHardwareModal")).hide();
});

