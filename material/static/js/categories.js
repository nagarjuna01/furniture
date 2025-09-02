
const categoryApi = "/material/v1/categories/";
const catModal = new bootstrap.Modal(document.getElementById("categoryModal"));

let currentPage = 1;

function loadCategoriesPage(page = 1) {
  fetch(`/material/v1/categories/?page=${page}`)
    .then(res => res.json())
    .then(data => {
      const categories = data.results || [];
      renderCategories(categories);

      // For pagination
      currentPage = page;
      updatePaginationUI(data.next, data.previous);
    });
}

$("#btn-add-category").on("click", function () {
  $("#category-id").val('');
  $("#category-name").val('');
  $("#categoryModal .modal-title").text("Add Category");
  catModal.show();
});

$(document).on("click", ".edit-cat", function () {
  $("#category-id").val($(this).data("id"));
  $("#category-name").val($(this).data("name"));
  $("#categoryModal .modal-title").text("Edit Category");
  catModal.show();
});

$("#categoryForm").on("submit", function (e) {
  e.preventDefault();

  const id = $("#category-id").val();
  let name = $("#category-name").val();

  if (!name || typeof name !== 'string') {
    console.warn("Category name is required and must be a string.");
    return;
  }

  name = name.toUpperCase();  // Optional normalization

  const method = id ? "PUT" : "POST";
  const url = id ? `${categoryApi}${id}/` : categoryApi;

  console.log("Submitting category:", { id, name, method, url });

  fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ name })
  })
    .then(res => {
      if (!res.ok) {
        return res.json().then(err => {
          console.error("Server returned 400:", err);
          throw new Error("Bad Request");
        });
      }
      return res.json();
    })
    .then(() => {
      catModal.hide();
      loadCategoriesPage(currentPage);
    })
    .catch(err => {
      console.error("Submit failed:", err);
    });
});

$(document).on("click", ".delete-cat", function () {
  const id = $(this).data("id");
  if (confirm("Delete category?")) {
    fetch(`${categoryApi}${id}/`, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCookie("csrftoken")
      }
    }).then(() => loadCategoriesPage(currentPage));
  }
});

// CSRF Token helper
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

function renderCategories(categories) {
  const tbody = $("#categoryTable tbody");
  tbody.empty();

  categories.forEach(cat => {
    const row = `
      <tr>
        <td>${cat.name}</td>
        <td>
          <button class="btn btn-sm btn-warning edit-cat" data-id="${cat.id}" data-name="${cat.name}">Edit</button>
          <button class="btn btn-sm btn-danger delete-cat" data-id="${cat.id}">Delete</button>
        </td>
      </tr>
    `;
    tbody.append(row);
  });
}

function updatePaginationUI(nextUrl, prevUrl) {
  const paginationContainer = $("#category-pagination");
  paginationContainer.html(""); // Clear old buttons

  const prevDisabled = prevUrl ? "" : "disabled";
  const nextDisabled = nextUrl ? "" : "disabled";

  const prevBtn = `<button class="btn btn-outline-primary btn-sm me-2" id="prev-page" ${prevDisabled}>Previous</button>`;
  const nextBtn = `<button class="btn btn-outline-primary btn-sm" id="next-page" ${nextDisabled}>Next</button>`;

  paginationContainer.append(prevBtn + nextBtn);

  // Bind click events to new buttons
  $("#prev-page").on("click", function () {
    if (currentPage > 1) {
      loadCategoriesPage(currentPage - 1);
    }
  });

  $("#next-page").on("click", function () {
    loadCategoriesPage(currentPage + 1);
  });
}

loadCategoriesPage(currentPage);
