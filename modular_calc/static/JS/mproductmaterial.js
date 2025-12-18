// Open Material Modal
window.openMaterialModal = function(initialSelection) {
    initialSelection = initialSelection || { whitelist: [], defaultMaterial: null };

    if (!allData.materials || !allData.materials.length) {
        console.warn("[MODAL-DEBUG] Materials data not loaded yet, retrying in 100ms");
        setTimeout(() => openMaterialModal(initialSelection), 100);
        return;
    }

    console.log("[MODAL-DEBUG] Opening materialModal", initialSelection);

    // Preselect whitelist
    selected.materials = allData.materials.filter(m => 
        initialSelection.whitelist && initialSelection.whitelist.includes(m.id)
    );

    // Preselect default material
    selected.defaultMaterialId = initialSelection.defaultMaterial || null;

    showModal("materialModal");

    updateFiltersAndTable();      // Render filtered table
    renderSelectedMaterials();    // Render selected materials at bottom

    console.log("[MODAL-DEBUG] Preselected whitelist IDs:", selected.materials.map(m => m.id));
    console.log("[MODAL-DEBUG] Preselected default ID:", selected.defaultMaterialId);
};


// Initialize filters
function initMaterialFilters() {
    console.log("[MODAL-DEBUG] Initializing Material Filters");

    fillSelect('filter-material-group', [...new Set(allData.materials.map(m => m.material_grp?.name).filter(Boolean))]);
    fillSelect('filter-material-type', [...new Set(allData.materials.map(m => m.material_type?.name).filter(Boolean))]);
    fillSelect('filter-material-model', [...new Set(allData.materials.map(m => m.material_model?.name).filter(Boolean))]);
    fillSelect('filter-material-brand', [...new Set(allData.materials.map(m => m.brand?.name).filter(Boolean))]);
    fillSelect('filter-material-thickness', [...new Set(allData.materials.map(m => m.thickness).filter(Boolean))]);

    ['filter-material-group','filter-material-type','filter-material-model','filter-material-brand','filter-material-thickness']
        .forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', onFilterChange);
        });
}

// Filter change handler
function onFilterChange(e) {
    const id = e.target.id;
    const groupSelect = document.getElementById('filter-material-group');
    const typeSelect = document.getElementById('filter-material-type');
    const modelSelect = document.getElementById('filter-material-model');

    console.log("[MODAL-DEBUG] Filter changed:", id, e.target.value);

    // Reset dependent filters
    if (id === 'filter-material-group') {
        typeSelect.value = '';
        modelSelect.value = '';
    } else if (id === 'filter-material-type') {
        modelSelect.value = '';
    }

    // Disable/enable dependent filters
    typeSelect.disabled = !groupSelect.value;       // Type disabled if no Group
    modelSelect.disabled = !typeSelect.value;       // Model disabled if no Type

    updateFiltersAndTable();
}

function getMaterialFilterValues() {
    return {
        group: document.getElementById('filter-material-group')?.value || '',
        type: document.getElementById('filter-material-type')?.value || '',
        model: document.getElementById('filter-material-model')?.value || '',
        brand: document.getElementById('filter-material-brand')?.value || '',
        thickness: document.getElementById('filter-material-thickness')?.value || ''
    };
}
// Update table & thickness options
function updateFiltersAndTable() {
    const { group, type, model, brand, thickness } = getMaterialFilterValues();
    let filtered = allData.materials.filter(m =>
        (!group || m.material_grp?.name === group) &&
        (!type || m.material_type?.name === type) &&
        (!model || m.material_model?.name === model) &&
        (!brand || m.brand?.name === brand)
    );

    const thicknessOptions = [...new Set(filtered.map(m => m.thickness).filter(Boolean))];
    fillSelect('filter-material-thickness', thicknessOptions);

    if (thickness && thicknessOptions.includes(thickness)) {
        filtered = filtered.filter(m => m.thickness === thickness);
    }

    renderMaterialTable(filtered);
}

// Render material table
function renderMaterialTable(materials = allData.materials) {
    console.log("[MODAL-DEBUG] Rendering material table", materials.length);

    const tbody = document.getElementById('material-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    materials.forEach(m => {
        const tr = document.createElement('tr');
        tr.dataset.materialId = m.id;

        const isChecked = selected.materials.some(sm => sm.id === m.id);
        const isDefault = selected.defaultMaterialId === m.id;

        tr.innerHTML = `
            <td>${m.name || '(No Name)'}</td>
            <td>${m.thickness || '-'}</td>
            <td>${m.brand?.name || '-'}</td>
            <td><input type="checkbox" class="material-whitelist" data-id="${m.id}" ${isChecked ? 'checked' : ''}></td>
            <td><input type="radio" class="material-default" name="material-default" data-id="${m.id}" ${isDefault ? 'checked' : ''}></td>
        `;

        // Whitelist checkbox
        tr.querySelector('.material-whitelist').addEventListener('change', function() {
            if (this.checked) {
                if (!selected.materials.some(sm => sm.id === m.id)) selected.materials.push(m);
            } else {
                selected.materials = selected.materials.filter(sm => sm.id !== m.id);
                if (selected.defaultMaterialId === m.id) selected.defaultMaterialId = null;
            }
            console.log("[MODAL-DEBUG] Whitelist changed", selected.materials.map(s => s.id));
            renderSelectedMaterials();
        });

        // Default radio
        tr.querySelector('.material-default').addEventListener('change', function() {
            selected.defaultMaterialId = m.id;
            console.log("[MODAL-DEBUG] Default material set:", selected.defaultMaterialId);
            renderSelectedMaterials();
        });

        tbody.appendChild(tr);
    });
}

// Render selected materials at bottom
function renderSelectedMaterials() {
    const container = document.getElementById('selected-materials');
    const defaultContainer = document.getElementById('default-material');
    if (!container || !defaultContainer) return;

    container.innerHTML = '';
    selected.materials.forEach(m => {
        const div = document.createElement('div');
        div.className = 'selected-material-item';
        div.innerHTML = `
            ${m.name || '(No Name)'} - ${m.thickness}mm - ${m.brand?.name || '-'}
            <button type="button" class="btn btn-sm btn-danger remove-selected" data-id="${m.id}">x</button>
        `;
        container.appendChild(div);
    });

    // Remove button
    container.querySelectorAll('.remove-selected').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = parseInt(this.dataset.id);
            selected.materials = selected.materials.filter(sm => sm.id !== id);
            if (selected.defaultMaterialId === id) selected.defaultMaterialId = null;
            console.log("[MODAL-DEBUG] Removed material:", id);
            updateFiltersAndTable();
            renderSelectedMaterials();
        });
    });

    // Show default
    const defaultMat = selected.materials.find(m => m.id === selected.defaultMaterialId);
    defaultContainer.innerHTML = defaultMat ? `${defaultMat.name || '(No Name)'} - ${defaultMat.thickness}mm - ${defaultMat.brand?.name || '-'}` : '(None)';
}

// Save materials
document.getElementById('save-material-btn').addEventListener('click', function() {
    console.log("[MODAL-DEBUG] Saving Materials");

    document.dispatchEvent(new CustomEvent("materialsSaved", {
        detail: {
            whitelist: selected.materials.map(m => m.id),
            defaultMaterial: selected.defaultMaterialId
        }
    }));

    bootstrap.Modal.getInstance(document.getElementById('materialModal')).hide();
});
