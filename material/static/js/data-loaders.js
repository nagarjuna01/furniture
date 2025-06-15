// data-loaders.js
function loadCategories() {
  $.get(categoriesApi)
    .done(data => {
      const $catSelect = $('#categories-select');
      $catSelect.empty().append('<option value="">Select Category</option>');
      $('#types-select, #models-select, #add-wooden-container, #wooden-list, #wooden-pagination').empty();

      data.forEach(cat => $catSelect.append(new Option(cat.name, cat.id)));
    })
    .fail(() => showAlert('Failed to load categories'));
}

function loadTypes(categoryId) {
  if (!categoryId) {
    $('#types-select, #models-select, #add-wooden-container, #wooden-list, #wooden-pagination').empty();
    return;
  }

  $.get(`${typesApi}?category=${categoryId}`)
    .done(data => {
      const $typeSelect = $('#types-select');
      $typeSelect.empty().append('<option value="">Select Type</option>');
      $('#models-select, #add-wooden-container, #wooden-list, #wooden-pagination').empty();

      data.forEach(type => $typeSelect.append(new Option(type.name, type.id)));
    })
    .fail(() => showAlert('Failed to load types'));
}

function loadModels(type_id) {
  $.get(modelsApi, { model_category: type_id })
    .done(data => {
      const $modelSelect = $('#models-select');
      $modelSelect.empty().append('<option value="">Select Model</option>');
      $('#add-wooden-container, #wooden-list, #wooden-pagination').empty();

      if (data.length === 0) {
        $modelSelect.append('<option>No models found</option>');
      } else {
        data.forEach(model => $modelSelect.append(new Option(model.name, model.id)));
      }
    })
    .fail(() => showAlert('Failed to load models'));
}

function loadBrands() {
  $.get('http://127.0.0.1:8000/material/brands/')
    .done(data => {
      const $brandSelect = $('#wooden-brand');
      $brandSelect.empty().append('<option value="">Select Brand</option>');
      data.forEach(brand => $brandSelect.append(new Option(brand.name, brand.id)));

      $brandSelect.select2({
        placeholder: 'Select a brand',
        allowClear: true,
        width: '100%'
      });
    })
    .fail(() => showAlert('Failed to load brands'));
}

function loadWoodens(model_id) {
  if (!model_id) return;

  $.get(`${woodenApi}?model=${model_id}`)
    .done(data => {
      woodenData = Array.isArray(data.results) ? data.results : [];
      currentPage = 1;
      renderWoodensPage(currentPage);
    })
    .fail(() => showAlert('Failed to load wooden items'));
}
