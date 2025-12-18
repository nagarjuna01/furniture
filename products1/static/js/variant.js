// ---------------- API MAP --------------------
const variantApi = {
    list: productId => `/products1/api/variants/?product=${productId}`,
    detail: id => `/products1/api/variants/${id}/`,
    attributes: '/products1/api/attributes/',
};

console.debug('master_admin.js initialized');
console.debug('showToast loaded:', typeof showToast);


let attributeDefinitions = [];

function loadAttributes() {
    return $.get(variantApi.attributes)
        .done(data => {
            attributeDefinitions = data.results || [];
            console.debug('Loaded attributes:', attributeDefinitions);
        })
        .fail(err => console.error('Failed to load attributes:', err));
}

// Call loadAttributes when the script loads, and make sure any modal opening
// waits for it if it's not guaranteed to be finished.
// For now, assume it completes quickly enough before edit button clicks.
loadAttributes();

// ---------------- DROPDOWN LOADERS --------------
function loadMeasurementUnits() {
    return $.ajax({
        url: '/products1/api/measurement-units/',
        method: 'GET',
    }).done(data => {
        const $select = $('#variant-measurement-unit');
        $select.empty().append('<option value="">Select</option>');
        (data.results || []).forEach(u => {
            $select.append(`<option value="${u.id}">${u.name}</option>`);
        });
    });
}

function loadBillingUnits() {
    return $.ajax({
        url: '/products1/api/billing-units/',
        method: 'GET',
    }).done(data => {
        const $select = $('#variant-billing-unit');
        $select.empty().append('<option value="">Select</option>');
        (data.results || []).forEach(u => {
            $select.append(`<option value="${u.id}">${u.name}</option>`);
        });
    });
}
function loadVariants(productId) {
    console.debug('Loading variants for product:', productId);

    $.get(`/products1/api/products/${productId}/`)
        .done(product => {
            console.debug('Product with variants loaded:', product);

            const html = renderVariantSection(product);
            $(`#variant-section-${productId}`).replaceWith(html);

            // Auto-open the variants section
            $(`#variant-section-${productId}`).collapse('show');
        })
        .fail(err => {
            console.error('Failed to load variants', err);
            showToast('Failed to reload variants', 'danger');
        });
}

// ----------------- VALUE INPUT RENDER ----------------
function renderValueInput(type, choices, val = '') {
    switch (type) {
        case 'choice':
            return `<select name="attribute_value" class="form-select" required>
                <option value="">Select</option>
                ${choices.map(ch => `<option value="${ch}" ${ch == val ? 'selected' : ''}>${ch}</option>`).join('')}
              </select>`;
        case 'boolean':
            // Ensure value comparison for boolean is strict or handles string "true"/"false"
            const isChecked = (val === true || val === 'true');
            return `<div class="form-check">
                <input type="checkbox" name="attribute_value" class="form-check-input" ${isChecked ? 'checked' : ''}>
              </div>`;
        case 'number':
            return `<input type="number" name="attribute_value" class="form-control" value="${val}" required>`;
        case 'text':
        default:
            return `<input type="text" name="attribute_value" class="form-control" value="${val}" required>`;
    }
}

