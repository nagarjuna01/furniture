/* =====================================================
   PRODUCT TYPE & SERIES CRUD (ADMIN)
===================================================== */

const TypeSeriesAPI = {
    types: '/products1/v1/product-types/',
    series: '/products1/v1/product-series/',
};

/* ================== GENERIC CRUD ================== */

// FIX: Accepts 'data' object to support slug, code, and type_id
function submitSimpleForm({ form, idInput, data, api, onSuccess }) {
    const id = $(idInput).val();
    
    $.ajax({
        url: id ? `${api}${id}/` : api,
        method: id ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data)
    })
    .done(() => {
        $(form).closest('.modal').modal('hide');
        showToast('Saved successfully');
        onSuccess?.();
    })
    .fail(xhr => {
        console.error('Save failed:', xhr.responseText);
        showToast('Save failed: ' + xhr.statusText, 'danger');
    });
}

/* ================== LOADERS ================== */

function populateTypeDropdown(selectedId = null) {
    $.get(TypeSeriesAPI.types).done(function(res) {
        const data = res.results || res;
        let options = '<option value="">Select a Type...</option>';
        data.forEach(t => {
            options += `<option value="${t.id}" ${t.id == selectedId ? 'selected' : ''}>${t.name}</option>`;
        });
        $('#series-type-id').html(options);
    });
}

function loadTypeTable() {
    $.get(TypeSeriesAPI.types).done(function (res) {
        const $tbody = $('#table-types tbody');
        $tbody.empty();
        (res.results || []).forEach(function (t) {
            $tbody.append(`
                <tr>
                    <td>${t.name}</td>
                    <td>${t.slug}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-primary edit-type"
                            data-id="${t.id}" data-name="${t.name}" data-slug="${t.slug}">
                            Edit
                        </button>
                    </td>
                </tr>`);
        });
        populateTypeDropdown(); 
    });
}

function loadSeriesTable() {
    $.get(TypeSeriesAPI.series).done(function (res) {
        const $tbody = $('#table-models tbody');
        $tbody.empty();
        (res.results || []).forEach(function (s) {
            $tbody.append(`
                <tr>
                    <td>${s.name}</td>
                    <td>${s.code}</td>
                    <td>${s.product_type?.name || '-'}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-primary edit-series"
                            data-id="${s.id}" data-name="${s.name}" 
                            data-code="${s.code}" data-product-type="${s.product_type?.id}">
                            Edit
                        </button>
                    </td>
                </tr>`);
        });
    });
}

/* ================== TYPE LOGIC ================== */

function generateSlug(text) {
    return text.toString().toLowerCase().trim()
        .replace(/\s+/g, '-').replace(/[^\w\-]+/g, '')
        .replace(/\-\-+/g, '-').replace(/^-+/, '').replace(/-+$/, '');
}

$(document).on('input', '#type-name', function() {
    if (!$('#type-id').val()) {
        $('#type-slug').val(generateSlug($(this).val()));
    }
});

window.openTypeModal = function (type = null) {
    $('#type-id').val(type ? type.id : '');
    $('#type-name').val(type ? type.name : '');
    $('#type-slug').val(type ? type.slug : '');
    $('#typeModalLabel').text(type ? 'Edit Product Type' : 'Add Product Type');
    $('#typeModal').modal('show');
};

$(document).on('submit', '#form-type', function (e) {
    e.preventDefault();
    submitSimpleForm({
        form: this,
        idInput: '#type-id',
        data: { name: $('#type-name').val(), slug: $('#type-slug').val() },
        api: TypeSeriesAPI.types,
        onSuccess: loadTypeTable
    });
});

/* ================== SERIES LOGIC ================== */

window.openSeriesModal = function (series = null) {
    const typeId = series ? (series.productType || series.id) : null;
    populateTypeDropdown(typeId);

    $('#series-id').val(series ? series.id : '');
    $('#series-name').val(series ? series.name : '');
    $('#series-code').val(series ? series.code : '');
    
    $('#seriesModalLabel').text(series ? 'Edit Product Series' : 'Add Product Series');
    $('#seriesModal').modal('show');
};

$(document).on('submit', '#form-series', function (e) {
    e.preventDefault();
    submitSimpleForm({
        form: this,
        idInput: '#series-id',
        data: {
            name: $('#series-name').val(),
            code: $('#series-code').val(),
            product_type_id: $('#series-type-id').val()
        },
        api: TypeSeriesAPI.series,
        onSuccess: loadSeriesTable
    });
});

/* ================== EVENT LISTENERS ================== */

$(document).ready(() => {
    loadTypeTable();
    loadSeriesTable();

    $('#btn-add-type').on('click', () => openTypeModal());
    $('#btn-add-model').on('click', () => openSeriesModal());
});

$(document).on('click', '.edit-type', function () {
    openTypeModal($(this).data()); 
});

$(document).on('click', '.edit-series', function () {
    const d = $(this).data();
    openSeriesModal({
        id: d.id,
        name: d.name,
        code: d.code,
        productType: d.productType 
    });
});