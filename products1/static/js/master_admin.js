

$(function() {
    // --- Get the CSRF token once ---
    const csrftoken = $('[name="csrfmiddlewaretoken"]').val();

    const api = {
        products: '/products1/api/products/',
        types: '/products1/api/product-types/',
        models: '/products1/api/product-series/',
        measurementUnits: '/products1/api/measurement-units/',
        billingUnits: '/products1/api/billing-units/',
        attributes: '/products1/api/attributes/',
    };

    // --- Utility Functions ---
    function safeReset(formId) {
        const form = document.getElementById(formId);
        if (form?.reset) form.reset();
        else console.warn(`[safeReset] Form not found: #${formId}`);
    }

    

    function ajaxSubmit(form, url, method, data, reloadFn) {
        $.ajax({ url, method, contentType: 'application/json', data: JSON.stringify(data), headers: { 'X-CSRFToken': csrftoken } })
            .done(() => {
                $(form).closest('.modal').modal('hide');
                reloadFn();
                showToast('Saved successfully', 'success');
            })
            .fail(err => {
                console.error('AJAX Error:', err.responseJSON || err);
                showToast('Error saving', 'danger');
            });
    }

    function confirmDel(url, reloadFn) {
        if (confirm('Are you sure?')) {
            $.ajax({ url, method: 'DELETE', headers: { 'X-CSRFToken': csrftoken } })
                .done(() => { reloadFn(); showToast('Deleted successfully', 'success'); })
                .fail(err => { console.error('AJAX Error:', err.responseJSON || err); showToast('Error deleting', 'danger'); });
        }
    }
function refreshModelDropdown(typeId, selectedModel = null) {
    const $model = $('#product-model-id');
    $model.empty();

    initSelect2({
        selector: '#product-model-id',
        url: api.models + '?type=' + typeId,
        value: selectedModel?.id || null,
        text: selectedModel?.name || '',
        placeholder: 'Select Product Model',
        dropdownParent: '#productModal'
    });
}
$('#product-type-id').on('change', function () {
    const typeId = $(this).val();
    if (typeId) refreshModelDropdown(typeId);
});
    // --- Refactored Select2 Utility ---
    function initSelect2({ selector, url, textField = 'name', value = null, text = null, placeholder = 'Select...', dropdownParent = 'body', minimumInputLength = 0, pageSize = 10 }) {
        const $el = $(selector);
        if (!$el.length) return console.error(`initSelect2: Element not found: ${selector}`);
        if ($el.data('select2')) $el.select2('destroy');

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

        if (value != null && text != null) {
            const opt = new Option(text, value, true, true);
            $el.append(opt).trigger('change');
        } else {
            $el.val(null).trigger('change');
        }
    }

    // --- Load / Render Functions ---
    function loadProducts() {
        $.get(api.products, ({ results }) => {
            console.log("Loaded products:", results);
            $('#productTable tbody').html(results.map(p => `
                <tr data-id="${p.id}">
                    <td>${p.name}</td>
                    <td>${p.product_type?.name || 'N/A'}</td>
                    <td>${p.product_series?.name || 'N/A'}</td>
                    <td>${p.is_active ? 'Yes' : 'No'}</td>
                    <td>${new Date(p.created_at).toLocaleDateString()}</td>
                    <td>${p.variants_data?.length || 0}</td>
                    <td>${p.images?.length || 0}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-product">Edit</button>
                        <button class="btn btn-danger btn-sm delete-product">Delete</button>
                    </td>
                </tr>`).join(''));
        });
    }

    function renderImagePreviews(images) {
        window.deletedImageIds = [];
        $('#existing-product-images').html((images || []).map(img => `
            <div class="position-relative" data-img-id="${img.id}">
                <img src="${img.image}" class="img-thumbnail" style="width:100px;height:100px;object-fit:cover">
                <button class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-image">×</button>
            </div>`).join(''));
    }
window.loadProducts = loadProducts;
    // --- Admin Data Tables ---
    function loadTypes() {
        $.get(api.types, ({ results }) => {
            $('#table-types tbody').html(results.map(t => `
                <tr data-id="${t.id}">
                    <td>${t.name}</td><td>${t.slug}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-type">Edit</button>
                        <button class="btn btn-danger btn-sm delete-type">Delete</button>
                    </td>
                </tr>`).join(''));
        });
    }
    $('#btn-add-type').click(() => { safeReset('form-type'); $('#type-id').val(''); $('#typeModal').modal('show'); });
    $('#table-types').on('click', '.edit-type', function() {
        const row = $(this).closest('tr');
        $('#type-id').val(row.data('id'));
        $('#type-name').val(row.find('td').eq(0).text());
        $('#type-slug').val(row.find('td').eq(1).text());
        $('#typeModal').modal('show');
    });
    $('#table-types').on('click', '.delete-type', function() {
        confirmDel(api.types + $(this).closest('tr').data('id') + '/', loadTypes);
    });
    $('#form-type').submit(e => {
        e.preventDefault();
        const id = $('#type-id').val();
        ajaxSubmit('#form-type', api.types + (id ? id + '/' : ''), id ? 'PUT' : 'POST', {
            name: $('#type-name').val(),
            slug: $('#type-slug').val()
        }, loadTypes);
    });

    function loadModels(typeId = null) {
    let url = api.models;
    if (typeId) url += `?type=${typeId}`;

    $.get(url, function (resp) {
        const results = resp.results || [];

        console.log('Loaded models:', results);

        if (!results.length) {
            $('#table-models tbody').html(
                `<tr><td colspan="4" class="text-center text-muted">No models found</td></tr>`
            );
            return;
        }

        $('#table-models tbody').html(
            results.map(m => `
                <tr data-id="${m.id}" data-type="${m.product_type ? m.product_type.id : ''}">
                    <td>${m.name}</td>
                    <td>${m.code}</td>
                    <td>${m.product_type ? m.product_type.name : '-'}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-model">Edit</button>
                        <button class="btn btn-danger btn-sm delete-model">Delete</button>
                    </td>
                </tr>
            `).join('')
        );
    }).fail(xhr => {
        console.error('Failed to load models', xhr.responseText);
    });
}

$('#filter-model-type').on('change', function () {
    const typeId = $(this).val();
    loadModels(typeId);
});
    $('#btn-add-model').click(() => {
        safeReset('form-model');
        $('#model-id').val('');
        $('#model-type-id').empty();
        initSelect2({ selector: '#model-type-id', url: api.types, dropdownParent: '#modelModal' });
        $('#modelModal').modal('show');
    });
    $('#table-models').on('click', '.edit-model', function() {
        const r = $(this).closest('tr');
        $.get(api.models + r.data('id') + '/', modelData => {
            $('#model-id').val(modelData.id);
            $('#model-name').val(modelData.name);
            $('#model-code').val(modelData.code);
            $('#model-type-id').empty();
            if (modelData.type) {
                initSelect2({
                    selector: '#model-type-id',
                    url: api.types,
                    value: modelData.type.id,
                    text: modelData.type.name,
                    dropdownParent: '#modelModal'
                });
            } else {
                initSelect2({ selector: '#model-type-id', url: api.types, dropdownParent: '#modelModal' });
            }
            $('#modelModal').modal('show');
        });
    });
    $('#table-models').on('click', '.delete-model', function() {
        confirmDel(api.models + $(this).closest('tr').data('id') + '/', loadModels);
    });
    $('#form-model').submit(e => {
        e.preventDefault();
        const id = $('#model-id').val();
        ajaxSubmit('#form-model', api.models + (id ? id + '/' : ''), id ? 'PUT' : 'POST', {
            name: $('#model-name').val(),
            code: $('#model-code').val(),
            product_type_id: $('#model-type-id').val()
        }, loadModels);
    });

    function loadUnits() {
        $.get(api.measurementUnits, ({ results }) => {
            $('#table-units tbody').html(results.map(u => `
                <tr data-id="${u.id}">
                    <td>${u.name}</td><td>${u.code}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-unit">Edit</button>
                        <button class="btn btn-danger btn-sm delete-unit">Delete</button>
                    </td>
                </tr>`).join(''));
        });
    }
    $('#btn-add-unit').click(() => { safeReset('form-unit'); $('#unit-id').val(''); $('#unitModal').modal('show'); });
    $('#table-units').on('click', '.edit-unit', function() {
        const r = $(this).closest('tr');
        $('#unit-id').val(r.data('id'));
        $('#unit-name').val(r.find('td').eq(0).text());
        $('#unit-code').val(r.find('td').eq(1).text());
        $('#unitModal').modal('show');
    });
    $('#table-units').on('click', '.delete-unit', function() {
        confirmDel(api.measurementUnits + $(this).closest('tr').data('id') + '/', loadUnits);
    });
    $('#form-unit').submit(e => {
        e.preventDefault();
        const id = $('#unit-id').val();
        ajaxSubmit('#form-unit', api.measurementUnits + (id ? id + '/' : ''), id ? 'PUT' : 'POST', {
            name: $('#unit-name').val(),
            code: $('#unit-code').val()
        }, loadUnits);
    });

    function loadBilling() {
        $.get(api.billingUnits, ({ results }) => {
            $('#table-billing tbody').html(results.map(b => `
                <tr data-id="${b.id}">
                    <td>${b.name}</td><td>${b.code}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-billing">Edit</button>
                        <button class="btn btn-danger btn-sm delete-billing">Delete</button>
                    </td>
                </tr>`).join(''));
        });
    }
    $('#btn-add-billing').click(() => { safeReset('form-billing'); $('#billing-id').val(''); $('#billingModal').modal('show'); });
    $('#table-billing').on('click', '.edit-billing', function() {
        const r = $(this).closest('tr');
        $('#billing-id').val(r.data('id'));
        $('#billing-name').val(r.find('td').eq(0).text());
        $('#billing-code').val(r.find('td').eq(1).text());
        $('#billingModal').modal('show');
    });
    $('#table-billing').on('click', '.delete-billing', function() {
        confirmDel(api.billingUnits + $(this).closest('tr').data('id') + '/', loadBilling);
    });
    $('#form-billing').submit(e => {
        e.preventDefault();
        const id = $('#billing-id').val();
        ajaxSubmit('#form-billing', api.billingUnits + (id ? id + '/' : ''), id ? 'PUT' : 'POST', {
            name: $('#billing-name').val(),
            code: $('#billing-code').val()
        }, loadBilling);
    });

    $('#attribute-type').change(function() {
        $(this).val() === 'choice'
            ? $('#choice-container').show()
            : $('#choice-container').hide();
    });

    function loadAttributes() {
        $.get(api.attributes, ({ results }) => {
            $('#table-attributes tbody').html(results.map(a => `
                <tr data-id="${a.id}">
                    <td>${a.name}</td><td>${a.field_type}</td><td>${JSON.stringify(a.choices)}</td>
                    <td>
                        <button class="btn btn-info btn-sm edit-attribute">Edit</button>
                        <button class="btn btn-danger btn-sm delete-attribute">Delete</button>
                    </td>
                </tr>`).join(''));
        });
    }

    $('#btn-add-attribute-definition').click(() => {
        safeReset('form-attribute');
        $('#attribute-id').val('');
        $('#attribute-choices').val('');
        $('#choice-container').hide();
        $('#attributeModal').modal('show');
    });

    $('#table-attributes').on('click', '.edit-attribute', function() {
        const r = $(this).closest('tr');
        $('#attribute-id').val(r.data('id'));
        $('#attribute-name').val(r.find('td').eq(0).text());
        $('#attribute-type').val(r.find('td').eq(1).text()).change();
        $('#attribute-choices').val(r.find('td').eq(2).text());
        $('#attributeModal').modal('show');
    });

    $('#table-attributes').on('click', '.delete-attribute', function() {
        confirmDel(api.attributes + $(this).closest('tr').data('id') + '/', loadAttributes);
    });

    $('#form-attribute').submit(e => {
        e.preventDefault();
        const id = $('#attribute-id').val();
        const payload = {
            name: $('#attribute-name').val(),
            field_type: $('#attribute-type').val()
        };
        if ($('#attribute-type').val() === 'choice') {
            try {
                payload.choices = JSON.parse($('#attribute-choices').val());
            } catch {
                return showToast('Invalid JSON for choices', 'danger');
            }
        }
        ajaxSubmit('#form-attribute', api.attributes + (id ? id + '/' : ''), id ? 'PUT' : 'POST', payload, loadAttributes);
    });

    // --- Initial Load ---
    loadProducts();
    loadTypes();
    loadModels();
    loadUnits();
    loadBilling();
    loadAttributes();
});