// ----------------- ADD ATTR ROW ------------------
function addAttributeRow(selectedAttrId = '', value = '') {
    const uid = Date.now();
    const attrSelectId = `attr-select-${uid}`;
    const valueInputId = `attr-value-${uid}`;

    // Ensure attributeDefinitions is populated here. This is a critical point.
    // If addAttributeRow is called too quickly before loadAttributes finishes,
    // attributeDefinitions will be empty, and no options will be rendered.
    // You might want a small delay or a retry mechanism here, or ensure loadAttributes()
    // is awaited before openVariantModal can proceed, especially if called for new variant.
    if (attributeDefinitions.length === 0) {
        console.warn("attributeDefinitions is empty when trying to add attribute row. Attributes may not load correctly. Retrying or awaiting might be needed.");
        // A simple (but not robust) solution would be to defer or add a flag
        // A better solution: openVariantModal should only call addAttributeRow
        // after Promise.all([loadAttributes(), loadMeasurementUnits(), loadBillingUnits()]) resolves.
        // Currently, loadAttributes is called independently.
    }

    const options = attributeDefinitions.map(attr => {
        const selected = attr.id == selectedAttrId ? 'selected' : '';
        return `<option value="${attr.id}" ${selected}
            data-field-type="${attr.field_type}"
            data-choices='${JSON.stringify(attr.choices)}'>${attr.name}</option>`;
    }).join('');

    const $row = $(`
        <div class="d-flex mb-2 attr-row align-items-center gap-2">
            <select name="attribute_definition" class="form-select" id="${attrSelectId}" required>
                <option value="">Select Attribute</option>
                ${options}
            </select>
            <div id="${valueInputId}-container" style="flex-grow: 1;"></div>
            <button type="button" class="btn btn-sm btn-danger" title="Remove">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `);

    $row.find('button').click(() => $row.remove());
    $('#variant-attribute-container').append($row);

    const selectedAttr = attributeDefinitions.find(a => a.id == selectedAttrId);
    if (selectedAttr) {
        $(`#${valueInputId}-container`).html(renderValueInput(selectedAttr.field_type, selectedAttr.choices, value));
    }

    $(`#${attrSelectId}`).change(function () {
        const opt = $(this).find('option:selected');
        const type = opt.data('field-type') || 'text';
        const choices = opt.data('choices') || [];
        $(`#${valueInputId}-container`).html(renderValueInput(type, choices)); // Clear value on attribute change
    });
}

// ---------------- OPEN MODAL --------------------
function openVariantModal(productId, variant = null) {
    $('#variantForm')[0].reset();
    $('#variantForm').data('variant-id', null);
    $('#variant-image-preview').empty();
    $('#variant-attribute-container').empty();
    $('#variant-product-id').val(productId);

    // Ensure all necessary data (attributes, units) are loaded before populating the form
    Promise.all([
        loadAttributes(), // Make sure attributes are loaded/reloaded if there's a chance they've changed
        loadMeasurementUnits(),
        loadBillingUnits()
    ]).then(() => {
        if (variant) {
            console.log("Opening modal for variant:", variant);

            $('#variantForm').data('variant-id', variant.id);
            $('#variant-length').val(variant.length);
            $('#variant-width').val(variant.width);
            $('#variant-height').val(variant.height);
            $('#variant-purchase-price').val(variant.purchase_price);
            $('#variant-selling-price').val(variant.selling_price);

            if (variant.measurement_unit && variant.measurement_unit.id) {
                console.log('Attempting to set measurement unit to ID:', variant.measurement_unit.id);
                if ($(`#variant-measurement-unit option[value="${variant.measurement_unit.id}"]`).length) {
                    $('#variant-measurement-unit').val(variant.measurement_unit.id);
                    console.log('Measurement unit set successfully.');
                } else {
                    console.warn('Measurement unit option not found for ID:', variant.measurement_unit.id);
                }
            } else {
                // If unit is null, explicitly set select to empty/default option
                $('#variant-measurement-unit').val('');
                console.warn('Variant has no measurement_unit or measurement_unit.id is missing, setting to empty.');
            }

            if (variant.billing_unit && variant.billing_unit.id) {
                console.log('Attempting to set billing unit to ID:', variant.billing_unit.id);
                if ($(`#variant-billing-unit option[value="${variant.billing_unit.id}"]`).length) {
                    $('#variant-billing-unit').val(variant.billing_unit.id);
                    console.log('Billing unit set successfully.');
                } else {
                    console.warn('Billing unit option not found for ID:', variant.billing_unit.id);
                }
            } else {
                // If unit is null, explicitly set select to empty/default option
                $('#variant-billing-unit').val('');
                console.warn('Variant has no billing_unit or billing_unit.id is missing, setting to empty.');
            }

            console.log('Processing variant attributes:', variant.attributes);
            (variant.attributes || []).forEach(attr_value_obj => {
                if (attr_value_obj.attribute && attr_value_obj.attribute.id) {
                    console.log('Adding attribute row for attribute ID:', attr_value_obj.attribute.id, 'with value:', attr_value_obj.value);
                    addAttributeRow(attr_value_obj.attribute.id, attr_value_obj.value);
                } else {
                    console.warn('Attribute value object missing attribute or attribute.id:', attr_value_obj);
                }
            });

            (variant.images || []).forEach(img => {
                $('#variant-image-preview').append(`
                    <div class="variant-image-wrapper d-inline-block position-relative me-2 mb-2">
                        <img src="${img.image}" class="img-thumbnail" style="height: 80px;">
                        <button type="button" class="btn btn-sm btn-danger btn-delete-image position-absolute top-0 end-0"
                                data-id="${img.id}" title="Delete image">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                `);
            });
        } else {
            console.log('No variant data provided, opening modal for new variant.');
            addAttributeRow(); // Add one empty row for new variant
        }
        $('#variantModal').modal('show');
    }).catch(error => {
        console.error('Failed to load initial data for variant modal:', error);
        showToast('Failed to load initial form data', 'danger');
    });
}

