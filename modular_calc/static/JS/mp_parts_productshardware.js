/* ============================================================
   PRODUCT HARDWARE LOGIC (In-Memory Version)
============================================================ */

/**
 * Global Initialization
 */
function initProductHardwareAccordion() {
    const $groupSel = $('#prod-hw-filter-group');
    if (!$groupSel.length) return;

    const populate = () => {
        // Fetch groups from global cache (populated by fetchReferenceData)
        const groups = window.hardwareGroupsCache || [];
        
        // If data hasn't arrived from API yet, don't break Select2
        if (groups.length === 0) {
            console.warn("⚠️ Hardware Groups not loaded yet...");
            return;
        }

        if ($groupSel.data('select2')) { $groupSel.select2('destroy'); }

        let html = '<option value="">All Hardware Groups</option>';
        groups.forEach(g => {
            // Adjust g.id and g.name to match your API response fields
            html += `<option value="${g.id}">${g.name}</option>`;
        });
        $groupSel.html(html);

        $groupSel.select2({
            placeholder: "Filter by Group",
            allowClear: true,
            width: '100%',
            dropdownParent: $('#collapseProductHardware')
        }).on('change.select2', renderProductHardwareTable);

        renderProductHardwareTable();
    };

    // Trigger on first load
    populate();
    
    // Re-trigger when accordion expands (fixes Select2 zero-width bug)
    $('#collapseProductHardware').on('shown.bs.collapse', populate);
}

/**
 * Main Table Renderer
 */
function renderProductHardwareTable() {
    const tbody = document.getElementById("product-hardware-body");
    if (!tbody) return;

    // Safety check for Global State
    if (!window.productSubmissionState) {
        window.productSubmissionState = { parameters: [], parts: [], product_hardware: [] };
    }
    if (!window.productSubmissionState.product_hardware) {
        window.productSubmissionState.product_hardware = [];
    }

    const catalog = window.hardwareCache || [];
    const searchVal = ($('#prod-hw-search').val() || "").toLowerCase();
    const groupVal = $('#prod-hw-filter-group').val() || "";
    const selectedList = window.productSubmissionState.product_hardware;

    // Filter logic
    const filtered = catalog.filter(h => {
        // Match against h_name and h_group (standard Django field naming)
        const matchesSearch = !searchVal || (h.h_name && h.h_name.toLowerCase().includes(searchVal));
        const matchesGroup = !groupVal || String(h.h_group) === String(groupVal);
        return matchesSearch && matchesGroup;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">
            ${catalog.length === 0 ? '📡 Loading catalog...' : '🔍 No hardware matches filters.'}
        </td></tr>`;
        updateProductHardwareUI();
        return;
    }

    tbody.innerHTML = filtered.map(h => {
        const entry = selectedList.find(item => Number(item.hardware) === Number(h.id));
        const isChecked = !!entry;

        const groupObj = window.hardwareGroupsCache?.find(g => String(g.id) === String(h.h_group));
        const groupLabel = groupObj ? groupObj.name : 'General';

        return `
            <tr class="${isChecked ? 'table-info' : ''} align-middle">
                <td class="text-center">
                    <input type="checkbox" class="form-check-input" 
                        ${isChecked ? 'checked' : ''} 
                        onclick="window.toggleProductHardware(${h.id})">
                </td>
                <td>
                    <div class="fw-bold small">${h.h_name}</div>
                    <div class="text-muted" style="font-size:0.7rem;">${groupLabel} | ${h.code || 'No Code'}</div>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm font-monospace hw-smart-input" 
                        placeholder="Qty" value="${entry ? entry.quantity_equation : '1'}"
                        ${!isChecked ? 'disabled' : ''}
                        onfocus="window.applySmartEngine(this)"
                        onblur="window.validateAndCommit(this, (v) => { window.commitProductHardware(${h.id}, 'qty', v) })">
                </td>
                <td>
                <input type="text" class="form-control form-control-sm hw-smart-input" 
                    placeholder="Condition" value="${entry ? entry.condition_expression : ''}"
                    ${!isChecked ? 'disabled' : ''}
                    onfocus="window.applySmartEngine(this)"
                    onblur="window.validateAndCommit(this, (v) => { window.commitProductHardware(${h.id}, 'condition', v) })">
                </td>
            </tr>`;
    }).join("");

    updateProductHardwareUI();
}

/**
 * Global State Modifiers
 */
window.toggleProductHardware = function(id) {
    const hwList = window.productSubmissionState.product_hardware;
    const targetId = Number(id);
    const idx = hwList.findIndex(item => Number(item.hardware) === targetId);

    if (idx > -1) {
        hwList.splice(idx, 1);
    } else {
        hwList.push({
            hardware: targetId,
            quantity_equation: "1",
            condition_expression: ""
        });
    }
    renderProductHardwareTable();
};

window.updateProductHardwareEntry = function(id, field, value) {
    const item = window.productSubmissionState.product_hardware.find(h => Number(h.hardware) === Number(id));
    if (item) {
        if (field === 'qty') item.quantity_equation = value;
        if (field === 'condition') item.condition_expression = value;
        if (window.validateExpressionStatic && inputElement) {
            const result = window.validateExpressionStatic(value);
            updateValidationUI(inputElement, result);
        }
    }
};

function updateProductHardwareUI() {
    const count = window.productSubmissionState.product_hardware?.length || 0;
    const badge = document.getElementById("prod-hw-badge");
    const counterText = document.getElementById("prod-hw-count");
    
    if (badge) {
        badge.innerText = count;
        count > 0 ? badge.classList.remove("d-none") : badge.classList.add("d-none");
    }
    if (counterText) counterText.innerText = `${count} items selected`;
}

window.clearProductHardware = function() {
    if (confirm("Are you sure you want to clear all product hardware selections?")) {
        window.productSubmissionState.product_hardware = [];
        renderProductHardwareTable();
    }
}
// Initialize caches
window.hardwareCache = [];
window.hardwareGroupsCache = [];

async function fetchHardwareCatalog() {
    try {
        const [hwRes, grpRes] = await Promise.all([
            fetch('/material/v1/hardware/'), 
            fetch('/material/v1/hardware-groups/') 
        ]);

        const hwData = await hwRes.json();
        const grpData = await grpRes.json();

        // FIX: Grab the 'results' array from the paginated response
        window.hardwareCache = hwData.results || []; 
        
        // Groups usually aren't paginated, but check if they follow the same pattern
        window.hardwareGroupsCache = grpData.results || grpData || [];

        console.log("📦 Hardware Results Loaded:", window.hardwareCache);

        renderProductHardwareTable();
        initProductHardwareAccordion();
    } catch (e) {
        console.error("❌ Failed to load hardware catalog", e);
        window.hardwareCache = []; 
    }
}

document.addEventListener('DOMContentLoaded', fetchHardwareCatalog);