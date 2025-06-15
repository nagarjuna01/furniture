const woodenApi = 'http://127.0.0.1:8000/material/woodens/';
let saveAndAddAnother = false;

// Load brand dropdown with Select2
function loadBrands() {
  $.get('http://127.0.0.1:8000/material/brands/')
    .done(data => {
      const $brandSelect = $('#wooden-brand');
      $brandSelect.empty().append('<option value="">Select Brand</option>');

      data.forEach(brand => {
        $brandSelect.append(new Option(brand.name, brand.id));
      });

      $brandSelect.select2({
        placeholder: 'Select a brand',
        allowClear: true,
        width: '100%'
      });
    })
    .fail(() => showAlert('Failed to load brands'));
}

// Open modal for add
$(document).on('click', '#add-wooden-btn', function () {
  $('#wooden-id').val('');
  $('#wooden-form')[0].reset();
  $('#wooden-brand').val(null).trigger('change');
  $('#woodenModalLabel').text('Add Wooden');
  loadBrands();
  new bootstrap.Modal('#woodenModal').show();
});

$('#save-add-another-btn').on('click', function () {
  saveAndAddAnother = true;
  $('#wooden-form').submit();
});

// Submit handler
$('#wooden-form').on('submit', function (e) {
  e.preventDefault();

  const woodenId = $('#wooden-id').val();
  const payload = {
    material_grp: $('#categories-select').val(),
    material_type: $('#types-select').val(),
    material_model: $('#models-select').val(),
    brand: $('#wooden-brand').val(),
    name: $('#wooden-name').val().trim(),
    grain: $('#wooden-grain').val(),
    length: parseInt($('#wooden-length').val()),
    length_unit: $('#wooden-length-unit').val(),
    width: parseInt($('#wooden-width').val()),
    width_unit: $('#wooden-width-unit').val(),
    thickness: $('#wooden-thickness').val(),
    thickness_unit: $('#wooden-thickness-unit').val(),
    compatible_thicknesses: $('#wooden-compatible-thicknesses').val().split(',').map(Number).filter(Boolean),
    cost_price: $('#wooden-cost-price').val(),
    costprice_type: $('#wooden-costprice-type').val(),
    sell_price: $('#wooden-sell-price').val(),
    sellprice_type: $('#wooden-sellprice-type').val(),
    color: $('#wooden-color').val() || 'no color',
  };

  const method = woodenId ? 'PUT' : 'POST';
  const url = woodenId ? `${woodenApi}${woodenId}/` : woodenApi;

  $.ajax({
    url,
    method,
    contentType: 'application/json',
    data: JSON.stringify(payload),
    success: function () {
      showAlert('Wooden saved successfully!');
      loadWoodens(payload.material_model);

      if (saveAndAddAnother) {
        $('#wooden-form')[0].reset();
        $('#wooden-id').val('');
      } else {
        $('#woodenModal').modal('hide');
      }

      saveAndAddAnother = false;
    },
    error: function () {
      showAlert('Failed to save wooden.');
      saveAndAddAnother = false;
    }
  });
});

$(document).on('click', '.edit-wooden-btn', function () {
  const idx = $(this).closest('.wooden-card').data('index');
  const item = woodenData[idx];
  if (!item) return;

  $('#wooden-id').val(item.id);
  $('#wooden-name').val(item.name);
  $('#wooden-thickness').val(item.thickness);
  $('#wooden-color').val(item.color || 'no color');

  $('#wooden-grain').val(item.grain);
  $('#wooden-length').val(item.length);
  $('#wooden-length-unit').val(item.length_unit);
  $('#wooden-width').val(item.width);
  $('#wooden-width-unit').val(item.width_unit);
  $('#wooden-thickness-unit').val(item.thickness_unit);
  $('#wooden-compatible-thicknesses').val((item.compatible_thicknesses || []).join(','));

  $('#wooden-cost-price').val(item.cost_price);
  $('#wooden-costprice-type').val(item.costprice_type);
  $('#wooden-sell-price').val(item.sell_price);
  $('#wooden-sellprice-type').val(item.sellprice_type);

  $('#wooden-brand').val(item.brand).trigger('change');

  $('#woodenModalLabel').text('Edit Wooden');
  new bootstrap.Modal('#woodenModal').show();
});