// ------------------ FORM SUBMIT --------------------
$('#variantForm').on('submit', function (e) {
    e.preventDefault();

    const variantId = $(this).data('variant-id');
    const productId = $('#variant-product-id').val();
    const method = variantId ? 'PUT' : 'POST';
    const url = variantId ? variantApi.detail(variantId) : variantApi.list(productId);
    const csrftoken = $('[name="csrfmiddlewaretoken"]').val();

    const payload = {
        product_id: productId,
        length: parseFloat($('#variant-length').val()) || 0,
        width: parseFloat($('#variant-width').val()) || 0,
        height: parseFloat($('#variant-height').val()) || 0,
        purchase_price: parseFloat($('#variant-purchase-price').val()) || 0,
        selling_price: parseFloat($('#variant-selling-price').val()) || 0,
        measurement_unit_id: $('#variant-measurement-unit').val() ? parseInt($('#variant-measurement-unit').val()) : null,
        billing_unit_id: $('#variant-billing-unit').val() ? parseInt($('#variant-billing-unit').val()) : null,
        attributes: []
    };

    $('.attr-row').each(function () {
        const attrSelect = $(this).find('select[name="attribute_definition"]');
        const attrId = attrSelect.val();
        const valueEl = $(this).find('[name="attribute_value"]');
        let value = valueEl.attr('type') === 'checkbox' ? valueEl.prop('checked') : valueEl.val();

        if (attrId) {
            const attributeValue = { attribute_id: parseInt(attrId), value: String(value) };
            const currentAttrIdOnRow = $(this).data('variant-attr-id');
            if (currentAttrIdOnRow) attributeValue.id = currentAttrIdOnRow;
            payload.attributes.push(attributeValue);
        }
    });

    console.log("Submitting payload:", payload);

    $.ajax({
        url,
        method,
        headers: { 'X-CSRFToken': csrftoken },
        contentType: 'application/json',
        data: JSON.stringify(payload),
        success: function (variant) {
            const imageFiles = $('#variant-images')[0].files;

            const uploadPromise = imageFiles.length > 0
                ? uploadVariantImages(variant.id, imageFiles)
                : Promise.resolve();

            uploadPromise
                .then(() => {
                    $('#variantModal').modal('hide');
                    showToast('Variant saved successfully', 'success');
                    if (typeof loadVariants === 'function') loadVariants(productId);
                    else window.loadProducts?.();
                })
                .catch(() => {
                    $('#variantModal').modal('hide');
                    showToast('Variant saved, but some images failed to upload', 'warning');
                    if (typeof loadVariants === 'function') loadVariants(productId);
                    else window.loadProducts?.();
                });
        },
        error: function (xhr) {
            console.error('Variant save failed:', xhr.responseJSON || xhr.responseText);
            let errorMessage = 'Failed to save variant';
            if (xhr.responseJSON) {
                try {
                    const errors = xhr.responseJSON;
                    if (errors.non_field_errors) errorMessage += `: ${errors.non_field_errors.join(', ')}`;
                    else if (errors.detail) errorMessage += `: ${errors.detail}`;
                    else Object.keys(errors).forEach(f => errorMessage += `\n${f}: ${errors[f].join(', ')}`);
                } catch (e) {
                    console.error("Error parsing response:", e);
                }
            }
            showToast(errorMessage, 'danger');
        }
    });
});

