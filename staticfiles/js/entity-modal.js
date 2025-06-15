function openEntityModal(type, id = '', name = '') {
  $('#entity-type').val(type);
  $('#entity-id').val(id);
  $('#entity-name').val(name);
  $('#entityModalLabel').text(id ? `Edit ${capitalize(type)}` : `Add ${capitalize(type)}`);
  new bootstrap.Modal('#entityModal').show();
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function saveEntity(type, id, name) {
  const method = id ? 'PUT' : 'POST';
  let url = '';
  const data = { name };

  if (type === 'category') {
    url = id ? `${categoriesApi}${id}/` : categoriesApi;
  } else if (type === 'type') {
    const categoryId = $('#categories-select').val();
    if (!categoryId) return showAlert('Select a category first');
    data.category_id = categoryId;
    url = id ? `${typesApi}${id}/` : typesApi;
  } else if (type === 'model') {
    const typeId = $('#types-select').val();
    if (!typeId) return showAlert('Select a type first');
    data.model_category_id = typeId;
    url = id ? `${modelsApi}${id}/` : modelsApi;
  }

  $.ajax({
    url,
    method,
    contentType: 'application/json',
    data: JSON.stringify(data),
    success: () => {
      $('#entityModal').modal('hide');
      showAlert(`${capitalize(type)} saved successfully`);
      if (type === 'category') loadCategories();
      if (type === 'type') loadTypes($('#categories-select').val());
      if (type === 'model') loadModels($('#types-select').val());
    },
    error: () => showAlert(`Failed to save ${type}`)
  });
}

$('#entity-form').on('submit', function (e) {
  e.preventDefault();

  const id = $('#entity-id').val();
  const type = $('#entity-type').val();
  const name = $('#entity-name').val().trim();
  if (!name) return showAlert('Name is required');

  saveEntity(type, id, name);
});
