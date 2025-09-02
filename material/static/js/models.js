const modelApi = "/material/v1/category-models/";
const modelModal = new bootstrap.Modal(document.getElementById("modelModal"));
let currentModelPage = 1;

function loadCategoryDropdown(selectedId = null) {
  fetch("/material/v1/categories/")
    .then(res => res.json())
    .then(data => {
      const results = data.results || [];
      const select = $("#model-category-id");
      select.empty().append(`<option value="">Select Category</option>`);
      results.forEach(cat => {
        select.append(`<option value="${cat.id}">${cat.name}</option>`);
      });
      if (selectedId) select.val(selectedId);
      select.trigger("change.select2");
    });
}
function loadTypeDropdown(categoryId, selectedTypeId = null) {
  const typeSelect = $("#model-type-id");
  if (!categoryId) {
    typeSelect.html(`<option value="">Select Category First</option>`);
    return;
  }

  fetch(`/material/v1/category-types/?category=${categoryId}`)
    .then(res => res.json())
    .then(data => {
      const results = data.results || [];
      typeSelect.empty().append(`<option value="">Select Type</option>`);
      results.forEach(type => {
        typeSelect.append(`<option value="${type.id}">${type.name}</option>`);
      });

      if (selectedTypeId) typeSelect.val(selectedTypeId);
      typeSelect.trigger("change.select2");
    });
}
$("#model-category-id").on("change", function () {
  const categoryId = $(this).val();
  loadTypeDropdown(categoryId);
});
function loadModelsPage(page = 1) {
  fetch(`${modelApi}?page=${page}`)
    .then(res => res.json())
    .then(data => {
      const models = data.results || [];
      renderModels(models);
      currentModelPage = page;
      updateModelPagination(data.next, data.previous);
    });
}
function renderModels(data) {
  const tbody = $("#modelTable tbody");
  tbody.empty();

  data.forEach(model => {
    const row = `<tr>
      <td>${model.model_category?.category?.name || 'N/A'}</td>
      <td>${model.model_category?.name || 'N/A'}</td>
      <td>${model.name}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary edit-model"
          data-id="${model.id}"
          data-name="${model.name}"
          data-type-id="${model.model_category?.id || ''}"
          data-category-id="${model.model_category?.category?.id || ''}">
          Edit
        </button>
        <button class="btn btn-sm btn-outline-danger delete-model" data-id="${model.id}">Delete</button>
      </td>
    </tr>`;
    tbody.append(row);
  });
}
function updateModelPagination(nextUrl, prevUrl) {
  const container = $("#model-pagination");
  container.empty();

  const prevBtn = `<button class="btn btn-outline-secondary btn-sm me-2" id="model-prev" ${prevUrl ? "" : "disabled"}>Prev</button>`;
  const nextBtn = `<button class="btn btn-outline-secondary btn-sm" id="model-next" ${nextUrl ? "" : "disabled"}>Next</button>`;

  container.append(prevBtn, nextBtn);

  $("#model-prev").on("click", () => {
    if (currentModelPage > 1) loadModelsPage(currentModelPage - 1);
  });

  $("#model-next").on("click", () => {
    loadModelsPage(currentModelPage + 1);
  });
}
$("#btn-add-model").on("click", function () {
  $("#model-id").val('');
  $("#model-name").val('');
  $("#model-category-id").val('').trigger("change"); // clears both category + type
  $("#model-type-id").html('<option value="">Select Category First</option>');
  $("#modelModal .modal-title").text("Add Blueprint");
  modelModal.show();
});


$(document).on("click", ".edit-model", function () {
  const id = $(this).data("id");
  const name = $(this).data("name");
  const typeId = $(this).data("type-id");
  const categoryId = $(this).data("category-id");

  $("#model-id").val(id);
  $("#model-name").val(name);
  $("#model-category-id").val(categoryId).trigger("change");

  // Delay loading types until category select settles
  setTimeout(() => {
    loadTypeDropdown(categoryId, typeId);
  }, 200);

  $("#modelModal .modal-title").text("Edit Blueprint");
  modelModal.show();
});
$("#modelForm").on("submit", function (e) {
  e.preventDefault();
  const id = $("#model-id").val();
  const name = $("#model-name").val().toUpperCase();
  const model_category_id = $("#model-type-id").val();

  const method = id ? "PUT" : "POST";
  const url = id ? `${modelApi}${id}/` : modelApi;

  fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ name, model_category_id })
  })
    .then(res => res.json())
    .then(() => {
      modelModal.hide();
      loadModelsPage(currentModelPage);
    });
});
$(document).on("click", ".delete-model", function () {
  const id = $(this).data("id");
  if (confirm("Delete this model?")) {
    fetch(`${modelApi}${id}/`, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")
      }
    }).then(() => loadModelsPage(currentModelPage));
  }
});
function getCookie(name) {
  let cookie = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
      const trimmed = c.trim();
      if (trimmed.startsWith(name + "=")) {
        cookie = decodeURIComponent(trimmed.substring(name.length + 1));
        break;
      }
    }
  }
  return cookie;
}
loadCategoryDropdown();
loadModelsPage(currentModelPage);
