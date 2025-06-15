// main.js
$(function () {
  loadCategories();
  loadBrands();

  setupEnableDisable('categories-select', 'edit-category-btn', 'delete-category-btn');
  setupEnableDisable('types-select', 'edit-type-btn', 'delete-type-btn');
  setupEnableDisable('models-select', 'edit-model-btn', 'delete-model-btn');

  $('#categories-select').on('change', function () {
    loadTypes($(this).val());
  });

  $('#types-select').on('change', function () {
    loadModels($(this).val());
  });

  $('#models-select').on('change', function () {
    const modelId = $(this).val();
    const $btnContainer = $('#add-wooden-container');
    $btnContainer.empty();

    if (modelId) {
      loadWoodens(modelId);
      $btnContainer.append(`<button class="btn btn-primary" id="add-wooden-btn">+ Add Wooden</button>`);
    } else {
      $('#wooden-list, #wooden-pagination').empty();
    }
  });

  // Other logic from wooden-form.js and entity-modal.js will also hook here
});
