const typeApi = "/material/v1/category-types/";
const typeModal = new bootstrap.Modal(document.getElementById("typeModal"));
let currentTypePage = 1;

// === Load Types Page with Pagination ===
function loadTypesPage(page = 1) {
  fetch(`${typeApi}?page=${page}`)
    .then(res => res.json())
    .then(data => {
      const types = data.results || [];
      renderTypes(types);
      currentTypePage = page;
      updateTypePagination(data.next, data.previous, data.count);
    })
    .catch(err => console.error("Pagination fetch error:", err));
}

// === Render Types into Table ===
function renderTypes(data) {
  const tbody = $("#typeTable tbody");
  tbody.empty();

  data.forEach(type => {
    const row = `<tr>
      <td>${type.category?.name ?? "N/A"}</td>
      <td>${type.name}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary edit-type"
          data-id="${type.id}"
          data-name="${type.name}"
          data-category-id="${type.category?.id ?? ''}">
          Edit
        </button>
        <button class="btn btn-sm btn-outline-danger delete-type" data-id="${type.id}">
          Delete
        </button>
      </td>
    </tr>`;
    tbody.append(row);
  });
}

// === Pagination Buttons ===
function updateTypePagination(nextUrl, prevUrl, totalCount = null) {
  const container = $("#type-pagination");
  container.empty();

  const prevBtn = `<button class="btn btn-outline-secondary btn-sm me-2" id="type-prev" ${prevUrl ? "" : "disabled"}>Prev</button>`;
  const nextBtn = `<button class="btn btn-outline-secondary btn-sm ms-2" id="type-next" ${nextUrl ? "" : "disabled"}>Next</button>`;
  const info = totalCount !== null
    ? `<span class="small text-muted align-self-center">Page ${currentTypePage}</span>`
    : "";

  container.append(prevBtn, info, nextBtn);
}

// === Open Modal (Reused for Add/Edit) ===
function openTypeModal({ id = '', name = '', categoryId = '' }) {
  $("#type-id").val(id);
  $("#type-name").val(name);
  $("#type-category-id").val(categoryId).trigger('change');
  $("#typeModal .modal-title").text(id ? "Edit Product Type" : "Add Product Type");
  $("#typeFormError").hide();
  typeModal.show();
}

// === Reset Modal on Close ===
document.getElementById("typeModal").addEventListener("hidden.bs.modal", () => {
  $("#typeForm")[0].reset();
  $("#type-category-id").val('').trigger("change");
  $("#typeFormError").hide();
  toggleFormLoading(false);
});

// === Add Button Click ===
$("#btn-add-type").on("click", () => openTypeModal({}));

// === Edit Button Click (Delegated) ===
$(document).on("click", ".edit-type", function () {
  openTypeModal({
    id: $(this).data("id"),
    name: $(this).data("name"),
    categoryId: $(this).data("category-id"),
  });
});

// === Submit Type Form (Add or Edit) ===
$("#typeForm").on("submit", function (e) {
  e.preventDefault();
  toggleFormLoading(true);
  $("#typeFormError").hide();

  const id = $("#type-id").val();
  const name = $("#type-name").val();
  const category_id = $("#type-category-id").val();

  const payload = JSON.stringify({ name, category_id });
  const method = id ? "PUT" : "POST";
  const url = id ? `${typeApi}${id}/` : typeApi;

  fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: payload
  })
    .then(async res => {
      if (!res.ok) {
        const errData = await res.json();
        console.error("DRF Error:", errData);
        if (errData.non_field_errors) {
          showError("This type already exists for the selected category.");
        } else {
          showError("Failed to save. Check inputs.");
        }
        throw new Error("Validation failed");
      }
      return res.json();
    })
    .then(() => {
      typeModal.hide();
      loadTypesPage(currentTypePage);
    })
    .catch(err => console.error("Save error:", err))
    .finally(() => toggleFormLoading(false));
});

// === Delete Type (Delegated) ===
$(document).on("click", ".delete-type", function () {
  const id = $(this).data("id");
  if (confirm("Delete this type?")) {
    fetch(`${typeApi}${id}/`, {
      method: "DELETE",
      headers: { "X-CSRFToken": getCookie("csrftoken") }
    })
      .then(() => loadTypesPage(currentTypePage))
      .catch(err => console.error("Delete error:", err));
  }
});

// === Load Categories for Select2 Dropdown ===
function loadCategoryDropdown() {
  return fetch("/material/v1/categories/")
    .then(res => res.json())
    .then(data => {
      const options = data.results || [];
      const select = $("#type-category-id");
      select.empty().append(`<option value="">Select Category</option>`);
      options.forEach(cat => {
        select.append(`<option value="${cat.id}">${cat.name}</option>`);
      });
    })
    .catch(err => console.error("Dropdown load error:", err));
}

// === Initialize Select2 ===
function setupSelect2() {
  $("#type-category-id").select2({
    dropdownParent: $("#typeModal"),
    placeholder: "Select Category",
    allowClear: true,
    width: "100%"
  });
}

// === Toggle Submit Button ===
function toggleFormLoading(disabled) {
  $("#typeForm button[type='submit']").prop("disabled", disabled);
}

// === Show Inline Error ===
function showError(msg) {
  $("#typeFormError").text(msg).show();
}

// === CSRF Cookie Helper ===
function getCookie(name) {
  let cookie = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const c = cookies[i].trim();
      if (c.substring(0, name.length + 1) === name + "=") {
        cookie = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookie;
}

// === INITIAL LOAD ===
$(document).ready(function () {
  loadTypesPage(currentTypePage);
  loadCategoryDropdown().then(setupSelect2);

  // ✅ One-time delegated pagination handlers
  $("#type-pagination").on("click", "#type-prev", () => {
    console.log("Prev clicked");
    if (currentTypePage > 1) loadTypesPage(currentTypePage - 1);
  });

  $("#type-pagination").on("click", "#type-next", () => {
    console.log("Next clicked");
    loadTypesPage(currentTypePage + 1);
  });
});
