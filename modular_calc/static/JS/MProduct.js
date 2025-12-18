
    // ==============================
// Global State
// ==============================
const mpState = {
    page: 1,
    lastPage: 1,
    category: "",
    type: "",
    model: "",
    search: ""
};

let allCategories = [];
let allTypes = [];
let allModels = [];

let tableSort = {
    categories: { field: null, direction: 1 },
    types:      { field: null, direction: 1 },
    models:     { field: null, direction: 1 }
};

let currentCategoryPage = 1;
let currentTypePage = 1;
let currentModelPage = 1;

// ==============================
// API Endpoints
// ==============================
const api = {
    categories: "/modularcalc/api/product-categories/",
    types: "/modularcalc/api/product-types/",
    models: "/modularcalc/api/product-models/",
    products: "/modularcalc/api/products/"
};

// ==============================
// Fetch All Pages Utility
// ==============================
async function fetchAllPages(url) {
    let results = [];
    let nextUrl = url;

    while (nextUrl) {
        try {
            const res = await fetch(nextUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (data.results) results.push(...data.results);
            nextUrl = data.next;
        } catch (err) {
            console.error("Error fetching", nextUrl, err);
            nextUrl = null;
        }
    }
    return results;
}

// ==============================
// Preload reference data
// ==============================
async function preloadReferenceData() {
    try {
        [allCategories, allTypes, allModels] = await Promise.all([
            fetchAllPages(api.categories),
            fetchAllPages(api.types),
            fetchAllPages(api.models)
        ]);

        

        renderCategoryTable();
        renderTypeTable();
        renderModelTable();
        loadCategoriesDropdown(["mp-filter-category"]);
    } catch (err) {
        console.error("Failed to preload reference data:", err);
    }
}

// ==============================
// Modular Products
// ==============================
async function apiGet(url, params = {}) {
    const fullUrl = new URL(url, window.location.origin);
    Object.keys(params).forEach(k => params[k] && fullUrl.searchParams.append(k, params[k]));
    const res = await fetch(fullUrl);
    return res.json();
}

async function loadModularProducts() {
    const data = await apiGet(api.products, {
        page: mpState.page,
        category: mpState.category,
        type: mpState.type,
        model: mpState.model,
        search: mpState.search
    });

    mpState.lastPage = Math.ceil(data.count / 10);
    renderProducts(data.results);
}

function renderProducts(products) {
    const container = document.getElementById("product-list-container");
    if (!products.length) {
        container.innerHTML = "<p class='text-center'>No products found</p>";
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="col-md-4 mb-3" data-product-id="${product.id}">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${product.name}</h5>
                    <p class="card-text">${product.description || 'No description available'}</p>
                    <p><strong>Price:</strong> $${product.price ?? 0}</p>
                    <button class="btn btn-primary view-btn" data-id="${product.id}">View</button>
                    <button class="btn btn-warning btn-sm edit-btn" data-id="${product.id}">Edit</button>
                    <button class="btn btn-danger btn-sm delete-btn" data-id="${product.id}">Delete</button>
                </div>
            </div>
        </div>
    `).join("");
}

// Product buttons
document.addEventListener("click", async e => {
    const id = e.target.dataset.id;
    if (!id) return;
    if (e.target.classList.contains("view-btn")) viewProductDetails(id);
    if (e.target.classList.contains("edit-btn")) editProduct(id);
    if (e.target.classList.contains("delete-btn")) deleteProduct(id);
});

// Pagination buttons
document.getElementById("mp-next-page").addEventListener("click", () => {
    if (mpState.page < mpState.lastPage) { mpState.page++; loadModularProducts(); }
});
document.getElementById("mp-prev-page").addEventListener("click", () => {
    if (mpState.page > 1) { mpState.page--; loadModularProducts(); }
});

// Search input
document.getElementById("mp-search").addEventListener("input", e => {
    mpState.search = e.target.value.trim();
    mpState.page = 1;
    loadModularProducts();
});
document.getElementById("show-add-product-btn").addEventListener("click", () => {
    window.location.href = "/modularcalc/addproduct/";
});
// ==============================
// Sorting Utility
// ==============================
function sortList(list, sortState) {
    if (!sortState.field) return list;
    return list.slice().sort((a,b) => {
        let x = a[sortState.field], y = b[sortState.field];
        if (x === undefined || y === undefined) return 0;
        x = typeof x === "string" ? x.toLowerCase() : x;
        y = typeof y === "string" ? y.toLowerCase() : y;
        if (x < y) return -1 * sortState.direction;
        if (x > y) return  1 * sortState.direction;
        return 0;
    });
}

// ==============================
// Tables rendering
// ==============================
function renderCategoryTable() {
    const searchTerm = document.getElementById("category-search").value.toLowerCase();
    let filtered = allCategories;
    if (searchTerm.length >= 3) filtered = allCategories.filter(c => c.name.toLowerCase().includes(searchTerm));
    filtered = sortList(filtered, tableSort.categories);

    const perPage = parseInt(document.getElementById("category-per-page").value) || 5;
    const totalPages = Math.ceil(filtered.length / perPage);
    if (currentCategoryPage > totalPages) currentCategoryPage = totalPages || 1;
    const start = (currentCategoryPage-1)*perPage;
    const paginated = filtered.slice(start,start+perPage);

    let html = "";
    paginated.forEach(c => {
        html += `
        <tr>
            <td>${c.name}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-warning me-1" onclick="editCategory(${c.id}, '${c.name}')"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${c.id})"><i class="bi bi-trash"></i></button>
            </td>
        </tr>`;
    });
    document.getElementById("categoryTable").innerHTML = html;

    document.getElementById("category-prev").disabled = currentCategoryPage <= 1;
    document.getElementById("category-next").disabled = currentCategoryPage >= totalPages;
    document.getElementById("category-prev").onclick = () => { currentCategoryPage--; renderCategoryTable(); };
    document.getElementById("category-next").onclick = () => { currentCategoryPage++; renderCategoryTable(); };
}

document.getElementById("category-search").addEventListener("input", () => {
    currentCategoryPage = 1; // go back to first page
    renderCategoryTable();
});
function renderTypeTable() {
    const searchTerm = document.getElementById("type-search").value.toLowerCase();
    let filtered = allTypes;
    if (searchTerm.length >= 3) filtered = filtered.filter(t =>
        t.name.toLowerCase().includes(searchTerm) ||
        (t.category_name && t.category_name.toLowerCase().includes(searchTerm))
    );
    filtered = sortList(filtered, tableSort.types);

    const perPage = parseInt(document.getElementById("type-per-page").value) || 5;
    const totalPages = Math.ceil(filtered.length/perPage);
    if (currentTypePage>totalPages) currentTypePage=totalPages||1;
    const start=(currentTypePage-1)*perPage;
    const paginated=filtered.slice(start,start+perPage);

    let html="";
    paginated.forEach(t=>{
        html += `<tr>
            
            <td>${t.name}</td>
            <td>${t.category_name}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="editType(${t.id}, '${t.name}', ${t.category})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-danger btn-sm" onclick="deleteType(${t.id})"><i class="bi bi-trash"></button>
            </td>
        </tr>`;
    });
    document.getElementById("typeTable").innerHTML = html;
    document.getElementById("type-prev").disabled=currentTypePage<=1;
    document.getElementById("type-next").disabled=currentTypePage>=totalPages;
    document.getElementById("type-prev").onclick=()=>{currentTypePage--;renderTypeTable();};
    document.getElementById("type-next").onclick=()=>{currentTypePage++;renderTypeTable();};
}
document.getElementById("type-search").addEventListener("input", () => {
    currentTypePage = 1; // go back to first page when typing
    renderTypeTable();
});
function renderModelTable() {
    const searchTerm=document.getElementById("model-search").value.toLowerCase();
    let filtered=allModels;
    if(searchTerm.length>=3) filtered=filtered.filter(m=>m.name.toLowerCase().includes(searchTerm) || (m.type_name && m.type_name.toLowerCase().includes(searchTerm)));
    filtered=sortList(filtered, tableSort.models);

    const perPage=parseInt(document.getElementById("model-per-page").value)||5;
    const totalPages=Math.ceil(filtered.length/perPage);
    if(currentModelPage>totalPages) currentModelPage=totalPages||1;
    const start=(currentModelPage-1)*perPage;
    const paginated=filtered.slice(start,start+perPage);

    let html="";
    paginated.forEach(m=>{
        html+=`<tr>
            
            <td>${m.name}</td>
            <td>${m.type_name||""}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="editModel(${m.id}, '${m.name}', ${m.type}, ${m.category})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-danger btn-sm" onclick="deleteModel(${m.id})"><i class="bi bi-trash"></button>
            </td>
        </tr>`;
    });
    document.getElementById("modelTable").innerHTML=html;
    document.getElementById("model-prev").disabled=currentModelPage<=1;
    document.getElementById("model-next").disabled=currentModelPage>=totalPages;
    document.getElementById("model-prev").onclick=()=>{currentModelPage--;renderModelTable();};
    document.getElementById("model-next").onclick=()=>{currentModelPage++;renderModelTable();};
}
document.getElementById("model-search").addEventListener("input", () => {
    currentModelPage = 1; // reset page when searching
    renderModelTable();
});
// ==============================
// Dropdowns
// ==============================
function loadCategoriesDropdown(extraIds=[]) {
    let html=`<option value="">Select Category</option>`;
    allCategories.forEach(c=>html+=`<option value="${c.id}">${c.name}</option>`);
    ["categoryselect","typeCategory","modelCategory"].concat(extraIds).forEach(id=>{
        const el=document.getElementById(id);
        if(el) el.innerHTML=html;
    });
}

function loadTypesDropdownByCategory(categoryId, targetIds=[]) {
    let list = allTypes.filter(t=>t.category==categoryId);
    let html=`<option value="">Select Type</option>`;
    list.forEach(t=>html+=`<option value="${t.id}">${t.name}</option>`);
    ["type-select","modelType"].concat(targetIds).forEach(id=>{
        const el=document.getElementById(id);
        if(el){ el.innerHTML=html; el.disabled=false; }
    });
}

function loadModelsDropdownByType(typeId, targetIds=[]) {
    let list = allModels.filter(m=>m.type==typeId);
    let html=`<option value="">Select Model</option>`;
    list.forEach(m=>html+=`<option value="${m.id}">${m.name}</option>`);
    ["model-select"].concat(targetIds).forEach(id=>{
        const el=document.getElementById(id);
        if(el){ el.innerHTML=html; el.disabled=false; }
    });
}

// ==============================
// Filters setup
// ==============================
function setupFilter(selectId, stateKey, loadDependentDropdown=null){
    const select=document.getElementById(selectId);
    select.addEventListener("change",async e=>{
        mpState[stateKey]=e.target.value;
        mpState.page=1;

        if(selectId==="mp-filter-category"){ mpState.type=""; mpState.model=""; }
        if(selectId==="mp-filter-type") mpState.model="";

        if(loadDependentDropdown) await loadDependentDropdown(mpState[stateKey]);

        document.getElementById("mp-filter-type").disabled=!mpState.category;
        document.getElementById("mp-filter-model").disabled=!mpState.type;

        loadModularProducts();
    });
}

// ==============================
// Init on page load
// ==============================
document.addEventListener("DOMContentLoaded", async ()=>{
    await preloadReferenceData();

    setupFilter("mp-filter-category","category",async c=>loadTypesDropdownByCategory(c,["mp-filter-type"]));
    setupFilter("mp-filter-type","type",async t=>loadModelsDropdownByType(t,["mp-filter-model"]));
    setupFilter("mp-filter-model","model");

    loadModularProducts();
});

// ==============================
// Sorting click events
// ==============================
document.querySelectorAll(".sortable").forEach(h=>{
    h.style.cursor="pointer";
    h.addEventListener("click",()=>{
        const tab=h.dataset.tab, field=h.dataset.sort;
        let s=tableSort[tab];
        if(s.field===field) s.direction*=-1; else { s.field=field; s.direction=1; }

        if(tab==="categories") renderCategoryTable();
        if(tab==="types") renderTypeTable();
        if(tab==="models") renderModelTable();
    });
});
function openCategoryModal() {
    document.getElementById("categoryId").value = "";
    document.getElementById("categoryName").value = "";
    const modal = new bootstrap.Modal(document.getElementById("categoryModal"));
    modal.show();
}
function editCategory(id, name) {
    document.getElementById("categoryId").value = id;
    document.getElementById("categoryName").value = name;
    const modal = new bootstrap.Modal(document.getElementById("categoryModal"));
    modal.show();
}
function saveCategory(event) {
    event.preventDefault();
    const id = document.getElementById("categoryId").value;
    const name = document.getElementById("categoryName").value;

    const method = id ? "PUT" : "POST";
    const url = id ? api.categories + id + "/" : api.categories;

    console.log(`Saving category (${method}):`, name);

    fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
    })
    .then(res => res.json())
    .then(() => {
        console.log("Category saved successfully");
        document.getElementById("categoryForm").reset();
        bootstrap.Modal.getInstance(document.getElementById("categoryModal")).hide();
        preloadReferenceData();
    })
    .catch(err => console.error("Save Category Error:", err));
}
function deleteCategory(id) {
    if (!confirm("Are you sure you want to delete this category?")) return;
    console.log("Deleting category:", id);

    fetch(api.categories + id + "/", { method: "DELETE" })
        .then(() => {
            
            preloadReferenceData();
        })
        .catch(err => console.error("Delete Category Error:", err));
}
function openTypeModal() {
  document.getElementById("typeId").value = "";
  document.getElementById("typeName").value = "";
  loadCategoriesDropdown();
  new bootstrap.Modal("#typeModal").show();
}

function editType(id, name, category) {
  document.getElementById("typeId").value = id;
  document.getElementById("typeName").value = name;
  loadCategoriesDropdown();

  setTimeout(() => {
    document.getElementById("typeCategory").value = category;
  }, 300);

  new bootstrap.Modal("#typeModal").show();
}

function saveType(e) {
  e.preventDefault();
  let id = document.getElementById("typeId").value;
  let payload = {
    name: document.getElementById("typeName").value,
    category: document.getElementById("typeCategory").value
  };

  fetch(id ? api.types + id + "/" : api.types, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(() => {
    bootstrap.Modal.getInstance(document.getElementById("typeModal")).hide();
    preloadReferenceData();
  });
}

function deleteType(id) {
    if (!confirm("Are you sure you want to delete this Type?")) return;

    fetch(`${api.types}${id}/`, { method: "DELETE" })
        .then((res) => {
            if (!res.ok) {
                throw new Error(`Failed to delete type. HTTP ${res.status}`);
            }
            return preloadReferenceData();
        })
        .catch(err => {
            console.error("Delete Type Error:", err);
            alert("Failed to delete type. Check console for details.");
        });
}

async function openModelModal() {
  document.getElementById("modelId").value = "";
  document.getElementById("modelName").value = "";
  await loadCategoriesDropdown(); // wait for categories
  document.getElementById("modelType").innerHTML = ''; // clear type
  new bootstrap.Modal("#modelModal").show();
}

async function editModel(id, name, type, category) {
  document.getElementById("modelId").value = id;
  document.getElementById("modelName").value = name;

  await loadCategoriesDropdown();          // load categories
  document.getElementById("modelCategory").value = category; 

  await loadTypesDropdownByCategory(category); // load types for category
  document.getElementById("modelType").value = type;

  new bootstrap.Modal("#modelModal").show();
}
async function saveModel(e) {
  e.preventDefault();
  let id = document.getElementById("modelId").value;
  let payload = {
    name: document.getElementById("modelName").value,
    type: document.getElementById("modelType").value
  };

  await fetch(id ? api.models + id + "/" : api.models, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  bootstrap.Modal.getInstance(document.getElementById("modelModal")).hide();

  // Prefetch all models to refresh table
  allModels = await fetchAllPages(api.models);
  preloadReferenceData();
}

async function deleteModel(id) {
    if (!confirm("Are you sure you want to delete this Model?")) return;

    try {
        const res = await fetch(`${api.models}${id}/`, { method: "DELETE" });
        if (!res.ok) {
            throw new Error(`Failed to delete model. HTTP ${res.status}`);
        }

        await preloadReferenceData();   // refresh categories, types, models, dropdowns, tables

    } catch (err) {
        console.error("Delete Model Error:", err);
        alert("Failed to delete model. Check console for details.");
    }
}