// ---------------- IMAGE UPLOAD ----------------------
function uploadVariantImages(variantId, files) {
    const csrftoken = $('[name="csrfmiddlewaretoken"]').val();
    const formData = new FormData();

    // IMPORTANT: append all images under the SAME key
    for (let file of files) {
        formData.append("images", file);
    }

    return $.ajax({
        url: `/products1/api/variants/${variantId}/upload-images/`,
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        processData: false,
        contentType: false,
        data: formData
    })
    .done(() => {
        console.log("Images uploaded successfully for variant:", variantId);
    })
    .fail(xhr => {
        console.error(
            "Image upload failed:",
            xhr.responseJSON || xhr.responseText
        );
        throw xhr;
    });
}
function resolveImageUrl(url) {
    if (!url) return '';

    // Absolute URL → return as-is
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }

    // Media-relative path
    if (url.startsWith('/media/')) {
        return url;
    }

    // Fallback (relative media)
    return `/media/${url}`;
}


// ---------------- DELETE VARIANT ----------------------
$(document).on('click', '.btn-delete-variant', function () {
    const variantId = $(this).data('id');
    const productId = $(this).data('product');
    const csrftoken = $('[name="csrfmiddlewaretoken"]').val();

    if (!confirm("Are you sure you want to delete this variant?")) return;

    $.ajax({
        url: `/products1/api/variants/${variantId}/`,
        type: 'DELETE',
        headers: { 'X-CSRFToken': csrftoken },
        success: function () {
            showToast('Variant deleted', 'success');
            if (typeof loadVariants === 'function') {
                loadVariants(productId);
            } else {
                window.loadProducts(); // Fallback
            }
        },
        error: function (xhr) {
            console.error('Failed to delete variant', xhr.responseText);
            showToast('Delete failed', 'danger');
        }
    });
});

$(document).on('click', '.btn-edit-variant', function () {
    const variantId = $(this).data('id');
    const productId = $(this).data('product');

    if (!variantId || !productId) {
        console.warn('Missing variantId or productId on edit button');
        return;
    }

    $.get(variantApi.detail(variantId))
        .done(variant => {
            openVariantModal(productId, variant);
        })
        .fail(err => {
            console.error('Failed to load variant for editing', err);
            showToast('Could not load variant data', 'danger');
        });
});


// ------------- MODAL RESET -------------------------
$('#variantModal').on('hidden.bs.modal', function () {
    $('#variantForm')[0].reset();
    $('#variantForm').removeData('variant-id product-id'); // Clear data attributes
    $('#variant-attribute-container').empty();
    $('#variant-image-preview').empty();
    $('#variant-images').val(''); // Clear file input
});

$(document).on('click', '.btn-delete-image', function () {
    const imageId = $(this).data('id');
    const variantId = $('#variantForm').data('variant-id');
    const csrftoken = $('[name="csrfmiddlewaretoken"]').val();
    const $wrapper = $(this).closest('.variant-image-wrapper');

    if (!variantId) {
        console.error('Variant ID missing while deleting image');
        return;
    }

    if (!confirm('Delete this image?')) return;

    $.ajax({
        url: `/products1/api/variants/${variantId}/delete-image/${imageId}/`,
        method: 'DELETE',
        headers: { 'X-CSRFToken': csrftoken },
    })
    .done(() => {
        showToast('Image deleted', 'success');
        $wrapper.remove();
    })
    .fail(xhr => {
        console.error('Failed to delete image', xhr.responseText);
        showToast('Delete failed', 'danger');
    });
});
