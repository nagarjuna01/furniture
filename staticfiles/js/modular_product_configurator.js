// products/static/js/modular_product_configurator.js

$(document).ready(function() {
    // --- DOM Elements ---
    const $productTitle = $('#productTitle');
    const $productName = $('#productName');
    const $productDescription = $('#productDescription');
    const $productPrice = $('#productPrice');
    const $productCategory = $('#productCategory');
    const $productType = $('#productType');
    const $productModel = $('#productModel');
    const $productBrand = $('#productBrand');
    const $productImage = $('#productImage');
    const $totalLength = $('#totalLength');
    const $totalWidth = $('#totalWidth');
    const $totalDepth = $('#totalDepth');
    const $lengthMin = $('#lengthMin');
    const $lengthMax = $('#lengthMax');
    const $widthMin = $('#widthMin');
    const $widthMax = $('#widthMax');
    const $heightMin = $('#heightMin');
    const $heightMax = $('#heightMax');
    const $threedModel = $('#threedModel');
    const $threedConfig = $('#threedConfig');

    const $modulesList = $('#modulesList');
    const $addModuleBtn = $('#addModuleBtn');

    const $constraintsList = $('#constraintsList');
    const $addConstraintBtn = $('#addConstraintBtn');

    const $materialOverridesList = $('#materialOverridesList');
    const $addMaterialOverrideBtn = $('#addMaterialOverrideBtn');

    const $calcLength = $('#calcLength');
    const $calcWidth = $('#calcWidth');
    const $calcDepth = $('#calcDepth');
    const $calculateLiveCostBtn = $('#calculateLiveCostBtn');
    const $calculationStatus = $('#calculationStatus');
    const $calculatedPurchaseCost = $('#calculatedPurchaseCost');
    const $calculatedSellingPrice = $('#calculatedSellingPrice');
    const $calculatedBreakEvenAmount = $('#calculatedBreakEvenAmount');
    const $calculatedProfitMargin = $('#calculatedProfitMargin');
    const $calculationSpinner = $('#calculation-tab .loading-spinner'); // Specific spinner for calculation tab

    const $saveProductBtn = $('#saveProductBtn');
    const $saveStatus = $('#saveStatus');
    const $saveSpinner = $('#saveProductBtn .loading-spinner'); // Specific spinner for save button

     const CSRF_TOKEN = $('meta[name="csrf-token"]').attr('content');
    // --- Data Storage (for tracking added/removed items) ---
    // These will store objects with `id` for existing, `_is_new` for new, `_is_deleted` for marked for deletion
    let modularProductModules = [];
    let constraints = [];
    let materialOverrides = [];

    // --- Helper Functions ---

    // Function to generate unique IDs for new dynamically added rows (for internal tracking)
    let nextUniqueId = 0;
    function getUniqueTempId() {
        return `temp_${nextUniqueId++}`;
    }

    // Function to render a single Module row
    function renderModuleRow(moduleData = {}) {
        const uniqueId = moduleData.id || getUniqueTempId();
        const isNew = !moduleData.id;
        const moduleOptions = ALL_MODULES.map(m =>
            `<option value="${m.id}" ${m.id === moduleData.module?.id ? 'selected' : ''}>${m.name}</option>`
        ).join('');

        const rowHtml = `
            <div class="form-row module-row" data-id="${uniqueId}" data-is-new="${isNew}">
                <input type="hidden" class="module-id" value="${moduleData.id || ''}">
                <div class="form-group">
                    <label for="module-select-${uniqueId}" class="form-label">Module</label>
                    <select id="module-select-${uniqueId}" class="form-select module-select" required>
                        <option value="">Select a Module</option>
                        ${moduleOptions}
                    </select>
                </div>
                <div class="form-group">
                    <label for="module-quantity-${uniqueId}" class="form-label">Quantity</label>
                    <input type="number" id="module-quantity-${uniqueId}" class="form-control module-quantity" value="${moduleData.quantity || 1}" min="1" required>
                </div>
                 <div class="form-group">
                    <label for="module-posx-${uniqueId}" class="form-label">Pos X</label>
                    <input type="number" id="module-posx-${uniqueId}" class="form-control module-posx" value="${moduleData.position_x || 0}" step="0.01">
                </div>
                <div class="form-group">
                    <label for="module-posy-${uniqueId}" class="form-label">Pos Y</label>
                    <input type="number" id="module-posy-${uniqueId}" class="form-control module-posy" value="${moduleData.position_y || 0}" step="0.01">
                </div>
                <div class="form-group">
                    <label for="module-posz-${uniqueId}" class="form-label">Pos Z</label>
                    <input type="number" id="module-posz-${uniqueId}" class="form-control module-posz" value="${moduleData.position_z || 0}" step="0.01">
                </div>
                <div class="form-group">
                    <label for="module-orientroll-${uniqueId}" class="form-label">Roll</label>
                    <input type="number" id="module-orientroll-${uniqueId}" class="form-control module-orientroll" value="${moduleData.orientation_roll || 0}" step="0.01">
                </div>
                <div class="form-group">
                    <label for="module-orientpitch-${uniqueId}" class="form-label">Pitch</label>
                    <input type="number" id="module-orientpitch-${uniqueId}" class="form-control module-orientpitch" value="${moduleData.orientation_pitch || 0}" step="0.01">
                </div>
                <div class="form-group">
                    <label for="module-orientyaw-${uniqueId}" class="form-label">Yaw</label>
                    <input type="number" id="module-orientyaw-${uniqueId}" class="form-control module-orientyaw" value="${moduleData.orientation_yaw || 0}" step="0.01">
                </div>
                <button type="button" class="btn btn-danger remove-module-btn">Remove</button>
            </div>
        `;
        const $row = $(rowHtml);
        $modulesList.append($row);
        $row.find('.remove-module-btn').on('click', function() {
            removeDynamicRow($row, modularProductModules);
        });
        if (isNew) {
            modularProductModules.push({ _temp_id: uniqueId, _is_new: true, quantity: 1, position_x: 0, position_y: 0, position_z: 0, orientation_roll:0, orientation_pitch:0, orientation_yaw:0});
        }
    }

    // Function to render a single Constraint row
    function renderConstraintRow(constraintData = {}) {
        const uniqueId = constraintData.id || getUniqueTempId();
        const isNew = !constraintData.id;
        const rowHtml = `
            <div class="form-row constraint-row" data-id="${uniqueId}" data-is-new="${isNew}">
                <input type="hidden" class="constraint-id" value="${constraintData.id || ''}">
                <div class="form-group">
                    <label for="constraint-abbr-${uniqueId}" class="form-label">Abbreviation</label>
                    <input type="text" id="constraint-abbr-${uniqueId}" class="form-control constraint-abbr" value="${constraintData.abbreviation || ''}" required>
                </div>
                <div class="form-group">
                    <label for="constraint-value-${uniqueId}" class="form-label">Value</label>
                    <input type="number" id="constraint-value-${uniqueId}" class="form-control constraint-value" value="${constraintData.value || 0}" step="0.01" required>
                </div>
                <button type="button" class="btn btn-danger remove-constraint-btn">Remove</button>
            </div>
        `;
        const $row = $(rowHtml);
        $constraintsList.append($row);
        $row.find('.remove-constraint-btn').on('click', function() {
            removeDynamicRow($row, constraints);
        });
        if (isNew) {
            constraints.push({ _temp_id: uniqueId, _is_new: true, abbreviation: '', value: 0 });
        }
    }

    // Function to render a single Material Override row
    function renderMaterialOverrideRow(overrideData = {}) {
        const uniqueId = overrideData.id || getUniqueTempId();
        const isNew = !overrideData.id;
        const materialOptions = ALL_MODULES.map(m => // Assuming ALL_MODULES has material info or similar for dropdown
            `<option value="${m.material?.id || ''}" ${m.material?.id === overrideData.wooden_material?.id ? 'selected' : ''}>${m.material?.name || 'N/A'}</option>`
        ).join(''); // This needs to be ALL_WOODEN_MATERIALS, not ALL_MODULES. Will fix later.

        // Placeholder for correct material options
        // Assuming we would fetch all WoodenMaterial objects separately if not embedded in modules
        // For now, let's just make a simple dropdown for any ID for demonstration.
        const allMaterials = [
             {id: 1, name: "MDF 18mm"},
             {id: 2, name: "Plywood 12mm"},
             {id: 3, name: "Veneer Oak"},
             // ... populate with actual material data from backend
        ];
        const materialDropdownOptions = allMaterials.map(mat => `<option value="${mat.id}" ${mat.id === overrideData.wooden_material?.id ? 'selected' : ''}>${mat.name}</option>`).join('');

        const rowHtml = `
            <div class="form-row material-override-row" data-id="${uniqueId}" data-is-new="${isNew}">
                <input type="hidden" class="override-id" value="${overrideData.id || ''}">
                <div class="form-group">
                    <label for="material-select-${uniqueId}" class="form-label">Material</label>
                    <select id="material-select-${uniqueId}" class="form-select material-select" required>
                        <option value="">Select a Material</option>
                        ${materialDropdownOptions}
                    </select>
                </div>
                <div class="form-group form-check mt-auto">
                    <input type="checkbox" class="form-check-input material-is-default" id="material-is-default-${uniqueId}" ${overrideData.is_default ? 'checked' : ''}>
                    <label class="form-check-label" for="material-is-default-${uniqueId}">Is Default</label>
                </div>
                <button type="button" class="btn btn-danger remove-override-btn">Remove</button>
            </div>
        `;
        const $row = $(rowHtml);
        $materialOverridesList.append($row);
        $row.find('.remove-override-btn').on('click', function() {
            removeDynamicRow($row, materialOverrides);
        });
        if (isNew) {
            materialOverrides.push({ _temp_id: uniqueId, _is_new: true, wooden_material: null, is_default: false });
        }
    }


    // Generic function to remove a dynamic row and mark for deletion
    function removeDynamicRow($rowElement, dataArray) {
        const id = $rowElement.data('id');
        const isNew = $rowElement.data('is-new') === true; // Convert to boolean

        if (!isNew) {
            // Find the item in the dataArray by its true ID (not temp_id)
            const item = dataArray.find(item => item.id === id);
            if (item) {
                item._is_deleted = true; // Mark for deletion
            }
        }
        // Always remove from display
        $rowElement.remove();
        // For new items, just remove from array
        if (isNew) {
            const index = dataArray.findIndex(item => item._temp_id === id);
            if (index > -1) {
                dataArray.splice(index, 1);
            }
        }
    }


    function loadProductDetails() {
    if (MODULAR_PRODUCT_ID === 0) {
        $productTitle.text('New Modular Product');
        renderModuleRow();
        renderConstraintRow();
        renderMaterialOverrideRow();
        return;
    }

    $saveSpinner.show();
    $.ajax({
        url: MODULAR_PRODUCT_DETAIL_API_URL,
        method: 'GET',
        success: function(data) {
            $productTitle.text(data.name || 'Modular Product');
            $productName.val(data.name || '');
            $productDescription.val(data.description || '');
            $productPrice.val(data.price || '');
            $productCategory.val(data.category || '');
            $productType.val(data.type || '');
            $productModel.val(data.model || '');
            $productBrand.val(data.brand || '');
            $productImage.val(data.image || '');
            $totalLength.val(data.total_length || '');
            $totalWidth.val(data.total_width || '');
            $totalDepth.val(data.total_depth || '');
            $lengthMin.val(data.length_mm_min || '');
            $lengthMax.val(data.length_mm_max || '');
            $widthMin.val(data.width_mm_min || '');
            $widthMax.val(data.width_mm_max || '');
            $heightMin.val(data.height_mm_min || '');
            $heightMax.val(data.height_mm_max || '');
            $threedModel.val(data.threed_model_assembly_file || '');
            $threedConfig.val(data.threed_config_json ? JSON.stringify(data.threed_config_json, null, 2) : '');

            // Safely populate nested lists
            modularProductModules = Array.isArray(data.modular_product_modules)
                ? data.modular_product_modules.map(item => ({ ...item, _is_new: false }))
                : [];

            constraints = Array.isArray(data.constraints)
                ? data.constraints.map(item => ({ ...item, _is_new: false }))
                : [];

            materialOverrides = Array.isArray(data.material_overrides)
                ? data.material_overrides.map(item => ({ ...item, _is_new: false }))
                : [];

            $modulesList.empty();
            modularProductModules.forEach(module => renderModuleRow(module));
            if (modularProductModules.length === 0) renderModuleRow();

            $constraintsList.empty();
            constraints.forEach(constraint => renderConstraintRow(constraint));
            if (constraints.length === 0) renderConstraintRow();

            $materialOverridesList.empty();
            materialOverrides.forEach(override => renderMaterialOverrideRow(override));
            if (materialOverrides.length === 0) renderMaterialOverrideRow();
        },
        error: function(xhr, status, error) {
            $saveStatus
                .removeClass('d-none alert-success')
                .addClass('alert-danger')
                .text('Error loading product details: ' + (xhr.responseJSON ? xhr.responseJSON.detail : error));
        },
        complete: function() {
            $saveSpinner.hide();
        }
    });
}


    // --- Collect All Form Data ---
    function collectFormData() {
        const data = {
            name: $productName.val(),
            description: $productDescription.val(),
            price: parseFloat($productPrice.val()) || 0,
            category: parseInt($productCategory.val()) || null,
            type: parseInt($productType.val()) || null,
            model: parseInt($productModel.val()) || null,
            brand: parseInt($productBrand.val()) || null,
            image: $productImage.val() || null,
            total_length: parseFloat($totalLength.val()) || null,
            total_width: parseFloat($totalWidth.val()) || null,
            total_depth: parseFloat($totalDepth.val()) || null,
            length_mm_min: parseFloat($lengthMin.val()) || null,
            length_mm_max: parseFloat($lengthMax.val()) || null,
            width_mm_min: parseFloat($widthMin.val()) || null,
            width_mm_max: parseFloat($widthMax.val()) || null,
            height_mm_min: parseFloat($heightMin.val()) || null,
            height_mm_max: parseFloat($heightMax.val()) || null,
            threed_model_assembly_file: $threedModel.val() || null,
            threed_config_json: parseJsonSafely($threedConfig.val()),
        };

        data.modular_product_modules = [];
        modularProductModules.forEach(item => { // Iterate through the JavaScript array
    if (item._is_deleted) {
        // If it's an existing item and marked for deletion
        if (item.id) {
            data.modular_product_modules.push({ id: item.id, _destroy: true });
        }
        // If it's a new item marked for deletion, we simply don't include it.
    } else {
        // Only include if a module is selected and it's not deleted
        const $row = $(`div.module-row[data-id="${item.id || item._temp_id}"]`); // Find the corresponding DOM row
        const moduleId = parseInt($row.find('.module-select').val());

        if (moduleId) {
            data.modular_product_modules.push({
                id: item.id || undefined, // Send ID for existing, undefined for new
                module: moduleId,
                quantity: parseInt($row.find('.module-quantity').val()) || 1,
                position_x: parseFloat($row.find('.module-posx').val()) || 0,
                position_y: parseFloat($row.find('.module-posy').val()) || 0,
                position_z: parseFloat($row.find('.module-posz').val()) || 0,
                orientation_roll: parseFloat($row.find('.module-orientroll').val()) || 0,
                orientation_pitch: parseFloat($row.find('.module-orientpitch').val()) || 0,
                orientation_yaw: parseFloat($row.find('.module-orientyaw').val()) || 0,
            });
        }
    }
});
        // Collect constraints
data.constraints = [];
constraints.forEach(item => { // Iterate through the JavaScript array
    if (item._is_deleted) {
        if (item.id) {
            data.constraints.push({ id: item.id, _destroy: true });
        }
    } else {
        const $row = $(`div.constraint-row[data-id="${item.id || item._temp_id}"]`); // Find the corresponding DOM row
        const abbreviation = $row.find('.constraint-abbr').val();

        if (abbreviation) {
            data.constraints.push({
                id: item.id || undefined,
                abbreviation: abbreviation,
                value: parseFloat($row.find('.constraint-value').val()) || 0
            });
        }
    }
});
       // Collect material_overrides
data.material_overrides = [];
materialOverrides.forEach(item => { // Iterate through the JavaScript array
    if (item._is_deleted) {
        if (item.id) {
            data.material_overrides.push({ id: item.id, _destroy: true });
        }
    } else {
        const $row = $(`div.material-override-row[data-id="${item.id || item._temp_id}"]`); // Find the corresponding DOM row
        const materialId = parseInt($row.find('.material-select').val());

        if (materialId) {
            data.material_overrides.push({
                id: item.id || undefined,
                wooden_material: materialId,
                is_default: $row.find('.material-is-default').is(':checked')
            });
        }
    }
});

        return data;
    }

    function parseJsonSafely(jsonString) {
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            return {}; // Return empty object or handle error
        }
    }

    // --- Save Product Configuration ---
    function saveProductConfiguration() {
        const formData = collectFormData();
        const method = MODULAR_PRODUCT_ID === 0 ? 'POST' : 'PATCH';
        const url = MODULAR_PRODUCT_ID === 0 ? MODULAR_PRODUCT_CREATE_API_URL : MODULAR_PRODUCT_DETAIL_API_URL;

        $saveProductBtn.prop('disabled', true);
        $saveSpinner.show();
        $saveStatus.addClass('d-none').removeClass('alert-success alert-danger');

        $.ajax({
            url: url,
            method: method,
            data: JSON.stringify(formData),
            contentType: 'application/json',
             headers: { 'X-CSRFToken': CSRF_TOKEN }, // Uncomment if authentication is enabled
            success: function(data) {
                $saveStatus.removeClass('d-none alert-danger').addClass('alert-success').text('Product configuration saved successfully!');
                if (MODULAR_PRODUCT_ID === 0 && data.id) {
                    // Redirect to the edit page for the newly created product
                    window.location.href = `/products/admin-custom/modular-products/${data.id}/configurator/`;
                } else {
                    // Reload data to ensure frontend reflects backend state after save
                    loadProductDetails();
                }
            },
            error: function(xhr, status, error) {
                const errorMessage = xhr.responseJSON ? JSON.stringify(xhr.responseJSON, null, 2) : error;
                $saveStatus.removeClass('d-none alert-success').addClass('alert-danger').html(`Error saving product: <pre>${errorMessage}</pre>`);
                console.error("Save error:", xhr.responseText);
            },
            complete: function() {
                $saveProductBtn.prop('disabled', false);
                $saveSpinner.hide();
            }
        });
    }

    // --- Live Cost Calculation ---
    function calculateLiveCost() {
        const length = $calcLength.val();
        const width = $calcWidth.val();
        const depth = $calcDepth.val();

        if (!MODULAR_PRODUCT_ID) {
            $calculationStatus.removeClass('d-none alert-info').addClass('alert-danger').text('Please save the product first to enable live calculation.');
            return;
        }
        if (!length || !width || !depth) {
            $calculationStatus.removeClass('d-none alert-info').addClass('alert-danger').text('Please enter Length, Width, and Depth for calculation.');
            return;
        }

        $calculateLiveCostBtn.prop('disabled', true);
        $calculationSpinner.show();
        $calculationStatus.addClass('d-none').removeClass('alert-success alert-danger');

        const constraints = [
            { abbreviation: 'L', value: parseFloat(length) },
            { abbreviation: 'W', value: parseFloat(width) },
            { abbreviation: 'D', value: parseFloat(depth) }
        ];

        $.ajax({
            url: CALCULATE_LIVE_COST_API_URL,
            method: 'POST',
            data: JSON.stringify({ constraints: constraints }),
            contentType: 'application/json',
            headers: { 'X-CSRFToken': CSRF_TOKEN }, // Uncomment if authentication is enabled
            success: function(data) {
                $calculatedPurchaseCost.text(data.calculated_purchase_cost !== undefined ? parseFloat(data.calculated_purchase_cost).toFixed(2) : 'N/A');
                $calculatedSellingPrice.text(data.calculated_selling_price !== undefined ? parseFloat(data.calculated_selling_price).toFixed(2) : 'N/A');
                $calculatedBreakEvenAmount.text(data.break_even_amount !== undefined ? parseFloat(data.break_even_amount).toFixed(2) : 'N/A');
                $calculatedProfitMargin.text(data.profit_margin_percentage !== undefined ? parseFloat(data.profit_margin_percentage).toFixed(2) + '%' : 'N/A');

                $calculationStatus.removeClass('d-none alert-danger').addClass('alert-success').text('Calculation successful!');
            },
            error: function(xhr, status, error) {
                const errorMessage = xhr.responseJSON ? JSON.stringify(xhr.responseJSON, null, 2) : error;
                $calculationStatus.removeClass('d-none alert-success').addClass('alert-danger').html(`Calculation error: <pre>${errorMessage}</pre>`);
                console.error("Calculation error:", xhr.responseText);
            },
            complete: function() {
                $calculateLiveCostBtn.prop('disabled', false);
                $calculationSpinner.hide();
            }
        });
    }


    // --- Event Listeners ---
    $addModuleBtn.on('click', () => renderModuleRow());
    $addConstraintBtn.on('click', () => renderConstraintRow());
    $addMaterialOverrideBtn.on('click', () => renderMaterialOverrideRow());

    $saveProductBtn.on('click', saveProductConfiguration);
    $calculateLiveCostBtn.on('click', calculateLiveCost);

    // Initial load of product data
    loadProductDetails();
});