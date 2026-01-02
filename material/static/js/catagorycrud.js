
// ======== CATEGORIES CRUD =========
function loadCategories(url){
  const search = $("#categorySearch").val() || "";
    const fetchUrl = url || (API.categories + (search ? `?search=${search}` : ""));
    $.get(fetchUrl, function(res){
        const data = toArrayOrResults(res);
        const rows = (data.results || []).map(c => `
            <tr data-id="${c.id}">
                <td>${c.name}</td>
                <td class="text-nowrap">
                    <button class="btn btn-sm btn-warning me-1 btn-edit-cat">Edit</button>
                    <button class="btn btn-sm btn-danger btn-del-cat">Delete</button>
                </td>
            </tr>
        `).join("");
        $("#categoriesTable tbody").html(rows);
        $("#categoriesPrev").prop("disabled", !data.previous).off("click").on("click", ()=> loadCategories(data.previous));
        $("#categoriesNext").prop("disabled", !data.next).off("click").on("click", ()=> loadCategories(data.next));
        $("#categoriesCount").text(`${data.count} items`);
    }).fail(handleApiError);
}

// Category form submit
$("#categoryForm").on("submit", function(e){
    e.preventDefault();
    const id = $("#categoryId").val();
    const name = $("#categoryName").val().trim();
    if(!name){ alert("Name required"); return; }

    $.get(API.categories, { search: name }, function(res){
        const duplicate = res.results.find(c => c.name.toLowerCase() === name.toLowerCase() && c.id != id);
        if(duplicate){ showToast("Category already exists", "error"); $("#categoryModal").modal("hide"); return; }

        const payload = { name };
        const req = id
          ? $.ajax({ url: API.categories+id+"/", type:"PUT", data:JSON.stringify(payload), contentType:"application/json", headers: { "X-CSRFToken": window.CSRF_TOKEN } })
          : $.ajax({ url: API.categories, type:"POST", data:JSON.stringify(payload), contentType:"application/json", headers: { "X-CSRFToken": window.CSRF_TOKEN } });

        req.done(()=> { $("#categoryModal").modal("hide"); loadCategories(); }).fail(handleApiError);
    }).fail(handleApiError);
});

// Edit & Delete
$("#categoriesTable").on("click", ".btn-edit-cat", function(){
    const id = $(this).closest("tr").data("id");
    $.get(API.categories+id+"/", function(c){
        $("#categoryId").val(c.id);
        $("#categoryName").val(c.name);
        $("#categoryModalTitle").text("Edit Category");
        $("#categoryModal").modal("show");
    }).fail(handleApiError);
});
$("#categoriesTable").on("click", ".btn-del-cat", function(){
    if(!confirm("Delete this category?")) return;
    const id = $(this).closest("tr").data("id");
    $.ajax({ url: API.categories+id+"/", type:"DELETE" }).done(()=> loadCategories()).fail(handleApiError);
});
$("#categorySearch").on("input", debounce(()=> loadCategories(), 400));
$("#addCategoryBtn").click(()=> { $("#categoryModalTitle").text("Add Category"); $("#categoryForm")[0].reset(); $("#categoryId").val(""); $("#categoryModal").modal("show"); });
