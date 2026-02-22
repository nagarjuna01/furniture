const productApi = {
    list: '/products1/v1/products/',
    // Add a detail method for consistency, used for GET/PUT/PATCH/DELETE on a single product
    detail: id => `/products1/v1/products/${id}/`,
    types: '/products1/v1/product-types/',
    models: '/products1/v1/product-series/',
    // The 'update' is redundant if 'detail' is used for PUT/PATCH. I'll remove it below for clarity.
    // update: id => `/products1/api/products/${id}/`,
};
const productImageApi = {
    upload: productId =>
        `/products1/v1/products/${productId}/upload-images/`,
    delete: (productId, imageId) =>
        `/products1/v1/products/${productId}/delete-image/${imageId}/`,
};

$(function() {
    
    function initSelect2({ selector, url, textField = 'name', value = null, text = null, placeholder = 'Select...', dropdownParent = 'body', minimumInputLength = 0, pageSize = 10 }) {
        const $el = $(selector);
        if (!$el.length) return console.error(`initSelect2: Element not found: ${selector}`);
        // Destroy existing Select2 instance if it exists to prevent re-initialization issues
        if ($el.data('select2')) {
            $el.select2('destroy');
        }

        $el.select2({
            placeholder,
            allowClear: true,
            minimumInputLength,
            ajax: {
                url,
                dataType: 'json',
                delay: 250,
                data: params => ({ search: params.term || '', page: params.page || 1 }),
                processResults: (data, params) => {
                    params.page ??= 1;
                    return {
                        results: (data.results || []).map(item => ({ id: item.id, text: item[textField] })),
                        pagination: { more: (params.page * pageSize) < data.count }
                    };
                },
                cache: true
            },
            dropdownParent: $(dropdownParent),
            width: '100%'
        });

        // Set initial selected value if provided
        if (value !== null && text !== null) {
            const opt = new Option(text, value, true, true);
            $el.append(opt).trigger('change');
        } else {
            // Clear any pre-selected values if no value is provided
            $el.val(null).trigger('change');
        }
    }

    window.renderVariantSection =function renderVariantSection(product, isCardView = false) {
    const variantHtml = (product.variants || []).map(variant => {
    const imgHtml = (variant.images && variant.images.length > 0)
            ? `<div class="variant-image-gallery d-flex overflow-auto"
                style="gap: 0.5rem; scroll-snap-type: x mandatory;">
                ${variant.images.map(img => `
                    <div class="flex-shrink-0 border rounded shadow-sm"
                        style="width: 75px; height: 75px; scroll-snap-align: start; overflow: hidden;">
                        <img src="${resolveImageUrl(img.image)}"
                            class="img-fluid"
                            style="object-fit: cover; width: 100%; height: 100%;">
                    </div>
                `).join('')}
            </div>`
            : `<div class="text-muted small">No images uploaded</div>`;


        const l = Number(variant.length || 0);
        const w = Number(variant.width || 0);
        const h = Number(variant.height || 0);

        const measurementUnitCode = variant.measurement_unit?.code || '';
        const billingUnitCode = variant.billing_unit?.code || '';

        const attributesDisplay = (variant.attributes || [])
            .map(attr => `
                <span class="badge bg-secondary me-1 mb-1">
                    ${attr.attribute?.name || 'N/A'}: ${attr.value}
                </span>
            `).join('');

        const variantInfo = `
            <div><strong>SKU:</strong> ${variant.sku || '—'}</div>
            <div><strong>L×W×H:</strong> ${l}×${w}×${h} ${measurementUnitCode}</div>
            <div>
                <strong>Purchase:</strong> ₹${variant.purchase_price}
                | <strong>Selling:</strong> ₹${variant.selling_price}
                ${billingUnitCode}
            </div>
            ${attributesDisplay ? `<div class="mt-2">${attributesDisplay}</div>` : ''}
        `;

        const actionButtons = `
            <div class="mt-3 text-end">
                <button class="btn btn-sm btn-outline-primary btn-edit-variant"
                        data-id="${variant.id}"
                        data-product="${product.id}">
                    Edit
                </button>
                <button class="btn btn-sm btn-danger btn-delete-variant"
                        data-id="${variant.id}"
                        data-product="${product.id}">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        `;

        return `
            <div class="col-md-6 mb-3">
                <div class="border rounded p-3 bg-light">
                    <div class="row g-2 align-items-start">
                        <div class="col-12">
                            ${imgHtml}
                        </div>
                        <div class="col-12 small">
                            ${variantInfo}
                            ${actionButtons}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="variant-section mt-2 collapse" id="variant-section-${product.id}">
            <h6>Variants</h6>
            <div class="row" id="variant-list-${product.id}">
                ${variantHtml || '<p class="text-muted small">No variants available</p>'}
            </div>
        </div>
    `;
}


    // --- Main Product Loading (Updated for primary_image) ---
    function loadProducts() {
    const isCardView = $('#viewToggleSwitch').is(':checked');
    const $tableBody = $('#productTableBody').empty();
    const $cardContainer = $('#productCardView').empty();

    $.get(productApi.list, function (data) {
        
        const products = data.results || [];

        products.forEach(product => {
            console.log(
  'PRODUCT', product.id,
  'variants:', product.variants
);

            // ✅ IMAGE RESOLUTION (VERY IMPORTANT)
            const resolvedImage =
                product.primary_image ||
                (product.images && product.images.length ? product.images[0].image : null) ||
                null;

            const productButtons = `
                <button class="btn btn-sm btn-primary me-1 edit-product" data-id="${product.id}">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-sm btn-outline-success me-1" onclick="openVariantModal(${product.id})">
                    <i class="bi bi-plus-lg"></i>
                </button>
                <button class="btn btn-sm btn-outline-dark me-1"
                        data-bs-toggle="collapse"
                        data-bs-target="#variant-section-${product.id}">
                    <i class="bi bi-chevron-down"></i>
                </button>
                
            `;

            const statusBtn = `
                <button class="btn btn-sm toggle-status-btn btn-${product.is_active ? 'success' : 'secondary'}"
                        data-id="${product.id}"
                        data-status="${product.is_active ? 'active' : 'inactive'}">
                    ${product.is_active ? 'Active' : 'Inactive'}
                </button>
            `;

            if (isCardView) {

                const cardHtml = `
                <div class="col-md-4 mb-4 product-card" data-product-id="${product.id}">
                    <div class="card h-100 shadow-sm">

                        <!-- ✅ IMAGE SLOT ALWAYS EXISTS -->
                        <img
                            src="${resolvedImage}"
                            class="card-img-top product-card-image object-fit-cover"
                            style="height:180px;"
                            alt="${product.name}"
                        >

                        <div class="card-body">
                            <h5 class="card-title mb-1">${product.name}</h5>

                            <p class="card-text small text-muted mb-2">
                                <strong>SKU:</strong> ${product.sku || '—'}<br>
                                <strong>Type:</strong> ${product.product_type?.name || '—'}<br>
                                <strong>Model:</strong> ${product.product_series?.name || '—'}
                            </p>

                            <div class="mb-2">${statusBtn}</div>

                            <div class="d-flex justify-content-between mb-2">
                                ${productButtons}
                            </div>

                            ${renderVariantSection(product, isCardView)}
                        </div>
                    </div>
                </div>
                `;

                $cardContainer.append(cardHtml);

            } else {
 
                const rowHtml = `
                <tr>
                    <td colspan="6">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${product.name}</h6>
                                <div class="small text-muted">
                                    SKU: ${product.sku || '—'} |
                                    Type: ${product.product_type || '—'} |
                                    Model: ${product.product_series || '—'}
                                </div>
                                <div class="mt-2">${statusBtn}</div>
                            </div>
                            <div>${productButtons}</div>
                        </div>

                        ${renderVariantSection(product, isCardView)}
                    </td>
                </tr>
                `;

                $tableBody.append(rowHtml);
            }
        });

    }).fail(err => {
        console.error('Error loading products', err);
        showToast('Failed to load products', 'danger');
    });
}

    window.openProductModal = function(productId = null) {
        const isEdit = productId !== null;
        $('#productForm')[0].reset();
        $('#product-id').val(productId || '');
        $('#productModalLabel').text(isEdit ? 'Edit Product' : 'Add Product');
        $('#product-image-preview').empty(); // Clear existing image previews
        $('#product-images').val(''); // Clear the file input for new uploads

        // Initialize Product Type Select2
        initSelect2({
            selector: '#product-type-id',
            url: productApi.types,
            placeholder: 'Select Product Type',
            dropdownParent: '#productModal'
        });

        // Initialize Product Model Select2 (will be re-initialized if in edit mode with a type filter)
        // Also clear previous selection to avoid displaying old value if type changes later
        initSelect2({
            selector: '#product-model-id',
            url: productApi.models, // Initial URL without type filter
            placeholder: 'Select Product Model',
            dropdownParent: '#productModal'
        });

        if (isEdit) {
            $.get(productApi.detail(productId), function (product) { // Use productApi.detail
                $('#product-name').val(product.name);

                // Populate Product Type Select2 for editing
                const typeSelect = $('#product-type-id');
                if (product.type) {
                    // Check if the option already exists before appending
                    if (!typeSelect.find(`option[value="${product.type.id}"]`).length) {
                        typeSelect.append(new Option(product.type.name, product.type.id, true, true));
                    }
                    typeSelect.val(product.type.id).trigger('change');
                } else {
                    typeSelect.val(null).trigger('change');
                }

                // IMPORTANT: Re-initialize Product Model Select2 with type filter AFTER product.type is set
                // This will trigger the 'change' on product-type-id to re-fetch models
                const modelUrl = product.type ? productApi.models + '?type=' + product.type.id : productApi.models;
                initSelect2({
                    selector: '#product-model-id',
                    url: modelUrl,
                    placeholder: 'Select Product Model',
                    dropdownParent: '#productModal'
                });

                if (product.model) {
                    const modelSelect = $('#product-model-id');
                    if (!modelSelect.find(`option[value="${product.model.id}"]`).length) {
                         modelSelect.append(new Option(product.model.name, product.model.id, true, true));
                    }
                    modelSelect.val(product.model.id).trigger('change');
                } else {
                    $('#product-model-id').val(null).trigger('change');
                }


                // --- NEW: Display existing product images ---
                // Assuming product.images is an array of objects {id: ..., image: 'url'}
                if (product.images && product.images.length > 0) {
                    product.images.forEach(img => {
                        displayProductImagePreview(img.image, img.id);
                    });
                } else if (product.primary_image) {
                    // Fallback if backend only provides primary_image URL directly
                    displayProductImagePreview(product.primary_image, 'primary-mock');
                }
                // --- END NEW ---

            }).fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Error fetching product data for edit:', textStatus, errorThrown, jqXHR.responseText);
                showToast('Failed to load product data for editing.', 'danger');
                $('#productModal').modal('hide'); // Close modal if data fetch fails
            });
        }

        $('#productModal').modal('show');
    };

    // --- Product Form Submission (UPDATED for Image Upload) ---
    $('#productForm').on('submit', function (e) {
        e.preventDefault();
        const id = $('#product-id').val();
        const payload = {
            name: $('#product-name').val(),
            product_type_id: $('#product-type-id').val() || null,
            product_series_id: $('#product-model-id').val() || null,
        };
        const method = id ? 'PUT' : 'POST';
        const url = id ? productApi.detail(id) : productApi.list; // Use productApi.detail or list

        $.ajax({
            url,
            method,
            headers: { 'X-CSRFToken': Window.CSRF_TOKEN },
            contentType: 'application/json', // Important for sending JSON data
            data: JSON.stringify(payload),
            success: function (productResponse) {
                const imageFiles = $('#product-images')[0].files;
                if (imageFiles.length > 0) {
                    // Upload images only AFTER the product is successfully created/updated
                    uploadProductImages(productResponse.id, imageFiles)
                        .then(() => {
                            $('#productModal').modal('hide');
                            showToast('Product and images saved successfully', 'success');
                            loadProducts(); // Reload product list after all images are uploaded
                        })
                        .catch(() => {
                            // Even if some images failed, product was saved, so hide modal and reload
                            $('#productModal').modal('hide');
                            showToast('Product saved, but some images failed to upload', 'warning');
                            loadProducts();
                        });
                } else {
                    // If no new images to upload, just hide modal and reload products
                    $('#productModal').modal('hide');
                    showToast('Product saved successfully', 'success');
                    loadProducts();
                }
            },
            error: function (xhr) {
                console.error('Product save failed:', xhr.responseJSON || xhr.responseText);
                let errorMessage = 'Failed to save product';
                if (xhr.responseJSON) {
                    try {
                        const errors = xhr.responseJSON;
                        if (errors.non_field_errors) {
                            errorMessage += `: ${errors.non_field_errors.join(', ')}`;
                        } else if (errors.detail) {
                            errorMessage += `: ${errors.detail}`;
                        } else {
                            for (const field in errors) {
                                errorMessage += `\n${field}: ${errors[field].join(', ')}`;
                            }
                        }
                    } catch (e) {
                        console.error("Error parsing product error response:", e);
                    }
                }
                showToast(errorMessage, 'danger');
            }
        });
    });

    // --- NEW PRODUCT IMAGE FUNCTIONS ---

    // Helper function to display an image in the preview area of the product modal
    function displayProductImagePreview(imageUrl, imageId, productId) {
    $('#product-image-preview').append(`
        <div class="product-image-wrapper d-inline-block position-relative me-2 mb-2">
            <img src="${imageUrl}" class="img-thumbnail" style="height: 80px;">
            <button type="button"
                    class="btn btn-sm btn-danger btn-delete-product-image position-absolute top-0 end-0"
                    data-id="${imageId}"
                    data-product-id="${productId}"
                    title="Delete image"
                    style="font-size: 0.7em; padding: 0.1em 0.4em; line-height: 1; border-radius: 50%;">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `);
}

    function uploadProductImages(productId, files) {
    const uploadPromises = [];

    for (let file of files) {
        const formData = new FormData();
        formData.append('images', file); // ✅ MUST be "images"

        const promise = $.ajax({
            url: productImageApi.upload(productId),
            method: 'POST',
            headers: { 'X-CSRFToken': window.CSRF_TOKEN },
            processData: false,
            contentType: false,
            data: formData,
        }).done(res => {
            console.log('Product image uploaded:', file.name, res);
        }).fail(xhr => {
            console.error(
                'Product image upload failed:',
                file.name,
                xhr.responseJSON || xhr.responseText
            );
            showToast(`Failed to upload image: ${file.name}`, 'danger');
        });

        uploadPromises.push(promise);
    }

    return Promise.all(uploadPromises);
}
$(document).on('click', '.btn-delete-product-image', function () {
    const imageId = $(this).data('id');
    const productId = $(this).data('product-id');
    const $wrapper = $(this).closest('.product-image-wrapper');

    if (!confirm('Are you sure you want to delete this image?')) return;

    $.ajax({
        url: productImageApi.delete(productId, imageId),
        method: 'DELETE',
        headers: {  'X-CSRFToken': window.CSRF_TOKEN },
    }).done(() => {
        showToast('Product image deleted', 'success');
        $wrapper.remove();
        loadProducts();
    }).fail(xhr => {
        console.error(
            'Failed to delete product image',
            xhr.responseJSON || xhr.responseText
        );
        showToast('Failed to delete image', 'danger');
    });
});


    // Clear product image input and preview when modal is hidden
    $('#productModal').on('hidden.bs.modal', function () {
        $('#product-image-preview').empty();
        $('#product-images').val(''); // Clear the file input
    });

    // --- Existing Event Listeners (Keep as is) ---
    $('#btn-add-product').click(() => openProductModal());

    // Update the event listener for editing a product to call openProductModal
    // Note: The click handler for '.edit-product' is now in the main (document).on('click')
    // and uses openProductModal directly.
    $(document).on('click', '.edit-product', function() {
        const productId = $(this).data('id');
        openProductModal(productId);
    });

    $('#viewToggleSwitch').on('change', function () {
        const isCard = $(this).is(':checked');
        $('#productTableView').toggle(!isCard);
        $('#productCardView').toggle(isCard);
        loadProducts();
    });

     

    // This handles filtering models based on selected type
    $('#product-type-id').on('change', function () {
        const typeId = $(this).val();
        if (typeId) {
            initSelect2({
                selector: '#product-model-id',
                url: productApi.models + '?type=' + typeId,
                placeholder: 'Select Product Model',
                dropdownParent: '#productModal'
            });
            $('#product-model-id').next('.select2-container').show(); // Ensure visible
        } else {
            $('#product-model-id').empty();
            $('#product-model-id').next('.select2-container').hide(); // Hide if no type selected
        }
    });

    // --- Product Status Toggle (Keep as is) ---
    $(document).on('click', '.toggle-status-btn', function () {
        const $btn = $(this);
        const productId = $btn.data('id');
        const currentStatus = $btn.data('status');
        const newStatus = currentStatus === 'active' ? false : true;

        $.ajax({
            url: productApi.detail(productId), // Use productApi.detail for PATCH
            method: 'PATCH',
            headers: { 'X-CSRFToken': window.CSRF_TOKEN },
            contentType: 'application/json',
            data: JSON.stringify({ is_active: newStatus }),
            success: function (updated) {
                showToast(`Product marked as ${updated.is_active ? 'Active' : 'Inactive'}`, 'success');

                $btn
                    .toggleClass('btn-success btn-secondary')
                    .html(`${updated.is_active ? '<i class="bi bi-check-circle me-1"></i>Active' : '<i class="bi bi-x-circle me-1"></i>Inactive'}`)
                    .data('status', updated.is_active ? 'active' : 'inactive');
            },
            error: function (err) {
                console.error('Failed to update status', err);
                showToast('Status update failed', 'danger');
            }
        });
    });

    // Initial load of products when the page is ready
    loadProducts();
});

